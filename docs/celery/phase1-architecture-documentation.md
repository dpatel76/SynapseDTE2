# Phase 1: Complete Architecture Documentation

## Table of Contents
1. [System Architecture Overview](#system-architecture-overview)
2. [Component Architecture](#component-architecture)
3. [Data Flow Architecture](#data-flow-architecture)
4. [Integration Architecture](#integration-architecture)
5. [Deployment Architecture](#deployment-architecture)
6. [Security Architecture](#security-architecture)
7. [Monitoring Architecture](#monitoring-architecture)
8. [Migration Architecture](#migration-architecture)

## System Architecture Overview

### High-Level Architecture Diagram

```
┌────────────────────────────────────────────────────────────────────────────┐
│                            SynapseDTE Application                           │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────┐   ┌────────────┐│
│  │   FastAPI   │    │   Frontend   │    │   Temporal  │   │  External  ││
│  │   Backend   │◄──►│   (React)    │    │  Workflows  │   │   APIs     ││
│  └──────┬──────┘    └──────────────┘    └──────┬──────┘   └─────┬──────┘│
│         │                                       │                  │       │
├─────────┼───────────────────────────────────────┼──────────────────┼───────┤
│         ▼                                       ▼                  ▼       │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                      Job Processing Layer                            │  │
│  ├─────────────────────────────────────────────────────────────────────┤  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐│  │
│  │  │Job Manager  │  │   Celery    │  │   Redis     │  │ Monitoring ││  │
│  │  │  Adapter    │──│   Tasks     │──│   Broker    │──│  (Flower)  ││  │
│  │  └─────────────┘  └──────┬──────┘  └──────┬──────┘  └────────────┘│  │
│  │                          │                 │                        │  │
│  │  ┌─────────────────────────────────────────────────────────────┐  │  │
│  │  │                    Celery Workers Pool                       │  │  │
│  │  ├─────────────┬─────────────┬─────────────┬─────────────────┤  │  │
│  │  │  Worker 1   │  Worker 2   │  Worker 3   │    Worker N     │  │  │
│  │  │ ┌─────────┐ │ ┌─────────┐ │ ┌─────────┐ │  ┌───────────┐ │  │  │
│  │  │ │ Tasks   │ │ │ Tasks   │ │ │ Tasks   │ │  │  Tasks    │ │  │  │
│  │  │ │ Engine  │ │ │ Engine  │ │ │ Engine  │ │  │  Engine   │ │  │  │
│  │  │ └─────────┘ │ └─────────┘ │ └─────────┘ │  └───────────┘ │  │  │
│  │  └─────────────┴─────────────┴─────────────┴─────────────────┘  │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                       │                                    │
├───────────────────────────────────────┼────────────────────────────────────┤
│                                       ▼                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                         Data Layer                                   │  │
│  ├─────────────────────────────────────────────────────────────────────┤  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐│  │
│  │  │ PostgreSQL  │  │   Redis     │  │   MinIO/S3  │  │ File System││  │
│  │  │  Database   │  │   Cache     │  │   Storage   │  │  Storage   ││  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘│  │
│  └─────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────┘
```

### Key Architectural Principles

1. **Separation of Concerns**
   - Clear boundaries between layers
   - Single responsibility per component
   - Loose coupling through interfaces

2. **Scalability First**
   - Horizontal scaling of workers
   - Queue-based load distribution
   - Stateless worker design

3. **Fault Tolerance**
   - Checkpoint-based recovery
   - Automatic retry mechanisms
   - Circuit breaker patterns

4. **Observable System**
   - Comprehensive metrics
   - Distributed tracing
   - Centralized logging

## Component Architecture

### Core Components

#### 1. Job Manager Adapter
```python
class JobManagerAdapter:
    """
    Maintains backward compatibility while routing to Celery
    """
    def __init__(self):
        self.celery_manager = CeleryJobManager()
        self.legacy_manager = BackgroundJobManager()  # During transition
    
    def create_job(self, job_type: str, metadata: dict) -> str:
        # Route based on configuration
        if is_celery_enabled(job_type):
            return self.celery_manager.create_job(
                task_name=self._get_task_name(job_type),
                job_type=job_type,
                metadata=metadata
            )
        else:
            return self.legacy_manager.create_job(job_type, metadata)
```

#### 2. Celery Task Registry
```python
# app/tasks/registry.py
class TaskRegistry:
    """Central registry for all Celery tasks"""
    
    _tasks = {
        'data_profiling_llm_generation': 'app.tasks.data_profiling.generate_rules',
        'data_profiling_rule_execution': 'app.tasks.data_profiling.execute_rules',
        'pde_auto_mapping': 'app.tasks.planning.auto_map_pdes',
        'scoping_recommendations': 'app.tasks.scoping.generate_recommendations',
        'intelligent_sampling': 'app.tasks.sample_selection.intelligent_sample',
        'test_execution': 'app.tasks.test_execution.execute_tests',
    }
    
    @classmethod
    def get_task(cls, job_type: str) -> str:
        return cls._tasks.get(job_type)
```

#### 3. Checkpoint Manager
```python
class CheckpointManager:
    """Manages task checkpoints in Redis"""
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.ttl = 86400  # 24 hours
    
    def save_checkpoint(self, task_id: str, data: dict):
        key = f"checkpoint:{task_id}"
        value = {
            'data': data,
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0'
        }
        self.redis.setex(key, self.ttl, json.dumps(value))
    
    def load_checkpoint(self, task_id: str) -> Optional[dict]:
        key = f"checkpoint:{task_id}"
        data = self.redis.get(key)
        return json.loads(data) if data else None
```

### Task Architecture

#### Base Task Classes
```python
# app/tasks/base.py
class BaseTask(Task):
    """Base class for all Celery tasks"""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure"""
        logger.error(f"Task {task_id} failed: {exc}")
        # Update job status
        # Send notifications
        # Clean up resources
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Handle task retry"""
        logger.warning(f"Task {task_id} retrying: {exc}")
        # Update retry count
        # Adjust parameters if needed
    
    def on_success(self, retval, task_id, args, kwargs):
        """Handle task success"""
        logger.info(f"Task {task_id} completed successfully")
        # Clean up checkpoints
        # Update metrics

class CheckpointableTask(BaseTask):
    """Task with checkpoint support"""
    
    checkpoint_manager = CheckpointManager(redis_client)
    
    def save_checkpoint(self, task_id: str, checkpoint_data: dict):
        self.checkpoint_manager.save_checkpoint(task_id, checkpoint_data)
    
    def load_checkpoint(self, task_id: str) -> Optional[dict]:
        return self.checkpoint_manager.load_checkpoint(task_id)

class LLMTask(CheckpointableTask):
    """Specialized task for LLM operations"""
    
    rate_limiter = RateLimiter(max_calls=60, period=60)  # 60 calls/minute
    
    async def call_llm_with_retry(self, prompt: str, **kwargs):
        """Call LLM service with rate limiting and retry"""
        await self.rate_limiter.acquire()
        
        for attempt in range(3):
            try:
                return await llm_service.generate(prompt, **kwargs)
            except RateLimitError:
                await asyncio.sleep(2 ** attempt)
            except Exception as e:
                if attempt == 2:
                    raise
                logger.warning(f"LLM call failed, retrying: {e}")
```

## Data Flow Architecture

### Job Lifecycle Flow

```
1. Job Creation
   Client Request → FastAPI Endpoint → Job Manager Adapter → Celery Task Queue

2. Job Execution  
   Redis Queue → Celery Worker → Task Execution → Checkpoint Updates → Progress Updates

3. Job Monitoring
   Client Poll → API Status Check → Redis Result Backend → Response

4. Job Completion
   Task Complete → Result Storage → Notification → Cleanup
```

### Checkpoint Flow

```python
# Checkpoint save flow during execution
async def process_items_with_checkpoints(items: List[Any], task_id: str):
    checkpoint = load_checkpoint(task_id) or {'processed': []}
    processed = checkpoint['processed']
    
    for i, item in enumerate(items):
        if item.id in processed:
            continue  # Skip already processed
            
        try:
            result = await process_item(item)
            processed.append(item.id)
            
            # Save checkpoint every 10 items
            if i % 10 == 0:
                save_checkpoint(task_id, {
                    'processed': processed,
                    'current_index': i,
                    'total': len(items)
                })
                
        except Exception as e:
            # Checkpoint before failing
            save_checkpoint(task_id, {
                'processed': processed,
                'failed_at': item.id,
                'error': str(e)
            })
            raise
```

### Message Flow Patterns

#### 1. Direct Task Execution
```python
# Immediate execution
result = task.apply_async(args=[data], kwargs={'user_id': user.id})
```

#### 2. Scheduled Execution
```python
# Execute in 5 minutes
result = task.apply_async(args=[data], countdown=300)

# Execute at specific time
result = task.apply_async(args=[data], eta=datetime(2025, 1, 30, 10, 0))
```

#### 3. Chain Execution
```python
# Sequential task execution
from celery import chain

workflow = chain(
    fetch_data.s(source_id),
    validate_data.s(),
    process_data.s(),
    save_results.s()
)
result = workflow.apply_async()
```

#### 4. Parallel Execution
```python
# Parallel task execution
from celery import group

job = group(
    process_item.s(item) for item in items
)
result = job.apply_async()
```

## Integration Architecture

### API Integration Layer

```python
# app/api/v1/endpoints/jobs.py
class JobsAPI:
    """Unified job management API"""
    
    @router.post("/jobs")
    async def create_job(self, request: JobCreateRequest) -> JobResponse:
        # Validate request
        # Check permissions
        # Create job via adapter
        # Return job ID and status
    
    @router.get("/jobs/{job_id}")
    async def get_job_status(self, job_id: str) -> JobStatusResponse:
        # Fetch from Celery or legacy system
        # Transform to unified format
        # Include progress and metadata
    
    @router.post("/jobs/{job_id}/control")
    async def control_job(self, job_id: str, action: JobAction) -> JobResponse:
        # Pause, resume, cancel operations
        # Validate action permissions
        # Execute control operation
```

### Database Integration

```python
# app/tasks/db_utils.py
class TaskDatabaseSession:
    """Manages database sessions for tasks"""
    
    @contextmanager
    def get_task_session(self):
        """Create isolated session for task execution"""
        session = AsyncSession(engine)
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# Usage in tasks
@celery_app.task(base=CheckpointableTask)
async def process_data_task(data_id: str):
    async with TaskDatabaseSession().get_task_session() as db:
        # All database operations within session
        data = await db.get(DataModel, data_id)
        # Process data
        await db.commit()
```

### External Service Integration

```python
# app/tasks/external_services.py
class ExternalServiceClient:
    """Manages external service calls with circuit breaker"""
    
    def __init__(self):
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
            expected_exception=ServiceException
        )
    
    @circuit_breaker
    async def call_service(self, endpoint: str, data: dict):
        """Call external service with protection"""
        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint, json=data) as response:
                if response.status >= 500:
                    raise ServiceException("Service unavailable")
                return await response.json()
```

## Deployment Architecture

### Container Architecture

```yaml
# docker-compose.yml
version: '3.8'

services:
  # Redis - Message Broker and Result Backend
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  # Celery Worker - General Tasks
  celery-worker:
    build:
      context: .
      dockerfile: Dockerfile.worker
    command: celery -A app.core.celery_app worker -Q default,planning,scoping -n worker@%h
    environment:
      - CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - CELERY_RESULT_BACKEND=redis://:${REDIS_PASSWORD}@redis:6379/1
    depends_on:
      redis:
        condition: service_healthy
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '2'
          memory: 2G

  # Celery Worker - LLM Tasks (Resource Intensive)
  celery-worker-llm:
    build:
      context: .
      dockerfile: Dockerfile.worker
    command: celery -A app.core.celery_app worker -Q llm_processing -n llm@%h -c 2
    environment:
      - CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      redis:
        condition: service_healthy
    deploy:
      replicas: 1
      resources:
        limits:
          cpus: '4'
          memory: 4G

  # Celery Worker - Data Profiling (Memory Intensive)
  celery-worker-profiling:
    build:
      context: .
      dockerfile: Dockerfile.worker
    command: celery -A app.core.celery_app worker -Q data_profiling -n profiling@%h -c 1
    depends_on:
      redis:
        condition: service_healthy
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '2'
          memory: 8G

  # Celery Beat - Scheduled Tasks
  celery-beat:
    build:
      context: .
      dockerfile: Dockerfile.worker
    command: celery -A app.core.celery_app beat -l info
    depends_on:
      redis:
        condition: service_healthy
    deploy:
      replicas: 1

  # Flower - Monitoring Dashboard
  flower:
    build:
      context: .
      dockerfile: Dockerfile.worker
    command: celery -A app.core.celery_app flower --basic_auth=${FLOWER_USER}:${FLOWER_PASSWORD}
    ports:
      - "5555:5555"
    depends_on:
      redis:
        condition: service_healthy
    deploy:
      replicas: 1
```

### Kubernetes Architecture

```yaml
# k8s/celery-worker-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: celery-worker
  labels:
    app: celery-worker
spec:
  replicas: 3
  selector:
    matchLabels:
      app: celery-worker
  template:
    metadata:
      labels:
        app: celery-worker
    spec:
      containers:
      - name: worker
        image: synapse-dte:latest
        command: ["celery", "-A", "app.core.celery_app", "worker"]
        env:
        - name: CELERY_BROKER_URL
          valueFrom:
            secretKeyRef:
              name: celery-secrets
              key: broker-url
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "4Gi"
            cpu: "2"
        livenessProbe:
          exec:
            command:
            - celery
            - inspect
            - ping
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          exec:
            command:
            - celery
            - inspect
            - ping
          initialDelaySeconds: 10
          periodSeconds: 10
---
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
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

## Security Architecture

### Authentication & Authorization

```python
# app/tasks/security.py
class TaskSecurity:
    """Security layer for task execution"""
    
    @staticmethod
    def verify_task_permissions(user_id: str, task_type: str) -> bool:
        """Verify user has permission to execute task type"""
        # Check user roles
        # Verify task permissions
        # Log access attempt
        return has_permission
    
    @staticmethod
    def encrypt_sensitive_data(data: dict) -> dict:
        """Encrypt sensitive task data"""
        # Identify sensitive fields
        # Apply encryption
        # Return encrypted data
    
    @staticmethod
    def sanitize_task_input(data: dict) -> dict:
        """Sanitize task input to prevent injection"""
        # Validate input types
        # Escape special characters
        # Remove dangerous patterns
```

### Network Security

```yaml
# Redis TLS Configuration
redis:
  image: redis:7-alpine
  command: >
    redis-server
    --tls-port 6379
    --port 0
    --tls-cert-file /tls/redis.crt
    --tls-key-file /tls/redis.key
    --tls-ca-cert-file /tls/ca.crt
    --tls-auth-clients yes
  volumes:
    - ./certs:/tls:ro
```

### Data Security

```python
# Task data encryption
class EncryptedTask(CheckpointableTask):
    """Task with encrypted checkpoint support"""
    
    def save_checkpoint(self, task_id: str, checkpoint_data: dict):
        # Encrypt sensitive data
        encrypted_data = encrypt_data(checkpoint_data, get_encryption_key())
        super().save_checkpoint(task_id, encrypted_data)
    
    def load_checkpoint(self, task_id: str) -> Optional[dict]:
        encrypted_data = super().load_checkpoint(task_id)
        if encrypted_data:
            return decrypt_data(encrypted_data, get_encryption_key())
        return None
```

## Monitoring Architecture

### Metrics Collection

```python
# app/core/monitoring.py
from prometheus_client import Counter, Histogram, Gauge, Info

# Define metrics
task_counter = Counter(
    'celery_task_total',
    'Total number of tasks',
    ['task_name', 'status', 'queue']
)

task_duration = Histogram(
    'celery_task_duration_seconds',
    'Task execution duration',
    ['task_name', 'queue']
)

queue_length = Gauge(
    'celery_queue_length',
    'Number of tasks in queue',
    ['queue_name']
)

worker_info = Info(
    'celery_worker_info',
    'Worker information'
)

# Collect metrics
@task_prerun.connect
def collect_task_start_metrics(sender=None, task_id=None, task=None, **kwargs):
    task_counter.labels(
        task_name=task.name,
        status='started',
        queue=task.request.delivery_info.get('routing_key', 'default')
    ).inc()

@task_postrun.connect
def collect_task_complete_metrics(sender=None, task_id=None, task=None, 
                                state=None, **kwargs):
    duration = time.time() - task.request.start_time
    task_duration.labels(
        task_name=task.name,
        queue=task.request.delivery_info.get('routing_key', 'default')
    ).observe(duration)
    
    task_counter.labels(
        task_name=task.name,
        status=state,
        queue=task.request.delivery_info.get('routing_key', 'default')
    ).inc()
```

### Logging Architecture

```python
# app/core/logging_config.py
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.CallsiteParameterAdder(
            parameters=[
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.LINENO,
                structlog.processors.CallsiteParameter.FUNC_NAME,
            ]
        ),
        structlog.processors.dict_tracebacks,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

# Task logging
logger = structlog.get_logger()

@celery_app.task
def example_task(data):
    logger.info(
        "task_started",
        task_id=current_task.request.id,
        task_name=current_task.name,
        data_size=len(data)
    )
    
    try:
        result = process_data(data)
        logger.info(
            "task_completed",
            task_id=current_task.request.id,
            result_size=len(result)
        )
        return result
    except Exception as e:
        logger.error(
            "task_failed",
            task_id=current_task.request.id,
            error=str(e),
            exc_info=True
        )
        raise
```

### Dashboard Architecture

```yaml
# Grafana Dashboard Configuration
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-dashboards
data:
  celery-dashboard.json: |
    {
      "dashboard": {
        "title": "Celery Task Monitoring",
        "panels": [
          {
            "title": "Task Execution Rate",
            "targets": [
              {
                "expr": "rate(celery_task_total[5m])"
              }
            ]
          },
          {
            "title": "Task Duration",
            "targets": [
              {
                "expr": "histogram_quantile(0.95, celery_task_duration_seconds)"
              }
            ]
          },
          {
            "title": "Queue Depth",
            "targets": [
              {
                "expr": "celery_queue_length"
              }
            ]
          },
          {
            "title": "Worker Status",
            "targets": [
              {
                "expr": "up{job='celery-worker'}"
              }
            ]
          }
        ]
      }
    }
```

## Migration Architecture

### Dual-Mode Operation

```python
# app/core/job_router.py
class JobRouter:
    """Routes jobs between legacy and Celery systems"""
    
    def __init__(self):
        self.feature_flags = FeatureFlags()
        self.legacy_manager = BackgroundJobManager()
        self.celery_manager = CeleryJobManager()
    
    def route_job(self, job_type: str, **kwargs) -> str:
        """Route job based on feature flags"""
        if self.feature_flags.is_enabled(f"celery_{job_type}"):
            # Route to Celery
            return self.celery_manager.create_job(job_type, **kwargs)
        else:
            # Route to legacy system
            return self.legacy_manager.create_job(job_type, **kwargs)
    
    def get_job_status(self, job_id: str) -> dict:
        """Get job status from appropriate system"""
        # Check Celery first
        celery_status = self.celery_manager.get_job_status(job_id)
        if celery_status:
            return self._normalize_celery_status(celery_status)
        
        # Fall back to legacy
        legacy_status = self.legacy_manager.get_job_status(job_id)
        if legacy_status:
            return legacy_status
        
        raise JobNotFoundError(f"Job {job_id} not found")
```

### Migration State Tracking

```python
# app/core/migration_tracker.py
class MigrationTracker:
    """Tracks migration progress"""
    
    def __init__(self):
        self.redis = Redis.from_url(REDIS_URL)
    
    def mark_job_type_migrated(self, job_type: str):
        """Mark a job type as migrated to Celery"""
        key = f"migration:job_type:{job_type}"
        self.redis.hset(key, {
            'migrated': True,
            'migrated_at': datetime.utcnow().isoformat(),
            'version': '1.0'
        })
    
    def get_migration_status(self) -> dict:
        """Get overall migration status"""
        all_job_types = TaskRegistry.get_all_job_types()
        migrated = []
        pending = []
        
        for job_type in all_job_types:
            if self.is_migrated(job_type):
                migrated.append(job_type)
            else:
                pending.append(job_type)
        
        return {
            'total': len(all_job_types),
            'migrated': len(migrated),
            'pending': len(pending),
            'progress': len(migrated) / len(all_job_types) * 100,
            'details': {
                'migrated': migrated,
                'pending': pending
            }
        }
```

### Rollback Mechanism

```python
# app/core/rollback.py
class RollbackManager:
    """Manages rollback procedures"""
    
    def rollback_job_type(self, job_type: str):
        """Rollback a specific job type to legacy system"""
        # Disable Celery routing
        feature_flags.disable(f"celery_{job_type}")
        
        # Stop accepting new Celery tasks
        celery_app.control.cancel_consumer(job_type)
        
        # Wait for in-flight tasks
        self._wait_for_tasks(job_type)
        
        # Update migration status
        migration_tracker.mark_job_type_rollback(job_type)
        
        logger.warning(f"Rolled back job type {job_type} to legacy system")
    
    def emergency_rollback_all(self):
        """Emergency rollback all job types"""
        # Disable all Celery routing
        feature_flags.disable_pattern("celery_*")
        
        # Stop all Celery workers gracefully
        celery_app.control.shutdown()
        
        # Switch traffic to legacy system
        load_balancer.route_all_to_legacy()
        
        logger.critical("Emergency rollback executed - all traffic to legacy")
```

## Summary

This architecture provides:

1. **Robust Foundation**: Enterprise-grade job processing with Celery and Redis
2. **Seamless Migration**: Dual-mode operation with gradual rollout
3. **Full Control**: Pause, resume, and restart capabilities
4. **High Availability**: Fault tolerance and automatic recovery
5. **Scalability**: Horizontal scaling and resource management
6. **Observability**: Comprehensive monitoring and logging
7. **Security**: Multiple layers of protection
8. **Flexibility**: Adaptable to changing requirements

The architecture is designed to evolve with the application's needs while maintaining stability and performance throughout the migration and beyond.