# Temporal Workflow Integration Guide

## Overview

The SynapseDT application now includes Temporal workflow orchestration for managing the 8-phase test cycle process. This integration provides:

- **Reliable workflow execution** with automatic retries and compensation
- **Parallel phase execution** for improved performance
- **Comprehensive tracking** of workflow steps and timing
- **Version management** for workflow evolution
- **Real-time monitoring** and visualization

## Architecture

### Workflow Structure

The test cycle workflow consists of 8 phases:
1. **Planning** - Generate test attributes using LLM
2. **Scoping** - Define testing scope and get approvals
3. **Sample Selection** - Select test samples (runs in parallel with phase 4)
4. **Data Owner Identification** - Identify data owners (runs in parallel with phase 3)
5. **Request for Information** - Send RFIs to data owners
6. **Test Execution** - Execute test cases
7. **Observation Management** - Manage and track observations
8. **Finalize Test Report** - Generate final test report

### Key Components

1. **Workflow Definitions** (`app/temporal/workflows/`)
   - `EnhancedTestCycleWorkflow` - Main workflow with tracking and compensation

2. **Activities** (`app/temporal/activities/`)
   - Phase-specific activities for each workflow phase
   - Tracking activities for metrics and analytics
   - Retry and compensation logic

3. **Services** (`app/services/`)
   - `WorkflowService` - Manages workflow lifecycle
   - `WorkflowMetricsService` - Provides analytics and insights

4. **API Endpoints** (`app/api/v1/endpoints/`)
   - `/workflow/*` - Workflow management
   - `/workflow-metrics/*` - Metrics and monitoring
   - `/workflow-versions/*` - Version management
   - `/workflow-compensation/*` - Compensation logs

5. **UI Components** (`frontend/src/`)
   - `WorkflowVisualization` - Real-time workflow progress
   - `WorkflowMonitoringDashboard` - Analytics dashboard

## Setup and Configuration

### Prerequisites

1. **Docker** - Required for Temporal server
2. **PostgreSQL** - Application database
3. **Python 3.8+** - Backend runtime
4. **Node.js 14+** - Frontend runtime

### Starting Services

Use the integrated startup script:

```bash
# Make scripts executable
chmod +x start_all_services.sh stop_all_services.sh

# Start all services (PostgreSQL, Temporal, Backend, Frontend)
./start_all_services.sh

# Stop all services
./stop_all_services.sh
```

### Environment Configuration

Add these to your `.env` file:

```env
# Temporal Configuration
TEMPORAL_HOST=localhost:7233
TEMPORAL_NAMESPACE=default
TEMPORAL_TASK_QUEUE=synapse-workflow-queue
TEMPORAL_WORKER_ENABLED=false  # Set to true to enable worker
TEMPORAL_ACTIVITY_TIMEOUT=300
TEMPORAL_WORKFLOW_TIMEOUT=86400
```

### Running Database Migrations

The workflow integration includes new database tables:

```bash
# Apply workflow-related migrations
alembic upgrade head
```

New tables added:
- `workflow_execution` - Tracks workflow instances
- `workflow_step` - Detailed step tracking
- `workflow_transition` - Phase transitions
- `workflow_metrics` - Performance metrics
- `workflow_alert` - System alerts
- `workflow_migration_history` - Version migrations
- `workflow_compensation_log` - Compensation actions
- `workflow_activity_retry_log` - Retry tracking

## Usage

### Starting a Workflow (UI)

1. Navigate to a Test Cycle detail page
2. Click "Start Workflow" button (Test Manager only)
3. Monitor progress in real-time

### Starting a Workflow (API)

```bash
# Start workflow for a test cycle
curl -X POST "http://localhost:8000/api/v1/workflow/start/123" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "report_ids": [1, 2, 3],
    "skip_phases": []
  }'
```

### Monitoring Workflows

1. **Workflow Visualization** - Available on Cycle Detail page
2. **Monitoring Dashboard** - Navigate to `/workflow-monitoring`
3. **Temporal UI** - http://localhost:8080

## Key Features

### 1. Parallel Execution
- Phases 3 (Sample Selection) and 4 (Data Owner ID) run in parallel
- Automatic synchronization before phase 5

### 2. Retry Policies
Different retry strategies per activity type:
- **LLM requests**: 3 attempts, exponential backoff
- **Database operations**: 3 attempts, linear backoff
- **Email notifications**: 3 attempts, fixed delay

### 3. Compensation Logic
Phase-specific compensation strategies:
- **Rollback**: Undo completed actions
- **Notify**: Alert relevant users
- **Skip**: Continue with manual intervention
- **Partial Rollback**: Preserve successful work

### 4. Version Management
- Workflow versioning with migration support
- Feature compatibility checking
- Safe upgrades for running workflows

### 5. Comprehensive Tracking
- Step-by-step execution tracking
- Timing metrics for each phase
- Bottleneck analysis
- Trend tracking over time

## Troubleshooting

### Import Errors

If you encounter import errors when starting the worker:

1. Ensure all models are properly exported in `app/models/__init__.py`
2. Check that activity imports match actual function names
3. Verify database models exist for referenced entities

### Temporal Connection Issues

1. Ensure Docker is running
2. Check Temporal container: `docker ps | grep temporal`
3. Verify port 7233 is accessible
4. Check logs: `docker logs temporal`

### Worker Not Starting

1. Set `TEMPORAL_WORKER_ENABLED=true` in `.env`
2. Fix any import errors in `app/temporal/worker.py`
3. Check worker logs: `tail -f temporal_worker.log`

## Development Tips

### Adding New Activities

1. Create activity in appropriate file under `app/temporal/activities/`
2. Use `@activity.defn` decorator
3. Add retry policy using `@with_retry` decorator
4. Import in worker configuration

### Modifying Workflow

1. Update workflow definition in `app/temporal/workflows/`
2. Increment version in `WorkflowVersion` enum
3. Add migration strategy if needed
4. Test with existing and new workflows

### Testing Workflows

```python
# Example test
async def test_workflow():
    from temporalio.testing import WorkflowEnvironment
    from app.temporal.workflows.enhanced_test_cycle_workflow import EnhancedTestCycleWorkflow
    
    async with WorkflowEnvironment() as env:
        result = await env.client.execute_workflow(
            EnhancedTestCycleWorkflow.run,
            TestCycleWorkflowInput(...),
            id="test-workflow-1",
            task_queue="test-queue"
        )
        assert result["status"] == "completed"
```

## Important Notes

1. **Existing Workflows**: Current workflows continue to work without Temporal
2. **New Workflows Only**: Temporal is used only for new test cycles
3. **Manual Start**: Workflows must be manually initiated by Test Managers
4. **Worker Required**: The Temporal worker must be running to process workflows
5. **Database Consistency**: Workflow state is synchronized with main database

## Future Enhancements

1. **Automatic Workflow Start**: Trigger workflows based on cycle creation
2. **Dynamic Phase Configuration**: Allow custom phase definitions
3. **Advanced Scheduling**: Schedule workflows for future execution
4. **Integration with External Systems**: Connect to enterprise systems
5. **Enhanced Monitoring**: More detailed performance analytics

## Support

For issues or questions:
1. Check logs in `backend.log`, `temporal_worker.log`
2. Review Temporal UI at http://localhost:8080
3. Check database workflow tables for state information
4. Review this documentation for configuration details