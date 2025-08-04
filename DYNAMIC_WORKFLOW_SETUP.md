# Dynamic Workflow System Setup Guide

## Quick Start

### 1. Environment Configuration

Copy the example environment file and configure it:
```bash
cp .env.example .env
```

Edit `.env` and ensure these settings are configured:
```bash
# Enable dynamic workflows
USE_DYNAMIC_WORKFLOWS=true
WORKFLOW_VERSION="v2"
TEMPORAL_WORKER_ENABLED=true

# Optional: Customize behavior
DYNAMIC_ACTIVITY_RETRY_ENABLED=true
DYNAMIC_ACTIVITY_TIMEOUT_ENABLED=true
PARALLEL_ACTIVITY_MAX_CONCURRENT=10
```

### 2. Verify Configuration

Run the configuration checker:
```bash
python -m scripts.check_dynamic_workflow_config
```

You should see:
- ✅ Dynamic workflows are ENABLED
- ✅ V2 workflow will be used by default
- ✅ 49 activity templates configured
- ✅ 14 parallel activities

### 3. Start the Worker

The dynamic workflow system requires the V2 worker to be running:

```bash
# Start the V2 worker with dynamic activity support
python -m app.temporal.worker_v2
```

## Configuration Options

### Core Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `USE_DYNAMIC_WORKFLOWS` | `true` | Enable/disable dynamic workflow system |
| `WORKFLOW_VERSION` | `"v2"` | Workflow version to use (v1=legacy, v2=dynamic) |
| `TEMPORAL_WORKER_ENABLED` | `false` | Enable workflow processing (set to true!) |

### Dynamic Activity Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `DYNAMIC_ACTIVITY_RETRY_ENABLED` | `true` | Use retry policies from database |
| `DYNAMIC_ACTIVITY_TIMEOUT_ENABLED` | `true` | Use timeouts from database |
| `PARALLEL_ACTIVITY_MAX_CONCURRENT` | `10` | Max concurrent parallel activities |
| `WORKFLOW_ACTIVITY_SIGNAL_TIMEOUT` | `300` | Timeout for activity signals (seconds) |

### Handler Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `ACTIVITY_HANDLER_PACKAGE` | `"app.temporal.activities.handlers"` | Package containing handlers |
| `FALLBACK_HANDLER` | `"AutomatedActivityHandler"` | Default handler for automated activities |
| `MANUAL_ACTIVITY_HANDLER` | `"ManualActivityHandler"` | Handler for manual activities |

### Feature Flags

| Setting | Default | Description |
|---------|---------|-------------|
| `ENABLE_ACTIVITY_DEPENDENCIES` | `true` | Check dependencies before execution |
| `ENABLE_CONDITIONAL_ACTIVITIES` | `true` | Support conditional expressions |
| `ENABLE_ACTIVITY_COMPENSATION` | `true` | Enable compensation on failure |
| `TRACK_ACTIVITY_METRICS` | `true` | Track execution metrics |

## Switching Between Workflow Versions

### Use Dynamic Workflows (Recommended)
```bash
USE_DYNAMIC_WORKFLOWS=true
WORKFLOW_VERSION="v2"
```

### Use Legacy Workflows
```bash
USE_DYNAMIC_WORKFLOWS=false
WORKFLOW_VERSION="v1"
```

### Per-Workflow Override
You can override the default behavior when starting a workflow:
```python
# Force V2 workflow
metadata = {"use_v2_workflow": True}

# Force legacy workflow
metadata = {"use_v2_workflow": False}
```

## Verifying the System

### 1. Check Database Setup
```bash
# Verify activity templates are populated
python -m scripts.check_dynamic_workflow_config
```

### 2. Test Workflow Execution
```python
# Start a test workflow
from app.services.workflow_service import WorkflowService

async def test_workflow():
    service = WorkflowService(db)
    result = await service.start_test_cycle_workflow(
        cycle_id=1,
        user_id=1,
        metadata={"test": True}
    )
    print(f"Started workflow: {result['workflow_id']}")
```

### 3. Monitor in Temporal UI
- Open http://localhost:8233
- Look for workflows with ID pattern: `test-cycle-*-v2`
- Activities should show handler names and retry policies

## Troubleshooting

### Dynamic workflows not being used?
1. Check `USE_DYNAMIC_WORKFLOWS=true` in .env
2. Check `WORKFLOW_VERSION="v2"` in .env
3. Restart the application after config changes

### Activities not found?
1. Run `python -m scripts.populate_dynamic_activity_templates`
2. Verify with `python -m scripts.check_dynamic_workflow_config`

### Worker not processing?
1. Check `TEMPORAL_WORKER_ENABLED=true` in .env
2. Ensure worker_v2 is running: `python -m app.temporal.worker_v2`
3. Check worker logs for connection errors

### Parallel activities not working?
1. Check `execution_mode='parallel'` in activity templates
2. Verify `PARALLEL_ACTIVITY_MAX_CONCURRENT` is set
3. Check activity dependencies are configured correctly

## Next Steps

1. **Monitor Performance**: Track activity execution times in Temporal UI
2. **Customize Handlers**: Create custom handlers for specific activities
3. **Adjust Timeouts**: Fine-tune timeouts based on actual execution times
4. **Configure Retries**: Adjust retry policies for critical activities
5. **Add New Activities**: Simply insert into `workflow_activity_templates` table