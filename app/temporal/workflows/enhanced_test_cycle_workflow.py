"""
Enhanced Test Cycle Workflow - Temporal sandbox compliant
Supports sequential dependencies and parallel execution paths
"""

from temporalio import workflow
from temporalio.common import RetryPolicy
from datetime import timedelta, datetime
from typing import List, Dict, Any, Optional, Set
import uuid
import asyncio

# Import only data classes - no activities or external modules
from app.temporal.shared import (
    TestCycleWorkflowInput, PhaseResult,
    WorkflowStatus, PhaseStatus, WORKFLOW_PHASES
)


@workflow.defn
class EnhancedTestCycleWorkflow:
    """Enhanced workflow with dynamic activity execution - sandbox compliant"""
    
    def __init__(self):
        self.workflow_id = str(uuid.uuid4())
        self.status = WorkflowStatus.PENDING
        self.completed_phases: Set[str] = set()
        self.phase_results: Dict[str, PhaseResult] = {}
        self.current_version = "2.0"
        self.retry_count = 0
        self.max_retries = 3
    
    @workflow.run
    async def run(self, input_data: TestCycleWorkflowInput) -> Dict[str, Any]:
        """Execute the enhanced test cycle workflow"""
        
        self.status = WorkflowStatus.RUNNING
        workflow.logger.info(f"Starting enhanced workflow v2 for cycle {input_data.cycle_id}")
        
        # Record workflow start
        await self._record_workflow_start(input_data)
        
        # Define retry policy
        retry_policy = RetryPolicy(
            maximum_attempts=3,
            initial_interval=timedelta(seconds=2),
            maximum_interval=timedelta(seconds=60),
            backoff_coefficient=2
        )
        
        try:
            # Process each report
            report_results = []
            for report_data in input_data.reports:
                workflow.logger.info(f"Processing report {report_data['report_id']}")
                
                # Execute workflow for this report
                report_result = await self._execute_report_workflow(
                    input_data.cycle_id,
                    report_data,
                    input_data.initiated_by_user_id,
                    retry_policy
                )
                report_results.append(report_result)
            
            # Record workflow completion
            await self._record_workflow_complete(input_data, report_results)
            
            self.status = WorkflowStatus.COMPLETED
            
            return {
                "workflow_id": self.workflow_id,
                "status": "completed",
                "cycle_id": input_data.cycle_id,
                "version": self.current_version,
                "report_results": report_results,
                "metrics": await self._calculate_metrics()
            }
            
        except Exception as e:
            self.status = WorkflowStatus.FAILED
            workflow.logger.error(f"Enhanced workflow failed: {str(e)}")
            
            # Record failure
            await workflow.execute_activity(
                "record_workflow_complete_activity",
                {
                    "workflow_id": self.workflow_id,
                    "cycle_id": input_data.cycle_id,
                    "status": "failed",
                    "error": str(e)
                },
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=retry_policy
            )
            
            raise
    
    async def _execute_report_workflow(
        self,
        cycle_id: int,
        report_data: Dict[str, Any],
        user_id: int,
        retry_policy: RetryPolicy
    ) -> Dict[str, Any]:
        """Execute workflow for a single report with dynamic activities"""
        
        report_id = report_data['report_id']
        
        # Get dynamic activities for each phase
        phase_activities = {}
        for phase_name in WORKFLOW_PHASES:
            activities = await workflow.execute_activity(
                "get_activities_for_phase_activity",
                {
                    "phase_name": phase_name,
                    "report_type": report_data.get('report_type', 'standard'),
                    "workflow_version": self.current_version
                },
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=retry_policy
            )
            phase_activities[phase_name] = activities.get('activities', [])
        
        # Execute phases with dependencies
        phase_results = {}
        completed_phases = set()
        
        # Define phase dependencies
        phase_dependencies = {
            "Planning": [],
            "Scoping": ["Planning"],
            "Sample Selection": ["Scoping"],
            "Data Owner Identification": ["Scoping"],
            "Request for Information": ["Data Owner Identification"],
            "Test Execution": ["Sample Selection", "Request for Information"],
            "Observation Management": ["Test Execution"],
            "Testing Report": ["Observation Management"]
        }
        
        # Execute phases respecting dependencies
        while len(completed_phases) < len(WORKFLOW_PHASES):
            # Find phases ready to execute
            ready_phases = []
            for phase, deps in phase_dependencies.items():
                if phase not in completed_phases and all(d in completed_phases for d in deps):
                    ready_phases.append(phase)
            
            if not ready_phases:
                raise Exception("No phases ready to execute - possible circular dependency")
            
            # Execute ready phases in parallel
            phase_tasks = []
            for phase_name in ready_phases:
                task = self._execute_phase_with_activities(
                    cycle_id,
                    report_id,
                    phase_name,
                    phase_activities.get(phase_name, []),
                    user_id,
                    retry_policy
                )
                phase_tasks.append(task)
            
            # Wait for all parallel phases to complete
            results = await asyncio.gather(*phase_tasks)
            
            # Update completed phases and results
            for i, phase_name in enumerate(ready_phases):
                phase_results[phase_name] = results[i]
                completed_phases.add(phase_name)
                workflow.logger.info(f"Completed phase: {phase_name}")
        
        return {
            "report_id": report_id,
            "phase_results": phase_results,
            "status": "completed"
        }
    
    async def _execute_phase_with_activities(
        self,
        cycle_id: int,
        report_id: int,
        phase_name: str,
        activities: List[Dict[str, Any]],
        user_id: int,
        retry_policy: RetryPolicy
    ) -> PhaseResult:
        """Execute a phase with its dynamic activities"""
        
        # Record phase start
        await workflow.execute_activity(
            "record_step_start_activity",
            {
                "workflow_id": self.workflow_id,
                "step_name": phase_name,
                "cycle_id": cycle_id,
                "report_id": report_id
            },
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=retry_policy
        )
        
        phase_result = PhaseResult(
            phase_name=phase_name,
            status=PhaseStatus.IN_PROGRESS,
            started_at=workflow.now().isoformat(),
            data={}
        )
        
        try:
            # Execute each activity in the phase
            for activity_config in activities:
                activity_name = activity_config['activity_name']
                is_manual = activity_config.get('is_manual', False)
                timeout_seconds = activity_config.get('timeout_seconds', 300)
                
                if is_manual:
                    # Create record for manual activity
                    activity_record = await workflow.execute_activity(
                        "create_workflow_activity_record_activity",
                        {
                            "workflow_id": self.workflow_id,
                            "phase_name": phase_name,
                            "activity_name": activity_name,
                            "cycle_id": cycle_id,
                            "report_id": report_id,
                            "assigned_to": user_id
                        },
                        start_to_close_timeout=timedelta(seconds=30),
                        retry_policy=retry_policy
                    )
                    
                    # Wait for manual completion
                    activity_id = activity_record['activity_id']
                    completed = False
                    while not completed:
                        await workflow.sleep(timedelta(seconds=30))  # Check every 30 seconds
                        
                        check_result = await workflow.execute_activity(
                            "check_manual_activity_completed_activity",
                            {"activity_id": activity_id},
                            start_to_close_timeout=timedelta(seconds=30),
                            retry_policy=retry_policy
                        )
                        completed = check_result.get('completed', False)
                    
                    phase_result.data[activity_name] = check_result.get('result', {})
                    
                else:
                    # Execute automatic activity
                    result = await workflow.execute_activity(
                        "execute_workflow_activity",
                        {
                            "activity_name": activity_name,
                            "parameters": {
                                "cycle_id": cycle_id,
                                "report_id": report_id,
                                "phase_name": phase_name,
                                "workflow_id": self.workflow_id
                            }
                        },
                        start_to_close_timeout=timedelta(seconds=timeout_seconds),
                        retry_policy=retry_policy
                    )
                    phase_result.data[activity_name] = result
            
            # Check phase completion dependencies
            completion_check = await workflow.execute_activity(
                "check_phase_completion_dependencies_activity",
                {
                    "cycle_id": cycle_id,
                    "report_id": report_id,
                    "phase_name": phase_name
                },
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=retry_policy
            )
            
            if not completion_check.get('can_complete', True):
                raise Exception(f"Phase completion dependencies not met: {completion_check.get('reason')}")
            
            # Mark phase as completed
            phase_result.status = PhaseStatus.COMPLETED
            phase_result.completed_at = workflow.now().isoformat()
            
            # Record phase completion
            await workflow.execute_activity(
                "record_step_complete_activity",
                {
                    "workflow_id": self.workflow_id,
                    "step_name": phase_name,
                    "status": "completed",
                    "result_data": phase_result.data
                },
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=retry_policy
            )
            
        except Exception as e:
            phase_result.status = PhaseStatus.FAILED
            phase_result.error = str(e)
            
            # Record phase failure
            await workflow.execute_activity(
                "record_step_complete_activity",
                {
                    "workflow_id": self.workflow_id,
                    "step_name": phase_name,
                    "status": "failed",
                    "error": str(e)
                },
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=retry_policy
            )
            
            raise
        
        return phase_result
    
    async def _record_workflow_start(self, input_data: TestCycleWorkflowInput):
        """Record workflow start in tracking system"""
        
        await workflow.execute_activity(
            "record_workflow_start_activity",
            {
                "workflow_id": self.workflow_id,
                "workflow_type": "TestCycleWorkflowV2",
                "cycle_id": input_data.cycle_id,
                "initiated_by": input_data.initiated_by_user_id,
                "parameters": {
                    "report_count": len(input_data.reports),
                    "version": self.current_version
                }
            },
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )
    
    async def _record_workflow_complete(
        self,
        input_data: TestCycleWorkflowInput,
        results: List[Dict[str, Any]]
    ):
        """Record workflow completion"""
        
        await workflow.execute_activity(
            "record_workflow_complete_activity",
            {
                "workflow_id": self.workflow_id,
                "cycle_id": input_data.cycle_id,
                "status": "completed",
                "results": {
                    "reports_processed": len(results),
                    "successful": len([r for r in results if r.get('status') == 'completed'])
                }
            },
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )
    
    async def _calculate_metrics(self) -> Dict[str, Any]:
        """Calculate workflow metrics"""
        
        return await workflow.execute_activity(
            "calculate_workflow_metrics_activity",
            {"workflow_id": self.workflow_id},
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )