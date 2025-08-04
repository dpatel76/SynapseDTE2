"""
Background tasks for observation detection
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select, and_

from app.core.config import settings
from app.core.job_manager import job_manager
from app.models.workflow import WorkflowPhase
from app.models.observation_management import ObservationRecord
from app.services.observation_detection_service import ObservationDetectionService

logger = logging.getLogger(__name__)

# Create async engine for background tasks
engine = create_async_engine(settings.DATABASE_URL_ASYNC)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def run_observation_detection_job(
    job_id: str,
    phase_id: int,
    cycle_id: int, 
    report_id: int,
    user_id: int,
    batch_size: int = 100
) -> Dict[str, Any]:
    """
    Background job to detect observations from failed test executions
    
    Args:
        job_id: Job ID for tracking
        phase_id: Phase ID
        cycle_id: Cycle ID
        report_id: Report ID
        user_id: User ID initiating the detection
        batch_size: Number of test executions to process per batch
        
    Returns:
        Detection results
    """
    logger.info(f"Starting observation detection job {job_id} for phase {phase_id}")
    
    try:
        # Create new session for async task (CRITICAL: Session management lesson)
        async with AsyncSessionLocal() as task_db:
            # Update job status to running (CRITICAL: Job status lesson)
            job_manager.update_job_progress(
                job_id,
                status="running",
                current_step="Starting observation detection",
                progress_percentage=0
            )
            
            # Verify phase exists
            phase_query = select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.phase_id == phase_id,
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Observation Management"
                )
            )
            phase_result = await task_db.execute(phase_query)
            phase = phase_result.scalar_one_or_none()
            
            if not phase:
                error_msg = f"Observation Management phase not found for cycle {cycle_id}, report {report_id}"
                logger.error(error_msg)
                job_manager.update_job_progress(
                    job_id,
                    status="failed",
                    error=error_msg
                )
                return {"success": False, "error": error_msg}
            
            # Update progress
            job_manager.update_job_progress(
                job_id,
                status="running",
                current_step="Creating detection service",
                progress_percentage=10
            )
            
            # Create detection service
            detection_service = ObservationDetectionService(task_db)
            
            # Run detection
            job_manager.update_job_progress(
                job_id,
                status="running",
                current_step="Detecting observations from failed tests",
                progress_percentage=20
            )
            
            try:
                detection_results = await detection_service.detect_observations_from_failures(
                    phase_id=phase_id,
                    cycle_id=cycle_id,
                    report_id=report_id,
                    detection_user_id=user_id,
                    batch_size=batch_size
                )
                
                # Update progress based on results
                job_manager.update_job_progress(
                    job_id,
                    status="running",
                    current_step="Detection complete, finalizing results",
                    progress_percentage=90,
                    metadata={
                        "processed_count": detection_results.get("processed_count", 0),
                        "groups_created": detection_results.get("groups_created", 0),
                        "observations_created": detection_results.get("observations_created", 0)
                    }
                )
                
                # Update phase metadata
                if not phase.metadata:
                    phase.metadata = {}
                phase.metadata["last_detection_run"] = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "results": detection_results,
                    "job_id": job_id
                }
                phase.updated_at = datetime.utcnow()
                phase.updated_by_id = user_id
                
                await task_db.commit()
                
                # Complete job
                job_manager.update_job_progress(
                    job_id,
                    status="completed",
                    current_step="Observation detection completed successfully",
                    progress_percentage=100,
                    result=detection_results
                )
                
                logger.info(f"Observation detection job {job_id} completed: {detection_results}")
                return {
                    "success": True,
                    "results": detection_results
                }
                
            except Exception as e:
                logger.error(f"Error during observation detection: {str(e)}")
                await task_db.rollback()
                
                job_manager.update_job_progress(
                    job_id,
                    status="failed", 
                    error=str(e),
                    current_step="Detection failed"
                )
                
                return {
                    "success": False,
                    "error": str(e)
                }
                
    except Exception as e:
        logger.error(f"Critical error in observation detection job {job_id}: {str(e)}")
        job_manager.update_job_progress(
            job_id,
            status="failed",
            error=f"Critical error: {str(e)}"
        )
        return {
            "success": False,
            "error": str(e)
        }


async def check_and_create_observations_batch(
    phase_id: int,
    cycle_id: int,
    report_id: int,
    user_id: int,
    auto_create: bool = True,
    batch_size: int = 100
) -> str:
    """
    Check for failed tests and optionally create observations
    
    Args:
        phase_id: Phase ID
        cycle_id: Cycle ID 
        report_id: Report ID
        user_id: User ID
        auto_create: Whether to automatically create observations
        batch_size: Batch size for processing
        
    Returns:
        Job ID for tracking
    """
    # Create job
    job_id = job_manager.create_job(
        job_type="observation_detection",
        description=f"Detect observations for phase {phase_id}",
        created_by=user_id,
        metadata={
            "phase_id": phase_id,
            "cycle_id": cycle_id,
            "report_id": report_id,
            "auto_create": auto_create,
            "batch_size": batch_size
        }
    )
    
    # Schedule async task
    try:
        from app.core.celery import celery_app
        celery_app.send_task(
            "app.tasks.observation_detection_tasks.run_observation_detection_job",
            args=[job_id, phase_id, cycle_id, report_id, user_id, batch_size]
        )
    except Exception as e:
        logger.warning(f"Celery not available, running synchronously: {e}")
        # Run directly if Celery not available
        import asyncio
        asyncio.create_task(
            run_observation_detection_job(
                job_id, phase_id, cycle_id, report_id, user_id, batch_size
            )
        )
    
    return job_id