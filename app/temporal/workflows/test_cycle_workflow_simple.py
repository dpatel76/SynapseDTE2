"""Simplified Test Cycle Workflow for testing

This workflow uses activity stubs instead of direct imports
"""

from temporalio import workflow
from temporalio.common import RetryPolicy
from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import timedelta
import logging


@dataclass
class WorkflowInput:
    """Input parameters for the test cycle workflow"""
    cycle_id: int
    report_id: int
    user_id: int
    metadata: Dict[str, Any] = None


@dataclass
class WorkflowResult:
    """Result of the test cycle workflow"""
    cycle_id: int
    report_id: int
    status: str
    phases_completed: list
    completion_time: str
    errors: list = None


@workflow.defn
class TestCycleWorkflowSimple:
    """Simplified test cycle workflow for testing"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.current_phase = None
        self.phases_completed = []
        self.workflow_state = {}
    
    @workflow.run
    async def run(self, input_data: WorkflowInput) -> WorkflowResult:
        """Main workflow execution"""
        self.logger.info(f"Starting test cycle workflow for cycle {input_data.cycle_id}, report {input_data.report_id}")
        
        try:
            # Phase 1: Planning - Simple activity execution
            self.current_phase = "Planning"
            planning_result = await workflow.execute_activity(
                "start_planning_phase_activity",
                args=[input_data.cycle_id, input_data.report_id, input_data.user_id],
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=RetryPolicy(maximum_attempts=3)
            )
            
            if planning_result.get("success"):
                self.phases_completed.append("Planning")
                self.logger.info("Planning phase started successfully")
            else:
                raise Exception(f"Planning phase failed: {planning_result.get('error')}")
            
            # Return early for testing
            return WorkflowResult(
                cycle_id=input_data.cycle_id,
                report_id=input_data.report_id,
                status="In Progress",
                phases_completed=self.phases_completed,
                completion_time=workflow.now().isoformat()
            )
            
        except Exception as e:
            self.logger.error(f"Workflow failed: {str(e)}")
            return WorkflowResult(
                cycle_id=input_data.cycle_id,
                report_id=input_data.report_id,
                status="Failed",
                phases_completed=self.phases_completed,
                completion_time=workflow.now().isoformat(),
                errors=[str(e)]
            )