"""Temporal worker with dynamic activity support"""

import asyncio
import logging
from temporalio.client import Client
from temporalio.worker import Worker
from typing import Optional

from app.temporal.shared.constants import (
    TASK_QUEUE_WORKFLOW, TASK_QUEUE_LLM, 
    TASK_QUEUE_NOTIFICATION, TASK_QUEUE_REPORT
)
# Import workflows that comply with Temporal sandbox
from app.temporal.workflows.test_cycle_workflow import TestCycleWorkflow
from app.temporal.workflows.report_testing_workflow import ReportTestingWorkflow
from app.temporal.workflows.llm_analysis_workflow import LLMAnalysisWorkflow
from app.temporal.workflows.enhanced_test_cycle_workflow import EnhancedTestCycleWorkflow

# Import all activities
from app.temporal.activities import (
    # Legacy phase activities (for backward compatibility)
    start_phase_activity, complete_phase_activity,
    check_phase_dependencies_activity,
    # Test activities
    create_test_cases_activity, execute_test_activity,
    batch_execute_tests_activity, validate_test_results_activity,
    # Notification activities
    send_email_notification_activity, create_in_app_notification_activity,
    send_phase_completion_notification_activity,
    # LLM activities
    generate_test_attributes_activity, analyze_document_activity,
    recommend_tests_activity, analyze_patterns_activity
)

# Import new dynamic activities
from app.temporal.activities.dynamic_activities import (
    get_activities_for_phase_activity,
    execute_workflow_activity,
    check_manual_activity_completed_activity,
    get_parallel_instances_activity,
    check_phase_completion_dependencies_activity,
    create_workflow_activity_record_activity
)

# Import tracking activities
from app.temporal.activities.tracking_activities import (
    record_workflow_start_activity,
    record_workflow_complete_activity,
    record_step_start_activity,
    record_step_complete_activity,
    record_transition_activity,
    calculate_workflow_metrics_activity
)

# Import phase-specific activity handlers (ensures registration)
# NOTE: Commented out due to import errors - needs model fixes
# import app.temporal.activities.phase_specific_handlers

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class EnhancedTemporalWorker:
    """Enhanced Temporal worker with dynamic activity support.
    
    This worker provides advanced features including:
    - Dynamic activity registration
    - Multiple task queue support
    - Specialized workers for different workload types
    """
    
    def __init__(self):
        self.client: Optional[Client] = None
        self.workers = []
        self.settings = get_settings()
    
    async def start(self):
        """Start all workers"""
        try:
            # Connect to Temporal
            self.client = await Client.connect(
                self.settings.TEMPORAL_HOST or "localhost:7233",
                namespace=self.settings.TEMPORAL_NAMESPACE or "default"
            )
            
            # Create main workflow worker with all activities
            workflow_worker = Worker(
                self.client,
                task_queue=TASK_QUEUE_WORKFLOW,
                workflows=[
                    # Workflows that comply with Temporal sandbox
                    TestCycleWorkflow,
                    ReportTestingWorkflow,
                    # Enhanced workflow with dynamic activities
                    EnhancedTestCycleWorkflow
                ],
                activities=[
                    # Legacy activities
                    start_phase_activity,
                    complete_phase_activity,
                    check_phase_dependencies_activity,
                    create_test_cases_activity,
                    execute_test_activity,
                    batch_execute_tests_activity,
                    validate_test_results_activity,
                    send_phase_completion_notification_activity,
                    create_in_app_notification_activity,
                    # Dynamic activity support
                    get_activities_for_phase_activity,
                    execute_workflow_activity,
                    check_manual_activity_completed_activity,
                    get_parallel_instances_activity,
                    check_phase_completion_dependencies_activity,
                    create_workflow_activity_record_activity,
                    # Tracking activities
                    record_workflow_start_activity,
                    record_workflow_complete_activity,
                    record_step_start_activity,
                    record_step_complete_activity,
                    record_transition_activity,
                    calculate_workflow_metrics_activity
                ]
            )
            self.workers.append(workflow_worker)
            
            # Create LLM worker (separate for resource isolation)
            llm_worker = Worker(
                self.client,
                task_queue=TASK_QUEUE_LLM,
                workflows=[LLMAnalysisWorkflow],
                activities=[
                    generate_test_attributes_activity,
                    analyze_document_activity,
                    recommend_tests_activity,
                    analyze_patterns_activity,
                    # Add dynamic execution for LLM activities
                    execute_workflow_activity
                ]
            )
            self.workers.append(llm_worker)
            
            # Create notification worker
            notification_worker = Worker(
                self.client,
                task_queue=TASK_QUEUE_NOTIFICATION,
                activities=[
                    send_email_notification_activity,
                    create_in_app_notification_activity,
                    send_phase_completion_notification_activity
                ]
            )
            self.workers.append(notification_worker)
            
            # Create report generation worker
            report_worker = Worker(
                self.client,
                task_queue=TASK_QUEUE_REPORT,
                activities=[
                    # Report generation activities would go here
                    execute_workflow_activity  # Can handle report activities dynamically
                ]
            )
            self.workers.append(report_worker)
            
            logger.info(f"Starting {len(self.workers)} workers with dynamic activity support")
            
            # Start all workers
            await asyncio.gather(*[worker.run() for worker in self.workers])
            
        except Exception as e:
            logger.error(f"Failed to start Temporal workers: {str(e)}")
            raise
    
    async def stop(self):
        """Stop all workers"""
        logger.info("Shutting down workers...")
        
        for worker in self.workers:
            await worker.shutdown()
        
        # Client doesn't need explicit close in newer versions
        pass
        
        logger.info("Workers shut down successfully")


async def main():
    """Main entry point for worker"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Starting Temporal workers with dynamic activity support...")
    
    worker = EnhancedTemporalWorker()
    
    try:
        await worker.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal...")
        await worker.stop()
    except Exception as e:
        logger.error(f"Worker error: {str(e)}")
        await worker.stop()
        raise


if __name__ == "__main__":
    asyncio.run(main())