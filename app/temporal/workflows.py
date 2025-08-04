"""
Temporal Workflow Definitions for SynapseDTE
"""
from datetime import timedelta
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.workflow import ParentClosePolicy

from app.temporal.activities import (
    planning_activities,
    scoping_activities,
    sample_selection_activities,
    data_owner_activities,
    rfi_activities,
    test_execution_activities,
    observation_activities,
    report_activities,
    notification_activities,
    sla_activities
)

@dataclass
class WorkflowInput:
    cycle_id: int
    report_id: int
    user_id: int
    metadata: Dict[str, Any]

@dataclass
class PhaseResult:
    phase_name: str
    status: str
    completed_at: Optional[str]
    result_data: Dict[str, Any]

@workflow.defn
class RegulatoryTestingWorkflow:
    """Main 8-phase regulatory testing workflow"""
    
    @workflow.run
    async def run(self, input: WorkflowInput) -> Dict[str, Any]:
        """Execute the complete 8-phase workflow"""
        
        workflow_result = {
            "cycle_id": input.cycle_id,
            "report_id": input.report_id,
            "phases": [],
            "status": "in_progress"
        }
        
        # Common retry policy for activities
        retry_policy = RetryPolicy(
            maximum_attempts=3,
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=10),
            backoff_coefficient=2
        )
        
        try:
            # Phase 1: Planning
            planning_result = await workflow.execute_child_workflow(
                PlanningPhaseWorkflow.run,
                input,
                id=f"planning-{input.cycle_id}-{input.report_id}",
                retry_policy=retry_policy
            )
            workflow_result["phases"].append(planning_result)
            
            # Phase 2: Scoping (depends on Planning)
            scoping_result = await workflow.execute_child_workflow(
                ScopingPhaseWorkflow.run,
                input,
                id=f"scoping-{input.cycle_id}-{input.report_id}",
                retry_policy=retry_policy
            )
            workflow_result["phases"].append(scoping_result)
            
            # Phase 3 & 4: Sample Selection and Data Owner ID (parallel)
            # These can run in parallel after Scoping
            sample_future = workflow.execute_child_workflow(
                SampleSelectionWorkflow.run,
                input,
                id=f"sample-selection-{input.cycle_id}-{input.report_id}",
                retry_policy=retry_policy
            )
            
            data_owner_future = workflow.execute_child_workflow(
                DataOwnerIdentificationWorkflow.run,
                input,
                id=f"data-owner-{input.cycle_id}-{input.report_id}",
                retry_policy=retry_policy
            )
            
            # Wait for both parallel phases
            sample_result = await sample_future
            data_owner_result = await data_owner_future
            
            workflow_result["phases"].extend([sample_result, data_owner_result])
            
            # Phase 5: Request for Information (depends on Data Owner ID)
            rfi_result = await workflow.execute_child_workflow(
                RequestForInformationWorkflow.run,
                input,
                id=f"rfi-{input.cycle_id}-{input.report_id}",
                retry_policy=retry_policy
            )
            workflow_result["phases"].append(rfi_result)
            
            # Phase 6: Test Execution (depends on RFI and Sample Selection)
            test_result = await workflow.execute_child_workflow(
                TestExecutionWorkflow.run,
                input,
                id=f"test-execution-{input.cycle_id}-{input.report_id}",
                retry_policy=retry_policy
            )
            workflow_result["phases"].append(test_result)
            
            # Phase 7: Observation Management (depends on Test Execution)
            observation_result = await workflow.execute_child_workflow(
                ObservationManagementWorkflow.run,
                input,
                id=f"observations-{input.cycle_id}-{input.report_id}",
                retry_policy=retry_policy
            )
            workflow_result["phases"].append(observation_result)
            
            # Phase 8: Testing Report (depends on Observations)
            report_result = await workflow.execute_child_workflow(
                TestingReportWorkflow.run,
                input,
                id=f"testing-report-{input.cycle_id}-{input.report_id}",
                retry_policy=retry_policy
            )
            workflow_result["phases"].append(report_result)
            
            workflow_result["status"] = "completed"
            
            # Send completion notification
            await workflow.execute_activity(
                notification_activities.send_notification,
                {
                    "user_id": input.user_id,
                    "type": "workflow_completed",
                    "title": "Testing Cycle Completed",
                    "message": f"All phases completed for cycle {input.cycle_id}"
                },
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=retry_policy
            )
            
        except Exception as e:
            workflow_result["status"] = "failed"
            workflow_result["error"] = str(e)
            
            # Send failure notification
            await workflow.execute_activity(
                notification_activities.send_notification,
                {
                    "user_id": input.user_id,
                    "type": "workflow_failed",
                    "title": "Testing Cycle Failed",
                    "message": f"Workflow failed: {str(e)}"
                },
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=retry_policy
            )
            
            raise
        
        return workflow_result

@workflow.defn
class PlanningPhaseWorkflow:
    """Planning phase workflow"""
    
    @workflow.run
    async def run(self, input: WorkflowInput) -> PhaseResult:
        """Execute planning phase activities"""
        
        # Start SLA tracking
        await workflow.execute_activity(
            sla_activities.start_sla_tracking,
            {
                "entity_type": "workflow_phase",
                "entity_id": f"{input.cycle_id}_{input.report_id}_planning",
                "sla_hours": 72
            },
            start_to_close_timeout=timedelta(seconds=30)
        )
        
        # Create test cycle
        cycle_result = await workflow.execute_activity(
            planning_activities.create_test_cycle,
            {
                "cycle_id": input.cycle_id,
                "user_id": input.user_id,
                "metadata": input.metadata
            },
            start_to_close_timeout=timedelta(minutes=5)
        )
        
        # Add report to cycle
        await workflow.execute_activity(
            planning_activities.add_report_to_cycle,
            {
                "cycle_id": input.cycle_id,
                "report_id": input.report_id
            },
            start_to_close_timeout=timedelta(minutes=2)
        )
        
        # Assign tester
        await workflow.execute_activity(
            planning_activities.assign_tester,
            {
                "cycle_id": input.cycle_id,
                "report_id": input.report_id,
                "tester_id": input.metadata.get("tester_id")
            },
            start_to_close_timeout=timedelta(minutes=2)
        )
        
        # Finalize planning
        await workflow.execute_activity(
            planning_activities.finalize_planning,
            {
                "cycle_id": input.cycle_id,
                "report_id": input.report_id
            },
            start_to_close_timeout=timedelta(minutes=2)
        )
        
        # Complete SLA
        await workflow.execute_activity(
            sla_activities.complete_sla,
            {
                "entity_type": "workflow_phase",
                "entity_id": f"{input.cycle_id}_{input.report_id}_planning"
            },
            start_to_close_timeout=timedelta(seconds=30)
        )
        
        return PhaseResult(
            phase_name="Planning",
            status="completed",
            completed_at=workflow.now().isoformat(),
            result_data={"cycle_created": True}
        )

@workflow.defn
class ScopingPhaseWorkflow:
    """Scoping phase workflow"""
    
    @workflow.run
    async def run(self, input: WorkflowInput) -> PhaseResult:
        """Execute scoping phase activities"""
        
        # Start SLA tracking
        await workflow.execute_activity(
            sla_activities.start_sla_tracking,
            {
                "entity_type": "workflow_phase",
                "entity_id": f"{input.cycle_id}_{input.report_id}_scoping",
                "sla_hours": 48
            },
            start_to_close_timeout=timedelta(seconds=30)
        )
        
        # Generate test attributes using LLM
        attributes_result = await workflow.execute_activity(
            scoping_activities.generate_test_attributes,
            {
                "cycle_id": input.cycle_id,
                "report_id": input.report_id,
                "regulatory_context": input.metadata.get("regulatory_context")
            },
            start_to_close_timeout=timedelta(minutes=10)  # LLM operations need more time
        )
        
        # Review attributes
        review_result = await workflow.execute_activity(
            scoping_activities.review_attributes,
            {
                "cycle_id": input.cycle_id,
                "report_id": input.report_id,
                "attributes": attributes_result["attributes"]
            },
            start_to_close_timeout=timedelta(minutes=5)
        )
        
        # Wait for approval signal
        approval_signal = await workflow.wait_condition(
            lambda: workflow.info().is_signal_received("approve_scoping"),
            timeout=timedelta(hours=24)
        )
        
        # Approve scoping
        await workflow.execute_activity(
            scoping_activities.approve_scoping,
            {
                "cycle_id": input.cycle_id,
                "report_id": input.report_id,
                "approved_by": input.user_id
            },
            start_to_close_timeout=timedelta(minutes=2)
        )
        
        # Complete SLA
        await workflow.execute_activity(
            sla_activities.complete_sla,
            {
                "entity_type": "workflow_phase",
                "entity_id": f"{input.cycle_id}_{input.report_id}_scoping"
            },
            start_to_close_timeout=timedelta(seconds=30)
        )
        
        return PhaseResult(
            phase_name="Scoping",
            status="completed",
            completed_at=workflow.now().isoformat(),
            result_data={
                "attributes_count": len(attributes_result.get("attributes", [])),
                "approved": True
            }
        )

@workflow.defn
class SampleSelectionWorkflow:
    """Sample Selection phase workflow"""
    
    @workflow.run
    async def run(self, input: WorkflowInput) -> PhaseResult:
        """Execute sample selection phase activities"""
        
        # Start SLA tracking
        await workflow.execute_activity(
            sla_activities.start_sla_tracking,
            {
                "entity_type": "workflow_phase",
                "entity_id": f"{input.cycle_id}_{input.report_id}_sample_selection",
                "sla_hours": 48
            },
            start_to_close_timeout=timedelta(seconds=30)
        )
        
        # Generate sample selection
        sample_result = await workflow.execute_activity(
            sample_selection_activities.generate_sample_selection,
            {
                "cycle_id": input.cycle_id,
                "report_id": input.report_id,
                "sample_criteria": input.metadata.get("sample_criteria")
            },
            start_to_close_timeout=timedelta(minutes=5)
        )
        
        # Approve sample selection
        await workflow.execute_activity(
            sample_selection_activities.approve_sample_selection,
            {
                "cycle_id": input.cycle_id,
                "report_id": input.report_id,
                "approved_by": input.user_id
            },
            start_to_close_timeout=timedelta(minutes=2)
        )
        
        # Upload sample data
        await workflow.execute_activity(
            sample_selection_activities.upload_sample_data,
            {
                "cycle_id": input.cycle_id,
                "report_id": input.report_id,
                "sample_data": sample_result.get("cycle_report_sample_selection_samples")
            },
            start_to_close_timeout=timedelta(minutes=5)
        )
        
        # Complete SLA
        await workflow.execute_activity(
            sla_activities.complete_sla,
            {
                "entity_type": "workflow_phase",
                "entity_id": f"{input.cycle_id}_{input.report_id}_sample_selection"
            },
            start_to_close_timeout=timedelta(seconds=30)
        )
        
        return PhaseResult(
            phase_name="Sample Selection",
            status="completed",
            completed_at=workflow.now().isoformat(),
            result_data={
                "sample_count": len(sample_result.get("cycle_report_sample_selection_samples", [])),
                "uploaded": True
            }
        )

@workflow.defn
class DataOwnerIdentificationWorkflow:
    """Data Owner Identification phase workflow"""
    
    @workflow.run
    async def run(self, input: WorkflowInput) -> PhaseResult:
        """Execute data owner identification phase activities"""
        
        # Start SLA tracking
        await workflow.execute_activity(
            sla_activities.start_sla_tracking,
            {
                "entity_type": "workflow_phase",
                "entity_id": f"{input.cycle_id}_{input.report_id}_data_owner_id",
                "sla_hours": 24
            },
            start_to_close_timeout=timedelta(seconds=30)
        )
        
        # Identify data owners
        owners_result = await workflow.execute_activity(
            data_owner_activities.identify_data_owners,
            {
                "cycle_id": input.cycle_id,
                "report_id": input.report_id
            },
            start_to_close_timeout=timedelta(minutes=5)
        )
        
        # Assign data owners
        for owner in owners_result.get("data_owners", []):
            await workflow.execute_activity(
                data_owner_activities.assign_data_owner,
                {
                    "cycle_id": input.cycle_id,
                    "report_id": input.report_id,
                    "owner_id": owner["id"],
                    "lob": owner["lob"]
                },
                start_to_close_timeout=timedelta(minutes=2)
            )
            
            # Notify data owner
            await workflow.execute_activity(
                data_owner_activities.notify_data_owner,
                {
                    "owner_id": owner["id"],
                    "cycle_id": input.cycle_id,
                    "report_id": input.report_id
                },
                start_to_close_timeout=timedelta(minutes=2)
            )
        
        # Complete SLA
        await workflow.execute_activity(
            sla_activities.complete_sla,
            {
                "entity_type": "workflow_phase",
                "entity_id": f"{input.cycle_id}_{input.report_id}_data_owner_id"
            },
            start_to_close_timeout=timedelta(seconds=30)
        )
        
        return PhaseResult(
            phase_name="Data Owner Identification",
            status="completed",
            completed_at=workflow.now().isoformat(),
            result_data={
                "owners_assigned": len(owners_result.get("data_owners", [])),
                "notifications_sent": True
            }
        )

@workflow.defn
class RequestForInformationWorkflow:
    """Request for Information phase workflow"""
    
    @workflow.run
    async def run(self, input: WorkflowInput) -> PhaseResult:
        """Execute RFI phase activities"""
        
        # Start SLA tracking
        await workflow.execute_activity(
            sla_activities.start_sla_tracking,
            {
                "entity_type": "workflow_phase",
                "entity_id": f"{input.cycle_id}_{input.report_id}_rfi",
                "sla_hours": 72
            },
            start_to_close_timeout=timedelta(seconds=30)
        )
        
        # Create RFI
        rfi_result = await workflow.execute_activity(
            rfi_activities.create_rfi,
            {
                "cycle_id": input.cycle_id,
                "report_id": input.report_id,
                "attributes": input.metadata.get("attributes")
            },
            start_to_close_timeout=timedelta(minutes=5)
        )
        
        # Send RFI notifications
        await workflow.execute_activity(
            rfi_activities.send_rfi_notification,
            {
                "cycle_id": input.cycle_id,
                "report_id": input.report_id,
                "rfi_id": rfi_result["rfi_id"]
            },
            start_to_close_timeout=timedelta(minutes=2)
        )
        
        # Wait for responses (with timeout)
        responses_complete = await workflow.wait_condition(
            lambda: workflow.info().is_signal_received("rfi_responses_complete"),
            timeout=timedelta(hours=48)
        )
        
        # Process RFI responses
        await workflow.execute_activity(
            rfi_activities.process_rfi_response,
            {
                "cycle_id": input.cycle_id,
                "report_id": input.report_id,
                "rfi_id": rfi_result["rfi_id"]
            },
            start_to_close_timeout=timedelta(minutes=5)
        )
        
        # Complete SLA
        await workflow.execute_activity(
            sla_activities.complete_sla,
            {
                "entity_type": "workflow_phase",
                "entity_id": f"{input.cycle_id}_{input.report_id}_rfi"
            },
            start_to_close_timeout=timedelta(seconds=30)
        )
        
        return PhaseResult(
            phase_name="Request for Information",
            status="completed",
            completed_at=workflow.now().isoformat(),
            result_data={
                "rfi_sent": True,
                "responses_received": True
            }
        )

@workflow.defn
class TestExecutionWorkflow:
    """Test Execution phase workflow"""
    
    @workflow.run
    async def run(self, input: WorkflowInput) -> PhaseResult:
        """Execute test execution phase activities"""
        
        # Start SLA tracking
        await workflow.execute_activity(
            sla_activities.start_sla_tracking,
            {
                "entity_type": "workflow_phase",
                "entity_id": f"{input.cycle_id}_{input.report_id}_test_execution",
                "sla_hours": 120  # 5 days
            },
            start_to_close_timeout=timedelta(seconds=30)
        )
        
        # Get test cases
        test_cases = input.metadata.get("test_cases", [])
        results = []
        
        # Execute tests
        for test_case in test_cases:
            test_result = await workflow.execute_activity(
                test_execution_activities.execute_test,
                {
                    "cycle_id": input.cycle_id,
                    "report_id": input.report_id,
                    "test_case": test_case
                },
                start_to_close_timeout=timedelta(minutes=10)
            )
            
            # Record test result
            await workflow.execute_activity(
                test_execution_activities.record_test_result,
                {
                    "cycle_id": input.cycle_id,
                    "report_id": input.report_id,
                    "test_result": test_result
                },
                start_to_close_timeout=timedelta(minutes=2)
            )
            
            results.append(test_result)
        
        # Calculate completion
        completion_result = await workflow.execute_activity(
            test_execution_activities.calculate_completion,
            {
                "cycle_id": input.cycle_id,
                "report_id": input.report_id,
                "results": results
            },
            start_to_close_timeout=timedelta(minutes=2)
        )
        
        # Complete SLA
        await workflow.execute_activity(
            sla_activities.complete_sla,
            {
                "entity_type": "workflow_phase",
                "entity_id": f"{input.cycle_id}_{input.report_id}_test_execution"
            },
            start_to_close_timeout=timedelta(seconds=30)
        )
        
        return PhaseResult(
            phase_name="Test Execution",
            status="completed",
            completed_at=workflow.now().isoformat(),
            result_data={
                "tests_executed": len(results),
                "pass_rate": completion_result.get("pass_rate", 0),
                "completion_percentage": completion_result.get("completion_percentage", 0)
            }
        )

@workflow.defn
class ObservationManagementWorkflow:
    """Observation Management phase workflow"""
    
    @workflow.run
    async def run(self, input: WorkflowInput) -> PhaseResult:
        """Execute observation management phase activities"""
        
        # Start SLA tracking
        await workflow.execute_activity(
            sla_activities.start_sla_tracking,
            {
                "entity_type": "workflow_phase",
                "entity_id": f"{input.cycle_id}_{input.report_id}_observations",
                "sla_hours": 72
            },
            start_to_close_timeout=timedelta(seconds=30)
        )
        
        # Create observations from test results
        observations = []
        test_results = input.metadata.get("test_results", [])
        
        for result in test_results:
            if result.get("status") == "failed":
                obs_result = await workflow.execute_activity(
                    observation_activities.create_observation,
                    {
                        "cycle_id": input.cycle_id,
                        "report_id": input.report_id,
                        "observation_data": result
                    },
                    start_to_close_timeout=timedelta(minutes=2)
                )
                observations.append(obs_result)
        
        # Group similar observations
        if observations:
            await workflow.execute_activity(
                observation_activities.group_observations,
                {
                    "cycle_id": input.cycle_id,
                    "report_id": input.report_id,
                    "observations": observations
                },
                start_to_close_timeout=timedelta(minutes=5)
            )
        
        # Wait for approval
        approval_signal = await workflow.wait_condition(
            lambda: workflow.info().is_signal_received("approve_observations"),
            timeout=timedelta(hours=48)
        )
        
        # Approve observations
        await workflow.execute_activity(
            observation_activities.approve_observations,
            {
                "cycle_id": input.cycle_id,
                "report_id": input.report_id,
                "approved_by": input.user_id
            },
            start_to_close_timeout=timedelta(minutes=2)
        )
        
        # Complete SLA
        await workflow.execute_activity(
            sla_activities.complete_sla,
            {
                "entity_type": "workflow_phase",
                "entity_id": f"{input.cycle_id}_{input.report_id}_observations"
            },
            start_to_close_timeout=timedelta(seconds=30)
        )
        
        return PhaseResult(
            phase_name="Observation Management",
            status="completed",
            completed_at=workflow.now().isoformat(),
            result_data={
                "observations_created": len(observations),
                "approved": True
            }
        )

@workflow.defn
class TestingReportWorkflow:
    """Testing Report phase workflow"""
    
    @workflow.run
    async def run(self, input: WorkflowInput) -> PhaseResult:
        """Execute testing report phase activities"""
        
        # Start SLA tracking
        await workflow.execute_activity(
            sla_activities.start_sla_tracking,
            {
                "entity_type": "workflow_phase",
                "entity_id": f"{input.cycle_id}_{input.report_id}_testing_report",
                "sla_hours": 48
            },
            start_to_close_timeout=timedelta(seconds=30)
        )
        
        # Generate report
        report_result = await workflow.execute_activity(
            report_activities.generate_report,
            {
                "cycle_id": input.cycle_id,
                "report_id": input.report_id,
                "template": input.metadata.get("report_template", "standard")
            },
            start_to_close_timeout=timedelta(minutes=10)
        )
        
        # Send for review
        await workflow.execute_activity(
            report_activities.review_report,
            {
                "cycle_id": input.cycle_id,
                "report_id": input.report_id,
                "report_data": report_result
            },
            start_to_close_timeout=timedelta(minutes=5)
        )
        
        # Wait for approval
        approval_signal = await workflow.wait_condition(
            lambda: workflow.info().is_signal_received("approve_report"),
            timeout=timedelta(hours=24)
        )
        
        # Finalize report
        final_report = await workflow.execute_activity(
            report_activities.finalize_report,
            {
                "cycle_id": input.cycle_id,
                "report_id": input.report_id,
                "format": input.metadata.get("export_format", "pdf")
            },
            start_to_close_timeout=timedelta(minutes=5)
        )
        
        # Complete SLA
        await workflow.execute_activity(
            sla_activities.complete_sla,
            {
                "entity_type": "workflow_phase",
                "entity_id": f"{input.cycle_id}_{input.report_id}_testing_report"
            },
            start_to_close_timeout=timedelta(seconds=30)
        )
        
        return PhaseResult(
            phase_name="Testing Report",
            status="completed",
            completed_at=workflow.now().isoformat(),
            result_data={
                "report_generated": True,
                "report_url": final_report.get("report_url"),
                "format": final_report.get("format")
            }
        )