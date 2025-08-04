"""
Scoping API Endpoints - Consolidated Version Management System

This module provides REST API endpoints for the consolidated scoping system,
implementing comprehensive version and attribute management.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, and_, func
from uuid import UUID
from datetime import datetime
import logging
import uuid

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import (
    ValidationError, NotFoundError, ConflictError, 
    BusinessLogicError, PermissionError
)
from app.core.background_jobs import BackgroundJobManager
from app.core.permissions import require_permission
from app.models.user import User
from app.models.scoping import ScopingVersion, ScopingAttribute, VersionStatus, TesterDecision
from app.models.workflow import WorkflowPhase
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
    APIErrorResponse, LLMRecommendationCreate,
    
    # Legacy compatibility schemas
    LegacyScopingPhaseStatus,
    
    # Enums
    TesterDecision
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["scoping"])

# Helper functions for calculating metrics
async def _calculate_cdes_count(db: AsyncSession, phase_id: int) -> int:
    """Calculate number of CDEs in the phase"""
    from app.models.report_attribute import ReportAttribute
    
    query = await db.execute(
        select(func.count()).select_from(ReportAttribute)
        .where(
            and_(
                ReportAttribute.phase_id == phase_id,
                ReportAttribute.is_cde == True
            )
        )
    )
    return query.scalar() or 0

async def _calculate_historical_issues(db: AsyncSession, phase_id: int) -> int:
    """Calculate number of attributes with historical issues"""
    from app.models.report_attribute import ReportAttribute
    
    query = await db.execute(
        select(func.count()).select_from(ReportAttribute)
        .where(
            and_(
                ReportAttribute.phase_id == phase_id,
                ReportAttribute.has_issues == True
            )
        )
    )
    return query.scalar() or 0

async def _calculate_attributes_with_anomalies_scoping(db: AsyncSession, cycle_id: int, report_id: int) -> int:
    """Calculate number of attributes with anomalies from data profiling phase"""
    from app.models.data_profiling import ProfilingResult
    
    # Get data profiling phase
    profiling_phase_query = await db.execute(
        select(WorkflowPhase.phase_id).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == "Data Profiling"
            )
        )
    )
    profiling_phase_id = profiling_phase_query.scalar_one_or_none()
    
    if not profiling_phase_id:
        return 0
    
    query = await db.execute(
        select(func.count(func.distinct(ProfilingResult.attribute_id)))
        .where(
            and_(
                ProfilingResult.phase_id == profiling_phase_id,
                ProfilingResult.has_anomaly == True
            )
        )
    )
    return query.scalar() or 0


# Version Management Endpoints
@router.post("/versions", response_model=ScopingVersionResponse, status_code=status.HTTP_201_CREATED)
async def create_version(
    version_data: ScopingVersionCreate,
    db: AsyncSession = Depends(get_db),
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
    db: AsyncSession = Depends(get_db),
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
    db: AsyncSession = Depends(get_db),
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
    db: AsyncSession = Depends(get_db),
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
    db: AsyncSession = Depends(get_db),
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
    db: AsyncSession = Depends(get_db),
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


@router.post("/versions/{version_id}/submit")
async def submit_version_for_approval(
    version_id: UUID = Path(..., description="Version ID"),
    submission_data: VersionSubmissionCreate = Body(...),
    db: AsyncSession = Depends(get_db),
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
    db: AsyncSession = Depends(get_db),
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


@router.post("/versions/{version_id}/reject")
async def reject_version(
    version_id: UUID = Path(..., description="Version ID"),
    rejection_data: VersionRejectionCreate = Body(...),
    db: AsyncSession = Depends(get_db),
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
    except Exception as e:
        logger.error(f"Unexpected error rejecting version {version_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/versions/{version_id}/attributes", response_model=List[ScopingAttributeResponse])
async def get_version_attributes(
    version_id: UUID = Path(..., description="Version ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all attributes for a specific version.
    
    Returns all scoping attributes associated with the specified version,
    including their decisions and feedback, along with planning attribute details.
    """
    try:
        service = ScopingService(db)
        attributes = await service.get_version_attributes_with_planning_details(version_id)
        
        if not attributes:
            # Check if version exists
            version = await service.get_version(version_id)
            if not version:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Version {version_id} not found")
        
        return attributes
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting version attributes: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/versions/{version_id}/statistics", response_model=VersionStatistics)
async def get_version_statistics(
    version_id: UUID = Path(..., description="Version ID"),
    db: AsyncSession = Depends(get_db),
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


@router.post("/cycles/{cycle_id}/reports/{report_id}/resubmit-after-feedback")
async def resubmit_after_feedback(
    cycle_id: int,
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new scoping version when tester resubmits after report owner feedback.
    This allows the tester to update decisions based on report owner feedback.
    """
    try:
        # Get phase_id
        phase_query = await db.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Scoping"
                )
            )
        )
        phase = phase_query.scalar_one_or_none()
        if not phase:
            raise HTTPException(status_code=404, detail="Scoping phase not found")
        
        # Get latest version
        latest_version_query = await db.execute(
            select(ScopingVersion)
            .where(ScopingVersion.phase_id == phase.phase_id)
            .order_by(ScopingVersion.version_number.desc())
            .limit(1)
        )
        latest_version = latest_version_query.scalar_one_or_none()
        
        if not latest_version:
            raise HTTPException(status_code=404, detail="No scoping version found")
        
        # Check if there's report owner feedback on ANY version in this phase
        # This allows resubmission based on feedback from previous versions
        from sqlalchemy import func
        feedback_check_query = await db.execute(
            select(func.count(ScopingAttribute.attribute_id))
            .join(ScopingVersion, ScopingAttribute.version_id == ScopingVersion.version_id)
            .where(
                and_(
                    ScopingVersion.phase_id == phase.phase_id,
                    ScopingAttribute.report_owner_decision.isnot(None)
                )
            )
        )
        feedback_count = feedback_check_query.scalar() or 0
        
        if feedback_count == 0:
            raise HTTPException(
                status_code=400, 
                detail="No report owner feedback found. Resubmission is only allowed after receiving feedback."
            )
        
        # Check if there are any rejected or needs_revision decisions across all versions
        # These are the decisions that warrant resubmission
        rejected_feedback_query = await db.execute(
            select(func.count(ScopingAttribute.attribute_id))
            .join(ScopingVersion, ScopingAttribute.version_id == ScopingVersion.version_id)
            .where(
                and_(
                    ScopingVersion.phase_id == phase.phase_id,
                    ScopingAttribute.report_owner_decision.in_(["rejected", "needs_revision"])
                )
            )
        )
        rejected_count = rejected_feedback_query.scalar() or 0
        
        # Only allow resubmission if there are rejected/needs_revision decisions
        if rejected_count == 0:
            raise HTTPException(
                status_code=400,
                detail="No rejected attributes found. Resubmission is only needed for rejected feedback."
            )
        
        # Find the version with report owner feedback to use as baseline
        feedback_version_query = await db.execute(
            select(ScopingVersion)
            .join(ScopingAttribute, ScopingAttribute.version_id == ScopingVersion.version_id)
            .where(
                and_(
                    ScopingVersion.phase_id == phase.phase_id,
                    ScopingAttribute.report_owner_decision.isnot(None)
                )
            )
            .order_by(ScopingVersion.version_number.desc())
            .limit(1)
        )
        feedback_version = feedback_version_query.scalar_one_or_none()
        
        if not feedback_version:
            raise HTTPException(
                status_code=400,
                detail="Could not find version with report owner feedback to use as baseline."
            )
        
        # Create new version using the version with feedback as the baseline
        service = ScopingService(db)
        new_version = await service.create_version_from_feedback(
            phase_id=phase.phase_id,
            parent_version_id=feedback_version.version_id,  # Use feedback version as baseline
            user_id=current_user.user_id
        )
        
        await db.flush()
        
        # Create Universal Assignment for report owner to review the resubmitted version
        # Create universal assignment for report owner
        from app.services.universal_assignment_service import UniversalAssignmentService
        from app.models.report import Report
        from datetime import timedelta
        
        assignment_service = UniversalAssignmentService(db)
        
        # Get report and cycle info for context
        from app.models.test_cycle import TestCycle
        report_query = await db.execute(
            select(Report).where(Report.report_id == report_id)
        )
        report = report_query.scalar_one_or_none()
        if not report or not report.report_owner_id:
            raise HTTPException(status_code=404, detail="Report or report owner not found")
        
        cycle_query = await db.execute(
            select(TestCycle).where(TestCycle.cycle_id == cycle_id)
        )
        cycle = cycle_query.scalar_one_or_none()
        
        # Create assignment
        assignment = await assignment_service.create_assignment(
            assignment_type="Scoping Approval",
            from_role=current_user.role,
            to_role="Report Owner",
            from_user_id=current_user.user_id,
            to_user_id=report.report_owner_id,
            title="Review Updated Scoping Decisions",
            description=f"Review updated scoping decisions (Version {new_version.version_number}) that have been revised based on your feedback for {report.report_name} in {cycle.cycle_name if cycle else f'cycle {cycle_id}'}.",
            task_instructions="The tester has updated the scoping decisions based on your previous feedback. Please review the revised decisions and approve or provide additional feedback.",
            context_type="Report",
            context_data={
                "cycle_id": cycle_id,
                "report_id": report_id,
                "report_name": report.report_name,
                "cycle_name": cycle.cycle_name if cycle else None,
                "phase": "scoping",
                "phase_name": "Scoping",
                "phase_id": phase.phase_id,
                "version_id": str(new_version.version_id),
                "version_number": new_version.version_number,
                "workflow_step": "tester_updated_scoping_for_report_owner_review",
                "is_resubmission": True
            },
            priority="High",
            due_date=datetime.utcnow() + timedelta(days=5),  # Shorter deadline for resubmission
            requires_approval=False
        )
        
        await db.commit()
        await db.refresh(new_version)
        
        return {
            "message": "New version created successfully for resubmission",
            "version_id": new_version.version_id,
            "version_number": new_version.version_number,
            "status": new_version.version_status,
            "attributes_with_feedback": feedback_count,
            "attributes_needing_update": rejected_count,
            "assignment_id": assignment.assignment_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in resubmit_after_feedback: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/versions/{version_id}/copy", response_model=ScopingVersionResponse)
async def copy_version(
    version_id: UUID = Path(..., description="Source version ID"),
    copy_data: VersionCopyCreate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a copy of an existing version.
    
    Copies a version with optional attribute and decision copying.
    """
    try:
        service = ScopingService(db)
        new_version = await service.copy_version(
            source_version_id=version_id,
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


@router.post("/versions/{version_id}/generate-recommendations")
async def generate_scoping_recommendations(
    version_id: UUID = Path(..., description="Version ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate LLM recommendations for all attributes in a scoping version.
    
    This endpoint initiates a background job to generate LLM recommendations
    for all planning attributes that don't already have recommendations.
    """
    try:
        service = ScopingService(db)
        
        # Get the version to validate it exists and is editable
        version = await service.get_version(version_id)
        if not version:
            raise NotFoundError(f"Version {version_id} not found")
        
        if version.version_status != VersionStatus.DRAFT:
            raise BusinessLogicError("Recommendations can only be generated for draft versions")
        
        # Get planning attributes for this phase
        from app.models.report_attribute import ReportAttribute
        from app.models.workflow import WorkflowPhase
        
        phase_query = select(WorkflowPhase).where(
            WorkflowPhase.phase_id == version.phase_id
        )
        phase_result = await db.execute(phase_query)
        phase = phase_result.scalar_one_or_none()
        
        if not phase:
            raise NotFoundError("Phase not found")
        
        # Get all planning attributes for this report
        planning_attrs_query = select(ReportAttribute).join(WorkflowPhase).where(
            and_(
                WorkflowPhase.report_id == phase.report_id,
                WorkflowPhase.cycle_id == phase.cycle_id,
                WorkflowPhase.phase_name == "Planning"
            )
        ).order_by(ReportAttribute.line_item_number)
        
        planning_attrs_result = await db.execute(planning_attrs_query)
        planning_attributes = planning_attrs_result.scalars().all()
        
        if not planning_attributes:
            raise BusinessLogicError("No planning attributes found. Please complete the planning phase first.")
        
        # Get existing scoping attributes to identify which need recommendations
        existing_attrs_query = select(ScopingAttribute.planning_attribute_id).where(
            ScopingAttribute.version_id == version_id
        )
        existing_attrs_result = await db.execute(existing_attrs_query)
        existing_attr_ids = set(row[0] for row in existing_attrs_result.fetchall())
        
        # Prepare attributes that need recommendations
        attributes_to_process = []
        for attr in planning_attributes:
            if attr.id not in existing_attr_ids:
                attributes_to_process.append({
                    "id": attr.id,
                    "attribute_name": attr.attribute_name,
                    "description": attr.description,
                    "data_type": attr.data_type,
                    "line_item_number": attr.line_item_number,
                    "mdrm_code": attr.mdrm,  # Add MDRM code
                    "is_cde": attr.is_cde,  # Add CDE flag
                    "is_primary_key": attr.is_primary_key,  # Add primary key flag
                    "is_required": attr.is_required,
                    "has_historical_issues": False  # Default to False, would need to check profiling results for actual value
                })
        
        if not attributes_to_process:
            return {
                "message": "All attributes already have recommendations",
                "job_id": None,
                "attributes_count": 0
            }
        
        # Get report and cycle information for context
        from app.models.report import Report
        from app.models.cycle import Cycle
        
        report_query = select(Report).where(Report.id == phase.report_id)
        report_result = await db.execute(report_query)
        report = report_result.scalar_one_or_none()
        
        cycle_query = select(Cycle).where(Cycle.id == phase.cycle_id)
        cycle_result = await db.execute(cycle_query)
        cycle = cycle_result.scalar_one_or_none()
        
        # Start background job for LLM recommendations
        job_manager = BackgroundJobManager()
        job_id = str(uuid.uuid4())
        
        # Create progress tracker
        progress = job_manager.create_job(job_id, "scoping_llm_recommendations")
        progress.total_steps = len(attributes_to_process)
        progress.message = f"Starting LLM recommendation generation for {len(attributes_to_process)} attributes..."
        progress.metadata = {
            "version_id": str(version_id),
            "phase_id": version.phase_id,
            "cycle_id": phase.cycle_id,
            "report_id": phase.report_id,
            "total_attributes": len(attributes_to_process)
        }
        
        # Use the correct threading approach from the legacy function
        from app.tasks.scoping_tasks import _generate_scoping_recommendations_async
        import threading
        import asyncio
        
        # Prepare context data for async function
        cycle_context = {"cycle_id": phase.cycle_id, "cycle_name": cycle.name if cycle else ""}
        report_context = {"report_id": phase.report_id, "report_name": report.report_name if report else ""}
        
        def run_in_background():
            try:
                # Create new event loop for this thread
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                
                # Run the async task function
                new_loop.run_until_complete(
                    _generate_scoping_recommendations_async(
                        job_id=job_id,
                        cycle_id=phase.cycle_id,
                        report_id=phase.report_id,
                        phase_id=version.phase_id,
                        version_id=version_id,
                        user_id=current_user.user_id,
                        attributes_to_process=attributes_to_process,
                        report_context=report_context,
                        cycle_context=cycle_context
                    )
                )
                new_loop.close()
            except Exception as e:
                logger.error(f"Background task failed: {str(e)}")
                job_manager.update_job_progress(
                    job_id,
                    status="failed",
                    error=str(e),
                    message=f"Failed to generate recommendations: {str(e)}"
                )
        
        # Start the background thread
        thread = threading.Thread(target=run_in_background, daemon=True)
        thread.start()
        
        logger.info(f"Started LLM recommendation generation job {job_id} for version {version_id}")
        
        return {
            "message": f"Started LLM recommendation generation for {len(attributes_to_process)} attributes",
            "job_id": job_id,
            "attributes_count": len(attributes_to_process),
            "estimated_time_minutes": max(1, len(attributes_to_process) // 10)  # Rough estimate
        }
        
    except (ValidationError, BusinessLogicError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating scoping recommendations: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/phases/{phase_id}/versions", response_model=List[ScopingVersionSummary])
async def get_phase_versions(
    phase_id: int = Path(..., description="Phase ID"),
    limit: int = Query(10, ge=1, le=100, description="Number of versions to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    include_attributes: bool = Query(False, description="Include attributes in response"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all versions for a phase.
    
    Returns a list of versions ordered by version number (newest first).
    """
    try:
        service = ScopingService(db)
        versions = await service.get_phase_versions(
            phase_id=phase_id,
            limit=limit,
            offset=offset,
            include_attributes=include_attributes
        )
        return versions
    except Exception as e:
        logger.error(f"Error retrieving versions for phase {phase_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/phases/{phase_id}/versions/history")
async def get_version_history(
    phase_id: int = Path(..., description="Phase ID"),
    status: Optional[List[str]] = Query(None, description="Filter by version status"),
    include_statistics: bool = Query(True, description="Include summary statistics"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get complete version history for a phase with filtering.
    
    Returns all versions for a phase with optional status filtering.
    Supports filtering by multiple statuses (e.g., ?status=approved&status=draft).
    """
    try:
        logger.info(f"Getting version history for phase {phase_id}")
        service = ScopingService(db)
        
        # Convert status strings to enums if provided
        status_filter = None
        if status:
            try:
                status_filter = [VersionStatus(s) for s in status]
            except Exception as e:
                logger.error(f"Error converting status filter: {e}")
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        versions = await service.get_version_history(
            phase_id=phase_id,
            status_filter=status_filter,
            include_statistics=include_statistics
        )
        
        # Return raw data for debugging
        return [
            {
                "version_id": str(version.version_id),
                "phase_id": version.phase_id,
                "version_number": version.version_number,
                "version_status": version.version_status.value if hasattr(version.version_status, 'value') else str(version.version_status),
                "total_attributes": version.total_attributes or 0,
                "created_at": version.created_at.isoformat() if version.created_at else None,
            }
            for version in versions
        ]
        
    except Exception as e:
        logger.error(f"Error retrieving version history for phase {phase_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/phases/{phase_id}/versions/approved", response_model=List[ScopingVersionResponse])
async def get_approved_versions(
    phase_id: int = Path(..., description="Phase ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get only approved versions for a phase.
    
    Returns approved versions ordered by version number descending.
    """
    try:
        service = ScopingService(db)
        versions = await service.get_approved_versions(phase_id)
        
        return [
            ScopingVersionResponse(
                version_id=str(version.version_id),
                phase_id=version.phase_id,
                version_number=version.version_number,
                version_status=version.version_status,
                total_attributes=version.total_attributes or 0,
                scoped_attributes=version.scoped_attributes or 0,
                declined_attributes=version.declined_attributes or 0,
                override_count=version.override_count or 0,
                cde_count=version.cde_count or 0,
                created_at=version.created_at,
                created_by_id=version.created_by_id,
                updated_at=version.updated_at,
                updated_by_id=version.updated_by_id,
            )
            for version in versions
        ]
        
    except Exception as e:
        logger.error(f"Error retrieving approved versions for phase {phase_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/phases/{phase_id}/versions/latest", response_model=Optional[ScopingVersionResponse])
async def get_latest_version(
    phase_id: int = Path(..., description="Phase ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the latest version for a phase.
    
    Returns the version with the highest version number regardless of status.
    """
    try:
        service = ScopingService(db)
        version = await service.get_latest_version(phase_id)
        
        if not version:
            return None
            
        return ScopingVersionResponse(
            version_id=str(version.version_id),
            phase_id=version.phase_id,
            version_number=version.version_number,
            version_status=version.version_status,
            total_attributes=version.total_attributes or 0,
            scoped_attributes=version.scoped_attributes or 0,
            declined_attributes=version.declined_attributes or 0,
            override_count=version.override_count or 0,
            cde_count=version.cde_count or 0,
            created_at=version.created_at,
            created_by_id=version.created_by_id,
            updated_at=version.updated_at,
            updated_by_id=version.updated_by_id,
        )
        
    except Exception as e:
        logger.error(f"Error retrieving latest version for phase {phase_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/attributes/{attribute_id}/history", response_model=List[ScopingAttributeResponse])
async def get_attribute_decision_history(
    attribute_id: int = Path(..., description="Planning attribute ID"),
    phase_id: int = Query(..., description="Phase ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get decision history for an attribute across all versions.
    
    Returns the decision history for a planning attribute across all versions
    in a phase, ordered by creation date (newest first).
    """
    try:
        service = ScopingService(db)
        history = await service.get_attribute_decision_history(
            planning_attribute_id=attribute_id,
            phase_id=phase_id
        )
        return history
    except Exception as e:
        logger.error(f"Error retrieving decision history for attribute {attribute_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/versions/{version_id}/bulk-update", response_model=BulkUpdateResponse)
async def bulk_update_attributes(
    version_id: UUID = Path(..., description="Version ID"),
    updates: List[Dict[str, Any]] = Body(..., description="List of attribute updates"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Bulk update multiple attributes in a version.
    
    Updates multiple attributes with their decisions and metadata.
    """
    try:
        service = ScopingService(db)
        updated_attributes = await service.bulk_update_attributes(
            version_id=version_id,
            updates=updates,
            user_id=current_user.user_id
        )
        
        return BulkUpdateResponse(
            updated_count=len(updated_attributes),
            updated_attributes=[attr.attribute_id for attr in updated_attributes]
        )
    except (ValidationError, BusinessLogicError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/attributes/bulk-approve")
async def bulk_approve_attributes(
    request: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Bulk approve multiple scoping attributes.
    Automatically determines whether to apply tester or report owner decision based on user role.
    
    Request body:
    {
        "attribute_ids": ["uuid1", "uuid2", ...],
        "notes": "Optional approval notes"
    }
    """
    try:
        attribute_ids = [UUID(id_str) for id_str in request.get("attribute_ids", [])]
        notes = request.get("notes")
        
        service = ScopingService(db)
        result = await service.bulk_approve_attributes(
            attribute_ids=attribute_ids,
            user_id=current_user.user_id,
            user_role=current_user.role,
            notes=notes
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid attribute ID format")
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error in bulk approve: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/attributes/bulk-reject")
async def bulk_reject_attributes(
    request: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Bulk reject multiple scoping attributes.
    Automatically determines whether to apply tester or report owner decision based on user role.
    
    Request body:
    {
        "attribute_ids": ["uuid1", "uuid2", ...],
        "reason": "Reason for rejection",
        "notes": "Optional additional notes"
    }
    """
    try:
        attribute_ids = [UUID(id_str) for id_str in request.get("attribute_ids", [])]
        reason = request.get("reason")
        notes = request.get("notes")
        
        if not reason:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reason is required for rejection")
        
        service = ScopingService(db)
        result = await service.bulk_reject_attributes(
            attribute_ids=attribute_ids,
            user_id=current_user.user_id,
            user_role=current_user.role,
            reason=reason,
            notes=notes
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid attribute ID format")
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error in bulk reject: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


# Note: Report owner bulk approve is now handled automatically in the regular bulk-approve endpoint
# based on user role. This eliminates the need for a separate endpoint.


# Legacy endpoints for backward compatibility
@router.get("/cycles/{cycle_id}/reports/{report_id}/status", response_model=LegacyScopingPhaseStatus)
async def get_scoping_status_legacy(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Legacy endpoint for backward compatibility with existing frontend"""
    try:
        # Get the phase for this cycle/report
        from app.models.workflow import WorkflowPhase
        from sqlalchemy import select
        
        phase_query = select(WorkflowPhase).where(
            WorkflowPhase.cycle_id == cycle_id,
            WorkflowPhase.report_id == report_id,
            WorkflowPhase.phase_name == "Scoping"
        ).limit(1)
        phase_result_obj = await db.execute(phase_query)
        phase_result = phase_result_obj.scalar_one_or_none()
        
        if not phase_result:
            return LegacyScopingPhaseStatus(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_status="Not Started",
                total_attributes=0,
                attributes_with_recommendations=0,
                attributes_with_decisions=0,
                attributes_scoped_for_testing=0,
                submission_status="Not Submitted",
                can_generate_recommendations=False,
                can_submit_for_approval=False,
                can_complete_phase=False,
                completion_requirements=["Phase not started"],
                has_submission=False
            )
        
        service = ScopingService(db)
        current_version = await service.get_current_version(phase_result.phase_id)
        
        # Build legacy response from current version
        if current_version:
            statistics = await service.get_version_statistics(UUID(current_version["version_id"]))
            
            # Check if version has been submitted
            has_submission = current_version.get("submitted_at") is not None or current_version["version_status"] != "draft"
            
            # Calculate additional metrics
            cdes_count = await _calculate_cdes_count(db, phase_result.phase_id)
            historical_issues_count = await _calculate_historical_issues(db, phase_result.phase_id)
            attributes_with_anomalies = await _calculate_attributes_with_anomalies_scoping(db, cycle_id, report_id)
            from datetime import timezone
            days_elapsed = (datetime.now(timezone.utc) - phase_result.created_at).days if phase_result.created_at else 0
            
            return LegacyScopingPhaseStatus(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_status=phase_result.status.value if hasattr(phase_result.status, 'value') else phase_result.status,
                total_attributes=statistics["total_attributes"],
                attributes_with_recommendations=statistics["total_attributes"],  # All have recommendations in new system
                attributes_with_decisions=statistics["decision_progress"]["completed_decisions"],
                attributes_scoped_for_testing=statistics["scoped_attributes"],
                submission_status=current_version["version_status"],
                can_generate_recommendations=current_version["can_be_edited"],
                can_submit_for_approval=current_version["can_be_submitted"],
                can_complete_phase=current_version["version_status"] == "approved",
                completion_requirements=[],
                has_submission=has_submission,  # Add this field
                cdes_count=cdes_count,
                historical_issues_count=historical_issues_count,
                attributes_with_anomalies=attributes_with_anomalies,
                days_elapsed=days_elapsed
            )
        else:
            return LegacyScopingPhaseStatus(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_status=phase_result.status.value if hasattr(phase_result.status, 'value') else phase_result.status,
                total_attributes=0,
                attributes_with_recommendations=0,
                attributes_with_decisions=0,
                attributes_scoped_for_testing=0,
                submission_status="Not Submitted",
                can_generate_recommendations=True,
                can_submit_for_approval=False,
                can_complete_phase=False,
                completion_requirements=["Create scoping version"],
                has_submission=False
            )
    except Exception as e:
        import traceback
        logger.error(f"Error retrieving legacy scoping status: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/cycles/{cycle_id}/reports/{report_id}/current-version")
async def get_current_version_legacy(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Legacy endpoint for backward compatibility"""
    try:
        # Get the phase for this cycle/report
        from app.models.workflow import WorkflowPhase
        from sqlalchemy import select
        
        phase_query = select(WorkflowPhase).where(
            WorkflowPhase.cycle_id == cycle_id,
            WorkflowPhase.report_id == report_id,
            WorkflowPhase.phase_name == "Scoping"
        ).limit(1)
        phase_result_obj = await db.execute(phase_query)
        phase_result = phase_result_obj.scalar_one_or_none()
        
        if not phase_result:
            raise HTTPException(status_code=404, detail="Scoping phase not found")
        
        service = ScopingService(db)
        version = await service.get_current_version(phase_result.phase_id)
        return version
    except Exception as e:
        logger.error(f"Error retrieving current version for cycle {cycle_id}, report {report_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


# Missing legacy endpoints for frontend compatibility
@router.get("/cycles/{cycle_id}/reports/{report_id}/recommendations")
async def get_scoping_recommendations_legacy(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Legacy endpoint for scoping recommendations"""
    try:
        # Return empty recommendations for now
        return {"recommendations": []}
    except Exception as e:
        logger.error(f"Error retrieving scoping recommendations: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/cycles/{cycle_id}/reports/{report_id}/recommendations")
async def generate_scoping_recommendations_legacy(
    cycle_id: int,
    report_id: int,
    request_data: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate scoping recommendations using background job manager.
    
    Supports:
    - Incremental generation (only attributes without recommendations)
    - Force regeneration for all attributes
    - Force regeneration for specific attributes
    
    Request body:
    {
        "force_regenerate": false,  # Optional: regenerate all even if they have recommendations
        "attribute_ids": ["uuid1", "uuid2"],  # Optional: specific attributes to regenerate
        "batch_size": 6  # Optional: number of attributes per batch (default: 6)
    }
    """
    try:
        from app.core.background_jobs import job_manager
        from app.models.workflow import WorkflowPhase
        from app.models.report import Report
        from app.models.test_cycle import TestCycle
        from app.services.llm_service import get_llm_service
        import asyncio
        
        # Check if there's already an active job for this cycle/report
        active_jobs = job_manager.get_active_jobs()
        for job in active_jobs:
            if (job.get('metadata', {}).get('cycle_id') == cycle_id and 
                job.get('metadata', {}).get('report_id') == report_id and
                job.get('job_type') == 'scoping_recommendations'):
                # If job is stuck in pending for more than 5 minutes, cancel it
                created_at = job.get('created_at')
                if created_at and isinstance(created_at, str):
                    from datetime import datetime, timedelta
                    job_created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    if datetime.utcnow() - job_created.replace(tzinfo=None) > timedelta(minutes=5):
                        job_manager.complete_job(job.get('job_id'), error="Job timeout - stuck in pending")
                        continue
                
                return {
                    "message": "Recommendation generation already in progress",
                    "job_id": job.get('job_id'),
                    "status": "in_progress"
                }
        
        # Get scoping phase
        phase_query = select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == "Scoping"
            )
        )
        phase_result = await db.execute(phase_query)
        phase = phase_result.scalar_one_or_none()
        
        if not phase:
            raise HTTPException(status_code=404, detail="Scoping phase not found")
        
        # Get planning phase to find attributes
        planning_phase_query = select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == "Planning"
            )
        )
        planning_phase_result = await db.execute(planning_phase_query)
        planning_phase = planning_phase_result.scalar_one_or_none()
        
        if not planning_phase:
            raise HTTPException(status_code=400, detail="Planning phase not found. Please complete planning first.")
        
        # Get approved planning attributes
        from app.models.report_attribute import ReportAttribute
        attrs_query = select(ReportAttribute).where(
            and_(
                ReportAttribute.phase_id == planning_phase.phase_id,
                ReportAttribute.approval_status == "approved",
                ReportAttribute.is_active == True
            )
        ).order_by(ReportAttribute.line_item_number)
        
        attrs_result = await db.execute(attrs_query)
        attributes = attrs_result.scalars().all()
        
        if not attributes:
            return {
                "message": "No approved attributes found in planning phase",
                "job_id": None,
                "status": "error"
            }
        
        # Extract request parameters
        force_regenerate = request_data.get("force_regenerate", False)
        specific_attribute_ids = request_data.get("attribute_ids", [])
        batch_size = request_data.get("batch_size", 6)
        
        # Check if we already have a current version with recommendations
        service = ScopingService(db)
        current_version = await service.get_current_version(phase.phase_id)
        
        # Create a new version if none exists
        if not current_version:
            new_version = await service.create_version(
                phase_id=phase.phase_id,
                user_id=current_user.user_id,
                notes="Created for LLM recommendations"
            )
            version_id = new_version.version_id
        else:
            # Use existing draft version or create new one
            latest_version = await service.get_latest_version(phase.phase_id)
            if latest_version and latest_version.version_status == VersionStatus.DRAFT:
                version_id = latest_version.version_id
            else:
                new_version = await service.create_version(
                    phase_id=phase.phase_id,
                    user_id=current_user.user_id,
                    notes="Created for new LLM recommendations"
                )
                version_id = new_version.version_id
        
        # Get existing scoping attributes for this version if not forcing regeneration
        existing_recommendations = {}
        existing_scoping_attrs = {}
        if version_id:
            from app.models.scoping import ScopingAttribute
            existing_query = select(ScopingAttribute).where(
                ScopingAttribute.version_id == version_id
            )
            existing_result = await db.execute(existing_query)
            existing_attrs = existing_result.scalars().all()
            
            # Build map of planning_attribute_id -> has_recommendation
            for scoping_attr in existing_attrs:
                attr_id = scoping_attr.planning_attribute_id  # This is an integer
                existing_scoping_attrs[attr_id] = scoping_attr
                # Only mark as having recommendation if not forcing regeneration and it actually has one
                if not force_regenerate and scoping_attr.llm_recommendation:
                    existing_recommendations[attr_id] = True
        
        # Prepare attributes for LLM processing
        attributes_to_process = []
        for attr in attributes:
            attr_id = attr.id  # This is already an integer
            
            # Skip if we have a recommendation and not forcing regeneration
            if not force_regenerate and attr_id in existing_recommendations:
                # Skip if specific attributes requested and this isn't one of them
                if specific_attribute_ids and str(attr_id) not in specific_attribute_ids:
                    continue
                # Skip if no specific attributes requested (general incremental update)
                elif not specific_attribute_ids:
                    continue
            
            # Skip if specific attributes requested and this isn't one of them
            if specific_attribute_ids and str(attr_id) not in specific_attribute_ids:
                continue
            
            attributes_to_process.append({
                "id": str(attr.id),  # Use string version of integer ID for consistency
                "attribute_id": attr.id,  # Keep the actual integer ID for database operations
                "attribute_name": attr.attribute_name,
                "description": attr.description,
                "data_type": attr.data_type,
                "line_item_number": attr.line_item_number,
                "mdrm_code": attr.mdrm,  # Add MDRM code
                "is_required": getattr(attr, 'is_required', False),
                "is_cde": attr.cde_flag,
                "is_primary_key": attr.is_primary_key,
                "has_historical_issues": attr.historical_issues_flag
            })
        
        # Check if we have any attributes to process
        if not attributes_to_process:
            return {
                "message": "All attributes already have recommendations. Use force_regenerate=true to regenerate.",
                "job_id": None,
                "status": "no_action_needed",
                "total_attributes": len(attributes),
                "attributes_with_recommendations": len(existing_recommendations)
            }
        
        # Get report and cycle info
        report_query = select(Report).where(Report.report_id == report_id)
        report_result = await db.execute(report_query)
        report = report_result.scalar_one_or_none()
        
        cycle_query = select(TestCycle).where(TestCycle.cycle_id == cycle_id)
        cycle_result = await db.execute(cycle_query)
        cycle = cycle_result.scalar_one_or_none()
        
        # Create background job
        job_id = job_manager.create_job("scoping_recommendations", {
            "cycle_id": cycle_id,
            "report_id": report_id,
            "user_id": current_user.user_id,
            "cycle_name": cycle.cycle_name if cycle else f"Cycle {cycle_id}",
            "report_name": report.report_name if report else f"Report {report_id}",
            "phase": "Scoping",
            "version_id": str(version_id),
            "total_attributes": len(attributes_to_process)
        })
        
        # Update initial progress
        job_manager.update_job_progress(
            job_id,
            total_steps=len(attributes_to_process),
            message="Starting LLM recommendation generation..."
        )
        
        # Capture necessary variables for async function
        user_id = current_user.user_id
        report_name = report.report_name if report else None
        
        async def run_scoping_recommendations():
            try:
                logger.info(f"🚀 Started scoping recommendations for job {job_id}")
                # Get a new database session for the background task
                from app.core.database import AsyncSessionLocal
                async with AsyncSessionLocal() as task_db:
                    # Start the job - update status to running
                    job_manager.update_job_progress(
                        job_id,
                        status="running",
                        current_step="Starting recommendation generation",
                        progress_percentage=0,
                        message="Initializing LLM service..."
                    )
                    
                    # Get LLM service
                    llm_service = get_llm_service()
                    
                    # Get service with task db session
                    service = ScopingService(task_db)
                    
                    # Process attributes in batches
                    all_recommendations = []
                    total_batches = (len(attributes_to_process) + batch_size - 1) // batch_size
                    updated_count = 0
                    
                    for batch_num, i in enumerate(range(0, len(attributes_to_process), batch_size)):
                        batch = attributes_to_process[i:i + batch_size]
                        
                        # Update job progress
                        job_manager.update_job_progress(
                            job_id,
                            progress_percentage=int((batch_num / total_batches) * 80),
                            current_step=f"Processing batch {batch_num + 1} of {total_batches}",
                            message=f"Generating recommendations for {len(batch)} attributes..."
                        )
                        
                        # Log what we're sending
                        logger.info(f"Sending batch {batch_num + 1} with {len(batch)} attributes to LLM")
                        if batch and logger.isEnabledFor(logging.DEBUG):
                            logger.debug(f"First attribute in batch: id={batch[0].get('id')}, attribute_id={batch[0].get('attribute_id')}, name={batch[0].get('attribute_name')}")
                        
                        # Generate recommendations for this batch
                        result = await llm_service.generate_scoping_recommendations(
                            attributes=batch,
                            report_type=report_name
                        )
                        
                        batch_recommendations = result.get("recommendations", [])
                        all_recommendations.extend(batch_recommendations)
                        
                        logger.info(f"Received {len(batch_recommendations)} recommendations from LLM for batch {batch_num + 1}")
                        if batch_recommendations and logger.isEnabledFor(logging.DEBUG):
                            logger.debug(f"First recommendation structure: {batch_recommendations[0] if batch_recommendations else 'None'}")
                        
                        # Save recommendations incrementally after each batch
                        if batch_recommendations:
                            planning_attr_ids = []
                            llm_recommendations = []
                            
                            for rec in batch_recommendations:
                                # Try to match by attribute_id first, then by attribute_name
                                attr_id = None
                                
                                # First try to match by attribute_id if present
                                if rec.get("attribute_id"):
                                    for orig_attr in attributes_to_process:
                                        # Handle both string and int comparisons
                                        if str(orig_attr["id"]) == str(rec["attribute_id"]) or orig_attr["attribute_id"] == rec.get("attribute_id"):
                                            attr_id = orig_attr["attribute_id"]
                                            break
                                
                                # If no match by ID, try to match by attribute_name
                                if not attr_id and rec.get("attribute_name"):
                                    for orig_attr in attributes_to_process:
                                        if orig_attr["attribute_name"] == rec["attribute_name"]:
                                            attr_id = orig_attr["attribute_id"]
                                            break
                                
                                # Log if we couldn't find a match
                                if not attr_id:
                                    logger.warning(f"Could not match LLM recommendation for attribute: {rec.get('attribute_name', 'Unknown')} (id: {rec.get('attribute_id', 'None')})")
                                    continue
                                    
                                if attr_id:
                                        planning_attr_ids.append(attr_id)
                                        llm_recommendations.append({
                                        "recommendation": rec.get("recommendation", "include"),
                                        "confidence_score": rec.get("confidence_score", 0.8),
                                        "rationale": rec.get("rationale", ""),
                                        "provider": "anthropic",
                                        "is_cde": rec.get("is_cde", False),
                                        "is_primary_key": rec.get("is_primary_key", False),
                                        "has_historical_issues": rec.get("has_historical_issues", False),
                                        "data_quality_score": rec.get("data_quality_score"),
                                        "risk_factors": rec.get("risk_factors", []),
                                        "processing_time_ms": rec.get("processing_time_ms", 0),
                                        "request_payload": {
                                            "model": result.get("model_used", "claude-3"),
                                            "temperature": 0.3
                                        },
                                        "response_payload": rec
                                    })
                            
                            if planning_attr_ids:
                                logger.info(f"Saving {len(planning_attr_ids)} recommendations for batch {batch_num + 1}")
                                # Save this batch of recommendations
                                await service.add_attributes_to_version(
                                    version_id=version_id,
                                    planning_attribute_ids=planning_attr_ids,
                                    llm_recommendations=llm_recommendations,
                                    user_id=user_id
                                )
                                updated_count += len(planning_attr_ids)
                                logger.info(f"Successfully saved batch {batch_num + 1}. Total saved: {updated_count}")
                                
                                # Update progress with saved count
                                job_manager.update_job_progress(
                                    job_id,
                                    message=f"Saved {updated_count} recommendations so far..."
                                )
                            else:
                                logger.warning(f"No valid planning_attr_ids found for batch {batch_num + 1} - skipping save")
                    
                    # Commit any remaining changes
                    await task_db.commit()
                    
                    # Mark job as completed
                    job_manager.update_job_progress(
                        job_id,
                        status="completed",
                        progress_percentage=100,
                        current_step="Completed",
                        message=f"Successfully generated recommendations for {updated_count} attributes"
                    )
                    job_manager.complete_job(job_id, result={
                        "test_recommendations": updated_count,
                        "attributes_processed": len(attributes_to_process),
                        "incremental_update": not force_regenerate,
                        "force_regenerate": force_regenerate
                    })
                    
                    logger.info(f"✅ Completed scoping recommendations for job {job_id}")
                    
            except Exception as e:
                logger.error(f"Error in scoping recommendations: {str(e)}")
                job_manager.update_job_progress(
                    job_id,
                    message=f"Recommendation generation failed: {str(e)}"
                )
                job_manager.complete_job(job_id, error=str(e))
        
        # Run the task using background jobs manager with proper async handling
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        import threading
        
        logger.info(f"Running scoping recommendations using background jobs manager for job {job_id}")
        
        # Run in a separate thread to avoid blocking
        def run_in_background():
            try:
                # Create new event loop for this thread
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                new_loop.run_until_complete(run_scoping_recommendations())
                new_loop.close()
            except Exception as e:
                logger.error(f"Background task failed: {str(e)}")
                job_manager.complete_job(job_id, error=str(e))
        
        # Start the background thread
        thread = threading.Thread(target=run_in_background, daemon=True)
        thread.start()
        
        logger.info(f"✅ Started background thread for job {job_id}")
        
        return {
            "message": f"LLM recommendation generation started in background ({('incremental' if not force_regenerate else 'force regeneration')})",
            "job_id": job_id,
            "status": "started",
            "total_attributes": len(attributes_to_process),
            "force_regenerate": force_regenerate,
            "attributes_without_recommendations": len(attributes_to_process) if not force_regenerate else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting scoping recommendations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start recommendation generation: {str(e)}")


@router.post("/cycles/{cycle_id}/reports/{report_id}/recommendations/attribute/{attribute_id}")
async def regenerate_single_attribute_recommendation(
    cycle_id: int,
    report_id: int,
    attribute_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Regenerate LLM recommendation for a single attribute.
    This is a convenience endpoint that calls the main recommendations endpoint
    with the specific attribute ID.
    """
    try:
        # Call the main endpoint with specific attribute
        return await generate_scoping_recommendations_legacy(
            cycle_id=cycle_id,
            report_id=report_id,
            request_data={
                "force_regenerate": True,
                "attribute_ids": [attribute_id]
            },
            db=db,
            current_user=current_user
        )
    except Exception as e:
        logger.error(f"Error regenerating recommendation for attribute {attribute_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cycles/{cycle_id}/reports/{report_id}/decisions")
async def get_scoping_decisions_legacy(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Legacy endpoint for scoping decisions"""
    try:
        # Get the phase for this cycle/report
        from app.models.workflow import WorkflowPhase
        from sqlalchemy import select
        
        phase_query = select(WorkflowPhase).where(
            WorkflowPhase.cycle_id == cycle_id,
            WorkflowPhase.report_id == report_id,
            WorkflowPhase.phase_name == "Scoping"
        ).limit(1)
        phase_result_obj = await db.execute(phase_query)
        phase_result = phase_result_obj.scalar_one_or_none()
        
        if not phase_result:
            return []  # Return empty array if no phase found
        
        # Get existing scoping decisions
        decisions_query = """
        SELECT 
            decision_id,
            attribute_id,
            phase_id,
            tester_decision,
            final_scoping,
            tester_rationale,
            tester_decided_by,
            tester_decided_at,
            report_owner_decision,
            report_owner_notes,
            report_owner_decided_by,
            report_owner_decided_at,
            override_reason,
            created_at,
            version
        FROM cycle_report_scoping_decisions 
        WHERE phase_id = :phase_id
        ORDER BY created_at DESC
        """
        
        result = await db.execute(text(decisions_query), {"phase_id": phase_result.phase_id})
        rows = result.fetchall()
        
        # Convert to expected format
        decisions = []
        for row in rows:
            try:
                decisions.append({
                    "decision_id": row.decision_id,
                    "attribute_id": row.attribute_id,
                    "phase_id": row.phase_id,
                    "tester_decision": row.tester_decision,
                    "final_scoping": row.final_scoping,
                    "tester_rationale": row.tester_rationale,
                    "tester_decided_by": row.tester_decided_by,
                    "tester_decided_at": row.tester_decided_at.isoformat() if row.tester_decided_at else None,
                    "report_owner_decision": row.report_owner_decision,
                    "report_owner_notes": row.report_owner_notes,
                    "report_owner_decided_by": row.report_owner_decided_by,
                    "report_owner_decided_at": row.report_owner_decided_at.isoformat() if row.report_owner_decided_at else None,
                    "override_reason": row.override_reason,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "version": row.version
                })
            except Exception as row_error:
                logger.error(f"Error processing decision row {row.decision_id}: {str(row_error)}")
                continue
        
        return decisions
    except Exception as e:
        logger.error(f"Error retrieving scoping decisions: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/cycles/{cycle_id}/reports/{report_id}/start")
@require_permission("scoping", "write")
async def start_scoping_phase(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start the scoping phase and create initial version with planning attributes"""
    try:
        # Get the scoping phase
        from app.models.workflow import WorkflowPhase
        from sqlalchemy import select, and_
        
        phase_query = select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == "Scoping"
            )
        )
        phase_result = await db.execute(phase_query)
        phase = phase_result.scalar_one_or_none()
        
        if not phase:
            raise HTTPException(status_code=404, detail="Scoping phase not found")
        
        if phase.state == "In Progress":
            return {"message": "Scoping phase already started", "phase_id": phase.phase_id}
        
        # Get planning phase
        planning_query = select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == "Planning"
            )
        )
        planning_result = await db.execute(planning_query)
        planning_phase = planning_result.scalar_one_or_none()
        
        if not planning_phase or planning_phase.status != "Complete":
            raise HTTPException(
                status_code=400, 
                detail="Planning phase must be completed before starting scoping"
            )
        
        # Start the phase
        phase.state = "In Progress"
        phase.status = "In Progress"
        phase.actual_start_date = datetime.utcnow()
        phase.started_by = current_user.user_id
        
        # Create initial scoping version
        service = ScopingService(db)
        existing_version = await service.get_current_version(phase.phase_id)
        
        if not existing_version:
            # Create new version
            new_version = await service.create_version(
                phase_id=phase.phase_id,
                user_id=current_user.user_id,
                notes="Initial version created when phase started"
            )
            
            # Import approved planning attributes
            from app.models.report_attribute import ReportAttribute
            planning_attrs_query = select(ReportAttribute).where(
                and_(
                    ReportAttribute.phase_id == planning_phase.phase_id,
                    ReportAttribute.approval_status == "approved",
                    ReportAttribute.is_active == True
                )
            ).order_by(ReportAttribute.line_item_number)
            
            attrs_result = await db.execute(planning_attrs_query)
            planning_attributes = attrs_result.scalars().all()
            
            # Create scoping attributes from planning attributes
            from app.models.scoping import ScopingAttribute
            for attr in planning_attributes:
                scoping_attr = ScopingAttribute(
                    version_id=new_version.version_id,
                    phase_id=phase.phase_id,
                    planning_attribute_id=attr.id,
                    # Default selections based on attribute properties
                    tester_decision="include" if (attr.is_primary_key or attr.cde_flag) else None,
                    tester_rationale="Primary key attribute - required for testing" if attr.is_primary_key else None,
                    final_status="pending"
                )
                db.add(scoping_attr)
            
            await db.commit()
            
            logger.info(f"Created initial scoping version with {len(planning_attributes)} attributes")
        
        await db.commit()
        
        return {
            "message": "Scoping phase started successfully",
            "phase_id": phase.phase_id,
            "status": "In Progress",
            "attributes_imported": len(planning_attributes) if not existing_version else 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting scoping phase: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start scoping phase: {str(e)}")


@router.get("/cycles/{cycle_id}/reports/{report_id}/attributes")
async def get_scoping_attributes_legacy(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Legacy endpoint for scoping attributes"""
    try:
        # Get the phase for this cycle/report
        from app.models.workflow import WorkflowPhase
        from sqlalchemy import select
        
        phase_query = select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == "Scoping"
            )
        ).order_by(WorkflowPhase.phase_id.desc())  # Get the most recent if multiple exist
        
        phase_result_obj = await db.execute(phase_query)
        phase_result = phase_result_obj.scalars().first()
        
        if not phase_result:
            raise HTTPException(status_code=404, detail="Scoping phase not found")
        
        # Get the latest version by version number
        from app.models.scoping import ScopingVersion
        version_query = select(ScopingVersion).where(
            ScopingVersion.phase_id == phase_result.phase_id
        ).order_by(
            ScopingVersion.version_number.desc()
        )
        
        version_result = await db.execute(version_query)
        current_version = version_result.scalars().first()
        
        if not current_version:
            return []  # Return empty array directly
            
        # Get scoping attributes with planning attribute details
        from app.models.scoping import ScopingAttribute
        from app.models.report_attribute import ReportAttribute
        from sqlalchemy.orm import joinedload
        
        # Query scoping attributes
        scoping_attrs_query = select(ScopingAttribute).where(
            ScopingAttribute.version_id == current_version.version_id
        )
        
        scoping_attrs_result = await db.execute(scoping_attrs_query)
        scoping_attrs = scoping_attrs_result.scalars().unique().all()
        
        # If no scoping attributes, return empty array
        if not scoping_attrs:
            return []
            
        # Get planning attribute IDs
        planning_attr_ids = [attr.planning_attribute_id for attr in scoping_attrs]
        
        # Query planning attributes
        planning_attrs_query = select(ReportAttribute).where(
            ReportAttribute.id.in_(planning_attr_ids)
        )
        planning_attrs_result = await db.execute(planning_attrs_query)
        planning_attrs = planning_attrs_result.scalars().all()
        
        # Create a mapping for easy lookup
        planning_attrs_map = {str(attr.id): attr for attr in planning_attrs}
        
        # Get DQ scores from data profiling results for the same phase context
        dq_scores_map = {}
        dq_rule_counts = {}
        try:
            # Get the data profiling phase for the same cycle/report
            profiling_phase_query = select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Data Profiling"
                )
            ).order_by(WorkflowPhase.phase_id.desc())
            
            profiling_phase_result = await db.execute(profiling_phase_query)
            profiling_phase = profiling_phase_result.scalars().first()
            
            if profiling_phase:
                # Get latest data profiling results for attributes in this phase
                from app.models.data_profiling import ProfilingResult
                
                # Get only the latest execution for each rule per attribute
                # Using a window function to get the most recent execution
                from sqlalchemy import text
                
                dq_query_text = """
                WITH latest_executions AS (
                    SELECT 
                        pr.attribute_id,
                        pr.rule_id,
                        pr.pass_rate,
                        pr.executed_at,
                        ROW_NUMBER() OVER (
                            PARTITION BY pr.attribute_id, pr.rule_id 
                            ORDER BY pr.executed_at DESC
                        ) as rn
                    FROM cycle_report_data_profiling_results pr
                    WHERE pr.phase_id = :phase_id 
                        AND pr.attribute_id = ANY(:attribute_ids)
                        AND pr.execution_status = 'success'
                )
                SELECT 
                    attribute_id,
                    COUNT(DISTINCT rule_id) as rule_count,
                    AVG(pass_rate) as avg_pass_rate
                FROM latest_executions
                WHERE rn = 1
                GROUP BY attribute_id
                """
                
                dq_result = await db.execute(
                    text(dq_query_text),
                    {
                        "phase_id": profiling_phase.phase_id,
                        "attribute_ids": planning_attr_ids
                    }
                )
                
                # Store DQ scores and rule counts
                dq_rule_counts = {}
                for row in dq_result:
                    dq_scores_map[row.attribute_id] = round(row.avg_pass_rate, 1)
                    dq_rule_counts[row.attribute_id] = row.rule_count
                
                logger.info(f"Loaded DQ scores for {len(dq_scores_map)} attributes from phase {profiling_phase.phase_id} (latest executions only)")
        except Exception as e:
            logger.warning(f"Could not calculate DQ scores: {str(e)}")
        
        # Convert to frontend expected format
        attributes = []
        for scoping_attr in scoping_attrs:
            planning_attr = planning_attrs_map.get(str(scoping_attr.planning_attribute_id))
            if planning_attr:
                attributes.append({
                    "id": str(scoping_attr.attribute_id),
                    "attribute_id": str(scoping_attr.attribute_id),
                    "attribute_name": planning_attr.attribute_name,
                    "mdrm": planning_attr.mdrm,
                    "description": planning_attr.description,
                    "line_item_number": planning_attr.line_item_number,
                    "data_type": planning_attr.data_type,
                    "is_primary_key": planning_attr.is_primary_key,
                    "is_required": planning_attr.mandatory_flag == 'Mandatory',
                    "cde_flag": planning_attr.is_cde,
                    "historical_issues_flag": planning_attr.historical_issues_flag,
                    "keywords_to_look_for": planning_attr.keywords_to_look_for,
                    "testing_approach": planning_attr.testing_approach,
                    "validation_rules": planning_attr.validation_rules,
                    
                    # Scoping specific fields
                    "tester_decision": scoping_attr.tester_decision.value if scoping_attr.tester_decision and hasattr(scoping_attr.tester_decision, 'value') else scoping_attr.tester_decision,
                    "report_owner_decision": scoping_attr.report_owner_decision.value if scoping_attr.report_owner_decision and hasattr(scoping_attr.report_owner_decision, 'value') else scoping_attr.report_owner_decision,
                    "report_owner_notes": scoping_attr.report_owner_notes,
                    "report_owner_decided_at": scoping_attr.report_owner_decided_at.isoformat() if scoping_attr.report_owner_decided_at else None,
                    "report_owner_decided_by_id": scoping_attr.report_owner_decided_by_id,
                    "final_status": scoping_attr.status.value if scoping_attr.status and hasattr(scoping_attr.status, 'value') else scoping_attr.status,
                    "selected_for_testing": scoping_attr.tester_decision == "accept" if scoping_attr.tester_decision else False,
                    
                    # LLM fields
                    "llm_recommendation": scoping_attr.llm_recommendation.get("recommendation") if scoping_attr.llm_recommendation and isinstance(scoping_attr.llm_recommendation, dict) else scoping_attr.llm_recommendation,
                    "llm_risk_score": (
                        scoping_attr.llm_response_payload.get("risk_score") 
                        if scoping_attr.llm_response_payload and isinstance(scoping_attr.llm_response_payload, dict) 
                        else (float(scoping_attr.llm_confidence_score) * 100 if scoping_attr.llm_confidence_score else None)
                    ),
                    "llm_confidence_score": float(scoping_attr.llm_confidence_score) if scoping_attr.llm_confidence_score else None,
                    "llm_rationale": (
                        # Format enhanced rationale if available
                        (lambda er: f"**Business Impact:** {er.get('business_impact', 'N/A')}\n"
                                   f"**Regulatory Usage:** {er.get('regulatory_usage', 'N/A')}\n"
                                   f"**Interconnections:** {er.get('interconnections', 'N/A')}\n"
                                   f"**Historical Issues:** {er.get('historical_issues', 'N/A')}"
                        )(scoping_attr.llm_response_payload.get("enhanced_rationale"))
                        if scoping_attr.llm_response_payload and isinstance(scoping_attr.llm_response_payload, dict) 
                           and scoping_attr.llm_response_payload.get("enhanced_rationale") and isinstance(scoping_attr.llm_response_payload.get("enhanced_rationale"), dict)
                        else scoping_attr.llm_rationale
                    ),
                    "llm_provider": scoping_attr.llm_provider,
                    
                    # Data Quality fields
                    "composite_dq_score": dq_scores_map.get(scoping_attr.planning_attribute_id),
                    "has_profiling_data": scoping_attr.planning_attribute_id in dq_scores_map,
                    "dq_rules_count": dq_rule_counts.get(scoping_attr.planning_attribute_id, 0),
                    
                    # Additional scoping fields from model
                    "tester_rationale": scoping_attr.tester_rationale,
                    "tester_decided_at": scoping_attr.tester_decided_at.isoformat() if scoping_attr.tester_decided_at else None,
                    "report_owner_notes": scoping_attr.report_owner_notes,
                    "report_owner_decided_at": scoping_attr.report_owner_decided_at.isoformat() if scoping_attr.report_owner_decided_at else None,
                    "is_override": scoping_attr.is_override,
                    "override_reason": scoping_attr.override_reason,
                    "final_scoping": scoping_attr.final_scoping,
                    "is_cde": scoping_attr.is_cde,
                    "status": scoping_attr.status.value if hasattr(scoping_attr.status, 'value') else scoping_attr.status
                })
        
        return attributes  # Return array directly for frontend compatibility
    except Exception as e:
        import traceback
        logger.error(f"Error retrieving scoping attributes: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {str(e)}")


@router.get("/cycles/{cycle_id}/reports/{report_id}/feedback")
async def get_scoping_feedback_legacy(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Legacy endpoint for scoping feedback"""
    try:
        # Placeholder implementation - return empty feedback for now
        return {"feedback": [], "phase_id": None}
    except Exception as e:
        logger.error(f"Error retrieving scoping feedback: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/cycles/{cycle_id}/reports/{report_id}/versions")
async def get_scoping_versions_legacy(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Legacy endpoint for scoping versions"""
    try:
        # Get the phase for this cycle/report
        from app.models.workflow import WorkflowPhase
        from sqlalchemy import select
        
        phase_query = select(WorkflowPhase).where(
            WorkflowPhase.cycle_id == cycle_id,
            WorkflowPhase.report_id == report_id,
            WorkflowPhase.phase_name == "Scoping"
        ).limit(1)
        phase_result_obj = await db.execute(phase_query)
        phase_result = phase_result_obj.scalar_one_or_none()
        
        if not phase_result:
            raise HTTPException(status_code=404, detail="Scoping phase not found")
        
        service = ScopingService(db)
        versions_objects = await service.get_phase_versions(phase_result.phase_id)
        
        # The service now returns dictionaries, not objects
        versions = [
            {
                "version_id": version.get("version_id"),
                "version_number": version.get("version_number"),
                "phase_id": version.get("phase_id"),
                "version_status": version.get("version_status", "draft"),
                "created_at": version.get("created_at").isoformat() if version.get("created_at") else None,
                "created_by": version.get("created_by"),
                "submitted_at": version.get("submitted_at").isoformat() if version.get("submitted_at") else None,
                "approved_at": version.get("approved_at").isoformat() if version.get("approved_at") else None,
                "is_current": version.get("is_current", False)  # Include the is_current flag
            }
            for version in versions_objects
        ]
        
        return {"versions": versions}
    except Exception as e:
        logger.error(f"Error retrieving scoping versions: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/cycles/{cycle_id}/reports/{report_id}/scoping-submission")
async def submit_scoping_decisions(
    cycle_id: int,
    report_id: int,
    submission_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit scoping decisions to Report Owner for approval"""
    try:
        # Get the phase for this cycle/report
        from app.models.workflow import WorkflowPhase
        from sqlalchemy import select
        
        phase_query = select(WorkflowPhase).where(
            WorkflowPhase.cycle_id == cycle_id,
            WorkflowPhase.report_id == report_id,
            WorkflowPhase.phase_name == "Scoping"
        ).limit(1)
        phase_result_obj = await db.execute(phase_query)
        phase_result = phase_result_obj.scalar_one_or_none()
        
        if not phase_result:
            raise HTTPException(status_code=404, detail="Scoping phase not found")
        
        service = ScopingService(db)
        
        # Get current version
        current_version = await service.get_current_version(phase_result.phase_id)
        if not current_version:
            raise HTTPException(status_code=404, detail="No scoping version found")
        
        # Save the decisions
        decisions = submission_data.get("decisions", [])
        for decision in decisions:
            # Update attribute with tester decision
            attribute = await service.make_tester_decision(
                attribute_id=UUID(decision["attribute_id"]),
                decision=TesterDecision.ACCEPT if decision["decision"] == "Accept" else TesterDecision.DECLINE,
                rationale=decision.get("tester_rationale"),
                user_id=current_user.user_id
            )
        
        # Submit version for approval
        version = await service.submit_version_for_approval(
            version_id=current_version["version_id"],
            submission_notes=submission_data.get("submission_notes"),
            user_id=current_user.user_id
        )
        
        # Determine if this is a revision
        is_revision = submission_data.get("confirm_submission", False) and version.version_number > 1
        
        return {
            "success": True,
            "message": "Scoping decisions submitted successfully",
            "version": version.version_number,
            "is_revision": is_revision
        }
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error submitting scoping decisions: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


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