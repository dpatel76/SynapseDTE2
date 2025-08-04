"""
Background Jobs API endpoints for managing long-running operations
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.dependencies import get_current_user
from app.models.user import User
from app.core.background_jobs import job_manager
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
    
    job_status = job_manager.get_job_status(job_id)
    
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
    active_jobs = job_manager.get_active_jobs()
    
    return {
        "active_jobs": active_jobs
    }

@router.post("/{job_id}/cancel")
async def cancel_job(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Cancel a running job
    """
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
    
    job_manager.cancel_job(job_id)
    
    return {
        "message": "Job cancelled successfully",
        "job_id": job_id
    } 