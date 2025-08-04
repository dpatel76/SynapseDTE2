"""Test script for Temporal workflow integration

This script tests the enhanced test cycle workflow with comprehensive tracking.
"""

import asyncio
import logging
from datetime import datetime
from temporalio.client import Client
from temporalio.worker import Worker

from app.temporal.workflows.enhanced_test_cycle_workflow import EnhancedTestCycleWorkflow
from app.temporal.shared import TestCycleWorkflowInput
from app.temporal.shared.constants import TASK_QUEUE_WORKFLOW
from app.temporal.activities.tracking_activities import *
from app.temporal.activities.phase_activities import *
from app.temporal.activities.planning_activities import *
from app.temporal.activities.scoping_activities import *
from app.temporal.activities.sample_selection_activities import *
from app.temporal.activities.data_owner_activities import *
from app.temporal.activities.request_info_activities import *

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Main test function"""
    # Connect to Temporal server
    client = await Client.connect("localhost:7233")
    
    # Create worker with all activities
    activities = [
        # Tracking activities
        record_workflow_start_activity,
        record_workflow_complete_activity,
        record_step_start_activity,
        record_step_complete_activity,
        record_transition_activity,
        calculate_workflow_metrics_activity,
        # Phase activities
        start_phase_activity,
        complete_phase_activity,
        check_phase_dependencies_activity,
        # Planning activities
        start_planning_phase_activity,
        review_regulatory_requirements_activity,
        identify_initial_attributes_activity,
        create_test_plan_activity,
        complete_planning_phase_activity,
        execute_planning_activities,
        # Scoping activities
        start_scoping_phase_activity,
        enhance_attributes_with_llm_activity,
        determine_testing_approach_activity,
        create_scope_document_activity,
        complete_scoping_phase_activity,
        execute_scoping_activities,
        # Sample Selection activities
        start_sample_selection_phase_activity,
        define_selection_criteria_activity,
        generate_samples_activity,
        validate_sample_coverage_activity,
        complete_sample_selection_phase_activity,
        execute_sample_selection_activities,
        # Data Owner activities
        start_data_owner_identification_phase_activity,
        identify_lobs_from_samples_activity,
        identify_data_owners_for_lobs_activity,
        create_data_owner_assignments_activity,
        notify_data_owners_activity,
        complete_data_owner_identification_phase_activity,
        execute_data_owner_activities,
        # Request Info activities
        start_request_info_phase_activity,
        create_information_requests_activity,
        send_request_notifications_activity,
        monitor_request_responses_activity,
        complete_request_info_phase_activity,
        execute_request_info_activities
    ]
    
    async with Worker(
        client,
        task_queue=TASK_QUEUE_WORKFLOW,
        workflows=[EnhancedTestCycleWorkflow],
        activities=activities,
    ):
        # Create test input
        workflow_input = TestCycleWorkflowInput(
            cycle_id=1,
            report_ids=[1],
            initiated_by_user_id=1,
            auto_assign_testers=True,
            auto_generate_attributes=True,
            skip_phases=[],  # Run all phases
            metadata={
                "test_run": True,
                "test_timestamp": datetime.utcnow().isoformat()
            }
        )
        
        # Start workflow execution
        logger.info("Starting enhanced test cycle workflow...")
        handle = await client.start_workflow(
            EnhancedTestCycleWorkflow.run,
            workflow_input,
            id=f"test-cycle-{workflow_input.cycle_id}-{datetime.utcnow().timestamp()}",
            task_queue=TASK_QUEUE_WORKFLOW,
        )
        
        logger.info(f"Workflow started with ID: {handle.id}")
        
        # Wait for workflow to complete
        result = await handle.result()
        
        # Print results
        logger.info("Workflow completed successfully!")
        logger.info(f"Execution ID: {result['execution_id']}")
        logger.info(f"Status: {result['status']}")
        logger.info(f"Completed phases: {result['completed_phases']}")
        logger.info(f"Total duration: {result['total_duration']} seconds")
        
        # Print phase metrics
        logger.info("\nPhase Metrics:")
        for phase, duration in result['metrics']['phase_durations'].items():
            logger.info(f"  {phase}: {duration:.2f} seconds")
        
        # Print transition times
        logger.info("\nTransition Times:")
        for transition, time in result['metrics']['transition_times'].items():
            logger.info(f"  {transition}: {time:.2f} seconds")
        
        # Query workflow execution history for detailed tracking
        await query_workflow_tracking(client, result['execution_id'])


async def query_workflow_tracking(client: Client, execution_id: str):
    """Query workflow tracking data"""
    from app.core.database import get_db
    from app.models.workflow_tracking import WorkflowExecution, WorkflowStep, WorkflowMetrics
    from sqlalchemy import select
    
    logger.info("\n\nQuerying workflow tracking data...")
    
    async with get_db() as db:
        # Get workflow execution
        result = await db.execute(
            select(WorkflowExecution).where(
                WorkflowExecution.execution_id == execution_id
            )
        )
        execution = result.scalar_one_or_none()
        
        if execution:
            logger.info(f"\nWorkflow Execution:")
            logger.info(f"  Type: {execution.workflow_type}")
            logger.info(f"  Status: {execution.status}")
            logger.info(f"  Duration: {execution.duration_seconds:.2f} seconds")
            logger.info(f"  Started: {execution.started_at}")
            logger.info(f"  Completed: {execution.completed_at}")
            
            # Get steps
            steps_result = await db.execute(
                select(WorkflowStep).where(
                    WorkflowStep.execution_id == execution_id
                ).order_by(WorkflowStep.started_at)
            )
            steps = steps_result.scalars().all()
            
            logger.info(f"\nWorkflow Steps ({len(steps)} total):")
            for step in steps[:10]:  # Show first 10 steps
                logger.info(f"  - {step.step_name} ({step.step_type}): "
                          f"{step.status} - {step.duration_seconds:.2f}s")


if __name__ == "__main__":
    asyncio.run(main())