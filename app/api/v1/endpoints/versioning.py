"""
Versioning API endpoints
Provides version management capabilities for versioned entities
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.versioned_models import VersioningService
from app.schemas.versioning import (
    CreateVersionRequest,
    VersionHistoryResponse,
    VersionComparisonResponse,
    RevertVersionRequest
)

router = APIRouter()


@router.post("/create")
async def create_version(
    request: CreateVersionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Create a new version of an entity.
    
    Supports versioning for:
    - Report Attributes
    - CycleReportSampleSelectionSamples Sets
    - Data Profiling Rules
    - Test Executions
    - Observations
    - Scoping Decisions
    """
    
    try:
        # Map entity type to model class
        entity_class = _get_entity_class(request.entity_type)
        
        # Get the entity
        entity = await db.get(entity_class, request.entity_id)
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{request.entity_type} not found"
            )
        
        # Check permissions (simplified - should be role-based)
        if not _can_create_version(current_user, entity):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to create versions for this entity"
            )
        
        # Create new version
        new_version = await VersioningService.create_version(
            db_session=db,
            entity=entity,
            reason=request.reason,
            user_id=current_user.user_id,
            notes=request.notes,
            auto_approve=request.auto_approve
        )
        
        return {
            "success": True,
            "version_id": str(new_version.id),
            "version_number": new_version.version_number,
            "status": new_version.version_status
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create version: {str(e)}"
        )


@router.get("/history/{entity_type}/{entity_id}")
async def get_version_history(
    entity_type: str,
    entity_id: str,
    limit: int = Query(10, description="Number of history records to return"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> VersionHistoryResponse:
    """
    Get version history for an entity.
    
    Returns list of all versions with change information.
    """
    
    try:
        history = await VersioningService.get_version_history(
            db_session=db,
            entity_type=entity_type,
            entity_id=entity_id,
            limit=limit
        )
        
        return VersionHistoryResponse(
            entity_type=entity_type,
            entity_id=entity_id,
            history=[
                {
                    "version_number": h.version_number,
                    "change_type": h.change_type,
                    "change_reason": h.change_reason,
                    "changed_by": h.changed_by,
                    "changed_at": h.changed_at.isoformat(),
                    "change_details": h.change_details
                }
                for h in history
            ]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get version history: {str(e)}"
        )


@router.get("/compare")
async def compare_versions(
    entity_type: str = Query(..., description="Type of entity"),
    version1_id: str = Query(..., description="ID of first version"),
    version2_id: str = Query(..., description="ID of second version"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> VersionComparisonResponse:
    """
    Compare two versions of an entity.
    
    Returns differences between the versions.
    """
    
    try:
        entity_class = _get_entity_class(entity_type)
        
        comparison = await VersioningService.compare_versions(
            db_session=db,
            entity_class=entity_class,
            version1_id=version1_id,
            version2_id=version2_id
        )
        
        return VersionComparisonResponse(**comparison)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compare versions: {str(e)}"
        )


@router.post("/revert")
async def revert_to_version(
    request: RevertVersionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Revert to a previous version of an entity.
    
    Creates a new version with content from the target version.
    """
    
    try:
        entity_class = _get_entity_class(request.entity_type)
        
        # Check permissions
        if current_user.role not in ["Test Manager", "Report Owner", "Admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Test Managers and Report Owners can revert versions"
            )
        
        new_version = await VersioningService.revert_to_version(
            db_session=db,
            entity_class=entity_class,
            entity_id=request.entity_id,
            target_version_number=request.target_version_number,
            user_id=current_user.user_id,
            reason=request.reason
        )
        
        return {
            "success": True,
            "new_version_id": str(new_version.id),
            "new_version_number": new_version.version_number,
            "reverted_from": request.target_version_number
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revert version: {str(e)}"
        )


@router.post("/approve/{entity_type}/{version_id}")
async def approve_version(
    entity_type: str,
    version_id: str,
    notes: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Approve a version.
    
    Only Report Owners and Test Managers can approve versions.
    """
    
    if current_user.role not in ["Report Owner", "Report Owner Executive", "Test Manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to approve versions"
        )
    
    try:
        entity_class = _get_entity_class(entity_type)
        
        # Get the version
        version = await db.get(entity_class, version_id)
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Version not found"
            )
        
        # Approve
        version.approve_version(current_user.user_id)
        if notes:
            version.version_notes = f"{version.version_notes}\nApproval notes: {notes}" if version.version_notes else f"Approval notes: {notes}"
        
        # Create history record
        from app.models.versioning import VersionHistory
        
        history = VersionHistory.record_change(
            entity_type=entity_type,
            entity_id=str(version.id),
            entity_name=getattr(version, 'name', str(version.id)),
            version_number=version.version_number,
            change_type="approved",
            changed_by=current_user.user_id,
            change_reason=notes,
            cycle_id=getattr(version, 'cycle_id', None),
            report_id=getattr(version, 'report_id', None)
        )
        
        db.add(history)
        await db.commit()
        
        return {
            "success": True,
            "version_id": version_id,
            "status": "approved",
            "approved_by": current_user.user_id
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve version: {str(e)}"
        )


@router.post("/reject/{entity_type}/{version_id}")
async def reject_version(
    entity_type: str,
    version_id: str,
    reason: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Reject a version.
    
    Only Report Owners and Test Managers can reject versions.
    """
    
    if current_user.role not in ["Report Owner", "Report Owner Executive", "Test Manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to reject versions"
        )
    
    try:
        entity_class = _get_entity_class(entity_type)
        
        # Get the version
        version = await db.get(entity_class, version_id)
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Version not found"
            )
        
        # Reject
        version.reject_version(current_user.user_id, reason)
        
        # Create history record
        from app.models.versioning import VersionHistory
        
        history = VersionHistory.record_change(
            entity_type=entity_type,
            entity_id=str(version.id),
            entity_name=getattr(version, 'name', str(version.id)),
            version_number=version.version_number,
            change_type="rejected",
            changed_by=current_user.user_id,
            change_reason=reason,
            cycle_id=getattr(version, 'cycle_id', None),
            report_id=getattr(version, 'report_id', None)
        )
        
        db.add(history)
        await db.commit()
        
        return {
            "success": True,
            "version_id": version_id,
            "status": "rejected",
            "rejected_by": current_user.user_id
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reject version: {str(e)}"
        )


@router.get("/latest/{entity_type}/{entity_id}")
async def get_latest_version(
    entity_type: str,
    entity_id: str,
    approved_only: bool = Query(False, description="Only return approved versions"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get the latest version of an entity.
    
    Can filter to only approved versions.
    """
    
    try:
        from sqlalchemy import select
        
        entity_class = _get_entity_class(entity_type)
        
        # Build query
        query = select(entity_class).where(
            (entity_class.id == entity_id) &
            (entity_class.is_latest_version == True)
        )
        
        if approved_only:
            query = query.where(entity_class.version_status == "approved")
        
        result = await db.execute(query)
        latest_version = result.scalar_one_or_none()
        
        if not latest_version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No version found matching criteria"
            )
        
        return {
            "version_id": str(latest_version.id),
            "version_number": latest_version.version_number,
            "status": latest_version.version_status,
            "created_at": latest_version.version_created_at.isoformat(),
            "created_by": latest_version.version_created_by
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get latest version: {str(e)}"
        )


# Helper functions

def _get_entity_class(entity_type: str):
    """Map entity type string to model class"""
    from app.models.report_attribute import ReportAttribute
    from app.models.sample_selection import SampleSet
    from app.models.versioned_models import (
        DataProfilingRuleVersion,
        TestExecutionVersion,
        ObservationVersion,
        ScopingDecisionVersion
    )
    
    entity_map = {
        "ReportAttribute": ReportAttribute,
        "SampleSet": SampleSet,
        "DataProfilingRule": DataProfilingRuleVersion,
        "TestExecution": TestExecutionVersion,
        "Observation": ObservationVersion,
        "ScopingDecision": ScopingDecisionVersion
    }
    
    if entity_type not in entity_map:
        raise ValueError(f"Unknown entity type: {entity_type}")
    
    return entity_map[entity_type]


def _can_create_version(user: User, entity) -> bool:
    """Check if user can create version for entity"""
    # Simplified permission check
    # In production, this would check specific permissions per entity type
    
    allowed_roles = {
        "Tester": ["ReportAttribute", "DataProfilingRule", "TestExecution", "Observation"],
        "Test Manager": ["ReportAttribute", "SampleSet", "DataProfilingRule", "TestExecution", "Observation", "ScopingDecision"],
        "Report Owner": ["ReportAttribute", "SampleSet", "ScopingDecision"],
        "Data Owner": ["TestExecution"],
        "Admin": ["ReportAttribute", "SampleSet", "DataProfilingRule", "TestExecution", "Observation", "ScopingDecision"]
    }
    
    user_allowed_types = allowed_roles.get(user.role, [])
    entity_type = entity.__class__.__name__
    
    return entity_type in user_allowed_types