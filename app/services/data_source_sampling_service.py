"""
Data Source Sampling Service
Generates samples from database or file data sources
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging
import uuid
import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, and_
from sqlalchemy.orm import selectinload
import pandas as pd

from app.models.sample_selection import SampleSelectionVersion, SampleSelectionSample
from app.models.workflow import WorkflowPhase
from app.models.cycle_report_data_source import CycleReportDataSource
from app.core.background_jobs import job_manager
from app.core.exceptions import BusinessLogicError
from app.services.data_source_query_service import DataSourceQueryService
from app.services.sample_selection_table_service import SampleSelectionTableService

logger = logging.getLogger(__name__)


class DataSourceSamplingService:
    """Service for generating samples from data sources"""
    
    def __init__(self):
        self.query_service = DataSourceQueryService()
        self.table_service = SampleSelectionTableService()
    
    async def generate_samples_from_data_source(
        self,
        db: AsyncSession,
        cycle_id: int,
        report_id: int,
        phase_id: int,
        target_sample_size: int,
        scoped_attributes: List[Dict[str, Any]],
        data_source_config: Dict[str, Any],
        distribution: Optional[Dict[str, float]] = None,
        profiling_rules: Optional[List[Any]] = None,
        job_id: Optional[str] = None,
        current_user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate samples from configured data source
        
        Args:
            db: Database session
            cycle_id: Cycle ID
            report_id: Report ID
            phase_id: Phase ID
            target_sample_size: Number of samples to generate
            scoped_attributes: List of scoped attributes
            data_source_config: Data source configuration
            distribution: Optional distribution ratios
            profiling_rules: Optional list of profiling rules to factor in
            job_id: Background job ID
            current_user_id: Current user ID
            
        Returns:
            Dict with samples and generation summary
        """
        try:
            logger.info(f"Generating {target_sample_size} samples from data source for cycle {cycle_id}, report {report_id}")
            
            # Default distribution if not provided
            if not distribution:
                distribution = {
                    "clean": 0.3,
                    "anomaly": 0.5,
                    "boundary": 0.2
                }
            
            # Get or create version
            version = await self.table_service.get_or_create_version(db, phase_id, current_user_id or 1)
            
            # Update job progress
            if job_id:
                job_manager.update_job_progress(
                    job_id,
                    current_step="Connecting to data source",
                    progress_percentage=40
                )
            
            samples_created = []
            
            # Handle different data source types
            if data_source_config.get('type') == 'file':
                # Handle uploaded file samples
                uploaded_samples = data_source_config.get('uploaded_samples', [])
                logger.info(f"Using {len(uploaded_samples)} uploaded samples")
                
                for idx, sample_data in enumerate(uploaded_samples[:target_sample_size]):
                    samples_created.append({
                        'sample_number': idx + 1,
                        # Don't auto-assign LOB - let tester assign it
                        'primary_attribute_value': sample_data.get('primary_attribute_value', f'SAMPLE_{idx+1}'),
                        'data_row_snapshot': sample_data.get('data_row_snapshot', {}),
                        'sample_category': 'clean',  # Default for uploaded samples
                        'sample_source': 'manual',
                        'generation_method': 'File Upload',
                        'metadata': {
                            'source': 'uploaded_file',
                            'original_index': idx
                        }
                    })
                    
            elif data_source_config.get('type') == 'database':
                # Generate samples from database
                criteria = data_source_config.get('criteria', {})
                
                if job_id:
                    job_manager.update_job_progress(
                        job_id,
                        current_step="Querying database for samples",
                        progress_percentage=50
                    )
                
                # Build query to get random samples
                table_name = criteria.get('table_name')
                schema_name = criteria.get('schema_name', 'public')
                database_name = criteria.get('database_name')
                
                if not table_name:
                    raise BusinessLogicError("Table name not specified in data source configuration")
                
                # Check if we should use intelligent sampling
                # Use intelligent sampling if we have non-PK attributes
                non_pk_attrs = [attr for attr in scoped_attributes if not attr.get('is_primary_key')]
                if len(non_pk_attrs) >= 1:
                    # Select target attribute for intelligent sampling
                    # Priority: numeric non-PK attributes, then any non-PK attribute
                    target_attribute = None
                    
                    # First try to find a numeric non-PK attribute
                    numeric_attrs = [attr for attr in non_pk_attrs 
                                   if attr.get('data_type', '').lower() in ['numeric', 'integer', 'decimal', 'float', 'double', 'bigint', 'int']]
                    
                    if numeric_attrs:
                        # Prefer the first numeric attribute
                        target_attribute = numeric_attrs[0]['attribute_name']
                    else:
                        # Fall back to first non-PK attribute
                        target_attribute = non_pk_attrs[0]['attribute_name']
                    
                    logger.info(f"Selected target attribute for intelligent sampling: {target_attribute}")
                    
                    from app.services.intelligent_data_sampling_service import IntelligentDataSamplingService
                    intelligent_service = IntelligentDataSamplingService()
                    
                    # Get PDE mappings first
                    pde_mappings = await self._get_pde_mappings(db, cycle_id, report_id)
                    
                    result = await intelligent_service.generate_intelligent_samples(
                        db=db,
                        cycle_id=cycle_id,
                        report_id=report_id,
                        phase_id=phase_id,
                        target_attribute=target_attribute,
                        target_sample_size=target_sample_size,
                        scoped_attributes=scoped_attributes,
                        data_source_config=data_source_config,
                        pde_mappings=pde_mappings,
                        distribution=distribution,
                        profiling_rules=profiling_rules,
                        job_id=job_id,
                        current_user_id=current_user_id
                    )
                    
                    return result
                
                # Get report LOB once
                from app.models.report import Report
                report_result = await db.execute(
                    select(Report).options(selectinload(Report.lob)).where(Report.report_id == report_id)
                )
                report = report_result.scalar_one_or_none()
                lob_name = report.lob.lob_name if report and report.lob else 'General'
                
                # Get primary key attributes
                pk_attributes = [attr for attr in scoped_attributes if attr.get('is_primary_key')]
                if not pk_attributes:
                    # Use first attribute as identifier if no PK
                    pk_attributes = scoped_attributes[:1] if scoped_attributes else []
                
                # Get PDE mappings to get actual column names
                from app.models.planning import PlanningPDEMapping
                from app.models.report_attribute import ReportAttribute
                
                # Get planning phase
                planning_phase_result = await db.execute(
                    select(WorkflowPhase).where(
                        and_(
                            WorkflowPhase.cycle_id == cycle_id,
                            WorkflowPhase.report_id == report_id,
                            WorkflowPhase.phase_name == "Planning"
                        )
                    )
                )
                planning_phase = planning_phase_result.scalar_one_or_none()
                
                # Get PDE mappings for the attributes
                pde_mappings = {}
                if planning_phase and planning_phase.phase_id:
                    pde_result = await db.execute(
                        select(PlanningPDEMapping).where(
                            PlanningPDEMapping.phase_id == planning_phase.phase_id
                        )
                    )
                    pde_mappings_list = pde_result.scalars().all()
                    
                    # Create mapping from attribute_name to pde_code (column name)
                    # First get attribute id to name mapping
                    attr_id_to_name = {}
                    attr_result = await db.execute(
                        select(ReportAttribute).where(
                            ReportAttribute.phase_id == planning_phase.phase_id
                        )
                    )
                    attrs = attr_result.scalars().all()
                    for attr in attrs:
                        attr_id_to_name[attr.id] = attr.attribute_name
                    
                    # Now map attribute names to pde_codes
                    for mapping in pde_mappings_list:
                        attr_name = attr_id_to_name.get(mapping.attribute_id)
                        if attr_name:
                            pde_mappings[attr_name] = mapping.pde_code
                
                # Build column list using PDE codes (actual column names)
                columns = []
                for attr in scoped_attributes:
                    attr_name = attr['attribute_name']
                    column_name = pde_mappings.get(attr_name, attr_name)  # Use PDE code if available
                    columns.append(column_name)
                
                if not columns:
                    columns = ['*']
                
                # Calculate samples per category
                samples_per_category = {
                    'clean': int(target_sample_size * distribution.get('clean', 0.3)),
                    'anomaly': int(target_sample_size * distribution.get('anomaly', 0.5)),
                    'boundary': int(target_sample_size * distribution.get('boundary', 0.2))
                }
                
                # Ensure we generate exactly target_sample_size
                total_planned = sum(samples_per_category.values())
                if total_planned < target_sample_size:
                    samples_per_category['anomaly'] += target_sample_size - total_planned
                
                sample_number = 1
                
                # Generate samples for each category
                for category, count in samples_per_category.items():
                    if count == 0:
                        continue
                    
                    # Build sampling query
                    # Using TABLESAMPLE for efficient random sampling
                    query = f"""
                        SELECT {', '.join(columns)}
                        FROM {schema_name}.{table_name}
                        TABLESAMPLE SYSTEM (10)
                        ORDER BY RANDOM()
                        LIMIT {count}
                    """
                    
                    try:
                        # Execute query
                        result = await db.execute(text(query))
                        rows = result.fetchall()
                        
                        logger.info(f"Retrieved {len(rows)} {category} samples from database")
                        
                        # Create reverse mapping from column names to attribute names
                        column_to_attr = {}
                        for attr in scoped_attributes:
                            attr_name = attr['attribute_name']
                            column_name = pde_mappings.get(attr_name, attr_name)
                            column_to_attr[column_name] = attr_name
                        
                        # Convert rows to samples
                        for row in rows:
                            # Create data snapshot using attribute names
                            data_snapshot = {}
                            for idx, col in enumerate(columns):
                                value = row[idx]
                                # Convert non-serializable types
                                if isinstance(value, datetime):
                                    value = value.isoformat()
                                elif hasattr(value, 'to_eng_string'):  # Decimal type
                                    value = str(value)
                                elif value is None:
                                    value = None
                                else:
                                    # Convert to string for safety
                                    value = str(value)
                                # Use attribute name as key in snapshot
                                attr_name = column_to_attr.get(col, col)
                                data_snapshot[attr_name] = value
                            
                            # Determine primary key value
                            pk_value = 'UNKNOWN'
                            if pk_attributes:
                                pk_attr = pk_attributes[0]['attribute_name']
                                pk_value = data_snapshot.get(pk_attr, f'SAMPLE_{sample_number}')
                            
                            samples_created.append({
                                'sample_number': sample_number,
                                # Don't auto-assign LOB - let tester assign it
                                'primary_attribute_value': str(pk_value),
                                'data_row_snapshot': data_snapshot,
                                'sample_category': category,
                                'sample_source': 'tester',
                                'generation_method': 'Database Query',
                                'risk_score': self._calculate_risk_score(category),
                                'confidence_score': 0.85,
                                'metadata': {
                                    'source': 'database',
                                    'table': f'{schema_name}.{table_name}',
                                    'category': category,
                                    'query_timestamp': datetime.utcnow().isoformat()
                                }
                            })
                            sample_number += 1
                            
                    except Exception as e:
                        logger.error(f"Error querying database for {category} samples: {str(e)}")
                        # Rollback the transaction to recover from error
                        await db.rollback()
                        # Continue with other categories
                        
            else:
                # Fallback: Generate mock samples if no data source
                logger.warning("No valid data source found, generating mock samples")
                
                for i in range(target_sample_size):
                    category = self._get_category_for_index(i, target_sample_size, distribution)
                    
                    samples_created.append({
                        'sample_number': i + 1,
                        # Don't auto-assign LOB - let tester assign it
                        'primary_attribute_value': f'SAMPLE_{i+1:04d}',
                        'data_row_snapshot': {
                            attr['attribute_name']: f'Value_{i+1}' 
                            for attr in scoped_attributes
                        },
                        'sample_category': category,
                        'sample_source': 'tester',
                        'generation_method': 'Mock Generation',
                        'risk_score': self._calculate_risk_score(category),
                        'confidence_score': 0.75,
                        'metadata': {
                            'source': 'mock',
                            'reason': 'No data source available'
                        }
                    })
            
            if job_id:
                job_manager.update_job_progress(
                    job_id,
                    current_step="Creating sample records",
                    progress_percentage=80
                )
            
            # Create sample records in database
            if samples_created and version:
                await self.table_service.create_samples_from_generation(
                    db, version.version_id, samples_created, current_user_id or 1
                )
            
            # Prepare result
            result = {
                'samples': samples_created,
                'generation_summary': {
                    'total_samples': len(samples_created),
                    'distribution_achieved': {
                        'clean': len([s for s in samples_created if s['sample_category'] == 'clean']),
                        'anomaly': len([s for s in samples_created if s['sample_category'] == 'anomaly']),
                        'boundary': len([s for s in samples_created if s['sample_category'] == 'boundary'])
                    },
                    'data_source': data_source_config.get('type', 'none'),
                    'generation_method': 'Data Source Sampling',
                    'timestamp': datetime.utcnow().isoformat()
                },
                'attribute_results': {
                    attr['attribute_name']: {
                        'samples_generated': len(samples_created),
                        'coverage': 100.0
                    }
                    for attr in scoped_attributes
                }
            }
            
            logger.info(f"Successfully generated {len(samples_created)} samples")
            return result
            
        except Exception as e:
            logger.error(f"Error generating samples from data source: {str(e)}", exc_info=True)
            raise BusinessLogicError(f"Failed to generate samples: {str(e)}")
    
    def _calculate_risk_score(self, category: str) -> float:
        """Calculate risk score based on category"""
        risk_scores = {
            'clean': 0.2,
            'anomaly': 0.8,
            'boundary': 0.5
        }
        return risk_scores.get(category, 0.5)
    
    def _get_category_for_index(self, index: int, total: int, distribution: Dict[str, float]) -> str:
        """Determine category for a given index based on distribution"""
        clean_count = int(total * distribution.get('clean', 0.3))
        anomaly_count = int(total * distribution.get('anomaly', 0.5))
        
        if index < clean_count:
            return 'clean'
        elif index < clean_count + anomaly_count:
            return 'anomaly'
        else:
            return 'boundary'
    
    async def _get_pde_mappings(self, db: AsyncSession, cycle_id: int, report_id: int) -> Dict[str, str]:
        """Get PDE mappings for attributes from planning phase"""
        from app.models.planning import PlanningPDEMapping
        from app.models.report_attribute import ReportAttribute
        
        # Get planning phase
        planning_phase_result = await db.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Planning"
                )
            )
        )
        planning_phase = planning_phase_result.scalar_one_or_none()
        
        pde_mappings = {}
        
        if planning_phase and planning_phase.phase_id:
            # Get PDE mappings
            pde_result = await db.execute(
                select(PlanningPDEMapping).where(
                    PlanningPDEMapping.phase_id == planning_phase.phase_id
                )
            )
            pde_mappings_list = pde_result.scalars().all()
            
            # Get attribute id to name mapping
            attr_id_to_name = {}
            attr_result = await db.execute(
                select(ReportAttribute).where(
                    ReportAttribute.phase_id == planning_phase.phase_id
                )
            )
            attrs = attr_result.scalars().all()
            for attr in attrs:
                attr_id_to_name[attr.id] = attr.attribute_name
            
            # Map attribute names to pde_codes (column names)
            for mapping in pde_mappings_list:
                attr_name = attr_id_to_name.get(mapping.attribute_id)
                if attr_name:
                    pde_mappings[attr_name] = mapping.pde_code
        
        return pde_mappings