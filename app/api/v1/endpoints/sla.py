"""
SLA Management API Endpoints
Provides SLA tracking, monitoring, and escalation management
"""

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.security import role_required
from app.services.sla_service import get_sla_service, SLAService
from app.models.user import User
from app.api.v1.deps import get_current_user
from pydantic import BaseModel, Field

router = APIRouter()


# Pydantic models for SLA endpoints
class SLAConfigurationRequest(BaseModel):
    phase: str = Field(..., description="Workflow phase (planning, scoping, etc.)")
    sla_hours: int = Field(..., gt=0, description="SLA duration in hours")
    escalation_levels: List[Dict[str, Any]] = Field(..., description="Escalation configuration")

class SLATrackingStart(BaseModel):
    cycle_id: int = Field(..., description="Cycle ID")
    report_id: int = Field(..., description="Report ID")
    phase: str = Field(..., description="Workflow phase")

class SLATrackingComplete(BaseModel):
    cycle_id: int = Field(..., description="Cycle ID")
    report_id: int = Field(..., description="Report ID")
    phase: str = Field(..., description="Workflow phase")

class EscalationTrigger(BaseModel):
    cycle_id: int = Field(..., description="Cycle ID")
    phase: str = Field(..., description="Workflow phase")
    escalation_level: int = Field(..., ge=1, le=4, description="Escalation level (1-4)")
    reason: str = Field(..., description="Reason for manual escalation")


@router.post("/configure")
@role_required(["Admin", "Test Manager"])
async def configure_sla(
    config: SLAConfigurationRequest,
    current_user: User = Depends(get_current_user),
    sla_service: SLAService = Depends(get_sla_service)
) -> Dict[str, Any]:
    """Configure SLA settings for a workflow phase"""
    try:
        # In a real implementation, this would store SLA configuration in database
        configuration = {
            "phase": config.phase,
            "sla_hours": config.sla_hours,
            "escalation_levels": config.escalation_levels,
            "configured_by": current_user.user_id,
            "configured_at": datetime.utcnow().isoformat(),
            "status": "active"
        }
        
        return {
            "message": f"SLA configuration updated for {config.phase}",
            "configuration": configuration
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to configure SLA: {str(e)}")


@router.post("/start-tracking")
@role_required(["Tester", "Test Manager", "Report Owner"])
async def start_sla_tracking(
    tracking: SLATrackingStart,
    current_user: User = Depends(get_current_user),
    sla_service: SLAService = Depends(get_sla_service)
) -> Dict[str, Any]:
    """Start SLA tracking for a workflow phase"""
    try:
        result = await sla_service.start_tracking(
            tracking.cycle_id,
            tracking.report_id,
            tracking.phase,
            current_user.user_id
        )
        
        return {
            "message": f"SLA tracking started for {tracking.phase}",
            "tracking_record": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start SLA tracking: {str(e)}")


@router.post("/complete-tracking")
@role_required(["Tester", "Test Manager", "Report Owner"])
async def complete_sla_tracking(
    tracking: SLATrackingComplete,
    current_user: User = Depends(get_current_user),
    sla_service: SLAService = Depends(get_sla_service)
) -> Dict[str, Any]:
    """Complete SLA tracking for a workflow phase"""
    try:
        result = await sla_service.complete_tracking(
            tracking.cycle_id,
            tracking.report_id,
            tracking.phase,
            current_user.user_id
        )
        
        return {
            "message": f"SLA tracking completed for {tracking.phase}",
            "completion_record": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete SLA tracking: {str(e)}")


@router.get("/status/{cycle_id}/{report_id}")
@role_required(["Tester", "Test Manager", "Report Owner", "Report Owner Executive", "CDO"])
async def get_sla_status(
    cycle_id: int,
    report_id: int,
    current_user: User = Depends(get_current_user),
    sla_service: SLAService = Depends(get_sla_service)
) -> Dict[str, Any]:
    """Get SLA status for a specific cycle and report"""
    try:
        status = await sla_service.get_sla_status(cycle_id, report_id)
        return status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get SLA status: {str(e)}")


@router.get("/breaches")
@role_required(["Test Manager", "Report Owner Executive", "CDO", "Admin"])
async def get_sla_breaches(
    current_user: User = Depends(get_current_user),
    sla_service: SLAService = Depends(get_sla_service)
) -> Dict[str, Any]:
    """Get current SLA breaches"""
    try:
        breaches = await sla_service.check_breaches()
        
        return {
            "total_breaches": len(breaches),
            "breaches": breaches,
            "checked_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check SLA breaches: {str(e)}")


@router.post("/escalate")
@role_required(["Test Manager", "Report Owner", "CDO", "Admin"])
async def trigger_manual_escalation(
    escalation: EscalationTrigger,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    sla_service: SLAService = Depends(get_sla_service)
) -> Dict[str, Any]:
    """Manually trigger an escalation"""
    try:
        # Create breach info for manual escalation
        breach_info = {
            "cycle_id": escalation.cycle_id,
            "phase": escalation.phase,
            "breach_time": datetime.utcnow(),
            "severity": "MANUAL",
            "triggered_by": current_user.user_id,
            "reason": escalation.reason
        }
        
        # Trigger escalation
        result = await sla_service.escalation_manager.trigger_escalation(breach_info)
        
        return {
            "message": f"Manual escalation triggered for cycle {escalation.cycle_id}",
            "escalation_record": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger escalation: {str(e)}")


@router.get("/notifications")
@role_required(["Test Manager", "Report Owner", "Report Owner Executive", "CDO", "Admin"])
async def get_notifications(
    current_user: User = Depends(get_current_user),
    limit: int = 50,
    offset: int = 0
) -> Dict[str, Any]:
    """Get SLA notifications for the current user"""
    try:
        # In a real implementation, this would query notification records from database
        # For now, return simulated notifications
        
        notifications = [
            {
                "notification_id": f"notif_{i}",
                "type": "SLA_BREACH",
                "cycle_id": 1,
                "phase": "planning",
                "message": f"SLA breach in planning phase for cycle 1",
                "severity": "HIGH",
                "created_at": (datetime.utcnow() - timedelta(hours=i)).isoformat(),
                "read": False
            }
            for i in range(1, min(limit + 1, 6))  # Simulate up to 5 notifications
        ]
        
        return {
            "notifications": notifications[offset:offset + limit],
            "total_count": len(notifications),
            "unread_count": len([n for n in notifications if not n["read"]])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get notifications: {str(e)}")


@router.post("/notifications/{notification_id}/mark-read")
@role_required(["Tester", "Test Manager", "Report Owner", "Report Owner Executive", "CDO"])
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Mark a notification as read"""
    try:
        # In a real implementation, this would update the notification in database
        return {
            "message": f"Notification {notification_id} marked as read",
            "notification_id": notification_id,
            "marked_read_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to mark notification as read: {str(e)}")


@router.get("/dashboard")
@role_required(["Test Manager", "Report Owner Executive", "CDO", "Admin"])
async def get_sla_dashboard(
    current_user: User = Depends(get_current_user),
    sla_service: SLAService = Depends(get_sla_service)
) -> Dict[str, Any]:
    """Get SLA dashboard data"""
    try:
        # Check current breaches
        breaches = await sla_service.check_breaches()
        
        # Generate dashboard data
        dashboard_data = {
            "overview": {
                "total_active_slas": 15,
                "current_breaches": len(breaches),
                "breaches_this_week": 3,
                "average_resolution_time": "4.2 hours"
            },
            "phase_status": {
                "planning": {"active": 5, "on_time": 4, "at_risk": 1, "breached": 0},
                "scoping": {"active": 3, "on_time": 2, "at_risk": 0, "breached": 1},
                "data_provider_id": {"active": 2, "on_time": 2, "at_risk": 0, "breached": 0},
                "sample_selection": {"active": 4, "on_time": 3, "at_risk": 1, "breached": 0},
                "request_for_info": {"active": 1, "on_time": 1, "at_risk": 0, "breached": 0}
            },
            "recent_breaches": breaches[:5],  # Most recent 5 breaches
            "escalation_trends": {
                "level_1": 12,
                "level_2": 5,
                "level_3": 2,
                "level_4": 1
            },
            "performance_metrics": {
                "sla_compliance_rate": 87.5,
                "average_escalation_time": "2.1 hours",
                "resolution_rate": 94.2
            }
        }
        
        return dashboard_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get SLA dashboard: {str(e)}")


@router.post("/run-monitoring")
@role_required(["Admin"])
async def run_sla_monitoring(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    sla_service: SLAService = Depends(get_sla_service)
) -> Dict[str, Any]:
    """Manually trigger SLA monitoring (for testing/debugging)"""
    try:
        # Run SLA monitoring in background
        background_tasks.add_task(sla_service.run_sla_monitoring)
        
        return {
            "message": "SLA monitoring task started",
            "started_by": current_user.user_id,
            "started_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start SLA monitoring: {str(e)}") 