"""Base metrics calculation engine for SynapseDTE."""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.test_cycle import TestCycle
from app.models.report import Report
from app.models.report_attribute import ReportAttribute
from app.models.workflow_tracking import WorkflowPhase, WorkflowStep
from app.models.test_scoping import ScopedReportAttribute
from app.models.sample_selection import SampleSet, CycleReportSampleSelectionSamples
from app.models.lob_assignment import LOBAssignment
from app.models.test_planning import TestPlan
from app.models.test_execution import TestExecution
from app.models.observations import Observation
from app.core.enums import WorkflowPhaseState, ScheduleStatus


class BaseMetricsCalculator:
    """Base class for calculating metrics across the SynapseDTE system."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def aggregate_report_metrics(
        self,
        cycle_id: str,
        report_id: Optional[str] = None,
        lob_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calculate aggregate metrics for a report or all reports in a cycle."""
        metrics = {
            "total_reports": 0,
            "reports_completed": 0,
            "reports_in_progress": 0,
            "reports_not_started": 0,
            "total_attributes": 0,
            "attributes_approved": 0,
            "observations_confirmed": 0,
            "overall_completion_percentage": 0.0
        }
        
        # Build query
        query = select(WorkflowPhase).where(WorkflowPhase.cycle_id == cycle_id)
        if report_id:
            query = query.where(WorkflowPhase.report_id == report_id)
        
        result = await self.db.execute(query)
        phases = result.scalars().all()
        
        # Group by report
        reports_data = {}
        for phase in phases:
            if phase.report_id not in reports_data:
                reports_data[phase.report_id] = {"phases": []}
            reports_data[phase.report_id]["phases"].append(phase)
        
        metrics["total_reports"] = len(reports_data)
        
        # Calculate report-level metrics
        for report_id, data in reports_data.items():
            report_phases = data["phases"]
            
            # Check if all phases are complete
            all_complete = all(p.state == WorkflowPhaseState.COMPLETE for p in report_phases)
            any_started = any(p.state != WorkflowPhaseState.NOT_STARTED for p in report_phases)
            
            if all_complete:
                metrics["reports_completed"] += 1
            elif any_started:
                metrics["reports_in_progress"] += 1
            else:
                metrics["reports_not_started"] += 1
        
        # Get attribute metrics
        if report_id:
            metrics["total_attributes"] = await self._count_report_attributes(report_id)
            metrics["attributes_approved"] = await self._count_approved_attributes(cycle_id, report_id)
        else:
            # Aggregate across all reports
            report_ids = list(reports_data.keys())
            for rid in report_ids:
                metrics["total_attributes"] += await self._count_report_attributes(rid)
                metrics["attributes_approved"] += await self._count_approved_attributes(cycle_id, rid)
        
        # Get observation metrics
        metrics["observations_confirmed"] = await self._count_confirmed_observations(cycle_id, report_id)
        
        # Calculate completion percentage
        if metrics["total_reports"] > 0:
            metrics["overall_completion_percentage"] = (
                metrics["reports_completed"] / metrics["total_reports"] * 100
            )
        
        return metrics
    
    async def calculate_phase_metrics(
        self,
        cycle_id: str,
        report_id: str,
        phase_name: str,
        lob_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calculate detailed metrics for a specific phase."""
        # Get phase data
        query = select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == phase_name
            )
        )
        result = await self.db.execute(query)
        phase = result.scalar_one_or_none()
        
        if not phase:
            return {}
        
        metrics = {
            "phase_name": phase_name,
            "state": phase.state,
            "schedule_status": phase.schedule_status,
            "started_at": phase.actual_start_date,
            "completed_at": phase.actual_end_date,
            "completion_time_minutes": None,
            "on_time_completion": None,
            "submissions_for_approval": 0
        }
        
        # Calculate completion time
        if phase.actual_start_date and phase.actual_end_date:
            duration = phase.actual_end_date - phase.actual_start_date
            metrics["completion_time_minutes"] = int(duration.total_seconds() / 60)
            
            # Check if completed on time
            if phase.planned_end_date:
                metrics["on_time_completion"] = phase.actual_end_date <= phase.planned_end_date
        
        # Phase-specific metrics
        if phase_name == "Planning":
            metrics.update(await self._calculate_planning_metrics(cycle_id, report_id, lob_name))
        elif phase_name == "Data Profiling":
            metrics.update(await self._calculate_profiling_metrics(cycle_id, report_id, lob_name))
        elif phase_name == "Scoping":
            metrics.update(await self._calculate_scoping_metrics(cycle_id, report_id, lob_name))
        elif phase_name == "CycleReportSampleSelectionSamples Selection":
            metrics.update(await self._calculate_sample_selection_metrics(cycle_id, report_id, lob_name))
        elif phase_name == "Data Owner Identification":
            metrics.update(await self._calculate_data_provider_metrics(cycle_id, report_id, lob_name))
        elif phase_name == "Request for Information":
            metrics.update(await self._calculate_rfi_metrics(cycle_id, report_id, lob_name))
        elif phase_name == "Test Execution":
            metrics.update(await self._calculate_testing_metrics(cycle_id, report_id, lob_name))
        elif phase_name == "Observation Management":
            metrics.update(await self._calculate_observation_metrics(cycle_id, report_id, lob_name))
        
        return metrics
    
    async def calculate_sla_compliance(
        self,
        cycle_id: str,
        report_id: Optional[str] = None,
        phase_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calculate SLA compliance metrics."""
        query = select(WorkflowPhase).where(WorkflowPhase.cycle_id == cycle_id)
        
        if report_id:
            query = query.where(WorkflowPhase.report_id == report_id)
        if phase_name:
            query = query.where(WorkflowPhase.phase_name == phase_name)
        
        result = await self.db.execute(query)
        phases = result.scalars().all()
        
        total_phases = len(phases)
        on_time = sum(1 for p in phases if p.schedule_status == ScheduleStatus.ON_TRACK)
        at_risk = sum(1 for p in phases if p.schedule_status == ScheduleStatus.AT_RISK)
        past_due = sum(1 for p in phases if p.schedule_status == ScheduleStatus.PAST_DUE)
        
        return {
            "total_phases": total_phases,
            "on_time": on_time,
            "at_risk": at_risk,
            "past_due": past_due,
            "on_time_percentage": (on_time / total_phases * 100) if total_phases > 0 else 0,
            "at_risk_percentage": (at_risk / total_phases * 100) if total_phases > 0 else 0,
            "past_due_percentage": (past_due / total_phases * 100) if total_phases > 0 else 0
        }
    
    async def calculate_error_rates(
        self,
        cycle_id: str,
        report_id: str,
        entity_type: str = "sample"  # sample, attribute, or test_case
    ) -> Dict[str, Any]:
        """Calculate error rates for samples, attributes, or test cases."""
        if entity_type == "sample":
            return await self._calculate_sample_error_rates(cycle_id, report_id)
        elif entity_type == "attribute":
            return await self._calculate_attribute_error_rates(cycle_id, report_id)
        elif entity_type == "test_case":
            return await self._calculate_test_case_error_rates(cycle_id, report_id)
        else:
            return {"error": "Invalid entity type"}
    
    # Helper methods for specific calculations
    
    async def _count_report_attributes(self, report_id: str) -> int:
        """Count total attributes for a report."""
        query = select(func.count(ReportAttribute.attribute_id)).where(
            ReportAttribute.report_id == report_id
        )
        result = await self.db.execute(query)
        return result.scalar() or 0
    
    async def _count_approved_attributes(self, cycle_id: str, report_id: str) -> int:
        """Count approved attributes in planning phase."""
        # Check WorkflowPhase data field for planning approval status
        query = select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == "Planning"
            )
        )
        result = await self.db.execute(query)
        phase = result.scalar_one_or_none()
        
        if phase and phase.phase_data:
            # Assuming phase_data stores approval information
            approved_count = phase.phase_data.get("approved_attributes", 0)
            return approved_count
        
        return 0
    
    async def _count_confirmed_observations(self, cycle_id: str, report_id: Optional[str] = None) -> int:
        """Count confirmed observations."""
        query = select(func.count(Observation.observation_id)).where(
            and_(
                Observation.cycle_id == cycle_id,
                Observation.status == "approved"
            )
        )
        
        if report_id:
            query = query.where(Observation.report_id == report_id)
        
        result = await self.db.execute(query)
        return result.scalar() or 0
    
    async def _calculate_planning_metrics(self, cycle_id: str, report_id: str, lob_name: Optional[str]) -> Dict[str, Any]:
        """Calculate planning phase specific metrics."""
        metrics = {
            "total_attributes": await self._count_report_attributes(report_id),
            "attributes_approved_for_planning": 0,
            "attributes_pending_approval": 0
        }
        
        # Get planning phase data
        query = select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == "Planning"
            )
        )
        result = await self.db.execute(query)
        phase = result.scalar_one_or_none()
        
        if phase and phase.phase_data:
            metrics["attributes_approved_for_planning"] = phase.phase_data.get("approved_attributes", 0)
            metrics["submissions_for_approval"] = phase.phase_data.get("submission_count", 0)
        
        metrics["attributes_pending_approval"] = metrics["total_attributes"] - metrics["attributes_approved_for_planning"]
        
        return metrics
    
    async def _calculate_profiling_metrics(self, cycle_id: str, report_id: str, lob_name: Optional[str]) -> Dict[str, Any]:
        """Calculate data profiling phase specific metrics."""
        # Get approved attributes from planning
        planning_metrics = await self._calculate_planning_metrics(cycle_id, report_id, lob_name)
        total_attributes = planning_metrics.get("attributes_approved_for_planning", 0)
        
        metrics = {
            "total_attributes": total_attributes,
            "approved_profiling_rules": 0,
            "attributes_no_dq_issues": 0,
            "attributes_with_anomalies": 0
        }
        
        # Get profiling phase data
        query = select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == "Data Profiling"
            )
        )
        result = await self.db.execute(query)
        phase = result.scalar_one_or_none()
        
        if phase and phase.phase_data:
            metrics["approved_profiling_rules"] = phase.phase_data.get("approved_rules", 0)
            metrics["attributes_no_dq_issues"] = phase.phase_data.get("clean_attributes", 0)
            metrics["attributes_with_anomalies"] = phase.phase_data.get("anomaly_attributes", 0)
            metrics["submissions_for_approval"] = phase.phase_data.get("submission_count", 0)
        
        return metrics
    
    async def _calculate_scoping_metrics(self, cycle_id: str, report_id: str, lob_name: Optional[str]) -> Dict[str, Any]:
        """Calculate scoping phase specific metrics using direct SQL."""
        from sqlalchemy import text
        
        # Get scoped attributes using direct SQL
        result = await self.db.execute(
            text("SELECT COUNT(*) FROM report_attributes WHERE cycle_id = :cycle_id AND report_id = :report_id AND is_scoped = true AND is_latest_version = true"),
            {"cycle_id": cycle_id, "report_id": report_id}
        )
        total_scoped = result.scalar() or 0
        
        # Count primary keys - this information might not be available in report_attributes table
        # For now, we'll use a placeholder calculation
        primary_keys = 0  # This might need to be adjusted based on actual database schema
        
        return {
            "total_attributes": total_scoped,
            "primary_keys": primary_keys,
            "non_pk_scoped_attributes": total_scoped - primary_keys
        }
    
    async def _calculate_sample_selection_metrics(self, cycle_id: str, report_id: str, lob_name: Optional[str]) -> Dict[str, Any]:
        """Calculate sample selection phase specific metrics using direct SQL."""
        from sqlalchemy import text
        
        # Get scoping metrics first
        scoping_metrics = await self._calculate_scoping_metrics(cycle_id, report_id, lob_name)
        
        # Total samples using direct SQL from test_cases table
        result = await self.db.execute(
            text("SELECT COUNT(DISTINCT sample_id) FROM test_cases WHERE cycle_id = :cycle_id AND report_id = :report_id"),
            {"cycle_id": cycle_id, "report_id": report_id}
        )
        total_samples = result.scalar() or 0
        
        # For now, consider all samples as approved
        samples_approved = total_samples
        
        # Count LOBs - this might need adjustment based on actual schema
        result = await self.db.execute(
            text("SELECT COUNT(DISTINCT lob_name) FROM test_cases WHERE cycle_id = :cycle_id AND report_id = :report_id"),
            {"cycle_id": cycle_id, "report_id": report_id}
        )
        total_lobs = result.scalar() or 0
        
        return {
            "non_pk_scoped_attributes": scoping_metrics.get("non_pk_scoped_attributes", 0),
            "samples_approved": samples_approved,
            "total_lobs": total_lobs,
            "samples_pending_approval": 0
        }
    
    async def _calculate_data_provider_metrics(self, cycle_id: str, report_id: str, lob_name: Optional[str]) -> Dict[str, Any]:
        """Calculate data provider identification phase specific metrics."""
        # Get base metrics from sample selection
        sample_metrics = await self._calculate_sample_selection_metrics(cycle_id, report_id, lob_name)
        
        # Get LOB assignments
        query = select(LOBAssignment).where(
            and_(
                LOBAssignment.cycle_id == cycle_id,
                LOBAssignment.report_id == report_id
            )
        )
        
        if lob_name:
            query = query.where(LOBAssignment.lob_name == lob_name)
        
        result = await self.db.execute(query)
        assignments = result.scalars().all()
        
        metrics = {
            "non_pk_scoped_attributes": sample_metrics.get("non_pk_scoped_attributes", 0),
            "samples_approved": sample_metrics.get("samples_approved", 0),
            "total_lobs": sample_metrics.get("total_lobs", 0),
            "data_providers_assigned": len(set(a.assigned_user_id for a in assignments if a.assigned_user_id)),
            "lobs_with_assignments": len(set(a.lob_name for a in assignments if a.assigned_user_id)),
            "changes_to_data_providers": sum(1 for a in assignments if a.reassignment_count > 0)
        }
        
        return metrics
    
    async def _calculate_rfi_metrics(self, cycle_id: str, report_id: str, lob_name: Optional[str]) -> Dict[str, Any]:
        """Calculate RFI phase specific metrics."""
        # Get test plans for counting test cases
        query = select(TestPlan).where(
            and_(
                TestPlan.cycle_id == cycle_id,
                TestPlan.report_id == report_id
            )
        )
        
        result = await self.db.execute(query)
        test_plans = result.scalars().all()
        
        total_test_cases = len(test_plans)
        rfi_completed = sum(1 for tp in test_plans if tp.status == "rfi_completed")
        rfi_pending = sum(1 for tp in test_plans if tp.status in ["rfi_sent", "rfi_pending"])
        
        return {
            "total_test_cases": total_test_cases,
            "test_cases_rfi_completed": rfi_completed,
            "test_cases_rfi_pending": rfi_pending,
            "rfi_completion_rate": (rfi_completed / total_test_cases * 100) if total_test_cases > 0 else 0
        }
    
    async def _calculate_testing_metrics(self, cycle_id: str, report_id: str, lob_name: Optional[str]) -> Dict[str, Any]:
        """Calculate test execution phase specific metrics."""
        # Get test executions
        query = select(TestExecution).where(
            and_(
                TestExecution.cycle_id == cycle_id,
                TestExecution.report_id == report_id
            )
        )
        
        result = await self.db.execute(query)
        executions = result.scalars().all()
        
        total_test_cases = len(executions)
        completed = sum(1 for e in executions if e.status == "completed")
        passed = sum(1 for e in executions if e.overall_result == "pass")
        failed = sum(1 for e in executions if e.overall_result == "fail")
        requiring_reupload = sum(1 for e in executions if e.requires_resubmission)
        
        return {
            "total_test_cases": total_test_cases,
            "test_cases_completed": completed,
            "test_cases_passed": passed,
            "test_cases_failed": failed,
            "test_cases_requiring_reupload": requiring_reupload,
            "pass_rate": (passed / completed * 100) if completed > 0 else 0,
            "fail_rate": (failed / completed * 100) if completed > 0 else 0
        }
    
    async def _calculate_observation_metrics(self, cycle_id: str, report_id: str, lob_name: Optional[str]) -> Dict[str, Any]:
        """Calculate observation management phase specific metrics using direct SQL."""
        from sqlalchemy import text
        
        # First get the base metrics like other phases
        base_metrics = await self._calculate_sample_selection_metrics(cycle_id, report_id, lob_name)
        
        # Total test cases using direct SQL
        result = await self.db.execute(
            text("SELECT COUNT(*) FROM cycle_report_test_execution_test_executions WHERE cycle_id = :cycle_id AND report_id = :report_id"),
            {"cycle_id": cycle_id, "report_id": report_id}
        )
        total_test_cases = result.scalar() or 0
        
        # Test cases with observations - check observation_groups table first
        result = await self.db.execute(
            text("SELECT COUNT(DISTINCT source_test_execution_id) FROM observation_groups WHERE cycle_id = :cycle_id AND report_id = :report_id AND source_test_execution_id IS NOT NULL"),
            {"cycle_id": cycle_id, "report_id": report_id}
        )
        test_cases_with_observations = result.scalar() or 0
        
        # If no data in observation_groups, try observations table
        if test_cases_with_observations == 0:
            result = await self.db.execute(
                text("SELECT COUNT(DISTINCT source_test_execution_id) FROM observations WHERE cycle_id = :cycle_id AND report_id = :report_id AND source_test_execution_id IS NOT NULL"),
                {"cycle_id": cycle_id, "report_id": report_id}
            )
            test_cases_with_observations = result.scalar() or 0
        
        # Total observations
        result = await self.db.execute(
            text("SELECT COUNT(*) FROM observation_groups WHERE cycle_id = :cycle_id AND report_id = :report_id"),
            {"cycle_id": cycle_id, "report_id": report_id}
        )
        total_observations = result.scalar() or 0
        
        # If no observations in observation_groups, try observations table
        if total_observations == 0:
            result = await self.db.execute(
                text("SELECT COUNT(*) FROM observations WHERE cycle_id = :cycle_id AND report_id = :report_id"),
                {"cycle_id": cycle_id, "report_id": report_id}
            )
            total_observations = result.scalar() or 0
        
        # Approved observations
        result = await self.db.execute(
            text("SELECT COUNT(*) FROM observation_groups WHERE cycle_id = :cycle_id AND report_id = :report_id AND approval_status = 'FULLY_APPROVED'"),
            {"cycle_id": cycle_id, "report_id": report_id}
        )
        approved_observations = result.scalar() or 0
        
        # If no approved in observation_groups, try observations table
        if approved_observations == 0 and total_observations > 0:
            result = await self.db.execute(
                text("SELECT COUNT(*) FROM observations WHERE cycle_id = :cycle_id AND report_id = :report_id AND status = 'approved'"),
                {"cycle_id": cycle_id, "report_id": report_id}
            )
            approved_observations = result.scalar() or 0
        
        # Samples impacted - count distinct samples from test executions that have observations
        result = await self.db.execute(
            text("""
            SELECT COUNT(DISTINCT sample_id) 
            FROM cycle_report_test_execution_test_executions 
            WHERE cycle_id = :cycle_id AND report_id = :report_id 
            AND test_execution_id IN (
                SELECT DISTINCT source_test_execution_id 
                FROM observation_groups 
                WHERE cycle_id = :cycle_id AND report_id = :report_id 
                AND source_test_execution_id IS NOT NULL
            )
            """),
            {"cycle_id": cycle_id, "report_id": report_id}
        )
        samples_impacted = result.scalar() or 0
        
        # If no data from observation_groups, try observations table
        if samples_impacted == 0 and test_cases_with_observations > 0:
            result = await self.db.execute(
                text("""
                SELECT COUNT(DISTINCT sample_id) 
                FROM cycle_report_test_execution_test_executions 
                WHERE cycle_id = :cycle_id AND report_id = :report_id 
                AND test_execution_id IN (
                    SELECT DISTINCT source_test_execution_id 
                    FROM observations 
                    WHERE cycle_id = :cycle_id AND report_id = :report_id 
                    AND source_test_execution_id IS NOT NULL
                )
                """),
                {"cycle_id": cycle_id, "report_id": report_id}
            )
            samples_impacted = result.scalar() or 0
        
        # Attributes impacted - count distinct attributes from test executions that have observations
        result = await self.db.execute(
            text("""
            SELECT COUNT(DISTINCT attribute_id) 
            FROM cycle_report_test_execution_test_executions 
            WHERE cycle_id = :cycle_id AND report_id = :report_id 
            AND test_execution_id IN (
                SELECT DISTINCT source_test_execution_id 
                FROM observation_groups 
                WHERE cycle_id = :cycle_id AND report_id = :report_id 
                AND source_test_execution_id IS NOT NULL
            )
            """),
            {"cycle_id": cycle_id, "report_id": report_id}
        )
        attributes_impacted = result.scalar() or 0
        
        # If no data from observation_groups, try observations table
        if attributes_impacted == 0 and test_cases_with_observations > 0:
            result = await self.db.execute(
                text("""
                SELECT COUNT(DISTINCT attribute_id) 
                FROM cycle_report_test_execution_test_executions 
                WHERE cycle_id = :cycle_id AND report_id = :report_id 
                AND test_execution_id IN (
                    SELECT DISTINCT source_test_execution_id 
                    FROM observations 
                    WHERE cycle_id = :cycle_id AND report_id = :report_id 
                    AND source_test_execution_id IS NOT NULL
                )
                """),
                {"cycle_id": cycle_id, "report_id": report_id}
            )
            attributes_impacted = result.scalar() or 0
        
        return {
            "non_pk_scoped_attributes": base_metrics.get("non_pk_scoped_attributes", 0),
            "samples_approved": base_metrics.get("samples_approved", 0),
            "total_lobs": base_metrics.get("total_lobs", 0),
            "total_test_cases": total_test_cases,
            "test_cases_with_observations": test_cases_with_observations,
            "total_observations": total_observations,
            "approved_observations": approved_observations,
            "samples_impacted": samples_impacted,
            "attributes_impacted": attributes_impacted,
            "approval_rate": (approved_observations / total_observations * 100) if total_observations > 0 else 0
        }
    
    async def _calculate_sample_error_rates(self, cycle_id: str, report_id: str) -> Dict[str, Any]:
        """Calculate error rates at sample level."""
        # Get all samples and their test results
        query = select(CycleReportSampleSelectionSamples).join(SampleSet).where(
            and_(
                SampleSet.cycle_id == cycle_id,
                SampleSet.report_id == report_id,
                SampleSet.is_latest_version == True
            )
        )
        
        result = await self.db.execute(query)
        samples = result.scalars().all()
        
        total_samples = len(samples)
        
        # Count failed samples based on test executions
        failed_samples = 0
        passed_samples = 0
        under_review = 0
        
        for sample in samples:
            # Check test results for this sample
            test_query = select(TestExecution).where(
                and_(
                    TestExecution.cycle_id == cycle_id,
                    TestExecution.report_id == report_id,
                    TestExecution.metadata.contains({"sample_id": sample.sample_id})
                )
            )
            test_result = await self.db.execute(test_query)
            tests = test_result.scalars().all()
            
            if any(t.overall_result == "fail" for t in tests):
                failed_samples += 1
            elif all(t.overall_result == "pass" for t in tests):
                passed_samples += 1
            else:
                under_review += 1
        
        return {
            "total_samples": total_samples,
            "samples_passed": passed_samples,
            "samples_failed": failed_samples,
            "samples_under_review": under_review,
            "error_rate": (failed_samples / total_samples * 100) if total_samples > 0 else 0
        }
    
    async def _calculate_attribute_error_rates(self, cycle_id: str, report_id: str) -> Dict[str, Any]:
        """Calculate error rates at attribute level."""
        # Get scoped attributes
        query = select(ScopedReportAttribute).where(
            and_(
                ScopedReportAttribute.cycle_id == cycle_id,
                ScopedReportAttribute.report_id == report_id
            )
        )
        
        result = await self.db.execute(query)
        attributes = result.scalars().all()
        
        total_attributes = len(attributes)
        
        # Count failed attributes based on test executions and observations
        failed_attributes = 0
        passed_attributes = 0
        under_review = 0
        
        for attr in attributes:
            # Check if attribute has any failed tests or observations
            obs_query = select(Observation).where(
                and_(
                    Observation.cycle_id == cycle_id,
                    Observation.report_id == report_id,
                    Observation.metadata.contains({"attribute_id": attr.attribute_id})
                )
            )
            obs_result = await self.db.execute(obs_query)
            observations = obs_result.scalars().all()
            
            if observations:
                if any(o.severity in ["high", "critical"] for o in observations):
                    failed_attributes += 1
                else:
                    under_review += 1
            else:
                # No observations means passed
                passed_attributes += 1
        
        return {
            "total_attributes": total_attributes,
            "attributes_passed": passed_attributes,
            "attributes_failed": failed_attributes,
            "attributes_under_review": under_review,
            "error_rate": (failed_attributes / total_attributes * 100) if total_attributes > 0 else 0
        }
    
    async def _calculate_test_case_error_rates(self, cycle_id: str, report_id: str) -> Dict[str, Any]:
        """Calculate error rates at test case level."""
        # Get test executions
        query = select(TestExecution).where(
            and_(
                TestExecution.cycle_id == cycle_id,
                TestExecution.report_id == report_id
            )
        )
        
        result = await self.db.execute(query)
        test_cases = result.scalars().all()
        
        total_test_cases = len(test_cases)
        passed = sum(1 for t in test_cases if t.overall_result == "pass")
        failed = sum(1 for t in test_cases if t.overall_result == "fail")
        under_review = sum(1 for t in test_cases if t.status not in ["completed", "failed"])
        
        return {
            "total_test_cases": total_test_cases,
            "test_cases_passed": passed,
            "test_cases_failed": failed,
            "test_cases_under_review": under_review,
            "error_rate": (failed / total_test_cases * 100) if total_test_cases > 0 else 0
        }