"""Test Executive-specific metrics calculator."""
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.metrics.base_metrics_calculator import BaseMetricsCalculator
from app.models.test_cycle import TestCycle
from app.models.workflow_tracking import WorkflowPhase
from app.models.report import Report
from app.core.enums import WorkflowPhaseState, ScheduleStatus


class TestExecutiveMetricsCalculator(BaseMetricsCalculator):
    """Calculate metrics specific to the Test Executive role."""
    
    async def get_test_executive_dashboard_metrics(
        self,
        executive_id: str,
        cycle_id: Optional[str] = None,
        time_period: str = "current_cycle"
    ) -> Dict[str, Any]:
        """Get comprehensive dashboard metrics for a test executive."""
        metrics = {
            "executive_summary": {},
            "cycle_metrics": [],
            "report_breakdown": {},
            "tester_performance": {},
            "sla_compliance": {},
            "trend_analysis": {}
        }
        
        # Get test cycles managed by this executive
        managed_cycles = await self._get_managed_cycles(executive_id, cycle_id)
        
        # Executive summary
        metrics["executive_summary"] = await self._calculate_executive_summary(
            executive_id,
            managed_cycles
        )
        
        # Detailed metrics for each cycle
        for cycle in managed_cycles:
            cycle_metric = await self._calculate_cycle_metrics(cycle["cycle_id"])
            metrics["cycle_metrics"].append(cycle_metric)
        
        # Report breakdown across all cycles
        metrics["report_breakdown"] = await self._calculate_report_breakdown(
            managed_cycles
        )
        
        # Tester performance metrics
        metrics["tester_performance"] = await self._calculate_tester_performance(
            managed_cycles
        )
        
        # SLA compliance
        metrics["sla_compliance"] = await self._calculate_sla_compliance_summary(
            managed_cycles
        )
        
        # Trend analysis
        metrics["trend_analysis"] = await self._calculate_trend_analysis(
            executive_id,
            time_period
        )
        
        return metrics
    
    async def get_cycle_comparison_metrics(
        self,
        executive_id: str,
        cycle_ids: List[str]
    ) -> Dict[str, Any]:
        """Compare metrics across multiple test cycles."""
        comparison = {
            "cycles": [],
            "performance_comparison": {},
            "quality_comparison": {},
            "efficiency_comparison": {}
        }
        
        for cycle_id in cycle_ids:
            cycle_metrics = await self._calculate_cycle_metrics(cycle_id)
            comparison["cycles"].append(cycle_metrics)
        
        # Performance comparison
        comparison["performance_comparison"] = {
            "completion_rate": {},
            "on_time_delivery": {},
            "average_duration": {}
        }
        
        # Quality comparison
        comparison["quality_comparison"] = {
            "error_rates": {},
            "first_time_approval": {},
            "observation_density": {}
        }
        
        # Efficiency comparison
        comparison["efficiency_comparison"] = {
            "resource_utilization": {},
            "productivity_metrics": {},
            "bottleneck_analysis": {}
        }
        
        # Populate comparisons
        for cycle in comparison["cycles"]:
            cycle_name = cycle["cycle_name"]
            
            # Performance
            comparison["performance_comparison"]["completion_rate"][cycle_name] = (
                cycle["summary"]["completion_percentage"]
            )
            comparison["performance_comparison"]["on_time_delivery"][cycle_name] = (
                cycle["sla_metrics"]["on_time_percentage"]
            )
            
            # Quality
            comparison["quality_comparison"]["error_rates"][cycle_name] = (
                cycle["quality_metrics"]["overall_error_rate"]
            )
            
        return comparison
    
    async def _get_managed_cycles(
        self,
        executive_id: str,
        cycle_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get test cycles managed by an executive."""
        query = select(TestCycle).where(
            or_(
                TestCycle.created_by == executive_id,
                TestCycle.executive_id == executive_id  # Assuming executive assignment field
            )
        )
        
        if cycle_id:
            query = query.where(TestCycle.cycle_id == cycle_id)
        
        result = await self.db.execute(query)
        cycles = result.scalars().all()
        
        return [
            {
                "cycle_id": cycle.cycle_id,
                "cycle_name": cycle.cycle_name,
                "start_date": cycle.start_date,
                "end_date": cycle.end_date,
                "status": cycle.status
            }
            for cycle in cycles
        ]
    
    async def _calculate_executive_summary(
        self,
        executive_id: str,
        managed_cycles: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate executive summary metrics."""
        summary = {
            "total_cycles_managed": len(managed_cycles),
            "active_cycles": 0,
            "completed_cycles": 0,
            "total_reports": 0,
            "reports_completed": 0,
            "overall_sla_compliance": 0,
            "critical_issues": 0,
            "resource_allocation": {}
        }
        
        total_phases = 0
        on_time_phases = 0
        
        for cycle in managed_cycles:
            if cycle["status"] == "active":
                summary["active_cycles"] += 1
            elif cycle["status"] == "completed":
                summary["completed_cycles"] += 1
            
            # Get reports in cycle
            report_query = select(WorkflowPhase.report_id).where(
                WorkflowPhase.cycle_id == cycle["cycle_id"]
            ).distinct()
            
            report_result = await self.db.execute(report_query)
            report_count = len(report_result.all())
            summary["total_reports"] += report_count
            
            # Count completed reports
            completed_query = select(WorkflowPhase.report_id).where(
                and_(
                    WorkflowPhase.cycle_id == cycle["cycle_id"],
                    WorkflowPhase.phase_name == "Finalize Test Report",
                    WorkflowPhase.state == WorkflowPhaseState.COMPLETE
                )
            ).distinct()
            
            completed_result = await self.db.execute(completed_query)
            summary["reports_completed"] += len(completed_result.all())
            
            # SLA compliance
            sla_metrics = await self.calculate_sla_compliance(cycle["cycle_id"])
            total_phases += sla_metrics["total_phases"]
            on_time_phases += sla_metrics["on_time"]
            
            # Critical issues (past due phases)
            summary["critical_issues"] += sla_metrics["past_due"]
        
        # Calculate overall SLA compliance
        if total_phases > 0:
            summary["overall_sla_compliance"] = (on_time_phases / total_phases) * 100
        
        return summary
    
    async def _calculate_cycle_metrics(self, cycle_id: str) -> Dict[str, Any]:
        """Calculate detailed metrics for a single cycle."""
        # Get cycle details
        cycle_query = select(TestCycle).where(TestCycle.cycle_id == cycle_id)
        cycle_result = await self.db.execute(cycle_query)
        cycle = cycle_result.scalar_one()
        
        metrics = {
            "cycle_id": cycle_id,
            "cycle_name": cycle.cycle_name,
            "status": cycle.status,
            "summary": await self.aggregate_report_metrics(cycle_id),
            "phase_metrics": {},
            "report_metrics": [],
            "sla_metrics": await self.calculate_sla_compliance(cycle_id),
            "quality_metrics": {},
            "timeline_metrics": {}
        }
        
        # Phase breakdown
        for phase_name in ["Planning", "Data Profiling", "Scoping", "CycleReportSampleSelectionSamples Selection",
                          "Data Provider Identification", "Request for Information",
                          "Test Execution", "Observation Management"]:
            phase_query = select(
                func.count(WorkflowPhase.phase_id).label("total"),
                func.sum(func.cast(WorkflowPhase.state == WorkflowPhaseState.COMPLETE, func.Integer)).label("completed"),
                func.sum(func.cast(WorkflowPhase.state == WorkflowPhaseState.IN_PROGRESS, func.Integer)).label("in_progress"),
                func.avg(
                    func.extract('epoch', WorkflowPhase.actual_end_date - WorkflowPhase.actual_start_date) / 3600
                ).label("avg_duration_hours")
            ).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.phase_name == phase_name
                )
            )
            
            phase_result = await self.db.execute(phase_query)
            phase_data = phase_result.one()
            
            metrics["phase_metrics"][phase_name] = {
                "total": phase_data.total or 0,
                "completed": phase_data.completed or 0,
                "in_progress": phase_data.in_progress or 0,
                "not_started": (phase_data.total or 0) - (phase_data.completed or 0) - (phase_data.in_progress or 0),
                "avg_duration_hours": float(phase_data.avg_duration_hours or 0),
                "completion_rate": ((phase_data.completed or 0) / phase_data.total * 100) if phase_data.total else 0
            }
        
        # Get report-level metrics
        report_query = select(WorkflowPhase.report_id).where(
            WorkflowPhase.cycle_id == cycle_id
        ).distinct()
        
        report_result = await self.db.execute(report_query)
        report_ids = [row[0] for row in report_result]
        
        for report_id in report_ids:
            report_metric = await self._calculate_report_summary_for_executive(cycle_id, report_id)
            metrics["report_metrics"].append(report_metric)
        
        # Quality metrics
        metrics["quality_metrics"] = await self._calculate_cycle_quality_metrics(cycle_id)
        
        # Timeline metrics
        metrics["timeline_metrics"] = await self._calculate_cycle_timeline_metrics(cycle_id)
        
        return metrics
    
    async def _calculate_report_breakdown(
        self,
        managed_cycles: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate report breakdown across all managed cycles."""
        breakdown = {
            "by_status": {
                "completed": 0,
                "in_progress": 0,
                "not_started": 0,
                "at_risk": 0
            },
            "by_report_type": {},
            "by_phase": {},
            "critical_reports": []
        }
        
        for cycle in managed_cycles:
            # Get all reports in cycle
            report_query = select(
                WorkflowPhase.report_id,
                Report.report_name,
                Report.report_type,
                func.bool_and(WorkflowPhase.state == WorkflowPhaseState.COMPLETE).label("all_complete"),
                func.bool_or(WorkflowPhase.state != WorkflowPhaseState.NOT_STARTED).label("any_started"),
                func.bool_or(WorkflowPhase.schedule_status == ScheduleStatus.AT_RISK).label("at_risk")
            ).join(
                Report, Report.report_id == WorkflowPhase.report_id
            ).where(
                WorkflowPhase.cycle_id == cycle["cycle_id"]
            ).group_by(
                WorkflowPhase.report_id,
                Report.report_name,
                Report.report_type
            )
            
            report_result = await self.db.execute(report_query)
            
            for row in report_result:
                # Status breakdown
                if row.all_complete:
                    breakdown["by_status"]["completed"] += 1
                elif row.any_started:
                    breakdown["by_status"]["in_progress"] += 1
                else:
                    breakdown["by_status"]["not_started"] += 1
                
                if row.at_risk:
                    breakdown["by_status"]["at_risk"] += 1
                    breakdown["critical_reports"].append({
                        "cycle_id": cycle["cycle_id"],
                        "report_id": row.report_id,
                        "report_name": row.report_name,
                        "reason": "At risk of missing deadline"
                    })
                
                # By report type
                if row.report_type not in breakdown["by_report_type"]:
                    breakdown["by_report_type"][row.report_type] = 0
                breakdown["by_report_type"][row.report_type] += 1
        
        return breakdown
    
    async def _calculate_tester_performance(
        self,
        managed_cycles: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate tester performance metrics across cycles."""
        tester_metrics = {}
        
        for cycle in managed_cycles:
            # Get all testers working on this cycle
            tester_query = select(
                WorkflowPhase.started_by,
                func.count(WorkflowPhase.phase_id).label("phases_handled"),
                func.avg(
                    func.extract('epoch', WorkflowPhase.actual_end_date - WorkflowPhase.actual_start_date) / 3600
                ).label("avg_completion_time"),
                func.sum(
                    func.cast(
                        and_(
                            WorkflowPhase.actual_end_date != None,
                            WorkflowPhase.planned_end_date != None,
                            WorkflowPhase.actual_end_date <= WorkflowPhase.planned_end_date
                        ),
                        func.Integer
                    )
                ).label("on_time_completions")
            ).where(
                and_(
                    WorkflowPhase.cycle_id == cycle["cycle_id"],
                    WorkflowPhase.started_by != None
                )
            ).group_by(WorkflowPhase.started_by)
            
            tester_result = await self.db.execute(tester_query)
            
            for row in tester_result:
                tester_id = row.started_by
                
                if tester_id not in tester_metrics:
                    tester_metrics[tester_id] = {
                        "total_phases": 0,
                        "total_completion_time": 0,
                        "on_time_completions": 0,
                        "cycles_worked": 0
                    }
                
                tester_metrics[tester_id]["total_phases"] += row.phases_handled
                tester_metrics[tester_id]["total_completion_time"] += (
                    row.avg_completion_time * row.phases_handled if row.avg_completion_time else 0
                )
                tester_metrics[tester_id]["on_time_completions"] += row.on_time_completions or 0
                tester_metrics[tester_id]["cycles_worked"] += 1
        
        # Calculate final metrics
        performance = {
            "testers": [],
            "top_performers": [],
            "improvement_needed": []
        }
        
        for tester_id, metrics in tester_metrics.items():
            avg_completion = (
                metrics["total_completion_time"] / metrics["total_phases"]
                if metrics["total_phases"] > 0 else 0
            )
            on_time_rate = (
                metrics["on_time_completions"] / metrics["total_phases"] * 100
                if metrics["total_phases"] > 0 else 0
            )
            
            tester_perf = {
                "tester_id": tester_id,
                "phases_completed": metrics["total_phases"],
                "average_completion_hours": avg_completion,
                "on_time_rate": on_time_rate,
                "cycles_worked": metrics["cycles_worked"]
            }
            
            performance["testers"].append(tester_perf)
            
            # Categorize performance
            if on_time_rate >= 90:
                performance["top_performers"].append(tester_id)
            elif on_time_rate < 70:
                performance["improvement_needed"].append(tester_id)
        
        # Sort by performance
        performance["testers"].sort(key=lambda x: x["on_time_rate"], reverse=True)
        
        return performance
    
    async def _calculate_sla_compliance_summary(
        self,
        managed_cycles: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate SLA compliance summary across all cycles."""
        summary = {
            "overall_compliance": 0,
            "by_phase": {},
            "by_cycle": {},
            "trending": [],
            "breaches": []
        }
        
        total_phases = 0
        compliant_phases = 0
        
        for cycle in managed_cycles:
            cycle_sla = await self.calculate_sla_compliance(cycle["cycle_id"])
            
            total_phases += cycle_sla["total_phases"]
            compliant_phases += cycle_sla["on_time"]
            
            summary["by_cycle"][cycle["cycle_name"]] = {
                "compliance_rate": cycle_sla["on_time_percentage"],
                "at_risk": cycle_sla["at_risk"],
                "breached": cycle_sla["past_due"]
            }
            
            # Track breaches
            if cycle_sla["past_due"] > 0:
                # Get specific breach details
                breach_query = select(
                    WorkflowPhase.report_id,
                    WorkflowPhase.phase_name,
                    WorkflowPhase.planned_end_date,
                    WorkflowPhase.actual_end_date
                ).where(
                    and_(
                        WorkflowPhase.cycle_id == cycle["cycle_id"],
                        WorkflowPhase.schedule_status == ScheduleStatus.PAST_DUE
                    )
                )
                
                breach_result = await self.db.execute(breach_query)
                
                for breach in breach_result:
                    delay_days = None
                    if breach.actual_end_date and breach.planned_end_date:
                        delay_days = (breach.actual_end_date - breach.planned_end_date).days
                    
                    summary["breaches"].append({
                        "cycle_name": cycle["cycle_name"],
                        "report_id": breach.report_id,
                        "phase_name": breach.phase_name,
                        "planned_date": breach.planned_end_date,
                        "actual_date": breach.actual_end_date,
                        "delay_days": delay_days
                    })
        
        # Overall compliance
        if total_phases > 0:
            summary["overall_compliance"] = (compliant_phases / total_phases) * 100
        
        # By phase breakdown
        for phase_name in ["Planning", "Data Profiling", "Scoping", "CycleReportSampleSelectionSamples Selection",
                          "Data Provider Identification", "Request for Information",
                          "Test Execution", "Observation Management"]:
            phase_total = 0
            phase_compliant = 0
            
            for cycle in managed_cycles:
                phase_sla = await self.calculate_sla_compliance(
                    cycle["cycle_id"],
                    phase_name=phase_name
                )
                phase_total += phase_sla["total_phases"]
                phase_compliant += phase_sla["on_time"]
            
            if phase_total > 0:
                summary["by_phase"][phase_name] = (phase_compliant / phase_total) * 100
            else:
                summary["by_phase"][phase_name] = 100.0
        
        return summary
    
    async def _calculate_trend_analysis(
        self,
        executive_id: str,
        time_period: str
    ) -> Dict[str, Any]:
        """Calculate trend analysis for executive metrics."""
        trends = {
            "completion_rate_trend": [],
            "sla_compliance_trend": [],
            "quality_trend": [],
            "efficiency_trend": []
        }
        
        # This would typically query historical data
        # For now, returning structure
        
        return trends
    
    async def _calculate_report_summary_for_executive(
        self,
        cycle_id: str,
        report_id: str
    ) -> Dict[str, Any]:
        """Calculate report summary for executive view."""
        # Get report details
        report_query = select(Report).where(Report.report_id == report_id)
        report_result = await self.db.execute(report_query)
        report = report_result.scalar_one()
        
        # Get phase summary
        phase_query = select(
            WorkflowPhase.phase_name,
            WorkflowPhase.state,
            WorkflowPhase.schedule_status,
            WorkflowPhase.started_by,
            WorkflowPhase.actual_start_date,
            WorkflowPhase.actual_end_date,
            WorkflowPhase.planned_end_date
        ).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id
            )
        )
        
        phase_result = await self.db.execute(phase_query)
        phases = phase_result.all()
        
        completed_phases = sum(1 for p in phases if p.state == WorkflowPhaseState.COMPLETE)
        current_phase = next((p.phase_name for p in phases if p.state == WorkflowPhaseState.IN_PROGRESS), None)
        
        # Calculate overall status
        all_complete = all(p.state == WorkflowPhaseState.COMPLETE for p in phases)
        any_at_risk = any(p.schedule_status == ScheduleStatus.AT_RISK for p in phases)
        any_past_due = any(p.schedule_status == ScheduleStatus.PAST_DUE for p in phases)
        
        overall_status = "completed" if all_complete else "at_risk" if any_at_risk else "past_due" if any_past_due else "on_track"
        
        # Get quality metrics
        error_rates = await self.calculate_error_rates(cycle_id, report_id, "sample")
        
        return {
            "report_id": report_id,
            "report_name": report.report_name,
            "report_type": report.report_type,
            "overall_status": overall_status,
            "phases_completed": completed_phases,
            "total_phases": len(phases),
            "current_phase": current_phase,
            "completion_percentage": (completed_phases / len(phases) * 100) if phases else 0,
            "error_rate": error_rates.get("error_rate", 0),
            "assigned_testers": list(set(p.started_by for p in phases if p.started_by))
        }
    
    async def _calculate_cycle_quality_metrics(self, cycle_id: str) -> Dict[str, Any]:
        """Calculate quality metrics for a cycle."""
        # Get all reports in cycle
        report_query = select(WorkflowPhase.report_id).where(
            WorkflowPhase.cycle_id == cycle_id
        ).distinct()
        
        report_result = await self.db.execute(report_query)
        report_ids = [row[0] for row in report_result]
        
        total_error_rate = 0
        total_observation_count = 0
        
        for report_id in report_ids:
            # CycleReportSampleSelectionSamples error rate
            sample_errors = await self.calculate_error_rates(cycle_id, report_id, "sample")
            total_error_rate += sample_errors.get("error_rate", 0)
            
            # Observation count
            obs_count = await self._count_confirmed_observations(cycle_id, report_id)
            total_observation_count += obs_count
        
        avg_error_rate = total_error_rate / len(report_ids) if report_ids else 0
        
        return {
            "overall_error_rate": avg_error_rate,
            "total_observations": total_observation_count,
            "observation_density": total_observation_count / len(report_ids) if report_ids else 0
        }
    
    async def _calculate_cycle_timeline_metrics(self, cycle_id: str) -> Dict[str, Any]:
        """Calculate timeline metrics for a cycle."""
        # Get cycle dates
        cycle_query = select(TestCycle).where(TestCycle.cycle_id == cycle_id)
        cycle_result = await self.db.execute(cycle_query)
        cycle = cycle_result.scalar_one()
        
        # Calculate progress
        total_days = (cycle.end_date - cycle.start_date).days if cycle.end_date else None
        elapsed_days = (datetime.utcnow().date() - cycle.start_date).days if cycle.start_date else None
        
        # Get phase timeline data
        phase_query = select(
            func.min(WorkflowPhase.actual_start_date).label("first_start"),
            func.max(WorkflowPhase.actual_end_date).label("last_end")
        ).where(WorkflowPhase.cycle_id == cycle_id)
        
        phase_result = await self.db.execute(phase_query)
        phase_data = phase_result.one()
        
        actual_duration = None
        if phase_data.first_start and phase_data.last_end:
            actual_duration = (phase_data.last_end - phase_data.first_start).days
        
        return {
            "planned_duration_days": total_days,
            "elapsed_days": elapsed_days,
            "actual_duration_days": actual_duration,
            "progress_percentage": (elapsed_days / total_days * 100) if total_days and elapsed_days else 0,
            "ahead_behind_schedule": "on_schedule"  # Would calculate based on actual vs planned
        }