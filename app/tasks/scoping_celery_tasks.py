"""
Scoping Phase Celery Tasks with Pause/Resume Support
Handles long-running LLM scoping operations as proper background tasks
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
from app.services.scoping_service import ScopingService
from app.core.background_jobs import job_manager
from app.core.redis_job_manager import get_redis_job_manager
from app.models.scoping import ScopingVersion
from app.models.report_attribute import ReportAttribute
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
    name='app.tasks.scoping_tasks.generate_llm_recommendations',
    queue='llm',
    max_retries=3,
    default_retry_delay=60
)
def generate_llm_recommendations_celery_task(
    self,
    version_id: str,
    phase_id: int,
    cycle_id: int,
    report_id: int,
    attributes: List[Dict[str, Any]],
    user_id: int
) -> Dict[str, Any]:
    """
    Celery task for generating LLM scoping recommendations with pause/resume support
    """
    task_id = self.request.id
    logger.info(f"🚀 Starting LLM scoping recommendations task {task_id}")
    
    # Use Redis job manager for cross-container state
    redis_job_manager = get_redis_job_manager()
    
    # Update job status at start
    redis_job_manager.update_job_progress(
        task_id,
        status="running",
        current_step="Initializing LLM scoping recommendations",
        progress_percentage=0,
        message="Starting automatic scoping recommendations with LLM..."
    )
    
    # Check for existing checkpoint
    checkpoint = self.load_checkpoint(task_id)
    start_index = 0
    recommendations_generated = 0
    recommendations_failed = 0
    
    if checkpoint:
        logger.info(f"📋 Resuming from checkpoint: {checkpoint}")
        start_index = checkpoint.get('last_processed_index', 0)
        recommendations_generated = checkpoint.get('recommendations_generated', 0)
        recommendations_failed = checkpoint.get('recommendations_failed', 0)
    
    # Run async function in sync context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(
            _generate_llm_recommendations_with_pause_support(
                task=self,
                task_id=task_id,
                version_id=version_id,
                phase_id=phase_id,
                cycle_id=cycle_id,
                report_id=report_id,
                attributes=attributes,
                user_id=user_id,
                start_index=start_index,
                initial_generated=recommendations_generated,
                initial_failed=recommendations_failed,
                redis_job_manager=redis_job_manager
            )
        )
        
        # Only clear checkpoint if task completed (not paused)
        if result.get('status') != 'paused':
            self.clear_checkpoint(task_id)
        
        return result
        
    except Exception as e:
        logger.error(f"❌ LLM scoping recommendations task failed: {str(e)}")
        
        # Update Redis job manager with error
        redis_job_manager.complete_job(task_id, error=str(e))
        
        # Save checkpoint on failure for retry
        if 'last_processed_index' in locals():
            self.save_checkpoint(task_id, {
                'last_processed_index': locals().get('last_processed_index', 0),
                'recommendations_generated': locals().get('recommendations_generated', 0),
                'recommendations_failed': locals().get('recommendations_failed', 0)
            })
        raise
    finally:
        loop.close()


async def _generate_llm_recommendations_with_pause_support(
    task: PausableTask,
    task_id: str,
    version_id: str,
    phase_id: int,
    cycle_id: int,
    report_id: int,
    attributes: List[Dict[str, Any]],
    user_id: int,
    start_index: int = 0,
    initial_generated: int = 0,
    initial_failed: int = 0,
    redis_job_manager = None
) -> Dict[str, Any]:
    """Async helper for LLM recommendations generation with pause support"""
    
    async with AsyncSessionLocal() as db:
        try:
            # Get scoping service
            scoping_service = ScopingService(db)
            
            # Get version
            from app.models.scoping import ScopingVersion
            version_result = await db.execute(
                select(ScopingVersion)
                .where(ScopingVersion.version_id == version_id)
            )
            version = version_result.scalar_one_or_none()
            
            if not version:
                raise ValueError(f"Version {version_id} not found")
            
            # Get LLM service
            llm_service = get_llm_service()
            
            recommendations_generated = initial_generated
            recommendations_failed = initial_failed
            total_attributes = len(attributes)
            
            # Get report info for regulatory context
            from app.models.report import Report
            from app.models.cycle_report import CycleReport
            report_query = await db.execute(
                select(Report).join(CycleReport).where(
                    and_(
                        CycleReport.cycle_id == cycle_id,
                        CycleReport.report_id == report_id
                    )
                )
            )
            report = report_query.scalar_one_or_none()
            
            regulation_type = None
            if report and report.report_name:
                regulation_type = "fr_y_14m" if "14M" in report.report_name.upper() else "generic"
            
            # Process attributes one by one for better control
            for i in range(start_index, total_attributes):
                # Check if task is paused
                if task.is_paused(task_id):
                    logger.info(f"⏸️ Task {task_id} is paused at index {i}")
                    # Save checkpoint
                    task.save_checkpoint(task_id, {
                        'last_processed_index': i,
                        'recommendations_generated': recommendations_generated,
                        'recommendations_failed': recommendations_failed
                    })
                    
                    # Update Redis job manager if available
                    if redis_job_manager:
                        redis_job_manager.update_job_progress(
                            task_id,
                            status="paused",
                            current_step=f"Paused at attribute {i} of {total_attributes}",
                            message=f"Task paused. Generated: {recommendations_generated}, Failed: {recommendations_failed}"
                        )
                    
                    # Update task state
                    task.update_state(
                        state='PAUSED',
                        meta={
                            'current': i,
                            'total': total_attributes,
                            'status': f'Paused at attribute {i} of {total_attributes}',
                            'recommendations_generated': recommendations_generated,
                            'recommendations_failed': recommendations_failed
                        }
                    )
                    return {
                        'status': 'paused',
                        'last_processed_index': i,
                        'recommendations_generated': recommendations_generated,
                        'recommendations_failed': recommendations_failed
                    }
                
                # Get current attribute
                attribute = attributes[i]
                
                # Update progress
                progress_percentage = int((i / total_attributes) * 100)
                
                # Update Redis job manager if available
                if redis_job_manager:
                    redis_job_manager.update_job_progress(
                        task_id,
                        progress_percentage=progress_percentage,
                        current_step=f"Generating recommendation for {attribute.get('attribute_name')}",
                        total_steps=total_attributes,
                        completed_steps=i,
                        message=f"Processing attribute {i+1} of {total_attributes}"
                    )
                
                # Also update Celery task state
                task.update_state(
                    state='PROGRESS',
                    meta={
                        'current': i,
                        'total': total_attributes,
                        'status': f'Processing attribute {i+1} of {total_attributes}',
                        'progress_percentage': progress_percentage,
                        'recommendations_generated': recommendations_generated,
                        'recommendations_failed': recommendations_failed
                    }
                )
                
                logger.info(f"📊 Processing attribute {i+1}/{total_attributes}: {attribute.get('attribute_name')}")
                
                try:
                    # Prepare context for LLM
                    attribute_context = {
                        "attribute_name": attribute.get("attribute_name"),
                        "data_type": attribute.get("data_type"),
                        "description": attribute.get("description"),
                        "is_primary_key": attribute.get("is_primary_key", False),
                        "is_cde": attribute.get("is_cde", False),
                        "mandatory_flag": attribute.get("mandatory_flag", True),
                        "has_issues": attribute.get("has_issues", False),
                        "testing_approach": attribute.get("testing_approach"),
                        "regulatory_reference": attribute.get("regulatory_reference"),
                        "mdrm": attribute.get("mdrm"),
                        "validation_rules": attribute.get("validation_rules"),
                        "report_type": regulation_type,
                        "schedule_name": report.report_name if report else None  # Use report_name instead of schedule_name
                    }
                    
                    # Capture LLM request metadata
                    llm_request_payload = {
                        "model": "claude-3-5-sonnet",
                        "temperature": 0.3,
                        "max_tokens": 2000,
                        "timestamp": datetime.utcnow().isoformat(),
                        "attribute_context": attribute_context,
                        "report_type": report.report_name if report else None
                    }
                    
                    # Generate recommendation via LLM
                    # Pass report_name instead of the context dict
                    llm_result = await llm_service.generate_scoping_recommendations(
                        [attribute_context], 
                        report_type=report.report_name if report else None
                    )
                    
                    # Extract recommendation for this attribute
                    recommendation_data = None
                    if llm_result.get("recommendations"):
                        for rec in llm_result["recommendations"]:
                            if rec.get("attribute_name") == attribute.get("attribute_name"):
                                recommendation_data = rec
                                break
                    
                    if recommendation_data:
                        # Use the service to add attributes with recommendations
                        try:
                            await scoping_service.add_attributes_to_version(
                                version_id=version_id,
                                attribute_ids=[attribute.get("attribute_id")],
                                llm_recommendations=[{
                                    "recommended_action": "Test",  # Default to Test for all LLM recommendations
                                    "confidence_score": float(recommendation_data.get("risk_score", 85)) / 100.0,  # Convert 0-100 to 0-1
                                    "rationale": recommendation_data.get("enhanced_rationale", {}).get("regulatory_usage", ""),
                                    "risk_factors": recommendation_data.get("risk_factors", []),
                                    "expected_source_documents": recommendation_data.get("typical_source_documents", "").split(", ") if recommendation_data.get("typical_source_documents") else [],
                                    "search_keywords": recommendation_data.get("keywords_to_look_for", "").split(", ") if recommendation_data.get("keywords_to_look_for") else [],
                                    "validation_rules": recommendation_data.get("validation_rules"),  # Extract validation rules
                                    "testing_approach": recommendation_data.get("testing_approach"),  # Extract testing approach
                                    "priority_level": "high" if float(str(recommendation_data.get("risk_score", 0))) > 70 else "medium",
                                    "is_cde": recommendation_data.get("is_cde", False),
                                    "is_primary_key": recommendation_data.get("is_primary_key", False),
                                    "has_historical_issues": recommendation_data.get("has_historical_issues", False),
                                    "data_quality_score": recommendation_data.get("data_quality_score"),
                                    "data_quality_issues": recommendation_data.get("data_quality_issues"),
                                    "provider": "claude",
                                    "processing_time_ms": recommendation_data.get("processing_time_ms", 0),
                                    "request_payload": llm_request_payload,  # Now properly captured and passed
                                    "response_payload": recommendation_data  # Store the complete LLM response
                                }],
                                user_id=user_id
                            )
                            recommendations_generated += 1
                        except Exception as e:
                            logger.error(f"Error saving recommendation for {attribute.get('attribute_name')}: {str(e)}")
                            recommendations_failed += 1
                    else:
                        logger.warning(f"No recommendation generated for {attribute.get('attribute_name')}")
                        recommendations_failed += 1
                    
                    # Service handles commits internally
                    
                except Exception as e:
                    logger.error(f"Error generating recommendation for attribute {attribute.get('attribute_name')}: {e}")
                    recommendations_failed += 1
                    # Continue with next attribute
                    continue
            
            # Update version status
            version.llm_completed_at = datetime.utcnow()
            await db.commit()
            
            # Update Redis job manager with final result
            if redis_job_manager:
                redis_job_manager.complete_job(
                    task_id,
                    result={
                        'recommendations_generated': recommendations_generated,
                        'recommendations_failed': recommendations_failed,
                        'total_attributes': total_attributes,
                        'success_rate': f"{(recommendations_generated / total_attributes * 100) if total_attributes > 0 else 0:.1f}%"
                    }
                )
            
            return {
                'status': 'completed',
                'recommendations_generated': recommendations_generated,
                'recommendations_failed': recommendations_failed,
                'total_attributes': total_attributes,
                'message': f"Successfully generated {recommendations_generated} recommendations, {recommendations_failed} failed"
            }
            
        except Exception as e:
            logger.error(f"❌ Error in LLM recommendations generation: {str(e)}")
            raise


@celery_app.task(name='app.tasks.scoping_tasks.pause_scoping_recommendations')
def pause_scoping_recommendations_task(task_id: str) -> Dict[str, Any]:
    """Pause a running scoping recommendations task"""
    task = generate_llm_recommendations_celery_task
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


@celery_app.task(name='app.tasks.scoping_tasks.resume_scoping_recommendations')
def resume_scoping_recommendations_task(original_task_id: str) -> Dict[str, Any]:
    """Resume a paused scoping recommendations task"""
    # Get the task instance
    task_instance = generate_llm_recommendations_celery_task
    
    # Load checkpoint
    checkpoint = task_instance.load_checkpoint(original_task_id)
    if not checkpoint:
        logger.error(f"No checkpoint found for task {original_task_id}")
        return {
            'status': 'error',
            'message': 'No checkpoint found for task'
        }
    
    # Get the job details from Redis job manager to retrieve original parameters
    redis_job_manager = get_redis_job_manager()
    job_data = redis_job_manager.get_job_status(original_task_id)
    
    if not job_data:
        logger.error(f"No job data found for task {original_task_id}")
        return {
            'status': 'error',
            'message': 'Cannot retrieve job data'
        }
    
    # Get the original task data from Celery backend
    result = AsyncResult(original_task_id, app=celery_app)
    backend_result = celery_app.backend.get_task_meta(original_task_id)
    original_args = backend_result.get('args', [])
    original_kwargs = backend_result.get('kwargs', {})
    
    if not original_args or len(original_args) < 6:
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
    new_task = generate_llm_recommendations_celery_task.apply_async(
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