"""
Background tasks for sample selection
Implements intelligent sampling with proper async patterns
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select, and_
from sqlalchemy.orm.attributes import flag_modified

from app.core.database import AsyncSessionLocal
from app.core.config import settings
from app.core.background_jobs import job_manager, BackgroundJobManager
from app.core.redis_job_manager import get_redis_job_manager, RedisJobManager
from app.core.exceptions import BusinessLogicError
from app.models.workflow import WorkflowPhase
from app.models.report_attribute import ReportAttribute
from app.models.cycle_report_data_source import CycleReportDataSource
from app.models.audit import LLMAuditLog
from app.services.sample_selection_table_service import SampleSelectionTableService
from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)


async def execute_intelligent_sampling_task(
    job_id: str,
    cycle_id: int,
    report_id: int,
    target_sample_size: int,
    use_data_source: bool,
    distribution: Optional[Dict[str, float]],
    include_file_samples: bool,
    current_user_id: int,
    current_user_name: str
) -> Dict[str, Any]:
    """
    Execute intelligent sampling in background task
    Applies all lessons learned from planning phase issues
    """
    logger.info(f"Starting intelligent sampling task {job_id} for cycle {cycle_id}, report {report_id}")
    
    try:
        # Create new session for async task (CRITICAL: Session management lesson)
        async with AsyncSessionLocal() as task_db:
            # Update job status to running (CRITICAL: Job status lesson)
            job_manager.update_job_progress(
                job_id,
                status="running",
                current_step="Loading phase data",
                progress_percentage=0
            )
            
            # Get workflow phase - reload in task session
            phase_query = await task_db.execute(
                select(WorkflowPhase).where(
                    and_(
                        WorkflowPhase.cycle_id == cycle_id,
                        WorkflowPhase.report_id == report_id,
                        WorkflowPhase.phase_name == "Sample Selection"
                    )
                )
            )
            phase = phase_query.scalar_one_or_none()
            
            if not phase:
                raise BusinessLogicError("Sample Selection phase not found")
            
            job_manager.update_job_progress(
                job_id,
                current_step="Loading data source configuration",
                progress_percentage=10
            )
            
            # Get planning phase to retrieve data source information
            planning_phase_query = await task_db.execute(
                select(WorkflowPhase).where(
                    and_(
                        WorkflowPhase.cycle_id == cycle_id,
                        WorkflowPhase.report_id == report_id,
                        WorkflowPhase.phase_name == "Planning"
                    )
                )
            )
            planning_phase = planning_phase_query.scalar_one_or_none()
            
            if not planning_phase:
                logger.warning(f"No planning phase found for cycle {cycle_id}, report {report_id}")
            
            # Get data source configuration from planning phase
            data_source_config = {}
            
            if use_data_source and planning_phase and planning_phase.phase_id:
                # Query data sources from planning phase
                data_sources_query = await task_db.execute(
                    select(CycleReportDataSource).where(
                        CycleReportDataSource.phase_id == planning_phase.phase_id
                    )
                )
                data_sources = data_sources_query.scalars().all()
                
                if data_sources:
                    # Use the first data source for now
                    data_source = data_sources[0]
                    
                    # Extract connection details from connection_config
                    conn_config = data_source.connection_config or {}
                    data_source_config = {
                        'type': 'database',
                        'criteria': {
                            'database_name': conn_config.get('database', conn_config.get('database_name')),
                            'schema_name': conn_config.get('schema', conn_config.get('schema_name', 'public')),
                            'table_name': conn_config.get('table_name', conn_config.get('default_table'))
                        }
                    }
                    logger.info(f"Using data source: {data_source_config['criteria']['database_name']}.{data_source_config['criteria']['schema_name']}.{data_source_config['criteria']['table_name']}")
                else:
                    logger.warning("No data sources found in planning phase")
                    if use_data_source:
                        raise BusinessLogicError(
                            "No data sources configured in planning phase. Please complete planning phase first or set use_data_source=false"
                        )
            
            # Check for uploaded file samples if requested
            if include_file_samples:
                existing_samples = phase.phase_data.get("cycle_report_sample_selection_samples", []) if phase.phase_data else []
                uploaded_samples = [s for s in existing_samples if s.get('generation_method') == 'Manual Upload']
                if uploaded_samples:
                    data_source_config['type'] = 'file'
                    data_source_config['uploaded_samples'] = uploaded_samples
                    logger.info(f"Including {len(uploaded_samples)} uploaded samples")
            
            job_manager.update_job_progress(
                job_id,
                current_step="Loading scoped attributes",
                progress_percentage=20
            )
            
            # Get scoped attributes - need to check scoping decisions
            attributes = []
            
            if planning_phase and planning_phase.phase_id:
                # First, get scoping phase
                scoping_phase_query = await task_db.execute(
                    select(WorkflowPhase).where(
                        and_(
                            WorkflowPhase.cycle_id == cycle_id,
                            WorkflowPhase.report_id == report_id,
                            WorkflowPhase.phase_name == "Scoping"
                        )
                    )
                )
                scoping_phase = scoping_phase_query.scalar_one_or_none()
                
                if scoping_phase:
                    # Import scoping models
                    from app.models.scoping import ScopingVersion, ScopingAttribute
                    
                    # Get the latest approved or pending scoping version
                    # Use cast to handle potential enum type issues
                    from sqlalchemy import cast, String
                    scoping_version_query = await task_db.execute(
                        select(ScopingVersion).where(
                            and_(
                                ScopingVersion.phase_id == scoping_phase.phase_id,
                                cast(ScopingVersion.version_status, String).in_(['approved', 'pending_approval'])
                            )
                        ).order_by(ScopingVersion.version_number.desc())
                    )
                    scoping_version = scoping_version_query.scalars().first()
                    
                    if scoping_version:
                        # Get approved scoping attributes
                        scoping_attrs_query = await task_db.execute(
                            select(ScopingAttribute).where(
                                and_(
                                    ScopingAttribute.version_id == scoping_version.version_id,
                                    ScopingAttribute.report_owner_decision == 'approved'
                                )
                            )
                        )
                        scoping_attrs = scoping_attrs_query.scalars().all()
                        
                        # Get the corresponding planning attributes
                        approved_attr_ids = [sa.attribute_id for sa in scoping_attrs]
                        
                        if approved_attr_ids:
                            planning_attrs_query = await task_db.execute(
                                select(ReportAttribute).where(
                                    ReportAttribute.id.in_(approved_attr_ids)
                                )
                            )
                            attributes = planning_attrs_query.scalars().all()
                            
                            logger.info(f"Found {len(attributes)} approved scoped attributes from scoping phase")
                        else:
                            logger.warning("No approved attributes found in scoping phase")
                    else:
                        logger.warning("No approved/pending scoping version found")
                else:
                    logger.warning("No scoping phase found")
            
            # If no scoped attributes found, use all attributes from planning
            if not attributes:
                logger.warning("No scoped attributes found, using all attributes from planning")
                planning_attrs_query = await task_db.execute(
                    select(ReportAttribute).where(
                        ReportAttribute.phase_id == planning_phase.phase_id
                    )
                )
                attributes = planning_attrs_query.scalars().all()
                
                if not attributes:
                    raise BusinessLogicError("No attributes found in planning phase.")
            
            # Convert attributes to format expected by service
            scoped_attributes = [
                {
                    "attribute_name": attr.attribute_name,
                    "is_primary_key": attr.is_primary_key,
                    "data_type": attr.data_type,
                    "mandatory_flag": attr.mandatory_flag
                }
                for attr in attributes
            ]
            
            # Always add primary key attributes
            all_planning_attrs = await task_db.execute(
                select(ReportAttribute).where(
                    ReportAttribute.phase_id == planning_phase.phase_id
                )
            )
            all_attrs_dict = {attr.attribute_name: attr for attr in all_planning_attrs.scalars().all()}
            
            for attr_name, attr in all_attrs_dict.items():
                if attr.is_primary_key:
                    # Check if already added
                    if not any(a['attribute_name'] == attr_name for a in scoped_attributes):
                        scoped_attributes.append({
                            "attribute_name": attr_name,
                            "is_primary_key": True,
                            "data_type": attr.data_type,
                            "mandatory_flag": True
                        })
            
            logger.info(f"Processing {len(scoped_attributes)} scoped attributes (including PK)")
            
            # Get profiling results from data profiling phase to use as DQ rules
            profiling_results = []
            profiling_phase_query = await task_db.execute(
                select(WorkflowPhase).where(
                    and_(
                        WorkflowPhase.cycle_id == cycle_id,
                        WorkflowPhase.report_id == report_id,
                        WorkflowPhase.phase_name == "Data Profiling"
                    )
                )
            )
            profiling_phase = profiling_phase_query.scalar_one_or_none()
            
            if profiling_phase:
                # Import profiling models
                from app.models.data_profiling import DataProfilingRuleVersion, ProfilingResult, ProfilingRule
                
                # Get the latest approved profiling version
                profiling_version_query = await task_db.execute(
                    select(DataProfilingRuleVersion).where(
                        and_(
                            DataProfilingRuleVersion.phase_id == profiling_phase.phase_id,
                            DataProfilingRuleVersion.version_status == 'approved'
                        )
                    ).order_by(DataProfilingRuleVersion.version_number.desc())
                )
                profiling_version = profiling_version_query.scalars().first()
                
                if not profiling_version:
                    logger.info("No approved profiling version found")
                else:
                    logger.info(f"Using profiling version {profiling_version.version_number}")
                    
                    # Get attribute IDs for scoped non-PK attributes
                    scoped_attr_ids = []
                    for attr in attributes:
                        if hasattr(attr, 'id') and not attr.is_primary_key:
                            scoped_attr_ids.append(attr.id)
                    
                    if scoped_attr_ids:
                        # Get profiling rules from the approved version for scoped attributes
                        results_query = await task_db.execute(
                            select(ProfilingRule).where(
                                and_(
                                    ProfilingRule.version_id == profiling_version.version_id,
                                    ProfilingRule.attribute_id.in_(scoped_attr_ids),
                                    ProfilingRule.status == "approved"
                                )
                            )
                        )
                        rules = results_query.scalars().all()
                        
                        # For each rule, get its latest execution result
                        result_pairs = []
                        for rule in rules:
                            result_query = await task_db.execute(
                                select(ProfilingResult).where(
                                    and_(
                                        ProfilingResult.rule_id == rule.rule_id,
                                        ProfilingResult.phase_id == profiling_phase.phase_id,
                                        ProfilingResult.execution_status == "success"
                                    )
                                ).order_by(ProfilingResult.executed_at.desc())
                            )
                            result = result_query.scalars().first()
                            if result:
                                result_pairs.append((result, rule))
                    
                    # Convert results to rule-like objects for compatibility
                    # Group by rule name to get unique rules with best results
                    unique_rules = {}
                    for profiling_result, profiling_rule in result_pairs:
                        rule_key = f"{profiling_rule.rule_name}_{profiling_rule.rule_type}"
                        
                        # Keep the result with the lowest pass rate (most failures to find)
                        if rule_key not in unique_rules or (profiling_result.pass_rate or 100) < (unique_rules[rule_key]['pass_rate'] or 100):
                            unique_rules[rule_key] = {
                                'rule_id': profiling_rule.rule_id,
                                'rule_name': profiling_rule.rule_name,
                                'rule_type': profiling_rule.rule_type,
                                'attribute_id': profiling_result.attribute_id,
                                'attribute_name': profiling_rule.attribute_name,
                                'rule_parameters': profiling_rule.rule_parameters,
                                'pass_rate': profiling_result.pass_rate,
                                'severity': profiling_result.severity,
                                'result_summary': profiling_result.result_summary,
                                'failed_count': profiling_result.failed_count,
                                'total_count': profiling_result.total_count
                            }
                    
                    # Create rule objects from unique rules
                    for rule_data in unique_rules.values():
                        profiling_results.append(type('ProfilingRuleResult', (), rule_data)())
                    
                    logger.info(f"Found {len(profiling_results)} unique profiling rules for scoped non-PK attributes to use as DQ rules")
            
            job_manager.update_job_progress(
                job_id,
                current_step="Starting intelligent sample generation",
                progress_percentage=30
            )
            
            # Get existing samples to determine starting sample number
            existing_samples = phase.phase_data.get("cycle_report_sample_selection_samples", []) if phase.phase_data else []
            
            # Generate samples using data source
            from app.services.data_source_sampling_service import DataSourceSamplingService
            sampling_service = DataSourceSamplingService()
            
            # Generate samples from data source
            result = await sampling_service.generate_samples_from_data_source(
                db=task_db,
                cycle_id=cycle_id,
                report_id=report_id,
                phase_id=phase.phase_id,
                target_sample_size=target_sample_size,
                scoped_attributes=scoped_attributes,
                data_source_config=data_source_config,
                distribution=distribution,
                profiling_rules=profiling_results,
                job_id=job_id,
                current_user_id=current_user_id
            )
            
            job_manager.update_job_progress(
                job_id,
                current_step="Saving generated samples",
                progress_percentage=90
            )
            
            # Extract generated samples
            samples_created = result.get('samples', [])
            
            # The intelligent sampling service already creates the version and samples
            # We just need to get the current version for metadata update
            from app.services.sample_selection_table_service import SampleSelectionTableService
            
            table_service = SampleSelectionTableService()
            current_version = await table_service.get_current_version(task_db, phase.phase_id)
            
            if current_version:
                logger.info(f"Sample generation completed. Version {current_version.version_number} with {current_version.actual_sample_size} samples")
            
            # Update phase metadata with minimal info
            if not phase.phase_data:
                phase.phase_data = {}
            
            phase.phase_data['last_updated'] = datetime.utcnow().isoformat()
            phase.phase_data['last_updated_by_id'] = current_user_id
            if current_version:
                phase.phase_data['current_version'] = current_version.version_number
                phase.phase_data['latest_version_id'] = str(current_version.version_id)
            
            # CRITICAL: Ensure tracking of modified object (Planning phase lesson)
            task_db.add(phase)
            flag_modified(phase, 'phase_data')
            
            # Skip audit log creation as table doesn't exist
            # TODO: Implement audit logging when LLMAuditLog table is created
            logger.info(f"Audit log skipped - would have logged: {len(samples_created)} samples generated")
            
            # Commit changes
            await task_db.commit()
            
            # Prepare completion result
            completion_result = {
                "samples_generated": len(samples_created),
                "distribution_achieved": result.get('generation_summary', {}).get('distribution_achieved', {}),
                "generation_summary": result.get('generation_summary', {}),
                "attribute_results": result.get('attribute_results', {}),
                "message": f"Successfully generated {len(samples_created)} samples using intelligent sampling"
            }
            
            # Complete job successfully
            job_manager.complete_job(job_id, result=completion_result)
            
            logger.info(f"Intelligent sampling job {job_id} completed successfully")
            return completion_result
            
    except Exception as e:
        logger.error(f"Intelligent sampling job {job_id} failed: {str(e)}", exc_info=True)
        job_manager.complete_job(job_id, error=str(e))
        raise


@celery_app.task(name='app.tasks.sample_selection_tasks.execute_intelligent_sampling_celery_task')
def execute_intelligent_sampling_celery_task(
    job_id: str,
    cycle_id: int,
    report_id: int,
    target_sample_size: int,
    use_data_source: bool,
    distribution: Optional[Dict[str, float]],
    include_file_samples: bool,
    current_user_id: int,
    current_user_name: str
) -> Dict[str, Any]:
    """
    Celery wrapper for async intelligent sampling task
    """
    logger.info(f"Celery task started for intelligent sampling job {job_id}")
    
    # Use Redis job manager for cross-container communication
    redis_job_manager = get_redis_job_manager()
    
    # Check if job exists (it should have been created by the endpoint)
    job_status = redis_job_manager.get_job_status(job_id)
    if not job_status:
        logger.warning(f"Job {job_id} not found in Redis, creating it manually")
        # Create job data manually with specific ID
        job_data = {
            "job_id": job_id,
            "job_type": "intelligent_sampling",
            "status": "pending",
            "progress_percentage": 0,
            "current_step": "Created",
            "total_steps": 0,
            "completed_steps": 0,
            "message": "Job created",
            "result": None,
            "error": None,
            "created_at": datetime.utcnow().isoformat(),
            "started_at": None,
            "completed_at": None,
            "metadata": {
                "cycle_id": cycle_id,
                "report_id": report_id,
                "target_sample_size": target_sample_size,
                "use_data_source": use_data_source,
                "distribution": distribution,
                "initiated_by": current_user_name,
                "initiated_by_id": current_user_id
            }
        }
        
        try:
            # Store job data directly
            redis_job_manager.redis_client.setex(
                f"{redis_job_manager.job_prefix}{job_id}",
                redis_job_manager.job_ttl,
                json.dumps(job_data)
            )
            # Add to active jobs set
            redis_job_manager.redis_client.sadd(redis_job_manager.active_jobs_key, job_id)
            logger.info(f"✅ Created job {job_id} in Redis")
        except Exception as e:
            logger.error(f"Failed to create job in Redis: {e}")
    
    # Create a custom job manager that uses Redis
    class CeleryRedisJobManager:
        def __init__(self, redis_manager):
            self.redis_manager = redis_manager
            
        def update_job_progress(self, job_id, **kwargs):
            return self.redis_manager.update_job_progress(job_id, **kwargs)
            
        def complete_job(self, job_id, result=None, error=None):
            return self.redis_manager.complete_job(job_id, result=result, error=error)
            
        def get_job_status(self, job_id):
            return self.redis_manager.get_job_status(job_id)
    
    # Replace global job_manager with Redis-based one for this execution
    global job_manager
    original_job_manager = job_manager
    job_manager = CeleryRedisJobManager(redis_job_manager)
    
    try:
        # Close any existing event loop to avoid conflicts
        try:
            existing_loop = asyncio.get_running_loop()
            if existing_loop and existing_loop.is_running():
                logger.warning("Found existing running loop, will create new one")
        except RuntimeError:
            # No loop running, which is what we want
            pass
        
        # Create a fresh event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Create a new async engine and session factory for this task
        # This ensures we don't have event loop conflicts
        engine = create_async_engine(
            settings.database_url.replace('postgresql://', 'postgresql+asyncpg://'),
            echo=False,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10
        )
        
        # Create task-specific session factory
        TaskSessionLocal = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # Temporarily replace the global AsyncSessionLocal
        global AsyncSessionLocal
        original_session_local = AsyncSessionLocal
        AsyncSessionLocal = TaskSessionLocal
        
        try:
            # Run the async task
            result = loop.run_until_complete(
                execute_intelligent_sampling_task(
                    job_id=job_id,
                    cycle_id=cycle_id,
                    report_id=report_id,
                    target_sample_size=target_sample_size,
                    use_data_source=use_data_source,
                    distribution=distribution,
                    include_file_samples=include_file_samples,
                    current_user_id=current_user_id,
                    current_user_name=current_user_name
                )
            )
            return result
        finally:
            # Restore original session factory
            AsyncSessionLocal = original_session_local
            
            # Dispose of the engine
            loop.run_until_complete(engine.dispose())
            
            # Clean up the event loop
            try:
                loop.close()
            except Exception as e:
                logger.warning(f"Error closing event loop: {e}")
            
    except Exception as e:
        logger.error(f"Error in Celery task: {str(e)}", exc_info=True)
        job_manager.complete_job(job_id, error=str(e))
        raise
    finally:
        # Restore original job manager
        job_manager = original_job_manager