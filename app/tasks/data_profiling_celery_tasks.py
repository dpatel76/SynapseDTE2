"""
Data Profiling Phase Celery Tasks with Pause/Resume Support
Handles long-running data profiling operations as proper background tasks
"""
import logging
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from celery import Task, states
from celery.result import AsyncResult

from app.core.celery_app import celery_app
from app.core.database import AsyncSessionLocal, SyncSessionLocal
from app.services.llm_service import get_llm_service
from app.services.data_profiling_service import DataProfilingService
from app.core.background_jobs import job_manager
from app.core.redis_job_manager import get_redis_job_manager
from app.models.data_profiling import DataProfilingRuleVersion, ProfilingRule
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
    name='app.tasks.data_profiling_celery_tasks.generate_profiling_rules',
    queue='llm',
    max_retries=3,
    default_retry_delay=60
)
def generate_profiling_rules_celery_task(
    self,
    version_id: str,
    phase_id: int,
    attributes: List[Dict[str, Any]],
    data_source_config: Dict[str, Any],
    user_id: int
) -> Dict[str, Any]:
    """
    Celery task for generating data profiling rules with pause/resume support
    """
    task_id = self.request.id
    logger.info(f"🚀 Starting profiling rule generation task {task_id}")
    
    # Use Redis job manager for cross-container state
    redis_job_manager = get_redis_job_manager()
    
    # Update job status at start
    redis_job_manager.update_job_progress(
        task_id,
        status="running",
        current_step="Initializing profiling rule generation",
        progress_percentage=0,
        message="Starting automatic profiling rule generation with LLM..."
    )
    
    # Check for existing checkpoint
    checkpoint = self.load_checkpoint(task_id)
    start_index = 0
    rules_generated = 0
    rules_failed = 0
    
    if checkpoint:
        logger.info(f"📋 Resuming from checkpoint: {checkpoint}")
        start_index = checkpoint.get('last_processed_index', 0)
        rules_generated = checkpoint.get('rules_generated', 0)
        rules_failed = checkpoint.get('rules_failed', 0)
    
    # Run async function in sync context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(
            _generate_profiling_rules_with_pause_support(
                task=self,
                task_id=task_id,
                version_id=version_id,
                phase_id=phase_id,
                attributes=attributes,
                data_source_config=data_source_config,
                user_id=user_id,
                start_index=start_index,
                initial_generated=rules_generated,
                initial_failed=rules_failed,
                redis_job_manager=redis_job_manager
            )
        )
        
        # Only clear checkpoint if task completed (not paused)
        if result.get('status') != 'paused':
            self.clear_checkpoint(task_id)
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Profiling rule generation task failed: {str(e)}")
        
        # Update Redis job manager with error
        redis_job_manager.complete_job(task_id, error=str(e))
        
        # Save checkpoint on failure for retry
        if 'last_processed_index' in locals():
            self.save_checkpoint(task_id, {
                'last_processed_index': locals().get('last_processed_index', 0),
                'rules_generated': locals().get('rules_generated', 0),
                'rules_failed': locals().get('rules_failed', 0)
            })
        raise
    finally:
        loop.close()


async def _generate_profiling_rules_with_pause_support(
    task: PausableTask,
    task_id: str,
    version_id: str,
    phase_id: int,
    attributes: List[Dict[str, Any]],
    data_source_config: Dict[str, Any],
    user_id: int,
    start_index: int = 0,
    initial_generated: int = 0,
    initial_failed: int = 0,
    redis_job_manager = None
) -> Dict[str, Any]:
    """Async helper for profiling rule generation with pause support"""
    
    async with AsyncSessionLocal() as db:
        try:
            # Get LLM service
            llm_service = get_llm_service()
            
            # Get version
            version_result = await db.execute(
                select(DataProfilingRuleVersion)
                .where(DataProfilingRuleVersion.version_id == version_id)
            )
            version = version_result.scalar_one_or_none()
            
            if not version:
                raise ValueError(f"Version {version_id} not found")
            
            rules_generated = initial_generated
            rules_failed = initial_failed
            total_attributes = len(attributes)
            
            # Process attributes one by one for better control
            for i in range(start_index, total_attributes):
                # Check if task is paused
                if task.is_paused(task_id):
                    logger.info(f"⏸️ Task {task_id} is paused at index {i}")
                    # Save checkpoint
                    task.save_checkpoint(task_id, {
                        'last_processed_index': i,
                        'rules_generated': rules_generated,
                        'rules_failed': rules_failed
                    })
                    
                    # Update Redis job manager if available
                    if redis_job_manager:
                        redis_job_manager.update_job_progress(
                            task_id,
                            status="paused",
                            current_step=f"Paused at attribute {i} of {total_attributes}",
                            message=f"Task paused. Generated: {rules_generated}, Failed: {rules_failed}"
                        )
                    
                    # Update task state
                    task.update_state(
                        state='PAUSED',
                        meta={
                            'current': i,
                            'total': total_attributes,
                            'status': f'Paused at attribute {i} of {total_attributes}',
                            'rules_generated': rules_generated,
                            'rules_failed': rules_failed
                        }
                    )
                    return {
                        'status': 'paused',
                        'last_processed_index': i,
                        'rules_generated': rules_generated,
                        'rules_failed': rules_failed
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
                        current_step=f"Generating rules for {attribute.get('attribute_name')}",
                        total_steps=total_attributes,
                        completed_steps=i,
                        message=f"Processing attribute {i+1} of {total_attributes}: generated {rules_generated}, failed {rules_failed}"
                    )
                
                # Also update Celery task state
                task.update_state(
                    state='PROGRESS',
                    meta={
                        'current': i,
                        'total': total_attributes,
                        'status': f'Processing attribute {i+1} of {total_attributes}',
                        'progress_percentage': progress_percentage,
                        'rules_generated': rules_generated,
                        'rules_failed': rules_failed
                    }
                )
                
                logger.info(f"📊 Processing attribute {i+1}/{total_attributes}: {attribute.get('attribute_name')}")
                
                try:
                    # Generate rules for this attribute
                    llm_result = await llm_service.generate_data_profiling_rules(
                        attribute_context=attribute,
                        preferred_provider=data_source_config.get("preferred_provider", "claude")
                    )
                    
                    # Create rule records
                    for rule_data in llm_result.get("rules", []):
                        rule = ProfilingRule(
                            version_id=version_id,
                            phase_id=phase_id,
                            attribute_id=attribute.get("attribute_id"),
                            attribute_name=attribute.get("attribute_name"),
                            rule_name=rule_data.get("name"),
                            rule_type=rule_data.get("type"),
                            rule_description=rule_data.get("description"),
                            rule_code=rule_data.get("code"),
                            rule_parameters=rule_data.get("parameters", {}),
                            llm_provider=llm_result.get("model_used"),
                            llm_rationale=rule_data.get("rationale"),
                            llm_confidence_score=rule_data.get("confidence_score"),
                            regulatory_reference=rule_data.get("regulatory_reference"),
                            execution_order=rule_data.get("execution_order", 0),
                            severity=rule_data.get("severity", "medium"),
                            status="pending",
                            created_by_id=user_id
                        )
                        
                        db.add(rule)
                        rules_generated += 1
                    
                    # Commit after each attribute to avoid losing progress
                    await db.commit()
                    logger.info(f"✅ Generated {len(llm_result.get('rules', []))} rules for {attribute.get('attribute_name')}")
                    
                except Exception as e:
                    logger.error(f"Error generating rules for attribute {attribute.get('attribute_name')}: {e}")
                    rules_failed += 1
                    # Continue with next attribute
                    continue
            
            # Update version summary
            version.total_rules = rules_generated
            version.generation_completed_at = datetime.utcnow()
            version.generation_status = "completed"
            await db.commit()
            
            # Update Redis job manager with final result
            if redis_job_manager:
                redis_job_manager.complete_job(
                    task_id,
                    result={
                        'rules_generated': rules_generated,
                        'rules_failed': rules_failed,
                        'total_attributes': total_attributes,
                        'success_rate': f"{(rules_generated / (rules_generated + rules_failed) * 100) if (rules_generated + rules_failed) > 0 else 0:.1f}%"
                    }
                )
            
            return {
                'status': 'completed',
                'rules_generated': rules_generated,
                'rules_failed': rules_failed,
                'total_attributes': total_attributes,
                'message': f"Successfully generated {rules_generated} rules, {rules_failed} failed"
            }
            
        except Exception as e:
            logger.error(f"❌ Error in profiling rule generation: {str(e)}")
            raise


@celery_app.task(
    bind=True,
    base=PausableTask,
    name='app.tasks.data_profiling_celery_tasks.execute_profiling_rules',
    queue='data_processing',
    max_retries=3,
    default_retry_delay=60
)
def execute_profiling_rules_celery_task(
    self,
    version_id: str,
    executed_by: int,
    execution_config: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Celery task for executing profiling rules with pause/resume support
    """
    task_id = self.request.id
    logger.info(f"🚀 Starting profiling rule execution task {task_id}")
    
    # Use Redis job manager for cross-container state
    redis_job_manager = get_redis_job_manager()
    
    # Update job status at start
    redis_job_manager.update_job_progress(
        task_id,
        status="running",
        current_step="Initializing profiling rule execution",
        progress_percentage=0,
        message="Starting profiling rule execution..."
    )
    
    # Check for existing checkpoint
    checkpoint = self.load_checkpoint(task_id)
    start_index = 0
    successful_rules = 0
    failed_rules = 0
    total_records_processed = 0
    total_anomalies_found = 0
    
    if checkpoint:
        logger.info(f"📋 Resuming from checkpoint: {checkpoint}")
        start_index = checkpoint.get('last_processed_index', 0)
        successful_rules = checkpoint.get('successful_rules', 0)
        failed_rules = checkpoint.get('failed_rules', 0)
        total_records_processed = checkpoint.get('total_records_processed', 0)
        total_anomalies_found = checkpoint.get('total_anomalies_found', 0)
    
    # Run async function in sync context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(
            _execute_profiling_rules_with_pause_support(
                task=self,
                task_id=task_id,
                version_id=version_id,
                executed_by=executed_by,
                execution_config=execution_config,
                start_index=start_index,
                initial_successful=successful_rules,
                initial_failed=failed_rules,
                initial_records=total_records_processed,
                initial_anomalies=total_anomalies_found,
                redis_job_manager=redis_job_manager
            )
        )
        
        # Only clear checkpoint if task completed (not paused)
        if result.get('status') != 'paused':
            self.clear_checkpoint(task_id)
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Profiling rule execution task failed: {str(e)}")
        
        # Update Redis job manager with error
        redis_job_manager.complete_job(task_id, error=str(e))
        
        # Save checkpoint on failure for retry
        if 'last_processed_index' in locals():
            self.save_checkpoint(task_id, {
                'last_processed_index': locals().get('last_processed_index', 0),
                'successful_rules': locals().get('successful_rules', 0),
                'failed_rules': locals().get('failed_rules', 0),
                'total_records_processed': locals().get('total_records_processed', 0),
                'total_anomalies_found': locals().get('total_anomalies_found', 0)
            })
        raise
    finally:
        loop.close()


async def _execute_profiling_rules_with_pause_support(
    task: PausableTask,
    task_id: str,
    version_id: str,
    executed_by: int,
    execution_config: Optional[Dict],
    start_index: int = 0,
    initial_successful: int = 0,
    initial_failed: int = 0,
    initial_records: int = 0,
    initial_anomalies: int = 0,
    redis_job_manager = None
) -> Dict[str, Any]:
    """Async helper for profiling rule execution with pause support"""
    
    # Use a fresh event loop for this task to avoid connection conflicts
    current_loop = None
    try:
        current_loop = asyncio.get_running_loop()
        logger.warning("Found existing event loop in task - this may cause issues")
    except RuntimeError:
        logger.info("No existing event loop found - creating new one")
    
    # Create a new database session specifically for this async context
    async with AsyncSessionLocal() as db:
        try:
            # Get version and rules
            version_result = await db.execute(
                select(DataProfilingRuleVersion)
                .where(DataProfilingRuleVersion.version_id == version_id)
            )
            version = version_result.scalar_one_or_none()
            
            if not version:
                raise ValueError(f"Version {version_id} not found")
            
            # Get all rules approved by BOTH tester and report owner
            rules_result = await db.execute(
                select(ProfilingRule)
                .where(
                    and_(
                        ProfilingRule.version_id == version_id,
                        ProfilingRule.tester_decision == 'approved',
                        ProfilingRule.report_owner_decision == 'approved'
                    )
                )
                .order_by(ProfilingRule.execution_order)
            )
            rules = list(rules_result.scalars().all())
            
            if not rules:
                raise ValueError("No rules approved by both tester and report owner found for execution")
            
            # Get profiling service
            profiling_service = DataProfilingService(db)
            
            # Update version execution metadata
            version.execution_started_at = datetime.utcnow()
            version.executed_by = executed_by
            version.background_job_id = task_id
            version.execution_job_id = task_id
            await db.commit()
            
            # Initialize counters
            successful_rules = initial_successful
            failed_rules = initial_failed
            total_records_processed = initial_records
            total_anomalies_found = initial_anomalies
            total_rules = len(rules)
            execution_results = {}
            
            # Process rules one by one
            for i in range(start_index, total_rules):
                # Check if task is paused
                if task.is_paused(task_id):
                    logger.info(f"⏸️ Task {task_id} is paused at rule {i}")
                    # Save checkpoint
                    task.save_checkpoint(task_id, {
                        'last_processed_index': i,
                        'successful_rules': successful_rules,
                        'failed_rules': failed_rules,
                        'total_records_processed': total_records_processed,
                        'total_anomalies_found': total_anomalies_found
                    })
                    
                    # Update Redis job manager if available
                    if redis_job_manager:
                        redis_job_manager.update_job_progress(
                            task_id,
                            status="paused",
                            current_step=f"Paused at rule {i} of {total_rules}",
                            message=f"Task paused. Successful: {successful_rules}, Failed: {failed_rules}"
                        )
                    
                    # Update task state
                    task.update_state(
                        state='PAUSED',
                        meta={
                            'current': i,
                            'total': total_rules,
                            'status': f'Paused at rule {i} of {total_rules}',
                            'successful_rules': successful_rules,
                            'failed_rules': failed_rules
                        }
                    )
                    return {
                        'status': 'paused',
                        'last_processed_index': i,
                        'successful_rules': successful_rules,
                        'failed_rules': failed_rules,
                        'total_records_processed': total_records_processed,
                        'total_anomalies_found': total_anomalies_found
                    }
                
                rule = rules[i]
                
                # Update progress
                progress_percentage = int((i / total_rules) * 100)
                
                # Update Redis job manager if available
                if redis_job_manager:
                    redis_job_manager.update_job_progress(
                        task_id,
                        progress_percentage=progress_percentage,
                        current_step=f"Executing rule: {rule.rule_name}",
                        total_steps=total_rules,
                        completed_steps=i,
                        message=f"Processing rule {i+1} of {total_rules}"
                    )
                
                # Also update Celery task state
                task.update_state(
                    state='PROGRESS',
                    meta={
                        'current': i,
                        'total': total_rules,
                        'status': f'Executing rule {i+1} of {total_rules}: {rule.rule_name}',
                        'progress_percentage': progress_percentage,
                        'successful_rules': successful_rules,
                        'failed_rules': failed_rules
                    }
                )
                
                logger.info(f"🔄 Executing rule {i+1}/{total_rules}: {rule.rule_name}")
                
                try:
                    # Execute individual rule
                    result = await profiling_service.execute_rule(
                        rule, 
                        execution_config or {}
                    )
                    
                    execution_results[str(rule.rule_id)] = {
                        "rule_name": rule.rule_name,
                        "rule_type": rule.rule_type,
                        "status": "success",
                        "records_processed": result.get("records_processed", 0),
                        "records_passed": result.get("records_passed", 0),
                        "records_failed": result.get("records_failed", 0),
                        "pass_rate": result.get("pass_rate", 0.0),
                        "execution_time_ms": result.get("execution_time_ms", 0),
                        "quality_scores": result.get("quality_scores", {}),
                        "anomaly_details": result.get("anomaly_details", []),
                        "statistical_summary": result.get("statistical_summary", {})
                    }
                    
                    successful_rules += 1
                    total_records_processed += result.get("records_processed", 0)
                    total_anomalies_found += len(result.get("anomaly_details", []))
                    
                    logger.info(f"✅ Rule {rule.rule_name} executed successfully")
                    
                except Exception as rule_error:
                    execution_results[str(rule.rule_id)] = {
                        "rule_name": rule.rule_name,
                        "rule_type": rule.rule_type,
                        "status": "failed",
                        "error": str(rule_error),
                        "execution_time_ms": 0
                    }
                    
                    failed_rules += 1
                    logger.error(f"❌ Rule {rule.rule_name} failed: {str(rule_error)}")
            
            # Update version with results
            version.execution_completed_at = datetime.utcnow()
            version.total_records_processed = total_records_processed
            
            # Calculate overall quality score as average pass rate
            if successful_rules > 0:
                total_pass_rate = sum(
                    result.get("pass_rate", 0) 
                    for result in execution_results.values() 
                    if result.get("status") == "success"
                )
                version.overall_quality_score = (total_pass_rate / successful_rules)
            else:
                version.overall_quality_score = 0
            
            await db.commit()
            
            # Complete the job in Redis job manager
            if redis_job_manager:
                redis_job_manager.complete_job(
                    task_id,
                    result={
                        "status": "success",
                        "version_id": version_id,
                        "summary": {
                            "total_rules": total_rules,
                            "successful_rules": successful_rules,
                            "failed_rules": failed_rules,
                            "total_records_processed": total_records_processed,
                            "total_anomalies_found": total_anomalies_found
                        },
                        "execution_time_seconds": (
                            version.execution_completed_at - version.execution_started_at
                        ).total_seconds()
                    }
                )
            
            return {
                "status": "completed",
                "version_id": version_id,
                "summary": {
                    "total_rules": total_rules,
                    "successful_rules": successful_rules,
                    "failed_rules": failed_rules,
                    "total_records_processed": total_records_processed,
                    "total_anomalies_found": total_anomalies_found
                },
                "execution_time_seconds": (
                    version.execution_completed_at - version.execution_started_at
                ).total_seconds()
            }
            
        except Exception as e:
            logger.error(f"❌ Error in profiling rule execution: {str(e)}")
            
            # Update version status to indicate execution failed
            try:
                version_result = await db.execute(
                    select(DataProfilingRuleVersion)
                    .where(DataProfilingRuleVersion.version_id == version_id)
                )
                version = version_result.scalar_one_or_none()
                
                if version:
                    version.execution_completed_at = datetime.utcnow()
                    await db.commit()
                    
            except Exception as update_error:
                logger.error(f"Failed to update version status: {str(update_error)}")
            
            raise


@celery_app.task(name='app.tasks.data_profiling_celery_tasks.pause_profiling_generation')
def pause_profiling_generation_task(task_id: str) -> Dict[str, Any]:
    """Pause a running profiling rule generation task"""
    task = generate_profiling_rules_celery_task
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


@celery_app.task(name='app.tasks.data_profiling_celery_tasks.resume_profiling_generation')
def resume_profiling_generation_task(original_task_id: str) -> Dict[str, Any]:
    """Resume a paused profiling rule generation task"""
    # Get the task instance
    task_instance = generate_profiling_rules_celery_task
    
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
    
    if not original_args or len(original_args) < 5:
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
    new_task = generate_profiling_rules_celery_task.apply_async(
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


@celery_app.task(name='app.tasks.data_profiling_celery_tasks.pause_profiling_execution')
def pause_profiling_execution_task(task_id: str) -> Dict[str, Any]:
    """Pause a running profiling rule execution task"""
    task = execute_profiling_rules_celery_task
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


@celery_app.task(name='app.tasks.data_profiling_celery_tasks.resume_profiling_execution')
def resume_profiling_execution_task(original_task_id: str) -> Dict[str, Any]:
    """Resume a paused profiling rule execution task"""
    # Get the task instance
    task_instance = execute_profiling_rules_celery_task
    
    # Load checkpoint
    checkpoint = task_instance.load_checkpoint(original_task_id)
    if not checkpoint:
        logger.error(f"No checkpoint found for task {original_task_id}")
        return {
            'status': 'error',
            'message': 'No checkpoint found for task'
        }
    
    # Get the original task data from Celery backend
    result = AsyncResult(original_task_id, app=celery_app)
    backend_result = celery_app.backend.get_task_meta(original_task_id)
    original_args = backend_result.get('args', [])
    original_kwargs = backend_result.get('kwargs', {})
    
    if not original_args or len(original_args) < 3:
        logger.error(f"Cannot retrieve original task parameters for {original_task_id}")
        return {
            'status': 'error',
            'message': 'Cannot retrieve original task parameters. Task data may have expired.'
        }
    
    # Clear pause state
    task_instance.resume(original_task_id)
    
    # Update job status to resuming
    redis_job_manager = get_redis_job_manager()
    redis_job_manager.update_job_progress(
        original_task_id,
        status="resuming",
        current_step="Resuming task from checkpoint",
        message=f"Resuming from rule {checkpoint.get('last_processed_index', 0)}"
    )
    
    # Start new task from checkpoint with the same task ID
    new_task = execute_profiling_rules_celery_task.apply_async(
        args=original_args,
        kwargs=original_kwargs,
        task_id=original_task_id,  # Reuse the same task ID
        queue='data_processing'
    )
    
    return {
        'status': 'resumed',
        'task_id': original_task_id,
        'checkpoint': checkpoint,
        'message': f'Task resumed from rule {checkpoint.get("last_processed_index", 0)}'
    }


@celery_app.task(
    bind=True,
    name='app.tasks.data_profiling_celery_tasks.execute_profiling_rules_sync',
    queue='data_processing',
    max_retries=3,
    default_retry_delay=60
)
def execute_profiling_rules_sync_task(
    self,
    version_id: str,
    executed_by: int,
    execution_config: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Sync Celery task for executing profiling rules (no asyncio complexity)
    """
    task_id = self.request.id
    logger.info(f"🚀 Starting sync profiling rule execution task {task_id}")
    
    # Use Redis job manager for cross-container state
    redis_job_manager = get_redis_job_manager()
    
    # Update job status at start
    redis_job_manager.update_job_progress(
        task_id,
        status="running",
        current_step="Initializing sync profiling rule execution",
        progress_percentage=0,
        message="Starting sync profiling rule execution..."
    )
    
    try:
        # Use sync database session
        with SyncSessionLocal() as db:
            # Get version and rules (sync queries)
            version = db.get(DataProfilingRuleVersion, version_id)
            
            if not version:
                raise ValueError(f"Version {version_id} not found")
            
            # Get all rules approved by BOTH tester and report owner
            rules = db.execute(
                select(ProfilingRule)
                .where(
                    and_(
                        ProfilingRule.version_id == version_id,
                        ProfilingRule.tester_decision == 'approved',
                        ProfilingRule.report_owner_decision == 'approved'
                    )
                )
                .order_by(ProfilingRule.execution_order)
            ).scalars().all()
            
            if not rules:
                raise ValueError("No rules approved by both tester and report owner found for execution")
            
            # Update version execution metadata
            version.execution_started_at = datetime.utcnow()
            version.executed_by = executed_by
            version.background_job_id = task_id
            version.execution_job_id = task_id
            db.commit()
            
            # Initialize counters
            successful_rules = 0
            failed_rules = 0
            total_rules = len(rules)
            execution_results = {}
            
            logger.info(f"Processing {total_rules} rules for version {version_id}")
            
            # Process rules one by one
            for i, rule in enumerate(rules):
                progress_percentage = int((i / total_rules) * 100)
                
                # Update progress
                redis_job_manager.update_job_progress(
                    task_id,
                    progress_percentage=progress_percentage,
                    current_step=f"Executing rule: {rule.rule_name}",
                    total_steps=total_rules,
                    completed_steps=i,
                    message=f"Processing rule {i+1} of {total_rules}"
                )
                
                logger.info(f"🔄 Executing rule {i+1}/{total_rules}: {rule.rule_name}")
                
                try:
                    # Execute individual rule (sync version)
                    result = execute_single_rule_sync(rule, execution_config or {}, db)
                    
                    # Check if the result indicates a failed execution
                    if result.get("execution_status") == "failed":
                        raise Exception(result.get("error", "Rule execution failed"))
                    
                    execution_results[str(rule.rule_id)] = {
                        "rule_name": rule.rule_name,
                        "rule_type": rule.rule_type,
                        "status": "success",
                        "records_processed": result.get("records_processed", 0),
                        "records_passed": result.get("records_passed", 0),
                        "records_failed": result.get("records_failed", 0),
                        "pass_rate": result.get("pass_rate", 0.0),
                        "execution_time_ms": result.get("execution_time_ms", 0),
                    }
                    
                    # Save execution result to database
                    from app.models.data_profiling import ProfilingResult
                    
                    # Convert numpy types to Python native types to avoid psycopg2 adapter errors
                    def to_native_type(value):
                        if hasattr(value, 'item'):  # numpy scalar
                            return value.item()
                        return value
                    
                    execution_result = ProfilingResult(
                        phase_id=rule.phase_id,
                        rule_id=rule.rule_id,
                        attribute_id=rule.attribute_id,
                        execution_status="success",
                        execution_time_ms=to_native_type(result.get("execution_time_ms", 0)),
                        passed_count=to_native_type(result.get("records_passed", 0)),
                        failed_count=to_native_type(result.get("records_failed", 0)),
                        total_count=to_native_type(result.get("records_processed", 0)),
                        pass_rate=float(to_native_type(result.get("pass_rate", 0.0))),
                        result_summary=result.get("quality_scores", {}),
                        failed_records=result.get("anomaly_details", []),
                        result_details=json.dumps({
                            "statistical_summary": result.get("statistical_summary", {}),
                            "version_id": str(version_id),
                            "job_id": task_id
                        }),
                        quality_impact=float(to_native_type(result.get("quality_impact", 0.0))),
                        severity=rule.severity,
                        created_by_id=executed_by,
                        updated_by_id=executed_by
                    )
                    db.add(execution_result)
                    
                    successful_rules += 1
                    logger.info(f"✅ Rule {rule.rule_name} executed successfully")
                    
                except Exception as rule_error:
                    execution_results[str(rule.rule_id)] = {
                        "rule_name": rule.rule_name,
                        "rule_type": rule.rule_type,
                        "status": "failed",
                        "error": str(rule_error),
                        "execution_time_ms": 0
                    }
                    
                    # Save failed execution result to database
                    from app.models.data_profiling import ProfilingResult
                    failed_result = ProfilingResult(
                        phase_id=rule.phase_id,
                        rule_id=rule.rule_id,
                        attribute_id=rule.attribute_id,
                        execution_status="failed",
                        execution_time_ms=0,
                        passed_count=0,
                        failed_count=0,
                        total_count=0,
                        pass_rate=0.0,
                        result_summary={},
                        failed_records=[],
                        result_details=json.dumps({
                            "error": str(rule_error),
                            "version_id": str(version_id),
                            "job_id": task_id
                        }),
                        quality_impact=0.0,
                        severity=rule.severity,
                        created_by_id=executed_by,
                        updated_by_id=executed_by
                    )
                    db.add(failed_result)
                    
                    failed_rules += 1
                    logger.error(f"❌ Rule {rule.rule_name} failed: {str(rule_error)}")
            
            # Commit all results to database before updating version
            db.commit()
            
            # Update version with results
            version.execution_completed_at = datetime.utcnow()
            
            # Calculate overall quality score as average pass rate
            if successful_rules > 0:
                total_pass_rate = sum(
                    result.get("pass_rate", 0) 
                    for result in execution_results.values() 
                    if result.get("status") == "success"
                )
                version.overall_quality_score = (total_pass_rate / successful_rules)
            else:
                version.overall_quality_score = 0
            
            db.commit()
            
            # Complete the job in Redis job manager
            redis_job_manager.complete_job(
                task_id,
                result={
                    "status": "success",
                    "version_id": version_id,
                    "summary": {
                        "total_rules": total_rules,
                        "successful_rules": successful_rules,
                        "failed_rules": failed_rules,
                    },
                    "execution_time_seconds": (
                        version.execution_completed_at - version.execution_started_at
                    ).total_seconds()
                }
            )
            
            logger.info(f"✅ Completed profiling rule execution for version {version_id}")
            
            return {
                "status": "completed",
                "version_id": version_id,
                "summary": {
                    "total_rules": total_rules,
                    "successful_rules": successful_rules,
                    "failed_rules": failed_rules,
                },
                "execution_time_seconds": (
                    version.execution_completed_at - version.execution_started_at
                ).total_seconds()
            }
            
    except Exception as e:
        logger.error(f"❌ Error in sync profiling rule execution: {str(e)}")
        
        # Update Redis job manager with error
        redis_job_manager.complete_job(task_id, error=str(e))
        
        raise


def execute_single_rule_sync(rule: ProfilingRule, execution_config: Dict, db) -> Dict[str, Any]:
    """Execute a single profiling rule synchronously - completely sync implementation"""
    import pandas as pd
    import numpy as np
    import time
    from sqlalchemy import text
    
    try:
        start_time = time.time()
        
        # Get PDE mapping for this rule's attribute from the Planning phase
        # PDE mappings are created in Planning phase, not Data Profiling phase
        from app.models.planning import PlanningPDEMapping
        
        # First get the Planning phase_id for this cycle/report
        planning_phase_result = db.execute(
            text("""
                SELECT p.phase_id 
                FROM workflow_phases p
                WHERE p.cycle_id = (SELECT cycle_id FROM workflow_phases WHERE phase_id = :data_profiling_phase_id)
                AND p.report_id = (SELECT report_id FROM workflow_phases WHERE phase_id = :data_profiling_phase_id)
                AND p.phase_name = 'Planning'
            """),
            {"data_profiling_phase_id": rule.phase_id}
        )
        planning_phase = planning_phase_result.fetchone()
        
        if not planning_phase:
            logger.warning(f"No Planning phase found for Data Profiling phase {rule.phase_id}")
            return {
                "execution_status": "failed",
                "records_processed": 0,
                "records_passed": 0,
                "records_failed": 0,
                "pass_rate": 0,
                "error": "No Planning phase found"
            }
        
        planning_phase_id = planning_phase[0]
        
        # Now get PDE mapping from Planning phase
        pde_mapping_result = db.execute(
            text("""
                SELECT pde_code, data_source_id 
                FROM cycle_report_planning_pde_mappings 
                WHERE phase_id = :phase_id AND attribute_id = :attribute_id
                LIMIT 1
            """),
            {"phase_id": planning_phase_id, "attribute_id": rule.attribute_id}
        )
        pde_mapping = pde_mapping_result.fetchone()
        
        if not pde_mapping:
            logger.warning(f"No PDE mapping found for attribute {rule.attribute_id}")
            return {
                "execution_status": "failed",
                "records_processed": 0,
                "records_passed": 0,
                "records_failed": 0,
                "pass_rate": 0,
                "error": "No PDE mapping found"
            }
        
        # Get data source
        from app.models.cycle_report_data_source import CycleReportDataSource
        data_source_result = db.execute(
            text("""
                SELECT connection_config 
                FROM cycle_report_planning_data_sources 
                WHERE id = :data_source_id
            """),
            {"data_source_id": pde_mapping.data_source_id}
        )
        data_source_row = data_source_result.fetchone()
        
        if not data_source_row:
            logger.warning(f"No data source found with id {pde_mapping.data_source_id}")
            return {
                "execution_status": "failed",
                "records_processed": 0,
                "records_passed": 0,
                "records_failed": 0,
                "pass_rate": 0,
                "error": "No data source found"
            }
        
        # Get connection config
        connection_config = data_source_row.connection_config
        
        # Connect to the data source and load data
        import psycopg2
        conn_str = f"host={connection_config.get('host', 'localhost')} port={connection_config.get('port', '5432')} dbname={connection_config.get('database', 'synapse_dt')} user=synapse_user password=synapse_password"
        
        with psycopg2.connect(conn_str) as conn:
            table_name = connection_config.get('table_name', 'data_table')
            schema_name = connection_config.get('schema', 'public')
            column_name = pde_mapping.pde_code  # This is the actual column name
            
            # Load data
            query = f"SELECT {column_name} FROM {schema_name}.{table_name}"
            df = pd.read_sql_query(query, conn)
            
            logger.info(f"Loaded {len(df)} records for rule {rule.rule_name}")
            
            # Execute the rule code
            import re
            exec_globals = {
                'pd': pd,
                'np': np,
                'df': df,
                'column_name': column_name,
                'len': len,
                'sum': sum,
                'float': float,
                'int': int,
                'str': str,
                'isinstance': isinstance,
                'range': range,
                're': re
            }
            exec_locals = {}
            
            # Execute the LLM-generated function
            if rule.rule_code.strip().startswith('def check_rule'):
                exec(rule.rule_code, exec_globals, exec_locals)
                
                # Call the function
                result = exec_locals['check_rule'](df, column_name)
                
                # Standardize the result
                execution_time_ms = int((time.time() - start_time) * 1000)
                
                return {
                    "execution_status": "success",
                    "records_processed": result.get('total', len(df)),
                    "records_passed": result.get('passed', 0),
                    "records_failed": result.get('failed', 0),
                    "pass_rate": result.get('pass_rate', 0),
                    "execution_time_ms": execution_time_ms,
                    "quality_scores": {},
                    "anomaly_details": [],
                    "statistical_summary": {}
                }
            else:
                # Fallback for non-function rules
                return {
                    "execution_status": "failed",
                    "records_processed": 0,
                    "records_passed": 0,
                    "records_failed": 0,
                    "pass_rate": 0,
                    "error": "Rule code format not supported"
                }
                
    except Exception as e:
        logger.error(f"Error executing rule {rule.rule_name}: {str(e)}")
        return {
            "execution_status": "failed",
            "records_processed": 0,
            "records_passed": 0,
            "records_failed": 0,
            "pass_rate": 0,
            "execution_time_ms": 0,
            "error": str(e)
        }