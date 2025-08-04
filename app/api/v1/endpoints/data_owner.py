"""
Clean Architecture Data Provider Identification API endpoints
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.permissions import require_permission
from app.models.user import User
from app.application.dtos.data_owner import (
    DataProviderPhaseStartDTO,
    DataProviderPhaseStatusDTO,
    LOBAssignmentSubmissionDTO,
    CDOAssignmentSubmissionDTO,
    HistoricalAssignmentResponseDTO,
    AssignmentMatrixDTO,
    SLAViolationDTO,
    EscalationEmailRequestDTO,
    EscalationEmailResponseDTO,
    DataProviderPhaseCompleteDTO,
    DataOwnerAssignmentDTO,
    CDODashboardResponseDTO,
    DataOwnerAssignmentAuditLogDTO
)
from app.application.use_cases.data_owner_universal import (
    StartDataProviderPhaseUseCase,
    GetDataProviderPhaseStatusUseCase,
    GetHistoricalAssignmentsUseCase,
    SubmitCDOAssignmentsUseCase,
    GetAssignmentMatrixUseCase,
    GetCDOAssignmentsUseCase,
    GetCDODashboardUseCase,
    CompleteDataProviderPhaseUseCase
)
from app.application.use_cases.send_to_data_executive import SendToDataExecutiveUseCase

router = APIRouter()


# Phase Management Endpoints
@router.post("/cycles/{cycle_id}/reports/{report_id}/start", response_model=Dict[str, Any])
@require_permission("data_owner", "execute")
async def start_data_provider_phase(
    cycle_id: int,
    report_id: int,
    start_data: DataProviderPhaseStartDTO,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start data provider identification phase"""
    try:
        use_case = StartDataProviderPhaseUseCase()
        result = await use_case.execute(
            cycle_id, report_id, start_data, current_user.user_id, db
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
            detail=f"Failed to start data provider phase: {str(e)}"
        )


@router.get("/cycles/{cycle_id}/reports/{report_id}/status", response_model=DataProviderPhaseStatusDTO)
@require_permission("data_owner", "read")
async def get_data_provider_phase_status(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get data provider identification phase status"""
    try:
        use_case = GetDataProviderPhaseStatusUseCase()
        return await use_case.execute(cycle_id, report_id, db)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get phase status: {str(e)}"
        )


@router.post("/cycles/{cycle_id}/reports/{report_id}/complete", response_model=Dict[str, Any])
@require_permission("data_owner", "complete")
async def complete_data_provider_phase(
    cycle_id: int,
    report_id: int,
    completion_data: DataProviderPhaseCompleteDTO,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Complete data provider identification phase"""
    try:
        use_case = CompleteDataProviderPhaseUseCase()
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


# Assignment Management Endpoints
@router.post("/cycles/{cycle_id}/reports/{report_id}/send-to-data-executives", response_model=Dict[str, Any])
@require_permission("data_owner", "execute")
async def send_to_data_executives(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send data owner assignment requests to Data Executives"""
    try:
        use_case = SendToDataExecutiveUseCase()
        result = await use_case.execute(
            cycle_id, report_id, current_user.user_id, db
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
            detail=f"Failed to send assignments to data executives: {str(e)}"
        )


@router.get("/cycles/{cycle_id}/reports/{report_id}/historical-assignments", response_model=HistoricalAssignmentResponseDTO)
@require_permission("data_owner", "read")
async def get_historical_assignments(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get historical data provider assignment suggestions"""
    try:
        use_case = GetHistoricalAssignmentsUseCase()
        return await use_case.execute(cycle_id, report_id, db)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get historical assignments: {str(e)}"
        )


@router.post("/cycles/{cycle_id}/reports/{report_id}/cdo-assignments", response_model=Dict[str, Any])
@require_permission("data_owner", "assign")
async def submit_cdo_assignments(
    cycle_id: int,
    report_id: int,
    submission: CDOAssignmentSubmissionDTO,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """CDO submits data provider assignments"""
    try:
        # Verify user is a CDO
        if not current_user.is_cdo:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Data Executive role required"
            )
        
        use_case = SubmitCDOAssignmentsUseCase()
        result = await use_case.execute(
            cycle_id, report_id, submission, current_user.user_id, db
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
            detail=f"Failed to submit CDO assignments: {str(e)}"
        )


@router.get("/cycles/{cycle_id}/reports/{report_id}/assignment-matrix", response_model=AssignmentMatrixDTO)
@require_permission("data_owner", "read")
async def get_assignment_matrix(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get complete assignment matrix for data provider phase"""
    try:
        use_case = GetAssignmentMatrixUseCase()
        return await use_case.execute(cycle_id, report_id, db)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get assignment matrix: {str(e)}"
        )


# CDO Dashboard and Assignments
@router.get("/cycles/{cycle_id}/reports/{report_id}/my-assignments", response_model=List[DataOwnerAssignmentDTO])
@require_permission("data_owner", "read")
async def get_cdo_assignments(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get data provider assignments made by the current CDO"""
    try:
        # Verify user is a CDO
        if not current_user.is_cdo:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Data Executive role required"
            )
        
        use_case = GetCDOAssignmentsUseCase()
        return await use_case.execute(cycle_id, report_id, current_user.user_id, db)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get CDO assignments: {str(e)}"
        )


@router.get("/cdo/dashboard", response_model=CDODashboardResponseDTO)
@require_permission("data_owner", "read")
async def get_cdo_dashboard(
    time_filter: str = Query(default="last_30_days"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive CDO dashboard with workflow status and assignments"""
    try:
        # Verify user is a CDO
        if not current_user.is_cdo:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Data Executive role required"
            )
        
        use_case = GetCDODashboardUseCase()
        return await use_case.execute(current_user.user_id, time_filter, db)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get CDO dashboard: {str(e)}"
        )


# Backwards compatibility endpoints
@router.post("/cycles/{cycle_id}/reports/{report_id}/lob-assignments", response_model=Dict[str, Any])
@require_permission("data_owner", "execute")
async def submit_lob_assignments(
    cycle_id: int,
    report_id: int,
    submission: LOBAssignmentSubmissionDTO,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit LOB assignments for scoped attributes (deprecated - LOBs determined from sample data)"""
    return {
        "success": True,
        "message": "LOB assignments are now automatically determined from sample data",
        "assignments_created": 0,
        "cdo_notifications_sent": False
    }


@router.get("/cycles/{cycle_id}/reports/{report_id}/sla-violations", response_model=List[SLAViolationDTO])
@require_permission("data_owner", "read")
async def get_sla_violations(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current SLA violations for escalation"""
    # SLA tracking not implemented in clean architecture yet
    return []


@router.post("/cycles/{cycle_id}/reports/{report_id}/send-escalation", response_model=EscalationEmailResponseDTO)
@require_permission("data_owner", "escalate")
async def send_escalation_email(
    cycle_id: int,
    report_id: int,
    request_body: EscalationEmailRequestDTO,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send escalation email for SLA violations"""
    # Email escalation not implemented in clean architecture yet
    return EscalationEmailResponseDTO(
        email_sent=False,
        recipients=[],
        violations_escalated=0,
        escalation_level=request_body.escalation_level,
        sent_at=datetime.utcnow()
    )


@router.get("/{cycle_id}/reports/{report_id}/audit-log", response_model=DataOwnerAssignmentAuditLogDTO)
@require_permission("data_owner", "read")
async def get_data_provider_audit_log(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get data provider phase audit log"""
    try:
        from sqlalchemy import select, and_
        from app.models import DataProviderPhaseAuditLog, User
        
        audit_entries = await db.execute(
            select(DataProviderPhaseAuditLog, User)
            .join(User, DataProviderPhaseAuditLog.performed_by == User.user_id)
            .where(and_(
                DataProviderPhaseAuditLog.cycle_id == cycle_id,
                DataProviderPhaseAuditLog.report_id == report_id
            ))
            .order_by(DataProviderPhaseAuditLog.performed_at.desc())
        )
        audit_entries = audit_entries.all()
        
        from app.application.dtos.data_owner import AuditLogEntryDTO
        
        audit_log_entries = []
        for audit_log, user in audit_entries:
            audit_log_entries.append(AuditLogEntryDTO(
                assignment_id=audit_log.entity_id or 0,
                attribute_id=0,
                action=audit_log.action,
                performed_by=audit_log.performed_by,
                performed_at=audit_log.performed_at,
                old_values=audit_log.old_values,
                new_values=audit_log.new_values,
                notes=audit_log.notes
            ))
        
        return DataProviderAssignmentAuditLogDTO(
            cycle_id=cycle_id,
            report_id=report_id,
            audit_entries=audit_log_entries,
            total_entries=len(audit_log_entries)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get audit log: {str(e)}"
        )