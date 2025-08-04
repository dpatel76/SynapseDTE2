"""Report Owner and Report Owner Executive specific metrics calculator."""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.metrics.base_metrics_calculator import BaseMetricsCalculator
from app.models.report import Report
# from app.models.report_owner_assignment import ReportOwnerAssignment  # Deprecated - using universal assignments
from app.models.workflow_tracking import WorkflowPhase
from app.models.test_cycle import TestCycle
from app.core.enums import WorkflowPhaseState, ScheduleStatus


class ReportOwnerMetricsCalculator(BaseMetricsCalculator):
    """Calculate metrics specific to Report Owner and Report Owner Executive roles."""
    
    async def get_report_owner_dashboard_metrics(
        self,
        owner_id: str,
        is_executive: bool = False,
        cycle_id: Optional[str] = None,
        time_period: str = "current_cycle"
    ) -> Dict[str, Any]:
        """Get comprehensive dashboard metrics for a report owner."""
        metrics = {
            "summary": {},
            "report_metrics": [],
            "approval_metrics": {},
            "phase_performance": {},
            "quality_metrics": {},
            "cross_cycle_view": []
        }
        
        # Get reports owned by this user
        owned_reports = await self._get_owned_reports(owner_id, is_executive)
        
        # Summary metrics
        metrics["summary"] = await self._calculate_owner_summary(
            owner_id,
            owned_reports,
            cycle_id
        )
        
        # Detailed metrics for each report
        for report in owned_reports:
            # Get metrics across all cycles for this report
            report_metric = await self._calculate_report_metrics_for_owner(
                report["report_id"],
                cycle_id
            )
            metrics["report_metrics"].append(report_metric)
        
        # Approval metrics
        metrics["approval_metrics"] = await self._calculate_approval_metrics(
            owner_id,
            owned_reports,
            cycle_id
        )
        
        # Phase performance
        metrics["phase_performance"] = await self._calculate_phase_performance_for_owner(
            owned_reports,
            cycle_id
        )
        
        # Quality metrics
        metrics["quality_metrics"] = await self._calculate_quality_metrics_for_owner(
            owned_reports,
            cycle_id
        )
        
        # Cross-cycle view
        metrics["cross_cycle_view"] = await self._calculate_cross_cycle_metrics(
            owned_reports
        )
        
        return metrics
    
    async def get_report_comparison_metrics(
        self,
        owner_id: str,
        report_ids: List[str],
        cycle_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Compare metrics across multiple reports owned by the user."""
        comparison = {
            "reports": [],
            "performance_comparison": {},
            "quality_comparison": {},
            "approval_efficiency": {}
        }
        
        for report_id in report_ids:
            if cycle_id:
                report_metrics = await self._calculate_single_report_cycle_metrics(
                    report_id,
                    cycle_id
                )
            else:
                report_metrics = await self._calculate_report_all_cycles_metrics(report_id)
            
            comparison["reports"].append(report_metrics)
        
        # Build comparisons
        comparison["performance_comparison"] = {
            "completion_rates": {},
            "phase_durations": {},
            "sla_compliance": {}
        }
        
        comparison["quality_comparison"] = {
            "error_rates": {},
            "observation_counts": {},
            "first_time_approval_rates": {}
        }
        
        comparison["approval_efficiency"] = {
            "avg_approval_time": {},
            "revision_rates": {},
            "bottleneck_phases": {}
        }
        
        # Populate comparison data
        for report in comparison["reports"]:
            report_name = report["report_name"]
            
            # Performance
            comparison["performance_comparison"]["completion_rates"][report_name] = (
                report["completion_percentage"]
            )
            comparison["performance_comparison"]["sla_compliance"][report_name] = (
                report["sla_compliance"]
            )
            
            # Quality
            comparison["quality_comparison"]["error_rates"][report_name] = (
                report["quality_metrics"]["error_rate"]
            )
            comparison["quality_comparison"]["observation_counts"][report_name] = (
                report["quality_metrics"]["observation_count"]
            )
        
        return comparison
    
    async def _get_owned_reports(
        self,
        owner_id: str,
        is_executive: bool = False
    ) -> List[Dict[str, Any]]:
        """Get reports owned by a user."""
        # TODO: Update to use UniversalAssignment model once migrated
        # For now, query reports directly where the user is the owner
        query = select(
            Report.report_id,
            Report.report_name,
            Report.report_number,
            Report.regulation
        ).where(
            Report.report_owner_id == int(owner_id)
        )
        
        result = await self.db.execute(query)
        
        reports = []
        for row in result:
            reports.append({
                "report_id": row.report_id,
                "report_name": row.report_name,
                "report_type": row.report_number,  # Using report_number as type
                "regulation": row.regulation
            })
        
        return reports
    
    async def _calculate_owner_summary(
        self,
        owner_id: str,
        owned_reports: List[Dict[str, Any]],
        cycle_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calculate summary metrics for a report owner."""
        summary = {
            "total_reports_owned": len(owned_reports),
            "active_test_cycles": 0,
            "pending_approvals": 0,
            "overdue_approvals": 0,
            "reports_at_risk": 0,
            "reports_on_track": 0,
            "average_approval_time_hours": 0
        }
        
        # Track unique cycles
        active_cycles = set()
        approval_times = []
        
        for report in owned_reports:
            # Get workflow phases for this report
            query = select(WorkflowPhase).where(
                WorkflowPhase.report_id == report["report_id"]
            )
            
            if cycle_id:
                query = query.where(WorkflowPhase.cycle_id == cycle_id)
            
            result = await self.db.execute(query)
            phases = result.scalars().all()
            
            # Track active cycles
            for phase in phases:
                if phase.state != WorkflowPhaseState.NOT_STARTED:
                    active_cycles.add(phase.cycle_id)
                
                # Check for pending approvals
                if phase.phase_data:
                    if phase.phase_data.get("pending_approval", False):
                        summary["pending_approvals"] += 1
                        
                        # Check if overdue
                        approval_requested_at = phase.phase_data.get("approval_requested_at")
                        if approval_requested_at:
                            requested_date = datetime.fromisoformat(approval_requested_at)
                            if datetime.utcnow() - requested_date > timedelta(days=2):
                                summary["overdue_approvals"] += 1
                    
                    # Track approval times
                    approval_time = phase.phase_data.get("approval_duration_hours")
                    if approval_time:
                        approval_times.append(approval_time)
            
            # Check report status
            any_at_risk = any(p.schedule_status == ScheduleStatus.AT_RISK for p in phases)
            all_on_track = all(p.schedule_status == ScheduleStatus.ON_TRACK for p in phases)
            
            if any_at_risk:
                summary["reports_at_risk"] += 1
            elif all_on_track:
                summary["reports_on_track"] += 1
        
        summary["active_test_cycles"] = len(active_cycles)
        
        if approval_times:
            summary["average_approval_time_hours"] = sum(approval_times) / len(approval_times)
        
        return summary
    
    async def _calculate_report_metrics_for_owner(
        self,
        report_id: str,
        cycle_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calculate metrics for a specific report owned by user."""
        # Get report details
        report_query = select(Report).where(Report.report_id == report_id)
        report_result = await self.db.execute(report_query)
        report = report_result.scalar_one()
        
        metrics = {
            "report_id": report_id,
            "report_name": report.report_name,
            "report_type": report.report_type,
            "regulation": report.regulation,
            "cycles": []
        }
        
        # Get all cycles for this report
        cycle_query = select(WorkflowPhase.cycle_id.label('cycle_id')).where(
            WorkflowPhase.report_id == report_id
        ).distinct()
        
        if cycle_id:
            cycle_query = cycle_query.where(WorkflowPhase.cycle_id == cycle_id)
        
        cycle_result = await self.db.execute(cycle_query)
        cycle_ids = [row.cycle_id for row in cycle_result]
        
        # Calculate metrics for each cycle
        for cid in cycle_ids:
            cycle_metrics = await self._calculate_single_report_cycle_metrics(report_id, cid)
            metrics["cycles"].append(cycle_metrics)
        
        # Aggregate metrics across cycles
        if metrics["cycles"]:
            metrics["average_completion_rate"] = sum(
                c["completion_percentage"] for c in metrics["cycles"]
            ) / len(metrics["cycles"])
            
            metrics["average_error_rate"] = sum(
                c["quality_metrics"]["error_rate"] for c in metrics["cycles"]
            ) / len(metrics["cycles"])
            
            metrics["trend"] = self._calculate_trend(metrics["cycles"])
        
        return metrics
    
    async def _calculate_single_report_cycle_metrics(
        self,
        report_id: str,
        cycle_id: str
    ) -> Dict[str, Any]:
        """Calculate metrics for a single report in a specific cycle."""
        # Get cycle details
        cycle_query = select(TestCycle).where(TestCycle.cycle_id == cycle_id)
        cycle_result = await self.db.execute(cycle_query)
        cycle = cycle_result.scalar_one()
        
        # Get all phases
        phase_query = select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id
            )
        )
        
        phase_result = await self.db.execute(phase_query)
        phases = phase_result.scalars().all()
        
        completed_phases = sum(1 for p in phases if p.state == WorkflowPhaseState.COMPLETE)
        
        # SLA compliance
        on_time_phases = sum(1 for p in phases if p.schedule_status == ScheduleStatus.ON_TRACK)
        
        # Quality metrics
        error_rates = await self.calculate_error_rates(cycle_id, report_id, "sample")
        observation_count = await self._count_confirmed_observations(cycle_id, report_id)
        
        # Approval metrics
        approval_metrics = await self._calculate_report_approval_metrics(cycle_id, report_id)
        
        return {
            "cycle_id": cycle_id,
            "cycle_name": cycle.cycle_name,
            "completion_percentage": (completed_phases / len(phases) * 100) if phases else 0,
            "phases_completed": completed_phases,
            "total_phases": len(phases),
            "sla_compliance": (on_time_phases / len(phases) * 100) if phases else 0,
            "quality_metrics": {
                "error_rate": error_rates.get("error_rate", 0),
                "observation_count": observation_count
            },
            "approval_metrics": approval_metrics,
            "current_status": self._determine_report_status(phases)
        }
    
    async def _calculate_approval_metrics(
        self,
        owner_id: str,
        owned_reports: List[Dict[str, Any]],
        cycle_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calculate approval-related metrics for report owner."""
        metrics = {
            "total_approvals_given": 0,
            "pending_approvals": [],
            "approval_turnaround_time": {},
            "revision_statistics": {},
            "approval_by_phase": {}
        }
        
        # Track approvals by phase
        phase_approvals = {}
        
        for report in owned_reports:
            # Query phases requiring approval
            query = select(WorkflowPhase).where(
                WorkflowPhase.report_id == report["report_id"]
            )
            
            if cycle_id:
                query = query.where(WorkflowPhase.cycle_id == cycle_id)
            
            result = await self.db.execute(query)
            phases = result.scalars().all()
            
            for phase in phases:
                if phase.phase_data:
                    # Check approval status
                    if phase.phase_data.get("approved_by") == owner_id:
                        metrics["total_approvals_given"] += 1
                        
                        # Track by phase
                        if phase.phase_name not in phase_approvals:
                            phase_approvals[phase.phase_name] = {
                                "approved": 0,
                                "rejected": 0,
                                "avg_time": []
                            }
                        
                        phase_approvals[phase.phase_name]["approved"] += 1
                        
                        # Track approval time
                        approval_time = phase.phase_data.get("approval_duration_hours")
                        if approval_time:
                            phase_approvals[phase.phase_name]["avg_time"].append(approval_time)
                    
                    # Check for pending approvals
                    if phase.phase_data.get("pending_approval", False):
                        metrics["pending_approvals"].append({
                            "report_name": report["report_name"],
                            "phase_name": phase.phase_name,
                            "cycle_id": phase.cycle_id,
                            "requested_at": phase.phase_data.get("approval_requested_at"),
                            "urgency": self._calculate_approval_urgency(phase)
                        })
        
        # Calculate averages
        for phase_name, data in phase_approvals.items():
            metrics["approval_by_phase"][phase_name] = {
                "total_approved": data["approved"],
                "total_rejected": data["rejected"],
                "avg_turnaround_hours": (
                    sum(data["avg_time"]) / len(data["avg_time"])
                    if data["avg_time"] else 0
                )
            }
        
        # Sort pending approvals by urgency
        metrics["pending_approvals"].sort(
            key=lambda x: x["urgency"],
            reverse=True
        )
        
        return metrics
    
    async def _calculate_phase_performance_for_owner(
        self,
        owned_reports: List[Dict[str, Any]],
        cycle_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calculate phase performance metrics for owned reports."""
        performance = {}
        
        for phase_name in ["Planning", "Data Profiling", "Scoping", "CycleReportSampleSelectionSamples Selection",
                          "Data Provider Identification", "Request for Information",
                          "Test Execution", "Observation Management"]:
            performance[phase_name] = {
                "avg_duration_days": 0,
                "on_time_rate": 0,
                "revision_rate": 0,
                "bottleneck_score": 0
            }
            
            durations = []
            on_time_count = 0
            total_count = 0
            revision_count = 0
            
            for report in owned_reports:
                query = select(WorkflowPhase).where(
                    and_(
                        WorkflowPhase.report_id == report["report_id"],
                        WorkflowPhase.phase_name == phase_name
                    )
                )
                
                if cycle_id:
                    query = query.where(WorkflowPhase.cycle_id == cycle_id)
                
                result = await self.db.execute(query)
                phases = result.scalars().all()
                
                for phase in phases:
                    total_count += 1
                    
                    # Duration
                    if phase.actual_start_date and phase.actual_end_date:
                        duration = (phase.actual_end_date - phase.actual_start_date).days
                        durations.append(duration)
                    
                    # On-time
                    if phase.schedule_status == ScheduleStatus.ON_TRACK:
                        on_time_count += 1
                    
                    # Revisions
                    if phase.phase_data and phase.phase_data.get("submission_count", 0) > 1:
                        revision_count += 1
            
            # Calculate metrics
            if durations:
                performance[phase_name]["avg_duration_days"] = sum(durations) / len(durations)
            
            if total_count > 0:
                performance[phase_name]["on_time_rate"] = (on_time_count / total_count) * 100
                performance[phase_name]["revision_rate"] = (revision_count / total_count) * 100
                
                # Bottleneck score (combination of duration and revision rate)
                performance[phase_name]["bottleneck_score"] = (
                    performance[phase_name]["avg_duration_days"] * 0.5 +
                    performance[phase_name]["revision_rate"] * 0.5
                )
        
        return performance
    
    async def _calculate_quality_metrics_for_owner(
        self,
        owned_reports: List[Dict[str, Any]],
        cycle_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calculate quality metrics for owned reports."""
        quality = {
            "overall_error_rate": 0,
            "observation_density": 0,
            "data_quality_score": 0,
            "by_report": {},
            "trending": []
        }
        
        total_error_rate = 0
        total_observations = 0
        report_count = 0
        
        for report in owned_reports:
            if cycle_id:
                # Single cycle metrics
                error_rates = await self.calculate_error_rates(
                    cycle_id,
                    report["report_id"],
                    "sample"
                )
                observations = await self._count_confirmed_observations(
                    cycle_id,
                    report["report_id"]
                )
                
                quality["by_report"][report["report_name"]] = {
                    "error_rate": error_rates.get("error_rate", 0),
                    "observation_count": observations
                }
                
                total_error_rate += error_rates.get("error_rate", 0)
                total_observations += observations
                report_count += 1
            else:
                # Aggregate across all cycles
                cycle_query = select(WorkflowPhase.cycle_id.label('cycle_id')).where(
                    WorkflowPhase.report_id == report["report_id"]
                ).distinct()
                
                cycle_result = await self.db.execute(cycle_query)
                cycles = [row.cycle_id for row in cycle_result]
                
                report_error_rate = 0
                report_observations = 0
                
                for cid in cycles:
                    error_rates = await self.calculate_error_rates(
                        cid,
                        report["report_id"],
                        "sample"
                    )
                    observations = await self._count_confirmed_observations(
                        cid,
                        report["report_id"]
                    )
                    
                    report_error_rate += error_rates.get("error_rate", 0)
                    report_observations += observations
                
                if cycles:
                    avg_error_rate = report_error_rate / len(cycles)
                    quality["by_report"][report["report_name"]] = {
                        "error_rate": avg_error_rate,
                        "observation_count": report_observations
                    }
                    
                    total_error_rate += avg_error_rate
                    total_observations += report_observations
                    report_count += 1
        
        # Calculate overall metrics
        if report_count > 0:
            quality["overall_error_rate"] = total_error_rate / report_count
            quality["observation_density"] = total_observations / report_count
            
            # Simple data quality score (inverse of error rate)
            quality["data_quality_score"] = max(0, 100 - quality["overall_error_rate"])
        
        return quality
    
    async def _calculate_cross_cycle_metrics(
        self,
        owned_reports: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Calculate metrics across multiple cycles for owned reports."""
        cross_cycle = []
        
        # Get all unique cycles
        cycle_ids = set()
        for report in owned_reports:
            cycle_query = select(WorkflowPhase.cycle_id.label('cycle_id')).where(
                WorkflowPhase.report_id == report["report_id"]
            ).distinct()
            
            cycle_result = await self.db.execute(cycle_query)
            cycle_ids.update(row.cycle_id for row in cycle_result)
        
        # Calculate metrics for each cycle
        for cycle_id in cycle_ids:
            cycle_metrics = {
                "cycle_id": cycle_id,
                "reports_in_cycle": 0,
                "avg_completion_rate": 0,
                "avg_error_rate": 0,
                "total_observations": 0
            }
            
            completion_rates = []
            error_rates = []
            
            for report in owned_reports:
                # Check if report is in this cycle
                phase_check = select(func.count(WorkflowPhase.phase_id)).where(
                    and_(
                        WorkflowPhase.cycle_id == cycle_id,
                        WorkflowPhase.report_id == report["report_id"]
                    )
                )
                
                check_result = await self.db.execute(phase_check)
                if check_result.scalar() > 0:
                    cycle_metrics["reports_in_cycle"] += 1
                    
                    # Get completion rate
                    report_cycle_metrics = await self._calculate_single_report_cycle_metrics(
                        report["report_id"],
                        cycle_id
                    )
                    
                    completion_rates.append(report_cycle_metrics["completion_percentage"])
                    error_rates.append(report_cycle_metrics["quality_metrics"]["error_rate"])
                    cycle_metrics["total_observations"] += (
                        report_cycle_metrics["quality_metrics"]["observation_count"]
                    )
            
            # Calculate averages
            if completion_rates:
                cycle_metrics["avg_completion_rate"] = sum(completion_rates) / len(completion_rates)
            if error_rates:
                cycle_metrics["avg_error_rate"] = sum(error_rates) / len(error_rates)
            
            cross_cycle.append(cycle_metrics)
        
        # Sort by cycle (newest first)
        cross_cycle.sort(key=lambda x: x["cycle_id"], reverse=True)
        
        return cross_cycle
    
    async def _calculate_report_approval_metrics(
        self,
        cycle_id: str,
        report_id: str
    ) -> Dict[str, Any]:
        """Calculate approval metrics for a specific report."""
        approval_metrics = {
            "total_submissions": 0,
            "first_time_approvals": 0,
            "avg_approval_time_hours": 0,
            "revision_rate": 0
        }
        
        query = select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id
            )
        )
        
        result = await self.db.execute(query)
        phases = result.scalars().all()
        
        approval_times = []
        
        for phase in phases:
            if phase.phase_data:
                submissions = phase.phase_data.get("submission_count", 0)
                if submissions > 0:
                    approval_metrics["total_submissions"] += 1
                    if submissions == 1:
                        approval_metrics["first_time_approvals"] += 1
                    
                    approval_time = phase.phase_data.get("approval_duration_hours")
                    if approval_time:
                        approval_times.append(approval_time)
        
        if approval_metrics["total_submissions"] > 0:
            approval_metrics["revision_rate"] = (
                (approval_metrics["total_submissions"] - approval_metrics["first_time_approvals"]) /
                approval_metrics["total_submissions"] * 100
            )
        
        if approval_times:
            approval_metrics["avg_approval_time_hours"] = sum(approval_times) / len(approval_times)
        
        return approval_metrics
    
    def _determine_report_status(self, phases: List[WorkflowPhase]) -> str:
        """Determine overall report status based on phases."""
        if all(p.state == WorkflowPhaseState.COMPLETE for p in phases):
            return "completed"
        elif any(p.schedule_status == ScheduleStatus.PAST_DUE for p in phases):
            return "past_due"
        elif any(p.schedule_status == ScheduleStatus.AT_RISK for p in phases):
            return "at_risk"
        elif any(p.state == WorkflowPhaseState.IN_PROGRESS for p in phases):
            return "in_progress"
        else:
            return "not_started"
    
    def _calculate_approval_urgency(self, phase: WorkflowPhase) -> int:
        """Calculate urgency score for pending approval (higher = more urgent)."""
        urgency = 0
        
        # Check how long it's been pending
        if phase.phase_data:
            requested_at = phase.phase_data.get("approval_requested_at")
            if requested_at:
                requested_date = datetime.fromisoformat(requested_at)
                days_pending = (datetime.utcnow() - requested_date).days
                urgency += min(days_pending * 10, 50)  # Max 50 points for time
        
        # Check phase schedule status
        if phase.schedule_status == ScheduleStatus.PAST_DUE:
            urgency += 30
        elif phase.schedule_status == ScheduleStatus.AT_RISK:
            urgency += 20
        
        # Check if blocking other phases
        if phase.phase_name in ["Planning", "Scoping", "CycleReportSampleSelectionSamples Selection"]:
            urgency += 20  # Critical path phases
        
        return urgency
    
    def _calculate_trend(self, cycles: List[Dict[str, Any]]) -> str:
        """Calculate trend direction based on recent cycles."""
        if len(cycles) < 2:
            return "stable"
        
        # Sort by cycle (newest first)
        sorted_cycles = sorted(cycles, key=lambda x: x["cycle_id"], reverse=True)
        
        # Compare last two cycles
        latest = sorted_cycles[0]
        previous = sorted_cycles[1]
        
        # Compare completion rates
        if latest["completion_percentage"] > previous["completion_percentage"] + 5:
            return "improving"
        elif latest["completion_percentage"] < previous["completion_percentage"] - 5:
            return "declining"
        else:
            return "stable"