"""Test Cycle Workflow - Reconciled with all human-in-the-loop activities

This workflow implements the complete 8-phase test cycle with proper
human interaction points using Temporal signals.
"""

from temporalio import workflow
from temporalio.common import RetryPolicy
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from datetime import timedelta
import asyncio

# Note: Activities are not imported directly in workflows
# They are executed using workflow.execute_activity with string names

# Note: Standard logging is not available in workflows
# Use workflow.logger instead


@dataclass
class TestCycleWorkflowInput:
    """Input for a single report workflow within a test cycle
    
    IMPORTANT: Each report in a test cycle gets its own workflow instance.
    For example, if a test cycle has 5 reports, there will be 5 separate
    workflow instances, each going through all 8 phases independently.
    """
    cycle_id: int
    report_id: int  # Single report ID - each report gets its own workflow
    user_id: int
    skip_phases: Optional[List[str]] = None


@dataclass
class HumanInput:
    """Generic human input data"""
    input_type: str
    data: Dict[str, Any]
    user_id: int
    timestamp: str


@workflow.defn
class TestCycleWorkflowReconciled:
    """
    Workflow for testing a single report through all 9 phases
    
    This workflow handles one report within a test cycle. Each report
    in a test cycle will have its own workflow instance running 
    independently through all 9 phases:
    
    1. Planning
    2. Data Profiling
    3. Scoping  
    4. Sample Selection (parallel with 5)
    5. Data Provider ID (parallel with 4)
    6. Request for Information
    7. Test Execution
    8. Observation Management
    9. Test Report Preparation
    """
    
    def __init__(self):
        # Planning phase signals
        self.planning_documents_ready = False
        self.planning_documents_data = None
        self.planning_attributes_ready = False
        self.planning_attributes_data = None
        
        # Data profiling phase signals
        self.data_profiling_tester_review_ready = False
        self.data_profiling_tester_review_data = None
        self.data_profiling_report_owner_approval_ready = False
        self.data_profiling_report_owner_approval_data = None
        
        # Scoping phase signals
        self.tester_review_complete = False
        self.tester_review_data = None
        self.report_owner_approval_complete = False
        self.report_owner_approval_data = None
        
        # Sample selection phase signals
        self.selection_criteria_ready = False
        self.selection_criteria_data = None
        self.sample_approval_ready = False
        self.sample_approval_data = None
        
        # Data provider phase signals
        self.dp_assignments_reviewed = False
        self.dp_assignments_data = None
        
        # Request info phase signals
        self.rfi_responses_ready = False
        self.rfi_responses_data = None
        
        # Test execution phase signals
        self.document_tests_complete = False
        self.document_tests_data = None
        self.database_tests_complete = False
        self.database_tests_data = None
        
        # Observation phase signals
        self.observations_created = False
        self.observations_data = None
        self.observations_reviewed = False
        self.observations_review_data = None
        
        # Test report phase signals
        self.report_reviewed = False
        self.report_review_data = None
        
        # Current phase tracking
        self.current_phase = None
        self.phase_results = {}
    
    # Signal handlers for all human interactions
    @workflow.signal
    async def submit_planning_documents(self, data: HumanInput):
        """Signal when planning documents are uploaded"""
        self.planning_documents_data = data.data
        self.planning_documents_ready = True
    
    @workflow.signal
    async def submit_planning_attributes(self, data: HumanInput):
        """Signal when attributes are created/imported"""
        self.planning_attributes_data = data.data
        self.planning_attributes_ready = True
    
    @workflow.signal
    async def submit_data_profiling_tester_review(self, data: HumanInput):
        """Signal when data profiling tester review is complete"""
        self.data_profiling_tester_review_data = data.data
        self.data_profiling_tester_review_ready = True
    
    @workflow.signal
    async def submit_data_profiling_report_owner_approval(self, data: HumanInput):
        """Signal when data profiling report owner approval is complete"""
        self.data_profiling_report_owner_approval_data = data.data
        self.data_profiling_report_owner_approval_ready = True
    
    @workflow.signal
    async def submit_tester_review(self, data: HumanInput):
        """Signal when tester completes attribute review"""
        self.tester_review_data = data.data
        self.tester_review_complete = True
    
    @workflow.signal
    async def submit_report_owner_approval(self, data: HumanInput):
        """Signal when report owner approves attributes"""
        self.report_owner_approval_data = data.data
        self.report_owner_approval_complete = True
    
    @workflow.signal
    async def submit_selection_criteria(self, data: HumanInput):
        """Signal when sample selection criteria defined"""
        self.selection_criteria_data = data.data
        self.selection_criteria_ready = True
    
    @workflow.signal
    async def submit_sample_approval(self, data: HumanInput):
        """Signal when samples are approved"""
        self.sample_approval_data = data.data
        self.sample_approval_ready = True
    
    @workflow.signal
    async def submit_dp_assignment_review(self, data: HumanInput):
        """Signal when data provider assignments reviewed"""
        self.dp_assignments_data = data.data
        self.dp_assignments_reviewed = True
    
    @workflow.signal
    async def submit_rfi_responses(self, data: HumanInput):
        """Signal to check/update RFI responses"""
        self.rfi_responses_data = data.data
        self.rfi_responses_ready = True
    
    @workflow.signal
    async def submit_document_tests(self, data: HumanInput):
        """Signal when document tests complete"""
        self.document_tests_data = data.data
        self.document_tests_complete = True
    
    @workflow.signal
    async def submit_database_tests(self, data: HumanInput):
        """Signal when database tests complete"""
        self.database_tests_data = data.data
        self.database_tests_complete = True
    
    @workflow.signal
    async def submit_observations(self, data: HumanInput):
        """Signal when observations created"""
        self.observations_data = data.data
        self.observations_created = True
    
    @workflow.signal
    async def submit_observation_review(self, data: HumanInput):
        """Signal when observations reviewed"""
        self.observations_review_data = data.data
        self.observations_reviewed = True
    
    @workflow.signal
    async def submit_report_review(self, data: HumanInput):
        """Signal when report reviewed/edited"""
        self.report_review_data = data.data
        self.report_reviewed = True
    
    # Query handlers
    @workflow.query
    def get_current_status(self) -> Dict[str, Any]:
        """Get current workflow status"""
        workflow_status = "in_progress"
        if self.current_phase == "Preparing Test Report" and "Preparing Test Report" in self.phase_results:
            workflow_status = "completed"
        elif any("failed" in str(result).lower() for result in self.phase_results.values()):
            workflow_status = "failed"
            
        return {
            "current_phase": self.current_phase,
            "awaiting_action": self.get_awaiting_action(),
            "phase_results": self.phase_results,
            "workflow_status": workflow_status
        }
    
    @workflow.query
    def get_awaiting_action(self) -> Optional[str]:
        """Get what action the workflow is waiting for"""
        if self.current_phase == "Planning":
            if not self.planning_documents_ready:
                return "upload_planning_documents"
            elif not self.planning_attributes_ready:
                return "create_planning_attributes"
        elif self.current_phase == "Scoping":
            if not self.tester_review_complete:
                return "tester_review_attributes"
            elif not self.report_owner_approval_complete:
                return "report_owner_approval"
        elif self.current_phase == "Sample Selection":
            if not self.selection_criteria_ready:
                return "define_selection_criteria"
            elif not self.sample_approval_ready:
                return "approve_samples"
        elif self.current_phase == "Data Provider ID":
            if not self.dp_assignments_reviewed:
                return "review_data_provider_assignments"
        # Handle parallel phases - check both Sample Selection and Data Provider ID
        elif self.current_phase == "Sample Selection" and "Sample Selection" not in self.phase_results:
            if not self.selection_criteria_ready:
                return "define_selection_criteria"
            elif not self.sample_approval_ready:
                return "approve_samples"
        # Also check Data Provider ID when in Sample Selection phase (parallel execution)
        if self.current_phase == "Sample Selection" and "Data Provider ID" not in self.phase_results:
            if not self.dp_assignments_reviewed:
                return "review_data_provider_assignments"
        elif self.current_phase == "Request Info":
            if not self.rfi_responses_ready:
                return "track_rfi_responses"
        elif self.current_phase == "Testing":
            if not self.document_tests_complete:
                return "execute_document_tests"
            elif not self.database_tests_complete:
                return "execute_database_tests"
        elif self.current_phase == "Observations":
            if not self.observations_created:
                return "create_observations"
            elif not self.observations_reviewed:
                return "review_observations"
        elif self.current_phase == "Preparing Test Report":
            if not self.report_reviewed:
                return "review_report"
        return None
    
    @workflow.run
    async def run(self, input_data: TestCycleWorkflowInput) -> Dict[str, Any]:
        """Execute the complete test cycle workflow"""
        
        # Default retry policy
        retry_policy = RetryPolicy(
            maximum_attempts=3,
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=30),
            backoff_coefficient=2
        )
        
        try:
            workflow.logger.info(f"Starting workflow for cycle {input_data.cycle_id}, report {input_data.report_id}")
            
            # Phase 1: Planning
            if not input_data.skip_phases or "Planning" not in input_data.skip_phases:
                self.current_phase = "Planning"
                workflow.logger.info("Executing Planning phase...")
                planning_result = await self.execute_planning_phase(
                    input_data, retry_policy
                )
                self.phase_results["Planning"] = planning_result
                workflow.logger.info(f"Planning phase result: {planning_result}")
            
            # Phase 2: Data Profiling
            if not input_data.skip_phases or "Data Profiling" not in input_data.skip_phases:
                self.current_phase = "Data Profiling"
                workflow.logger.info("Executing Data Profiling phase...")
                data_profiling_result = await self.execute_data_profiling_phase(
                    input_data, retry_policy
                )
                self.phase_results["Data Profiling"] = data_profiling_result
                workflow.logger.info(f"Data Profiling phase result: {data_profiling_result}")
            
            # Phase 3: Scoping
            if not input_data.skip_phases or "Scoping" not in input_data.skip_phases:
                self.current_phase = "Scoping"
                workflow.logger.info("Executing Scoping phase...")
                scoping_result = await self.execute_scoping_phase(
                    input_data, retry_policy
                )
                self.phase_results["Scoping"] = scoping_result
                workflow.logger.info(f"Scoping phase result: {scoping_result}")
            
            # Phases 4 & 5: Sample Selection and Data Provider ID (Parallel)
            parallel_futures = []
            
            # Set current phase to indicate parallel execution
            self.current_phase = "Sample Selection"  # Will be updated during execution
            
            if not input_data.skip_phases or "Sample Selection" not in input_data.skip_phases:
                parallel_futures.append(
                    self.execute_sample_selection_phase(input_data, retry_policy)
                )
            
            if not input_data.skip_phases or "Data Provider ID" not in input_data.skip_phases:
                parallel_futures.append(
                    self.execute_data_provider_phase(input_data, retry_policy)
                )
            
            if parallel_futures:
                parallel_results = await asyncio.gather(*parallel_futures)
                if len(parallel_results) > 0:
                    self.phase_results["Sample Selection"] = parallel_results[0]
                if len(parallel_results) > 1:
                    self.phase_results["Data Provider ID"] = parallel_results[1]
            
            # Phase 5: Request for Information
            if not input_data.skip_phases or "Request Info" not in input_data.skip_phases:
                self.current_phase = "Request Info"
                rfi_result = await self.execute_request_info_phase(
                    input_data, retry_policy
                )
                self.phase_results["Request Info"] = rfi_result
            
            # Phase 6: Test Execution
            if not input_data.skip_phases or "Testing" not in input_data.skip_phases:
                self.current_phase = "Testing"
                testing_result = await self.execute_testing_phase(
                    input_data, retry_policy
                )
                self.phase_results["Testing"] = testing_result
            
            # Phase 7: Observation Management
            if not input_data.skip_phases or "Observations" not in input_data.skip_phases:
                self.current_phase = "Observations"
                observation_result = await self.execute_observations_phase(
                    input_data, retry_policy
                )
                self.phase_results["Observations"] = observation_result
            
            # Phase 8: Preparing Test Report
            if not input_data.skip_phases or "Preparing Test Report" not in input_data.skip_phases:
                self.current_phase = "Preparing Test Report"
                report_result = await self.execute_test_report_phase(
                    input_data, retry_policy
                )
                self.phase_results["Preparing Test Report"] = report_result
            
            return {
                "status": "completed",
                "cycle_id": input_data.cycle_id,
                "report_id": input_data.report_id,
                "phases_completed": list(self.phase_results.keys()),
                "phase_results": self.phase_results
            }
            
        except Exception as e:
            workflow.logger.error(f"Workflow failed: {str(e)}")
            workflow.logger.error(f"Completed phases before failure: {list(self.phase_results.keys())}")
            import traceback
            workflow.logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                "status": "failed",
                "error": str(e),
                "completed_phases": list(self.phase_results.keys()),
                "current_phase": self.current_phase
            }
    
    async def execute_planning_phase(
        self,
        input_data: TestCycleWorkflowInput,
        retry_policy: RetryPolicy
    ) -> Dict[str, Any]:
        """Execute planning phase with human interactions"""
        
        # Step 1: Start planning phase
        start_result = await workflow.execute_activity(
            "start_planning_phase_activity",
            args=[input_data.cycle_id, input_data.report_id, input_data.user_id],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy
        )
        
        # Step 2: Wait for document uploads
        await workflow.execute_activity(
            "upload_planning_documents_activity",
            args=[input_data.cycle_id, input_data.report_id, input_data.user_id, None],
            start_to_close_timeout=timedelta(minutes=5)
        )
        
        await workflow.wait_condition(lambda: self.planning_documents_ready)
        
        doc_result = await workflow.execute_activity(
            "upload_planning_documents_activity",
            args=[
                input_data.cycle_id,
                input_data.report_id,
                input_data.user_id,
                self.planning_documents_data
            ],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy
        )
        
        # Step 3: Wait for attribute creation
        await workflow.execute_activity(
            "import_create_attributes_activity",
            args=[input_data.cycle_id, input_data.report_id, input_data.user_id, None],
            start_to_close_timeout=timedelta(minutes=5)
        )
        
        await workflow.wait_condition(lambda: self.planning_attributes_ready)
        
        attr_result = await workflow.execute_activity(
            "import_create_attributes_activity",
            args=[
                input_data.cycle_id,
                input_data.report_id,
                input_data.user_id,
                self.planning_attributes_data
            ],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy
        )
        
        # Step 4: Review checklist
        checklist_result = await workflow.execute_activity(
            "review_planning_checklist_activity",
            args=[input_data.cycle_id, input_data.report_id, input_data.user_id],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy
        )
        
        # Step 5: Complete planning phase
        complete_result = await workflow.execute_activity(
            "complete_planning_phase_activity",
            args=[
                input_data.cycle_id,
                input_data.report_id,
                input_data.user_id,
                checklist_result['data']
            ],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy
        )
        
        return complete_result
    
    async def execute_data_profiling_phase(
        self,
        input_data: TestCycleWorkflowInput,
        retry_policy: RetryPolicy
    ) -> Dict[str, Any]:
        """Execute data profiling phase with human interactions"""
        
        # Step 1: Start data profiling phase
        start_result = await workflow.execute_activity(
            "start_data_profiling_phase_activity",
            args=[input_data.cycle_id, input_data.report_id, input_data.user_id],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy
        )
        
        # Step 2: Generate profiling rules (LLM)
        rules_result = await workflow.execute_activity(
            "generate_profiling_rules_activity",
            args=[input_data.cycle_id, input_data.report_id, input_data.user_id, None],
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=retry_policy
        )
        
        # Step 3: Apply profiling rules
        apply_result = await workflow.execute_activity(
            "apply_profiling_rules_activity",
            args=[input_data.cycle_id, input_data.report_id, input_data.user_id, None],
            start_to_close_timeout=timedelta(minutes=15),
            retry_policy=retry_policy
        )
        
        # Step 4: Analyze profiling results
        analyze_result = await workflow.execute_activity(
            "analyze_profiling_results_activity",
            args=[input_data.cycle_id, input_data.report_id, input_data.user_id, None],
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=retry_policy
        )
        
        # Step 5: Wait for tester review
        await workflow.execute_activity(
            "data_profiling_tester_review_activity",
            args=[input_data.cycle_id, input_data.report_id, input_data.user_id, None],
            start_to_close_timeout=timedelta(minutes=5)
        )
        
        await workflow.wait_condition(lambda: self.data_profiling_tester_review_ready)
        
        tester_review_result = await workflow.execute_activity(
            "data_profiling_tester_review_activity",
            args=[
                input_data.cycle_id,
                input_data.report_id,
                input_data.user_id,
                {"review_data": self.data_profiling_tester_review_data}
            ],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy
        )
        
        # Step 6: Wait for report owner approval
        await workflow.execute_activity(
            "data_profiling_report_owner_approval_activity",
            args=[input_data.cycle_id, input_data.report_id, input_data.user_id, None],
            start_to_close_timeout=timedelta(minutes=5)
        )
        
        await workflow.wait_condition(lambda: self.data_profiling_report_owner_approval_ready)
        
        approval_result = await workflow.execute_activity(
            "data_profiling_report_owner_approval_activity",
            args=[
                input_data.cycle_id,
                input_data.report_id,
                input_data.user_id,
                {"approval_data": self.data_profiling_report_owner_approval_data}
            ],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy
        )
        
        # Step 7: Complete data profiling phase
        complete_result = await workflow.execute_activity(
            "complete_data_profiling_phase_activity",
            args=[input_data.cycle_id, input_data.report_id, input_data.user_id],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy
        )
        
        return complete_result
    
    # ... (implement other phase methods following the same pattern)
    
    async def execute_scoping_phase(
        self,
        input_data: TestCycleWorkflowInput,
        retry_policy: RetryPolicy
    ) -> Dict[str, Any]:
        """Execute scoping phase with tester review and report owner approval"""
        
        # Step 1: Start scoping phase
        start_result = await workflow.execute_activity(
            "start_scoping_phase_activity",
            args=[input_data.cycle_id, input_data.report_id, input_data.user_id],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy
        )
        
        # Step 2: Generate LLM recommendations
        llm_result = await workflow.execute_activity(
            "generate_llm_recommendations_activity",
            args=[input_data.cycle_id, input_data.report_id, input_data.user_id],
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=retry_policy
        )
        
        # Step 3: Wait for tester review
        await workflow.execute_activity(
            "tester_review_attributes_activity",
            args=[input_data.cycle_id, input_data.report_id, input_data.user_id, None],
            start_to_close_timeout=timedelta(minutes=5)
        )
        
        await workflow.wait_condition(lambda: self.tester_review_complete)
        
        review_result = await workflow.execute_activity(
            "tester_review_attributes_activity",
            args=[
                input_data.cycle_id,
                input_data.report_id,
                input_data.user_id,
                self.tester_review_data
            ],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy
        )
        
        # Step 4: Wait for report owner approval
        if review_result['data'].get('requires_report_owner_approval'):
            await workflow.execute_activity(
                "report_owner_approval_activity",
                args=[input_data.cycle_id, input_data.report_id, input_data.user_id, None],
                start_to_close_timeout=timedelta(minutes=5)
            )
            
            await workflow.wait_condition(lambda: self.report_owner_approval_complete)
            
            approval_result = await workflow.execute_activity(
                "report_owner_approval_activity",
                args=[
                    input_data.cycle_id,
                    input_data.report_id,
                    input_data.user_id,
                    self.report_owner_approval_data
                ],
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=retry_policy
            )
        
        # Step 5: Complete scoping phase
        complete_result = await workflow.execute_activity(
            "complete_scoping_phase_activity",
            args=[
                input_data.cycle_id,
                input_data.report_id,
                input_data.user_id,
                {
                    'llm_result': llm_result,
                    'review_result': review_result,
                    'approval_result': approval_result if 'approval_result' in locals() else None
                }
            ],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy
        )
        
        return complete_result
    
    async def execute_sample_selection_phase(
        self,
        input_data: TestCycleWorkflowInput,
        retry_policy: RetryPolicy
    ) -> Dict[str, Any]:
        """Execute sample selection phase"""
        # Step 1: Start sample selection phase
        start_result = await workflow.execute_activity(
            "start_sample_selection_phase_activity",
            args=[input_data.cycle_id, input_data.report_id, input_data.user_id],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy
        )
        
        # Step 2: Define selection criteria (wait for human input)
        await workflow.execute_activity(
            "define_selection_criteria_activity",
            args=[input_data.cycle_id, input_data.report_id, input_data.user_id, None],
            start_to_close_timeout=timedelta(minutes=5)
        )
        
        await workflow.wait_condition(lambda: self.selection_criteria_ready)
        
        criteria_result = await workflow.execute_activity(
            "define_selection_criteria_activity",
            args=[
                input_data.cycle_id,
                input_data.report_id,
                input_data.user_id,
                self.selection_criteria_data
            ],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy
        )
        
        # Step 3: Generate sample sets
        generate_result = await workflow.execute_activity(
            "generate_sample_sets_activity",
            args=[input_data.cycle_id, input_data.report_id, input_data.user_id],
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=retry_policy
        )
        
        # Step 4: Review and approve samples (wait for human input)
        await workflow.execute_activity(
            "review_approve_samples_activity",
            args=[input_data.cycle_id, input_data.report_id, input_data.user_id, None],
            start_to_close_timeout=timedelta(minutes=5)
        )
        
        await workflow.wait_condition(lambda: self.sample_approval_ready)
        
        approval_result = await workflow.execute_activity(
            "review_approve_samples_activity",
            args=[
                input_data.cycle_id,
                input_data.report_id,
                input_data.user_id,
                self.sample_approval_data
            ],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy
        )
        
        # Step 5: Complete sample selection phase
        complete_result = await workflow.execute_activity(
            "complete_sample_selection_phase_activity",
            args=[
                input_data.cycle_id,
                input_data.report_id,
                input_data.user_id,
                {
                    'criteria_result': criteria_result,
                    'generate_result': generate_result,
                    'approval_result': approval_result
                }
            ],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy
        )
        
        return complete_result
    
    async def execute_data_provider_phase(
        self,
        input_data: TestCycleWorkflowInput,
        retry_policy: RetryPolicy
    ) -> Dict[str, Any]:
        """Execute data provider identification phase"""
        # Step 1: Start data provider phase
        start_result = await workflow.execute_activity(
            "start_data_provider_phase_activity",
            args=[input_data.cycle_id, input_data.report_id, input_data.user_id],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy
        )
        
        # Step 2: Auto-assign data providers
        assign_result = await workflow.execute_activity(
            "auto_assign_data_providers_activity",
            args=[input_data.cycle_id, input_data.report_id, input_data.user_id],
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=retry_policy
        )
        
        # Step 3: Review data provider assignments (wait for human input)
        await workflow.execute_activity(
            "review_data_provider_assignments_activity",
            args=[input_data.cycle_id, input_data.report_id, input_data.user_id, None],
            start_to_close_timeout=timedelta(minutes=5)
        )
        
        await workflow.wait_condition(lambda: self.dp_assignments_reviewed)
        
        review_result = await workflow.execute_activity(
            "review_data_provider_assignments_activity",
            args=[
                input_data.cycle_id,
                input_data.report_id,
                input_data.user_id,
                self.dp_assignments_data
            ],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy
        )
        
        # Step 4: Send notifications to data providers
        notify_result = await workflow.execute_activity(
            "send_data_provider_notifications_activity",
            args=[input_data.cycle_id, input_data.report_id, input_data.user_id],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy
        )
        
        # Step 5: Complete data provider phase
        complete_result = await workflow.execute_activity(
            "complete_data_provider_phase_activity",
            args=[
                input_data.cycle_id,
                input_data.report_id,
                input_data.user_id,
                {
                    'assign_result': assign_result,
                    'review_result': review_result,
                    'notify_result': notify_result
                }
            ],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy
        )
        
        return complete_result
    
    async def execute_request_info_phase(
        self,
        input_data: TestCycleWorkflowInput,
        retry_policy: RetryPolicy
    ) -> Dict[str, Any]:
        """Execute request for information phase"""
        # Step 1: Start request info phase
        start_result = await workflow.execute_activity(
            "start_request_info_phase_activity",
            args=[input_data.cycle_id, input_data.report_id, input_data.user_id],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy
        )
        
        # Step 2: Generate test cases
        test_cases_result = await workflow.execute_activity(
            "generate_test_cases_activity",
            args=[input_data.cycle_id, input_data.report_id, input_data.user_id],
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=retry_policy
        )
        
        # Step 3: Create information requests
        create_requests_result = await workflow.execute_activity(
            "create_information_requests_activity",
            args=[input_data.cycle_id, input_data.report_id, input_data.user_id],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy
        )
        
        # Step 4: Send RFI emails
        send_emails_result = await workflow.execute_activity(
            "send_rfi_emails_activity",
            args=[input_data.cycle_id, input_data.report_id, input_data.user_id],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy
        )
        
        # Step 5: Track RFI responses (wait for human input)
        await workflow.execute_activity(
            "track_rfi_responses_activity",
            args=[input_data.cycle_id, input_data.report_id, input_data.user_id, None],
            start_to_close_timeout=timedelta(minutes=5)
        )
        
        await workflow.wait_condition(lambda: self.rfi_responses_ready)
        
        track_result = await workflow.execute_activity(
            "track_rfi_responses_activity",
            args=[
                input_data.cycle_id,
                input_data.report_id,
                input_data.user_id,
                self.rfi_responses_data
            ],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy
        )
        
        # Step 6: Complete request info phase
        complete_result = await workflow.execute_activity(
            "complete_request_info_phase_activity",
            args=[
                input_data.cycle_id,
                input_data.report_id,
                input_data.user_id,
                {
                    'test_cases_result': test_cases_result,
                    'create_requests_result': create_requests_result,
                    'send_emails_result': send_emails_result,
                    'track_result': track_result
                }
            ],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy
        )
        
        return complete_result
    
    async def execute_testing_phase(
        self,
        input_data: TestCycleWorkflowInput,
        retry_policy: RetryPolicy
    ) -> Dict[str, Any]:
        """Execute testing phase"""
        # Step 1: Start test execution phase
        start_result = await workflow.execute_activity(
            "start_test_execution_phase_activity",
            args=[input_data.cycle_id, input_data.report_id, input_data.user_id],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy
        )
        
        # Step 2: Create test execution records
        create_records_result = await workflow.execute_activity(
            "create_test_execution_records_activity",
            args=[input_data.cycle_id, input_data.report_id, input_data.user_id],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy
        )
        
        # Step 3: Execute document tests (wait for human input)
        await workflow.execute_activity(
            "execute_document_tests_activity",
            args=[input_data.cycle_id, input_data.report_id, input_data.user_id, None],
            start_to_close_timeout=timedelta(minutes=5)
        )
        
        await workflow.wait_condition(lambda: self.document_tests_complete)
        
        doc_test_result = await workflow.execute_activity(
            "execute_document_tests_activity",
            args=[
                input_data.cycle_id,
                input_data.report_id,
                input_data.user_id,
                self.document_tests_data
            ],
            start_to_close_timeout=timedelta(minutes=30),
            retry_policy=retry_policy
        )
        
        # Step 4: Execute database tests (wait for human input)
        await workflow.execute_activity(
            "execute_database_tests_activity",
            args=[input_data.cycle_id, input_data.report_id, input_data.user_id, None],
            start_to_close_timeout=timedelta(minutes=5)
        )
        
        await workflow.wait_condition(lambda: self.database_tests_complete)
        
        db_test_result = await workflow.execute_activity(
            "execute_database_tests_activity",
            args=[
                input_data.cycle_id,
                input_data.report_id,
                input_data.user_id,
                self.database_tests_data
            ],
            start_to_close_timeout=timedelta(minutes=30),
            retry_policy=retry_policy
        )
        
        # Step 5: Record test results
        record_result = await workflow.execute_activity(
            "record_test_results_activity",
            args=[
                input_data.cycle_id,
                input_data.report_id,
                input_data.user_id
            ],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy
        )
        
        # Step 6: Generate test summary
        summary_result = await workflow.execute_activity(
            "generate_test_summary_activity",
            args=[input_data.cycle_id, input_data.report_id, input_data.user_id],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy
        )
        
        # Step 7: Complete test execution phase
        complete_result = await workflow.execute_activity(
            "complete_test_execution_phase_activity",
            args=[
                input_data.cycle_id,
                input_data.report_id,
                input_data.user_id,
                {
                    'create_records_result': create_records_result,
                    'doc_test_result': doc_test_result,
                    'db_test_result': db_test_result,
                    'record_result': record_result,
                    'summary_result': summary_result
                }
            ],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy
        )
        
        return complete_result
    
    async def execute_observations_phase(
        self,
        input_data: TestCycleWorkflowInput,
        retry_policy: RetryPolicy
    ) -> Dict[str, Any]:
        """Execute observations phase"""
        # Step 1: Start observation phase
        start_result = await workflow.execute_activity(
            "start_observation_phase_activity",
            args=[input_data.cycle_id, input_data.report_id, input_data.user_id],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy
        )
        
        # Step 2: Create observations (wait for human input)
        await workflow.execute_activity(
            "create_observations_activity",
            args=[input_data.cycle_id, input_data.report_id, input_data.user_id, None],
            start_to_close_timeout=timedelta(minutes=5)
        )
        
        await workflow.wait_condition(lambda: self.observations_created)
        
        create_obs_result = await workflow.execute_activity(
            "create_observations_activity",
            args=[
                input_data.cycle_id,
                input_data.report_id,
                input_data.user_id,
                self.observations_data
            ],
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=retry_policy
        )
        
        # Step 3: Auto-group observations
        group_result = await workflow.execute_activity(
            "auto_group_observations_activity",
            args=[input_data.cycle_id, input_data.report_id, input_data.user_id],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy
        )
        
        # Step 4: Review and approve observations (wait for human input)
        await workflow.execute_activity(
            "review_approve_observations_activity",
            args=[input_data.cycle_id, input_data.report_id, input_data.user_id, None],
            start_to_close_timeout=timedelta(minutes=5)
        )
        
        await workflow.wait_condition(lambda: self.observations_reviewed)
        
        review_result = await workflow.execute_activity(
            "review_approve_observations_activity",
            args=[
                input_data.cycle_id,
                input_data.report_id,
                input_data.user_id,
                self.observations_review_data
            ],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy
        )
        
        # Step 5: Generate impact assessment
        impact_result = await workflow.execute_activity(
            "generate_impact_assessment_activity",
            args=[input_data.cycle_id, input_data.report_id, input_data.user_id],
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=retry_policy
        )
        
        # Step 6: Complete observation phase
        complete_result = await workflow.execute_activity(
            "complete_observation_phase_activity",
            args=[
                input_data.cycle_id,
                input_data.report_id,
                input_data.user_id,
                {
                    'create_obs_result': create_obs_result,
                    'group_result': group_result,
                    'review_result': review_result,
                    'impact_result': impact_result
                }
            ],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy
        )
        
        return complete_result
    
    async def execute_test_report_phase(
        self,
        input_data: TestCycleWorkflowInput,
        retry_policy: RetryPolicy
    ) -> Dict[str, Any]:
        """Execute test report preparation phase"""
        # Step 1: Start test report phase
        start_result = await workflow.execute_activity(
            "start_test_report_phase_activity",
            args=[input_data.cycle_id, input_data.report_id, input_data.user_id],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy
        )
        
        # Step 2: Generate report sections
        sections_result = await workflow.execute_activity(
            "generate_report_sections_activity",
            args=[input_data.cycle_id, input_data.report_id, input_data.user_id],
            start_to_close_timeout=timedelta(minutes=15),
            retry_policy=retry_policy
        )
        
        # Step 3: Generate executive summary
        summary_result = await workflow.execute_activity(
            "generate_executive_summary_activity",
            args=[input_data.cycle_id, input_data.report_id, input_data.user_id],
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=retry_policy
        )
        
        # Step 4: Review and edit report (wait for human input)
        await workflow.execute_activity(
            "review_edit_report_activity",
            args=[input_data.cycle_id, input_data.report_id, input_data.user_id, None],
            start_to_close_timeout=timedelta(minutes=5)
        )
        
        await workflow.wait_condition(lambda: self.report_reviewed)
        
        review_result = await workflow.execute_activity(
            "review_edit_report_activity",
            args=[
                input_data.cycle_id,
                input_data.report_id,
                input_data.user_id,
                self.report_review_data
            ],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy
        )
        
        # Step 5: Finalize report
        finalize_result = await workflow.execute_activity(
            "finalize_report_activity",
            args=[input_data.cycle_id, input_data.report_id, input_data.user_id],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy
        )
        
        # Step 6: Complete test report phase
        complete_result = await workflow.execute_activity(
            "complete_test_report_phase_activity",
            args=[
                input_data.cycle_id,
                input_data.report_id,
                input_data.user_id,
                {
                    'sections_result': sections_result,
                    'summary_result': summary_result,
                    'review_result': review_result,
                    'finalize_result': finalize_result
                }
            ],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy
        )
        
        return complete_result