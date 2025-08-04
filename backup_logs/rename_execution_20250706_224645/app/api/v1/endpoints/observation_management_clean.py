"""
Clean Architecture Observation Management API endpoints
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.permissions import require_permission
from app.models.user import User
from app.application.dtos.observation import (
    ObservationCreateDTO,
    ObservationResponseDTO,
    ObservationUpdateDTO,
    ImpactAssessmentCreateDTO,
    ImpactAssessmentResponseDTO,
    ObservationApprovalRequestDTO,
    ObservationApprovalResponseDTO,
    ObservationBatchReviewRequestDTO,
    ResolutionCreateDTO,
    ResolutionResponseDTO,
    ObservationPhaseStartDTO,
    ObservationPhaseStatusDTO,
    ObservationPhaseCompleteDTO,
    ObservationAnalyticsDTO,
    AutoDetectionRequestDTO,
    ObservationTypeEnum,
    ObservationSeverityEnum,
    ObservationStatusEnum
)
from app.application.use_cases.observation import (
    CreateObservationUseCase,
    GetObservationUseCase,
    ListObservationsUseCase,
    UpdateObservationUseCase,
    SubmitObservationUseCase,
    ReviewObservationUseCase,
    BatchReviewObservationsUseCase,
    CreateImpactAssessmentUseCase,
    CreateResolutionUseCase,
    GetObservationPhaseStatusUseCase,
    CompleteObservationPhaseUseCase,
    GetObservationAnalyticsUseCase,
    AutoDetectObservationsUseCase
)

router = APIRouter()


# Phase Management Endpoints
@router.post("/{cycle_id}/reports/{report_id}/start", response_model=ObservationPhaseStatusDTO)
@require_permission("observations", "create")
async def start_observation_phase(
    cycle_id: int,
    report_id: int,
    start_data: ObservationPhaseStartDTO,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start observation management phase"""
    try:
        # Get current status (this will create phase if it doesn't exist)
        use_case = GetObservationPhaseStatusUseCase()
        status = await use_case.execute(cycle_id, report_id, db)
        
        if status.phase_status != "Not Started":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Observation phase has already been started"
            )
        
        # Phase is automatically created when first observation is added
        # Return current status
        return status
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start observation phase: {str(e)}"
        )


@router.get("/{cycle_id}/reports/{report_id}/status", response_model=ObservationPhaseStatusDTO)
@require_permission("observations", "read")
async def get_observation_phase_status(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get observation management phase status"""
    try:
        use_case = GetObservationPhaseStatusUseCase()
        return await use_case.execute(cycle_id, report_id, db)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get phase status: {str(e)}"
        )


@router.post("/{cycle_id}/reports/{report_id}/complete")
@require_permission("observations", "execute")
async def complete_observation_phase(
    cycle_id: int,
    report_id: int,
    completion_data: ObservationPhaseCompleteDTO,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Complete observation management phase"""
    try:
        use_case = CompleteObservationPhaseUseCase()
        result = await use_case.execute(
            cycle_id, report_id, completion_data, current_user.user_id, db
        )
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete phase: {str(e)}"
        )


# Observation CRUD Endpoints
@router.post("/{cycle_id}/reports/{report_id}/observations", response_model=ObservationResponseDTO)
@require_permission("observations", "create")
async def create_observation(
    cycle_id: int,
    report_id: int,
    observation_data: ObservationCreateDTO,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new observation with intelligent grouping"""
    try:
        use_case = CreateObservationUseCase()
        observation = await use_case.execute(
            cycle_id, report_id, observation_data, current_user.user_id, db
        )
        return observation
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create observation: {str(e)}"
        )


@router.get("/{cycle_id}/reports/{report_id}/observations", response_model=List[ObservationResponseDTO])
@require_permission("observations", "read")
async def list_observations(
    cycle_id: int,
    report_id: int,
    status: Optional[ObservationStatusEnum] = None,
    severity: Optional[ObservationSeverityEnum] = None,
    observation_type: Optional[ObservationTypeEnum] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List observations with optional filters"""
    try:
        use_case = ListObservationsUseCase()
        observations = await use_case.execute(
            cycle_id, report_id, status, severity, observation_type, db
        )
        return observations
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list observations: {str(e)}"
        )


@router.get("/observations/{observation_id}", response_model=ObservationResponseDTO)
@require_permission("observations", "read")
async def get_observation(
    observation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get observation details"""
    try:
        use_case = GetObservationUseCase()
        observation = await use_case.execute(observation_id, db)
        return observation
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get observation: {str(e)}"
        )


@router.put("/observations/{observation_id}", response_model=ObservationResponseDTO)
@require_permission("observations", "update")
async def update_observation(
    observation_id: str,
    update_data: ObservationUpdateDTO,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update observation details"""
    try:
        use_case = UpdateObservationUseCase()
        observation = await use_case.execute(
            observation_id, update_data, current_user.user_id, db
        )
        return observation
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update observation: {str(e)}"
        )


@router.post("/observations/{observation_id}/submit", response_model=ObservationResponseDTO)
@require_permission("observations", "update")
async def submit_observation(
    observation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit observation for review"""
    try:
        use_case = SubmitObservationUseCase()
        observation = await use_case.execute(
            observation_id, current_user.user_id, db
        )
        return observation
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit observation: {str(e)}"
        )


# Review and Approval Endpoints
@router.post("/observations/{observation_id}/review", response_model=ObservationApprovalResponseDTO)
@require_permission("observations", "approve")
async def review_observation(
    observation_id: str,
    review_data: ObservationApprovalRequestDTO,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Review and approve/reject observation"""
    try:
        use_case = ReviewObservationUseCase()
        approval = await use_case.execute(
            observation_id, review_data, current_user.user_id, db
        )
        return approval
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to review observation: {str(e)}"
        )


@router.post("/{cycle_id}/reports/{report_id}/observations/batch-review", response_model=Dict[str, Any])
@require_permission("observations", "approve")
async def batch_review_observations(
    cycle_id: int,
    report_id: int,
    batch_request: ObservationBatchReviewRequestDTO,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Batch approve or reject multiple observations"""
    try:
        use_case = BatchReviewObservationsUseCase()
        result = await use_case.execute(
            cycle_id, report_id, batch_request, current_user.user_id, db
        )
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to batch review observations: {str(e)}"
        )


# Impact Assessment Endpoints
@router.post("/observations/{observation_id}/impact-assessment", response_model=ImpactAssessmentResponseDTO)
@require_permission("observations", "update")
async def create_impact_assessment(
    observation_id: str,
    assessment_data: ImpactAssessmentCreateDTO,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create impact assessment for observation"""
    try:
        use_case = CreateImpactAssessmentUseCase()
        assessment = await use_case.execute(
            observation_id, assessment_data, current_user.user_id, db
        )
        return assessment
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create impact assessment: {str(e)}"
        )


# Resolution Endpoints
@router.post("/observations/{observation_id}/resolution", response_model=ResolutionResponseDTO)
@require_permission("observations", "update")
async def create_resolution(
    observation_id: str,
    resolution_data: ResolutionCreateDTO,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create resolution for observation"""
    try:
        use_case = CreateResolutionUseCase()
        resolution = await use_case.execute(
            observation_id, resolution_data, current_user.user_id, db
        )
        return resolution
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create resolution: {str(e)}"
        )


# Analytics Endpoints
@router.get("/{cycle_id}/reports/{report_id}/analytics", response_model=ObservationAnalyticsDTO)
@require_permission("observations", "read")
async def get_observation_analytics(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get observation analytics and insights"""
    try:
        use_case = GetObservationAnalyticsUseCase()
        analytics = await use_case.execute(cycle_id, report_id, db)
        return analytics
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analytics: {str(e)}"
        )


# Auto-Detection Endpoints
@router.post("/{cycle_id}/reports/{report_id}/auto-detect", response_model=Dict[str, Any])
@require_permission("observations", "create")
async def auto_detect_observations(
    cycle_id: int,
    report_id: int,
    request_data: AutoDetectionRequestDTO,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Auto-detect and create observations from test failures"""
    try:
        use_case = AutoDetectObservationsUseCase()
        result = await use_case.execute(
            cycle_id, report_id, request_data, current_user.user_id, db
        )
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to auto-detect observations: {str(e)}"
        )


# Tester-specific endpoints
@router.get("/my-observations", response_model=List[ObservationResponseDTO])
@require_permission("observations", "read")
async def get_my_observations(
    status: Optional[ObservationStatusEnum] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get observations created by current user"""
    try:
        from sqlalchemy import select, and_
        from app.models import ObservationRecord
        
        query = select(ObservationRecord).where(
            ObservationRecord.created_by == current_user.user_id
        )
        
        if status:
            query = query.where(ObservationRecord.status == status)
        
        query = query.order_by(ObservationRecord.created_at.desc())
        
        result = await db.execute(query)
        observations = result.scalars().all()
        
        return [
            ObservationResponseDTO(
                observation_id=obs.observation_id,
                phase_id=obs.phase_id,
                cycle_id=obs.cycle_id,
                report_id=obs.report_id,
                observation_number=obs.observation_number,
                observation_title=obs.observation_title,
                observation_description=obs.observation_description,
                observation_type=obs.observation_type,
                severity=obs.severity,
                status=obs.status,
                source_attribute_id=obs.source_attribute_id,
                source_sample_id=obs.source_sample_id,
                test_execution_id=obs.test_execution_id,
                grouped_count=obs.grouped_count,
                created_by=obs.created_by,
                created_at=obs.created_at,
                updated_at=obs.updated_at,
                submitted_at=obs.submitted_at,
                reviewed_by=obs.reviewed_by,
                reviewed_at=obs.reviewed_at,
                resolution_status=obs.resolution.resolution_status if obs.resolution else None
            )
            for obs in observations
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user observations: {str(e)}"
        )


# Report Owner/Executive endpoints
@router.get("/pending-review", response_model=List[ObservationResponseDTO])
@require_permission("observations", "approve")
async def get_pending_review_observations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get observations pending review for current user's reports"""
    try:
        from sqlalchemy import select, and_, or_
        from app.models import ObservationRecord, Report, ReportOwner
        
        # Get reports owned by current user
        if current_user.role in ['Report Owner', 'Report Owner Executive']:
            # Get observations for owned reports
            query = select(ObservationRecord).join(
                Report, ObservationRecord.report_id == Report.report_id
            ).join(
                ReportOwner, Report.report_id == ReportOwner.report_id
            ).where(and_(
                ReportOwner.owner_id == current_user.user_id,
                ObservationRecord.status.in_([
                    ObservationStatusEnum.SUBMITTED,
                    ObservationStatusEnum.UNDER_REVIEW
                ])
            ))
        else:
            # Admin can see all pending
            query = select(ObservationRecord).where(
                ObservationRecord.status.in_([
                    ObservationStatusEnum.SUBMITTED,
                    ObservationStatusEnum.UNDER_REVIEW
                ])
            )
        
        query = query.order_by(
            ObservationRecord.severity.desc(),
            ObservationRecord.submitted_at
        )
        
        result = await db.execute(query)
        observations = result.scalars().all()
        
        return [
            ObservationResponseDTO(
                observation_id=obs.observation_id,
                phase_id=obs.phase_id,
                cycle_id=obs.cycle_id,
                report_id=obs.report_id,
                observation_number=obs.observation_number,
                observation_title=obs.observation_title,
                observation_description=obs.observation_description,
                observation_type=obs.observation_type,
                severity=obs.severity,
                status=obs.status,
                source_attribute_id=obs.source_attribute_id,
                source_sample_id=obs.source_sample_id,
                test_execution_id=obs.test_execution_id,
                grouped_count=obs.grouped_count,
                created_by=obs.created_by,
                created_at=obs.created_at,
                updated_at=obs.updated_at,
                submitted_at=obs.submitted_at,
                reviewed_by=obs.reviewed_by,
                reviewed_at=obs.reviewed_at,
                resolution_status=obs.resolution.resolution_status if obs.resolution else None
            )
            for obs in observations
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pending review observations: {str(e)}"
        )