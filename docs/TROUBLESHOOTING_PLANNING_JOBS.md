# Troubleshooting Planning Jobs: Lessons Learned

## Overview
This document captures critical learnings from troubleshooting issues with PDE mapping and classification jobs in the Planning phase. These issues took significant time to diagnose and fix, so documenting them will help prevent similar problems in the future.

## Issues Encountered and Solutions

### 1. Classification Data Not Being Saved to Database

**Problem**: 
- PDE classification data (information_security_classification, risk_level, regulatory_flag, pii_flag) was being returned by the LLM but not saved to the database
- SQL UPDATE statements were missing classification fields despite the code appearing to set them

**Root Causes**:
1. **SQLAlchemy Session Management**: Objects loaded outside an async task were not properly tracked when modified inside the task
2. **Detached Objects**: The `existing_mappings` were loaded in the main function but used in the async task, causing them to be detached from the session

**Solution**:
```python
# ❌ Wrong: Loading mappings outside async task
existing_mappings = await db.execute(query)  # In main function
async def run_regeneration():
    # existing_mappings used here are detached
    
# ✅ Correct: Reload mappings inside async task
async def run_regeneration():
    async with AsyncSessionLocal() as task_db:
        # Reload mappings in the async context
        existing_mappings_query = select(PlanningPDEMapping).where(
            PlanningPDEMapping.phase_id == phase.phase_id
        )
        existing_mappings_result = await task_db.execute(existing_mappings_query)
        existing_mappings = list(existing_mappings_result.scalars().all())
```

**Key Learning**: Always load database objects within the same session context where they will be modified.

### 2. Job Status Stuck on "Pending"

**Problem**:
- Background jobs showed "pending" status even when actively running
- Users couldn't tell if jobs were actually processing

**Root Cause**:
- Job status was never updated to "in_progress" when the async task started

**Solution**:
```python
# ✅ Add status update at the beginning of async task
async def run_regeneration():
    job_manager.update_job_progress(
        job_id,
        status="running",  # This was missing
        current_step="Starting regeneration",
        progress_percentage=0
    )
```

**Key Learning**: Always update job status to "running" as the first action in a background task.

### 3. AttributeError: 'BackgroundJobManager' object has no attribute 'update_job_status'

**Problem**:
- Code was calling `job_manager.update_job_status()` which doesn't exist
- Jobs were failing immediately with AttributeError

**Root Cause**:
- Incorrect method name - the actual method is `update_job_progress()` with a status parameter

**Solution**:
```python
# ❌ Wrong
job_manager.update_job_status(job_id, "in_progress")

# ✅ Correct
job_manager.update_job_progress(
    job_id,
    status="running",
    current_step="Starting",
    progress_percentage=0
)
```

**Key Learning**: Always verify the actual API of services/managers before using them.

### 4. Missing updated_at Timestamps

**Problem**:
- Records were being modified but `updated_at` timestamps weren't always being set
- Made it difficult to track when changes occurred

**Solution**:
```python
# ✅ Always set updated_at when modifying records
existing.information_security_classification = new_value
existing.updated_at = datetime.utcnow()
existing.updated_by_id = current_user.user_id
```

**Key Learning**: Even with database triggers (onupdate), explicitly set `updated_at` for clarity and reliability.

### 5. Frontend Not Calling Backend Endpoint

**Problem**:
- Frontend was attempting to call regeneration endpoint but no requests were appearing in logs
- Job IDs from different attempts were appearing

**Root Cause**:
- Initial suspicion was URL mismatch, but the actual issue was the backend failing before logging

**Solution**:
- Added extensive logging at the beginning of endpoints
- Added debug logging in frontend to trace API calls

**Key Learning**: Add logging as the very first line in API endpoints to confirm they're being reached.

## Best Practices Established

### 1. Database Session Management in Async Tasks

```python
async def background_task():
    # Always create a new session for background tasks
    async with AsyncSessionLocal() as task_db:
        # Load all needed data within this session
        data = await task_db.execute(query)
        
        # Modify and save within same session
        for item in data:
            item.field = new_value
            task_db.add(item)  # Ensure tracking
        
        await task_db.commit()
```

### 2. Job Progress Management Pattern

```python
def create_background_job():
    job_id = job_manager.create_job("job_type", metadata={})
    
    async def run_job():
        try:
            # First action: Update status to running
            job_manager.update_job_progress(
                job_id,
                status="running",
                current_step="Initializing",
                progress_percentage=0
            )
            
            # Do work with progress updates
            for i, item in enumerate(items):
                # Process item
                
                # Update progress
                progress = int((i + 1) / len(items) * 100)
                job_manager.update_job_progress(
                    job_id,
                    current_step=f"Processing item {i+1}",
                    progress_percentage=progress
                )
            
            # Complete job
            job_manager.complete_job(job_id)
            
        except Exception as e:
            logger.error(f"Job failed: {e}", exc_info=True)
            job_manager.complete_job(job_id, error=str(e))
    
    # Start async task
    task = asyncio.create_task(run_job())
    return {"job_id": job_id}
```

### 3. Debugging Checklist for Background Jobs

1. **Check Logs Chronologically**:
   ```bash
   tail -f backend_logs.txt | grep -E "(job_id|ERROR|Exception)"
   ```

2. **Verify Endpoint is Called**:
   ```bash
   tail -f backend_logs.txt | grep "POST.*endpoint-path"
   ```

3. **Check Job Status**:
   ```bash
   curl http://localhost:8000/api/v1/jobs/{job_id}/status
   ```

4. **Monitor SQL Statements**:
   ```bash
   tail -f backend_logs.txt | grep -A5 "UPDATE.*table_name"
   ```

### 4. Common Pitfalls to Avoid

1. **Don't Share Sessions Across Async Boundaries**
   - Always create new sessions in async tasks
   - Don't pass SQLAlchemy objects between different sessions

2. **Don't Assume Object Changes Are Tracked**
   - Explicitly call `session.add()` after modifying objects
   - Use `session.flush()` to see SQL before commit when debugging

3. **Don't Forget Progress Updates**
   - Update job status to "running" immediately
   - Provide regular progress updates for long-running tasks
   - Always complete or fail jobs explicitly

4. **Don't Skip Logging**
   - Log at the start of every endpoint
   - Log before and after critical operations
   - Include relevant IDs and data in log messages

### 5. Testing Background Jobs

```python
# Test script to verify job execution
async def test_regeneration():
    # Create a job
    response = await client.post(
        f"/api/v1/planning/cycles/{cycle_id}/reports/{report_id}/pde-mappings/regenerate-all"
    )
    job_id = response.json()["job_id"]
    
    # Poll for completion
    while True:
        status = await client.get(f"/api/v1/jobs/{job_id}/status")
        job_data = status.json()
        
        print(f"Status: {job_data['status']}, Progress: {job_data['progress_percentage']}%")
        
        if job_data['status'] in ['completed', 'failed']:
            break
            
        await asyncio.sleep(2)
    
    # Verify data was updated
    mappings = await db.execute(
        select(PlanningPDEMapping).where(
            PlanningPDEMapping.information_security_classification.isnot(None)
        )
    )
    assert len(list(mappings)) > 0, "No classifications were saved"
```

## Summary of Time-Consuming Issues

1. **SQLAlchemy Session Issues** (2+ hours)
   - Symptoms: Data appears to be set but UPDATE statements don't include the fields
   - Fix: Reload objects in the async task's session

2. **Job Status Not Updating** (1 hour)
   - Symptoms: Jobs show "pending" even when running
   - Fix: Add status="running" to update_job_progress calls

3. **Wrong Method Name** (30 minutes)
   - Symptoms: AttributeError immediately on job start
   - Fix: Use update_job_progress instead of update_job_status

4. **Missing Timestamps** (30 minutes)
   - Symptoms: Can't tell when records were last modified
   - Fix: Explicitly set updated_at on all modifications

## Monitoring and Debugging Commands

```bash
# Monitor job execution in real-time
tail -f backend_logs.txt | grep -E "(job_id|status|progress|ERROR)"

# Check for classification updates
tail -f backend_logs.txt | grep -E "(classification|risk_level|regulatory_flag)"

# Monitor SQL updates
tail -f backend_logs.txt | grep -A5 "UPDATE.*pde_mappings"

# Check specific job status
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/jobs/{job_id}/status

# Verify data in database
python check_pde_classifications.py
```

## Conclusion

The main lessons learned:
1. **Session management is critical** in async tasks - always reload data in the task's session
2. **Logging is essential** - add it early and extensively
3. **Test the full flow** - from API call to database update
4. **Monitor SQL statements** - they reveal what's actually happening
5. **Update job status immediately** - users need feedback that work is happening

These issues could have been caught earlier with:
- Better error messages in the job manager
- More extensive logging from the start
- Unit tests for async background tasks
- Integration tests for the full job flow