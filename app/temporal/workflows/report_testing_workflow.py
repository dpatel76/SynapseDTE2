"""Report Testing Workflow - Temporal sandbox compliant"""

from temporalio import workflow
from temporalio.common import RetryPolicy
from datetime import timedelta
from typing import Dict, Any, Optional

# Import only data classes - no activities
from app.temporal.shared import (
    ReportTestingWorkflowInput, WorkflowContext, PhaseResult,
    WorkflowStatus, PhaseStatus, WORKFLOW_PHASES,
    DEFAULT_ACTIVITY_TIMEOUT, LLM_ACTIVITY_TIMEOUT
)


@workflow.defn
class ReportTestingWorkflow:
    """Workflow for testing individual reports within a cycle - sandbox compliant"""
    
    def __init__(self):
        self.status = WorkflowStatus.PENDING
        self.current_phase: Optional[str] = None
        self.test_results: Dict[str, Any] = {}
    
    @workflow.run
    async def run(self, input_data: ReportTestingWorkflowInput) -> Dict[str, Any]:
        """Execute report testing workflow"""
        
        self.status = WorkflowStatus.RUNNING
        workflow.logger.info(f"Starting report testing workflow for report {input_data.report_id}")
        
        # Create workflow context
        context = WorkflowContext(
            cycle_id=0,  # Will be fetched from cycle_report
            report_id=input_data.report_id,
            cycle_report_id=input_data.cycle_report_id,
            user_id=input_data.tester_id,
            metadata={}
        )
        
        # Define retry policy
        retry_policy = RetryPolicy(
            maximum_attempts=3,
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=30),
            backoff_coefficient=2
        )
        
        try:
            # Phase 1: Test Planning
            self.current_phase = "Test Planning"
            await self._execute_test_planning(context, retry_policy)
            
            # Phase 2: Test Case Creation
            self.current_phase = "Test Case Creation"
            test_cases = await self._create_test_cases(context, retry_policy)
            
            # Phase 3: Test Execution
            self.current_phase = "Test Execution"
            await self._execute_tests(context, test_cases, retry_policy)
            
            # Phase 4: Result Validation
            self.current_phase = "Result Validation"
            validation_result = await self._validate_results(context, retry_policy)
            
            # Mark workflow as completed
            self.status = WorkflowStatus.COMPLETED
            
            # Send completion notification
            await workflow.execute_activity(
                "create_in_app_notification_activity",
                {
                    "user_id": input_data.tester_id,
                    "notification_type": "TEST_COMPLETE",
                    "title": "Report Testing Completed",
                    "message": f"Testing completed for report {input_data.report_id}",
                    "priority": "MEDIUM",
                    "metadata": {
                        "report_id": input_data.report_id,
                        "cycle_report_id": input_data.cycle_report_id
                    }
                },
                start_to_close_timeout=DEFAULT_ACTIVITY_TIMEOUT,
                retry_policy=retry_policy
            )
            
            return {
                "status": "completed",
                "report_id": input_data.report_id,
                "test_results": self.test_results,
                "validation": validation_result
            }
            
        except Exception as e:
            self.status = WorkflowStatus.FAILED
            workflow.logger.error(f"Report testing workflow failed: {str(e)}")
            
            # Send failure notification
            await workflow.execute_activity(
                "create_in_app_notification_activity",
                {
                    "user_id": input_data.tester_id,
                    "notification_type": "TEST_FAILED",
                    "title": "Report Testing Failed",
                    "message": f"Testing failed for report {input_data.report_id}: {str(e)}",
                    "priority": "HIGH",
                    "metadata": {
                        "report_id": input_data.report_id,
                        "error": str(e)
                    }
                },
                start_to_close_timeout=DEFAULT_ACTIVITY_TIMEOUT,
                retry_policy=retry_policy
            )
            
            raise
    
    async def _execute_test_planning(
        self,
        context: WorkflowContext,
        retry_policy: RetryPolicy
    ) -> None:
        """Execute test planning phase"""
        
        # Start phase
        await workflow.execute_activity(
            "start_phase_activity",
            context.cycle_id,
            context.report_id,
            "Test Planning",
            start_to_close_timeout=DEFAULT_ACTIVITY_TIMEOUT,
            retry_policy=retry_policy
        )
        
        # Phase-specific logic would go here
        
        # Complete phase
        await workflow.execute_activity(
            "complete_phase_activity",
            context.cycle_id,
            context.report_id,
            "Test Planning",
            {"status": "completed"},
            start_to_close_timeout=DEFAULT_ACTIVITY_TIMEOUT,
            retry_policy=retry_policy
        )
    
    async def _create_test_cases(
        self,
        context: WorkflowContext,
        retry_policy: RetryPolicy
    ) -> Dict[str, Any]:
        """Create test cases for the report"""
        
        test_cases = await workflow.execute_activity(
            "create_test_cases_activity",
            {
                "cycle_id": context.cycle_id,
                "report_id": context.report_id
            },
            start_to_close_timeout=DEFAULT_ACTIVITY_TIMEOUT,
            retry_policy=retry_policy
        )
        
        self.test_results["test_cases_created"] = len(test_cases.get("test_cases", []))
        return test_cases
    
    async def _execute_tests(
        self,
        context: WorkflowContext,
        test_cases: Dict[str, Any],
        retry_policy: RetryPolicy
    ) -> None:
        """Execute the test cases"""
        
        if not test_cases.get("test_cases"):
            workflow.logger.info("No test cases to execute")
            return
        
        # Execute each test
        results = []
        for test_case in test_cases["test_cases"]:
            result = await workflow.execute_activity(
                "execute_test_activity",
                {
                    "test_case_id": test_case["id"],
                    "test_data": test_case.get("test_data", {})
                },
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=retry_policy
            )
            results.append(result)
        
        self.test_results["executed"] = len(results)
        self.test_results["passed"] = len([r for r in results if r.get("status") == "passed"])
        self.test_results["failed"] = len([r for r in results if r.get("status") == "failed"])
    
    async def _validate_results(
        self,
        context: WorkflowContext,
        retry_policy: RetryPolicy
    ) -> Dict[str, Any]:
        """Validate test results"""
        
        return await workflow.execute_activity(
            "validate_test_results_activity",
            {
                "report_id": context.report_id,
                "test_results": self.test_results
            },
            start_to_close_timeout=DEFAULT_ACTIVITY_TIMEOUT,
            retry_policy=retry_policy
        )