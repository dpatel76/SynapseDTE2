"""
Metrics API endpoints for dashboard analytics and reporting
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, case
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user, get_db
from app.models import User, Report, CycleReport, WorkflowPhase, TestCycle
from app.models import ReportAttribute, CycleReportSampleSelectionSamples, TestExecution, Observation
from app.models import PhaseMetrics, ExecutionMetrics
from app.schemas.user import User as UserSchema

router = APIRouter()


@router.get("/dashboard/{user_id}")
async def get_dashboard_metrics(
    user_id: int,
    cycle_id: Optional[int] = Query(None),
    time_period: str = Query("current_cycle", description="Time period for metrics"),
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get dashboard metrics for a user"""
    
    # Build base query for user's reports
    query = select(CycleReport).join(Report).join(TestCycle)
    
    # Filter by user role
    if current_user.role == "Tester":
        query = query.where(CycleReport.tester_id == user_id)
    elif current_user.role == "Report Owner":
        query = query.where(Report.report_owner_id == user_id)
    elif current_user.role == "Data Owner":
        # Data owners see reports where they have assignments
        pass  # TODO: Implement data owner filter
    
    # Filter by cycle if specified
    if cycle_id:
        query = query.where(CycleReport.cycle_id == cycle_id)
    elif time_period == "current_cycle":
        # Get only active cycles
        query = query.where(TestCycle.status == "Active")
    
    # Execute query
    result = await db.execute(query.options(selectinload(CycleReport.report)))
    cycle_reports = result.scalars().all()
    
    # Calculate aggregate metrics
    total_reports = len(cycle_reports)
    completed_reports = sum(1 for r in cycle_reports if r.status == "Completed")
    in_progress_reports = sum(1 for r in cycle_reports if r.status == "In Progress")
    
    # Calculate trend (mock data for now)
    reports_trend = 10.5  # Positive trend
    
    # Calculate average completion time
    completed_with_time = [r for r in cycle_reports if r.status == "Completed" and r.completed_at and r.created_at]
    avg_completion_time = 0
    if completed_with_time:
        total_days = sum((r.completed_at - r.created_at).days for r in completed_with_time)
        avg_completion_time = total_days / len(completed_with_time)
    
    # Calculate SLA compliance
    sla_compliant = sum(1 for r in cycle_reports if r.status == "Completed")  # Simplified
    sla_compliance_rate = (sla_compliant / total_reports * 100) if total_reports > 0 else 0
    
    # Count observations
    obs_query = select(func.count(Observation.id)).join(TestExecution).join(CycleReport)
    if cycle_id:
        obs_query = obs_query.where(CycleReport.cycle_id == cycle_id)
    obs_result = await db.execute(obs_query)
    observations_count = obs_result.scalar() or 0
    
    return {
        "aggregate_metrics": {
            "reports_assigned": total_reports,
            "reports_completed": completed_reports,
            "reports_in_progress": in_progress_reports,
            "reports_trend": reports_trend,
            "avg_completion_time": avg_completion_time,
            "completion_rate": (completed_reports / total_reports * 100) if total_reports > 0 else 0,
            "sla_compliance_rate": sla_compliance_rate,
            "observations_confirmed": observations_count
        },
        "time_period": time_period,
        "cycle_id": cycle_id
    }


@router.get("/tester/{user_id}")
async def get_tester_metrics(
    user_id: int,
    cycle_id: Optional[int] = Query(None),
    report_id: Optional[int] = Query(None),
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get detailed metrics for a tester"""
    
    # Get tester's reports
    query = select(CycleReport).join(Report).join(TestCycle).where(
        CycleReport.tester_id == user_id
    )
    
    if cycle_id:
        query = query.where(CycleReport.cycle_id == cycle_id)
    else:
        # Get all active cycles
        query = query.where(TestCycle.status == "Active")
    
    if report_id:
        query = query.where(CycleReport.report_id == report_id)
    
    result = await db.execute(
        query.options(
            selectinload(CycleReport.report).selectinload(Report.lob),
            selectinload(CycleReport.cycle),
            selectinload(CycleReport.workflow_phases)
        )
    )
    cycle_reports = result.scalars().all()
    
    # Aggregate metrics
    total_reports = len(cycle_reports)
    completed_reports = sum(1 for r in cycle_reports if r.status == "Completed")
    in_progress_reports = sum(1 for r in cycle_reports if r.status == "In Progress")
    
    # Phase performance
    phase_performance = []
    phase_names = ["Planning", "Scoping", "Testing", "Observation Management"]
    for phase_name in phase_names:
        phase_total = 0
        phase_completed = 0
        for report in cycle_reports:
            phases = [p for p in report.workflow_phases if p.phase_name == phase_name]
            phase_total += len(phases)
            phase_completed += sum(1 for p in phases if p.status == "completed")
        
        if phase_total > 0:
            phase_performance.append({
                "phase_name": phase_name,
                "total": phase_total,
                "completed": phase_completed,
                "completion_rate": (phase_completed / phase_total * 100)
            })
    
    # LOB distribution
    lob_distribution = {}
    for report in cycle_reports:
        lob_name = report.report.lob.lob_name if report.report.lob else "Unknown"
        if lob_name not in lob_distribution:
            lob_distribution[lob_name] = {
                "lob_name": lob_name,
                "report_count": 0,
                "attribute_count": 0
            }
        lob_distribution[lob_name]["report_count"] += 1
    
    # Get attribute counts per LOB
    for lob_name in lob_distribution:
        attr_query = select(func.count(ReportAttribute.id)).join(Report).join(Report.lob).where(
            Report.lob.lob_name == lob_name
        )
        if cycle_id:
            attr_query = attr_query.join(CycleReport).where(CycleReport.cycle_id == cycle_id)
        attr_result = await db.execute(attr_query)
        lob_distribution[lob_name]["attribute_count"] = attr_result.scalar() or 0
    
    # Report summaries by LOB
    report_summaries = []
    for lob_name, lob_data in lob_distribution.items():
        # Get sample counts
        sample_query = select(func.count(CycleReportSampleSelectionSamples.id)).join(CycleReport).join(Report).join(Report.lob).where(
            Report.lob.lob_name == lob_name
        )
        if cycle_id:
            sample_query = sample_query.where(CycleReport.cycle_id == cycle_id)
        sample_result = await db.execute(sample_query)
        
        # Get test case counts
        test_query = select(func.count(TestExecution.id)).join(CycleReport).join(Report).join(Report.lob).where(
            Report.lob.lob_name == lob_name
        )
        if cycle_id:
            test_query = test_query.where(CycleReport.cycle_id == cycle_id)
        test_result = await db.execute(test_query)
        
        report_summaries.append({
            "lob_name": lob_name,
            "total_samples": sample_result.scalar() or 0,
            "total_attributes": lob_data["attribute_count"],
            "total_test_cases": test_result.scalar() or 0,
            "avg_progress": 75  # Mock progress for now
        })
    
    return {
        "data": {
            "aggregate_metrics": {
                "reports_assigned": total_reports,
                "reports_completed": completed_reports,
                "reports_in_progress": in_progress_reports,
                "reports_trend": 10.5,  # Mock
                "avg_completion_time": 14.5,  # Mock
                "completion_rate": (completed_reports / total_reports * 100) if total_reports > 0 else 0,
                "sla_compliance_rate": 95.5,  # Mock
                "observations_confirmed": 12  # Mock
            },
            "phase_performance": phase_performance,
            "lob_distribution": list(lob_distribution.values()),
            "report_summaries": report_summaries
        }
    }


@router.get("/report-owner/{user_id}")
async def get_report_owner_metrics(
    user_id: int,
    cycle_id: Optional[int] = Query(None),
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get metrics for report owner"""
    # TODO: Implement report owner specific metrics
    return {
        "pending_approvals": 5,
        "approved_items": 23,
        "rejected_items": 2,
        "average_review_time": 2.5
    }


@router.get("/data-provider/{user_id}")
async def get_data_provider_metrics(
    user_id: int,
    cycle_id: Optional[int] = Query(None),
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get metrics for data provider"""
    # TODO: Implement data provider specific metrics
    return {
        "assigned_attributes": 45,
        "data_provided": 38,
        "pending_requests": 7,
        "sla_compliance": 92.5
    }


@router.get("/phase/{phase_name}")
async def get_phase_metrics(
    phase_name: str,
    cycle_id: int,
    report_id: Optional[int] = Query(None),
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get metrics for a specific phase"""
    
    # Query phase metrics from the metrics table
    query = select(PhaseMetrics).where(
        and_(
            PhaseMetrics.cycle_id == cycle_id,
            PhaseMetrics.phase_name == phase_name
        )
    )
    
    if report_id:
        query = query.where(PhaseMetrics.report_id == report_id)
    
    result = await db.execute(query)
    metrics = result.scalars().all()
    
    # Aggregate metrics
    total_attributes = sum(m.total_attributes for m in metrics)
    approved_attributes = sum(m.approved_attributes for m in metrics)
    total_samples = sum(m.total_samples for m in metrics)
    approved_samples = sum(m.approved_samples for m in metrics)
    
    return {
        "phase_name": phase_name,
        "cycle_id": cycle_id,
        "metrics": {
            "total_attributes": total_attributes,
            "approved_attributes": approved_attributes,
            "attributes_with_issues": sum(m.attributes_with_issues for m in metrics),
            "total_samples": total_samples,
            "approved_samples": approved_samples,
            "failed_samples": sum(m.failed_samples for m in metrics),
            "completion_rate": (approved_attributes / total_attributes * 100) if total_attributes > 0 else 0,
            "on_time_delivery": sum(1 for m in metrics if m.on_time_completion) / len(metrics) * 100 if metrics else 0
        }
    }


@router.get("/activity/{user_id}")
async def get_user_activity_metrics(
    user_id: int,
    days: int = Query(7, description="Number of days to look back"),
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get user activity metrics"""
    # TODO: Implement activity tracking
    return {
        "daily_activity": [
            {"date": "2024-01-15", "actions": 12},
            {"date": "2024-01-16", "actions": 8},
            {"date": "2024-01-17", "actions": 15},
        ],
        "most_active_phase": "Testing",
        "average_daily_actions": 11.7
    }