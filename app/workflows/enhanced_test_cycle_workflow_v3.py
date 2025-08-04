"""
Enhanced Test Cycle Workflow V3 with Complete Versioning Integration
"""
from temporalio import workflow
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime, timedelta
import asyncio

from app.workflows.definitions.test_cycle import (
    TestCycleWorkflowInput,
    TestCycleWorkflowOutput,
    PhaseStatus,
    HumanInput
)
from app.workflows.activities.versioning_activities_complete import (
    PlanningActivities,
    DataProfilingActivities,
    ScopingActivities,
    SampleSelectionActivities,
    DataOwnerActivities,
    RequestInfoActivities,
    TestExecutionActivities,
    ObservationActivities,
    TestReportActivities
)


@workflow.defn
class EnhancedTestCycleWorkflowV3:
    """Test cycle workflow with complete versioning integration"""
    
    def __init__(self):
        # Phase tracking
        self.phase_versions: Dict[str, UUID] = {}
        self.phase_statuses: Dict[str, PhaseStatus] = {}
        self.pending_approvals: Dict[str, Any] = {}
        
        # Human input signals
        self.human_inputs: Dict[str, List[HumanInput]] = {}
        
        # Parallel execution tracking
        self.parallel_instances: Dict[str, List[Dict[str, Any]]] = {}
        
        # Workflow metadata
        self.cycle_id: Optional[int] = None
        self.report_id: Optional[int] = None
        self.user_id: Optional[int] = None
    
    @workflow.run
    async def run(self, input: TestCycleWorkflowInput) -> TestCycleWorkflowOutput:
        """Run the complete test cycle with versioning"""
        workflow.logger.info(f"Starting test cycle workflow for cycle {input.cycle_id}")
        
        # Initialize workflow state
        self.cycle_id = input.cycle_id
        self.report_id = input.report_id
        self.user_id = input.user_id
        
        try:
            # Sequential phases
            await self.run_planning_phase()
            await self.run_data_profiling_phase()
            await self.run_scoping_phase()
            
            # Parallel phases
            await asyncio.gather(
                self.run_sample_selection_phase(),
                self.run_data_owner_id_phase()
            )
            
            # Conditional parallel execution
            await self.run_parallel_downstream_phases()
            
            # Final phase (requires all observations complete)
            await self.wait_for_all_observations_complete()
            await self.run_finalize_test_report_phase()
            
            workflow.logger.info("Test cycle workflow completed successfully")
            
            return TestCycleWorkflowOutput(
                cycle_id=self.cycle_id,
                report_id=self.report_id,
                phase_versions=self.phase_versions,
                status="completed",
                completed_at=workflow.now()
            )
            
        except Exception as e:
            workflow.logger.error(f"Workflow failed: {str(e)}")
            raise
    
    # Phase 1: Planning
    async def run_planning_phase(self):
        """Run planning phase with auto-approval"""
        workflow.logger.info("Starting Planning phase")
        self.phase_statuses["Planning"] = PhaseStatus.IN_PROGRESS
        
        # Get planning attributes (from existing logic)
        attributes = await workflow.execute_activity(
            "get_planning_attributes",
            self.cycle_id,
            self.report_id,
            start_to_close_timeout=timedelta(minutes=10)
        )
        
        # Create version
        version_result = await workflow.execute_activity(
            PlanningActivities.create_planning_version,
            self.cycle_id,
            self.report_id,
            self.user_id,
            attributes,
            None,  # No parent version
            start_to_close_timeout=timedelta(minutes=5)
        )
        
        self.phase_versions["Planning"] = UUID(version_result["version_id"])
        
        # Auto-approve (tester approves their own work)
        await workflow.execute_activity(
            PlanningActivities.approve_planning_version,
            version_result["version_id"],
            self.user_id,
            "Auto-approved by tester",
            start_to_close_timeout=timedelta(minutes=2)
        )
        
        self.phase_statuses["Planning"] = PhaseStatus.COMPLETE
        workflow.logger.info("Planning phase completed")
    
    # Phase 2: Data Profiling
    async def run_data_profiling_phase(self):
        """Run data profiling with approval workflow"""
        workflow.logger.info("Starting Data Profiling phase")
        self.phase_statuses["Data Profiling"] = PhaseStatus.IN_PROGRESS
        
        # Generate profiling rules
        profiling_data = await workflow.execute_activity(
            "generate_profiling_rules",
            self.cycle_id,
            self.report_id,
            start_to_close_timeout=timedelta(minutes=30)
        )
        
        # Create version
        version_result = await workflow.execute_activity(
            DataProfilingActivities.create_profiling_version,
            self.cycle_id,
            self.report_id,
            self.user_id,
            profiling_data["rules"],
            profiling_data["source_data"],
            start_to_close_timeout=timedelta(minutes=5)
        )
        
        self.phase_versions["Data Profiling"] = UUID(version_result["version_id"])
        self.pending_approvals["Data Profiling"] = {
            "version_id": version_result["version_id"],
            "awaiting": "report_owner"
        }
        
        # Wait for approval
        await self.wait_for_approval("Data Profiling")
        
        self.phase_statuses["Data Profiling"] = PhaseStatus.COMPLETE
        workflow.logger.info("Data Profiling phase completed")
    
    # Phase 3: Scoping
    async def run_scoping_phase(self):
        """Run scoping phase with approval workflow"""
        workflow.logger.info("Starting Scoping phase")
        self.phase_statuses["Scoping"] = PhaseStatus.IN_PROGRESS
        
        # Generate scoping recommendations
        scoping_data = await workflow.execute_activity(
            "generate_scoping_recommendations",
            self.cycle_id,
            self.report_id,
            self.phase_versions["Planning"],
            start_to_close_timeout=timedelta(minutes=20)
        )
        
        # Create version
        version_result = await workflow.execute_activity(
            ScopingActivities.create_scoping_version,
            self.cycle_id,
            self.report_id,
            self.user_id,
            scoping_data["decisions"],
            scoping_data["criteria"],
            start_to_close_timeout=timedelta(minutes=5)
        )
        
        self.phase_versions["Scoping"] = UUID(version_result["version_id"])
        self.pending_approvals["Scoping"] = {
            "version_id": version_result["version_id"],
            "awaiting": "report_owner"
        }
        
        # Wait for approval
        await self.wait_for_approval("Scoping")
        
        self.phase_statuses["Scoping"] = PhaseStatus.COMPLETE
        workflow.logger.info("Scoping phase completed")
    
    # Phase 4: Sample Selection (Complex with revisions)
    async def run_sample_selection_phase(self):
        """Run sample selection with revision support"""
        workflow.logger.info("Starting Sample Selection phase")
        self.phase_statuses["Sample Selection"] = PhaseStatus.IN_PROGRESS
        
        # Generate initial samples
        samples_data = await workflow.execute_activity(
            "generate_sample_recommendations",
            self.cycle_id,
            self.report_id,
            start_to_close_timeout=timedelta(minutes=30)
        )
        
        # Create initial version
        version_result = await workflow.execute_activity(
            SampleSelectionActivities.create_sample_selection_version,
            self.cycle_id,
            self.report_id,
            self.user_id,
            samples_data["cycle_report_sample_selection_samples"],
            samples_data["criteria"],
            None,  # No parent version
            start_to_close_timeout=timedelta(minutes=10)
        )
        
        current_version_id = version_result["version_id"]
        self.phase_versions["Sample Selection"] = UUID(current_version_id)
        
        # Revision loop
        max_revisions = 3
        revision_count = 0
        approved = False
        
        while not approved and revision_count < max_revisions:
            # Wait for review
            workflow.logger.info(f"Waiting for sample selection review (version {revision_count + 1})")
            
            review_input = await self.wait_for_human_input("sample_selection_review")
            
            if review_input.data.get("approved"):
                # Process approval
                await workflow.execute_activity(
                    SampleSelectionActivities.approve_sample_selection,
                    current_version_id,
                    review_input.user_id,
                    review_input.data.get("notes"),
                    start_to_close_timeout=timedelta(minutes=5)
                )
                approved = True
                
            elif review_input.data.get("needs_revision"):
                # Process individual sample decisions
                if review_input.data.get("decisions"):
                    await workflow.execute_activity(
                        SampleSelectionActivities.process_sample_review,
                        current_version_id,
                        review_input.user_id,
                        review_input.data["decisions"],
                        start_to_close_timeout=timedelta(minutes=10)
                    )
                
                # Create revision with additional samples
                if review_input.data.get("additional_samples"):
                    revision_result = await workflow.execute_activity(
                        SampleSelectionActivities.create_sample_revision,
                        self.cycle_id,
                        self.report_id,
                        review_input.user_id,
                        current_version_id,
                        review_input.data["additional_samples"],
                        start_to_close_timeout=timedelta(minutes=10)
                    )
                    
                    current_version_id = revision_result["version_id"]
                    self.phase_versions["Sample Selection"] = UUID(current_version_id)
                    revision_count += 1
                else:
                    # No additional samples requested, just approve current
                    await workflow.execute_activity(
                        SampleSelectionActivities.approve_sample_selection,
                        current_version_id,
                        review_input.user_id,
                        "Approved after review",
                        start_to_close_timeout=timedelta(minutes=5)
                    )
                    approved = True
            else:
                # Rejection without revision
                raise workflow.ApplicationError(
                    "Sample selection rejected",
                    type="SampleSelectionRejected"
                )
        
        if not approved:
            raise workflow.ApplicationError(
                f"Max revisions ({max_revisions}) exceeded",
                type="MaxRevisionsExceeded"
            )
        
        self.phase_statuses["Sample Selection"] = PhaseStatus.COMPLETE
        workflow.logger.info("Sample Selection phase completed")
    
    # Phase 5: Data Owner ID (Parallel with Sample Selection)
    async def run_data_owner_id_phase(self):
        """Run data owner identification phase"""
        workflow.logger.info("Starting Data Owner ID phase")
        
        # Wait for sample selection to complete
        await workflow.wait_condition(
            lambda: self.phase_statuses.get("Sample Selection") == PhaseStatus.COMPLETE
        )
        
        self.phase_statuses["Data Owner ID"] = PhaseStatus.IN_PROGRESS
        
        # Get LOBs that need owners
        lobs = await workflow.execute_activity(
            "get_lobs_requiring_owners",
            self.cycle_id,
            self.report_id,
            start_to_close_timeout=timedelta(minutes=5)
        )
        
        # Track assignments
        self.parallel_instances["Data Owner ID"] = []
        
        for lob in lobs:
            # Wait for owner assignment signal
            assignment_input = await self.wait_for_human_input(
                f"data_owner_assignment_{lob['lob_id']}"
            )
            
            # Create assignment
            assignment_result = await workflow.execute_activity(
                DataOwnerActivities.assign_data_owner,
                self.cycle_id,
                self.report_id,
                lob["lob_id"],
                assignment_input.data["owner_id"],
                assignment_input.user_id,
                assignment_input.data.get("assignment_type", "primary"),
                start_to_close_timeout=timedelta(minutes=5)
            )
            
            self.parallel_instances["Data Owner ID"].append({
                "lob_id": lob["lob_id"],
                "owner_id": assignment_input.data["owner_id"],
                "assignment_id": assignment_result["assignment_id"]
            })
            
            # Trigger downstream phases for this LOB
            workflow.start_child_workflow(
                "process_lob_downstream_phases",
                args=[self.cycle_id, self.report_id, lob["lob_id"], 
                      assignment_input.data["owner_id"]],
                id=f"lob-{lob['lob_id']}-downstream"
            )
        
        self.phase_statuses["Data Owner ID"] = PhaseStatus.COMPLETE
        workflow.logger.info("Data Owner ID phase completed")
    
    # Parallel Downstream Phases
    async def run_parallel_downstream_phases(self):
        """Manage parallel execution of Request Info, Test Execution, and Observations"""
        
        # These run in parallel per LOB/owner
        # The child workflows handle the parallelism
        # Parent workflow tracks overall progress
        
        # Wait for all child workflows to complete
        await workflow.wait_condition(
            lambda: self.check_all_downstream_complete()
        )
    
    # Phase 9: Finalize Test Report
    async def run_finalize_test_report_phase(self):
        """Run test report finalization"""
        workflow.logger.info("Starting Finalize Test Report phase")
        self.phase_statuses["Finalize Test Report"] = PhaseStatus.IN_PROGRESS
        
        # Generate report data
        report_data = await workflow.execute_activity(
            "generate_test_report_data",
            self.cycle_id,
            self.report_id,
            start_to_close_timeout=timedelta(minutes=30)
        )
        
        # Create report version
        version_result = await workflow.execute_activity(
            TestReportActivities.create_report_version,
            self.cycle_id,
            self.report_id,
            self.user_id,
            report_data,
            start_to_close_timeout=timedelta(minutes=10)
        )
        
        self.phase_versions["Finalize Test Report"] = UUID(version_result["version_id"])
        
        # Collect sign-offs
        required_signoffs = ["test_lead", "test_executive", "report_owner"]
        
        for role in required_signoffs:
            signoff_input = await self.wait_for_human_input(f"report_signoff_{role}")
            
            await workflow.execute_activity(
                TestReportActivities.submit_report_signoff,
                version_result["version_id"],
                signoff_input.user_id,
                role,
                signoff_input.data.get("approved", False),
                signoff_input.data.get("comments"),
                start_to_close_timeout=timedelta(minutes=5)
            )
        
        self.phase_statuses["Finalize Test Report"] = PhaseStatus.COMPLETE
        workflow.logger.info("Finalize Test Report phase completed")
    
    # Helper Methods
    
    @workflow.signal
    async def submit_human_input(self, input: HumanInput):
        """Handle human input signals"""
        input_type = input.input_type
        
        if input_type not in self.human_inputs:
            self.human_inputs[input_type] = []
        
        self.human_inputs[input_type].append(input)
        workflow.logger.info(f"Received human input: {input_type}")
    
    async def wait_for_human_input(
        self,
        input_type: str,
        timeout: Optional[timedelta] = None
    ) -> HumanInput:
        """Wait for specific human input"""
        workflow.logger.info(f"Waiting for human input: {input_type}")
        
        def check_input():
            if input_type in self.human_inputs and self.human_inputs[input_type]:
                return self.human_inputs[input_type][-1]
            return None
        
        if timeout:
            try:
                await workflow.wait_condition(
                    lambda: check_input() is not None,
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                raise workflow.ApplicationError(
                    f"Timeout waiting for {input_type}",
                    type="HumanInputTimeout"
                )
        else:
            await workflow.wait_condition(
                lambda: check_input() is not None
            )
        
        return check_input()
    
    async def wait_for_approval(
        self,
        phase_name: str,
        timeout: Optional[timedelta] = None
    ) -> bool:
        """Wait for phase approval"""
        approval_input = await self.wait_for_human_input(
            f"{phase_name.lower().replace(' ', '_')}_approval",
            timeout
        )
        
        if approval_input.data.get("approved"):
            # Process approval based on phase
            if phase_name == "Data Profiling":
                await workflow.execute_activity(
                    DataProfilingActivities.process_profiling_review,
                    self.phase_versions[phase_name],
                    approval_input.user_id,
                    approval_input.data.get("rule_decisions", []),
                    start_to_close_timeout=timedelta(minutes=10)
                )
            
            return True
        
        return False
    
    async def wait_for_all_observations_complete(self):
        """Wait for all observation instances to complete"""
        workflow.logger.info("Waiting for all observations to complete")
        
        # In real implementation, this would check child workflow statuses
        await workflow.wait_condition(
            lambda: self.check_all_observations_approved()
        )
    
    def check_all_downstream_complete(self) -> bool:
        """Check if all downstream phases are complete"""
        # Implementation would check child workflow statuses
        return True
    
    def check_all_observations_approved(self) -> bool:
        """Check if all observations are approved"""
        # Implementation would query observation statuses
        return True
    
    # Workflow Queries
    
    @workflow.query
    def get_phase_statuses(self) -> Dict[str, str]:
        """Get current phase statuses"""
        return {
            phase: status.value 
            for phase, status in self.phase_statuses.items()
        }
    
    @workflow.query
    def get_phase_versions(self) -> Dict[str, str]:
        """Get current phase versions"""
        return {
            phase: str(version_id)
            for phase, version_id in self.phase_versions.items()
        }
    
    @workflow.query
    def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """Get pending approvals"""
        pending = []
        for phase, approval_info in self.pending_approvals.items():
            if phase not in self.phase_statuses or \
               self.phase_statuses[phase] != PhaseStatus.COMPLETE:
                pending.append({
                    "phase": phase,
                    "version_id": approval_info["version_id"],
                    "awaiting": approval_info.get("awaiting", "approval")
                })
        return pending
    
    @workflow.query
    def get_parallel_instances(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get parallel instance information"""
        return self.parallel_instances


# Child workflow for LOB-specific phases
@workflow.defn
class LOBDownstreamWorkflow:
    """Handle Request Info, Test Execution, and Observations for a specific LOB"""
    
    @workflow.run
    async def run(
        self,
        cycle_id: int,
        report_id: int,
        lob_id: str,
        owner_id: int
    ) -> Dict[str, Any]:
        """Run downstream phases for a LOB"""
        
        # Request Info phase
        await self.run_request_info_phase(cycle_id, report_id, lob_id, owner_id)
        
        # As documents are uploaded, trigger test execution
        # As tests complete, trigger observations
        
        return {
            "lob_id": lob_id,
            "status": "completed"
        }
    
    async def run_request_info_phase(
        self,
        cycle_id: int,
        report_id: int,
        lob_id: str,
        owner_id: int
    ):
        """Handle document requests and submissions"""
        # Wait for document submissions
        # Create document submission records
        # Trigger test execution as documents arrive
        pass