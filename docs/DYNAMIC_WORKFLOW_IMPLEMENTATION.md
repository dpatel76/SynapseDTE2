# Dynamic Workflow Implementation Guide

## Overview

This implementation transforms the workflow system to use Temporal activities for ALL workflow activities, providing maximum flexibility, consistency, and visibility.

## Key Changes

### 1. Activity Handler Framework (`app/temporal/activities/activity_handler.py`)
- **BaseActivityHandler**: Abstract base class for all activity handlers
- **ActivityHandlerRegistry**: Central registry for activity handlers
- **Dependency Management**: Built-in support for activity dependencies
- **Parallel Execution**: Support for parallel execution paths

### 2. Dynamic Activity Execution (`app/temporal/activities/dynamic_activities.py`)
- **execute_workflow_activity**: Generic activity executor that delegates to handlers
- **get_activities_for_phase_activity**: Retrieves activities from database templates
- **check_manual_activity_completed_activity**: Monitors manual activity completion
- **get_parallel_instances_activity**: Gets instances for parallel execution

### 3. Enhanced Workflow V2 (`app/temporal/workflows/enhanced_test_cycle_workflow_v2.py`)
- Uses dynamic activity loading
- Respects sequential dependencies:
  - Planning → Data Profiling → Scoping → Sample Selection (sequential)
  - Data Owner ID after Sample Selection
  - Finalize Report only after ALL observations complete
- Supports parallel execution:
  - Request for Information (parallel by data owner)
  - Test Execution (parallel by document)
  - Observation Management (parallel by test execution)

### 4. Database Enhancements
- Added fields to `workflow_activity_templates`:
  - `handler_name`: Handler class to use
  - `timeout_seconds`: Activity timeout
  - `retry_policy`: Custom retry configuration
  - `conditional_expression`: Activity conditions
  - `execution_mode`: sequential/parallel
- Added fields to `workflow_activities`:
  - `instance_id`: For parallel instances
  - `parent_activity_id`: Activity hierarchy
  - `retry_count`: Retry tracking
  - `last_error`: Error details

## Usage

### 1. Run Database Migrations
```bash
alembic upgrade head
```

### 2. Populate Activity Templates
```bash
python scripts/populate_dynamic_activity_templates.py
```

### 3. Start the Enhanced Worker
```bash
python app/temporal/worker_v2.py
```

### 4. Start Workflows with V2
```python
# In workflow service
metadata = {
    "use_v2_workflow": True,  # Enable V2 workflow
    "include_optional": False  # Skip optional activities
}
```

## Adding New Activities

### 1. Create Activity Handler
```python
class MyCustomHandler(BaseActivityHandler):
    async def can_execute(self, context: ActivityContext) -> bool:
        # Check dependencies
        return True
    
    async def execute(self, context: ActivityContext) -> ActivityResult:
        # Execute activity logic
        return ActivityResult(success=True, data={})
    
    async def compensate(self, context: ActivityContext, result: ActivityResult):
        # Rollback logic if needed
        pass
    
    def get_dependencies(self) -> List[ActivityDependency]:
        return []  # Define dependencies

# Register handler
ActivityHandlerRegistry.register("MyPhase", "my_activity", MyCustomHandler)
```

### 2. Add to Database
```sql
INSERT INTO workflow_activity_templates (
    phase_name, activity_name, activity_type, 
    activity_order, handler_name, timeout_seconds
) VALUES (
    'MyPhase', 'My Custom Activity', 'task',
    3, 'MyCustomHandler', 300
);
```

## Benefits

1. **Flexibility**: Add/remove activities without code changes
2. **Visibility**: All activities tracked in Temporal UI
3. **Consistency**: Unified retry/timeout handling
4. **Scalability**: Easy to scale specific activity types
5. **Maintainability**: Clear separation of concerns
6. **Testing**: Activities can be tested in isolation

## Migration Notes

- The system maintains backward compatibility with existing workflows
- Use `use_v2_workflow: false` to use legacy workflow
- Existing activities continue to work
- Can migrate phases incrementally

## Monitoring

### Check Activity Status
```python
# Query workflow activities
activities = await db.execute(
    select(WorkflowActivity)
    .where(
        WorkflowActivity.cycle_id == cycle_id,
        WorkflowActivity.status == ActivityStatus.IN_PROGRESS
    )
)
```

### Complete Manual Activities
```python
# Mark manual activity as complete
activity.status = ActivityStatus.COMPLETED
activity.completed_at = datetime.utcnow()
activity.completed_by = user_id
await db.commit()
```

## Testing

Run the test script to verify the implementation:
```bash
python scripts/test_dynamic_workflow.py
```

This will:
1. Create test data
2. Start a workflow with dynamic activities
3. Simulate manual activity completion
4. Monitor progress
5. Show final status

## Troubleshooting

### Activities Not Executing
- Check activity templates are populated
- Verify handler is registered
- Check dependencies are met
- Review Temporal UI for errors

### Manual Activities Stuck
- Ensure manual completion is triggered
- Check timeout settings
- Verify user has permission

### Parallel Execution Issues
- Check instance generation logic
- Verify parallel configuration
- Review dependency settings