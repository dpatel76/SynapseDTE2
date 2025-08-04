"""
Scoping API Endpoints - Consolidated Version Management System

This module provides REST API endpoints for the consolidated scoping system,
implementing comprehensive version and attribute management.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
import logging

from app.core.database import get_db
from app.core.auth import get_current_user
from app.core.exceptions import (
    ValidationError, NotFoundError, ConflictError, 
    BusinessLogicError, PermissionError
)
from app.models.user import User
from app.models.scoping import ScopingVersion, ScopingAttribute
from app.services.scoping_service import ScopingService
from app.schemas.scoping import (
    # Version schemas
    ScopingVersionCreate, ScopingVersionUpdate, ScopingVersionResponse,
    ScopingVersionSummary, VersionStatistics, VersionQueryParams,
    VersionSubmissionCreate, VersionApprovalCreate, VersionRejectionCreate,
    VersionCopyCreate,
    
    # Attribute schemas
    ScopingAttributeCreate, ScopingAttributesBulkCreate, ScopingAttributeUpdate,
    ScopingAttributeResponse, ScopingAttributeSummary, AttributeDecisionSummary,
    AttributeQueryParams, TesterDecisionCreate, ReportOwnerDecisionCreate,
    BulkTesterDecisionCreate, BulkUpdateResponse,
    
    # Utility schemas
    APIErrorResponse, LLMRecommendationCreate
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scoping", tags=["scoping"])


# Version Management Endpoints
@router.post("/versions", response_model=ScopingVersionResponse, status_code=status.HTTP_201_CREATED)
async def create_version(
    version_data: ScopingVersionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new scoping version.
    
    Creates a new version for scoping decisions within a workflow phase.
    """
    try:
        service = ScopingService(db)
        version = await service.create_version(
            phase_id=version_data.phase_id,
            workflow_activity_id=version_data.workflow_activity_id,
            workflow_execution_id=version_data.workflow_execution_id,
            workflow_run_id=version_data.workflow_run_id,
            activity_name=version_data.activity_name,
            user_id=current_user.user_id,
            notes=version_data.notes
        )
        return version
    except (ValidationError, ConflictError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/versions/{version_id}", response_model=ScopingVersionResponse)
async def get_version(
    version_id: UUID = Path(..., description="Version ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific scoping version.
    
    Retrieves detailed information about a scoping version including its
    summary statistics and workflow status.
    """
    try:
        service = ScopingService(db)
        version = await service.get_version(version_id)
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Version {version_id} not found"
            )
        return version
    except Exception as e:
        logger.error(f"Error retrieving version {version_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/phases/{phase_id}/current-version", response_model=Optional[ScopingVersionResponse])
async def get_current_version(
    phase_id: int = Path(..., description="Phase ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the current approved version for a phase.
    
    Retrieves the currently approved scoping version for a workflow phase.
    """
    try:
        service = ScopingService(db)
        version = await service.get_current_version(phase_id)
        return version
    except Exception as e:
        logger.error(f"Error retrieving current version for phase {phase_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/versions/{version_id}/attributes", response_model=List[ScopingAttributeResponse], status_code=status.HTTP_201_CREATED)
async def add_attributes_to_version(
    version_id: UUID = Path(..., description="Version ID"),
    attributes_data: ScopingAttributesBulkCreate = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add attributes to a scoping version.
    
    Bulk adds planning attributes to a version with their LLM recommendations.
    """
    try:
        service = ScopingService(db)
        
        # Extract data for service call
        planning_attribute_ids = [attr.planning_attribute_id for attr in attributes_data.attributes]
        llm_recommendations = [attr.llm_recommendation.dict() for attr in attributes_data.attributes]
        
        attributes = await service.add_attributes_to_version(
            version_id=version_id,
            planning_attribute_ids=planning_attribute_ids,
            llm_recommendations=llm_recommendations,
            user_id=current_user.user_id
        )
        
        return attributes
    except (ValidationError, BusinessLogicError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/attributes/{attribute_id}/tester-decision", response_model=ScopingAttributeResponse)
async def make_tester_decision(
    attribute_id: UUID = Path(..., description="Attribute ID"),
    decision_data: TesterDecisionCreate = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Make a tester decision on a scoping attribute.
    
    Records the tester's decision (accept, decline, or override) for an attribute.
    """
    try:
        service = ScopingService(db)
        attribute = await service.make_tester_decision(
            attribute_id=attribute_id,
            decision=decision_data.decision,
            final_scoping=decision_data.final_scoping,
            rationale=decision_data.rationale,
            override_reason=decision_data.override_reason,
            user_id=current_user.user_id
        )
        return attribute
    except (ValidationError, BusinessLogicError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/attributes/{attribute_id}/report-owner-decision", response_model=ScopingAttributeResponse)
async def make_report_owner_decision(
    attribute_id: UUID = Path(..., description="Attribute ID"),
    decision_data: ReportOwnerDecisionCreate = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Make a report owner decision on a scoping attribute.
    
    Records the report owner's decision (approved, rejected, etc.) for an attribute.
    """
    try:
        service = ScopingService(db)
        attribute = await service.make_report_owner_decision(
            attribute_id=attribute_id,
            decision=decision_data.decision,
            notes=decision_data.notes,
            user_id=current_user.user_id
        )
        return attribute
    except (ValidationError, BusinessLogicError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/versions/{version_id}/submit", response_model=ScopingVersionResponse)
async def submit_version_for_approval(
    version_id: UUID = Path(..., description="Version ID"),
    submission_data: VersionSubmissionCreate = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit a version for approval.
    
    Transitions a version from draft to pending approval status.
    All attributes must have tester decisions before submission.
    """
    try:
        service = ScopingService(db)
        version = await service.submit_version_for_approval(
            version_id=version_id,
            submission_notes=submission_data.submission_notes,
            user_id=current_user.user_id
        )
        
        # Update assessments if provided
        if submission_data.resource_impact_assessment:
            version.resource_impact_assessment = submission_data.resource_impact_assessment
        if submission_data.risk_coverage_assessment:
            version.risk_coverage_assessment = submission_data.risk_coverage_assessment
        
        await db.commit()
        await db.refresh(version)
        
        return version
    except (ValidationError, BusinessLogicError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/versions/{version_id}/approve", response_model=ScopingVersionResponse)
async def approve_version(
    version_id: UUID = Path(..., description="Version ID"),
    approval_data: VersionApprovalCreate = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Approve a version.
    
    Approves a version that is pending approval, making it the current
    approved version for the phase.
    """
    try:
        service = ScopingService(db)
        version = await service.approve_version(
            version_id=version_id,
            approval_notes=approval_data.approval_notes,
            user_id=current_user.user_id
        )
        return version
    except (ValidationError, BusinessLogicError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/versions/{version_id}/reject", response_model=ScopingVersionResponse)
async def reject_version(
    version_id: UUID = Path(..., description="Version ID"),
    rejection_data: VersionRejectionCreate = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Reject a version.
    
    Rejects a version that is pending approval, allowing it to be edited
    and resubmitted.
    """
    try:
        service = ScopingService(db)
        version = await service.reject_version(
            version_id=version_id,
            rejection_reason=rejection_data.rejection_reason,
            requested_changes=rejection_data.requested_changes,
            user_id=current_user.user_id
        )
        return version
    except (ValidationError, BusinessLogicError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("/versions/{version_id}/statistics", response_model=VersionStatistics)
async def get_version_statistics(
    version_id: UUID = Path(..., description="Version ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive statistics for a version.
    
    Returns detailed statistics including decision progress, accuracy metrics,
    and summary information.
    """
    try:
        service = ScopingService(db)
        statistics = await service.get_version_statistics(version_id)
        return statistics
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error retrieving statistics for version {version_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


# Legacy endpoints for backward compatibility
@router.get("/cycles/{cycle_id}/reports/{report_id}/current-version")
async def get_current_version_legacy(
    cycle_id: int,
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Legacy endpoint for backward compatibility"""
    try:
        # Get the phase for this cycle/report
        from app.models.workflow import WorkflowPhase
        phase = await db.execute(
            select(WorkflowPhase).where(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == "Scoping"
            )
        )
        phase_result = phase.scalar_one_or_none()
        
        if not phase_result:
            raise HTTPException(status_code=404, detail="Scoping phase not found")
        
        service = ScopingService(db)
        version = await service.get_current_version(phase_result.phase_id)
        return version
    except Exception as e:
        logger.error(f"Error retrieving current version for cycle {cycle_id}, report {report_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


# Health check endpoint
@router.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring.
    
    Returns the health status of the consolidated scoping API.
    """
    return {
        "status": "healthy",
        "service": "scoping-consolidated",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }