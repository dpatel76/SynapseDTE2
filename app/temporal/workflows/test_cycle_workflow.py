"""Test Cycle Workflow - Temporal sandbox compliant"""

from temporalio import workflow
from temporalio.common import RetryPolicy
from datetime import timedelta
from typing import List, Dict, Any
import logging

# Import only data classes and enums - no activities
from app.temporal.shared import (
    TestCycleWorkflowInput, WorkflowContext, PhaseResult,
    WorkflowStatus, PhaseStatus, WORKFLOW_PHASES,
    DEFAULT_ACTIVITY_TIMEOUT, DEFAULT_RETRY_ATTEMPTS
)

# DO NOT import activities directly - this violates Temporal's sandbox
# Activities will be called by their registered names


@workflow.defn
class TestCycleWorkflow:
    """Main workflow for test cycle execution - sandbox compliant"""
    
    def __init__(self):
        self.status = WorkflowStatus.PENDING
        self.completed_phases: List[str] = []
        self.phase_results: Dict[str, PhaseResult] = {}
    
    @workflow.run
    async def run(self, input_data: TestCycleWorkflowInput) -> Dict[str, Any]:
        """Execute the test cycle workflow"""
        
        # Set workflow status
        self.status = WorkflowStatus.RUNNING
        workflow.logger.info(f"Starting test cycle workflow for cycle {input_data.cycle_id}")
        
        # Create workflow context
        context = WorkflowContext(
            cycle_id=input_data.cycle_id,
            report_id=0,  # Will be set per report
            cycle_report_id=0,  # Will be set per report
            user_id=input_data.initiated_by_user_id,
            metadata={}
        )
        
        # Define retry policy for activities
        retry_policy = RetryPolicy(
            maximum_attempts=DEFAULT_RETRY_ATTEMPTS,
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=30),
            backoff_coefficient=2
        )
        
        try:
            # Process each report in the cycle
            results = []
            for report_data in input_data.reports:
                workflow.logger.info(f"Processing report {report_data['report_id']}")
                
                # Update context for this report
                context.report_id = report_data['report_id']
                context.cycle_report_id = report_data.get('cycle_report_id', 0)
                
                # Execute phases for this report
                report_result = await self._execute_report_phases(
                    context, report_data, retry_policy
                )
                results.append(report_result)
            
            # Mark workflow as completed
            self.status = WorkflowStatus.COMPLETED
            
            # Send completion notification
            await workflow.execute_activity(
                "send_phase_completion_notification_activity",
                {
                    "cycle_id": input_data.cycle_id,
                    "phase": "Workflow Complete",
                    "status": "completed",
                    "user_id": input_data.initiated_by_user_id
                },
                start_to_close_timeout=DEFAULT_ACTIVITY_TIMEOUT,
                retry_policy=retry_policy
            )
            
            return {
                "status": "completed",
                "cycle_id": input_data.cycle_id,
                "report_results": results,
                "completed_phases": self.completed_phases
            }
            
        except Exception as e:
            self.status = WorkflowStatus.FAILED
            workflow.logger.error(f"Workflow failed: {str(e)}")
            raise
    
    async def _execute_report_phases(
        self,
        context: WorkflowContext,
        report_data: Dict[str, Any],
        retry_policy: RetryPolicy
    ) -> Dict[str, Any]:
        """Execute all phases for a single report"""
        
        phases_to_execute = [
            "Planning",
            "Scoping", 
            "Sample Selection",
            "Data Owner Identification",
            "Request for Information",
            "Test Execution",
            "Observation Management",
            "Testing Report"
        ]
        
        phase_results = {}
        
        for phase_name in phases_to_execute:
            workflow.logger.info(f"Starting phase: {phase_name}")
            
            # Check phase dependencies
            dependencies_met = await workflow.execute_activity(
                "check_phase_dependencies_activity",
                {
                    "cycle_id": context.cycle_id,
                    "report_id": context.report_id,
                    "phase_name": phase_name
                },
                start_to_close_timeout=DEFAULT_ACTIVITY_TIMEOUT,
                retry_policy=retry_policy
            )
            
            if not dependencies_met.get("dependencies_met", False):
                raise Exception(f"Dependencies not met for phase {phase_name}")
            
            # Start phase
            await workflow.execute_activity(
                "start_phase_activity",
                context.cycle_id,
                context.report_id,
                phase_name,
                start_to_close_timeout=DEFAULT_ACTIVITY_TIMEOUT,
                retry_policy=retry_policy
            )
            
            # Execute phase-specific logic
            phase_result = await self._execute_phase(
                phase_name, context, report_data, retry_policy
            )
            phase_results[phase_name] = phase_result
            
            # Complete phase
            await workflow.execute_activity(
                "complete_phase_activity",
                context.cycle_id,
                context.report_id,
                phase_name,
                phase_result,
                start_to_close_timeout=DEFAULT_ACTIVITY_TIMEOUT,
                retry_policy=retry_policy
            )
            
            self.completed_phases.append(f"{context.report_id}:{phase_name}")
        
        return {
            "report_id": context.report_id,
            "cycle_report_id": context.cycle_report_id,
            "phase_results": phase_results,
            "status": "completed"
        }
    
    async def _execute_phase(
        self,
        phase_name: str,
        context: WorkflowContext,
        report_data: Dict[str, Any],
        retry_policy: RetryPolicy
    ) -> PhaseResult:
        """Execute a specific phase"""
        
        phase_result = PhaseResult(
            phase_name=phase_name,
            status=PhaseStatus.IN_PROGRESS,
            started_at=workflow.now().isoformat(),
            data={}
        )
        
        try:
            if phase_name == "Scoping":
                # Generate test attributes using LLM
                llm_result = await workflow.execute_activity(
                    "generate_test_attributes_activity",
                    {
                        "report_id": context.report_id,
                        "report_name": report_data.get("report_name", ""),
                        "regulatory_framework": report_data.get("regulatory_framework", "")
                    },
                    start_to_close_timeout=timedelta(minutes=5),  # LLM needs more time
                    retry_policy=retry_policy
                )
                phase_result.data["attributes_generated"] = llm_result.get("attributes_count", 0)
                
            elif phase_name == "Test Execution":
                # Create test cases
                test_cases = await workflow.execute_activity(
                    "create_test_cases_activity",
                    {
                        "cycle_id": context.cycle_id,
                        "report_id": context.report_id
                    },
                    start_to_close_timeout=DEFAULT_ACTIVITY_TIMEOUT,
                    retry_policy=retry_policy
                )
                
                # Execute tests in batches
                if test_cases.get("test_cases"):
                    batch_result = await workflow.execute_activity(
                        "batch_execute_tests_activity",
                        {
                            "test_case_ids": [tc["id"] for tc in test_cases["test_cases"]],
                            "batch_size": 10
                        },
                        start_to_close_timeout=timedelta(minutes=10),
                        retry_policy=retry_policy
                    )
                    phase_result.data["tests_executed"] = batch_result.get("executed_count", 0)
                    phase_result.data["tests_passed"] = batch_result.get("passed_count", 0)
            
            # Mark phase as completed
            phase_result.status = PhaseStatus.COMPLETED
            phase_result.completed_at = workflow.now().isoformat()
            
        except Exception as e:
            phase_result.status = PhaseStatus.FAILED
            phase_result.error = str(e)
            workflow.logger.error(f"Phase {phase_name} failed: {str(e)}")
            raise
        
        return phase_result