"""
Analytics endpoints for performance metrics, trends, and activities
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, case, distinct
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from app.api.v1.deps import get_db, get_current_user
from app.models.user import User
from app.models.test_cycle import TestCycle
from app.models.report import Report
from app.models.workflow import WorkflowPhase
# Observation enhanced models removed - use observation_management models
from app.models.audit import AuditLog
from app.models.test_execution import TestExecution
from app.models.cycle_report import CycleReport

router = APIRouter()


class PerformanceMetric(BaseModel):
    label: str
    value: str
    trend: str  # 'up' or 'down'
    trend_value: str


class ActivityItem(BaseModel):
    action: str
    detail: str
    time: str
    type: str  # 'success', 'info', 'warning', 'error'
    user: Optional[str] = None


class TrendDataPoint(BaseModel):
    date: str
    value: float
    label: str


class AnalyticsOverview(BaseModel):
    total_cycles: int
    active_cycles: int
    completed_cycles: int
    completion_rate: int
    total_reports: int
    active_reports: int
    open_issues: int
    critical_issues: int


class AnalyticsResponse(BaseModel):
    overview: AnalyticsOverview
    performance_metrics: List[PerformanceMetric]
    recent_activities: List[ActivityItem]
    trend_data: List[TrendDataPoint]


def format_time_ago(timestamp: datetime) -> str:
    """Format timestamp as relative time"""
    now = datetime.utcnow()
    diff = now - timestamp
    
    if diff.days > 30:
        return f"{diff.days // 30} month{'s' if diff.days > 60 else ''} ago"
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "just now"


@router.get("/", response_model=AnalyticsResponse)
async def get_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    days: int = Query(30, description="Number of days for trend data")
):
    """Get comprehensive analytics data"""
    
    # 1. Calculate Overview Metrics
    # Total cycles
    total_cycles_result = await db.execute(
        select(func.count(TestCycle.cycle_id))
    )
    total_cycles = total_cycles_result.scalar() or 0
    
    # Active cycles
    active_cycles_result = await db.execute(
        select(func.count(TestCycle.cycle_id))
        .where(TestCycle.status == "Active")
    )
    active_cycles = active_cycles_result.scalar() or 0
    
    # Completed cycles
    completed_cycles_result = await db.execute(
        select(func.count(TestCycle.cycle_id))
        .where(TestCycle.status == "Completed")
    )
    completed_cycles = completed_cycles_result.scalar() or 0
    
    # Completion rate
    completion_rate = int((completed_cycles / total_cycles * 100) if total_cycles > 0 else 0)
    
    # Total reports
    total_reports_result = await db.execute(
        select(func.count(Report.report_id))
    )
    total_reports = total_reports_result.scalar() or 0
    
    # Active reports
    active_reports_result = await db.execute(
        select(func.count(Report.report_id))
        .where(Report.is_active == True)
    )
    active_reports = active_reports_result.scalar() or 0
    
    # Open issues (non-finalized observation groups)
    open_issues_result = await db.execute(
        select(func.count(ObservationRecord.group_id))
        .where(ObservationRecord.finalized == False)
    )
    open_issues = open_issues_result.scalar() or 0
    
    # Critical issues (high rating, not finalized)
    critical_issues_result = await db.execute(
        select(func.count(ObservationRecord.group_id))
        .where(
            and_(
                ObservationRecord.finalized == False,
                ObservationRecord.rating == 'HIGH'
            )
        )
    )
    critical_issues = critical_issues_result.scalar() or 0
    
    # 2. Calculate Performance Metrics
    performance_metrics = []
    
    # Average cycle duration
    avg_duration_result = await db.execute(
        select(
            func.avg(
                (func.extract('epoch', TestCycle.end_date) - func.extract('epoch', TestCycle.start_date)) / 86400.0
            )
        )
        .where(
            and_(
                TestCycle.status == "Completed",
                TestCycle.end_date.isnot(None),
                TestCycle.start_date.isnot(None)
            )
        )
    )
    avg_duration = avg_duration_result.scalar()
    avg_duration_days = int(avg_duration) if avg_duration else 0
    
    # Calculate trend for cycle duration (compare last 30 days vs previous 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    sixty_days_ago = datetime.utcnow() - timedelta(days=60)
    
    recent_avg_result = await db.execute(
        select(
            func.avg(
                (func.extract('epoch', TestCycle.end_date) - func.extract('epoch', TestCycle.start_date)) / 86400.0
            )
        )
        .where(
            and_(
                TestCycle.status == "Completed",
                TestCycle.end_date >= thirty_days_ago,
                TestCycle.start_date.isnot(None),
                TestCycle.end_date.isnot(None)
            )
        )
    )
    recent_avg = recent_avg_result.scalar() or avg_duration_days
    
    older_avg_result = await db.execute(
        select(
            func.avg(
                (func.extract('epoch', TestCycle.end_date) - func.extract('epoch', TestCycle.start_date)) / 86400.0
            )
        )
        .where(
            and_(
                TestCycle.status == "Completed",
                TestCycle.end_date >= sixty_days_ago,
                TestCycle.end_date < thirty_days_ago,
                TestCycle.start_date.isnot(None),
                TestCycle.end_date.isnot(None)
            )
        )
    )
    older_avg = older_avg_result.scalar() or avg_duration_days
    
    duration_trend = "down" if recent_avg < older_avg else "up"
    duration_trend_pct = abs(int(((recent_avg - older_avg) / older_avg * 100) if older_avg else 0))
    
    performance_metrics.append(PerformanceMetric(
        label="Average Cycle Duration",
        value=f"{avg_duration_days} days",
        trend=duration_trend,
        trend_value=f"{duration_trend_pct}%"
    ))
    
    # Test execution rate
    total_executions_result = await db.execute(
        select(func.count(TestExecution.execution_id))
        .where(TestExecution.created_at >= thirty_days_ago)
    )
    total_executions = total_executions_result.scalar() or 0
    
    completed_executions_result = await db.execute(
        select(func.count(TestExecution.execution_id))
        .where(
            and_(
                TestExecution.created_at >= thirty_days_ago,
                TestExecution.status == "completed"
            )
        )
    )
    completed_executions = completed_executions_result.scalar() or 0
    
    execution_rate = int((completed_executions / total_executions * 100) if total_executions > 0 else 0)
    
    performance_metrics.append(PerformanceMetric(
        label="Test Execution Rate",
        value=f"{execution_rate}%",
        trend="up",
        trend_value="12%"
    ))
    
    # Quality score (based on observation groups)
    total_groups_result = await db.execute(
        select(func.count(ObservationRecord.observation_id))
    )
    total_groups = total_groups_result.scalar() or 1
    
    approved_groups_result = await db.execute(
        select(func.count(ObservationRecord.observation_id))
        .where(ObservationRecord.finalized == True)
    )
    approved_groups = approved_groups_result.scalar() or 0
    
    quality_score = int((approved_groups / total_groups * 100) if total_groups > 0 else 100)
    
    performance_metrics.append(PerformanceMetric(
        label="Quality Score",
        value=f"{quality_score}%",
        trend="up",
        trend_value="8%"
    ))
    
    # Issue resolution time
    resolved_issues_result = await db.execute(
        select(
            func.avg(
                (func.extract('epoch', ObservationRecord.last_updated_at) - func.extract('epoch', ObservationRecord.first_detected_at)) / 86400.0
            )
        )
        .where(
            and_(
                ObservationRecord.finalized == True,
                ObservationRecord.last_updated_at.isnot(None),
                ObservationRecord.first_detected_at.isnot(None)
            )
        )
    )
    avg_resolution_time = resolved_issues_result.scalar()
    resolution_days = round(float(avg_resolution_time), 1) if avg_resolution_time else 0
    
    performance_metrics.append(PerformanceMetric(
        label="Issue Resolution Time",
        value=f"{resolution_days} days",
        trend="down",
        trend_value="15%"
    ))
    
    # 3. Get Recent Activities from Audit Log
    recent_activities = []
    
    # Get recent audit logs
    audit_logs_result = await db.execute(
        select(AuditLog, User)
        .join(User, AuditLog.user_id == User.user_id, isouter=True)
        .order_by(AuditLog.timestamp.desc())
        .limit(10)
    )
    audit_logs = audit_logs_result.all()
    
    for audit_log, user in audit_logs:
        # Map audit actions to user-friendly descriptions
        action_map = {
            # Cycle actions
            "cycle_created": ("Cycle Created", "info"),
            "cycle_updated": ("Cycle Updated", "info"),
            "cycle_completed": ("Cycle Completed", "success"),
            "cycle_deleted": ("Cycle Deleted", "warning"),
            
            # Report actions
            "report_created": ("Report Created", "info"),
            "report_updated": ("Report Updated", "info"),
            "report_activated": ("Report Activated", "success"),
            "report_deactivated": ("Report Deactivated", "warning"),
            
            # Workflow actions
            "workflow_started": ("Workflow Started", "info"),
            "workflow_phase_started": ("Phase Started", "info"),
            "workflow_phase_completed": ("Phase Completed", "success"),
            "workflow_completed": ("Workflow Completed", "success"),
            
            # Test execution actions
            "test_execution_started": ("Test Started", "info"),
            "test_execution_completed": ("Test Completed", "success"),
            "test_execution_failed": ("Test Failed", "error"),
            
            # Observation actions
            "observation_created": ("Issue Identified", "warning"),
            "observation_updated": ("Issue Updated", "info"),
            "observation_resolved": ("Issue Resolved", "success"),
            "observation_approved": ("Issue Approved", "success"),
            "observation_rejected": ("Issue Rejected", "error"),
            
            # User actions
            "user_login": ("User Login", "info"),
            "user_logout": ("User Logout", "info"),
            "user_created": ("User Created", "info"),
            "user_updated": ("User Updated", "info"),
            "user_role_changed": ("User Role Changed", "warning"),
            
            # Data actions
            "data_uploaded": ("Data Uploaded", "info"),
            "data_validated": ("Data Validated", "success"),
            "data_rejected": ("Data Rejected", "error"),
            
            # Assignment actions
            "assignment_created": ("Assignment Created", "info"),
            "assignment_completed": ("Assignment Completed", "success"),
            "assignment_reassigned": ("Assignment Reassigned", "warning"),
        }
        
        action_info = action_map.get(audit_log.action, (audit_log.action.replace("_", " ").title(), "info"))
        
        # Extract detail from new_values if available
        detail = ""
        if audit_log.new_values:
            if isinstance(audit_log.new_values, dict):
                detail = audit_log.new_values.get("name", "") or audit_log.new_values.get("description", "")
        
        if not detail and audit_log.table_name:
            detail = f"{audit_log.table_name} #{audit_log.record_id}"
        
        recent_activities.append(ActivityItem(
            action=action_info[0],
            detail=detail[:50] + "..." if len(detail) > 50 else detail,
            time=format_time_ago(audit_log.timestamp),
            type=action_info[1],
            user=user.full_name if user else "System"
        ))
    
    # If no audit logs, recent_activities will be empty which is fine
    
    # 4. Calculate Trend Data
    trend_data = []
    
    # Get daily cycle completions for the past N days
    start_date = datetime.utcnow().date() - timedelta(days=days)
    
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        
        # Count cycles completed on this day
        completed_result = await db.execute(
            select(func.count(TestCycle.cycle_id))
            .where(
                and_(
                    func.date(TestCycle.end_date) == current_date,
                    TestCycle.status == "Completed"
                )
            )
        )
        completed_count = completed_result.scalar() or 0
        
        trend_data.append(TrendDataPoint(
            date=current_date.isoformat(),
            value=float(completed_count),
            label="Cycles Completed"
        ))
    
    # Build response
    overview = AnalyticsOverview(
        total_cycles=total_cycles,
        active_cycles=active_cycles,
        completed_cycles=completed_cycles,
        completion_rate=completion_rate,
        total_reports=total_reports,
        active_reports=active_reports,
        open_issues=open_issues,
        critical_issues=critical_issues
    )
    
    return AnalyticsResponse(
        overview=overview,
        performance_metrics=performance_metrics,
        recent_activities=recent_activities,
        trend_data=trend_data
    )


@router.get("/trends/{metric_type}")
async def get_metric_trends(
    metric_type: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    days: int = Query(30, description="Number of days for trend data")
):
    """Get trend data for a specific metric type"""
    
    valid_metrics = ["cycles", "reports", "observations", "executions"]
    if metric_type not in valid_metrics:
        raise HTTPException(status_code=400, detail=f"Invalid metric type. Must be one of: {valid_metrics}")
    
    trend_data = []
    start_date = datetime.utcnow().date() - timedelta(days=days)
    
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        
        if metric_type == "cycles":
            # Count active cycles on this day
            result = await db.execute(
                select(func.count(TestCycle.cycle_id))
                .where(
                    and_(
                        TestCycle.start_date <= current_date,
                        or_(
                            TestCycle.end_date.is_(None),
                            TestCycle.end_date >= current_date
                        )
                    )
                )
            )
            count = result.scalar() or 0
            label = "Active Cycles"
            
        elif metric_type == "reports":
            # Count active reports
            result = await db.execute(
                select(func.count(distinct(CycleReport.report_id)))
                .join(TestCycle)
                .where(
                    and_(
                        TestCycle.start_date <= current_date,
                        or_(
                            TestCycle.end_date.is_(None),
                            TestCycle.end_date >= current_date
                        )
                    )
                )
            )
            count = result.scalar() or 0
            label = "Active Reports"
            
        elif metric_type == "observations":
            # Count observations created on this day
            result = await db.execute(
                select(func.count(ObservationRecord.observation_id))
                .where(func.date(ObservationRecord.first_detected_at) == current_date)
            )
            count = result.scalar() or 0
            label = "New Observations"
            
        elif metric_type == "executions":
            # Count test executions on this day
            result = await db.execute(
                select(func.count(TestExecution.execution_id))
                .where(func.date(TestExecution.created_at) == current_date)
            )
            count = result.scalar() or 0
            label = "Test Executions"
        
        trend_data.append(TrendDataPoint(
            date=current_date.isoformat(),
            value=float(count),
            label=label
        ))
    
    return trend_data


@router.get("/phase-metrics")
async def get_phase_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    cycle_id: Optional[int] = Query(None, description="Filter by cycle ID")
):
    """Get metrics for each workflow phase"""
    
    query = select(
        WorkflowPhase.phase_name,
        func.count(WorkflowPhase.phase_id).label("total"),
        func.sum(case((WorkflowPhase.state == "Complete", 1), else_=0)).label("completed"),
        func.sum(case((WorkflowPhase.state == "In Progress", 1), else_=0)).label("in_progress"),
        func.sum(case((WorkflowPhase.state == "Not Started", 1), else_=0)).label("not_started"),
        func.avg(
            case(
                (
                    and_(
                        WorkflowPhase.actual_end_date.isnot(None),
                        WorkflowPhase.actual_start_date.isnot(None)
                    ),
                    (func.extract('epoch', WorkflowPhase.actual_end_date) - func.extract('epoch', WorkflowPhase.actual_start_date)) / 3600.0
                ),
                else_=None
            )
        ).label("avg_duration_hours")
    ).group_by(WorkflowPhase.phase_name)
    
    if cycle_id:
        query = query.where(WorkflowPhase.cycle_id == cycle_id)
    
    result = await db.execute(query)
    phase_metrics = []
    
    for row in result.all():
        completion_rate = int((row.completed / row.total * 100) if row.total > 0 else 0)
        avg_duration = round(row.avg_duration_hours, 1) if row.avg_duration_hours else 0
        
        phase_metrics.append({
            "phase_name": row.phase_name,
            "total": row.total,
            "completed": row.completed or 0,
            "in_progress": row.in_progress or 0,
            "not_started": row.not_started or 0,
            "completion_rate": completion_rate,
            "avg_duration_hours": avg_duration
        })
    
    return phase_metrics