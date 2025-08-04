"""
Activity States API endpoints
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.core.logging import get_logger
from app.services.activity_management_service import ActivityManagementService
from app.models.user import User

logger = get_logger(__name__)

router = APIRouter()


@router.get("/cycles/{cycle_id}/reports/{report_id}/phases/{phase_name}/activities")
async def get_phase_activities(
    cycle_id: int,
    report_id: int,
    phase_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get all activities for a phase with their current status"""
    
    service = ActivityManagementService(db)
    try:
        activities = await service.get_phase_activities(phase_name, cycle_id, report_id)
        
        # Format response to match expected structure
        total = len(activities)
        completed = sum(1 for a in activities if a['status'] == 'completed')
        in_progress = sum(1 for a in activities if a['status'] == 'active')
        
        return {
            "phase_name": phase_name,
            "activities": activities,
            "progress": {
                "total": total,
                "completed": completed,
                "in_progress": in_progress,
                "completion_percentage": int((completed / total * 100) if total > 0 else 0)
            }
        }
    except Exception as e:
        logger.error(f"Error getting phase activities: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/activities/{activity_name}/transition")
async def transition_activity(
    activity_name: str,
    target_status: str,
    cycle_id: int = Query(...),
    report_id: int = Query(...),
    phase_name: str = Query(...),
    reason: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Transition an activity to a new state"""
    
    service = ActivityManagementService(db)
    
    try:
        # Get activities to find the activity code
        activities = await service.get_phase_activities(phase_name, cycle_id, report_id)
        activity = next((a for a in activities if a['name'] == activity_name), None)
        
        if not activity:
            raise HTTPException(status_code=404, detail=f"Activity '{activity_name}' not found")
        
        # Map status names
        status_mapping = {
            'in_progress': 'active',
            'completed': 'completed',
            'not_started': 'pending',
            'revision_requested': 'blocked',
            'blocked': 'blocked',
            'skipped': 'skipped'
        }
        
        mapped_status = status_mapping.get(target_status.lower(), target_status)
        
        result = await service.transition_activity(
            activity_code=activity['activity_id'],
            target_status=mapped_status,
            cycle_id=cycle_id,
            report_id=report_id,
            phase_name=phase_name,
            user_id=current_user.user_id,
            notes=reason
        )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error transitioning activity: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{activity_name}/reset")
async def reset_activity_cascade(
    activity_name: str,
    cycle_id: int = Query(...),
    report_id: int = Query(...),
    phase_name: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Reset an activity and all dependent activities"""
    
    # Use ActivityManagementService which is the primary system
    from app.services.activity_management_service import ActivityManagementService
    
    service = ActivityManagementService(db)
    
    # Check permissions
    if current_user.role not in ["Tester", "Test Manager"]:
        raise HTTPException(
            status_code=403,
            detail="Only Tester or Test Manager can reset activities"
        )
    
    try:
        # Get the activity to reset
        activities = await service.get_phase_activities(phase_name, cycle_id, report_id)
        
        activity_to_reset = None
        activity_to_reset_idx = None
        for idx, activity in enumerate(activities):
            # Activities are dictionaries, not objects
            if activity.get('name') == activity_name:
                activity_to_reset = activity
                activity_to_reset_idx = idx
                break
        
        if not activity_to_reset:
            raise HTTPException(
                status_code=404,
                detail=f"Activity '{activity_name}' not found"
            )
        
        if activity_to_reset.get('status') != 'completed':
            raise HTTPException(
                status_code=400,
                detail="Can only reset completed activities"
            )
        
        # Use the reset_activity method from ActivityManagementService
        activity_code = activity_to_reset.get('activity_id')
        result = await service.reset_activity(
            activity_code=activity_code,
            cycle_id=cycle_id,
            report_id=report_id,
            phase_name=phase_name,
            user_id=current_user.user_id,
            cascade=True
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting activity: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset activity: {str(e)}"
        )


@router.post("/activities/start")
async def start_activity(
    activity_name: str,
    cycle_id: int = Query(...),
    report_id: int = Query(...),
    phase_name: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Start an activity (transition to active)"""
    
    return await transition_activity(
        activity_name=activity_name,
        target_status="in_progress",  # Will be mapped to 'active' internally
        cycle_id=cycle_id,
        report_id=report_id,
        phase_name=phase_name,
        db=db,
        current_user=current_user
    )


@router.post("/activities/complete")
async def complete_activity(
    activity_name: str,
    cycle_id: int = Query(...),
    report_id: int = Query(...),
    phase_name: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Complete an activity (transition to completed)"""
    
    return await transition_activity(
        activity_name=activity_name,
        target_status="completed",
        cycle_id=cycle_id,
        report_id=report_id,
        phase_name=phase_name,
        db=db,
        current_user=current_user
    )