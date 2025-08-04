"""Tester-specific metrics calculator."""
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.metrics.base_metrics_calculator import BaseMetricsCalculator
from app.models.workflow_tracking import WorkflowPhase
from app.models.test_cycle import TestCycle
from app.models.report import Report
from app.core.enums import WorkflowPhaseState


class TesterMetricsCalculator(BaseMetricsCalculator):
    """Calculate metrics specific to the Tester role."""
    
    async def get_tester_dashboard_metrics(
        self,
        tester_id: str,
        cycle_id: Optional[str] = None,
        time_period: str = "current_cycle"
    ) -> Dict[str, Any]:
        """Get comprehensive dashboard metrics for a tester."""
        metrics = {
            "summary": {},
            "report_metrics": [],
            "phase_breakdown": {},
            "time_metrics": {},
            "quality_metrics": {}
        }
        
        # Get assigned reports
        assigned_reports = await self._get_assigned_reports(tester_id, cycle_id)
        
        # Summary metrics
        metrics["summary"] = {
            "total_reports_assigned": len(assigned_reports),
            "reports_completed": 0,
            "reports_in_progress": 0,
            "observations_confirmed": 0,
            "average_completion_time": 0
        }
        
        # Calculate metrics for each report
        for report in assigned_reports:
            report_metric = await self._calculate_report_metrics_for_tester(
                tester_id,
                report["cycle_id"],
                report["report_id"]
            )
            metrics["report_metrics"].append(report_metric)
            
            # Update summary
            if report_metric["status"] == "completed":
                metrics["summary"]["reports_completed"] += 1
            elif report_metric["status"] == "in_progress":
                metrics["summary"]["reports_in_progress"] += 1
            
            metrics["summary"]["observations_confirmed"] += report_metric.get("observations_confirmed", 0)
        
        # Phase breakdown across all reports
        metrics["phase_breakdown"] = await self._calculate_phase_breakdown_for_tester(
            tester_id,
            assigned_reports
        )
        
        # Time metrics
        metrics["time_metrics"] = await self._calculate_time_metrics_for_tester(
            tester_id,
            assigned_reports
        )
        
        # Quality metrics
        metrics["quality_metrics"] = await self._calculate_quality_metrics_for_tester(
            tester_id,
            assigned_reports
        )
        
        return metrics
    
    async def get_report_testing_summary(
        self,
        tester_id: str,
        cycle_id: str,
        report_id: str
    ) -> Dict[str, Any]:
        """Get testing summary for a specific report."""
        summary = {
            "sample_metrics": {},
            "attribute_metrics": {},
            "test_case_metrics": {},
            "lob_breakdown": {}
        }
        
        # CycleReportSampleSelectionSamples metrics
        sample_metrics = await self.calculate_error_rates(cycle_id, report_id, "sample")
        summary["sample_metrics"] = {
            "aggregate": sample_metrics,
            "by_lob": await self._calculate_sample_metrics_by_lob(cycle_id, report_id)
        }
        
        # Attribute metrics
        attribute_metrics = await self.calculate_error_rates(cycle_id, report_id, "attribute")
        summary["attribute_metrics"] = {
            "aggregate": attribute_metrics,
            "by_lob": await self._calculate_attribute_metrics_by_lob(cycle_id, report_id)
        }
        
        # Test case metrics
        test_case_metrics = await self.calculate_error_rates(cycle_id, report_id, "test_case")
        summary["test_case_metrics"] = {
            "aggregate": test_case_metrics,
            "by_lob": await self._calculate_test_case_metrics_by_lob(cycle_id, report_id)
        }
        
        return summary
    
    async def _get_assigned_reports(
        self,
        tester_id: str,
        cycle_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get reports assigned to a tester."""
        # Query workflow phases where tester is assigned
        query = select(
            WorkflowPhase.cycle_id,
            WorkflowPhase.report_id,
            func.min(WorkflowPhase.actual_start_date).label("start_date"),
            func.max(WorkflowPhase.actual_end_date).label("end_date")
        ).where(
            WorkflowPhase.started_by == tester_id
        ).group_by(
            WorkflowPhase.cycle_id,
            WorkflowPhase.report_id
        )
        
        if cycle_id:
            query = query.where(WorkflowPhase.cycle_id == cycle_id)
        
        result = await self.db.execute(query)
        reports = []
        
        for row in result:
            reports.append({
                "cycle_id": row.cycle_id,
                "report_id": row.report_id,
                "start_date": row.start_date,
                "end_date": row.end_date
            })
        
        return reports
    
    async def _calculate_report_metrics_for_tester(
        self,
        tester_id: str,
        cycle_id: str,
        report_id: str
    ) -> Dict[str, Any]:
        """Calculate metrics for a specific report assigned to a tester."""
        # Get all phases for this report
        query = select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id
            )
        )
        
        result = await self.db.execute(query)
        phases = result.scalars().all()
        
        # Determine report status
        all_complete = all(p.state == WorkflowPhaseState.COMPLETE for p in phases)
        any_started = any(p.state != WorkflowPhaseState.NOT_STARTED for p in phases)
        
        status = "completed" if all_complete else "in_progress" if any_started else "not_started"
        
        # Get report details
        report_query = select(Report).where(Report.report_id == report_id)
        report_result = await self.db.execute(report_query)
        report = report_result.scalar_one()
        
        metrics = {
            "report_id": report_id,
            "report_name": report.report_name,
            "status": status,
            "phases_completed": sum(1 for p in phases if p.state == WorkflowPhaseState.COMPLETE),
            "total_phases": len(phases),
            "current_phase": next((p.phase_name for p in phases if p.state == WorkflowPhaseState.IN_PROGRESS), None)
        }
        
        # Add phase-specific metrics
        for phase_name in ["Planning", "Data Profiling", "Scoping", "CycleReportSampleSelectionSamples Selection", 
                          "Data Provider Identification", "Request for Information", 
                          "Test Execution", "Observation Management"]:
            phase_data = next((p for p in phases if p.phase_name == phase_name), None)
            if phase_data:
                phase_metrics = await self.calculate_phase_metrics(cycle_id, report_id, phase_name)
                metrics[phase_name.lower().replace(" ", "_")] = phase_metrics
        
        # Get observation count
        metrics["observations_confirmed"] = await self._count_confirmed_observations(cycle_id, report_id)
        
        return metrics
    
    async def _calculate_phase_breakdown_for_tester(
        self,
        tester_id: str,
        assigned_reports: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate phase breakdown metrics across all assigned reports."""
        phase_breakdown = {}
        
        for phase_name in ["Planning", "Data Profiling", "Scoping", "CycleReportSampleSelectionSamples Selection",
                          "Data Provider Identification", "Request for Information",
                          "Test Execution", "Observation Management"]:
            phase_breakdown[phase_name] = {
                "completed": 0,
                "in_progress": 0,
                "not_started": 0,
                "average_completion_time": 0,
                "on_time_percentage": 0
            }
            
            completion_times = []
            on_time_count = 0
            total_count = 0
            
            for report in assigned_reports:
                phase_query = select(WorkflowPhase).where(
                    and_(
                        WorkflowPhase.cycle_id == report["cycle_id"],
                        WorkflowPhase.report_id == report["report_id"],
                        WorkflowPhase.phase_name == phase_name
                    )
                )
                
                phase_result = await self.db.execute(phase_query)
                phase = phase_result.scalar_one_or_none()
                
                if phase:
                    if phase.state == WorkflowPhaseState.COMPLETE:
                        phase_breakdown[phase_name]["completed"] += 1
                        
                        # Calculate completion time
                        if phase.actual_start_date and phase.actual_end_date:
                            duration = (phase.actual_end_date - phase.actual_start_date).total_seconds() / 60
                            completion_times.append(duration)
                            
                            # Check if on time
                            if phase.planned_end_date and phase.actual_end_date <= phase.planned_end_date:
                                on_time_count += 1
                            total_count += 1
                    
                    elif phase.state == WorkflowPhaseState.IN_PROGRESS:
                        phase_breakdown[phase_name]["in_progress"] += 1
                    else:
                        phase_breakdown[phase_name]["not_started"] += 1
            
            # Calculate averages
            if completion_times:
                phase_breakdown[phase_name]["average_completion_time"] = sum(completion_times) / len(completion_times)
            
            if total_count > 0:
                phase_breakdown[phase_name]["on_time_percentage"] = (on_time_count / total_count) * 100
        
        return phase_breakdown
    
    async def _calculate_time_metrics_for_tester(
        self,
        tester_id: str,
        assigned_reports: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate time-based metrics for a tester."""
        time_metrics = {
            "average_report_completion_time": 0,
            "fastest_completion": None,
            "slowest_completion": None,
            "phases_behind_schedule": 0,
            "phases_ahead_schedule": 0
        }
        
        completion_times = []
        
        for report in assigned_reports:
            if report["start_date"] and report["end_date"]:
                duration = (report["end_date"] - report["start_date"]).total_seconds() / (60 * 60 * 24)  # Days
                completion_times.append(duration)
        
        if completion_times:
            time_metrics["average_report_completion_time"] = sum(completion_times) / len(completion_times)
            time_metrics["fastest_completion"] = min(completion_times)
            time_metrics["slowest_completion"] = max(completion_times)
        
        # Count phases behind/ahead of schedule
        for report in assigned_reports:
            phase_query = select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == report["cycle_id"],
                    WorkflowPhase.report_id == report["report_id"]
                )
            )
            
            phase_result = await self.db.execute(phase_query)
            phases = phase_result.scalars().all()
            
            for phase in phases:
                if phase.planned_end_date and phase.actual_end_date:
                    if phase.actual_end_date > phase.planned_end_date:
                        time_metrics["phases_behind_schedule"] += 1
                    elif phase.actual_end_date < phase.planned_end_date:
                        time_metrics["phases_ahead_schedule"] += 1
        
        return time_metrics
    
    async def _calculate_quality_metrics_for_tester(
        self,
        tester_id: str,
        assigned_reports: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate quality metrics for a tester."""
        quality_metrics = {
            "resubmission_rate": 0,
            "first_time_approval_rate": 0,
            "average_submissions_per_phase": {},
            "observation_accuracy_rate": 0
        }
        
        total_submissions = 0
        resubmissions = 0
        first_time_approvals = 0
        
        phase_submissions = {}
        
        for report in assigned_reports:
            # Get phase data for quality metrics
            phase_query = select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == report["cycle_id"],
                    WorkflowPhase.report_id == report["report_id"]
                )
            )
            
            phase_result = await self.db.execute(phase_query)
            phases = phase_result.scalars().all()
            
            for phase in phases:
                if phase.phase_data:
                    submissions = phase.phase_data.get("submission_count", 0)
                    if submissions > 0:
                        total_submissions += 1
                        if submissions == 1:
                            first_time_approvals += 1
                        else:
                            resubmissions += submissions - 1
                        
                        # Track by phase
                        if phase.phase_name not in phase_submissions:
                            phase_submissions[phase.phase_name] = []
                        phase_submissions[phase.phase_name].append(submissions)
        
        # Calculate rates
        if total_submissions > 0:
            quality_metrics["resubmission_rate"] = (resubmissions / total_submissions) * 100
            quality_metrics["first_time_approval_rate"] = (first_time_approvals / total_submissions) * 100
        
        # Average submissions per phase
        for phase_name, submissions_list in phase_submissions.items():
            if submissions_list:
                quality_metrics["average_submissions_per_phase"][phase_name] = (
                    sum(submissions_list) / len(submissions_list)
                )
        
        return quality_metrics
    
    async def _calculate_sample_metrics_by_lob(
        self,
        cycle_id: str,
        report_id: str
    ) -> Dict[str, Any]:
        """Calculate sample metrics broken down by LOB."""
        from app.models.sample_selection import SampleSet, CycleReportSampleSelectionSamples
        
        # Get all LOBs for this report
        lob_query = select(SampleSet.lob_name).where(
            and_(
                SampleSet.cycle_id == cycle_id,
                SampleSet.report_id == report_id,
                SampleSet.is_latest_version == True
            )
        ).distinct()
        
        lob_result = await self.db.execute(lob_query)
        lobs = [row[0] for row in lob_result]
        
        lob_metrics = {}
        
        for lob in lobs:
            # Calculate metrics for this LOB
            sample_query = select(CycleReportSampleSelectionSamples).join(SampleSet).where(
                and_(
                    SampleSet.cycle_id == cycle_id,
                    SampleSet.report_id == report_id,
                    SampleSet.lob_name == lob,
                    SampleSet.is_latest_version == True
                )
            )
            
            sample_result = await self.db.execute(sample_query)
            samples = sample_result.scalars().all()
            
            total = len(samples)
            passed = sum(1 for s in samples if s.validation_status == "pass")
            failed = sum(1 for s in samples if s.validation_status == "fail")
            under_review = total - passed - failed
            
            lob_metrics[lob] = {
                "total_samples": total,
                "samples_passed": passed,
                "samples_failed": failed,
                "samples_under_review": under_review,
                "error_rate": (failed / total * 100) if total > 0 else 0
            }
        
        return lob_metrics
    
    async def _calculate_attribute_metrics_by_lob(
        self,
        cycle_id: str,
        report_id: str
    ) -> Dict[str, Any]:
        """Calculate attribute metrics broken down by LOB."""
        from app.models.test_scoping import ScopedReportAttribute
        
        # Get all LOBs for scoped attributes
        lob_query = select(ScopedReportAttribute.lob_name).where(
            and_(
                ScopedReportAttribute.cycle_id == cycle_id,
                ScopedReportAttribute.report_id == report_id
            )
        ).distinct()
        
        lob_result = await self.db.execute(lob_query)
        lobs = [row[0] for row in lob_result if row[0]]  # Filter out None values
        
        lob_metrics = {}
        
        for lob in lobs:
            # Get attributes for this LOB
            attr_query = select(ScopedReportAttribute).where(
                and_(
                    ScopedReportAttribute.cycle_id == cycle_id,
                    ScopedReportAttribute.report_id == report_id,
                    ScopedReportAttribute.lob_name == lob
                )
            )
            
            attr_result = await self.db.execute(attr_query)
            attributes = attr_result.scalars().all()
            
            total = len(attributes)
            
            # Determine pass/fail based on observations
            from app.models.observations import Observation
            
            failed = 0
            passed = 0
            under_review = 0
            
            for attr in attributes:
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
                        failed += 1
                    else:
                        under_review += 1
                else:
                    passed += 1
            
            lob_metrics[lob] = {
                "total_attributes": total,
                "attributes_passed": passed,
                "attributes_failed": failed,
                "attributes_under_review": under_review,
                "error_rate": (failed / total * 100) if total > 0 else 0
            }
        
        return lob_metrics
    
    async def _calculate_test_case_metrics_by_lob(
        self,
        cycle_id: str,
        report_id: str
    ) -> Dict[str, Any]:
        """Calculate test case metrics broken down by LOB."""
        from app.models.test_execution import TestExecution
        
        # Get test executions with LOB information from metadata
        test_query = select(TestExecution).where(
            and_(
                TestExecution.cycle_id == cycle_id,
                TestExecution.report_id == report_id
            )
        )
        
        test_result = await self.db.execute(test_query)
        test_cases = test_result.scalars().all()
        
        # Group by LOB
        lob_tests = {}
        
        for test_case in test_cases:
            # Extract LOB from metadata
            lob = None
            if test_case.metadata:
                lob = test_case.metadata.get("lob_name")
            
            if lob:
                if lob not in lob_tests:
                    lob_tests[lob] = []
                lob_tests[lob].append(test_case)
        
        # Calculate metrics per LOB
        lob_metrics = {}
        
        for lob, tests in lob_tests.items():
            total = len(tests)
            passed = sum(1 for t in tests if t.overall_result == "pass")
            failed = sum(1 for t in tests if t.overall_result == "fail")
            under_review = sum(1 for t in tests if t.status not in ["completed", "failed"])
            
            lob_metrics[lob] = {
                "total_test_cases": total,
                "test_cases_passed": passed,
                "test_cases_failed": failed,
                "test_cases_under_review": under_review,
                "error_rate": (failed / total * 100) if total > 0 else 0
            }
        
        return lob_metrics