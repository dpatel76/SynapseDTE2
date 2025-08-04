"""
Scoping V2 API Endpoints - New consolidated scoping system

This module provides REST API endpoints for the new scoping system,
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
from app.models.scoping_v2 import ScopingAttribute
from app.services.scoping_service import ScopingService
from app.schemas.scoping_v2 import (
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

router = APIRouter(prefix="/scoping/v2", tags=["scoping-v2"])


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


@router.get("/versions/{version_id}/with-attributes", response_model=ScopingVersionResponse)
async def get_version_with_attributes(
    version_id: UUID = Path(..., description="Version ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a version with all its attributes loaded.
    
    Retrieves a version including all associated scoping attributes for
    comprehensive version analysis.
    """
    try:
        service = ScopingService(db)
        version = await service.get_version_with_attributes(version_id)
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Version {version_id} not found"
            )
        return version
    except Exception as e:
        logger.error(f"Error retrieving version with attributes {version_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/versions", response_model=List[ScopingVersionSummary])
async def get_versions(
    phase_id: Optional[int] = Query(None, description="Filter by phase ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(10, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    include_attributes: bool = Query(False, description="Include attributes in response"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get versions with optional filtering.
    
    Retrieves a list of scoping versions with optional filtering by phase,
    status, and other criteria.
    """
    try:
        service = ScopingService(db)
        if phase_id:
            versions = await service.get_phase_versions(
                phase_id=phase_id,
                limit=limit,
                offset=offset,
                include_attributes=include_attributes
            )
        else:
            # For now, return empty list if no phase_id provided
            # This could be enhanced to support cross-phase querying
            versions = []
        
        return versions
    except Exception as e:
        logger.error(f"Error retrieving versions: {str(e)}")
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


@router.get("/phases/{phase_id}/latest-version", response_model=Optional[ScopingVersionResponse])
async def get_latest_version(
    phase_id: int = Path(..., description="Phase ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the latest version for a phase.
    
    Retrieves the most recent scoping version for a workflow phase,
    regardless of its approval status.
    """
    try:
        service = ScopingService(db)
        version = await service.get_latest_version(phase_id)
        return version
    except Exception as e:
        logger.error(f"Error retrieving latest version for phase {phase_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.put("/versions/{version_id}", response_model=ScopingVersionResponse)
async def update_version(
    version_id: UUID = Path(..., description="Version ID"),
    version_data: ScopingVersionUpdate = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a scoping version.
    
    Updates version metadata, notes, and assessments. The version must be
    in a draft or rejected state to be updated.
    """
    try:
        service = ScopingService(db)
        version = await service.get_version(version_id)
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Version {version_id} not found"
            )
        
        if not version.can_be_edited:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Version {version_id} cannot be edited (status: {version.version_status})"
            )
        
        # Update version fields
        update_data = version_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(version, field):
                setattr(version, field, value)
        
        version.updated_by_id = current_user.user_id
        await db.commit()
        await db.refresh(version)
        
        return version
    except (ValidationError, BusinessLogicError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/versions/{version_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_version(
    version_id: UUID = Path(..., description="Version ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a scoping version.
    
    Deletes a version and all its associated attributes. Only draft versions
    can be deleted.
    """
    try:
        service = ScopingService(db)
        version = await service.get_version(version_id)
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Version {version_id} not found"
            )
        
        if not version.is_draft:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only draft versions can be deleted (current status: {version.version_status})"
            )
        
        await db.delete(version)
        await db.commit()
        
    except (ValidationError, BusinessLogicError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Attribute Management Endpoints
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


@router.get("/versions/{version_id}/attributes", response_model=List[ScopingAttributeResponse])
async def get_version_attributes(
    version_id: UUID = Path(..., description="Version ID"),
    limit: int = Query(100, ge=1, le=1000, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get attributes for a version.
    
    Retrieves all scoping attributes associated with a version.
    """
    try:
        service = ScopingService(db)
        version = await service.get_version_with_attributes(version_id)
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Version {version_id} not found"
            )
        
        # Apply pagination
        attributes = version.attributes[offset:offset + limit]
        return attributes
    except Exception as e:
        logger.error(f"Error retrieving attributes for version {version_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/attributes/{attribute_id}", response_model=ScopingAttributeResponse)
async def get_attribute(
    attribute_id: UUID = Path(..., description="Attribute ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific scoping attribute.
    
    Retrieves detailed information about a scoping attribute including
    all decisions and metadata.
    """
    try:
        attribute = await db.get(ScopingAttribute, attribute_id)
        if not attribute:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Attribute {attribute_id} not found"
            )
        return attribute
    except Exception as e:
        logger.error(f"Error retrieving attribute {attribute_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.put("/attributes/{attribute_id}", response_model=ScopingAttributeResponse)
async def update_attribute(
    attribute_id: UUID = Path(..., description="Attribute ID"),
    attribute_data: ScopingAttributeUpdate = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a scoping attribute.
    
    Updates attribute metadata, decisions, and other fields. The attribute's
    version must be in an editable state.
    """
    try:
        service = ScopingService(db)
        attribute = await db.get(ScopingAttribute, attribute_id)
        if not attribute:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Attribute {attribute_id} not found"
            )
        
        # Check if version can be edited
        version = await service.get_version(attribute.version_id)
        if not version.can_be_edited:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot update attribute in version with status {version.version_status}"
            )
        
        # Update attribute fields
        update_data = attribute_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(attribute, field):
                setattr(attribute, field, value)
        
        attribute.updated_by_id = current_user.user_id
        await db.commit()
        await db.refresh(attribute)
        
        return attribute
    except (ValidationError, BusinessLogicError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Decision Management Endpoints
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


@router.post("/versions/{version_id}/bulk-tester-decisions", response_model=BulkUpdateResponse)
async def make_bulk_tester_decisions(
    version_id: UUID = Path(..., description="Version ID"),
    decisions_data: BulkTesterDecisionCreate = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Make bulk tester decisions on multiple attributes.
    
    Allows testers to make decisions on multiple attributes in a single request
    for improved efficiency.
    """
    try:
        service = ScopingService(db)
        
        # Validate version exists and can be edited
        version = await service.get_version(version_id)
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Version {version_id} not found"
            )
        
        if not version.can_be_edited:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot make decisions on version with status {version.version_status}"
            )
        
        # Process decisions
        successful_updates = 0
        failed_updates = 0
        errors = []
        updated_attributes = []
        
        for decision in decisions_data.decisions:
            try:
                attribute = await service.make_tester_decision(
                    attribute_id=decision['attribute_id'],
                    decision=decision['decision'],
                    final_scoping=decision['final_scoping'],
                    rationale=decision.get('rationale'),
                    override_reason=decision.get('override_reason'),
                    user_id=current_user.user_id
                )
                successful_updates += 1
                updated_attributes.append(attribute.attribute_id)
            except Exception as e:
                failed_updates += 1
                errors.append({
                    'attribute_id': decision['attribute_id'],
                    'error': str(e)
                })
        
        return BulkUpdateResponse(
            total_requested=len(decisions_data.decisions),
            successful_updates=successful_updates,
            failed_updates=failed_updates,
            errors=errors,
            updated_attributes=updated_attributes
        )
    except (ValidationError, BusinessLogicError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Workflow Management Endpoints
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


# Statistics and Reporting Endpoints
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


@router.get("/attributes/{attribute_id}/decision-summary", response_model=AttributeDecisionSummary)
async def get_attribute_decision_summary(
    attribute_id: UUID = Path(..., description="Attribute ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive decision summary for an attribute.
    
    Returns detailed information about all decisions made on an attribute
    including timeline and accuracy metrics.
    """
    try:
        attribute = await db.get(ScopingAttribute, attribute_id)
        if not attribute:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Attribute {attribute_id} not found"
            )
        
        summary = attribute.get_decision_summary()
        return summary
    except Exception as e:
        logger.error(f"Error retrieving decision summary for attribute {attribute_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/planning-attributes/{planning_attribute_id}/decision-history", response_model=List[ScopingAttributeResponse])
async def get_attribute_decision_history(
    planning_attribute_id: int = Path(..., description="Planning attribute ID"),
    phase_id: int = Query(..., description="Phase ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get decision history for a planning attribute.
    
    Returns the history of scoping decisions for a planning attribute across
    all versions in a phase.
    """
    try:
        service = ScopingService(db)
        history = await service.get_attribute_decision_history(
            planning_attribute_id=planning_attribute_id,
            phase_id=phase_id
        )
        return history
    except Exception as e:
        logger.error(f"Error retrieving decision history for planning attribute {planning_attribute_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


# Utility Endpoints
@router.post("/versions/{version_id}/copy", response_model=ScopingVersionResponse, status_code=status.HTTP_201_CREATED)
async def copy_version(
    version_id: UUID = Path(..., description="Source version ID"),
    copy_data: VersionCopyCreate = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Copy an existing version.
    
    Creates a new version based on an existing one, optionally copying
    attributes and decisions.
    """
    try:
        service = ScopingService(db)
        new_version = await service.copy_version(
            source_version_id=copy_data.source_version_id,
            user_id=current_user.user_id,
            copy_attributes=copy_data.copy_attributes,
            copy_decisions=copy_data.copy_decisions
        )
        return new_version
    except (ValidationError, BusinessLogicError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/versions/{version_id}/bulk-update-attributes", response_model=BulkUpdateResponse)
async def bulk_update_attributes(
    version_id: UUID = Path(..., description="Version ID"),
    updates: List[Dict[str, Any]] = Body(..., description="List of attribute updates"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Bulk update multiple attributes.
    
    Allows updating multiple attributes in a single request for improved
    efficiency and transaction consistency.
    """
    try:
        service = ScopingService(db)
        updated_attributes = await service.bulk_update_attributes(
            version_id=version_id,
            updates=updates,
            user_id=current_user.user_id
        )
        
        return BulkUpdateResponse(
            total_requested=len(updates),
            successful_updates=len(updated_attributes),
            failed_updates=len(updates) - len(updated_attributes),
            errors=[],
            updated_attributes=[attr.attribute_id for attr in updated_attributes]
        )
    except (ValidationError, BusinessLogicError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


# Health check endpoint
@router.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring.
    
    Returns the health status of the scoping v2 API.
    """
    return {
        "status": "healthy",
        "service": "scoping-v2",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }