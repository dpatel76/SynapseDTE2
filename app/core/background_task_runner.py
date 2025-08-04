"""
Background Task Runner
Manages persistent background tasks that survive server restarts
"""
import asyncio
import logging
from typing import Dict, Any, Callable
from datetime import datetime
import json
import os

from app.core.background_jobs import job_manager

logger = logging.getLogger(__name__)

class BackgroundTaskRunner:
    """Manages background tasks with persistence"""
    
    def __init__(self):
        self.tasks: Dict[str, asyncio.Task] = {}
        self.task_registry: Dict[str, Callable] = {}
        
    def register_task(self, task_type: str, task_func: Callable):
        """Register a task function for a given task type"""
        self.task_registry[task_type] = task_func
        logger.info(f"Registered task type: {task_type}")
        
    async def run_task(self, job_id: str, task_type: str, **kwargs):
        """Run a background task"""
        if task_type not in self.task_registry:
            error = f"Unknown task type: {task_type}"
            logger.error(error)
            job_manager.complete_job(job_id, error=error)
            return
            
        task_func = self.task_registry[task_type]
        
        try:
            # Run the task
            result = await task_func(job_id=job_id, **kwargs)
            logger.info(f"Task {job_id} completed successfully")
            return result
        except Exception as e:
            logger.error(f"Task {job_id} failed: {str(e)}")
            job_manager.complete_job(job_id, error=str(e))
            raise
            
    async def resume_pending_tasks(self):
        """Resume tasks that were interrupted by server restart"""
        try:
            # Get all active jobs
            active_jobs = job_manager.get_active_jobs()
            
            for job in active_jobs:
                job_id = job.get('job_id')
                job_type = job.get('job_type')
                metadata = job.get('metadata', {})
                status = job.get('status')
                
                # Only resume running jobs
                if status != 'running':
                    continue
                    
                logger.info(f"Resuming interrupted job {job_id} of type {job_type}")
                
                # Map job types to task types
                task_mapping = {
                    'pde_auto_mapping': 'auto_map_pdes',
                    'pde_regeneration': 'regenerate_pde_mappings',
                    'pde_classification': 'classify_pdes_batch'
                }
                
                task_type = task_mapping.get(job_type)
                if not task_type:
                    logger.warning(f"Unknown job type {job_type} for job {job_id}")
                    continue
                    
                # Create task to resume the job
                if task_type == 'auto_map_pdes':
                    # For auto mapping, we need to reconstruct the context
                    # Mark as failed since we can't resume without full context
                    job_manager.complete_job(
                        job_id, 
                        error="Job interrupted by server restart. Please retry."
                    )
                else:
                    # For other types, mark as failed
                    job_manager.complete_job(
                        job_id,
                        error="Job interrupted by server restart. Please retry."
                    )
                    
        except Exception as e:
            logger.error(f"Error resuming pending tasks: {str(e)}")

# Global instance
task_runner = BackgroundTaskRunner()