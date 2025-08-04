"""
Sample Selection Service with Version Management
Follows the established versioning framework patterns
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import uuid
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc, asc
from sqlalchemy.orm import selectinload, joinedload

from app.models.sample_selection import (
    SampleSelectionVersion, SampleSelectionSample,
    VersionStatus, SampleCategory, SampleDecision, SampleSource
)
from app.models.workflow import WorkflowPhase
from app.models.user import User
from app.models.lob import LOB
from app.services.base_service import BaseService
from app.services.intelligent_sampling_service import IntelligentSamplingService
from app.core.exceptions import ValidationError, NotFoundError, BusinessLogicError

logger = logging.getLogger(__name__)


class SampleSelectionService(BaseService[SampleSelectionVersion]):
    """Service for managing sample selection versions and samples"""
    
    def __init__(self, intelligent_sampling_service: Optional[IntelligentSamplingService] = None):
        super().__init__(SampleSelectionVersion)
        self.intelligent_sampling_service = intelligent_sampling_service or IntelligentSamplingService()
    
    async def create_version(
        self,
        db: AsyncSession,
        phase_id: int,
        selection_criteria: Dict[str, Any],
        target_sample_size: int,
        workflow_execution_id: str,
        workflow_run_id: str,
        activity_name: str,
        created_by_id: int,
        intelligent_sampling_config: Optional[Dict[str, Any]] = None,
        data_source_config: Optional[Dict[str, Any]] = None
    ) -> SampleSelectionVersion:
        """Create a new sample selection version"""
        try:
            # Validate phase exists
            phase = await db.get(WorkflowPhase, phase_id)
            if not phase:
                raise NotFoundError(f"WorkflowPhase with id {phase_id} not found")
            
            # Get next version number
            version_number = await self._get_next_version_number(db, phase_id)
            
            # Create version
            version = SampleSelectionVersion(
                version_id=uuid.uuid4(),
                phase_id=phase_id,
                version_number=version_number,
                version_status=VersionStatus.DRAFT,
                workflow_execution_id=workflow_execution_id,
                workflow_run_id=workflow_run_id,
                activity_name=activity_name,
                selection_criteria=selection_criteria,
                target_sample_size=target_sample_size,
                actual_sample_size=0,
                intelligent_sampling_config=intelligent_sampling_config,
                data_source_config=data_source_config,
                created_by_id=created_by_id
            )
            
            db.add(version)
            await db.commit()
            await db.refresh(version)
            
            logger.info(f"Created sample selection version {version.version_id} for phase {phase_id}")
            return version
            
        except Exception as e:
            logger.error(f"Failed to create sample selection version: {str(e)}")
            await db.rollback()
            raise BusinessLogicError(f"Failed to create version: {str(e)}")
    
    async def get_version_by_id(
        self,
        db: AsyncSession,
        version_id: uuid.UUID,
        include_samples: bool = False
    ) -> Optional[SampleSelectionVersion]:
        """Get version by ID with optional samples"""
        try:
            query = select(SampleSelectionVersion).where(
                SampleSelectionVersion.version_id == version_id
            )
            
            if include_samples:
                query = query.options(
                    selectinload(SampleSelectionVersion.samples)
                    .selectinload(SampleSelectionSample.lob)
                )
            
            result = await db.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Failed to get version {version_id}: {str(e)}")
            raise BusinessLogicError(f"Failed to get version: {str(e)}")
    
    async def get_current_version(
        self,
        db: AsyncSession,
        phase_id: int,
        include_samples: bool = False
    ) -> Optional[SampleSelectionVersion]:
        """Get current version for a phase"""
        try:
            query = select(SampleSelectionVersion).where(
                and_(
                    SampleSelectionVersion.phase_id == phase_id,
                    SampleSelectionVersion.version_status.in_([
                        VersionStatus.APPROVED, 
                        VersionStatus.PENDING_APPROVAL
                    ])
                )
            ).order_by(desc(SampleSelectionVersion.version_number))
            
            if include_samples:
                query = query.options(
                    selectinload(SampleSelectionVersion.samples)
                    .selectinload(SampleSelectionSample.lob)
                )
            
            result = await db.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Failed to get current version for phase {phase_id}: {str(e)}")
            raise BusinessLogicError(f"Failed to get current version: {str(e)}")
    
    async def get_versions_by_phase(
        self,
        db: AsyncSession,
        phase_id: int,
        include_samples: bool = False
    ) -> List[SampleSelectionVersion]:
        """Get all versions for a phase"""
        try:
            query = select(SampleSelectionVersion).where(
                SampleSelectionVersion.phase_id == phase_id
            ).order_by(desc(SampleSelectionVersion.version_number))
            
            if include_samples:
                query = query.options(
                    selectinload(SampleSelectionVersion.samples)
                    .selectinload(SampleSelectionSample.lob)
                )
            
            result = await db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Failed to get versions for phase {phase_id}: {str(e)}")
            raise BusinessLogicError(f"Failed to get versions: {str(e)}")
    
    async def add_samples_to_version(
        self,
        db: AsyncSession,
        version_id: uuid.UUID,
        samples_data: List[Dict[str, Any]],
        current_user_id: int
    ) -> List[SampleSelectionSample]:
        """Add samples to a version"""
        try:
            # Get version and validate it's editable
            version = await self.get_version_by_id(db, version_id)
            if not version:
                raise NotFoundError(f"Version {version_id} not found")
            
            if not version.can_be_edited:
                raise ValidationError(f"Version {version_id} is not editable (status: {version.version_status})")
            
            # Create samples
            samples = []
            for sample_data in samples_data:
                sample = SampleSelectionSample(
                    sample_id=uuid.uuid4(),
                    version_id=version_id,
                    phase_id=version.phase_id,
                    lob_id=sample_data['lob_id'],
                    sample_identifier=sample_data['sample_identifier'],
                    sample_data=sample_data['sample_data'],
                    sample_category=SampleCategory(sample_data['sample_category']),
                    sample_source=SampleSource(sample_data.get('sample_source', SampleSource.MANUAL)),
                    risk_score=sample_data.get('risk_score'),
                    confidence_score=sample_data.get('confidence_score'),
                    generation_metadata=sample_data.get('generation_metadata'),
                    validation_results=sample_data.get('validation_results'),
                    carried_from_version_id=sample_data.get('carried_from_version_id'),
                    carried_from_sample_id=sample_data.get('carried_from_sample_id'),
                    carry_forward_reason=sample_data.get('carry_forward_reason')
                )
                samples.append(sample)
            
            db.add_all(samples)
            
            # Update version metrics
            version.actual_sample_size = await self._get_sample_count(db, version_id)
            version.distribution_metrics = await self._calculate_distribution_metrics(db, version_id)
            
            await db.commit()
            
            # Refresh samples with relationships
            for sample in samples:
                await db.refresh(sample)
            
            logger.info(f"Added {len(samples)} samples to version {version_id}")
            return samples
            
        except Exception as e:
            logger.error(f"Failed to add samples to version {version_id}: {str(e)}")
            await db.rollback()
            raise BusinessLogicError(f"Failed to add samples: {str(e)}")
    
    async def generate_intelligent_samples(
        self,
        db: AsyncSession,
        version_id: uuid.UUID,
        target_distribution: Optional[Dict[str, int]] = None,
        profiling_rules: Optional[List[Dict[str, Any]]] = None
    ) -> List[SampleSelectionSample]:
        """Generate intelligent samples with 30/50/20 distribution"""
        try:
            # Get version
            version = await self.get_version_by_id(db, version_id)
            if not version:
                raise NotFoundError(f"Version {version_id} not found")
            
            if not version.can_be_edited:
                raise ValidationError(f"Version {version_id} is not editable")
            
            # Default distribution: 30% clean, 50% anomaly, 20% boundary
            if not target_distribution:
                target_distribution = {
                    'clean': int(version.target_sample_size * 0.3),
                    'anomaly': int(version.target_sample_size * 0.5),
                    'boundary': int(version.target_sample_size * 0.2)
                }
            
            # Generate samples by category
            all_samples = []
            
            # Generate clean samples
            clean_samples = await self._generate_clean_samples(
                db, version, target_distribution['clean']
            )
            all_samples.extend(clean_samples)
            
            # Generate anomaly samples
            anomaly_samples = await self._generate_anomaly_samples(
                db, version, target_distribution['anomaly'], profiling_rules
            )
            all_samples.extend(anomaly_samples)
            
            # Generate boundary samples
            boundary_samples = await self._generate_boundary_samples(
                db, version, target_distribution['boundary']
            )
            all_samples.extend(boundary_samples)
            
            # Save samples
            db.add_all(all_samples)
            
            # Update version metrics
            version.actual_sample_size = len(all_samples)
            version.distribution_metrics = await self._calculate_distribution_metrics(db, version_id)
            
            await db.commit()
            
            # Refresh samples
            for sample in all_samples:
                await db.refresh(sample)
            
            logger.info(f"Generated {len(all_samples)} intelligent samples for version {version_id}")
            return all_samples
            
        except Exception as e:
            logger.error(f"Failed to generate intelligent samples: {str(e)}")
            await db.rollback()
            raise BusinessLogicError(f"Failed to generate samples: {str(e)}")
    
    async def carry_forward_samples(
        self,
        db: AsyncSession,
        source_version_id: uuid.UUID,
        target_version_id: uuid.UUID,
        sample_filters: Optional[Dict[str, Any]] = None
    ) -> List[SampleSelectionSample]:
        """Carry forward approved samples from source to target version"""
        try:
            # Get source and target versions
            source_version = await self.get_version_by_id(db, source_version_id, include_samples=True)
            target_version = await self.get_version_by_id(db, target_version_id)
            
            if not source_version:
                raise NotFoundError(f"Source version {source_version_id} not found")
            if not target_version:
                raise NotFoundError(f"Target version {target_version_id} not found")
            
            if not target_version.can_be_edited:
                raise ValidationError(f"Target version {target_version_id} is not editable")
            
            # Get approved samples from source
            approved_samples = [
                sample for sample in source_version.samples
                if sample.is_approved and self._matches_filters(sample, sample_filters)
            ]
            
            # Create carried forward samples
            carried_samples = []
            for source_sample in approved_samples:
                carried_sample = SampleSelectionSample(
                    sample_id=uuid.uuid4(),
                    version_id=target_version_id,
                    phase_id=target_version.phase_id,
                    lob_id=source_sample.lob_id,
                    sample_identifier=source_sample.sample_identifier,
                    sample_data=source_sample.sample_data,
                    sample_category=source_sample.sample_category,
                    sample_source=SampleSource.CARRIED_FORWARD,
                    risk_score=source_sample.risk_score,
                    confidence_score=source_sample.confidence_score,
                    generation_metadata=source_sample.generation_metadata,
                    validation_results=source_sample.validation_results,
                    carried_from_version_id=source_version_id,
                    carried_from_sample_id=source_sample.sample_id,
                    carry_forward_reason=f"Carried forward from version {source_version.version_number}",
                    # Auto-approve carried forward samples
                    tester_decision=SampleDecision.INCLUDE,
                    tester_decision_notes="Auto-approved (carried forward)",
                    tester_decision_at=datetime.utcnow(),
                    report_owner_decision=SampleDecision.INCLUDE,
                    report_owner_decision_notes="Auto-approved (carried forward)",
                    report_owner_decision_at=datetime.utcnow()
                )
                carried_samples.append(carried_sample)
            
            # Save samples
            db.add_all(carried_samples)
            
            # Update target version metrics
            target_version.actual_sample_size = await self._get_sample_count(db, target_version_id)
            target_version.distribution_metrics = await self._calculate_distribution_metrics(db, target_version_id)
            
            await db.commit()
            
            # Refresh samples
            for sample in carried_samples:
                await db.refresh(sample)
            
            logger.info(f"Carried forward {len(carried_samples)} samples from version {source_version_id} to {target_version_id}")
            return carried_samples
            
        except Exception as e:
            logger.error(f"Failed to carry forward samples: {str(e)}")
            await db.rollback()
            raise BusinessLogicError(f"Failed to carry forward samples: {str(e)}")
    
    async def submit_for_approval(
        self,
        db: AsyncSession,
        version_id: uuid.UUID,
        submitted_by_id: int,
        submission_notes: Optional[str] = None
    ) -> SampleSelectionVersion:
        """Submit version for report owner approval"""
        try:
            version = await self.get_version_by_id(db, version_id)
            if not version:
                raise NotFoundError(f"Version {version_id} not found")
            
            if version.version_status != VersionStatus.DRAFT:
                raise ValidationError(f"Only draft versions can be submitted for approval")
            
            # Validate version has samples
            sample_count = await self._get_sample_count(db, version_id)
            if sample_count == 0:
                raise ValidationError("Cannot submit version with no samples")
            
            # Update version status
            version.version_status = VersionStatus.PENDING_APPROVAL
            version.submitted_at = datetime.utcnow()
            version.submitted_by_id = submitted_by_id
            version.submission_notes = submission_notes
            
            await db.commit()
            await db.refresh(version)
            
            logger.info(f"Submitted version {version_id} for approval")
            return version
            
        except Exception as e:
            logger.error(f"Failed to submit version for approval: {str(e)}")
            await db.rollback()
            raise BusinessLogicError(f"Failed to submit for approval: {str(e)}")
    
    async def approve_version(
        self,
        db: AsyncSession,
        version_id: uuid.UUID,
        approved_by_id: int,
        approval_notes: Optional[str] = None
    ) -> SampleSelectionVersion:
        """Approve a version (marks previous versions as superseded)"""
        try:
            version = await self.get_version_by_id(db, version_id)
            if not version:
                raise NotFoundError(f"Version {version_id} not found")
            
            if version.version_status != VersionStatus.PENDING_APPROVAL:
                raise ValidationError(f"Only pending approval versions can be approved")
            
            # Mark previous versions as superseded
            await self._supersede_previous_versions(db, version.phase_id, version.version_number)
            
            # Update version status
            version.version_status = VersionStatus.APPROVED
            version.approved_at = datetime.utcnow()
            version.approved_by_id = approved_by_id
            version.approval_notes = approval_notes
            
            await db.commit()
            await db.refresh(version)
            
            logger.info(f"Approved version {version_id}")
            return version
            
        except Exception as e:
            logger.error(f"Failed to approve version: {str(e)}")
            await db.rollback()
            raise BusinessLogicError(f"Failed to approve version: {str(e)}")
    
    async def reject_version(
        self,
        db: AsyncSession,
        version_id: uuid.UUID,
        rejected_by_id: int,
        rejection_notes: str
    ) -> SampleSelectionVersion:
        """Reject a version"""
        try:
            version = await self.get_version_by_id(db, version_id)
            if not version:
                raise NotFoundError(f"Version {version_id} not found")
            
            if version.version_status != VersionStatus.PENDING_APPROVAL:
                raise ValidationError(f"Only pending approval versions can be rejected")
            
            # Update version status
            version.version_status = VersionStatus.REJECTED
            version.approved_at = datetime.utcnow()
            version.approved_by_id = rejected_by_id
            version.approval_notes = rejection_notes
            
            await db.commit()
            await db.refresh(version)
            
            logger.info(f"Rejected version {version_id}")
            return version
            
        except Exception as e:
            logger.error(f"Failed to reject version: {str(e)}")
            await db.rollback()
            raise BusinessLogicError(f"Failed to reject version: {str(e)}")
    
    async def update_sample_decision(
        self,
        db: AsyncSession,
        sample_id: uuid.UUID,
        decision_type: str,  # 'tester' or 'report_owner'
        decision: SampleDecision,
        decision_notes: Optional[str],
        decided_by_id: int
    ) -> SampleSelectionSample:
        """Update sample decision"""
        try:
            sample = await db.get(SampleSelectionSample, sample_id)
            if not sample:
                raise NotFoundError(f"Sample {sample_id} not found")
            
            # Check if version is still editable
            version = await self.get_version_by_id(db, sample.version_id)
            if not version or not version.can_be_edited:
                raise ValidationError("Cannot update decisions on non-editable versions")
            
            # Update decision
            if decision_type == 'tester':
                sample.tester_decision = decision
                sample.tester_decision_notes = decision_notes
                sample.tester_decision_at = datetime.utcnow()
                sample.tester_decision_by_id = decided_by_id
            elif decision_type == 'report_owner':
                sample.report_owner_decision = decision
                sample.report_owner_decision_notes = decision_notes
                sample.report_owner_decision_at = datetime.utcnow()
                sample.report_owner_decision_by_id = decided_by_id
            else:
                raise ValidationError(f"Invalid decision type: {decision_type}")
            
            await db.commit()
            await db.refresh(sample)
            
            logger.info(f"Updated {decision_type} decision for sample {sample_id}")
            return sample
            
        except Exception as e:
            logger.error(f"Failed to update sample decision: {str(e)}")
            await db.rollback()
            raise BusinessLogicError(f"Failed to update sample decision: {str(e)}")
    
    async def get_version_statistics(
        self,
        db: AsyncSession,
        version_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Get comprehensive statistics for a version"""
        try:
            version = await self.get_version_by_id(db, version_id, include_samples=True)
            if not version:
                raise NotFoundError(f"Version {version_id} not found")
            
            samples = version.samples
            
            # Basic counts
            total_samples = len(samples)
            approved_samples = len([s for s in samples if s.is_approved])
            rejected_samples = len([s for s in samples if s.is_rejected])
            pending_samples = len([s for s in samples if s.needs_review])
            
            # Category distribution
            category_counts = {}
            for category in SampleCategory:
                category_counts[category.value] = len([s for s in samples if s.sample_category == category])
            
            # Source distribution
            source_counts = {}
            for source in SampleSource:
                source_counts[source.value] = len([s for s in samples if s.sample_source == source])
            
            # LOB distribution
            lob_counts = {}
            for sample in samples:
                lob_name = sample.lob.name if sample.lob else "Unknown"
                lob_counts[lob_name] = lob_counts.get(lob_name, 0) + 1
            
            # Decision statistics
            tester_decisions = {}
            report_owner_decisions = {}
            for decision in SampleDecision:
                tester_decisions[decision.value] = len([s for s in samples if s.tester_decision == decision])
                report_owner_decisions[decision.value] = len([s for s in samples if s.report_owner_decision == decision])
            
            # Risk score statistics
            risk_scores = [s.risk_score for s in samples if s.risk_score is not None]
            risk_stats = {}
            if risk_scores:
                risk_stats = {
                    'min': min(risk_scores),
                    'max': max(risk_scores),
                    'avg': sum(risk_scores) / len(risk_scores),
                    'high_risk_count': len([r for r in risk_scores if r > 0.7])
                }
            
            return {
                'version_info': version.get_metadata(),
                'sample_counts': {
                    'total': total_samples,
                    'approved': approved_samples,
                    'rejected': rejected_samples,
                    'pending': pending_samples,
                    'approval_rate': approved_samples / total_samples if total_samples > 0 else 0
                },
                'category_distribution': category_counts,
                'source_distribution': source_counts,
                'lob_distribution': lob_counts,
                'decision_statistics': {
                    'tester_decisions': tester_decisions,
                    'report_owner_decisions': report_owner_decisions
                },
                'risk_statistics': risk_stats
            }
            
        except Exception as e:
            logger.error(f"Failed to get version statistics: {str(e)}")
            raise BusinessLogicError(f"Failed to get statistics: {str(e)}")
    
    # Private helper methods
    
    async def _get_next_version_number(self, db: AsyncSession, phase_id: int) -> int:
        """Get next version number for a phase"""
        result = await db.execute(
            select(func.max(SampleSelectionVersion.version_number))
            .where(SampleSelectionVersion.phase_id == phase_id)
        )
        max_version = result.scalar_one_or_none()
        return (max_version or 0) + 1
    
    async def _get_sample_count(self, db: AsyncSession, version_id: uuid.UUID) -> int:
        """Get sample count for a version"""
        result = await db.execute(
            select(func.count(SampleSelectionSample.sample_id))
            .where(SampleSelectionSample.version_id == version_id)
        )
        return result.scalar_one()
    
    async def _calculate_distribution_metrics(self, db: AsyncSession, version_id: uuid.UUID) -> Dict[str, Any]:
        """Calculate distribution metrics for a version"""
        result = await db.execute(
            select(
                SampleSelectionSample.sample_category,
                func.count(SampleSelectionSample.sample_id).label('count')
            )
            .where(SampleSelectionSample.version_id == version_id)
            .group_by(SampleSelectionSample.sample_category)
        )
        
        distribution = {}
        total = 0
        for category, count in result.fetchall():
            distribution[category.value] = count
            total += count
        
        # Calculate percentages
        percentages = {}
        for category, count in distribution.items():
            percentages[category] = (count / total * 100) if total > 0 else 0
        
        return {
            'category_distribution': distribution,
            'category_percentages': percentages,
            'total_samples': total
        }
    
    async def _supersede_previous_versions(self, db: AsyncSession, phase_id: int, current_version_number: int):
        """Mark previous versions as superseded"""
        await db.execute(
            SampleSelectionVersion.__table__.update()
            .where(
                and_(
                    SampleSelectionVersion.phase_id == phase_id,
                    SampleSelectionVersion.version_number < current_version_number,
                    SampleSelectionVersion.version_status == VersionStatus.APPROVED
                )
            )
            .values(version_status=VersionStatus.SUPERSEDED)
        )
    
    async def _generate_clean_samples(
        self,
        db: AsyncSession,
        version: SampleSelectionVersion,
        target_count: int
    ) -> List[SampleSelectionSample]:
        """Generate clean samples (30% of distribution)"""
        # This would integrate with data source to get clean samples
        # For now, create mock samples
        samples = []
        for i in range(target_count):
            sample = SampleSelectionSample(
                sample_id=uuid.uuid4(),
                version_id=version.version_id,
                phase_id=version.phase_id,
                lob_id=1,  # Default LOB, would be determined by data source
                sample_identifier=f"CLEAN_{i+1:04d}",
                sample_data={
                    'type': 'clean',
                    'generated_at': datetime.utcnow().isoformat(),
                    'criteria': 'no_anomalies_detected'
                },
                sample_category=SampleCategory.CLEAN,
                sample_source=SampleSource.LLM,
                risk_score=0.1,
                confidence_score=0.9,
                generation_metadata={
                    'method': 'intelligent_sampling',
                    'distribution_type': 'clean'
                }
            )
            samples.append(sample)
        
        return samples
    
    async def _generate_anomaly_samples(
        self,
        db: AsyncSession,
        version: SampleSelectionVersion,
        target_count: int,
        profiling_rules: Optional[List[Dict[str, Any]]] = None
    ) -> List[SampleSelectionSample]:
        """Generate anomaly samples (50% of distribution)"""
        # This would integrate with profiling service to get anomaly samples
        # For now, create mock samples
        samples = []
        for i in range(target_count):
            sample = SampleSelectionSample(
                sample_id=uuid.uuid4(),
                version_id=version.version_id,
                phase_id=version.phase_id,
                lob_id=1,  # Default LOB
                sample_identifier=f"ANOMALY_{i+1:04d}",
                sample_data={
                    'type': 'anomaly',
                    'generated_at': datetime.utcnow().isoformat(),
                    'anomaly_types': ['statistical_outlier', 'pattern_deviation'],
                    'failed_rules': ['rule_1', 'rule_2']
                },
                sample_category=SampleCategory.ANOMALY,
                sample_source=SampleSource.LLM,
                risk_score=0.8,
                confidence_score=0.85,
                generation_metadata={
                    'method': 'intelligent_sampling',
                    'distribution_type': 'anomaly',
                    'profiling_rules_applied': len(profiling_rules) if profiling_rules else 0
                }
            )
            samples.append(sample)
        
        return samples
    
    async def _generate_boundary_samples(
        self,
        db: AsyncSession,
        version: SampleSelectionVersion,
        target_count: int
    ) -> List[SampleSelectionSample]:
        """Generate boundary samples (20% of distribution)"""
        # This would integrate with data source to get boundary samples
        # For now, create mock samples
        samples = []
        for i in range(target_count):
            sample = SampleSelectionSample(
                sample_id=uuid.uuid4(),
                version_id=version.version_id,
                phase_id=version.phase_id,
                lob_id=1,  # Default LOB
                sample_identifier=f"BOUNDARY_{i+1:04d}",
                sample_data={
                    'type': 'boundary',
                    'generated_at': datetime.utcnow().isoformat(),
                    'boundary_type': 'high_value' if i % 2 == 0 else 'low_value',
                    'boundary_attributes': ['amount', 'balance']
                },
                sample_category=SampleCategory.BOUNDARY,
                sample_source=SampleSource.LLM,
                risk_score=0.6,
                confidence_score=0.8,
                generation_metadata={
                    'method': 'intelligent_sampling',
                    'distribution_type': 'boundary'
                }
            )
            samples.append(sample)
        
        return samples
    
    def _matches_filters(self, sample: SampleSelectionSample, filters: Optional[Dict[str, Any]]) -> bool:
        """Check if sample matches carry-forward filters"""
        if not filters:
            return True
        
        # Apply filters
        if 'categories' in filters:
            if sample.sample_category not in filters['categories']:
                return False
        
        if 'min_risk_score' in filters:
            if sample.risk_score is None or sample.risk_score < filters['min_risk_score']:
                return False
        
        if 'lob_ids' in filters:
            if sample.lob_id not in filters['lob_ids']:
                return False
        
        return True