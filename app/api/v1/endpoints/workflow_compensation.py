"""Workflow Compensation and Retry Monitoring API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from app.api.v1.deps import get_current_user, get_db
from app.models.user import User
from app.core.dependencies import require_roles
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/compensation-logs")
async def get_compensation_logs(
    workflow_id: Optional[str] = None,
    phase: Optional[str] = None,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(50, le=200),
    current_user: User = Depends(require_roles(["Test Manager", "Report Owner Executive"])),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get compensation logs for workflows"""
    
    # Build query
    query = "SELECT * FROM workflow_compensation_log WHERE 1=1"
    params = {}
    
    if workflow_id:
        query += " AND workflow_id = :workflow_id"
        params["workflow_id"] = workflow_id
    
    if phase:
        query += " AND phase = :phase"
        params["phase"] = phase
    
    if start_date:
        query += " AND timestamp >= :start_date"
        params["start_date"] = start_date
    
    if end_date:
        query += " AND timestamp <= :end_date"
        params["end_date"] = end_date
    
    query += " ORDER BY timestamp DESC LIMIT :limit"
    params["limit"] = limit
    
    # Execute query
    result = await db.execute(query, params)
    logs = result.fetchall()
    
    return {
        "count": len(logs),
        "logs": [
            {
                "log_id": log.log_id,
                "workflow_id": log.workflow_id,
                "phase": log.phase,
                "action": log.action,
                "error": log.error,
                "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                "success": log.success,
                "details": log.details
            }
            for log in logs
        ]
    }


@router.get("/retry-statistics")
async def get_retry_statistics(
    phase: Optional[str] = None,
    activity_type: Optional[str] = None,
    time_range: str = Query("7d", regex="^(1d|7d|30d|90d)$"),
    current_user: User = Depends(require_roles(["Test Manager", "Report Owner Executive"])),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get retry statistics for workflow activities"""
    
    # Calculate date range
    end_date = datetime.utcnow()
    if time_range == "1d":
        start_date = end_date - timedelta(days=1)
    elif time_range == "7d":
        start_date = end_date - timedelta(days=7)
    elif time_range == "30d":
        start_date = end_date - timedelta(days=30)
    else:  # 90d
        start_date = end_date - timedelta(days=90)
    
    # Get retry statistics
    query = """
    SELECT 
        phase,
        activity_type,
        COUNT(*) as total_attempts,
        SUM(CASE WHEN retry_count = 0 THEN 1 ELSE 0 END) as first_attempt_success,
        SUM(CASE WHEN retry_count > 0 AND success = true THEN 1 ELSE 0 END) as retry_success,
        SUM(CASE WHEN success = false THEN 1 ELSE 0 END) as failed,
        AVG(retry_count) as avg_retries,
        MAX(retry_count) as max_retries
    FROM workflow_activity_retry_log
    WHERE timestamp >= :start_date AND timestamp <= :end_date
    """
    
    params = {"start_date": start_date, "end_date": end_date}
    
    if phase:
        query += " AND phase = :phase"
        params["phase"] = phase
    
    if activity_type:
        query += " AND activity_type = :activity_type"
        params["activity_type"] = activity_type
    
    query += " GROUP BY phase, activity_type ORDER BY total_attempts DESC"
    
    result = await db.execute(query, params)
    stats = result.fetchall()
    
    # Calculate overall statistics
    total_attempts = sum(s.total_attempts for s in stats)
    total_first_success = sum(s.first_attempt_success for s in stats)
    total_retry_success = sum(s.retry_success for s in stats)
    total_failed = sum(s.failed for s in stats)
    
    return {
        "time_range": time_range,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "overall": {
            "total_attempts": total_attempts,
            "first_attempt_success_rate": (total_first_success / total_attempts * 100) if total_attempts > 0 else 0,
            "retry_success_rate": (total_retry_success / (total_attempts - total_first_success) * 100) if (total_attempts - total_first_success) > 0 else 0,
            "failure_rate": (total_failed / total_attempts * 100) if total_attempts > 0 else 0
        },
        "by_phase": [
            {
                "phase": stat.phase,
                "activity_type": stat.activity_type,
                "total_attempts": stat.total_attempts,
                "first_attempt_success": stat.first_attempt_success,
                "retry_success": stat.retry_success,
                "failed": stat.failed,
                "avg_retries": float(stat.avg_retries),
                "max_retries": stat.max_retries
            }
            for stat in stats
        ]
    }


@router.get("/compensation-actions/{workflow_id}")
async def get_workflow_compensation_actions(
    workflow_id: str,
    current_user: User = Depends(require_roles(["Test Manager"])),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get detailed compensation actions for a specific workflow"""
    
    # Get compensation logs
    comp_logs = await db.execute(
        """
        SELECT * FROM workflow_compensation_log 
        WHERE workflow_id = :workflow_id 
        ORDER BY timestamp ASC
        """,
        {"workflow_id": workflow_id}
    )
    
    compensation_actions = comp_logs.fetchall()
    
    # Get workflow details
    workflow = await db.execute(
        """
        SELECT * FROM workflow_execution
        WHERE workflow_id = :workflow_id
        """,
        {"workflow_id": workflow_id}
    )
    workflow_data = workflow.fetchone()
    
    if not workflow_data:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return {
        "workflow_id": workflow_id,
        "workflow_status": workflow_data.status if workflow_data else "unknown",
        "compensation_actions": [
            {
                "phase": action.phase,
                "action_type": action.action,
                "timestamp": action.timestamp.isoformat() if action.timestamp else None,
                "success": action.success,
                "error": action.error,
                "rollback_phases": action.rollback_phases,
                "notifications_sent": action.notifications_sent,
                "manual_intervention_required": action.manual_intervention_required,
                "details": action.details
            }
            for action in compensation_actions
        ],
        "total_compensations": len(compensation_actions),
        "requires_manual_review": any(
            action.manual_intervention_required for action in compensation_actions
        )
    }


@router.post("/retry-policy/update")
async def update_retry_policy(
    activity_type: str,
    max_attempts: Optional[int] = None,
    initial_interval_seconds: Optional[int] = None,
    backoff_coefficient: Optional[float] = None,
    max_interval_seconds: Optional[int] = None,
    current_user: User = Depends(require_roles(["Test Manager"])),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Update retry policy for an activity type (requires restart to take effect)"""
    
    # Validate activity type
    valid_types = ["data_fetch", "llm_request", "database_operation", "email_notification", "phase_transition"]
    if activity_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid activity type. Must be one of: {', '.join(valid_types)}"
        )
    
    # Store policy update in database
    await db.execute(
        """
        INSERT INTO workflow_retry_policy_config 
        (activity_type, max_attempts, initial_interval_seconds, backoff_coefficient, max_interval_seconds, updated_by, updated_at)
        VALUES (:activity_type, :max_attempts, :initial_interval, :backoff, :max_interval, :user_id, :timestamp)
        ON CONFLICT (activity_type) DO UPDATE SET
            max_attempts = COALESCE(:max_attempts, workflow_retry_policy_config.max_attempts),
            initial_interval_seconds = COALESCE(:initial_interval, workflow_retry_policy_config.initial_interval_seconds),
            backoff_coefficient = COALESCE(:backoff, workflow_retry_policy_config.backoff_coefficient),
            max_interval_seconds = COALESCE(:max_interval, workflow_retry_policy_config.max_interval_seconds),
            updated_by = :user_id,
            updated_at = :timestamp
        """,
        {
            "activity_type": activity_type,
            "max_attempts": max_attempts,
            "initial_interval": initial_interval_seconds,
            "backoff": backoff_coefficient,
            "max_interval": max_interval_seconds,
            "user_id": current_user.user_id,
            "timestamp": datetime.utcnow()
        }
    )
    await db.commit()
    
    return {
        "message": "Retry policy updated successfully",
        "activity_type": activity_type,
        "note": "Changes will take effect on next worker restart"
    }