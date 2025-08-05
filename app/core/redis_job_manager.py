"""
Redis-based Job Manager for cross-container job state management
"""
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
import redis
from redis.exceptions import RedisError
import os

logger = logging.getLogger(__name__)


class RedisJobManager:
    """
    Manages background job states in Redis for cross-container access
    """
    
    def __init__(self, redis_url: Optional[str] = None):
        """Initialize Redis connection"""
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        self._redis_client = None
        self.job_prefix = "job:"
        self.active_jobs_key = "active_jobs"
        self.job_ttl = 86400  # 24 hours
        
    @property
    def redis_client(self) -> redis.Redis:
        """Lazy initialize Redis client"""
        if self._redis_client is None:
            self._redis_client = redis.from_url(self.redis_url, decode_responses=True)
            # Test connection
            try:
                self._redis_client.ping()
                logger.info("✅ Connected to Redis for job management")
            except RedisError as e:
                logger.error(f"❌ Failed to connect to Redis: {e}")
                raise
        return self._redis_client
    
    def create_job(self, job_type: str, metadata: Dict[str, Any] = None) -> str:
        """Create a new job and return its ID"""
        job_id = str(uuid.uuid4())
        
        job_data = {
            "job_id": job_id,
            "job_type": job_type,
            "status": "pending",
            "progress_percentage": 0,
            "current_step": "Created",
            "total_steps": 0,
            "completed_steps": 0,
            "message": "Job created",
            "result": None,
            "error": None,
            "created_at": datetime.utcnow().isoformat(),
            "started_at": None,
            "completed_at": None,
            "metadata": metadata or {}
        }
        
        try:
            # Store job data
            self.redis_client.setex(
                f"{self.job_prefix}{job_id}",
                self.job_ttl,
                json.dumps(job_data)
            )
            
            # Add to active jobs set
            self.redis_client.sadd(self.active_jobs_key, job_id)
            
            logger.info(f"📝 Created job {job_id} of type {job_type}")
            return job_id
            
        except RedisError as e:
            logger.error(f"❌ Failed to create job: {e}")
            raise
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status by ID"""
        try:
            job_data = self.redis_client.get(f"{self.job_prefix}{job_id}")
            if job_data:
                return json.loads(job_data)
            return None
        except (RedisError, json.JSONDecodeError) as e:
            logger.error(f"❌ Failed to get job status for {job_id}: {e}")
            return None
    
    def update_job_progress(
        self,
        job_id: str,
        status: Optional[str] = None,
        progress_percentage: Optional[int] = None,
        current_step: Optional[str] = None,
        message: Optional[str] = None,
        total_steps: Optional[int] = None,
        completed_steps: Optional[int] = None,
        result: Optional[Any] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update job progress"""
        try:
            # Get current job data
            job_data = self.get_job_status(job_id)
            if not job_data:
                logger.warning(f"⚠️ Job {job_id} not found for update")
                return False
            
            # Update fields
            if status is not None:
                job_data["status"] = status
                if status == "running" and job_data["started_at"] is None:
                    job_data["started_at"] = datetime.utcnow().isoformat()
                elif status in ["completed", "failed", "cancelled"]:
                    job_data["completed_at"] = datetime.utcnow().isoformat()
                    # Remove from active jobs
                    self.redis_client.srem(self.active_jobs_key, job_id)
            
            if progress_percentage is not None:
                job_data["progress_percentage"] = progress_percentage
            
            if current_step is not None:
                job_data["current_step"] = current_step
            
            if message is not None:
                job_data["message"] = message
            
            if total_steps is not None:
                job_data["total_steps"] = total_steps
            
            if completed_steps is not None:
                job_data["completed_steps"] = completed_steps
            
            if result is not None:
                job_data["result"] = result
            
            if error is not None:
                job_data["error"] = error
            
            if metadata is not None:
                job_data["metadata"].update(metadata)
            
            # Save updated data
            self.redis_client.setex(
                f"{self.job_prefix}{job_id}",
                self.job_ttl,
                json.dumps(job_data)
            )
            
            logger.debug(f"📊 Updated job {job_id}: status={status}, progress={progress_percentage}%")
            return True
            
        except (RedisError, json.JSONDecodeError) as e:
            logger.error(f"❌ Failed to update job {job_id}: {e}")
            return False
    
    def complete_job(self, job_id: str, result: Any = None, error: Optional[str] = None) -> bool:
        """Mark job as completed"""
        status = "failed" if error else "completed"
        return self.update_job_progress(
            job_id,
            status=status,
            progress_percentage=100,
            result=result,
            error=error,
            current_step="Failed" if error else "Completed"
        )
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a job"""
        return self.update_job_progress(
            job_id,
            status="cancelled",
            current_step="Cancelled by user"
        )
    
    def get_active_jobs(self) -> List[Dict[str, Any]]:
        """Get all active jobs"""
        try:
            active_job_ids = self.redis_client.smembers(self.active_jobs_key)
            active_jobs = []
            
            for job_id in active_job_ids:
                job_data = self.get_job_status(job_id)
                if job_data:
                    # Verify job is actually active
                    if job_data["status"] in ["pending", "running", "pausing", "paused"]:
                        active_jobs.append(job_data)
                    else:
                        # Clean up inactive job from active set
                        self.redis_client.srem(self.active_jobs_key, job_id)
            
            return sorted(active_jobs, key=lambda x: x.get("created_at", ""), reverse=True)
            
        except RedisError as e:
            logger.error(f"❌ Failed to get active jobs: {e}")
            return []
    
    def get_user_jobs(self, user_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """Get jobs for a specific user"""
        # This would require maintaining a user-specific index in Redis
        # For now, filter from all active jobs
        all_jobs = self.get_active_jobs()
        user_jobs = [
            job for job in all_jobs
            if job.get("metadata", {}).get("user_id") == user_id
        ]
        return user_jobs[:limit]
    
    def cleanup_old_jobs(self, days: int = 7) -> int:
        """Clean up jobs older than specified days"""
        # Redis TTL handles this automatically
        # This method is for compatibility
        return 0
    
    def get_job_count_by_status(self) -> Dict[str, int]:
        """Get count of jobs by status"""
        try:
            active_jobs = self.get_active_jobs()
            status_counts = {}
            
            for job in active_jobs:
                status = job.get("status", "unknown")
                status_counts[status] = status_counts.get(status, 0) + 1
            
            return status_counts
            
        except Exception as e:
            logger.error(f"❌ Failed to get job counts: {e}")
            return {}


# Singleton instance
_redis_job_manager = None


def get_redis_job_manager() -> RedisJobManager:
    """Get or create Redis job manager instance"""
    global _redis_job_manager
    if _redis_job_manager is None:
        _redis_job_manager = RedisJobManager()
    return _redis_job_manager