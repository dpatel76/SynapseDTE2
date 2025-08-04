"""
Intelligent sampling service for anomaly-based and risk-based selection
"""
from typing import Dict, List, Optional, Tuple, Any
import asyncio
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
import pandas as pd

from app.models.sample_selection_enhanced import (
    IntelligentSamplingJob, SamplePool, IntelligentSample,
    SamplingRule, SampleLineage, SamplingStrategy, SampleCategory
)
from app.models.profiling_enhanced import ProfilingJob, ProfilingAnomalyPattern
from app.core.database import AsyncSessionLocal
from app.core.security.data_masking import DataMaskingService, FieldLevelSecurity

logger = logging.getLogger(__name__)


class IntelligentSamplingService:
    """Service for intelligent sample selection"""
    
    def __init__(self, masking_service: Optional[DataMaskingService] = None):
        self.masking_service = masking_service or DataMaskingService()
        self.field_security = FieldLevelSecurity(self.masking_service)
        self.anomaly_detector = AnomalyDetector()
        self.risk_scorer = RiskScorer()
    
    async def create_sampling_job(
        self,
        cycle_id: int,
        report_id: int,
        profiling_job_id: str,
        config: Dict[str, Any],
        session: AsyncSession
    ) -> IntelligentSamplingJob:
        """Create a new intelligent sampling job"""
        try:
            # Validate profiling job exists and is complete
            profiling_job = await session.get(ProfilingJob, profiling_job_id)
            if not profiling_job or profiling_job.status != 'completed':
                raise ValueError("Profiling job must be completed before sampling")
            
            # Create sampling job
            job = IntelligentSamplingJob(
                cycle_id=cycle_id,
                report_id=report_id,
                profiling_job_id=profiling_job_id,
                target_sample_size=config.get('target_size', 1000),
                sampling_strategies=config.get('strategies', [
                    SamplingStrategy.ANOMALY_BASED.value,
                    SamplingStrategy.BOUNDARY.value,
                    SamplingStrategy.RISK_BASED.value,
                    SamplingStrategy.RANDOM.value
                ]),
                normal_percentage=config.get('normal_percentage', 40),
                anomaly_percentage=config.get('anomaly_percentage', 30),
                boundary_percentage=config.get('boundary_percentage', 20),
                edge_case_percentage=config.get('edge_case_percentage', 10),
                source_type=config.get('source_type', 'database'),
                source_criteria=config.get('source_criteria', {}),
                status='pending'
            )
            
            session.add(job)
            await session.commit()
            
            return job
            
        except Exception as e:
            logger.error(f"Failed to create sampling job: {str(e)}")
            raise
    
    async def execute_sampling_job(
        self,
        job_id: str,
        session: AsyncSession
    ) -> IntelligentSamplingJob:
        """Execute intelligent sampling job"""
        try:
            # Get job
            job = await session.get(IntelligentSamplingJob, job_id)
            if not job:
                raise ValueError(f"Sampling job {job_id} not found")
            
            # Update status
            job.status = 'running'
            job.start_time = datetime.utcnow()
            await session.commit()
            
            # Create sample pools
            pools = await self._create_sample_pools(job, session)
            
            # Select samples from each pool
            selected_samples = []
            for pool in pools:
                samples = await self._select_from_pool(job, pool, session)
                selected_samples.extend(samples)
            
            # Calculate quality score
            quality_score = await self._calculate_quality_score(selected_samples)
            
            # Update job completion
            job.status = 'completed'
            job.end_time = datetime.utcnow()
            job.total_samples_selected = len(selected_samples)
            job.selection_quality_score = quality_score
            
            await session.commit()
            
            return job
            
        except Exception as e:
            logger.error(f"Sampling job execution failed: {str(e)}")
            job.status = 'failed'
            await session.commit()
            raise
    
    async def _create_sample_pools(
        self,
        job: IntelligentSamplingJob,
        session: AsyncSession
    ) -> List[SamplePool]:
        """Create candidate pools for different categories"""
        pools = []
        
        # Get profiling results and patterns
        profiling_job = await session.get(ProfilingJob, job.profiling_job_id)
        patterns = await session.execute(
            select(ProfilingAnomalyPattern).filter(
                ProfilingAnomalyPattern.job_id == job.profiling_job_id
            )
        )
        
        # Create anomaly pool
        if SamplingStrategy.ANOMALY_BASED.value in job.sampling_strategies:
            anomaly_pool = await self._create_anomaly_pool(job, patterns.scalars().all())
            pools.append(anomaly_pool)
        
        # Create boundary pool
        if SamplingStrategy.BOUNDARY.value in job.sampling_strategies:
            boundary_pools = await self._create_boundary_pools(job, session)
            pools.extend(boundary_pools)
        
        # Create risk-based pool
        if SamplingStrategy.RISK_BASED.value in job.sampling_strategies:
            risk_pool = await self._create_risk_pool(job, session)
            pools.append(risk_pool)
        
        # Create normal pool
        normal_pool = await self._create_normal_pool(job, session)
        pools.append(normal_pool)
        
        # Save pools
        session.add_all(pools)
        await session.commit()
        
        return pools
    
    async def _create_anomaly_pool(
        self,
        job: IntelligentSamplingJob,
        patterns: List[ProfilingAnomalyPattern]
    ) -> SamplePool:
        """Create pool of anomaly candidates"""
        # Aggregate anomaly candidates from patterns
        candidate_ids = []
        for pattern in patterns:
            if pattern.recommended_for_sampling:
                candidate_ids.extend(pattern.sample_record_ids or [])
        
        # Remove duplicates
        candidate_ids = list(set(candidate_ids))
        
        # Calculate diversity score based on pattern variety
        pattern_types = set(p.pattern_type for p in patterns)
        diversity_score = len(pattern_types) / 10.0  # Normalize to 0-1
        
        return SamplePool(
            job_id=job.job_id,
            category=SampleCategory.ANOMALY,
            total_candidates=len(candidate_ids),
            selection_criteria={
                'source': 'profiling_anomalies',
                'pattern_count': len(patterns)
            },
            diversity_score=diversity_score,
            relevance_score=0.9,  # High relevance for anomalies
            candidate_ids=candidate_ids[:10000],  # Limit for storage
            candidate_metadata={
                'pattern_summary': {
                    p.pattern_type: p.occurrence_count
                    for p in patterns[:10]
                }
            }
        )
    
    async def _create_boundary_pools(
        self,
        job: IntelligentSamplingJob,
        session: AsyncSession
    ) -> List[SamplePool]:
        """Create pools for boundary value candidates"""
        pools = []
        
        # Get schema information
        # This would query actual data to find boundary values
        # Placeholder implementation
        
        # High boundary pool
        high_pool = SamplePool(
            job_id=job.job_id,
            category=SampleCategory.BOUNDARY_HIGH,
            subcategory='numeric_high',
            total_candidates=1000,  # Placeholder
            selection_criteria={
                'percentile': '95-100',
                'attributes': ['amount', 'balance', 'transaction_count']
            },
            diversity_score=0.7,
            relevance_score=0.8,
            candidate_ids=[],  # Would be populated from query
            candidate_metadata={
                'value_ranges': {
                    'amount': {'min': 100000, 'max': 999999},
                    'balance': {'min': 50000, 'max': 500000}
                }
            }
        )
        pools.append(high_pool)
        
        # Low boundary pool
        low_pool = SamplePool(
            job_id=job.job_id,
            category=SampleCategory.BOUNDARY_LOW,
            subcategory='numeric_low',
            total_candidates=1000,  # Placeholder
            selection_criteria={
                'percentile': '0-5',
                'attributes': ['amount', 'balance', 'transaction_count']
            },
            diversity_score=0.7,
            relevance_score=0.8,
            candidate_ids=[],  # Would be populated from query
            candidate_metadata={
                'value_ranges': {
                    'amount': {'min': 0, 'max': 10},
                    'balance': {'min': -1000, 'max': 0}
                }
            }
        )
        pools.append(low_pool)
        
        return pools
    
    async def _create_risk_pool(
        self,
        job: IntelligentSamplingJob,
        session: AsyncSession
    ) -> SamplePool:
        """Create pool of high-risk candidates"""
        # This would use risk scoring logic to identify candidates
        # Placeholder implementation
        
        risk_criteria = {
            'large_transactions': True,
            'unusual_patterns': True,
            'regulatory_flags': True
        }
        
        return SamplePool(
            job_id=job.job_id,
            category=SampleCategory.HIGH_RISK,
            total_candidates=500,  # Placeholder
            selection_criteria=risk_criteria,
            diversity_score=0.8,
            relevance_score=0.95,  # Very high relevance
            candidate_ids=[],  # Would be populated
            candidate_metadata={
                'risk_factors': {
                    'high_amount': 200,
                    'unusual_timing': 150,
                    'pattern_break': 150
                }
            }
        )
    
    async def _create_normal_pool(
        self,
        job: IntelligentSamplingJob,
        session: AsyncSession
    ) -> SamplePool:
        """Create pool of normal candidates"""
        return SamplePool(
            job_id=job.job_id,
            category=SampleCategory.NORMAL,
            total_candidates=10000,  # Placeholder
            selection_criteria={
                'no_anomalies': True,
                'within_normal_ranges': True
            },
            diversity_score=0.5,
            relevance_score=0.5,  # Baseline relevance
            candidate_ids=[],  # Would be populated
            candidate_metadata={
                'selection_method': 'random_from_clean'
            }
        )
    
    async def _select_from_pool(
        self,
        job: IntelligentSamplingJob,
        pool: SamplePool,
        session: AsyncSession
    ) -> List[IntelligentSample]:
        """Select samples from a pool based on strategy"""
        # Calculate how many samples to select from this pool
        pool_percentage = self._get_pool_percentage(job, pool.category)
        target_count = int(job.target_sample_size * pool_percentage / 100)
        
        # Get sampling strategy for this category
        strategy = self._get_sampling_strategy(pool.category)
        
        # Select candidates
        if strategy == SamplingStrategy.CLUSTER:
            selected_ids = await self._cluster_based_selection(pool, target_count)
        elif strategy == SamplingStrategy.SYSTEMATIC:
            selected_ids = self._systematic_selection(pool, target_count)
        else:
            selected_ids = self._random_selection(pool, target_count)
        
        # Create sample records
        samples = []
        for i, candidate_id in enumerate(selected_ids):
            # Get sample data (would fetch from actual source)
            sample_data = await self._fetch_sample_data(candidate_id)
            
            # Apply masking if needed
            masked_data = self._apply_security_masking(sample_data)
            
            # Calculate risk score
            risk_score = await self.risk_scorer.calculate_score(sample_data)
            
            sample = IntelligentSample(
                job_id=job.job_id,
                pool_id=pool.pool_id,
                record_identifier=candidate_id,
                record_data=masked_data,
                category=pool.category,
                selection_reason=self._generate_selection_reason(pool, sample_data),
                anomaly_types=sample_data.get('anomaly_types', []),
                anomaly_rules=sample_data.get('anomaly_rules', []),
                anomaly_score=sample_data.get('anomaly_score', 0.0),
                boundary_attributes=sample_data.get('boundary_attributes', {}),
                boundary_values=sample_data.get('boundary_values', {}),
                risk_score=risk_score,
                risk_factors=sample_data.get('risk_factors', {}),
                selection_strategy=strategy,
                selection_rank=i + 1,
                testing_priority=self._calculate_testing_priority(pool.category, risk_score),
                must_test=(pool.category == SampleCategory.HIGH_RISK and risk_score > 0.8)
            )
            samples.append(sample)
        
        # Save samples
        session.add_all(samples)
        await session.commit()
        
        return samples
    
    def _get_pool_percentage(self, job: IntelligentSamplingJob, category: SampleCategory) -> int:
        """Get percentage allocation for pool category"""
        if category == SampleCategory.NORMAL:
            return job.normal_percentage
        elif category == SampleCategory.ANOMALY:
            return job.anomaly_percentage
        elif category in [SampleCategory.BOUNDARY_HIGH, SampleCategory.BOUNDARY_LOW]:
            return job.boundary_percentage // 2  # Split between high and low
        elif category in [SampleCategory.OUTLIER, SampleCategory.EDGE_CASE, SampleCategory.HIGH_RISK]:
            return job.edge_case_percentage // 3  # Split among edge cases
        return 0
    
    def _get_sampling_strategy(self, category: SampleCategory) -> SamplingStrategy:
        """Determine sampling strategy for category"""
        if category == SampleCategory.ANOMALY:
            return SamplingStrategy.ANOMALY_BASED
        elif category in [SampleCategory.BOUNDARY_HIGH, SampleCategory.BOUNDARY_LOW]:
            return SamplingStrategy.BOUNDARY
        elif category == SampleCategory.HIGH_RISK:
            return SamplingStrategy.RISK_BASED
        else:
            return SamplingStrategy.RANDOM
    
    async def _cluster_based_selection(
        self,
        pool: SamplePool,
        target_count: int
    ) -> List[str]:
        """Select samples using clustering"""
        # This would use actual data features for clustering
        # Placeholder implementation
        candidate_ids = pool.candidate_ids or []
        
        if len(candidate_ids) <= target_count:
            return candidate_ids
        
        # Simulate clustering selection
        # In practice, would use DBSCAN or K-means on actual features
        step = len(candidate_ids) // target_count
        return [candidate_ids[i] for i in range(0, len(candidate_ids), step)][:target_count]
    
    def _systematic_selection(self, pool: SamplePool, target_count: int) -> List[str]:
        """Select every nth sample systematically"""
        candidate_ids = pool.candidate_ids or []
        
        if len(candidate_ids) <= target_count:
            return candidate_ids
        
        step = len(candidate_ids) // target_count
        return [candidate_ids[i] for i in range(0, len(candidate_ids), step)][:target_count]
    
    def _random_selection(self, pool: SamplePool, target_count: int) -> List[str]:
        """Random selection from pool"""
        import random
        
        candidate_ids = pool.candidate_ids or []
        
        if len(candidate_ids) <= target_count:
            return candidate_ids
        
        return random.sample(candidate_ids, target_count)
    
    async def _fetch_sample_data(self, candidate_id: str) -> Dict[str, Any]:
        """Fetch actual sample data"""
        # This would query the actual data source
        # Placeholder implementation
        return {
            'id': candidate_id,
            'customer_id': f"CUST_{candidate_id}",
            'amount': 1000.0,
            'date': datetime.utcnow().isoformat(),
            'anomaly_types': [],
            'risk_factors': {}
        }
    
    def _apply_security_masking(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply security masking to sensitive fields"""
        sensitive_fields = ['ssn', 'ein', 'account_number']
        field_types = {
            'ssn': 'ssn',
            'ein': 'ein',
            'account_number': 'account'
        }
        
        return self.masking_service.mask_dict(data, sensitive_fields, field_types)
    
    def _generate_selection_reason(self, pool: SamplePool, sample_data: Dict[str, Any]) -> str:
        """Generate explanation for why sample was selected"""
        reasons = []
        
        if pool.category == SampleCategory.ANOMALY:
            reasons.append(f"Failed {len(sample_data.get('anomaly_rules', []))} profiling rules")
        elif pool.category == SampleCategory.BOUNDARY_HIGH:
            reasons.append("Contains boundary high values")
        elif pool.category == SampleCategory.HIGH_RISK:
            reasons.append("Identified as high-risk transaction")
        else:
            reasons.append("Selected for baseline comparison")
        
        if pool.selection_criteria:
            reasons.append(f"Matches criteria: {pool.selection_criteria}")
        
        return "; ".join(reasons)
    
    def _calculate_testing_priority(self, category: SampleCategory, risk_score: float) -> int:
        """Calculate testing priority (1-10)"""
        base_priority = {
            SampleCategory.HIGH_RISK: 8,
            SampleCategory.ANOMALY: 7,
            SampleCategory.BOUNDARY_HIGH: 6,
            SampleCategory.BOUNDARY_LOW: 6,
            SampleCategory.OUTLIER: 5,
            SampleCategory.EDGE_CASE: 5,
            SampleCategory.NORMAL: 3
        }
        
        priority = base_priority.get(category, 3)
        
        # Adjust based on risk score
        if risk_score > 0.8:
            priority = min(priority + 2, 10)
        elif risk_score > 0.6:
            priority = min(priority + 1, 10)
        
        return priority
    
    async def _calculate_quality_score(self, samples: List[IntelligentSample]) -> float:
        """Calculate overall quality score for sample selection"""
        if not samples:
            return 0.0
        
        # Factors for quality score
        diversity_score = self._calculate_diversity(samples)
        coverage_score = self._calculate_coverage(samples)
        risk_coverage = self._calculate_risk_coverage(samples)
        
        # Weighted average
        quality_score = (
            diversity_score * 0.3 +
            coverage_score * 0.4 +
            risk_coverage * 0.3
        )
        
        return round(quality_score, 2)
    
    def _calculate_diversity(self, samples: List[IntelligentSample]) -> float:
        """Calculate diversity of selected samples"""
        categories = set(s.category for s in samples)
        strategies = set(s.selection_strategy for s in samples)
        
        category_diversity = len(categories) / len(SampleCategory)
        strategy_diversity = len(strategies) / len(SamplingStrategy)
        
        return (category_diversity + strategy_diversity) / 2
    
    def _calculate_coverage(self, samples: List[IntelligentSample]) -> float:
        """Calculate coverage of different scenarios"""
        # Check coverage of different aspects
        has_anomalies = any(s.category == SampleCategory.ANOMALY for s in samples)
        has_boundaries = any(s.category in [SampleCategory.BOUNDARY_HIGH, SampleCategory.BOUNDARY_LOW] for s in samples)
        has_high_risk = any(s.category == SampleCategory.HIGH_RISK for s in samples)
        has_normal = any(s.category == SampleCategory.NORMAL for s in samples)
        
        coverage_count = sum([has_anomalies, has_boundaries, has_high_risk, has_normal])
        
        return coverage_count / 4
    
    def _calculate_risk_coverage(self, samples: List[IntelligentSample]) -> float:
        """Calculate coverage of risk spectrum"""
        risk_scores = [s.risk_score for s in samples if s.risk_score is not None]
        
        if not risk_scores:
            return 0.5
        
        # Check if we have good distribution across risk levels
        low_risk = sum(1 for r in risk_scores if r < 0.3)
        medium_risk = sum(1 for r in risk_scores if 0.3 <= r < 0.7)
        high_risk = sum(1 for r in risk_scores if r >= 0.7)
        
        total = len(risk_scores)
        
        # Ideal would be some representation in each category
        has_low = low_risk > 0
        has_medium = medium_risk > 0
        has_high = high_risk > 0
        
        return sum([has_low, has_medium, has_high]) / 3


class AnomalyDetector:
    """Detects anomalies using statistical and ML methods"""
    
    def detect_outliers(self, data: pd.DataFrame, columns: List[str]) -> np.ndarray:
        """Detect outliers using multiple methods"""
        outlier_scores = np.zeros(len(data))
        
        for col in columns:
            if col in data.columns and pd.api.types.is_numeric_dtype(data[col]):
                # Z-score method
                z_scores = np.abs((data[col] - data[col].mean()) / data[col].std())
                outlier_scores += (z_scores > 3).astype(int)
                
                # IQR method
                Q1 = data[col].quantile(0.25)
                Q3 = data[col].quantile(0.75)
                IQR = Q3 - Q1
                outlier_scores += ((data[col] < (Q1 - 1.5 * IQR)) | 
                                 (data[col] > (Q3 + 1.5 * IQR))).astype(int)
        
        return outlier_scores / (len(columns) * 2)  # Normalize


class RiskScorer:
    """Calculates risk scores for samples"""
    
    async def calculate_score(self, sample_data: Dict[str, Any]) -> float:
        """Calculate risk score for a sample"""
        risk_factors = []
        
        # Amount-based risk
        amount = sample_data.get('amount', 0)
        if amount > 100000:
            risk_factors.append(0.3)
        elif amount > 50000:
            risk_factors.append(0.2)
        elif amount > 10000:
            risk_factors.append(0.1)
        
        # Pattern-based risk
        if sample_data.get('unusual_pattern'):
            risk_factors.append(0.2)
        
        # Time-based risk
        if sample_data.get('off_hours_transaction'):
            risk_factors.append(0.1)
        
        # Regulatory risk
        if sample_data.get('regulatory_flag'):
            risk_factors.append(0.3)
        
        # Combine risk factors
        if not risk_factors:
            return 0.0
        
        # Use weighted combination
        return min(sum(risk_factors), 1.0)