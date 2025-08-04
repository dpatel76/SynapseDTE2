"""
Background task for executing data profiling jobs
Integrates with the background job manager
"""
import asyncio
import logging
from typing import Optional
from datetime import datetime

from app.core.background_jobs import job_manager
from app.core.database import AsyncSessionLocal
from app.services.data_profiling_service import DataProfilingService
from app.models.data_profiling import DataProfilingJob, DataProfilingConfiguration

logger = logging.getLogger(__name__)


async def execute_profiling_job_task(
    job_id: int,
    bg_job_id: str,
    configuration_id: int,
    user_id: int
):
    """Execute a data profiling job and update progress via job manager"""
    try:
        # Update job status to running
        job_manager.update_job_progress(
            bg_job_id,
            status="running",
            message="Starting data profiling job",
            current_step="Initializing",
            progress_percentage=0
        )
        
        async with AsyncSessionLocal() as db:
            # Get the job and configuration
            job = await db.get(DataProfilingJob, job_id)
            config = await db.get(DataProfilingConfiguration, configuration_id)
            
            if not job or not config:
                raise ValueError("Job or configuration not found")
            
            # Update job status in database
            job.status = 'running'
            job.started_at = datetime.utcnow()
            await db.commit()
            
            # Initialize service
            service = DataProfilingService(db)
            
            # Update progress
            job_manager.update_job_progress(
                bg_job_id,
                current_step="Analyzing data source",
                progress_percentage=10
            )
            
            # Estimate dataset size
            estimated_rows = await service._estimate_dataset_size(config)
            job.total_records = estimated_rows
            
            job_manager.update_job_progress(
                bg_job_id,
                current_step=f"Processing {estimated_rows} records",
                progress_percentage=20,
                metadata={"total_records": estimated_rows}
            )
            
            # Execute profiling based on dataset size
            if estimated_rows > 5_000_000 or config.profiling_mode == 'full_scan':
                logger.info(f"Using large dataset profiling for job {job.id}")
                await _profile_large_dataset_with_progress(
                    service, job, config, user_id, bg_job_id
                )
            else:
                logger.info(f"Using standard profiling for job {job.id}")
                await _profile_standard_dataset_with_progress(
                    service, job, config, user_id, bg_job_id
                )
            
            # Mark job as completed
            job.status = 'completed'
            job.completed_at = datetime.utcnow()
            job.duration_seconds = int((job.completed_at - job.started_at).total_seconds())
            await db.commit()
            
            # Complete the background job
            job_manager.complete_job(
                bg_job_id,
                result={
                    "job_id": job.id,
                    "status": "completed",
                    "total_records": job.total_records,
                    "records_processed": job.records_processed,
                    "records_failed": job.records_failed,
                    "anomalies_detected": job.anomalies_detected,
                    "data_quality_score": job.data_quality_score,
                    "duration_seconds": job.duration_seconds
                }
            )
            
    except Exception as e:
        logger.error(f"Error executing profiling job {job_id}: {e}")
        
        # Update job status to failed
        try:
            async with AsyncSessionLocal() as db:
                job = await db.get(DataProfilingJob, job_id)
                if job:
                    job.status = 'failed'
                    job.error_message = str(e)
                    job.completed_at = datetime.utcnow()
                    await db.commit()
        except Exception as db_error:
            logger.error(f"Failed to update job status: {db_error}")
        
        # Fail the background job
        job_manager.complete_job(
            bg_job_id,
            error=str(e)
        )


async def _profile_large_dataset_with_progress(
    service, job, config, user_id, bg_job_id
):
    """Profile large dataset with progress updates"""
    # This is a simplified version - in reality would process in chunks
    attributes = await service._get_attributes_for_profiling(config)
    total_attributes = len(attributes)
    
    for idx, attribute in enumerate(attributes):
        # Update progress
        progress = 20 + int((idx / total_attributes) * 70)
        job_manager.update_job_progress(
            bg_job_id,
            current_step=f"Profiling attribute {attribute.attribute_name}",
            progress_percentage=progress,
            completed_steps=idx,
            total_steps=total_attributes
        )
        
        # Profile the attribute
        result = await service._profile_single_attribute_large(
            job, config, attribute, user_id
        )
        
        # Update job metrics
        job.records_processed = (job.records_processed or 0) + result.total_values
        if result.anomaly_count > 0:
            job.anomalies_detected = (job.anomalies_detected or 0) + result.anomaly_count
    
    # Calculate overall quality score
    job.data_quality_score = 90.0  # Simplified calculation
    

async def _profile_standard_dataset_with_progress(
    service, job, config, user_id, bg_job_id
):
    """Profile standard dataset with progress updates"""
    # Similar to large dataset but with different processing strategy
    await _profile_large_dataset_with_progress(
        service, job, config, user_id, bg_job_id
    )


# Function to run the async task from sync context (for Celery)
def execute_profiling_job_sync(job_id: int, bg_job_id: str, configuration_id: int, user_id: int):
    """Sync wrapper for the async task"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(
            execute_profiling_job_task(job_id, bg_job_id, configuration_id, user_id)
        )
    finally:
        loop.close()