# Phase 1: Celery Architecture Design with Redis

## Executive Summary

This document outlines the proposed architecture for migrating SynapseDTE's background job processing system to Celery with Redis. The design focuses on providing fault tolerance, scalability, job control capabilities, and seamless integration with the existing codebase while maintaining backward compatibility during the transition period.

## Architecture Overview

### High-Level Components

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   FastAPI App   │────▶│  Redis Broker   │────▶│ Celery Workers  │
│   (Producer)    │     │  (Message Queue)│     │  (Consumers)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                       │                        │
         │                       ▼                        │
         │              ┌─────────────────┐              │
         │              │  Redis Backend  │              │
         │              │ (Result Store)  │              │
         │              └─────────────────┘              │
         │                       │                        │
         ▼                       ▼                        ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   PostgreSQL    │     │ Job State Store │     │   Monitoring    │
│   (App Data)    │     │  (Checkpoints)  │     │   (Flower)      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Core Components Design

### 1. Celery Application Configuration

```python
# app/core/celery_config.py
from celery import Celery
from kombu import Exchange, Queue
import os

# Redis configuration
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
REDIS_BACKEND_URL = os.getenv('REDIS_BACKEND_URL', 'redis://localhost:6379/1')

# Create Celery app
celery_app = Celery('synapse_dte')

# Broker and backend configuration
celery_app.conf.update(
    broker_url=REDIS_URL,
    result_backend=REDIS_BACKEND_URL,
    
    # Task execution settings
    task_track_started=True,
    task_time_limit=3600,  # 1 hour hard limit
    task_soft_time_limit=3000,  # 50 min soft limit
    task_acks_late=True,  # Ensure fault tolerance
    
    # Result settings
    result_expires=86400,  # 24 hours
    result_persistent=True,
    
    # Serialization
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    
    # Worker settings
    worker_prefetch_multiplier=1,  # One task at a time for long-running jobs
    worker_max_tasks_per_child=10,  # Restart worker after 10 tasks (memory management)
    
    # Task routing
    task_routes={
        'app.tasks.data_profiling.*': {'queue': 'data_profiling'},
        'app.tasks.llm.*': {'queue': 'llm_processing'},
        'app.tasks.planning.*': {'queue': 'planning'},
        'app.tasks.test_execution.*': {'queue': 'test_execution'},
        'app.tasks.sample_selection.*': {'queue': 'sample_selection'},
    },
    
    # Queue configuration
    task_queues=(
        Queue('default', Exchange('default'), routing_key='default'),
        Queue('data_profiling', Exchange('tasks'), routing_key='data_profiling', 
              queue_arguments={'x-max-priority': 10}),
        Queue('llm_processing', Exchange('tasks'), routing_key='llm_processing',
              queue_arguments={'x-max-priority': 10}),
        Queue('planning', Exchange('tasks'), routing_key='planning'),
        Queue('test_execution', Exchange('tasks'), routing_key='test_execution'),
        Queue('sample_selection', Exchange('tasks'), routing_key='sample_selection'),
    ),
    
    # Beat schedule for periodic tasks
    beat_schedule={
        'cleanup-old-jobs': {
            'task': 'app.tasks.maintenance.cleanup_old_jobs',
            'schedule': 3600.0,  # Every hour
        },
    }
)
```

### 2. Enhanced Job State Management

```python
# app/core/celery_job_manager.py
from typing import Dict, Any, Optional
import json
from datetime import datetime
from celery import Task, states
from celery.result import AsyncResult
import redis

class CheckpointableTask(Task):
    """Base task class with checkpoint support"""
    
    def __init__(self):
        self.redis_client = redis.Redis.from_url(REDIS_BACKEND_URL)
        self.checkpoint_prefix = "checkpoint:"
    
    def save_checkpoint(self, task_id: str, checkpoint_data: Dict[str, Any]):
        """Save task checkpoint to Redis"""
        key = f"{self.checkpoint_prefix}{task_id}"
        checkpoint = {
            'data': checkpoint_data,
            'timestamp': datetime.utcnow().isoformat(),
            'task_name': self.name
        }
        self.redis_client.setex(
            key, 
            86400,  # 24 hour expiry
            json.dumps(checkpoint)
        )
    
    def load_checkpoint(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Load task checkpoint from Redis"""
        key = f"{self.checkpoint_prefix}{task_id}"
        data = self.redis_client.get(key)
        if data:
            checkpoint = json.loads(data)
            return checkpoint['data']
        return None
    
    def clear_checkpoint(self, task_id: str):
        """Clear task checkpoint"""
        key = f"{self.checkpoint_prefix}{task_id}"
        self.redis_client.delete(key)

class CeleryJobManager:
    """Enhanced job manager for Celery integration"""
    
    def __init__(self):
        self.redis_client = redis.Redis.from_url(REDIS_BACKEND_URL)
        self.job_meta_prefix = "job_meta:"
    
    def create_job(self, task_name: str, job_type: str, 
                   args: tuple = (), kwargs: dict = None, 
                   metadata: dict = None) -> str:
        """Create and dispatch a Celery job"""
        # Import task dynamically
        task = celery_app.tasks[task_name]
        
        # Add job metadata to kwargs
        job_metadata = {
            'job_type': job_type,
            'created_at': datetime.utcnow().isoformat(),
            'metadata': metadata or {}
        }
        
        if kwargs is None:
            kwargs = {}
        kwargs['_job_metadata'] = job_metadata
        
        # Apply task with priority if specified
        priority = metadata.get('priority', 5) if metadata else 5
        result = task.apply_async(
            args=args, 
            kwargs=kwargs,
            priority=priority
        )
        
        # Store additional metadata
        self._store_job_metadata(result.id, job_metadata)
        
        return result.id
    
    def _store_job_metadata(self, job_id: str, metadata: Dict[str, Any]):
        """Store job metadata in Redis"""
        key = f"{self.job_meta_prefix}{job_id}"
        self.redis_client.setex(
            key,
            86400,  # 24 hour expiry
            json.dumps(metadata)
        )
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get comprehensive job status"""
        result = AsyncResult(job_id, app=celery_app)
        
        # Get metadata
        metadata = self._get_job_metadata(job_id)
        
        # Build status response
        status = {
            'job_id': job_id,
            'status': result.state,
            'result': result.result if result.state == states.SUCCESS else None,
            'error': str(result.info) if result.state == states.FAILURE else None,
            'traceback': result.traceback if result.state == states.FAILURE else None,
            'metadata': metadata
        }
        
        # Add progress info if available
        if result.state == 'PROGRESS':
            status.update(result.info)
        
        return status
    
    def pause_job(self, job_id: str) -> bool:
        """Pause a running job"""
        result = AsyncResult(job_id, app=celery_app)
        if result.state == states.PENDING or result.state == 'PROGRESS':
            # Revoke the task
            result.revoke(terminate=False, signal='SIGUSR1')
            # Mark as paused in metadata
            metadata = self._get_job_metadata(job_id)
            metadata['paused'] = True
            metadata['paused_at'] = datetime.utcnow().isoformat()
            self._store_job_metadata(job_id, metadata)
            return True
        return False
    
    def resume_job(self, job_id: str) -> Optional[str]:
        """Resume a paused job from checkpoint"""
        # Get original job metadata
        metadata = self._get_job_metadata(job_id)
        if not metadata or not metadata.get('paused'):
            return None
        
        # Get checkpoint
        checkpoint_key = f"checkpoint:{job_id}"
        checkpoint_data = self.redis_client.get(checkpoint_key)
        if not checkpoint_data:
            return None
        
        checkpoint = json.loads(checkpoint_data)
        
        # Create new job continuing from checkpoint
        task_name = checkpoint['task_name']
        new_job_id = self.create_job(
            task_name=task_name,
            job_type=metadata['job_type'],
            kwargs={'resume_from_checkpoint': checkpoint['data']},
            metadata={
                **metadata['metadata'],
                'resumed_from': job_id,
                'resumed_at': datetime.utcnow().isoformat()
            }
        )
        
        return new_job_id
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a job"""
        result = AsyncResult(job_id, app=celery_app)
        result.revoke(terminate=True)
        # Clear checkpoint
        self.redis_client.delete(f"checkpoint:{job_id}")
        return True
```

### 3. Task Implementation Pattern

```python
# app/tasks/base.py
from celery import current_task
from app.core.celery_job_manager import CheckpointableTask

class ResumableTask(CheckpointableTask):
    """Base class for resumable tasks"""
    
    def update_progress(self, current: int, total: int, 
                       message: str = "", **kwargs):
        """Update task progress"""
        progress = {
            'current': current,
            'total': total,
            'progress_percentage': int((current / total) * 100) if total > 0 else 0,
            'message': message,
            **kwargs
        }
        
        # Update Celery task state
        current_task.update_state(
            state='PROGRESS',
            meta=progress
        )
        
        # Save checkpoint periodically (every 10 items or 5%)
        if current % 10 == 0 or (current / total) > 0.05:
            self.save_progress_checkpoint(current, total, **kwargs)
    
    def save_progress_checkpoint(self, current: int, total: int, **kwargs):
        """Save progress checkpoint"""
        checkpoint_data = {
            'current': current,
            'total': total,
            'timestamp': datetime.utcnow().isoformat(),
            **kwargs
        }
        self.save_checkpoint(current_task.request.id, checkpoint_data)

# Example task implementation
@celery_app.task(base=ResumableTask, bind=True)
def process_data_profiling_rules(self, version_id: str, 
                                resume_from_checkpoint: Dict = None):
    """Process data profiling rules with checkpoint support"""
    
    # Load checkpoint if resuming
    start_index = 0
    if resume_from_checkpoint:
        start_index = resume_from_checkpoint.get('current', 0)
        self.update_progress(
            start_index, 
            resume_from_checkpoint.get('total', 0),
            message="Resuming from checkpoint"
        )
    
    # Get rules to process
    rules = get_rules_for_version(version_id)
    total_rules = len(rules)
    
    # Process rules starting from checkpoint
    for idx in range(start_index, total_rules):
        rule = rules[idx]
        
        try:
            # Process individual rule
            result = process_single_rule(rule)
            
            # Update progress and checkpoint
            self.update_progress(
                idx + 1, 
                total_rules,
                message=f"Processing rule: {rule.name}",
                processed_rules=[r.id for r in rules[:idx+1]]
            )
            
        except Exception as e:
            # Save checkpoint before failing
            self.save_progress_checkpoint(
                idx, 
                total_rules,
                error=str(e),
                failed_rule_id=rule.id
            )
            raise
    
    # Clear checkpoint on successful completion
    self.clear_checkpoint(current_task.request.id)
    
    return {
        'status': 'completed',
        'total_rules_processed': total_rules
    }
```

### 4. Worker Configuration

```python
# app/core/celery_worker_config.py
from celery.signals import worker_ready, worker_shutdown, task_prerun, task_postrun
import logging

logger = logging.getLogger(__name__)

@worker_ready.connect
def on_worker_ready(sender, **kwargs):
    """Initialize worker resources"""
    logger.info(f"Worker {sender.hostname} ready")
    # Initialize database connections
    # Set up monitoring
    # Load ML models if needed

@worker_shutdown.connect
def on_worker_shutdown(sender, **kwargs):
    """Clean up worker resources"""
    logger.info(f"Worker {sender.hostname} shutting down")
    # Close database connections
    # Clean up temporary files
    # Save any pending state

@task_prerun.connect
def on_task_prerun(sender, task_id, task, args, kwargs, **kw):
    """Pre-task setup"""
    logger.info(f"Starting task {task.name} with ID {task_id}")
    # Set up task-specific database session
    # Initialize monitoring context

@task_postrun.connect  
def on_task_postrun(sender, task_id, task, args, kwargs, retval, state, **kw):
    """Post-task cleanup"""
    logger.info(f"Completed task {task.name} with ID {task_id}, state: {state}")
    # Clean up database session
    # Log metrics
    # Clear temporary data
```

### 5. Redis Configuration

```yaml
# docker/redis.conf
# Persistence configuration
save 900 1      # Save after 900 sec if at least 1 key changed
save 300 10     # Save after 300 sec if at least 10 keys changed  
save 60 10000   # Save after 60 sec if at least 10000 keys changed

# Append only file for durability
appendonly yes
appendfsync everysec

# Memory management
maxmemory 2gb
maxmemory-policy allkeys-lru

# Connection settings
timeout 0
tcp-keepalive 300

# Clustering (for scalability)
# cluster-enabled yes
# cluster-config-file nodes.conf
# cluster-node-timeout 5000
```

### 6. Monitoring Integration

```python
# app/core/celery_monitoring.py
from flower.utils.tasks import flower_task
from prometheus_client import Counter, Histogram, Gauge
import time

# Prometheus metrics
task_counter = Counter('celery_tasks_total', 'Total tasks', ['task_name', 'status'])
task_duration = Histogram('celery_task_duration_seconds', 'Task duration', ['task_name'])
active_tasks = Gauge('celery_active_tasks', 'Currently active tasks', ['queue'])

class TaskMonitor:
    """Monitor Celery tasks and export metrics"""
    
    @classmethod
    def record_task_start(cls, task_name: str, queue: str):
        """Record task start"""
        active_tasks.labels(queue=queue).inc()
        task_counter.labels(task_name=task_name, status='started').inc()
    
    @classmethod
    def record_task_complete(cls, task_name: str, queue: str, 
                           duration: float, status: str):
        """Record task completion"""
        active_tasks.labels(queue=queue).dec()
        task_counter.labels(task_name=task_name, status=status).inc()
        task_duration.labels(task_name=task_name).observe(duration)

# Integrate with Celery signals
@task_prerun.connect
def monitor_task_start(sender, task_id, task, **kwargs):
    task.start_time = time.time()
    TaskMonitor.record_task_start(task.name, task.request.routing_key)

@task_postrun.connect
def monitor_task_complete(sender, task_id, task, state, **kwargs):
    duration = time.time() - getattr(task, 'start_time', time.time())
    TaskMonitor.record_task_complete(
        task.name, 
        task.request.routing_key,
        duration,
        state
    )
```

### 7. API Integration Layer

```python
# app/api/v1/endpoints/jobs.py
from fastapi import APIRouter, Depends, HTTPException
from app.core.celery_job_manager import CeleryJobManager
from app.schemas.jobs import (
    JobCreateRequest, JobStatusResponse, 
    JobControlRequest, JobListResponse
)

router = APIRouter()
job_manager = CeleryJobManager()

@router.post("/jobs", response_model=JobStatusResponse)
async def create_job(request: JobCreateRequest, 
                    current_user: User = Depends(get_current_user)):
    """Create a new background job"""
    job_id = job_manager.create_job(
        task_name=request.task_name,
        job_type=request.job_type,
        kwargs=request.parameters,
        metadata={
            'user_id': current_user.user_id,
            'priority': request.priority,
            **request.metadata
        }
    )
    
    return job_manager.get_job_status(job_id)

@router.get("/jobs/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Get job status"""
    status = job_manager.get_job_status(job_id)
    if not status:
        raise HTTPException(404, "Job not found")
    return status

@router.post("/jobs/{job_id}/pause")
async def pause_job(job_id: str):
    """Pause a running job"""
    success = job_manager.pause_job(job_id)
    if not success:
        raise HTTPException(400, "Job cannot be paused")
    return {"status": "paused", "job_id": job_id}

@router.post("/jobs/{job_id}/resume")
async def resume_job(job_id: str):
    """Resume a paused job"""
    new_job_id = job_manager.resume_job(job_id)
    if not new_job_id:
        raise HTTPException(400, "Job cannot be resumed")
    return {"status": "resumed", "job_id": job_id, "new_job_id": new_job_id}

@router.post("/jobs/{job_id}/cancel")
async def cancel_job(job_id: str):
    """Cancel a job"""
    success = job_manager.cancel_job(job_id)
    return {"status": "cancelled", "job_id": job_id}
```

## Scalability Features

### 1. Horizontal Worker Scaling
- Multiple worker processes per machine
- Multiple worker machines
- Queue-based load distribution
- Priority-based task routing

### 2. Resource-Aware Scheduling
```python
# Worker resource limits
celery_app.conf.worker_concurrency = 4  # Number of concurrent tasks
celery_app.conf.worker_max_memory_per_child = 200000  # 200MB per worker

# Task resource requirements
@celery_app.task(base=ResumableTask, bind=True, 
                 resource_limits={'memory': 100000})  # 100MB
def memory_intensive_task(self):
    pass
```

### 3. Auto-Scaling Configuration
```yaml
# kubernetes/celery-worker-hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: celery-worker-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: celery-worker
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Pods
    pods:
      metric:
        name: celery_queue_length
      target:
        type: AverageValue
        averageValue: "30"
```

## Fault Tolerance Mechanisms

### 1. Task Retry Configuration
```python
@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 1 minute
    retry_backoff=True,      # Exponential backoff
    retry_backoff_max=600,   # Max 10 minutes
    retry_jitter=True        # Add randomness to prevent thundering herd
)
def resilient_task(self, data):
    try:
        process_data(data)
    except TemporaryError as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc)
    except PermanentError:
        # Don't retry permanent errors
        raise
```

### 2. Dead Letter Queue
```python
# Failed tasks go to dead letter queue for manual inspection
celery_app.conf.task_dead_letter_queue = 'failed_tasks'
celery_app.conf.task_dead_letter_routing_key = 'failed'
```

### 3. Circuit Breaker Pattern
```python
from circuit_breaker import CircuitBreaker

db_breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60,
    expected_exception=DatabaseError
)

@celery_app.task
@db_breaker
def database_task(data):
    """Task with circuit breaker for database operations"""
    return process_in_database(data)
```

## Migration Strategy

### Phase 1: Parallel Running
- Keep existing job manager
- Add Celery adapter layer
- Route new jobs to Celery
- Maintain backward compatibility

### Phase 2: Gradual Migration
- Migrate one job type at a time
- Maintain dual execution paths
- Monitor performance and reliability
- Rollback capability per job type

### Phase 3: Full Migration
- Remove old job manager
- Update all endpoints
- Clean up legacy code
- Performance optimization

## Security Considerations

### 1. Message Security
- Redis password authentication
- TLS encryption for Redis connections
- Message signing for integrity

### 2. Access Control
- Job ownership tracking
- Role-based queue access
- Audit logging for all operations

### 3. Resource Isolation
- Separate queues per tenant
- CPU and memory limits
- Network isolation for workers

## Performance Optimization

### 1. Task Batching
```python
@celery_app.task
def process_batch(items):
    """Process multiple items in one task"""
    results = []
    for item in items:
        results.append(process_item(item))
    return results
```

### 2. Result Caching
```python
@celery_app.task(cache_result=True, cache_key='data_profiling:{version_id}')
def generate_profiling_rules(version_id):
    """Cache results for repeated requests"""
    return expensive_generation(version_id)
```

### 3. Pipeline Optimization
```python
# Chain tasks for efficient execution
from celery import chain

pipeline = chain(
    fetch_data.s(source_id),
    validate_data.s(),
    process_data.s(),
    store_results.s()
)
pipeline.apply_async()
```

## Monitoring and Observability

### 1. Flower Dashboard
- Real-time task monitoring
- Worker status and health
- Queue lengths and throughput
- Task history and trends

### 2. Prometheus Metrics
- Task execution times
- Queue depths
- Worker utilization
- Error rates

### 3. Logging Integration
- Structured logging
- Correlation IDs
- Distributed tracing
- Error aggregation

## Conclusion

This Celery architecture provides:
1. **Reliability**: Fault tolerance and automatic recovery
2. **Scalability**: Horizontal scaling and resource management
3. **Control**: Full job lifecycle management
4. **Visibility**: Comprehensive monitoring and observability
5. **Performance**: Optimized task execution and resource usage

The design maintains compatibility with existing code while providing a clear migration path and significant improvements in all key areas.