import asyncio
import json
import uuid
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class JobProgress:
    def __init__(self, job_id: str, job_type: str = "unknown"):
        self.job_id = job_id
        self.job_type = job_type
        self.status = JobStatus.PENDING
        self.progress_percentage = 0
        self.current_step = ""
        self.total_steps = 0
        self.completed_steps = 0
        self.message = ""
        self.result = None
        self.error = None
        self.created_at = datetime.utcnow()
        self.started_at = None
        self.completed_at = None
        self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "job_type": self.job_type,
            "status": self.status.value,
            "progress_percentage": self.progress_percentage,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "completed_steps": self.completed_steps,
            "message": self.message,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metadata": self.metadata
        }

class BackgroundJobManager:
    def __init__(self):
        self.jobs: Dict[str, JobProgress] = {}
        self.cleanup_interval = 3600  # 1 hour
        self.max_job_age = 86400  # 24 hours
        # Use absolute path for jobs file
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.jobs_file = os.path.join(base_dir, "jobs_storage.json")
        logger.info(f"📂 Job storage file path: {self.jobs_file}")
        
        # Load existing jobs from file
        self._load_jobs_from_file()
        
    def _load_jobs_from_file(self):
        """Load jobs from persistent storage."""
        try:
            if os.path.exists(self.jobs_file):
                logger.info(f"📁 Loading jobs from file: {self.jobs_file}")
                with open(self.jobs_file, 'r') as f:
                    jobs_data = json.load(f)
                    
                logger.info(f"📊 Found {len(jobs_data)} jobs in file")
                    
                for job_id, job_data in jobs_data.items():
                    job_type = job_data.get('job_type', job_data.get('metadata', {}).get('task_type', 'unknown'))
                    job = JobProgress(job_id, job_type)
                    job.status = JobStatus(job_data.get('status', 'pending'))
                    job.progress_percentage = job_data.get('progress_percentage', 0)
                    job.current_step = job_data.get('current_step', '')
                    job.total_steps = job_data.get('total_steps', 0)
                    job.completed_steps = job_data.get('completed_steps', 0)
                    job.message = job_data.get('message', '')
                    job.result = job_data.get('result')
                    job.error = job_data.get('error')
                    job.metadata = job_data.get('metadata', {})
                    
                    # Parse datetime strings
                    if job_data.get('created_at'):
                        job.created_at = datetime.fromisoformat(job_data['created_at'].replace('Z', '+00:00'))
                    if job_data.get('started_at'):
                        job.started_at = datetime.fromisoformat(job_data['started_at'].replace('Z', '+00:00'))
                    if job_data.get('completed_at'):
                        job.completed_at = datetime.fromisoformat(job_data['completed_at'].replace('Z', '+00:00'))
                    
                    self.jobs[job_id] = job
                    
                logger.info(f"📦 Loaded {len(self.jobs)} jobs from persistent storage")
            else:
                logger.warning(f"⚠️ Jobs file not found: {self.jobs_file}")
        except Exception as e:
            logger.error(f"❌ Failed to load jobs from file: {e}")
            
    def _save_jobs_to_file(self):
        """Save jobs to persistent storage."""
        try:
            jobs_data = {}
            for job_id, job in self.jobs.items():
                jobs_data[job_id] = job.to_dict()
                
            with open(self.jobs_file, 'w') as f:
                json.dump(jobs_data, f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"❌ Failed to save jobs to file: {e}")
        
    def create_job(self, job_type: str, metadata: Dict[str, Any] = None) -> str:
        """Create a new background job and return its ID."""
        job_id = str(uuid.uuid4())
        progress = JobProgress(job_id, job_type)  # Pass job_type to constructor
        progress.metadata = metadata or {}
        progress.metadata["job_type"] = job_type
        
        self.jobs[job_id] = progress
        self._save_jobs_to_file()  # Persist immediately
        logger.info(f"📝 Created background job {job_id} of type {job_type}")
        return job_id
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get a job by ID, reloading from file if not found in memory."""
        # First check memory
        job = self.jobs.get(job_id)
        if job:
            return job.to_dict()
        
        # If not found, reload from file and check again
        self._load_jobs_from_file()
        job = self.jobs.get(job_id)
        if job:
            logger.info(f"✅ Found job {job_id} after reloading from file")
            return job.to_dict()
        
        logger.warning(f"❌ Job {job_id} not found even after reloading")
        return None
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get the current status of a job."""
        logger.info(f"🔍 Looking for job {job_id}")
        logger.info(f"📊 Total jobs in manager: {len(self.jobs)}")
        logger.info(f"🔑 Available job IDs: {list(self.jobs.keys())[:5]}...")
        
        job = self.jobs.get(job_id)
        if job:
            logger.info(f"✅ Found job {job_id} with status {job.status.value}")
        else:
            logger.warning(f"❌ Job {job_id} not found in manager")
            logger.warning(f"📋 All job IDs in manager: {list(self.jobs.keys())}")
            
        return job.to_dict() if job else None
    
    def update_job_progress(self, job_id: str, **kwargs):
        """Update job progress with various parameters."""
        job = self.jobs.get(job_id)
        if not job:
            # Try reloading from file
            self._load_jobs_from_file()
            job = self.jobs.get(job_id)
            if not job:
                logger.warning(f"Attempted to update non-existent job {job_id}")
                return
        
        if "status" in kwargs:
            job.status = JobStatus(kwargs["status"])
            if job.status == JobStatus.RUNNING and not job.started_at:
                job.started_at = datetime.utcnow()
            elif job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                job.completed_at = datetime.utcnow()
                # For failed jobs, don't set progress to 100%
                if job.status == JobStatus.FAILED and "progress_percentage" not in kwargs:
                    job.progress_percentage = 0
        
        if "progress_percentage" in kwargs:
            job.progress_percentage = min(100, max(0, kwargs["progress_percentage"]))
        
        if "current_step" in kwargs:
            job.current_step = kwargs["current_step"]
        
        if "total_steps" in kwargs:
            job.total_steps = kwargs["total_steps"]
        
        if "completed_steps" in kwargs:
            job.completed_steps = kwargs["completed_steps"]
            if job.total_steps > 0:
                job.progress_percentage = int((job.completed_steps / job.total_steps) * 100)
        
        if "message" in kwargs:
            job.message = kwargs["message"]
        
        if "result" in kwargs:
            job.result = kwargs["result"]
        
        if "error" in kwargs:
            job.error = kwargs["error"]
        
        if "metadata" in kwargs:
            job.metadata.update(kwargs["metadata"])
        
        # Save to file after updates
        self._save_jobs_to_file()
        logger.debug(f"Updated job {job_id}: {job.status.value} - {job.progress_percentage}% - {job.current_step}")
    
    def complete_job(self, job_id: str, result: Any = None, error: str = None):
        """Mark a job as completed or failed."""
        job = self.jobs.get(job_id)
        if not job:
            # Try reloading from file
            self._load_jobs_from_file()
            job = self.jobs.get(job_id)
            if not job:
                logger.warning(f"🚫 Attempted to complete non-existent job {job_id}")
                return
        
        if error:
            job.status = JobStatus.FAILED
            job.error = error
            job.progress_percentage = 0  # Reset progress to 0 for failed jobs
            logger.error(f"❌ JOB FAILED - {job_id}: {error}")
        else:
            job.status = JobStatus.COMPLETED
            job.result = result
            job.progress_percentage = 100
            logger.info(f"✅ JOB COMPLETED - {job_id}")
            if result and isinstance(result, dict):
                logger.info(f"✅ JOB RESULT SUMMARY - {job_id}:")
                for key, value in result.items():
                    logger.info(f"   📊 {key}: {value}")
        
        job.completed_at = datetime.utcnow()
        self._save_jobs_to_file()  # Persist completion
        logger.info(f"🕐 Job {job_id} completion time: {job.completed_at}")
    
    def cancel_job(self, job_id: str):
        """Cancel a running job."""
        job = self.jobs.get(job_id)
        if job and job.status in [JobStatus.PENDING, JobStatus.RUNNING]:
            job.status = JobStatus.CANCELLED
            job.completed_at = datetime.utcnow()
            logger.info(f"Job {job_id} cancelled")
    
    def cleanup_old_jobs(self):
        """Remove old completed jobs to prevent memory leaks."""
        cutoff_time = datetime.utcnow() - timedelta(seconds=self.max_job_age)
        jobs_to_remove = []
        
        for job_id, job in self.jobs.items():
            if (job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED] and 
                job.completed_at and job.completed_at < cutoff_time):
                jobs_to_remove.append(job_id)
        
        for job_id in jobs_to_remove:
            del self.jobs[job_id]
            logger.debug(f"Cleaned up old job {job_id}")
    
    def get_active_jobs(self) -> List[Dict[str, Any]]:
        """Get all active (non-completed) jobs."""
        return [
            job.to_dict() for job in self.jobs.values()
            if job.status in [JobStatus.PENDING, JobStatus.RUNNING]
        ]
    
    async def run_job(self, job_id: str, job_func: Callable, *args, **kwargs):
        """Run a job function asynchronously with progress tracking."""
        try:
            self.update_job_progress(job_id, status="running", message="Starting job execution")
            
            # Execute the job function
            if asyncio.iscoroutinefunction(job_func):
                result = await job_func(job_id, *args, **kwargs)
            else:
                result = job_func(job_id, *args, **kwargs)
            
            self.complete_job(job_id, result=result)
            return result
            
        except Exception as e:
            error_msg = f"Job execution failed: {str(e)}"
            self.complete_job(job_id, error=error_msg)
            logger.error(f"Job {job_id} failed with error: {e}", exc_info=True)
            raise

# Global job manager instance
job_manager = BackgroundJobManager()

# Cleanup task
async def periodic_cleanup():
    """Periodically clean up old jobs."""
    while True:
        try:
            job_manager.cleanup_old_jobs()
            await asyncio.sleep(job_manager.cleanup_interval)
        except Exception as e:
            logger.error(f"Error during job cleanup: {e}")
            await asyncio.sleep(60)  # Wait a minute before retrying 