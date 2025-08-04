"""
CDO Dashboard Service  
Provides LOB-wide analytics and team performance metrics for Chief Data Officers
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, text, select, and_, case
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.models.test_cycle import TestCycle
from app.models.report import Report
from app.models.workflow import WorkflowPhase
# AttributeLOBAssignment removed - table doesn't exist
from app.models.testing import DataOwnerAssignment
from app.models.lob import LOB
from app.models.report_attribute import ReportAttribute
from app.models.request_info import CycleReportTestCase

logger = logging.getLogger(__name__)


@dataclass
class LOBMetrics:
    """LOB-level metrics for CDO dashboard"""
    lob_name: str
    total_data_owners: int
    active_assignments: int
    completion_rate: float
    average_response_time_hours: float
    data_quality_score: float
    sla_compliance_rate: float


@dataclass
class TeamPerformanceMetric:
    """Team performance metric for CDO dashboard"""
    metric_name: str
    current_value: float
    target_value: float
    trend: str
    performance_category: str
    unit: str


@dataclass
class CDOWorkflowStatus:
    """CDO workflow status for a specific cycle/report"""
    cycle_id: int
    cycle_name: str
    report_id: int
    report_name: str
    current_phase: str
    overall_progress: int
    cdo_assignments_count: int
    pending_assignments: int
    completed_assignments: int
    workflow_status: str


class CDODashboardService:
    """Service for CDO dashboard analytics"""
    
    def __init__(self):
        logger.info("CDO dashboard service initialized")
    
    async def get_cdo_dashboard_metrics(
        self,
        cdo_user_id: int,
        db: AsyncSession,
        time_filter: str = "last_30_days"
    ) -> Dict[str, Any]:
        """Get comprehensive CDO dashboard metrics"""
        try:
            # Get CDO user details with LOB
            cdo_user = await db.execute(
                select(User)
                .options(selectinload(User.lob))
                .where(User.user_id == cdo_user_id)
            )
            cdo_user = cdo_user.scalar_one_or_none()
            
            if not cdo_user or not cdo_user.is_cdo:
                raise ValueError("User is not a CDO")

            # Calculate time range
            if time_filter == "last_7_days":
                start_date = datetime.utcnow() - timedelta(days=7)
            elif time_filter == "last_90_days":
                start_date = datetime.utcnow() - timedelta(days=90)
            else:  # last_30_days default
                start_date = datetime.utcnow() - timedelta(days=30)
            
            # Get real data
            lob_overview = await self._get_real_lob_overview(cdo_user, start_date, db)
            assignment_analytics = await self._get_real_assignment_analytics(cdo_user, start_date, db)
            workflow_status = await self._get_cdo_workflow_status(cdo_user, db)
            
            # Get team performance metrics (still using calculated metrics)
            team_performance = await self._get_team_performance_metrics(cdo_user_id, start_date, db)
            
            # Get escalation management data
            escalation_data = await self._get_escalation_management(cdo_user_id, start_date, db)
            
            # Get strategic insights
            strategic_insights = await self._get_strategic_insights(cdo_user_id, db)
            
            return {
                "dashboard_type": "cdo",
                "user_id": cdo_user_id,
                "user_name": f"{cdo_user.first_name} {cdo_user.last_name}",
                "lob_name": await self._get_lob_name(cdo_user, db),
                "time_period": time_filter,
                "generated_at": datetime.utcnow().isoformat(),
                "lob_overview": lob_overview,
                "assignment_analytics": assignment_analytics,
                "workflow_status": workflow_status,
                "team_performance": [
                    {
                        "name": metric.metric_name,
                        "current_value": metric.current_value,
                        "target_value": metric.target_value,
                        "trend": metric.trend,
                        "performance_category": metric.performance_category,
                        "unit": metric.unit,
                        "achievement_percentage": round((metric.current_value / metric.target_value) * 100, 1) if metric.target_value > 0 else 0
                    }
                    for metric in team_performance
                ],
                "escalation_management": escalation_data,
                "strategic_insights": strategic_insights,
                "action_items": await self._get_action_items(cdo_user_id, lob_overview, team_performance)
            }
            
        except Exception as e:
            logger.error(f"Failed to get CDO dashboard metrics: {str(e)}")
            return {
                "error": f"Failed to generate dashboard: {str(e)}",
                "dashboard_type": "cdo",
                "user_id": cdo_user_id
            }

    async def _get_real_lob_overview(
        self,
        cdo_user: User,
        start_date: datetime,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Get real LOB overview metrics from database"""
        try:
            # Get data providers in CDO's LOB
            data_owners = await db.execute(
                select(User)
                .where(and_(
                    User.lob_id == cdo_user.lob_id,
                    User.role == 'Data Owner',
                    User.is_active == True
                ))
            )
            data_owners = data_owners.scalars().all()
            
            # Get data owner assignments made by this CDO
            assignments = await db.execute(
                select(DataOwnerAssignment)
                .where(and_(
                    DataOwnerAssignment.cdo_id == cdo_user.user_id,
                    DataOwnerAssignment.assigned_at >= start_date
                ))
            )
            assignments = assignments.scalars().all()
            
            # Calculate metrics
            total_assignments = len(assignments)
            completed_assignments = len([a for a in assignments if a.status == 'Completed'])
            completion_rate = (completed_assignments / total_assignments * 100) if total_assignments > 0 else 0
            
            # Calculate average response time (mock for now)
            avg_response_time = 18.5
            
            return {
                "summary": {
                    "lob_name": await self._get_lob_name(cdo_user, db),
                    "total_data_owners": len(data_owners),
                    "total_assignments": total_assignments,
                    "completed_assignments": completed_assignments,
                    "completion_rate": round(completion_rate, 1),
                    "average_response_time": avg_response_time,
                    "data_quality_score": 89.2,  # Mock for now
                    "sla_compliance_rate": 91.5   # Mock for now
                },
                "data_owners": [
                    {
                        "provider_id": dp.user_id,
                        "provider_name": f"{dp.first_name} {dp.last_name}",
                        "email": dp.email,
                        "assignments_count": len([a for a in assignments if a.data_owner_id == dp.user_id]),
                        "completion_rate": 85.0,  # Mock for now
                        "avg_response_time": 16.2  # Mock for now
                    }
                    for dp in data_owners
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get real LOB overview: {str(e)}")
            return {}

    async def _get_real_assignment_analytics(
        self,
        cdo_user: User,
        start_date: datetime,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Get real assignment analytics from database"""
        try:
            logger.info(f"[CDO Service] Getting assignment analytics for CDO {cdo_user.user_id}")
            
            # Debug: First check if there are any assignments at all
            test_result = await db.execute(
                text("SELECT COUNT(*) FROM data_owner_assignments WHERE cdo_id = :cdo_id"),
                {"cdo_id": cdo_user.user_id}
            )
            count = test_result.scalar()
            logger.info(f"[CDO Service] Raw SQL count for cdo_id={cdo_user.user_id}: {count}")
            
            # Get all assignments made by this CDO
            assignments = await db.execute(
                select(DataOwnerAssignment, ReportAttribute, Report, TestCycle, User)
                .join(ReportAttribute, DataOwnerAssignment.attribute_id == ReportAttribute.attribute_id)
                .join(Report, DataOwnerAssignment.report_id == Report.report_id)
                .join(TestCycle, DataOwnerAssignment.cycle_id == TestCycle.cycle_id)
                .outerjoin(User, DataOwnerAssignment.data_owner_id == User.user_id)
                .where(DataOwnerAssignment.cdo_id == cdo_user.user_id)
                .order_by(DataOwnerAssignment.assigned_at.desc())
            )
            assignments = assignments.all()
            
            logger.info(f"[CDO Service] Found {len(assignments)} assignments for CDO {cdo_user.user_id}")
            
            # Calculate analytics
            total_assignments = len(assignments)
            
            # Fix datetime comparison by ensuring both are timezone-aware or naive
            recent_assignments = 0
            for assignment, _, _, _, _ in assignments:
                if assignment.assigned_at:
                    # Make both datetimes timezone-naive for comparison
                    assigned_at = assignment.assigned_at.replace(tzinfo=None) if assignment.assigned_at.tzinfo else assignment.assigned_at
                    start_date_naive = start_date.replace(tzinfo=None) if start_date.tzinfo else start_date
                    if assigned_at >= start_date_naive:
                        recent_assignments += 1
            
            logger.info(f"[CDO Service] Recent assignments (since {start_date}): {recent_assignments}")
            
            # Group by status
            status_breakdown = {}
            for assignment, _, _, _, _ in assignments:
                status = assignment.status or 'Pending'
                status_breakdown[status] = status_breakdown.get(status, 0) + 1
            
            logger.info(f"[CDO Service] Status breakdown: {status_breakdown}")
            
            # Group by cycle
            cycle_breakdown = {}
            for assignment, _, _, cycle, _ in assignments:
                cycle_name = cycle.cycle_name
                cycle_breakdown[cycle_name] = cycle_breakdown.get(cycle_name, 0) + 1
            
            logger.info(f"[CDO Service] Cycle breakdown: {cycle_breakdown}")
            
            # Create recent activity list
            recent_activity = []
            for assignment, attribute, report, cycle, user in assignments[:10]:  # Last 10 assignments
                activity = {
                    "assignment_id": assignment.assignment_id,
                    "attribute_id": assignment.attribute_id,
                    "attribute_name": attribute.attribute_name,
                    "attribute_description": attribute.description,
                    "report_name": report.report_name,
                    "cycle_name": cycle.cycle_name,
                    "data_provider_name": f"{user.first_name} {user.last_name}" if user else "Not Assigned",
                    "data_provider_email": user.email if user else "",
                    "assigned_at": assignment.assigned_at.isoformat() if assignment.assigned_at else None,
                    "status": assignment.status
                }
                recent_activity.append(activity)
                logger.info(f"[CDO Service] Recent activity item: {activity}")
            
            result = {
                "total_assignments": total_assignments,
                "recent_assignments": recent_assignments,
                "status_breakdown": status_breakdown,
                "cycle_breakdown": cycle_breakdown,
                "recent_activity": recent_activity
            }
            
            logger.info(f"[CDO Service] Assignment analytics result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"[CDO Service] Failed to get real assignment analytics: {str(e)}")
            logger.error(f"[CDO Service] Exception details: {type(e).__name__}: {str(e)}")
            return {}

    async def _get_cdo_workflow_status(
        self,
        cdo_user: User,
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """Get CDO workflow status across all cycles with assignments"""
        try:
            logger.info(f"[CDO Service] Getting workflow status for CDO {cdo_user.user_id}")
            
            # Get all cycles and reports where CDO has assignments
            assignments_query = await db.execute(
                select(
                    TestCycle.cycle_id,
                    TestCycle.cycle_name,
                    TestCycle.status.label('cycle_status'),
                    TestCycle.end_date,
                    Report.report_id,
                    Report.report_name,
                    func.count(DataOwnerAssignment.assignment_id).label('total_assignments'),
                    func.sum(case((DataOwnerAssignment.status == 'Completed', 1), else_=0)).label('completed_assignments')
                )
                .join(DataOwnerAssignment, TestCycle.cycle_id == DataOwnerAssignment.cycle_id)
                .join(Report, DataOwnerAssignment.report_id == Report.report_id)
                .where(DataOwnerAssignment.cdo_id == cdo_user.user_id)
                .group_by(
                    TestCycle.cycle_id,
                    TestCycle.cycle_name,
                    TestCycle.status,
                    TestCycle.end_date,
                    Report.report_id,
                    Report.report_name
                )
            )
            
            assignments_data = assignments_query.fetchall()
            logger.info(f"[CDO Service] Found {len(assignments_data)} cycle/report combinations with assignments")
            
            workflow_statuses = []
            
            for row in assignments_data:
                total_assignments = row.total_assignments or 0
                completed_assignments = row.completed_assignments or 0
                
                logger.info(f"[CDO Service] Cycle {row.cycle_id} Report {row.report_id}: {completed_assignments}/{total_assignments} assignments completed")
                
                # Calculate progress
                progress_percentage = (completed_assignments / total_assignments * 100) if total_assignments > 0 else 0
                
                # Determine status
                if progress_percentage == 100:
                    status = "Completed"
                elif progress_percentage >= 75:
                    status = "On Track"
                elif progress_percentage >= 50:
                    status = "At Risk"
                else:
                    status = "Behind"
                
                # Get workflow phase for this cycle/report
                workflow_phase = await db.execute(
                    select(WorkflowPhase.phase_name, WorkflowPhase.status)
                    .where(and_(
                        WorkflowPhase.cycle_id == row.cycle_id,
                        WorkflowPhase.report_id == row.report_id,
                        WorkflowPhase.phase_name == 'Data Provider ID'
                    ))
                )
                phase_data = workflow_phase.first()
                
                current_phase = "Data Provider ID"
                phase_status = "Not Started"
                
                if phase_data:
                    current_phase = phase_data[0]
                    phase_status = phase_data[1]
                
                workflow_status = {
                    "cycle_id": row.cycle_id,
                    "cycle_name": row.cycle_name,
                    "report_id": row.report_id,
                    "report_name": row.report_name,
                    "current_phase": current_phase,
                    "phase_status": phase_status,
                    "overall_progress": round(progress_percentage, 1),
                    "total_assignments": total_assignments,
                    "completed_assignments": completed_assignments,
                    "pending_assignments": total_assignments - completed_assignments,
                    "workflow_status": status,
                    "cycle_status": row.cycle_status
                }
                
                workflow_statuses.append(workflow_status)
                logger.info(f"[CDO Service] Workflow status: {workflow_status}")
            
            logger.info(f"[CDO Service] Returning {len(workflow_statuses)} workflow statuses")
            return workflow_statuses
            
        except Exception as e:
            logger.error(f"[CDO Service] Error getting CDO workflow status: {str(e)}")
            logger.error(f"[CDO Service] Exception details: {type(e).__name__}: {str(e)}")
            return []

    async def _get_lob_overview(
        self,
        cdo_user_id: int,
        start_date: datetime,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Get LOB overview metrics (legacy method - kept for compatibility)"""
        try:
            # Get CDO user
            cdo_user = await db.execute(
                select(User).where(User.user_id == cdo_user_id)
            )
            cdo_user = cdo_user.scalar_one_or_none()
            
            if cdo_user:
                return await self._get_real_lob_overview(cdo_user, start_date, db)
            else:
                return {}
            
        except Exception as e:
            logger.error(f"Failed to get LOB overview: {str(e)}")
            return {}
    
    async def _get_team_performance_metrics(
        self,
        cdo_user_id: int,
        start_date: datetime,
        db: AsyncSession
    ) -> List[TeamPerformanceMetric]:
        """Get team performance metrics for CDO"""
        try:
            # Mock team performance metrics - in production, calculated from actual data
            return [
                TeamPerformanceMetric(
                    metric_name="Team Productivity Index",
                    current_value=87.4,
                    target_value=85.0,
                    trend="improving",
                    performance_category="excellent",
                    unit="score"
                ),
                TeamPerformanceMetric(
                    metric_name="Cross-LOB Collaboration Score",
                    current_value=73.2,
                    target_value=75.0,
                    trend="stable",
                    performance_category="needs_attention",
                    unit="score"
                ),
                TeamPerformanceMetric(
                    metric_name="Data Provider Satisfaction",
                    current_value=4.2,
                    target_value=4.0,
                    trend="improving",
                    performance_category="excellent",
                    unit="rating"
                ),
                TeamPerformanceMetric(
                    metric_name="Knowledge Transfer Rate",
                    current_value=68.9,
                    target_value=70.0,
                    trend="improving",
                    performance_category="good",
                    unit="%"
                ),
                TeamPerformanceMetric(
                    metric_name="Resource Utilization",
                    current_value=82.1,
                    target_value=80.0,
                    trend="stable",
                    performance_category="excellent",
                    unit="%"
                ),
                TeamPerformanceMetric(
                    metric_name="Training Completion Rate",
                    current_value=91.7,
                    target_value=90.0,
                    trend="improving",
                    performance_category="excellent",
                    unit="%"
                )
            ]
            
        except Exception as e:
            logger.error(f"Failed to get team performance metrics: {str(e)}")
            return []
    
    async def _get_assignment_analytics(
        self,
        cdo_user_id: int,
        start_date: datetime,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Get assignment analytics and patterns"""
        try:
            # Mock assignment analytics - in production, query actual assignment data
            return {
                "assignment_distribution": {
                    "by_complexity": {
                        "High": 18.5,
                        "Medium": 52.3,
                        "Low": 29.2
                    },
                    "by_type": {
                        "Source Documents": 42.1,
                        "Database Information": 35.7,
                        "Data Validation": 22.2
                    },
                    "by_urgency": {
                        "Critical": 8.3,
                        "High": 23.7,
                        "Medium": 45.2,
                        "Low": 22.8
                    }
                },
                "workload_trends": {
                    "weekly_assignments": [78, 82, 75, 89, 76, 84, 88],
                    "days": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                    "peak_day": "Thursday",
                    "trend": "stable"
                },
                "capacity_analysis": {
                    "current_utilization": 73.5,
                    "optimal_range": [70, 85],
                    "capacity_status": "optimal",
                    "projected_demand": {
                        "next_month": 86.2,
                        "recommendation": "Consider adding 1-2 additional resources"
                    }
                },
                "bottlenecks": [
                    {
                        "area": "Database Information requests",
                        "impact": "Medium",
                        "suggested_action": "Cross-train additional team members"
                    },
                    {
                        "area": "High complexity assignments",
                        "impact": "Low",
                        "suggested_action": "Implement peer review process"
                    }
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get assignment analytics: {str(e)}")
            return {}
    
    async def _get_escalation_management(
        self,
        cdo_user_id: int,
        start_date: datetime,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Get escalation management data"""
        try:
            # Mock escalation data - in production, query escalation tables
            return {
                "escalation_summary": {
                    "total_escalations": 7,
                    "resolved_escalations": 5,
                    "pending_escalations": 2,
                    "average_resolution_time_hours": 18.3,
                    "escalation_rate": 3.2  # percentage of total assignments
                },
                "escalation_types": {
                    "SLA Breach": 3,
                    "Data Quality Issues": 2,
                    "Resource Constraints": 1,
                    "Technical Problems": 1
                },
                "recent_escalations": [
                    {
                        "id": "ESC-2024-089",
                        "type": "SLA Breach",
                        "lob": "Insurance",
                        "created_date": "2024-12-15",
                        "status": "In Progress",
                        "priority": "High",
                        "estimated_resolution": "2024-12-18"
                    },
                    {
                        "id": "ESC-2024-087",
                        "type": "Resource Constraints", 
                        "lob": "Banking",
                        "created_date": "2024-12-12",
                        "status": "Resolved",
                        "priority": "Medium",
                        "resolution_date": "2024-12-16"
                    }
                ],
                "escalation_trends": {
                    "monthly_escalations": [5, 8, 6, 9, 7, 7],
                    "months": ["Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
                    "trend": "stable"
                },
                "prevention_measures": [
                    "Implement proactive SLA monitoring",
                    "Enhance resource capacity planning",
                    "Improve data quality validation processes"
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get escalation management data: {str(e)}")
            return {}
    
    async def _get_strategic_insights(
        self,
        cdo_user_id: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Get strategic insights for CDO decision making"""
        try:
            # Mock strategic insights - in production, analyze trends and patterns
            return {
                "key_insights": [
                    {
                        "insight": "Investment LOB consistently outperforms targets",
                        "impact": "High",
                        "action": "Apply Investment LOB practices to other divisions"
                    },
                    {
                        "insight": "Insurance LOB showing declining response times",
                        "impact": "Medium",
                        "action": "Investigate resource allocation and training needs"
                    },
                    {
                        "insight": "Cross-LOB collaboration opportunities identified",
                        "impact": "Medium",
                        "action": "Implement shared resource pool for peak demand"
                    }
                ],
                "performance_drivers": {
                    "positive_factors": [
                        "Strong training program completion rates",
                        "High data provider satisfaction scores",
                        "Effective escalation resolution process"
                    ],
                    "improvement_areas": [
                        "Cross-LOB collaboration framework",
                        "Resource capacity optimization",
                        "Proactive SLA monitoring"
                    ]
                },
                "competitive_analysis": {
                    "industry_benchmark": {
                        "completion_rate": 82.4,
                        "quality_score": 87.9,
                        "response_time": 20.1
                    },
                    "our_performance": {
                        "completion_rate": 86.6,
                        "quality_score": 91.0,
                        "response_time": 16.8
                    },
                    "ranking": "Top 25% in industry"
                },
                "future_outlook": {
                    "growth_projections": {
                        "assignment_volume": "+15% next quarter",
                        "team_expansion": "2-3 additional data providers needed",
                        "technology_needs": "Automation tools for routine tasks"
                    },
                    "strategic_recommendations": [
                        "Invest in automation to handle volume growth",
                        "Expand cross-training programs",
                        "Implement predictive analytics for capacity planning"
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get strategic insights: {str(e)}")
            return {}
    
    async def _get_action_items(
        self,
        cdo_user_id: int,
        lob_overview: Dict[str, Any],
        team_performance: List[TeamPerformanceMetric]
    ) -> List[Dict[str, Any]]:
        """Generate action items based on performance data"""
        try:
            action_items = []
            
            # Check for underperforming LOBs
            if "lob_breakdown" in lob_overview:
                for lob in lob_overview["lob_breakdown"]:
                    if lob["completion_rate"] < 85:
                        action_items.append({
                            "priority": "High",
                            "type": "Performance Issue",
                            "description": f"Address {lob['lob_name']} LOB completion rate ({lob['completion_rate']}%)",
                            "due_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
                            "assigned_to": "LOB Manager"
                        })
                    
                    if lob["avg_response_time"] > 18:
                        action_items.append({
                            "priority": "Medium",
                            "type": "Process Improvement",
                            "description": f"Optimize {lob['lob_name']} response time ({lob['avg_response_time']} hours)",
                            "due_date": (datetime.utcnow() + timedelta(days=14)).isoformat(),
                            "assigned_to": "Process Improvement Team"
                        })
            
            # Check team performance metrics for action items
            for metric in team_performance:
                if metric.performance_category == "needs_attention":
                    action_items.append({
                        "priority": "Medium",
                        "type": "Team Development",
                        "description": f"Improve {metric.metric_name} ({metric.current_value} vs target {metric.target_value})",
                        "due_date": (datetime.utcnow() + timedelta(days=21)).isoformat(),
                        "assigned_to": "Team Lead"
                    })
            
            # Add strategic action items
            action_items.extend([
                {
                    "priority": "Low",
                    "type": "Strategic Planning",
                    "description": "Review quarterly resource allocation and capacity planning",
                    "due_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
                    "assigned_to": "Data Executive"
                },
                {
                    "priority": "Medium", 
                    "type": "Team Development",
                    "description": "Conduct cross-LOB collaboration workshop",
                    "due_date": (datetime.utcnow() + timedelta(days=14)).isoformat(),
                    "assigned_to": "HR/Training"
                }
            ])
            
            # Sort by priority and return top 10
            priority_order = {"High": 1, "Medium": 2, "Low": 3}
            action_items.sort(key=lambda x: priority_order.get(x["priority"], 3))
            
            return action_items[:10]
            
        except Exception as e:
            logger.error(f"Failed to generate action items: {str(e)}")
            return []
    
    async def _get_lob_name(self, cdo_user: User, db: AsyncSession) -> str:
        """Get LOB name for CDO user"""
        try:
            if cdo_user.lob_id:
                lob = await db.execute(
                    select(LOB).where(LOB.lob_id == cdo_user.lob_id)
                )
                lob = lob.scalar_one_or_none()
                return lob.lob_name if lob else "Unknown"
            return "Unknown"
        except Exception:
            return "Unknown"

    def _get_lob_status(self, lob: LOBMetrics) -> str:
        """Determine overall status for a LOB"""
        if lob.completion_rate >= 90 and lob.sla_compliance_rate >= 95:
            return "excellent"
        elif lob.completion_rate >= 85 and lob.sla_compliance_rate >= 90:
            return "good"
        elif lob.completion_rate >= 75 and lob.sla_compliance_rate >= 85:
            return "needs_attention"
        else:
            return "critical"


# Global service instance
cdo_dashboard_service = CDODashboardService()


def get_cdo_dashboard_service() -> CDODashboardService:
    """Get the global CDO dashboard service instance"""
    return cdo_dashboard_service 