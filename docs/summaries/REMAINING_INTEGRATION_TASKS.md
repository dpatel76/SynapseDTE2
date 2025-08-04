# Remaining Integration Tasks

## Clean Architecture Migration - Incomplete Items

### 1. API Endpoints Still Using Non-Clean Versions
Based on `app/api/v1/api.py`:
- ❌ `lobs` - Model compatibility issues
- ❌ `planning` - Not all endpoints migrated
- ❌ `scoping` - Not all endpoints migrated
- ❌ `sample_selection` - Model issues to resolve
- ❌ `admin_rbac` - Import issues

### 2. Missing Clean Architecture Components
- ❌ Planning use cases need completion
- ❌ Scoping use cases need completion
- ❌ Sample selection repository implementation
- ❌ LOB repository implementation

## Temporal Workflow Integration - Remaining Tasks

### 1. Infrastructure Setup
- ❌ Temporal server deployment configuration
- ❌ Worker deployment and scaling
- ❌ Temporal client initialization in app startup
- ❌ Connection pooling for Temporal client

### 2. Missing Implementation
- ❌ `app/temporal/client.py` - Get temporal client function
- ❌ Worker process to run activities
- ❌ Workflow registration and deployment
- ❌ Activity retry configuration

### 3. Permission Integration
In `temporal_signals.py`:
- ❌ TODO: Implement permission checking (line 104)
- ❌ TODO: Check actual permissions (line 224)

### 4. UI Updates Required
- ❌ Update Planning page to use new components
- ❌ Update Scoping page to use new components
- ❌ Update Sample Selection page
- ❌ Update Data Provider page
- ❌ Update Request Info page
- ❌ Update Test Execution page
- ❌ Update Observations page
- ❌ Update Test Report page
- ❌ Add workflow start functionality to Cycle Detail page

### 5. Database Migrations
- ❌ Verify workflow tracking tables are created
- ❌ Add indexes for workflow queries
- ❌ Add workflow_id to test_cycle table

### 6. Testing Infrastructure
- ❌ Unit tests for reconciled activities
- ❌ Integration tests for workflows
- ❌ E2E tests with Temporal
- ❌ Mock Temporal client for testing

### 7. Monitoring & Observability
- ❌ Temporal workflow metrics
- ❌ Activity execution logging
- ❌ Workflow failure alerts
- ❌ Performance monitoring

### 8. Documentation
- ❌ Deployment guide for Temporal
- ❌ Developer guide for adding new activities
- ❌ Troubleshooting guide
- ❌ API documentation for signals

## Priority Order

### Phase 1: Core Infrastructure (High Priority)
1. Implement `get_temporal_client()` function
2. Set up Temporal worker
3. Deploy Temporal server (Docker)
4. Initialize client in app startup

### Phase 2: Complete Clean Architecture (Medium Priority)
1. Migrate planning endpoints
2. Migrate scoping endpoints
3. Fix model compatibility issues
4. Complete repository implementations

### Phase 3: UI Integration (Medium Priority)
1. Update phase pages with new components
2. Add workflow start functionality
3. Implement signal sending from UI
4. Add workflow status polling

### Phase 4: Production Readiness (Lower Priority)
1. Add comprehensive testing
2. Set up monitoring
3. Create documentation
4. Performance optimization

## Quick Start Commands

### Start Temporal Server
```bash
docker-compose -f docker-compose.temporal.yml up -d
```

### Run Temporal Worker
```bash
python app/temporal/worker.py
```

### Test Workflow
```bash
python test_temporal_workflow.py
```

## Estimated Effort

- **Infrastructure Setup**: 2-3 days
- **Clean Architecture Completion**: 3-4 days
- **UI Updates**: 2-3 days
- **Testing & Documentation**: 2-3 days

**Total**: ~10-13 days for complete integration

## Next Immediate Steps

1. **Create Temporal Client**:
```python
# app/temporal/client.py
from temporalio.client import Client

async def get_temporal_client():
    return await Client.connect("localhost:7233")
```

2. **Start Worker Process**:
```python
# app/temporal/worker.py
from temporalio.worker import Worker
from app.temporal.workflows.test_cycle_workflow_reconciled import TestCycleWorkflowReconciled
# Import all activities...

async def main():
    client = await get_temporal_client()
    worker = Worker(
        client,
        task_queue="test-cycle-queue",
        workflows=[TestCycleWorkflowReconciled],
        activities=[...all_activities...]
    )
    await worker.run()
```

3. **Update App Startup**:
```python
# app/main.py
from app.temporal.client import get_temporal_client

@app.on_event("startup")
async def startup_event():
    app.state.temporal_client = await get_temporal_client()
```