"""
Celery Job Synchronization
Syncs Celery task states with the job manager
"""
import logging
from typing import Optional, Dict, Any
from celery.result import AsyncResult
from app.core.celery_app import celery_app
from app.core.background_jobs import job_manager

logger = logging.getLogger(__name__)

# Map Celery states to our job states
CELERY_STATE_MAPPING = {
    'PENDING': 'pending',
    'STARTED': 'running',
    'SUCCESS': 'completed',
    'FAILURE': 'failed',
    'RETRY': 'running',
    'REVOKED': 'cancelled',
    'PROGRESS': 'running',
    'PAUSED': 'paused'
}


def sync_celery_task_status(job_id: str) -> Optional[Dict[str, Any]]:
    """
    Sync Celery task status with job manager
    """
    try:
        # Get job from job manager
        job_status = job_manager.get_job_status(job_id)
        if not job_status:
            return None
        
        # Check if this is a Celery task
        metadata = job_status.get('metadata', {})
        celery_task_id = metadata.get('celery_task_id')
        
        if not celery_task_id:
            # Not a Celery task, return as-is
            return job_status
        
        # Get Celery task result
        result = AsyncResult(celery_task_id, app=celery_app)
        
        # Map Celery state to our state
        celery_state = result.state
        mapped_state = CELERY_STATE_MAPPING.get(celery_state, 'unknown')
        
        # Get task info
        task_info = result.info or {}
        
        # Update job manager if states differ
        if job_status['status'] != mapped_state:
            update_data = {
                'status': mapped_state
            }
            
            # Extract progress information from Celery task
            if isinstance(task_info, dict):
                if 'current' in task_info and 'total' in task_info:
                    progress = int((task_info['current'] / task_info['total']) * 100)
                    update_data['progress_percentage'] = progress
                
                if 'status' in task_info:
                    update_data['message'] = task_info['status']
                
                if 'total_mapped' in task_info:
                    update_data['result'] = {
                        'total_mapped': task_info.get('total_mapped', 0),
                        'total_failed': task_info.get('total_failed', 0)
                    }
            
            # Handle completed state
            if celery_state == 'SUCCESS':
                update_data['completed_at'] = result.date_done
                if isinstance(task_info, dict):
                    update_data['result'] = task_info
            
            # Handle failure state
            elif celery_state == 'FAILURE':
                update_data['error'] = str(result.info)
            
            # Update job manager
            job_manager.update_job_progress(job_id, **update_data)
            
            # Get updated status
            job_status = job_manager.get_job_status(job_id)
        
        # Add Celery-specific info
        job_status['celery_state'] = celery_state
        job_status['celery_info'] = task_info
        
        return job_status
        
    except Exception as e:
        logger.error(f"Error syncing Celery task status for job {job_id}: {e}")
        return job_manager.get_job_status(job_id)


def get_job_status_with_sync(job_id: str) -> Optional[Dict[str, Any]]:
    """
    Get job status with Celery synchronization
    """
    return sync_celery_task_status(job_id)