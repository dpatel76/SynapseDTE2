"""Workflow Metrics API endpoints"""

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional, List
from datetime import datetime, timedelta, timezone

from app.api.v1.deps import get_current_user, get_db
from app.models.user import User
from app.services.workflow_metrics_service import (
    WorkflowMetricsService, MetricPeriod
)
from app.core.dependencies import require_roles

router = APIRouter()


@router.get("/metrics")
async def get_workflow_metrics(
    cycle_id: Optional[int] = Query(None, description="Filter by cycle ID"),
    report_id: Optional[int] = Query(None, description="Filter by report ID"),
    start_date: Optional[datetime] = Query(None, description="Start date for metrics"),
    end_date: Optional[datetime] = Query(None, description="End date for metrics"),
    period: MetricPeriod = Query(MetricPeriod.DAILY, description="Aggregation period"),
    current_user: User = Depends(require_roles(["Test Executive", "Report Executive"])),
    db = Depends(get_db)
):
    """Get comprehensive workflow metrics and insights"""
    
    # Default to last 30 days if no date range specified
    if not start_date:
        start_date = datetime.now(timezone.utc) - timedelta(days=30)
    if not end_date:
        end_date = datetime.now(timezone.utc)
    
    service = WorkflowMetricsService(db)
    metrics = await service.get_workflow_metrics(
        cycle_id=cycle_id,
        report_id=report_id,
        start_date=start_date,
        end_date=end_date,
        period=period
    )
    
    return metrics


@router.get("/phase-comparison")
async def compare_phases(
    phases: List[str] = Query(..., description="Phase names to compare"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    current_user: User = Depends(require_roles(["Test Executive", "Report Executive"])),
    db = Depends(get_db)
):
    """Compare performance metrics across workflow phases"""
    
    service = WorkflowMetricsService(db)
    comparison = await service.get_phase_comparison(
        phase_names=phases,
        start_date=start_date,
        end_date=end_date
    )
    
    return comparison


@router.get("/active-workflows")
async def get_active_workflows(
    current_user: User = Depends(require_roles(["Tester", "Test Executive", "Report Owner Executive"])),
    db = Depends(get_db)
):
    """Get list of currently active workflows"""
    
    service = WorkflowMetricsService(db)
    active = await service.get_active_workflows()
    
    return {
        "count": len(active),
        "workflows": active
    }


@router.get("/alerts")
async def get_workflow_alerts(
    limit: int = Query(10, ge=1, le=100, description="Number of alerts to return"),
    current_user: User = Depends(require_roles(["Test Executive", "Report Executive"])),
    db = Depends(get_db)
):
    """Get recent workflow performance alerts"""
    
    service = WorkflowMetricsService(db)
    alerts = await service.get_recent_alerts(limit=limit)
    
    return {
        "count": len(alerts),
        "alerts": alerts
    }


@router.get("/phase/{phase_name}/details")
async def get_phase_details(
    phase_name: str,
    cycle_id: Optional[int] = Query(None),
    report_id: Optional[int] = Query(None),
    current_user: User = Depends(require_roles(["Test Executive", "Report Executive"])),
    db = Depends(get_db)
):
    """Get detailed metrics for a specific phase"""
    
    from app.temporal.shared import WORKFLOW_PHASES
    
    if phase_name not in WORKFLOW_PHASES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid phase name. Must be one of: {', '.join(WORKFLOW_PHASES)}"
        )
    
    service = WorkflowMetricsService(db)
    
    # Get metrics for just this phase
    metrics = await service.get_workflow_metrics(
        cycle_id=cycle_id,
        report_id=report_id,
        period=MetricPeriod.DAILY
    )
    
    # Find the phase in metrics
    phase_metric = None
    for pm in metrics.get("phase_metrics", []):
        if pm["phase_name"] == phase_name:
            phase_metric = pm
            break
    
    if not phase_metric:
        return {
            "phase_name": phase_name,
            "message": "No data available for this phase"
        }
    
    return {
        "phase_name": phase_name,
        "metrics": phase_metric,
        "time_distribution": next(
            (td for td in metrics["bottlenecks"]["time_distribution"] 
             if td["phase"] == phase_name),
            None
        )
    }


@router.get("/cycle/{cycle_id}/summary")
async def get_cycle_workflow_summary(
    cycle_id: int,
    current_user: User = Depends(require_roles(["Tester", "Test Executive", "Report Owner Executive"])),
    db = Depends(get_db)
):
    """Get workflow summary for a specific test cycle"""
    
    service = WorkflowMetricsService(db)
    
    # Get metrics for this cycle
    metrics = await service.get_workflow_metrics(
        cycle_id=cycle_id,
        period=MetricPeriod.DAILY
    )
    
    # Get phase-level summary
    phase_summary = []
    for phase in ["Planning", "Scoping", "CycleReportSampleSelectionSamples Selection", "Data Owner Identification",
                  "Request for Information", "Test Execution", "Observation Management",
                  "Finalize Test Report"]:
        phase_data = next(
            (pm for pm in metrics.get("phase_metrics", []) if pm["phase_name"] == phase),
            None
        )
        if phase_data:
            phase_summary.append({
                "phase": phase,
                "status": "Completed" if phase_data["success_count"] > 0 else "Pending",
                "avg_duration_hours": round(phase_data["avg_duration_seconds"] / 3600, 1)
            })
        else:
            phase_summary.append({
                "phase": phase,
                "status": "Not Started",
                "avg_duration_hours": 0
            })
    
    return {
        "cycle_id": cycle_id,
        "summary": metrics["summary"],
        "phase_progress": phase_summary,
        "insights": metrics["insights"]
    }