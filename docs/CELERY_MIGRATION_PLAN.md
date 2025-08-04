# Celery Migration Plan - Consistent Background Job Pattern

## Overview
Migrate all `asyncio.create_task()` calls to use Celery tasks for consistent background job handling across all phases.

## Current State Analysis

### Files Using asyncio.create_task():
1. **Planning Phase**
   - `/app/api/v1/endpoints/planning.py` - PDE mapping regeneration
   - `/app/api/v1/endpoints/planning_llm_background.py` - LLM attribute generation
   
2. **Scoping Phase**
   - `/app/api/v1/endpoints/scoping.py` - Scoping recommendations
   
3. **Sample Selection Phase**
   - `/app/api/v1/endpoints/sample_selection.py` - Sample selection

4. **Data Profiling Phase**
   - `/app/services/data_profiling_service.py` - LLM rule generation (already partially migrated)

5. **Other Services**
   - `/app/services/test_execution_service.py`
   - `/app/services/streaming_profiler_service.py`

## Migration Strategy

### 1. Standard Celery Task Pattern
```python
# In task file (e.g., app/tasks/phase_tasks.py)
@celery_app.task(bind=True, max_retries=3)
def long_running_task(self, job_id: str, **kwargs):
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            _async_task_implementation(job_id, **kwargs)
        )
        loop.close()
        return result
    except Exception as exc:
        logger.error(f"Task failed: {str(exc)}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

async def _async_task_implementation(job_id: str, **kwargs):
    async with AsyncSessionLocal() as db:
        try:
            # Update job status
            job_manager.update_job_progress(job_id, status="running", ...)
            
            # Do the actual work
            result = await perform_work(db, **kwargs)
            
            # Update completion
            job_manager.update_job_progress(job_id, status="completed", ...)
            return result
            
        except Exception as e:
            job_manager.update_job_progress(job_id, status="failed", error=str(e))
            raise
```

### 2. Endpoint Pattern
```python
# In endpoint file
from app.tasks.phase_tasks import long_running_task

@router.post("/trigger-long-task")
async def trigger_task(...):
    # Create job
    job_id = job_manager.create_job("task_type", metadata)
    
    # Queue Celery task
    try:
        task = long_running_task.delay(job_id=job_id, **params)
        logger.info(f"Queued task {task.id} with job {job_id}")
    except Exception as e:
        # Fallback to async task if Celery not available
        logger.warning(f"Celery not available: {e}")
        from app.tasks.phase_tasks import _async_task_implementation
        asyncio.create_task(_async_task_implementation(job_id, **params))
    
    return {"job_id": job_id, "status": "queued"}
```

## Tasks to Create/Update

### 1. Planning Tasks ✅ (Created)
- [x] `regenerate_pde_mappings_task` - For PDE mapping regeneration
- [x] `generate_llm_attributes_task` - For LLM attribute generation

### 2. Scoping Tasks 
- [ ] Create `/app/tasks/scoping_tasks.py`
- [ ] `generate_scoping_recommendations_task` - For LLM scoping recommendations

### 3. Sample Selection Tasks (Already exists)
- [ ] Update to ensure consistent pattern

### 4. Data Profiling Tasks ✅ (Already migrated)
- [x] `generate_profiling_rules_task` - Already implemented

## Implementation Steps

1. **Update Planning Endpoints**
   - Modify `regenerate_all_pde_mappings` to use `regenerate_pde_mappings_task`
   - Update `generate_attributes_with_llm` to use `generate_llm_attributes_task`

2. **Create Scoping Tasks**
   - Create `scoping_tasks.py` with Celery tasks
   - Update scoping endpoints to use tasks

3. **Update Sample Selection**
   - Ensure consistent pattern in existing tasks

4. **Update Data Profiling Service**
   - Already partially done, ensure fallback pattern is consistent

5. **Test Each Phase**
   - Verify job creation and progress tracking
   - Test with and without Celery/Redis
   - Ensure proper error handling

## Benefits
1. **No more hanging UI** - All LLM calls run in separate processes
2. **Better scalability** - Can add more workers as needed
3. **Consistent pattern** - Same approach across all phases
4. **Reliable retries** - Built-in exponential backoff
5. **Better monitoring** - Can use Celery Flower for task monitoring

## Testing Strategy
1. Test with Redis/Celery running (production mode)
2. Test fallback when Redis is not available (development mode)
3. Verify job status updates work correctly
4. Test task retries on failure
5. Verify database session management in tasks