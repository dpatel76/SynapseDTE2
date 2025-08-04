"""
Unified Status API - Single endpoint for all phase and activity status
"""

from typing import Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.auth import RoleChecker, UserRoles
from app.models.user import User
from app.services.unified_status_service import get_unified_status_service, UnifiedStatusService, PhaseStatus, ActivityStatus
from app.schemas.unified_status import PhaseStatusSchema, ActivityStatusSchema, AllPhasesStatusSchema
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Define role access
all_roles = [UserRoles.TESTER, UserRoles.REPORT_OWNER, UserRoles.REPORT_OWNER_EXECUTIVE, 
             UserRoles.TEST_EXECUTIVE, UserRoles.DATA_OWNER, UserRoles.DATA_EXECUTIVE, UserRoles.ADMIN]

def _convert_activity_to_schema(activity: ActivityStatus) -> ActivityStatusSchema:
    """Convert ActivityStatus dataclass to Pydantic schema"""
    return ActivityStatusSchema(
        activity_id=activity.activity_id,
        name=activity.name,
        description=activity.description,
        status=activity.status,
        can_start=activity.can_start,
        can_complete=activity.can_complete,
        can_reset=getattr(activity, 'can_reset', False),
        completion_percentage=activity.completion_percentage,
        blocking_reason=activity.blocking_reason,
        last_updated=activity.last_updated,
        metadata=activity.metadata or {}
    )

def _convert_phase_to_schema(phase: PhaseStatus) -> PhaseStatusSchema:
    """Convert PhaseStatus dataclass to Pydantic schema"""
    return PhaseStatusSchema(
        phase_name=phase.phase_name,
        cycle_id=phase.cycle_id,
        report_id=phase.report_id,
        phase_status=phase.phase_status,
        overall_completion_percentage=phase.overall_completion_percentage,
        activities=[_convert_activity_to_schema(activity) for activity in phase.activities],
        can_proceed_to_next=phase.can_proceed_to_next,
        blocking_issues=phase.blocking_issues,
        last_updated=phase.last_updated,
        metadata=phase.metadata or {}
    )

@router.get("/cycles/{cycle_id}/reports/{report_id}/phases/{phase_name}/status")
async def get_phase_status(
    cycle_id: int,
    report_id: int,
    phase_name: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> PhaseStatusSchema:
    """Get unified status for a specific phase including all activities"""
    
    # Check permissions - all authenticated users can view status
    RoleChecker(all_roles)(current_user)
    
    try:
        print(f"API: Getting status for phase {phase_name}, cycle {cycle_id}, report {report_id}")
        # Use dependency injection pattern to ensure proper session lifecycle
        status_service = get_unified_status_service(db)
        phase_status = await status_service.get_phase_status(phase_name, cycle_id, report_id)
        return _convert_phase_to_schema(phase_status)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"Error getting phase status for {phase_name}: {str(e)}\n{tb}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get phase status for {phase_name}: {str(e)}"
        )

@router.get("/cycles/{cycle_id}/reports/{report_id}/status/all")
async def get_all_phases_status(
    cycle_id: int,
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, PhaseStatusSchema]:
    """Get unified status for all phases"""
    
    # Check permissions - all authenticated users can view status
    RoleChecker(all_roles)(current_user)
    
    phases = [
        "Planning",
        "Scoping", 
        "Data Provider ID",
        "CycleReportSampleSelectionSamples Selection",
        "Request Info",
        "Testing",
        "Observation Management"
    ]
    
    try:
        status_service = get_unified_status_service(db)
        result = {}
        for phase_name in phases:
            try:
                phase_status = await status_service.get_phase_status(phase_name, cycle_id, report_id)
                result[phase_name] = _convert_phase_to_schema(phase_status)
            except Exception as e:
                logger.warning(f"Failed to get status for phase {phase_name}: {str(e)}")
                # Continue with other phases even if one fails
                continue
        
        return result
    except Exception as e:
        logger.error(f"Error getting all phases status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get phases status"
        )

@router.get("/cycles/{cycle_id}/reports/{report_id}/phases/{phase_name}/activities/{activity_id}/status")
async def get_activity_status(
    cycle_id: int,
    report_id: int,
    phase_name: str,
    activity_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ActivityStatusSchema:
    """Get status for a specific activity within a phase"""
    
    # Check permissions - all authenticated users can view status
    RoleChecker(all_roles)(current_user)
    
    try:
        status_service = get_unified_status_service(db)
        phase_status = await status_service.get_phase_status(phase_name, cycle_id, report_id)
        
        # Find the specific activity
        activity = next((a for a in phase_status.activities if a.activity_id == activity_id), None)
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Activity '{activity_id}' not found in phase '{phase_name}'"
            )
        
        return _convert_activity_to_schema(activity)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting activity status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get activity status"
        )