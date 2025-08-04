# Phase 1: Revised Implementation Plan - Direct Migration to Celery

## Executive Summary

This revised implementation plan outlines a direct migration approach to Celery with Redis, eliminating the complexity of parallel systems and dual-mode operation. The plan focuses on achieving a clean target state with full Celery integration, removing all legacy job processing code in favor of a modern, scalable architecture.

## Key Changes from Original Plan

1. **No Parallel Running** - Complete replacement of existing system
2. **Clean Architecture** - No adapter layers or compatibility shims
3. **Faster Timeline** - 5-6 weeks instead of 8-10 weeks
4. **Simplified Testing** - No dual-system comparison needed
5. **Direct Cutover** - Single migration event per service

## Implementation Timeline

### Overall Timeline: 5-6 weeks
- **Phase 2 (Core Infrastructure)**: 1 week
- **Phase 3 (Complete Job Migration)**: 2 weeks  
- **Phase 4 (Advanced Features)**: 1 week
- **Phase 5 (Deployment)**: 1 week
- **Phase 6 (Cutover & Validation)**: 1 week

## Phase 2: Core Infrastructure Implementation (Week 1)

### Day 1-2: Complete Celery/Redis Setup

#### Redis Infrastructure
```yaml
# docker-compose.yml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    command: >
      redis-server
      --requirepass ${REDIS_PASSWORD}
      --appendonly yes
      --appendfsync everysec
      --maxmemory 2gb
      --maxmemory-policy allkeys-lru
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
```

#### Complete Celery Configuration
```python
# app/core/celery_app.py
from celery import Celery
from kombu import Exchange, Queue
import os

# Initialize Celery
celery_app = Celery('synapse_dte')

# Load configuration
celery_app.config_from_object('app.core.celery_config:CeleryConfig')

# Auto-discover tasks
celery_app.autodiscover_tasks(['app.tasks'])

# app/core/celery_config.py
class CeleryConfig:
    # Broker settings
    broker_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    result_backend = os.getenv('REDIS_URL', 'redis://localhost:6379/1')
    
    # Task execution settings
    task_track_started = True
    task_time_limit = 3600
    task_soft_time_limit = 3000
    task_acks_late = True
    worker_prefetch_multiplier = 1
    worker_max_tasks_per_child = 50
    
    # Result settings
    result_expires = 86400
    result_persistent = True
    result_compression = 'gzip'
    
    # Serialization
    task_serializer = 'json'
    result_serializer = 'json'
    accept_content = ['json']
    timezone = 'UTC'
    enable_utc = True
    
    # Task routing
    task_routes = {
        'app.tasks.data_profiling.*': {'queue': 'data_profiling', 'priority': 5},
        'app.tasks.llm.*': {'queue': 'llm', 'priority': 3},
        'app.tasks.planning.*': {'queue': 'planning', 'priority': 5},
        'app.tasks.scoping.*': {'queue': 'scoping', 'priority': 5},
        'app.tasks.test_execution.*': {'queue': 'test_execution', 'priority': 7},
        'app.tasks.sample_selection.*': {'queue': 'sample_selection', 'priority': 5},
    }
    
    # Queue configuration
    task_queues = (
        Queue('default', Exchange('default'), routing_key='default'),
        Queue('data_profiling', Exchange('tasks'), routing_key='data_profiling',
              queue_arguments={'x-max-priority': 10}),
        Queue('llm', Exchange('tasks'), routing_key='llm',
              queue_arguments={'x-max-priority': 10}),
        Queue('planning', Exchange('tasks'), routing_key='planning'),
        Queue('scoping', Exchange('tasks'), routing_key='scoping'),
        Queue('test_execution', Exchange('tasks'), routing_key='test_execution'),
        Queue('sample_selection', Exchange('tasks'), routing_key='sample_selection'),
    )
    
    # Beat schedule
    beat_schedule = {
        'cleanup-completed-jobs': {
            'task': 'app.tasks.maintenance.cleanup_completed_jobs',
            'schedule': 3600.0,  # Every hour
        },
        'health-check': {
            'task': 'app.tasks.maintenance.health_check',
            'schedule': 60.0,  # Every minute
        },
    }
```

### Day 3: New Job Manager Implementation

```python
# app/core/job_manager.py
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import redis
from celery import states
from celery.result import AsyncResult
from app.core.celery_app import celery_app

class JobManager:
    """Clean Celery-based job manager"""
    
    def __init__(self):
        self.redis_client = redis.from_url(
            celery_app.conf.result_backend,
            decode_responses=True
        )
        self.job_prefix = "job:meta:"
        
    def create_job(self, task_name: str, **kwargs) -> str:
        """Create and dispatch a Celery job"""
        # Extract metadata
        metadata = kwargs.pop('metadata', {})
        priority = metadata.get('priority', 5)
        
        # Apply task
        task = celery_app.tasks.get(task_name)
        if not task:
            raise ValueError(f"Unknown task: {task_name}")
            
        result = task.apply_async(
            kwargs=kwargs,
            priority=priority,
            headers={'metadata': metadata}
        )
        
        # Store job metadata
        self._store_metadata(result.id, {
            'task_name': task_name,
            'created_at': datetime.utcnow().isoformat(),
            'metadata': metadata,
            'status': 'pending'
        })
        
        return result.id
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get comprehensive job status"""
        result = AsyncResult(job_id, app=celery_app)
        metadata = self._get_metadata(job_id)
        
        # Build unified status
        status = {
            'job_id': job_id,
            'task_name': metadata.get('task_name'),
            'status': self._map_celery_state(result.state),
            'created_at': metadata.get('created_at'),
            'started_at': metadata.get('started_at'),
            'completed_at': metadata.get('completed_at'),
            'progress': None,
            'result': None,
            'error': None,
            'metadata': metadata.get('metadata', {})
        }
        
        # Add state-specific information
        if result.state == 'PROGRESS':
            status['progress'] = result.info
        elif result.state == states.SUCCESS:
            status['result'] = result.result
            status['completed_at'] = datetime.utcnow().isoformat()
        elif result.state == states.FAILURE:
            status['error'] = {
                'message': str(result.info),
                'traceback': result.traceback
            }
            status['completed_at'] = datetime.utcnow().isoformat()
            
        return status
    
    def pause_job(self, job_id: str) -> bool:
        """Pause a running job"""
        result = AsyncResult(job_id, app=celery_app)
        if result.state in ['PENDING', 'STARTED', 'PROGRESS']:
            # Signal pause to task
            self.redis_client.set(f"job:pause:{job_id}", "1", ex=86400)
            return True
        return False
    
    def resume_job(self, job_id: str) -> str:
        """Resume a paused job from checkpoint"""
        # Get checkpoint data
        checkpoint = self._get_checkpoint(job_id)
        if not checkpoint:
            raise ValueError(f"No checkpoint found for job {job_id}")
            
        # Get original task metadata
        metadata = self._get_metadata(job_id)
        task_name = metadata.get('task_name')
        
        # Create new job with checkpoint
        new_job_id = self.create_job(
            task_name,
            resume_from=checkpoint,
            original_job_id=job_id,
            metadata={
                **metadata.get('metadata', {}),
                'resumed_from': job_id,
                'resumed_at': datetime.utcnow().isoformat()
            }
        )
        
        return new_job_id
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a job and cleanup"""
        result = AsyncResult(job_id, app=celery_app)
        result.revoke(terminate=True)
        
        # Cleanup
        self._delete_checkpoint(job_id)
        self._update_metadata(job_id, {'status': 'cancelled'})
        
        return True
    
    def list_jobs(self, status: Optional[str] = None, 
                  limit: int = 100) -> List[Dict[str, Any]]:
        """List jobs with optional filtering"""
        pattern = f"{self.job_prefix}*"
        jobs = []
        
        for key in self.redis_client.scan_iter(match=pattern, count=1000):
            job_id = key.replace(self.job_prefix, "")
            job_status = self.get_job_status(job_id)
            
            if status is None or job_status['status'] == status:
                jobs.append(job_status)
                
            if len(jobs) >= limit:
                break
                
        return sorted(jobs, key=lambda x: x['created_at'], reverse=True)
    
    # Helper methods
    def _store_metadata(self, job_id: str, metadata: Dict[str, Any]):
        key = f"{self.job_prefix}{job_id}"
        self.redis_client.setex(
            key, 
            86400 * 7,  # 7 days
            json.dumps(metadata)
        )
    
    def _get_metadata(self, job_id: str) -> Dict[str, Any]:
        key = f"{self.job_prefix}{job_id}"
        data = self.redis_client.get(key)
        return json.loads(data) if data else {}
    
    def _update_metadata(self, job_id: str, updates: Dict[str, Any]):
        metadata = self._get_metadata(job_id)
        metadata.update(updates)
        self._store_metadata(job_id, metadata)
    
    def _get_checkpoint(self, job_id: str) -> Optional[Dict[str, Any]]:
        key = f"checkpoint:{job_id}"
        data = self.redis_client.get(key)
        return json.loads(data) if data else None
    
    def _delete_checkpoint(self, job_id: str):
        key = f"checkpoint:{job_id}"
        self.redis_client.delete(key)
    
    def _map_celery_state(self, state: str) -> str:
        """Map Celery states to our status names"""
        mapping = {
            'PENDING': 'pending',
            'STARTED': 'running',
            'PROGRESS': 'running',
            'SUCCESS': 'completed',
            'FAILURE': 'failed',
            'RETRY': 'running',
            'REVOKED': 'cancelled'
        }
        return mapping.get(state, state.lower())

# Global instance
job_manager = JobManager()
```

### Day 4: Base Task Classes

```python
# app/tasks/base.py
from celery import Task, current_task
from typing import Dict, Any, Optional
import time
import json
from app.core.celery_app import celery_app
from app.core.logging import get_logger

logger = get_logger(__name__)

class BaseTask(Task):
    """Base class for all tasks with standard features"""
    
    def __init__(self):
        super().__init__()
        self.start_time = None
        
    def before_start(self, task_id, args, kwargs):
        """Called before task execution"""
        self.start_time = time.time()
        logger.info(f"Starting task {self.name} with ID {task_id}")
        
        # Update job metadata
        from app.core.job_manager import job_manager
        job_manager._update_metadata(task_id, {
            'started_at': datetime.utcnow().isoformat(),
            'status': 'running'
        })
        
    def on_success(self, retval, task_id, args, kwargs):
        """Called on successful completion"""
        duration = time.time() - self.start_time
        logger.info(f"Task {task_id} completed in {duration:.2f}s")
        
        # Cleanup checkpoint
        self.clear_checkpoint(task_id)
        
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called on task failure"""
        logger.error(f"Task {task_id} failed: {exc}", exc_info=True)
        
        # Save failure checkpoint for debugging
        self.save_checkpoint(task_id, {
            'failed_at': time.time(),
            'error': str(exc),
            'args': args,
            'kwargs': kwargs
        })
        
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Called when task is retried"""
        logger.warning(f"Task {task_id} retrying due to: {exc}")
        
    def update_progress(self, current: int, total: int, 
                       message: str = "", **extra):
        """Update task progress"""
        progress_data = {
            'current': current,
            'total': total,
            'percentage': int((current / total * 100)) if total > 0 else 0,
            'message': message,
            **extra
        }
        
        current_task.update_state(
            state='PROGRESS',
            meta=progress_data
        )
        
    def save_checkpoint(self, task_id: str, data: Dict[str, Any]):
        """Save task checkpoint"""
        redis_client = celery_app.backend.client
        key = f"checkpoint:{task_id}"
        redis_client.setex(
            key,
            86400,  # 24 hours
            json.dumps({
                'task_name': self.name,
                'timestamp': time.time(),
                'data': data
            })
        )
        
    def load_checkpoint(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Load task checkpoint"""
        redis_client = celery_app.backend.client
        key = f"checkpoint:{task_id}"
        data = redis_client.get(key)
        if data:
            checkpoint = json.loads(data)
            return checkpoint.get('data')
        return None
        
    def clear_checkpoint(self, task_id: str):
        """Clear task checkpoint"""
        redis_client = celery_app.backend.client
        key = f"checkpoint:{task_id}"
        redis_client.delete(key)
        
    def check_pause_signal(self, task_id: str) -> bool:
        """Check if task should pause"""
        redis_client = celery_app.backend.client
        return redis_client.get(f"job:pause:{task_id}") == b"1"


class CheckpointableTask(BaseTask):
    """Task with automatic checkpointing"""
    
    def __init__(self):
        super().__init__()
        self.checkpoint_interval = 10  # Checkpoint every 10 items
        
    def process_with_checkpoints(self, items: List[Any], 
                                resume_from: Optional[Dict] = None):
        """Process items with automatic checkpointing"""
        # Load checkpoint or start fresh
        if resume_from:
            start_index = resume_from.get('last_index', 0) + 1
            processed_ids = set(resume_from.get('processed_ids', []))
            logger.info(f"Resuming from checkpoint at index {start_index}")
        else:
            start_index = 0
            processed_ids = set()
            
        task_id = current_task.request.id
        total_items = len(items)
        
        for idx in range(start_index, total_items):
            # Check for pause signal
            if self.check_pause_signal(task_id):
                logger.info(f"Task {task_id} paused at index {idx}")
                self.save_checkpoint(task_id, {
                    'last_index': idx - 1,
                    'processed_ids': list(processed_ids),
                    'total_items': total_items
                })
                raise self.retry(countdown=60, max_retries=None)
                
            item = items[idx]
            
            try:
                # Process item
                result = self.process_item(item)
                processed_ids.add(item.get('id', idx))
                
                # Update progress
                self.update_progress(
                    idx + 1, 
                    total_items,
                    f"Processing item {idx + 1} of {total_items}"
                )
                
                # Save checkpoint periodically
                if (idx + 1) % self.checkpoint_interval == 0:
                    self.save_checkpoint(task_id, {
                        'last_index': idx,
                        'processed_ids': list(processed_ids),
                        'total_items': total_items
                    })
                    
            except Exception as e:
                # Save checkpoint before failing
                self.save_checkpoint(task_id, {
                    'last_index': idx - 1,
                    'processed_ids': list(processed_ids),
                    'total_items': total_items,
                    'failed_item': item,
                    'error': str(e)
                })
                raise
                
        return {
            'processed': len(processed_ids),
            'total': total_items
        }
        
    def process_item(self, item: Any) -> Any:
        """Override this method in subclasses"""
        raise NotImplementedError


class DatabaseTask(BaseTask):
    """Task with database session management"""
    
    async def run_with_db(self, *args, **kwargs):
        """Run task with database session"""
        from app.core.database import AsyncSessionLocal
        
        async with AsyncSessionLocal() as db:
            try:
                # Pass session to task
                kwargs['db'] = db
                result = await self.execute(*args, **kwargs)
                await db.commit()
                return result
            except Exception as e:
                await db.rollback()
                logger.error(f"Database task failed: {e}")
                raise
                
    async def execute(self, *args, db=None, **kwargs):
        """Override this method in subclasses"""
        raise NotImplementedError
```

### Day 5: API Endpoints

```python
# app/api/v1/endpoints/jobs.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from app.core.job_manager import job_manager
from app.core.dependencies import get_current_user
from app.schemas.jobs import (
    JobCreate, JobStatus, JobList, 
    JobControl, JobUpdate
)

router = APIRouter(prefix="/jobs", tags=["jobs"])

@router.post("", response_model=JobStatus)
async def create_job(
    job: JobCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new background job"""
    try:
        job_id = job_manager.create_job(
            task_name=job.task_name,
            **job.parameters,
            metadata={
                'user_id': current_user.user_id,
                'description': job.description,
                **job.metadata
            }
        )
        return job_manager.get_job_status(job_id)
    except ValueError as e:
        raise HTTPException(400, str(e))

@router.get("/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Get job status and details"""
    status = job_manager.get_job_status(job_id)
    if not status:
        raise HTTPException(404, f"Job {job_id} not found")
    return status

@router.get("", response_model=JobList)
async def list_jobs(
    status: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user)
):
    """List jobs with optional filtering"""
    jobs = job_manager.list_jobs(status=status, limit=limit)
    # Filter by user if not admin
    if not current_user.is_admin:
        jobs = [j for j in jobs if j['metadata'].get('user_id') == current_user.user_id]
    return JobList(jobs=jobs, total=len(jobs))

@router.post("/{job_id}/pause", response_model=JobStatus)
async def pause_job(job_id: str):
    """Pause a running job"""
    if not job_manager.pause_job(job_id):
        raise HTTPException(400, "Job cannot be paused")
    return job_manager.get_job_status(job_id)

@router.post("/{job_id}/resume", response_model=JobStatus)
async def resume_job(job_id: str):
    """Resume a paused job"""
    try:
        new_job_id = job_manager.resume_job(job_id)
        return job_manager.get_job_status(new_job_id)
    except ValueError as e:
        raise HTTPException(400, str(e))

@router.delete("/{job_id}")
async def cancel_job(job_id: str):
    """Cancel a job"""
    if not job_manager.cancel_job(job_id):
        raise HTTPException(400, "Job cannot be cancelled")
    return {"message": f"Job {job_id} cancelled"}

@router.get("/{job_id}/logs")
async def get_job_logs(
    job_id: str,
    tail: int = Query(100, ge=1, le=1000)
):
    """Get job execution logs"""
    # Implementation depends on logging setup
    pass
```

## Phase 3: Complete Job Migration (Weeks 2-3)

### Week 2: Core Job Migrations

#### Day 1-2: Remove Old Job System
```bash
# Remove old files
rm app/core/background_jobs.py
rm app/core/background_task_runner.py

# Update imports in all files
find app -name "*.py" -exec sed -i 's/from app.core.background_jobs/from app.core.job_manager/g' {} +
```

#### Day 3-5: Migrate All Job Types

##### Data Profiling Tasks
```python
# app/tasks/data_profiling.py
from app.tasks.base import CheckpointableTask, DatabaseTask
from app.core.celery_app import celery_app
from typing import List, Dict, Any

@celery_app.task(base=CheckpointableTask, bind=True, name='app.tasks.data_profiling.generate_rules')
class GenerateProfilingRulesTask(CheckpointableTask):
    """Generate data profiling rules using LLM"""
    
    def run(self, version_id: str, attributes: List[Dict], 
            resume_from: Optional[Dict] = None, **kwargs):
        """Generate profiling rules for attributes"""
        
        # Process with checkpoints
        return self.process_with_checkpoints(attributes, resume_from)
        
    def process_item(self, attribute: Dict) -> Dict:
        """Process single attribute"""
        from app.services.llm_service import get_llm_service
        
        llm = get_llm_service()
        rules = llm.generate_profiling_rules(attribute)
        
        # Save rules to database
        self.save_rules(attribute['id'], rules)
        
        return {
            'attribute_id': attribute['id'],
            'rules_count': len(rules)
        }
        
    def save_rules(self, attribute_id: str, rules: List[Dict]):
        """Save rules to database"""
        # Database operations
        pass

@celery_app.task(base=DatabaseTask, bind=True, name='app.tasks.data_profiling.execute_rules')
class ExecuteProfilingRulesTask(DatabaseTask):
    """Execute data profiling rules"""
    
    async def execute(self, version_id: str, db=None, **kwargs):
        """Execute profiling rules against data"""
        from app.services.data_profiling_service import DataProfilingService
        
        service = DataProfilingService(db)
        results = await service.execute_version_rules(version_id)
        
        return {
            'version_id': version_id,
            'total_rules': results['total'],
            'passed': results['passed'],
            'failed': results['failed']
        }
```

##### Planning Tasks
```python
# app/tasks/planning.py
@celery_app.task(base=CheckpointableTask, bind=True, name='app.tasks.planning.auto_map_pdes')
class AutoMapPDEsTask(CheckpointableTask):
    """Auto-map PDEs using LLM"""
    
    def run(self, phase_id: int, mappings: List[Dict], 
            resume_from: Optional[Dict] = None, **kwargs):
        """Process PDE mappings"""
        return self.process_with_checkpoints(mappings, resume_from)
        
    def process_item(self, mapping: Dict) -> Dict:
        """Process single mapping"""
        # LLM processing for PDE mapping
        pass
```

##### Sample Selection Tasks
```python
# app/tasks/sample_selection.py
@celery_app.task(base=DatabaseTask, bind=True, name='app.tasks.sample_selection.intelligent_sample')
class IntelligentSampleTask(DatabaseTask):
    """Perform intelligent sampling"""
    
    async def execute(self, cycle_id: int, report_id: int, 
                     sample_config: Dict, db=None, **kwargs):
        """Execute intelligent sampling"""
        from app.services.intelligent_data_sampling_service import IntelligentSamplingService
        
        service = IntelligentSamplingService(db)
        results = await service.generate_samples(
            cycle_id, report_id, sample_config
        )
        
        return results
```

### Week 3: Service Layer Updates

#### Update All Services
```python
# app/services/data_profiling_service.py
from app.core.job_manager import job_manager

class DataProfilingService:
    """Updated service using Celery"""
    
    async def generate_profiling_rules_async(self, version_id: str, 
                                           attributes: List[Dict]) -> str:
        """Generate profiling rules asynchronously"""
        job_id = job_manager.create_job(
            'app.tasks.data_profiling.generate_rules',
            version_id=version_id,
            attributes=attributes,
            metadata={
                'version_id': version_id,
                'total_attributes': len(attributes)
            }
        )
        return job_id
    
    async def execute_profiling_rules_async(self, version_id: str) -> str:
        """Execute profiling rules asynchronously"""
        job_id = job_manager.create_job(
            'app.tasks.data_profiling.execute_rules',
            version_id=version_id,
            metadata={
                'version_id': version_id
            }
        )
        return job_id
```

#### Update All Endpoints
```python
# app/api/v1/endpoints/data_profiling.py
@router.post("/versions/{version_id}/generate-rules")
async def generate_profiling_rules(
    version_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate profiling rules using LLM"""
    service = DataProfilingService(db)
    
    # Get attributes
    attributes = await service.get_version_attributes(version_id)
    
    # Start async job
    job_id = await service.generate_profiling_rules_async(
        version_id, attributes
    )
    
    return {
        "job_id": job_id,
        "message": f"Started rule generation for {len(attributes)} attributes"
    }
```

## Phase 4: Advanced Features (Week 4)

### Implement Advanced Patterns

#### Job Chains and Workflows
```python
# app/tasks/workflows.py
from celery import chain, group, chord

def create_complete_profiling_workflow(version_id: str):
    """Create complete data profiling workflow"""
    workflow = chain(
        # Generate rules
        generate_rules_task.s(version_id),
        # Execute rules
        execute_rules_task.s(),
        # Generate report
        generate_report_task.s()
    )
    return workflow.apply_async()

def create_parallel_processing_workflow(items: List[Dict]):
    """Process items in parallel"""
    workflow = chord(
        group(process_item_task.s(item) for item in items),
        aggregate_results_task.s()
    )
    return workflow.apply_async()
```

#### Scheduled Tasks
```python
# app/tasks/maintenance.py
@celery_app.task(name='app.tasks.maintenance.cleanup_completed_jobs')
def cleanup_completed_jobs():
    """Clean up old completed jobs"""
    from app.core.job_manager import job_manager
    
    # Clean up jobs older than 7 days
    cutoff = datetime.utcnow() - timedelta(days=7)
    cleaned = 0
    
    for job in job_manager.list_jobs(status='completed', limit=1000):
        if datetime.fromisoformat(job['completed_at']) < cutoff:
            job_manager._delete_metadata(job['job_id'])
            cleaned += 1
            
    return {'cleaned': cleaned}

@celery_app.task(name='app.tasks.maintenance.health_check')
def health_check():
    """Periodic health check"""
    return {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'workers': celery_app.control.inspect().active()
    }
```

#### Priority and Resource Management
```python
# app/tasks/resource_management.py
@celery_app.task(
    base=CheckpointableTask,
    bind=True,
    name='app.tasks.heavy_processing',
    queue='heavy',
    max_retries=3,
    default_retry_delay=300,
    rate_limit='10/m',  # 10 tasks per minute
    time_limit=3600,    # 1 hour hard limit
    soft_time_limit=3000  # 50 min soft limit
)
class HeavyProcessingTask(CheckpointableTask):
    """Resource-intensive task with limits"""
    
    def run(self, data: Dict, **kwargs):
        """Process heavy data"""
        try:
            # Heavy processing
            pass
        except SoftTimeLimitExceeded:
            # Save checkpoint before timeout
            self.save_checkpoint(current_task.request.id, {
                'partial_results': self.partial_results
            })
            raise
```

## Phase 5: Deployment (Week 5)

### Complete Docker Setup

#### Dockerfile for Workers
```dockerfile
# Dockerfile.worker
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Create non-root user
RUN useradd -m -u 1000 celery && chown -R celery:celery /app
USER celery

# Default to general worker
CMD ["celery", "-A", "app.core.celery_app", "worker", "--loglevel=info"]
```

#### Complete Docker Compose
```yaml
# docker-compose.yml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis
  redis:
    image: redis:7-alpine
    command: >
      redis-server
      --requirepass ${REDIS_PASSWORD}
      --appendonly yes
      --appendfsync everysec
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # FastAPI Backend
  backend:
    build: .
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@postgres/${DB_NAME}
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

  # Celery Workers
  worker-default:
    build:
      context: .
      dockerfile: Dockerfile.worker
    command: celery -A app.core.celery_app worker -Q default,planning,scoping -n default@%h
    environment:
      - DATABASE_URL=postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@postgres/${DB_NAME}
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379
    depends_on:
      - redis
      - postgres
    deploy:
      replicas: 2

  worker-llm:
    build:
      context: .
      dockerfile: Dockerfile.worker
    command: celery -A app.core.celery_app worker -Q llm -n llm@%h -c 2
    environment:
      - DATABASE_URL=postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@postgres/${DB_NAME}
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - redis
      - postgres

  worker-profiling:
    build:
      context: .
      dockerfile: Dockerfile.worker
    command: celery -A app.core.celery_app worker -Q data_profiling -n profiling@%h -c 1
    environment:
      - DATABASE_URL=postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@postgres/${DB_NAME}
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379
    depends_on:
      - redis
      - postgres
    deploy:
      replicas: 2

  # Celery Beat
  beat:
    build:
      context: .
      dockerfile: Dockerfile.worker
    command: celery -A app.core.celery_app beat --loglevel=info
    environment:
      - DATABASE_URL=postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@postgres/${DB_NAME}
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379
    depends_on:
      - redis

  # Flower
  flower:
    build:
      context: .
      dockerfile: Dockerfile.worker
    command: celery -A app.core.celery_app flower --port=5555
    ports:
      - "5555:5555"
    environment:
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379
      - FLOWER_BASIC_AUTH=${FLOWER_USER}:${FLOWER_PASSWORD}
    depends_on:
      - redis

  # Frontend
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://backend:8000
    depends_on:
      - backend

volumes:
  postgres_data:
  redis_data:
```

### Kubernetes Deployment
```yaml
# k8s/celery-deployment.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: celery-config
data:
  celery_config.py: |
    broker_url = 'redis://redis-service:6379/0'
    result_backend = 'redis://redis-service:6379/1'
    # ... rest of config

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: celery-worker-default
spec:
  replicas: 3
  selector:
    matchLabels:
      app: celery-worker
      queue: default
  template:
    metadata:
      labels:
        app: celery-worker
        queue: default
    spec:
      containers:
      - name: worker
        image: synapse-dte:latest
        command: ["celery", "-A", "app.core.celery_app", "worker", "-Q", "default,planning,scoping"]
        env:
        - name: C_FORCE_ROOT
          value: "true"
        envFrom:
        - secretRef:
            name: app-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          exec:
            command: ["celery", "-A", "app.core.celery_app", "inspect", "ping"]
          periodSeconds: 60
          timeoutSeconds: 10
        volumeMounts:
        - name: config
          mountPath: /app/config
      volumes:
      - name: config
        configMap:
          name: celery-config

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: celery-worker-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: celery-worker-default
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: External
    external:
      metric:
        name: redis_queue_length
        selector:
          matchLabels:
            queue: default
      target:
        type: Value
        value: "100"
```

## Phase 6: Cutover & Validation (Week 6)

### Cutover Plan

#### Pre-Cutover Checklist
- [ ] All Celery infrastructure deployed and tested
- [ ] All task types migrated and unit tested
- [ ] Integration tests passing
- [ ] Load tests completed
- [ ] Monitoring dashboards configured
- [ ] Team trained on new system
- [ ] Rollback procedure documented

#### Cutover Steps
1. **Stop all job creation** (maintenance window)
2. **Wait for existing jobs to complete** (monitor old system)
3. **Deploy new code** (with Celery integration)
4. **Run smoke tests** (verify basic functionality)
5. **Enable job creation** (using new system)
6. **Monitor closely** (first 24-48 hours)

### Validation Tests

#### Functional Tests
```python
# tests/test_celery_integration.py
import pytest
from app.core.job_manager import job_manager

@pytest.mark.asyncio
async def test_complete_job_lifecycle():
    """Test job creation, monitoring, and completion"""
    # Create job
    job_id = job_manager.create_job(
        'app.tasks.test.simple_task',
        data={'test': 'data'}
    )
    
    # Check status
    status = job_manager.get_job_status(job_id)
    assert status['status'] in ['pending', 'running']
    
    # Wait for completion
    await wait_for_job(job_id, timeout=30)
    
    # Verify result
    final_status = job_manager.get_job_status(job_id)
    assert final_status['status'] == 'completed'
    assert final_status['result'] is not None

@pytest.mark.asyncio
async def test_job_pause_resume():
    """Test pause and resume functionality"""
    # Create long-running job
    job_id = job_manager.create_job(
        'app.tasks.test.long_task',
        items=list(range(100))
    )
    
    # Wait for it to start
    await asyncio.sleep(2)
    
    # Pause job
    assert job_manager.pause_job(job_id)
    
    # Resume job
    new_job_id = job_manager.resume_job(job_id)
    assert new_job_id != job_id
    
    # Verify it completes
    await wait_for_job(new_job_id, timeout=60)
```

#### Performance Tests
```python
# tests/test_performance.py
async def test_concurrent_job_execution():
    """Test system under load"""
    # Create 100 concurrent jobs
    job_ids = []
    for i in range(100):
        job_id = job_manager.create_job(
            'app.tasks.test.simple_task',
            data={'index': i}
        )
        job_ids.append(job_id)
    
    # Wait for all to complete
    results = await asyncio.gather(*[
        wait_for_job(job_id) for job_id in job_ids
    ])
    
    # Verify all completed
    assert all(r['status'] == 'completed' for r in results)
```

### Monitoring Setup

#### Prometheus Metrics
```yaml
# prometheus/celery-rules.yml
groups:
  - name: celery_alerts
    rules:
    - alert: CeleryWorkerDown
      expr: up{job="celery-worker"} == 0
      for: 5m
      annotations:
        summary: "Celery worker is down"
        
    - alert: CeleryQueueBacklog
      expr: celery_queue_length > 1000
      for: 10m
      annotations:
        summary: "Celery queue backlog is high"
        
    - alert: CeleryTaskFailureRate
      expr: rate(celery_task_total{status="failed"}[5m]) > 0.1
      for: 5m
      annotations:
        summary: "High task failure rate"
```

#### Grafana Dashboard
```json
{
  "dashboard": {
    "title": "Celery Monitoring",
    "panels": [
      {
        "title": "Task Throughput",
        "targets": [{
          "expr": "rate(celery_task_total[5m])"
        }]
      },
      {
        "title": "Queue Depths",
        "targets": [{
          "expr": "celery_queue_length"
        }]
      },
      {
        "title": "Task Duration P95",
        "targets": [{
          "expr": "histogram_quantile(0.95, celery_task_duration_seconds)"
        }]
      },
      {
        "title": "Worker CPU Usage",
        "targets": [{
          "expr": "rate(container_cpu_usage_seconds_total{pod=~\"celery-worker.*\"}[5m])"
        }]
      }
    ]
  }
}
```

## Post-Migration Cleanup

### Remove Legacy Code
```bash
# Remove old job system files
rm -rf app/core/background_jobs.py
rm -rf app/core/background_task_runner.py
rm -rf app/tasks/old_*

# Remove old imports
find app -name "*.py" -exec grep -l "background_jobs" {} \; | xargs rm

# Clean up database
DELETE FROM alembic_version WHERE version_num IN (
  SELECT version_num FROM alembic_version 
  WHERE script_location LIKE '%background_jobs%'
);
```

### Update Documentation
```markdown
# Job Processing System

## Overview
SynapseDTE uses Celery with Redis for all background job processing.

## Creating Jobs
```python
from app.core.job_manager import job_manager

job_id = job_manager.create_job(
    'app.tasks.module.task_name',
    param1=value1,
    param2=value2,
    metadata={'description': 'Processing data'}
)
```

## Monitoring Jobs
- Flower Dashboard: http://localhost:5555
- API Endpoints: /api/v1/jobs
- Grafana: http://localhost:3000/d/celery

## Job Control
- Pause: POST /api/v1/jobs/{job_id}/pause
- Resume: POST /api/v1/jobs/{job_id}/resume
- Cancel: DELETE /api/v1/jobs/{job_id}
```

## Success Metrics

### Technical Metrics
- [ ] All job types migrated successfully
- [ ] Zero data loss during migration
- [ ] Job completion rate > 99.9%
- [ ] Average latency improved by 20%
- [ ] Checkpoint recovery 100% successful
- [ ] Horizontal scaling demonstrated

### Business Metrics
- [ ] No increase in user-reported issues
- [ ] Job visibility improved (100% traceable)
- [ ] Support ticket reduction for job issues
- [ ] Pause/resume feature actively used
- [ ] Resource costs within budget

## Risk Mitigation

### Migration Risks
1. **Data Loss**: Mitigated by waiting for job completion
2. **Performance Issues**: Mitigated by load testing
3. **Integration Bugs**: Mitigated by comprehensive testing
4. **User Disruption**: Mitigated by maintenance window

### Contingency Plans
1. **Rollback Procedure**: Keep old code in version control
2. **Data Recovery**: Database backups before cutover
3. **Emergency Fix**: Hotfix deployment procedure ready
4. **Communication**: User notification templates prepared

## Conclusion

This revised plan provides a cleaner, more direct migration path to Celery:

1. **Simpler Architecture**: No dual systems or adapters
2. **Faster Implementation**: 5-6 weeks vs 8-10 weeks
3. **Cleaner Codebase**: Complete removal of legacy code
4. **Better Performance**: No overhead from compatibility layers
5. **Easier Maintenance**: Single system to monitor and manage

The direct migration approach reduces complexity and technical debt while delivering all required features in a production-ready implementation.