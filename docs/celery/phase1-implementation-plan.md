# Phase 1: Detailed Implementation Plan

## Executive Summary

This implementation plan outlines a systematic approach to migrate SynapseDTE's background job processing system from the current custom implementation to Celery with Redis. The plan emphasizes risk mitigation through parallel running, phased migration, comprehensive testing, and rollback capabilities at each stage.

## Implementation Timeline

### Overall Timeline: 8-10 weeks
- **Phase 2 (Core Infrastructure)**: 2 weeks
- **Phase 3 (Job Migration)**: 3-4 weeks  
- **Phase 4 (Advanced Features)**: 1-2 weeks
- **Phase 5 (Containerization)**: 1 week
- **Phase 6 (Testing & Validation)**: 1-2 weeks

## Phase 2: Core Infrastructure Implementation (Weeks 1-2)

### Week 1: Redis and Celery Setup

#### Day 1-2: Redis Infrastructure
1. **Local Development Setup**
   ```bash
   # Docker Compose for Redis
   services:
     redis:
       image: redis:7-alpine
       ports:
         - "6379:6379"
       volumes:
         - redis_data:/data
       command: redis-server --appendonly yes
   ```

2. **Redis Configuration**
   - Set up persistence (AOF + RDB)
   - Configure memory limits
   - Set up Redis Sentinel for HA (production)
   - Create separate databases for broker and results

3. **Connection Testing**
   - Verify connectivity from FastAPI
   - Test persistence across restarts
   - Benchmark performance

#### Day 3-4: Celery Framework
1. **Install Dependencies**
   ```python
   # requirements.txt additions
   celery[redis]==5.3.4
   flower==2.0.1
   redis==5.0.1
   celery-progress==0.3
   ```

2. **Create Celery Application**
   - `app/core/celery_app.py` - Main Celery instance
   - `app/core/celery_config.py` - Configuration
   - `app/core/celery_worker.py` - Worker initialization

3. **Basic Task Structure**
   ```python
   app/
   ├── tasks/
   │   ├── __init__.py
   │   ├── base.py          # Base task classes
   │   ├── data_profiling/
   │   ├── planning/
   │   ├── scoping/
   │   └── test_execution/
   ```

#### Day 5: Checkpoint System
1. **Implement CheckpointableTask Base Class**
   - Redis-based checkpoint storage
   - Automatic checkpoint management
   - Checkpoint expiration handling

2. **Create Checkpoint Schema**
   ```python
   {
     "task_id": "uuid",
     "task_name": "process_data_profiling",
     "checkpoint_data": {
       "current_index": 45,
       "total_items": 100,
       "processed_items": ["id1", "id2", ...],
       "state": {...}
     },
     "created_at": "2025-01-28T10:00:00Z",
     "expires_at": "2025-01-29T10:00:00Z"
   }
   ```

### Week 2: Job Control and Integration

#### Day 6-7: Job Control API
1. **Enhanced Job Manager**
   - Create `CeleryJobManager` class
   - Implement pause/resume logic
   - Add job metadata storage
   - Create job status tracking

2. **API Endpoints**
   ```python
   # New endpoints
   POST   /api/v1/jobs/{job_id}/pause
   POST   /api/v1/jobs/{job_id}/resume  
   POST   /api/v1/jobs/{job_id}/restart
   DELETE /api/v1/jobs/{job_id}
   GET    /api/v1/jobs?status=running
   ```

3. **Backward Compatibility Layer**
   ```python
   class JobManagerAdapter:
       """Adapter to maintain compatibility with existing code"""
       def create_job(self, job_type, metadata):
           # Route to appropriate Celery task
           return celery_job_manager.create_job(...)
   ```

#### Day 8-9: Monitoring Integration
1. **Flower Setup**
   - Configure Flower dashboard
   - Set up authentication
   - Create custom API endpoints

2. **Metrics Collection**
   - Prometheus exporter setup
   - Custom metrics for job types
   - Dashboard templates

3. **Logging Integration**
   - Structured logging format
   - Correlation ID propagation
   - Error aggregation setup

#### Day 10: Integration Testing
1. **Create Test Suite**
   - Unit tests for all components
   - Integration tests for job flow
   - Performance benchmarks

2. **Documentation**
   - Developer guide
   - Deployment instructions
   - Troubleshooting guide

## Phase 3: Job Migration Implementation (Weeks 3-6)

### Migration Order (Risk-Based)
1. **Week 3**: Low-risk jobs (Sample Selection)
2. **Week 4**: Medium-risk jobs (Planning, Scoping)
3. **Week 5-6**: High-risk jobs (Data Profiling, Test Execution)

### Week 3: Sample Selection Migration

#### Day 1-2: Task Implementation
```python
# app/tasks/sample_selection/intelligent_sampling.py
@celery_app.task(base=ResumableTask, bind=True)
def intelligent_sampling_task(self, cycle_id: int, report_id: int, 
                            sample_config: dict, 
                            resume_from_checkpoint: dict = None):
    """Migrated intelligent sampling task"""
    # Implementation with checkpoint support
```

#### Day 3: Integration
1. **Update Service Layer**
   ```python
   class SampleSelectionService:
       def trigger_intelligent_sampling(self, ...):
           # Use Celery instead of threading
           result = intelligent_sampling_task.apply_async(...)
           return result.id
   ```

2. **Update Endpoints**
   - Modify existing endpoints to use new service
   - Add feature flag for rollback

#### Day 4-5: Testing
- Unit tests for task logic
- Integration tests with real data
- Performance comparison
- Rollback testing

### Week 4: Planning and Scoping Migration

#### Planning Tasks (Day 1-2)
1. **PDE Mapping Tasks**
   ```python
   @celery_app.task(base=ResumableTask, bind=True)
   def auto_map_pdes_task(self, phase_id: int, ...):
       # Checkpoint after each batch of mappings
   ```

2. **LLM Attribute Generation**
   - Implement with retry logic
   - Add rate limiting for LLM calls
   - Checkpoint after each attribute

#### Scoping Tasks (Day 3-4)
1. **Recommendation Generation**
   - Batch processing support
   - Progress tracking per section
   - Partial result saving

2. **Integration and Testing** (Day 5)
   - Service layer updates
   - Endpoint modifications
   - A/B testing setup

### Week 5-6: Data Profiling Migration

#### Week 5: Rule Generation
1. **LLM Rule Generation Task**
   ```python
   @celery_app.task(base=ResumableTask, bind=True, 
                    time_limit=3600, soft_time_limit=3000)
   def generate_profiling_rules_task(self, version_id: str, 
                                   attributes: list,
                                   resume_from_checkpoint: dict = None):
       # Heavy LLM processing with checkpoints
   ```

2. **Optimization**
   - Implement request batching
   - Add caching layer
   - Parallel processing where possible

#### Week 6: Rule Execution
1. **Rule Execution Task**
   - Database query optimization
   - Memory-efficient processing
   - Result streaming

2. **Complex Integration**
   - Handle large datasets
   - Implement chunking
   - Progress reporting

## Phase 4: Advanced Features (Week 7)

### Dynamic Scaling
1. **Implement Autoscaling**
   ```python
   # Celery autoscale configuration
   celery_app.conf.worker_autoscaler = 'celery.worker.autoscale.Autoscaler'
   celery_app.conf.worker_autoscale_max = 10
   celery_app.conf.worker_autoscale_min = 2
   ```

2. **Queue-Based Scaling**
   - Monitor queue depths
   - Scale workers based on load
   - Implement priority queues

### Advanced Job Control
1. **Job Dependencies**
   ```python
   from celery import group, chain, chord
   
   # Complex workflow
   workflow = chord(
       group(preprocess.s(item) for item in items),
       aggregate_results.s()
   )
   ```

2. **Scheduled Jobs**
   - Implement Celery Beat
   - Recurring job patterns
   - Maintenance tasks

## Phase 5: Containerization (Week 8)

### Docker Configuration
1. **Celery Worker Dockerfile**
   ```dockerfile
   FROM python:3.11-slim
   
   WORKDIR /app
   
   # Install dependencies
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   
   # Copy application
   COPY . .
   
   # Run worker
   CMD ["celery", "-A", "app.core.celery_app", "worker", 
        "--loglevel=info", "--concurrency=4"]
   ```

2. **Docker Compose Updates**
   ```yaml
   services:
     celery-worker:
       build: .
       command: celery -A app.core.celery_app worker
       environment:
         - REDIS_URL=redis://redis:6379/0
       depends_on:
         - redis
         - postgres
       deploy:
         replicas: 3
   
     celery-beat:
       build: .
       command: celery -A app.core.celery_app beat
       depends_on:
         - redis
   
     flower:
       build: .
       command: celery -A app.core.celery_app flower
       ports:
         - "5555:5555"
   ```

### Kubernetes Deployment
1. **Worker Deployment**
   ```yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: celery-worker
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
           resources:
             requests:
               memory: "512Mi"
               cpu: "500m"
             limits:
               memory: "2Gi"
               cpu: "2000m"
   ```

## Phase 6: Testing & Validation (Week 9-10)

### Week 9: Comprehensive Testing

#### Unit Testing
1. **Task Testing**
   ```python
   @pytest.mark.asyncio
   async def test_data_profiling_task_with_checkpoint():
       # Test normal execution
       # Test checkpoint save/load
       # Test resume from checkpoint
       # Test failure scenarios
   ```

2. **Integration Testing**
   - End-to-end job flows
   - API endpoint testing
   - Database state verification

#### Performance Testing
1. **Load Testing**
   - Concurrent job execution
   - Queue saturation testing
   - Worker scaling verification

2. **Benchmark Comparisons**
   - Old vs new system performance
   - Resource usage analysis
   - Latency measurements

### Week 10: Production Validation

#### Staged Rollout
1. **Canary Deployment**
   - 10% traffic to new system
   - Monitor error rates
   - Performance comparison

2. **Progressive Rollout**
   - 25% → 50% → 100%
   - Rollback procedures ready
   - Monitoring at each stage

#### Documentation and Training
1. **Operations Guide**
   - Deployment procedures
   - Monitoring setup
   - Troubleshooting guide

2. **Developer Training**
   - Code examples
   - Best practices
   - Migration guide

## Risk Mitigation

### Technical Risks
1. **Data Loss**
   - Mitigation: Comprehensive checkpointing
   - Rollback: Keep old system running

2. **Performance Degradation**
   - Mitigation: Extensive benchmarking
   - Rollback: Feature flags per job type

3. **Integration Issues**
   - Mitigation: Adapter pattern
   - Rollback: Dual execution paths

### Operational Risks
1. **Deployment Failures**
   - Mitigation: Staged rollout
   - Rollback: Blue-green deployment

2. **Monitoring Gaps**
   - Mitigation: Comprehensive metrics
   - Rollback: Keep existing monitoring

## Success Metrics

### Technical Metrics
- Job completion rate > 99.9%
- Average job latency < current system
- Zero data loss during migration
- 100% checkpoint recovery success

### Business Metrics
- No increase in user-reported issues
- Improved job visibility
- Reduced operational overhead
- Successful pause/resume usage

## Rollback Plan

### Per-Phase Rollback
1. **Phase 2**: Remove Celery, keep using old system
2. **Phase 3**: Revert specific job types via feature flags
3. **Phase 4**: Disable advanced features, use basic
4. **Phase 5**: Continue with local deployment
5. **Phase 6**: Extend parallel running period

### Emergency Procedures
1. **Critical Issue Detection**
   - Automated alerts
   - Health check failures
   - Error rate thresholds

2. **Rollback Execution**
   - DNS/Load balancer switch
   - Feature flag toggles
   - Database state preservation

## Conclusion

This implementation plan provides a structured, risk-aware approach to migrating to Celery with Redis. Key aspects include:

1. **Gradual Migration**: Phased approach minimizes risk
2. **Parallel Running**: Both systems operate during transition
3. **Comprehensive Testing**: Each phase thoroughly validated
4. **Rollback Capability**: Can revert at any stage
5. **Clear Metrics**: Success measurable at each milestone

The plan balances the need for new capabilities with operational stability, ensuring a smooth transition to the enhanced job processing system.