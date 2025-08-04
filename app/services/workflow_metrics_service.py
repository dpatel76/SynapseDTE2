"""Workflow Metrics and Analytics Service

Provides insights into workflow performance, timing, and bottlenecks.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func, and_, Integer
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from enum import Enum

from app.models import WorkflowPhase, TestCycle, Report, CycleReport
from app.models.workflow import workflow_phase_enum, phase_status_enum

logger = logging.getLogger(__name__)


class MetricPeriod(str, Enum):
    """Time periods for metric aggregation"""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class WorkflowMetricsService:
    """Service for analyzing workflow metrics and performance"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_workflow_metrics(
        self,
        cycle_id: Optional[int] = None,
        report_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        period: MetricPeriod = MetricPeriod.DAILY
    ) -> Dict[str, Any]:
        """Get comprehensive workflow metrics"""
        
        # Build filters
        filters = []
        if cycle_id:
            filters.append(WorkflowPhase.cycle_id == cycle_id)
        if report_id:
            filters.append(WorkflowPhase.report_id == report_id)
        if start_date:
            filters.append(WorkflowPhase.started_at >= start_date)
        if end_date:
            filters.append(WorkflowPhase.started_at <= end_date)
        
        # Get phase summary
        phase_summary = await self._get_phase_summary(filters)
        
        # Get cycle summary
        cycle_summary = await self._get_cycle_summary(cycle_id)
        
        # Get completion rates
        completion_rates = await self._get_completion_rates(filters)
        
        # Get phase metrics with proper structure
        phase_metrics = await self._get_detailed_phase_metrics(filters)
        
        # Get bottlenecks
        bottlenecks = await self._get_bottlenecks(filters)
        
        # Generate insights
        insights = self._generate_insights(phase_summary, completion_rates, bottlenecks)
        
        return {
            "summary": {
                "total_phases": phase_summary["total"],
                "completed_phases": phase_summary["completed"],
                "in_progress_phases": phase_summary["in_progress"],
                "not_started_phases": phase_summary["not_started"],
                "active_cycles": cycle_summary["active_cycles"],
                "total_reports": cycle_summary["total_reports"]
            },
            "phase_metrics": phase_metrics,
            "completion_rates": completion_rates,
            "bottlenecks": bottlenecks,
            "insights": insights,
            "period": period.value
        }
    
    async def _get_phase_summary(self, filters: List) -> Dict[str, Any]:
        """Get summary of workflow phases"""
        
        # Total phases
        total_query = select(func.count(WorkflowPhase.phase_id))
        if filters:
            total_query = total_query.where(and_(*filters))
        total_result = await self.db.execute(total_query)
        total_count = total_result.scalar() or 0
        
        # Status breakdown
        status_query = select(
            WorkflowPhase.status,
            func.count(WorkflowPhase.phase_id).label("count")
        ).group_by(WorkflowPhase.status)
        if filters:
            status_query = status_query.where(and_(*filters))
        status_result = await self.db.execute(status_query)
        
        status_breakdown = {
            "completed": 0,
            "in_progress": 0,
            "not_started": 0
        }
        
        for row in status_result:
            if row.status == "Complete":
                status_breakdown["completed"] = row.count
            elif row.status == "In Progress":
                status_breakdown["in_progress"] = row.count
            elif row.status == "Not Started":
                status_breakdown["not_started"] = row.count
        
        # Phase type breakdown
        phase_query = select(
            WorkflowPhase.phase_name,
            func.count(WorkflowPhase.phase_id).label("count"),
            func.avg(
                func.extract('epoch', WorkflowPhase.completed_at - WorkflowPhase.started_at)
            ).label("avg_duration")
        ).group_by(WorkflowPhase.phase_name)
        if filters:
            phase_query = phase_query.where(and_(*filters))
        phase_result = await self.db.execute(phase_query)
        
        by_phase = []
        for row in phase_result:
            by_phase.append({
                "phase": row.phase_name,
                "count": row.count,
                "avg_duration_hours": round(row.avg_duration / 3600, 2) if row.avg_duration else None
            })
        
        return {
            "total": total_count,
            "completed": status_breakdown["completed"],
            "in_progress": status_breakdown["in_progress"],
            "not_started": status_breakdown["not_started"],
            "by_phase": by_phase
        }
    
    async def _get_cycle_summary(self, cycle_id: Optional[int]) -> Dict[str, Any]:
        """Get summary of test cycles"""
        
        # Active cycles
        active_query = select(func.count(TestCycle.cycle_id)).where(
            TestCycle.is_active == True
        )
        if cycle_id:
            active_query = active_query.where(TestCycle.cycle_id == cycle_id)
        active_result = await self.db.execute(active_query)
        active_count = active_result.scalar() or 0
        
        # Total reports in cycles
        reports_query = select(func.count(CycleReport.report_id.distinct()))
        if cycle_id:
            reports_query = reports_query.where(CycleReport.cycle_id == cycle_id)
        reports_result = await self.db.execute(reports_query)
        reports_count = reports_result.scalar() or 0
        
        return {
            "active_cycles": active_count,
            "total_reports": reports_count
        }
    
    async def _get_completion_rates(self, filters: List) -> Dict[str, Any]:
        """Calculate completion rates by phase type"""
        
        query = select(
            WorkflowPhase.phase_name,
            func.count(WorkflowPhase.phase_id).label("total"),
            func.count(
                func.case(
                    (WorkflowPhase.status == "Complete", WorkflowPhase.phase_id),
                    else_=None
                )
            ).label("completed")
        ).group_by(WorkflowPhase.phase_name)
        
        if filters:
            query = query.where(and_(*filters))
        
        result = await self.db.execute(query)
        
        rates = {}
        for row in result:
            if row.total > 0:
                rates[row.phase_name] = {
                    "total": row.total,
                    "completed": row.completed,
                    "rate": round((row.completed / row.total) * 100, 2)
                }
        
        return rates
    
    async def compare_phases(
        self,
        phases: List[str],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Compare performance across different phases"""
        
        filters = [WorkflowPhase.phase_name.in_(phases)]
        if start_date:
            filters.append(WorkflowPhase.started_at >= start_date)
        if end_date:
            filters.append(WorkflowPhase.started_at <= end_date)
        
        query = select(
            WorkflowPhase.phase_name,
            func.count(WorkflowPhase.phase_id).label("count"),
            func.avg(
                func.extract('epoch', WorkflowPhase.completed_at - WorkflowPhase.started_at)
            ).label("avg_duration"),
            func.min(
                func.extract('epoch', WorkflowPhase.completed_at - WorkflowPhase.started_at)
            ).label("min_duration"),
            func.max(
                func.extract('epoch', WorkflowPhase.completed_at - WorkflowPhase.started_at)
            ).label("max_duration")
        ).where(
            and_(*filters)
        ).group_by(WorkflowPhase.phase_name)
        
        result = await self.db.execute(query)
        
        comparison = {}
        for row in result:
            comparison[row.phase_name] = {
                "count": row.count,
                "avg_duration_hours": round(row.avg_duration / 3600, 2) if row.avg_duration else None,
                "min_duration_hours": round(row.min_duration / 3600, 2) if row.min_duration else None,
                "max_duration_hours": round(row.max_duration / 3600, 2) if row.max_duration else None
            }
        
        return comparison
    
    async def get_active_workflows(self) -> List[Dict[str, Any]]:
        """Get list of currently active workflows"""
        
        # Get active workflow phases (not completed)
        query = select(WorkflowPhase).where(
            and_(
                WorkflowPhase.state == "In Progress",
                WorkflowPhase.completed_at.is_(None)
            )
        ).order_by(WorkflowPhase.started_at.desc())
        
        result = await self.db.execute(query)
        phases = result.scalars().all()
        
        active_workflows = []
        for phase in phases:
            # Get cycle and report info
            cycle_query = select(TestCycle).where(TestCycle.cycle_id == phase.cycle_id)
            cycle_result = await self.db.execute(cycle_query)
            cycle = cycle_result.scalar_one_or_none()
            
            report_query = select(Report).where(Report.report_id == phase.report_id)
            report_result = await self.db.execute(report_query)
            report = report_result.scalar_one_or_none()
            
            active_workflows.append({
                "phase_id": phase.phase_id,
                "phase_name": phase.phase_name,
                "phase_type": phase.phase_name,
                "cycle_id": phase.cycle_id,
                "cycle_name": cycle.cycle_name if cycle else None,
                "report_id": phase.report_id,
                "report_name": report.report_name if report else None,
                "state": phase.state,
                "started_at": phase.started_at.isoformat() if phase.started_at else None,
                "expected_duration_hours": round(phase.expected_duration_seconds / 3600, 1) if phase.expected_duration_seconds else None,
                "elapsed_hours": round((datetime.now(timezone.utc) - phase.started_at).total_seconds() / 3600, 1) if phase.started_at else 0
            })
        
        return active_workflows
    
    async def get_recent_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent workflow performance alerts"""
        
        alerts = []
        
        # Check for overdue phases
        overdue_query = select(WorkflowPhase).where(
            and_(
                WorkflowPhase.state == "In Progress",
                WorkflowPhase.expected_end_date < datetime.now(timezone.utc),
                WorkflowPhase.completed_at.is_(None)
            )
        ).limit(limit)
        
        result = await self.db.execute(overdue_query)
        overdue_phases = result.scalars().all()
        
        for phase in overdue_phases:
            alerts.append({
                "type": "overdue",
                "severity": "high",
                "phase_id": phase.phase_id,
                "phase_name": phase.phase_name,
                "cycle_id": phase.cycle_id,
                "report_id": phase.report_id,
                "message": f"Phase '{phase.phase_name}' is overdue by {round((datetime.now(timezone.utc) - phase.expected_end_date).total_seconds() / 3600, 1)} hours",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        
        # Check for stalled phases (no update in 24 hours)
        stalled_cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        stalled_query = select(WorkflowPhase).where(
            and_(
                WorkflowPhase.state == "In Progress",
                WorkflowPhase.updated_at < stalled_cutoff,
                WorkflowPhase.completed_at.is_(None)
            )
        ).limit(limit - len(alerts))
        
        result = await self.db.execute(stalled_query)
        stalled_phases = result.scalars().all()
        
        for phase in stalled_phases:
            alerts.append({
                "type": "stalled",
                "severity": "medium",
                "phase_id": phase.phase_id,
                "phase_name": phase.phase_name,
                "cycle_id": phase.cycle_id,
                "report_id": phase.report_id,
                "message": f"Phase '{phase.phase_name}' has not been updated in over 24 hours",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        
        return alerts[:limit]
    
    async def _get_detailed_phase_metrics(self, filters: List) -> List[Dict[str, Any]]:
        """Get detailed metrics for each phase type"""
        
        # Query for phase metrics with success/failure counts
        query = select(
            WorkflowPhase.phase_name,
            func.count(WorkflowPhase.phase_id).label("total_count"),
            func.count(
                func.case(
                    (WorkflowPhase.status == "Complete", WorkflowPhase.phase_id),
                    else_=None
                )
            ).label("success_count"),
            func.count(
                func.case(
                    (WorkflowPhase.status == "Failed", WorkflowPhase.phase_id),
                    else_=None
                )
            ).label("failed_count"),
            func.avg(
                func.case(
                    (WorkflowPhase.status == "Complete",
                     func.extract('epoch', WorkflowPhase.completed_at - WorkflowPhase.started_at)),
                    else_=None
                )
            ).label("avg_duration_seconds")
        ).group_by(WorkflowPhase.phase_name)
        
        if filters:
            query = query.where(and_(*filters))
        
        result = await self.db.execute(query)
        
        phase_metrics = []
        for row in result:
            phase_metrics.append({
                "phase_name": row.phase_name,
                "total_count": row.total_count,
                "success_count": row.success_count or 0,
                "failed_count": row.failed_count or 0,
                "success_rate": round((row.success_count / row.total_count) * 100, 2) if row.total_count > 0 else 0,
                "avg_duration_seconds": row.avg_duration_seconds or 0
            })
        
        return phase_metrics
    
    async def _get_bottlenecks(self, filters: List) -> Dict[str, Any]:
        """Identify workflow bottlenecks"""
        
        # Get time distribution by phase
        time_query = select(
            WorkflowPhase.phase_name.label("phase"),
            func.avg(
                func.extract('epoch', WorkflowPhase.completed_at - WorkflowPhase.started_at)
            ).label("avg_duration"),
            func.min(
                func.extract('epoch', WorkflowPhase.completed_at - WorkflowPhase.started_at)
            ).label("min_duration"),
            func.max(
                func.extract('epoch', WorkflowPhase.completed_at - WorkflowPhase.started_at)
            ).label("max_duration"),
            func.count(WorkflowPhase.phase_id).label("sample_size")
        ).where(
            WorkflowPhase.status == "Complete"
        ).group_by(WorkflowPhase.phase_name)
        
        if filters:
            time_query = time_query.where(and_(*filters))
        
        result = await self.db.execute(time_query)
        
        time_distribution = []
        longest_phases = []
        
        for row in result:
            if row.avg_duration:
                phase_data = {
                    "phase": row.phase,
                    "avg_duration_hours": round(row.avg_duration / 3600, 2),
                    "min_duration_hours": round(row.min_duration / 3600, 2) if row.min_duration else 0,
                    "max_duration_hours": round(row.max_duration / 3600, 2) if row.max_duration else 0,
                    "sample_size": row.sample_size
                }
                time_distribution.append(phase_data)
                
                # Track longest phases
                if row.avg_duration > 0:
                    longest_phases.append({
                        "phase": row.phase,
                        "avg_hours": round(row.avg_duration / 3600, 2)
                    })
        
        # Sort longest phases
        longest_phases.sort(key=lambda x: x["avg_hours"], reverse=True)
        
        # Get stuck phases (in progress for too long)
        stuck_cutoff = datetime.now(timezone.utc) - timedelta(hours=48)
        stuck_query = select(
            WorkflowPhase.phase_name,
            func.count(WorkflowPhase.phase_id).label("count")
        ).where(
            and_(
                WorkflowPhase.state == "In Progress",
                WorkflowPhase.started_at < stuck_cutoff,
                WorkflowPhase.completed_at.is_(None)
            )
        ).group_by(WorkflowPhase.phase_name)
        
        if filters:
            stuck_query = stuck_query.where(and_(*filters))
        
        stuck_result = await self.db.execute(stuck_query)
        
        stuck_phases = []
        for row in stuck_result:
            if row.count > 0:
                stuck_phases.append({
                    "phase": row.phase_name,
                    "count": row.count
                })
        
        return {
            "time_distribution": time_distribution,
            "longest_phases": longest_phases[:5],  # Top 5 longest
            "stuck_phases": stuck_phases
        }
    
    def _generate_insights(
        self,
        phase_summary: Dict[str, Any],
        completion_rates: Dict[str, Any],
        bottlenecks: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate actionable insights from metrics"""
        
        insights = []
        
        # Check overall completion rate
        if phase_summary["total"] > 0:
            overall_completion_rate = (phase_summary["completed"] / phase_summary["total"]) * 100
            if overall_completion_rate < 80:
                insights.append({
                    "type": "warning",
                    "category": "completion",
                    "message": f"Overall completion rate is {overall_completion_rate:.1f}%, below target of 80%",
                    "recommendation": "Review stuck phases and allocate resources to complete pending work"
                })
        
        # Check for low-performing phases
        for phase, metrics in completion_rates.items():
            if metrics["rate"] < 70 and metrics["total"] > 5:
                insights.append({
                    "type": "warning",
                    "category": "phase_performance",
                    "phase": phase,
                    "message": f"{phase} has low completion rate of {metrics['rate']}%",
                    "recommendation": f"Investigate blockers in {phase} phase"
                })
        
        # Check for bottlenecks
        if bottlenecks["longest_phases"]:
            slowest = bottlenecks["longest_phases"][0]
            if slowest["avg_hours"] > 24:
                insights.append({
                    "type": "info",
                    "category": "bottleneck",
                    "phase": slowest["phase"],
                    "message": f"{slowest['phase']} takes {slowest['avg_hours']} hours on average",
                    "recommendation": "Consider process optimization or resource allocation"
                })
        
        # Check for stuck phases
        if bottlenecks["stuck_phases"]:
            total_stuck = sum(p["count"] for p in bottlenecks["stuck_phases"])
            insights.append({
                "type": "error",
                "category": "stuck_workflows",
                "message": f"{total_stuck} workflows are stuck for over 48 hours",
                "recommendation": "Immediate attention required to unblock workflows",
                "details": bottlenecks["stuck_phases"]
            })
        
        # Success insight if everything looks good
        if not insights:
            insights.append({
                "type": "success",
                "category": "overall",
                "message": "Workflow performance is within expected parameters",
                "recommendation": "Continue monitoring for any changes"
            })
        
        return insights
    
    async def get_phase_comparison(
        self,
        phase_names: List[str],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Compare performance across different phases"""
        
        return await self.compare_phases(phase_names, start_date, end_date)