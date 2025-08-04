"""
Clean test cycle workflow with integrated versioning
No backward compatibility or dual-write logic
"""
from datetime import timedelta
from typing import Dict, Any, List, Optional
from temporalio import workflow
from temporalio.common import RetryPolicy
import uuid

from app.workflows.activities.versioning_activities_clean import VersioningActivities
from app.workflows.activities.test_activities import TestActivities
from app.workflows.signals import ApprovalSignal, RevisionSignal
from app.core.logger import logger


@workflow.defn
class CleanTestCycleWorkflow:
    """Clean workflow implementation with integrated versioning"""
    
    def __init__(self):
        self.cycle_id: Optional[int] = None
        self.report_id: Optional[int] = None
        self.workflow_id: str = str(uuid.uuid4())
        self.phase_status: Dict[str, str] = {}
        self.phase_versions: Dict[str, Dict[str, Any]] = {}
        self.approval_signals: List[ApprovalSignal] = []
        self.revision_signals: List[RevisionSignal] = []
        
        # Phase dependencies
        self.phase_dependencies = {
            "Planning": [],
            "Data Profiling": ["Planning"],
            "Scoping": ["Data Profiling"],
            "Sample Selection": ["Scoping"],
            "Data Owner ID": ["Sample Selection"],
            "Request Info": ["Data Owner ID"],
            "Test Execution": ["Request Info"],
            "Observation Management": ["Test Execution"],
            "Finalize Test Report": ["Observation Management"]
        }
        
        # Phases that can run in parallel per LOB
        self.parallel_phases = ["Data Owner ID", "Request Info", "Test Execution", "Observation Management"]
    
    @workflow.run
    async def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the clean test cycle workflow"""
        self.cycle_id = params["cycle_id"]
        self.report_id = params["report_id"]
        user_id = params["user_id"]
        lobs = params.get("lobs", [])
        
        logger.info(f"Starting clean workflow for cycle {self.cycle_id}, report {self.report_id}")
        
        try:
            # Sequential phases (1-4)
            await self._execute_planning_phase(user_id, params.get("planning_data", {}))
            await self._execute_data_profiling_phase(user_id, params.get("profiling_data", {}))
            await self._execute_scoping_phase(user_id, params.get("scoping_data", {}))
            await self._execute_sample_selection_phase(user_id, params.get("sample_data", {}))
            
            # Parallel phases per LOB (5-8)
            if lobs:
                await self._execute_parallel_lob_phases(user_id, lobs)
            
            # Final phase (9)
            await self._execute_report_finalization_phase(user_id, params.get("report_data", {}))
            
            return {
                "workflow_id": self.workflow_id,
                "cycle_id": self.cycle_id,
                "report_id": self.report_id,
                "status": "completed",
                "phase_versions": self.phase_versions
            }
            
        except Exception as e:
            logger.error(f"Workflow failed: {str(e)}")
            raise
    
    async def _execute_planning_phase(self, user_id: int, planning_data: Dict[str, Any]):
        """Execute planning phase with versioning"""
        logger.info("Executing Planning phase")
        
        # Create version
        version_result = await workflow.execute_activity(
            VersioningActivities.create_planning_version,
            {
                "cycle_id": self.cycle_id,
                "report_id": self.report_id,
                "user_id": user_id,
                "attributes": planning_data.get("attributes", []),
                "workflow_execution_id": workflow.info().workflow_id,
                "workflow_run_id": workflow.info().run_id
            },
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )
        
        self.phase_versions["Planning"] = version_result
        
        # Auto-approve for planning
        await workflow.execute_activity(
            VersioningActivities.approve_planning_version,
            {
                "version_id": version_result["version_id"],
                "approver_id": user_id,
                "workflow_execution_id": workflow.info().workflow_id
            },
            start_to_close_timeout=timedelta(minutes=2)
        )
        
        self.phase_status["Planning"] = "completed"
    
    async def _execute_data_profiling_phase(self, user_id: int, profiling_data: Dict[str, Any]):
        """Execute data profiling phase"""
        logger.info("Executing Data Profiling phase")
        
        # Create version
        version_result = await workflow.execute_activity(
            VersioningActivities.create_profiling_version,
            {
                "cycle_id": self.cycle_id,
                "report_id": self.report_id,
                "user_id": user_id,
                "source_files": profiling_data.get("files", []),
                "rules": profiling_data.get("rules", []),
                "workflow_execution_id": workflow.info().workflow_id,
                "workflow_run_id": workflow.info().run_id
            },
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )
        
        self.phase_versions["Data Profiling"] = version_result
        
        # Wait for approval signal
        await self._wait_for_approval("Data Profiling", version_result["version_id"])
        
        self.phase_status["Data Profiling"] = "completed"
    
    async def _execute_scoping_phase(self, user_id: int, scoping_data: Dict[str, Any]):
        """Execute scoping phase"""
        logger.info("Executing Scoping phase")
        
        # Create version
        version_result = await workflow.execute_activity(
            VersioningActivities.create_scoping_version,
            {
                "cycle_id": self.cycle_id,
                "report_id": self.report_id,
                "user_id": user_id,
                "scoping_decisions": scoping_data.get("decisions", []),
                "workflow_execution_id": workflow.info().workflow_id,
                "workflow_run_id": workflow.info().run_id
            },
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )
        
        self.phase_versions["Scoping"] = version_result
        
        # Wait for approval
        await self._wait_for_approval("Scoping", version_result["version_id"])
        
        self.phase_status["Scoping"] = "completed"
    
    async def _execute_sample_selection_phase(self, user_id: int, sample_data: Dict[str, Any]):
        """Execute sample selection with revision support"""
        logger.info("Executing Sample Selection phase")
        
        # Create initial version
        version_result = await workflow.execute_activity(
            VersioningActivities.create_sample_selection_version,
            {
                "cycle_id": self.cycle_id,
                "report_id": self.report_id,
                "user_id": user_id,
                "cycle_report_sample_selection_samples": sample_data.get("cycle_report_sample_selection_samples", []),
                "selection_criteria": sample_data.get("criteria", {}),
                "workflow_execution_id": workflow.info().workflow_id,
                "workflow_run_id": workflow.info().run_id
            },
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )
        
        current_version_id = version_result["version_id"]
        self.phase_versions["Sample Selection"] = version_result
        
        # Sample selection revision loop
        while True:
            # Wait for approval or revision signal
            signal_type = await self._wait_for_approval_or_revision(
                "Sample Selection", 
                current_version_id
            )
            
            if signal_type == "approved":
                break
            elif signal_type == "revision":
                # Get revision signal data
                revision_signal = self._get_latest_revision_signal("Sample Selection")
                
                # Create revision
                revision_result = await workflow.execute_activity(
                    VersioningActivities.create_sample_revision,
                    {
                        "cycle_id": self.cycle_id,
                        "report_id": self.report_id,
                        "user_id": revision_signal.user_id,
                        "parent_version_id": current_version_id,
                        "additional_samples": revision_signal.additional_data.get("cycle_report_sample_selection_samples", []),
                        "workflow_execution_id": workflow.info().workflow_id,
                        "workflow_run_id": workflow.info().run_id
                    },
                    start_to_close_timeout=timedelta(minutes=5),
                    retry_policy=RetryPolicy(maximum_attempts=3)
                )
                
                current_version_id = revision_result["version_id"]
                self.phase_versions["Sample Selection"] = revision_result
        
        self.phase_status["Sample Selection"] = "completed"
    
    async def _execute_parallel_lob_phases(self, user_id: int, lobs: List[Dict[str, Any]]):
        """Execute parallel phases for each LOB"""
        logger.info(f"Executing parallel phases for {len(lobs)} LOBs")
        
        # Start child workflows for each LOB
        child_handles = []
        
        for lob in lobs:
            handle = await workflow.start_child_workflow(
                LOBProcessingWorkflow.run,
                {
                    "cycle_id": self.cycle_id,
                    "report_id": self.report_id,
                    "lob_id": lob["lob_id"],
                    "lob_name": lob["name"],
                    "user_id": user_id,
                    "parent_workflow_id": self.workflow_id
                },
                id=f"lob-processing-{self.cycle_id}-{self.report_id}-{lob['lob_id']}",
                task_queue="versioning-queue"
            )
            child_handles.append(handle)
        
        # Wait for all LOB workflows to complete
        lob_results = []
        for handle in child_handles:
            result = await handle
            lob_results.append(result)
        
        # Aggregate LOB results
        for phase in self.parallel_phases:
            self.phase_status[phase] = "completed"
            self.phase_versions[phase] = {
                "lob_results": lob_results,
                "status": "completed"
            }
    
    async def _execute_report_finalization_phase(self, user_id: int, report_data: Dict[str, Any]):
        """Execute report finalization"""
        logger.info("Executing Finalize Test Report phase")
        
        # Create report version
        version_result = await workflow.execute_activity(
            VersioningActivities.create_report_version,
            {
                "cycle_id": self.cycle_id,
                "report_id": self.report_id,
                "user_id": user_id,
                "report_data": report_data,
                "workflow_execution_id": workflow.info().workflow_id,
                "workflow_run_id": workflow.info().run_id
            },
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )
        
        self.phase_versions["Finalize Test Report"] = version_result
        
        # Wait for all signoffs
        signoff_roles = ["test_lead", "test_executive", "report_owner"]
        for role in signoff_roles:
            await self._wait_for_signoff(version_result["version_id"], role)
        
        self.phase_status["Finalize Test Report"] = "completed"
    
    @workflow.signal
    async def approval_signal(self, signal: ApprovalSignal):
        """Handle approval signals"""
        self.approval_signals.append(signal)
    
    @workflow.signal
    async def revision_signal(self, signal: RevisionSignal):
        """Handle revision signals"""
        self.revision_signals.append(signal)
    
    async def _wait_for_approval(self, phase: str, version_id: str):
        """Wait for approval signal"""
        await workflow.wait_condition(
            lambda: any(
                s.phase == phase and s.version_id == version_id and s.approved 
                for s in self.approval_signals
            )
        )
    
    async def _wait_for_approval_or_revision(self, phase: str, version_id: str) -> str:
        """Wait for either approval or revision signal"""
        while True:
            # Check for approval
            if any(s.phase == phase and s.version_id == version_id and s.approved 
                   for s in self.approval_signals):
                return "approved"
            
            # Check for revision request
            if any(s.phase == phase and s.version_id == version_id 
                   for s in self.revision_signals):
                return "revision"
            
            await workflow.condition()
    
    async def _wait_for_signoff(self, version_id: str, role: str):
        """Wait for report signoff"""
        await workflow.wait_condition(
            lambda: any(
                s.phase == "Finalize Test Report" and 
                s.version_id == version_id and 
                s.metadata.get("signoff_role") == role and 
                s.approved
                for s in self.approval_signals
            )
        )
    
    def _get_latest_revision_signal(self, phase: str) -> RevisionSignal:
        """Get the latest revision signal for a phase"""
        phase_revisions = [s for s in self.revision_signals if s.phase == phase]
        return max(phase_revisions, key=lambda s: s.timestamp)
    
    @workflow.query
    def get_phase_status(self) -> Dict[str, str]:
        """Query current phase status"""
        return self.phase_status
    
    @workflow.query
    def get_phase_versions(self) -> Dict[str, Dict[str, Any]]:
        """Query phase version information"""
        return self.phase_versions


@workflow.defn
class LOBProcessingWorkflow:
    """Child workflow for LOB-specific processing"""
    
    @workflow.run
    async def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute LOB-specific phases"""
        cycle_id = params["cycle_id"]
        report_id = params["report_id"]
        lob_id = params["lob_id"]
        lob_name = params["lob_name"]
        user_id = params["user_id"]
        parent_workflow_id = params["parent_workflow_id"]
        
        logger.info(f"Processing LOB {lob_name} ({lob_id})")
        
        results = {}
        
        try:
            # Data Owner Assignment
            owner_result = await workflow.execute_activity(
                VersioningActivities.assign_data_owner,
                {
                    "cycle_id": cycle_id,
                    "report_id": report_id,
                    "lob_id": lob_id,
                    "data_owner_id": user_id,  # Would be determined by business logic
                    "assigned_by_id": user_id,
                    "workflow_execution_id": workflow.info().workflow_id
                },
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=RetryPolicy(maximum_attempts=3)
            )
            results["data_owner"] = owner_result
            
            # Request Info - Document submissions
            doc_result = await workflow.execute_activity(
                VersioningActivities.submit_document,
                {
                    "cycle_id": cycle_id,
                    "report_id": report_id,
                    "lob_id": lob_id,
                    "document_name": f"Test Evidence - {lob_name}",
                    "document_type": "test_evidence",
                    "document_path": f"/documents/{cycle_id}/{lob_id}/evidence.pdf",
                    "submitted_by_id": user_id,
                    "workflow_execution_id": workflow.info().workflow_id
                },
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=RetryPolicy(maximum_attempts=3)
            )
            results["documents"] = [doc_result]
            
            # Test Execution - Record test actions
            test_result = await workflow.execute_activity(
                VersioningActivities.record_test_action,
                {
                    "cycle_id": cycle_id,
                    "report_id": report_id,
                    "test_execution_id": 1,  # Would come from test execution
                    "action_type": "test_completed",
                    "action_details": {"lob": lob_name, "status": "passed"},
                    "requested_by_id": user_id,
                    "workflow_execution_id": workflow.info().workflow_id
                },
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=RetryPolicy(maximum_attempts=3)
            )
            results["test_execution"] = test_result
            
            # Observation Management would be handled similarly
            
            return {
                "lob_id": lob_id,
                "lob_name": lob_name,
                "status": "completed",
                "results": results
            }
            
        except Exception as e:
            logger.error(f"LOB processing failed for {lob_name}: {str(e)}")
            raise