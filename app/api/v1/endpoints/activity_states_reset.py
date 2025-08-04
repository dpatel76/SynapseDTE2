"""
Activity Reset Endpoint Extension
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.activity_state_manager import get_activity_state_manager

router = APIRouter()


@router.post("/activities/{activity_id}/reset")
async def reset_activity(
    cycle_id: int,
    report_id: int,
    phase_name: str,
    activity_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Reset an activity and all dependent activities.
    
    Only Testers and Test Managers can reset activities.
    This will cascade reset all activities that depend on the reset activity.
    """
    
    if current_user.role not in ["Tester", "Test Manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Testers and Test Managers can reset activities"
        )
    
    manager = get_activity_state_manager(db)
    
    # Convert activity_id back to activity name (replace underscores with spaces and title case)
    activity_name = activity_id.replace('_', ' ').title()
    
    result = await manager.reset_activity_cascade(
        cycle_id=str(cycle_id),
        report_id=str(report_id),
        phase_name=phase_name,
        activity_name=activity_name,
        user_id=current_user.user_id,
        user_role=current_user.role
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result