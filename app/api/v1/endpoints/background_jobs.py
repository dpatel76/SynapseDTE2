"""
Background Jobs API endpoints for managing long-running operations
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.dependencies import get_current_user
from app.models.user import User
from app.core.background_jobs import job_manager
from app.core.redis_job_manager import get_redis_job_manager
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

@router.get("/test")
async def test_jobs_system():
    """
    Test endpoint to check if the background jobs system is working
    """
    active_jobs_count = len(job_manager.get_active_jobs())
    total_jobs_count = len(job_manager.jobs)
    
    return {
        "status": "healthy",
        "active_jobs": active_jobs_count,
        "total_jobs": total_jobs_count,
        "message": "Background jobs system is working"
    }

@router.get("/{job_id}/status")
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get the status of a background job
    """
    logger.info(f"🔍 GET /jobs/{job_id}/status called")
    logger.info(f"📊 Current user: {current_user.email if current_user else 'None'}")
    logger.info(f"📋 Total jobs in manager: {len(job_manager.jobs)}")
    
    # Try Redis job manager first (for Celery tasks)
    redis_job_manager = get_redis_job_manager()
    job_status = redis_job_manager.get_job_status(job_id)
    
    # If not found in Redis, try file-based job manager
    if not job_status:
        from app.core.celery_job_sync import get_job_status_with_sync
        job_status = get_job_status_with_sync(job_id)
    
    if not job_status:
        logger.warning(f"❌ Job {job_id} not found - returning 404")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    logger.info(f"✅ Returning job status for {job_id}")
    return job_status

@router.get("/active")
async def get_active_jobs(
    current_user: User = Depends(get_current_user)
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get all active jobs for the current user
    """
    # Get jobs from both managers
    redis_job_manager = get_redis_job_manager()
    redis_jobs = redis_job_manager.get_active_jobs()
    file_jobs = job_manager.get_active_jobs()
    
    # Combine and deduplicate
    all_jobs = redis_jobs + file_jobs
    seen_ids = set()
    unique_jobs = []
    
    for job in all_jobs:
        job_id = job.get("job_id")
        if job_id and job_id not in seen_ids:
            seen_ids.add(job_id)
            unique_jobs.append(job)
    
    return {
        "active_jobs": unique_jobs
    }

@router.post("/{job_id}/cancel")
async def cancel_job(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Cancel a running job
    """
    # Check Redis job manager first
    redis_job_manager = get_redis_job_manager()
    job_status = redis_job_manager.get_job_status(job_id)
    
    # Fallback to file-based job manager
    if not job_status:
        job_status = job_manager.get_job_status(job_id)
    
    if not job_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    if job_status["status"] not in ["pending", "running"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job cannot be cancelled in current state"
        )
    
    # Cancel in both managers to ensure consistency
    redis_job_manager.cancel_job(job_id)
    job_manager.cancel_job(job_id)
    
    return {
        "message": "Job cancelled successfully",
        "job_id": job_id
    }

@router.post("/{job_id}/pause")
async def pause_job(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Pause a running job (only works for Celery-based tasks)
    """
    logger.info(f"⏸️ Pausing job {job_id}")
    
    # Check Redis job manager first
    redis_job_manager = get_redis_job_manager()
    job_status = redis_job_manager.get_job_status(job_id)
    
    # Fallback to file-based job manager
    if not job_status:
        job_status = job_manager.get_job_status(job_id)
    
    if not job_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    if job_status["status"] != "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job is not running and cannot be paused"
        )
    
    # Check if this is a Celery task
    metadata = job_status.get("metadata", {})
    if not metadata.get("celery_task_id"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This job type does not support pause/resume"
        )
    
    # Import and call pause task
    from app.tasks.planning_celery_tasks import pause_pde_mapping_task
    
    pause_result = pause_pde_mapping_task.apply_async(args=[job_id])
    
    # Update job status in Redis (Celery tasks use Redis)
    redis_job_manager.update_job_progress(
        job_id,
        status="pausing",
        message="Job pause requested"
    )
    
    return {
        "message": "Job pause requested",
        "job_id": job_id,
        "pause_task_id": pause_result.id
    }

@router.post("/{job_id}/resume")
async def resume_job(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Resume a paused job (only works for Celery-based tasks)
    """
    logger.info(f"▶️ Resuming job {job_id}")
    
    # Check Redis job manager first
    redis_job_manager = get_redis_job_manager()
    job_status = redis_job_manager.get_job_status(job_id)
    
    # Fallback to file-based job manager
    if not job_status:
        job_status = job_manager.get_job_status(job_id)
    
    if not job_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Accept both 'paused' and 'PAUSED' status
    if job_status["status"] not in ["paused", "PAUSED", "pausing"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job is not paused (current status: {job_status['status']})"
        )
    
    # Check if this is a Celery task
    metadata = job_status.get("metadata", {})
    if not metadata.get("celery_task_id"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This job type does not support pause/resume"
        )
    
    # Import and call resume task
    from app.tasks.planning_celery_tasks import resume_pde_mapping_task
    
    resume_result = resume_pde_mapping_task.apply_async(args=[job_id])
    
    # Note: The job manager status will be updated by the resumed task
    
    return {
        "message": "Job resume requested",
        "original_job_id": job_id,
        "resume_task_id": resume_result.id
    } 