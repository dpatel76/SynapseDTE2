"""
Activity Management API Endpoints
Generic endpoints for activity state transitions
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.core.logging import get_logger
from app.models.user import User
from app.services.activity_management_service import ActivityManagementService
from app.schemas.activity_management import (
    ActivityStateResponse, 
    ActivityTransitionRequest,
    ActivityResetRequest,
    PhaseActivitiesResponse
)

logger = get_logger(__name__)
router = APIRouter()


@router.get("/phases/{phase_name}/activities", response_model=PhaseActivitiesResponse)
async def get_phase_activities(
    phase_name: str,
    cycle_id: int = Query(..., description="Cycle ID"),
    report_id: int = Query(..., description="Report ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> PhaseActivitiesResponse:
    """Get all activities for a phase with their current states"""
    
    service = ActivityManagementService(db)
    activities = await service.get_phase_activities(phase_name, cycle_id, report_id)
    
    return PhaseActivitiesResponse(
        phase_name=phase_name,
        cycle_id=cycle_id,
        report_id=report_id,
        activities=activities
    )


@router.post("/activities/{activity_code}/transition", response_model=Dict[str, Any])
async def transition_activity(
    activity_code: str,
    request: ActivityTransitionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Transition an activity to a new state"""
    
    service = ActivityManagementService(db)
    
    try:
        result = await service.transition_activity(
            activity_code=activity_code,
            target_status=request.target_status,
            cycle_id=request.cycle_id,
            report_id=request.report_id,
            phase_name=request.phase_name,
            user_id=current_user.user_id,
            notes=request.notes,
            completion_data=request.completion_data
        )
        return result
    except Exception as e:
        logger.error(f"Error transitioning activity {activity_code}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/activities/{activity_code}/start", response_model=Dict[str, Any])
async def start_activity(
    activity_code: str,
    cycle_id: int = Body(...),
    report_id: int = Body(...),
    phase_name: str = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Start an activity (transition to active)"""
    
    service = ActivityManagementService(db)
    
    try:
        result = await service.transition_activity(
            activity_code=activity_code,
            target_status='active',
            cycle_id=cycle_id,
            report_id=report_id,
            phase_name=phase_name,
            user_id=current_user.user_id
        )
        return result
    except Exception as e:
        logger.error(f"Error starting activity {activity_code}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/activities/{activity_code}/complete", response_model=Dict[str, Any])
async def complete_activity(
    activity_code: str,
    cycle_id: int = Body(...),
    report_id: int = Body(...),
    phase_name: str = Body(...),
    notes: Optional[str] = Body(None),
    completion_data: Optional[Dict[str, Any]] = Body(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Complete an activity (transition to completed)"""
    
    service = ActivityManagementService(db)
    
    try:
        result = await service.transition_activity(
            activity_code=activity_code,
            target_status='completed',
            cycle_id=cycle_id,
            report_id=report_id,
            phase_name=phase_name,
            user_id=current_user.user_id,
            notes=notes,
            completion_data=completion_data
        )
        return result
    except Exception as e:
        logger.error(f"Error completing activity {activity_code}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/activities/{activity_code}/reset", response_model=Dict[str, Any])
async def reset_activity(
    activity_code: str,
    request: ActivityResetRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Reset an activity and optionally cascade to dependent activities"""
    
    service = ActivityManagementService(db)
    
    try:
        result = await service.reset_activity(
            activity_code=activity_code,
            cycle_id=request.cycle_id,
            report_id=request.report_id,
            phase_name=request.phase_name,
            user_id=current_user.user_id,
            cascade=request.cascade
        )
        return result
    except Exception as e:
        logger.error(f"Error resetting activity {activity_code}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/activities/definitions", response_model=List[Dict[str, Any]])
async def get_activity_definitions(
    phase_name: Optional[str] = Query(None, description="Filter by phase name"),
    is_active: bool = Query(True, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Get activity definitions (templates)"""
    
    from sqlalchemy import select, and_
    from app.models.activity_definition import ActivityDefinition
    
    query = select(ActivityDefinition)
    conditions = []
    
    if phase_name:
        conditions.append(ActivityDefinition.phase_name == phase_name)
    conditions.append(ActivityDefinition.is_active == is_active)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    query = query.order_by(ActivityDefinition.phase_name, ActivityDefinition.sequence_order)
    
    result = await db.execute(query)
    definitions = result.scalars().all()
    
    return [
        {
            'id': d.id,
            'phase_name': d.phase_name,
            'activity_name': d.activity_name,
            'activity_code': d.activity_code,
            'description': d.description,
            'activity_type': d.activity_type,
            'sequence_order': d.sequence_order,
            'button_text': d.button_text,
            'success_message': d.success_message,
            'instructions': d.instructions,
            'can_skip': d.can_skip,
            'can_reset': d.can_reset,
            'is_active': d.is_active
        }
        for d in definitions
    ]