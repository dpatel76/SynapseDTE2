"""
Planning Phase Celery Tasks with Pause/Resume Support
Handles long-running planning operations as proper background tasks
"""
import logging
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from celery import Task, states
from celery.result import AsyncResult

from app.core.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.services.llm_service import get_llm_service
from app.core.background_jobs import job_manager
from app.core.redis_job_manager import get_redis_job_manager
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Track paused tasks in Redis
PAUSED_TASKS_KEY = "celery:paused_tasks"
TASK_STATE_KEY = "celery:task_state:{task_id}"


class PausableTask(Task):
    """Base task class that supports pause/resume functionality"""
    
    def __init__(self):
        super().__init__()
        self._is_paused = False
    
    def pause(self, task_id: str):
        """Pause a running task"""
        # Store pause state in Redis
        redis_client = celery_app.backend.client
        redis_client.sadd(PAUSED_TASKS_KEY, task_id)
        redis_client.set(f"{TASK_STATE_KEY}:{task_id}:paused", "1")
        logger.info(f"Task {task_id} marked for pause")
    
    def resume(self, task_id: str):
        """Resume a paused task"""
        redis_client = celery_app.backend.client
        redis_client.srem(PAUSED_TASKS_KEY, task_id)
        redis_client.delete(f"{TASK_STATE_KEY}:{task_id}:paused")
        logger.info(f"Task {task_id} resumed")
    
    def is_paused(self, task_id: str) -> bool:
        """Check if task is paused"""
        redis_client = celery_app.backend.client
        return redis_client.sismember(PAUSED_TASKS_KEY, task_id)
    
    def save_checkpoint(self, task_id: str, checkpoint_data: Dict[str, Any]):
        """Save task checkpoint for resumability"""
        redis_client = celery_app.backend.client
        checkpoint_key = f"{TASK_STATE_KEY}:{task_id}:checkpoint"
        redis_client.set(checkpoint_key, json.dumps(checkpoint_data))
        redis_client.expire(checkpoint_key, 86400)  # Expire after 24 hours
    
    def load_checkpoint(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Load task checkpoint"""
        redis_client = celery_app.backend.client
        checkpoint_key = f"{TASK_STATE_KEY}:{task_id}:checkpoint"
        checkpoint_data = redis_client.get(checkpoint_key)
        if checkpoint_data:
            return json.loads(checkpoint_data)
        return None
    
    def clear_checkpoint(self, task_id: str):
        """Clear task checkpoint"""
        redis_client = celery_app.backend.client
        redis_client.delete(f"{TASK_STATE_KEY}:{task_id}:checkpoint")
        redis_client.delete(f"{TASK_STATE_KEY}:{task_id}:paused")
        redis_client.srem(PAUSED_TASKS_KEY, task_id)


@celery_app.task(
    bind=True,
    base=PausableTask,
    name='app.tasks.planning_tasks.auto_map_pdes',
    queue='llm',
    max_retries=3,
    default_retry_delay=60
)
def auto_map_pdes_task(
    self,
    cycle_id: int,
    report_id: int,
    phase_id: int,
    user_id: int,
    attributes_context: List[Dict[str, Any]],
    data_sources_context: List[Dict[str, Any]],
    report_context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Celery task for auto-mapping PDEs with pause/resume support
    """
    task_id = self.request.id
    logger.info(f"🚀 Starting PDE auto-mapping task {task_id}")
    
    # Use Redis job manager for cross-container state
    redis_job_manager = get_redis_job_manager()
    
    # Update job status at start
    redis_job_manager.update_job_progress(
        task_id,
        status="running",
        current_step="Initializing PDE mapping",
        progress_percentage=0,
        message="Starting automatic PDE mapping with LLM..."
    )
    
    # Check for existing checkpoint
    checkpoint = self.load_checkpoint(task_id)
    start_index = 0
    total_mapped = 0
    total_failed = 0
    
    if checkpoint:
        logger.info(f"📋 Resuming from checkpoint: {checkpoint}")
        start_index = checkpoint.get('last_processed_index', 0)
        total_mapped = checkpoint.get('total_mapped', 0)
        total_failed = checkpoint.get('total_failed', 0)
    
    # Run async function in sync context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(
            _auto_map_pdes_with_pause_support(
                task=self,
                task_id=task_id,
                cycle_id=cycle_id,
                report_id=report_id,
                phase_id=phase_id,
                user_id=user_id,
                attributes_context=attributes_context,
                data_sources_context=data_sources_context,
                report_context=report_context,
                start_index=start_index,
                initial_mapped=total_mapped,
                initial_failed=total_failed,
                redis_job_manager=redis_job_manager
            )
        )
        
        # Only clear checkpoint if task completed (not paused)
        if result.get('status') != 'paused':
            self.clear_checkpoint(task_id)
        
        return result
        
    except Exception as e:
        logger.error(f"❌ PDE mapping task failed: {str(e)}")
        
        # Update Redis job manager with error
        redis_job_manager.complete_job(task_id, error=str(e))
        
        # Save checkpoint on failure for retry
        if 'last_processed_index' in locals():
            self.save_checkpoint(task_id, {
                'last_processed_index': locals().get('last_processed_index', 0),
                'total_mapped': locals().get('total_mapped', 0),
                'total_failed': locals().get('total_failed', 0)
            })
        raise
    finally:
        loop.close()


async def _auto_map_pdes_with_pause_support(
    task: PausableTask,
    task_id: str,
    cycle_id: int,
    report_id: int,
    phase_id: int,
    user_id: int,
    attributes_context: List[Dict[str, Any]],
    data_sources_context: List[Dict[str, Any]],
    report_context: Dict[str, Any],
    start_index: int = 0,
    initial_mapped: int = 0,
    initial_failed: int = 0,
    redis_job_manager = None
) -> Dict[str, Any]:
    """Async helper for PDE mapping with pause support"""
    
    async with AsyncSessionLocal() as db:
        try:
            # Get LLM service
            llm_service = get_llm_service()
            
            # Import models
            from app.models.planning import PlanningPDEMapping
            from app.models.report_attribute import ReportAttribute
            
            total_mapped = initial_mapped
            total_failed = initial_failed
            batch_size = 6  # Process 6 attributes at a time
            total_attributes = len(attributes_context)
            
            # Process attributes in batches
            for i in range(start_index, total_attributes, batch_size):
                # Check if task is paused
                if task.is_paused(task_id):
                    logger.info(f"⏸️ Task {task_id} is paused at index {i}")
                    # Save checkpoint
                    task.save_checkpoint(task_id, {
                        'last_processed_index': i,
                        'total_mapped': total_mapped,
                        'total_failed': total_failed
                    })
                    
                    # Update Redis job manager if available
                    if redis_job_manager:
                        redis_job_manager.update_job_progress(
                            task_id,
                            status="paused",
                            current_step=f"Paused at attribute {i} of {total_attributes}",
                            message=f"Task paused. Mapped: {total_mapped}, Failed: {total_failed}"
                        )
                    
                    # Update task state
                    task.update_state(
                        state='PAUSED',
                        meta={
                            'current': i,
                            'total': total_attributes,
                            'status': f'Paused at attribute {i} of {total_attributes}',
                            'total_mapped': total_mapped,
                            'total_failed': total_failed
                        }
                    )
                    return {
                        'status': 'paused',
                        'last_processed_index': i,
                        'total_mapped': total_mapped,
                        'total_failed': total_failed
                    }
                
                # Get batch of attributes
                batch_end = min(i + batch_size, total_attributes)
                batch_attributes = attributes_context[i:batch_end]
                
                # Update progress
                progress_percentage = int((i / total_attributes) * 100)
                
                # Update Redis job manager if available
                if redis_job_manager:
                    redis_job_manager.update_job_progress(
                        task_id,
                        progress_percentage=progress_percentage,
                        current_step=f"Processing attributes {i+1}-{batch_end} of {total_attributes}",
                        total_steps=total_attributes,
                        completed_steps=i,
                        message=f"Processing batch {i//batch_size + 1}: mapped {total_mapped}, failed {total_failed}"
                    )
                
                # Also update Celery task state
                task.update_state(
                    state='PROGRESS',
                    meta={
                        'current': i,
                        'total': total_attributes,
                        'status': f'Processing attributes {i+1}-{batch_end} of {total_attributes}',
                        'progress_percentage': progress_percentage,
                        'total_mapped': total_mapped,
                        'total_failed': total_failed
                    }
                )
                
                logger.info(f"📦 Processing batch {i//batch_size + 1}: attributes {i+1}-{batch_end}")
                
                try:
                    # Call LLM service for batch
                    batch_suggestions = await llm_service.suggest_pde_mappings(
                        attributes=batch_attributes,
                        data_sources=data_sources_context,
                        report_context=report_context,
                        job_id=task_id
                    )
                    
                    # Process suggestions
                    for idx, suggestion in enumerate(batch_suggestions):
                        try:
                            attribute_id = suggestion.get('attribute_id')
                            if not attribute_id:
                                logger.warning(f"Suggestion {idx} missing attribute_id")
                                continue
                            
                            # Debug logging for first suggestion
                            if idx == 0:
                                logger.info(f"🔍 First suggestion structure:")
                                logger.info(f"  Keys: {list(suggestion.keys())}")
                                logger.info(f"  attribute_id: {suggestion.get('attribute_id')}")
                                logger.info(f"  source_table: {suggestion.get('source_table')}")
                                logger.info(f"  source_column: {suggestion.get('source_column')}")
                                logger.info(f"  table_name: {suggestion.get('table_name')}")
                                logger.info(f"  column_name: {suggestion.get('column_name')}")
                                logger.info(f"  confidence_score: {suggestion.get('confidence_score')}")
                                logger.info(f"  confidence: {suggestion.get('confidence')}")
                            
                            # Check if mapping already exists
                            existing_mapping = await db.execute(
                                select(PlanningPDEMapping).where(
                                    and_(
                                        PlanningPDEMapping.phase_id == phase_id,
                                        PlanningPDEMapping.attribute_id == attribute_id
                                    )
                                )
                            )
                            existing = existing_mapping.scalar_one_or_none()
                            
                            if existing:
                                logger.info(f"Mapping already exists for attribute {attribute_id}, skipping")
                                continue
                            
                            # Create new mapping
                            # Get fields from normalized suggestion
                            confidence_score = suggestion.get('confidence_score', suggestion.get('confidence', 0))
                            # After fixing LLM service, it now returns table_name/column_name consistently
                            table_name = suggestion.get('table_name')
                            column_name = suggestion.get('column_name')
                            
                            if confidence_score >= 50 and table_name and column_name:
                                # Create mapping only if confidence is decent and we have valid source
                                new_mapping = PlanningPDEMapping(
                                    phase_id=phase_id,
                                    attribute_id=attribute_id,
                                    data_source_id=suggestion.get('data_source_id'),
                                    pde_name=column_name,
                                    pde_code=f"DS{suggestion.get('data_source_id', 0)}_{column_name}",
                                    source_field=f"{table_name}.{column_name}",
                                    mapping_type=suggestion.get('transformation_rule', 'direct'),
                                    business_process=suggestion.get('business_process', ''),
                                    llm_confidence_score=confidence_score,
                                    llm_mapping_rationale=suggestion.get('reasoning', ''),
                                    information_security_classification=suggestion.get('information_security_classification', 'Confidential'),
                                    criticality=suggestion.get('criticality', 'Medium'),
                                    risk_level=suggestion.get('risk_level', 'Medium'),
                                    regulatory_flag=suggestion.get('regulatory_flag', False),
                                    llm_classification_rationale=suggestion.get('classification_rationale', ''),
                                    created_by_id=user_id,
                                    created_at=datetime.utcnow()
                                )
                                
                                db.add(new_mapping)
                                total_mapped += 1
                                logger.info(f"✅ Created mapping for attribute {attribute_id} with confidence {confidence_score}%")
                            else:
                                total_failed += 1
                                logger.warning(f"⚠️ Low confidence or missing data for attribute {attribute_id}: {confidence_score}%")
                                
                        except Exception as e:
                            logger.error(f"Error processing suggestion for attribute {suggestion.get('attribute_id')}: {e}")
                            total_failed += 1
                    
                    # Commit batch
                    await db.commit()
                    
                except Exception as e:
                    logger.error(f"Error processing batch {i//batch_size + 1}: {e}")
                    # Continue with next batch
                    continue
            
            # Final commit
            await db.commit()
            
            success_rate = (total_mapped / total_attributes * 100) if total_attributes > 0 else 0
            
            # Update Redis job manager with final result
            if redis_job_manager:
                redis_job_manager.complete_job(
                    task_id,
                    result={
                        'total_mapped': total_mapped,
                        'total_failed': total_failed,
                        'total_attributes': total_attributes,
                        'success_rate': f"{success_rate:.1f}%"
                    }
                )
            
            return {
                'status': 'completed',
                'total_mapped': total_mapped,
                'total_failed': total_failed,
                'total_attributes': total_attributes,
                'success_rate': f"{success_rate:.1f}%",
                'message': f"Successfully mapped {total_mapped} attributes, {total_failed} require manual mapping"
            }
            
        except Exception as e:
            logger.error(f"❌ Error in PDE mapping: {str(e)}")
            raise


@celery_app.task(name='app.tasks.planning_tasks.pause_pde_mapping')
def pause_pde_mapping_task(task_id: str) -> Dict[str, Any]:
    """Pause a running PDE mapping task"""
    task = auto_map_pdes_task
    task.pause(task_id)
    
    # Update Redis job manager
    redis_job_manager = get_redis_job_manager()
    redis_job_manager.update_job_progress(
        task_id,
        status="paused",
        current_step="Task paused by user"
    )
    
    return {
        'status': 'paused',
        'task_id': task_id,
        'message': f'Task {task_id} has been marked for pause'
    }


@celery_app.task(name='app.tasks.planning_tasks.resume_pde_mapping')
def resume_pde_mapping_task(original_task_id: str) -> Dict[str, Any]:
    """Resume a paused PDE mapping task"""
    # Get the task instance
    task_instance = auto_map_pdes_task
    
    # Load checkpoint
    checkpoint = task_instance.load_checkpoint(original_task_id)
    if not checkpoint:
        logger.error(f"No checkpoint found for task {original_task_id}")
        return {
            'status': 'error',
            'message': 'No checkpoint found for task'
        }
    
    # Get the job details from Redis job manager to retrieve original parameters
    from app.core.redis_job_manager import get_redis_job_manager
    redis_job_manager = get_redis_job_manager()
    job_data = redis_job_manager.get_job_status(original_task_id)
    
    if not job_data:
        logger.error(f"No job data found for task {original_task_id}")
        return {
            'status': 'error',
            'message': 'Cannot retrieve job data'
        }
    
    # Extract the original parameters from job metadata
    metadata = job_data.get('metadata', {})
    cycle_id = metadata.get('cycle_id')
    report_id = metadata.get('report_id')
    user_id = metadata.get('user_id')
    
    if not all([cycle_id, report_id, user_id]):
        logger.error(f"Missing required parameters in job metadata: {metadata}")
        return {
            'status': 'error',
            'message': 'Missing required parameters in job metadata'
        }
    
    # We need to store the full task parameters in the checkpoint or job metadata
    # For now, we'll need to retrieve them from the result backend
    result = AsyncResult(original_task_id, app=celery_app)
    
    # Get the original args and kwargs
    original_args = getattr(result, '_cache', {}).get('args', [])
    original_kwargs = getattr(result, '_cache', {}).get('kwargs', {})
    
    # If we can't get the original args, try to get them from the backend
    if not original_args:
        backend_result = celery_app.backend.get_task_meta(original_task_id)
        original_args = backend_result.get('args', [])
        original_kwargs = backend_result.get('kwargs', {})
    
    if not original_args or len(original_args) < 7:
        logger.error(f"Cannot retrieve original task parameters for {original_task_id}")
        return {
            'status': 'error',
            'message': 'Cannot retrieve original task parameters. Task data may have expired.'
        }
    
    # Clear pause state
    task_instance.resume(original_task_id)
    
    # Update job status to resuming
    redis_job_manager.update_job_progress(
        original_task_id,
        status="resuming",
        current_step="Resuming task from checkpoint",
        message=f"Resuming from attribute {checkpoint.get('last_processed_index', 0)}"
    )
    
    # Start new task from checkpoint with the same task ID
    # The task will pick up from where it left off using the checkpoint
    new_task = auto_map_pdes_task.apply_async(
        args=original_args,
        kwargs=original_kwargs,
        task_id=original_task_id,  # Reuse the same task ID
        queue='llm'
    )
    
    return {
        'status': 'resumed',
        'task_id': original_task_id,
        'checkpoint': checkpoint,
        'message': f'Task resumed from attribute {checkpoint.get("last_processed_index", 0)}'
    }