# Temporal Versioning Integration - Quick Start Guide

## Overview

This guide helps you implement Temporal-integrated versioning, starting with the Planning phase as a proof of concept.

## Step 1: Run Database Migration

```bash
# Run the migration to add Temporal fields
alembic upgrade temporal_versioning_001
```

## Step 2: Create Base Versioning Service

```python
# app/services/temporal_versioning_service.py
from typing import Dict, Any, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.versioning import VersionedMixin
from app.models.workflow_tracking import WorkflowStep

class TemporalVersioningService:
    """Versioning service with Temporal integration"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_version_with_workflow_context(
        self,
        model_class: type,
        data: Dict[str, Any],
        workflow_context: Dict[str, Any]
    ) -> UUID:
        """Create version linked to workflow execution"""
        
        # Create the version
        version = model_class(
            **data,
            workflow_execution_id=workflow_context.get("workflow_execution_id"),
            workflow_step_id=workflow_context.get("workflow_step_id")
        )
        
        self.db.add(version)
        await self.db.commit()
        
        return version.version_id
```

## Step 3: Create Planning Phase Activities

```python
# app/workflows/activities/planning_activities.py
from temporalio import activity
from app.services.temporal_versioning_service import TemporalVersioningService
from app.models.planning import PlanningPhaseVersion, AttributeDecision

class PlanningActivities:
    """Planning phase activities with versioning"""
    
    @activity.defn
    async def create_planning_version(
        self,
        cycle_id: int,
        report_id: int,
        user_id: int,
        attributes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create planning phase version"""
        async with get_db() as db:
            # Get workflow context
            info = activity.info()
            workflow_context = {
                "workflow_execution_id": info.workflow_id,
                "workflow_run_id": info.workflow_run_id,
                "activity_name": info.activity_type
            }
            
            # Create version
            service = TemporalVersioningService(db)
            version = PlanningPhaseVersion(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_name="Planning",
                version_status="draft",
                created_by_id=user_id,
                workflow_execution_id=workflow_context["workflow_execution_id"]
            )
            
            db.add(version)
            await db.flush()
            
            # Create attribute decisions
            for attr in attributes:
                decision = AttributeDecision(
                    planning_version_id=version.version_id,
                    attribute_id=attr["attribute_id"],
                    attribute_data=attr["data"],
                    decision_type="include",
                    decision_reason="Initial selection"
                )
                db.add(decision)
            
            await db.commit()
            
            return {
                "version_id": str(version.version_id),
                "attribute_count": len(attributes),
                "status": "created"
            }
```

## Step 4: Update Workflow to Use Versioning

```python
# In your existing workflow
class EnhancedTestCycleWorkflow:
    
    async def run_planning_phase(self):
        """Run planning phase with versioning"""
        
        # Get attributes from existing logic
        attributes = await self.get_planning_attributes()
        
        # Create version through activity
        version_result = await workflow.execute_activity(
            PlanningActivities.create_planning_version,
            self.cycle_id,
            self.report_id,
            self.user_id,
            attributes,
            start_to_close_timeout=timedelta(minutes=5)
        )
        
        self.planning_version_id = version_result["version_id"]
        
        # Since Planning is auto-approved by tester, approve immediately
        await workflow.execute_activity(
            PlanningActivities.approve_planning_version,
            self.planning_version_id,
            self.user_id,
            "Auto-approved by tester",
            start_to_close_timeout=timedelta(minutes=2)
        )
```

## Step 5: Add Workflow Queries

```python
# Add to your workflow class
@workflow.query
def get_phase_versions(self) -> Dict[str, str]:
    """Get all phase versions"""
    return {
        "Planning": self.planning_version_id,
        "Sample Selection": self.sample_selection_version_id,
        # ... other phases
    }

@workflow.query
def get_pending_approvals(self) -> List[Dict[str, Any]]:
    """Get pending version approvals"""
    pending = []
    for phase, approval in self.pending_approvals.items():
        if approval["status"] == "pending":
            pending.append({
                "phase": phase,
                "version_id": approval["version_id"],
                "created_at": approval["created_at"]
            })
    return pending
```

## Step 6: Test the Integration

```python
# Test script
async def test_planning_versioning():
    # Start workflow
    client = await get_temporal_client()
    
    workflow_id = f"test-cycle-{cycle_id}-planning-test"
    handle = await client.start_workflow(
        EnhancedTestCycleWorkflow.run,
        TestCycleWorkflowInput(
            cycle_id=cycle_id,
            report_id=report_id,
            user_id=user_id
        ),
        id=workflow_id,
        task_queue="test-queue"
    )
    
    # Wait for planning phase
    await asyncio.sleep(5)
    
    # Query versions
    versions = await handle.query("get_phase_versions")
    print(f"Planning version: {versions.get('Planning')}")
    
    # Check database
    async with get_db() as db:
        version = await db.get(PlanningPhaseVersion, versions["Planning"])
        print(f"Version status: {version.version_status}")
        print(f"Workflow ID: {version.workflow_execution_id}")
```

## Common Issues and Solutions

### Issue 1: Activities not found
**Solution**: Register activities with worker
```python
worker = Worker(
    client,
    task_queue="test-queue",
    workflows=[EnhancedTestCycleWorkflow],
    activities=[
        PlanningActivities.create_planning_version,
        PlanningActivities.approve_planning_version
    ]
)
```

### Issue 2: Database connection in activities
**Solution**: Use async context manager
```python
async with get_db() as db:
    # Your database operations
```

### Issue 3: Workflow signals not received
**Solution**: Ensure signal is defined before workflow.run
```python
@workflow.defn
class MyWorkflow:
    @workflow.signal
    async def my_signal(self, data):
        # Handle signal
    
    @workflow.run
    async def run(self):
        # Workflow logic
```

## Next Steps

1. **Validate Planning phase** implementation
2. **Move to Sample Selection** - more complex with revisions
3. **Add UI integration** for version display
4. **Implement approval signals** for phases needing approval
5. **Add monitoring** for version operations

## Monitoring Versioning Operations

```sql
-- Check versions created by workflows
SELECT 
    vp.version_id,
    vp.cycle_id,
    vp.report_id,
    vp.version_status,
    vp.workflow_execution_id,
    we.status as workflow_status
FROM planning_phase_versions vp
JOIN workflow_executions we ON vp.workflow_execution_id = we.workflow_id
WHERE vp.created_at > NOW() - INTERVAL '1 day';

-- Check version operations
SELECT 
    operation_type,
    phase_name,
    success,
    COUNT(*) as count
FROM workflow_version_operations
WHERE initiated_at > NOW() - INTERVAL '1 day'
GROUP BY operation_type, phase_name, success;
```

This quick start guide gives you a working example to validate the approach before implementing across all phases.