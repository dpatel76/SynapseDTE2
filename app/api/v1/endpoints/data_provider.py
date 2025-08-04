"""
Data Provider Identification phase endpoints
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, update, delete
from sqlalchemy.orm import selectinload
import logging
import time
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.permissions import require_permission
from app.models.user import User
from app.models.test_cycle import TestCycle
from app.models.cycle_report import CycleReport
from app.models.report import Report
from app.models.workflow import WorkflowPhase
from app.models.report_attribute import ReportAttribute
from app.models.lob import LOB
from app.models.data_owner import (
    HistoricalDataOwnerAssignment,
    DataOwnerSLAViolation, DataOwnerEscalationLog, DataOwnerPhaseAuditLog
)
from app.models.sample_selection import SampleSet, SampleRecord
from app.models.testing import DataOwnerAssignment
from app.schemas.data_provider import (
    DataProviderPhaseStart, AttributeLOBAssignment as AttributeLOBAssignmentSchema,
    LOBAssignmentSubmission, CDONotificationData, DataProviderAssignmentRequest,
    CDOAssignmentSubmission, HistoricalAssignmentResponse, AttributeAssignmentStatus,
    DataProviderPhaseStatus, SLAViolation, EscalationEmailRequest, EscalationEmailResponse,
    DataProviderPhaseComplete, AssignmentMatrix, CDOWorkloadSummary,
    DataProviderAssignmentAuditLog, AssignmentStatus, EscalationLevel
)
from app.models.scoping import TesterScopingDecision

logger = logging.getLogger(__name__)
router = APIRouter()

# Role dependency functions
def require_tester(current_user: User = Depends(get_current_user)):
    """Require tester role"""
    if not current_user.is_tester:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tester role required"
        )
    return True

def require_cdo(current_user: User = Depends(get_current_user)):
    """Require CDO role"""
    if not current_user.is_cdo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CDO role required"
        )
    return True

def require_tester_or_cdo(current_user: User = Depends(get_current_user)):
    """Require tester or CDO role"""
    if not (current_user.is_tester or current_user.is_cdo):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tester or CDO role required"
        )
    return True

async def create_audit_log(
    db: AsyncSession,
    cycle_id: int,
    report_id: int,
    action: str,
    entity_type: str,
    entity_id: Optional[int],
    performed_by: int,
    old_values: Optional[Dict[str, Any]] = None,
    new_values: Optional[Dict[str, Any]] = None,
    notes: Optional[str] = None,
    request: Optional[Request] = None
):
    """Create audit log entry for data provider phase actions"""
    audit_log = DataProviderPhaseAuditLog(
        cycle_id=cycle_id,
        report_id=report_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        performed_by=performed_by,
        performed_at=datetime.utcnow(),
        old_values=old_values,
        new_values=new_values,
        notes=notes,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None
    )
    db.add(audit_log)
    await db.commit()

@router.post("/{cycle_id}/reports/{report_id}/start", response_model=dict)
@require_permission("data_provider", "execute")
async def start_data_provider_phase(
    cycle_id: int,
    report_id: int,
    request_body: DataProviderPhaseStart,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user),
    request: Request = None
):
    """Start data provider identification phase"""
    start_time = time.time()

    try:
        # Verify cycle and report exist
        cycle_report = await db.execute(
            select(CycleReport)
            .options(selectinload(CycleReport.cycle), selectinload(CycleReport.report))
            .where(and_(CycleReport.cycle_id == cycle_id, CycleReport.report_id == report_id))
        )
        cycle_report = cycle_report.scalar_one_or_none()

        if not cycle_report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cycle report not found"
            )

        # Verify tester assignment
        if cycle_report.tester_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only assigned tester can start data provider phase"
            )

        # Check if sampling phase is complete
        sampling_phase = await db.execute(
            select(WorkflowPhase)
            .where(and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == 'Sample Selection'
            ))
        )
        sampling_phase = sampling_phase.scalar_one_or_none()

        if not sampling_phase or sampling_phase.status != 'Complete':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sampling phase must be completed before starting data provider identification"
            )

        # Check if data provider phase already exists and has been started
        data_provider_phase = await db.execute(
            select(WorkflowPhase)
            .where(and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == 'Data Owner Identification'
            ))
        )
        data_provider_phase = data_provider_phase.scalar_one_or_none()

        if data_provider_phase and data_provider_phase.actual_start_date:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Data provider identification phase already started"
            )

        # If phase record exists but hasn't been started, update it instead of creating new one
        if data_provider_phase:
            # Update existing phase record
            data_provider_phase.status = 'In Progress'
            data_provider_phase.state = 'In Progress'
            data_provider_phase.actual_start_date = datetime.utcnow()
            data_provider_phase.started_by = current_user.user_id
            if request_body.planned_start_date:
                data_provider_phase.planned_start_date = request_body.planned_start_date
            if request_body.planned_end_date:
                data_provider_phase.planned_end_date = request_body.planned_end_date
            
            # Create DataProviderAssignment records for non-primary key scoped attributes
            await create_data_provider_assignments(db, cycle_id, report_id, current_user.user_id)
            
            await db.commit()
            
            # Create audit log
            await create_audit_log(
                db, cycle_id, report_id, "start_data_provider_phase", "WorkflowPhase", data_provider_phase.phase_id,
                current_user.user_id, notes=request_body.notes, request=request
            )
            
            processing_time = round((time.time() - start_time) * 1000)
            
            return {
                "success": True,
                "message": "Data provider identification phase started successfully",
                "phase_id": data_provider_phase.phase_id,
                "cycle_id": cycle_id,
                "report_id": report_id,
                "started_at": data_provider_phase.actual_start_date,
                "processing_time_ms": processing_time
            }

        # Create data provider phase workflow
        new_phase = WorkflowPhase(
            cycle_id=cycle_id,
            report_id=report_id,
            phase_name='Data Owner Identification',
            status='In Progress',
            state='In Progress',
            actual_start_date=datetime.utcnow(),
            started_by=current_user.user_id,
            planned_start_date=request_body.planned_start_date,
            planned_end_date=request_body.planned_end_date
        )

        db.add(new_phase)
        
        # Create DataProviderAssignment records for non-primary key scoped attributes
        await create_data_provider_assignments(db, cycle_id, report_id, current_user.user_id)
        
        await db.commit()

        # Create audit log
        await create_audit_log(
            db, cycle_id, report_id, "start_data_provider_phase", "WorkflowPhase", new_phase.phase_id,
            current_user.user_id, notes=request_body.notes, request=request
        )

        processing_time = round((time.time() - start_time) * 1000)

        return {
            "success": True,
            "message": "Data provider identification phase started successfully",
            "phase_id": new_phase.phase_id,
            "cycle_id": cycle_id,
            "report_id": report_id,
            "started_at": new_phase.actual_start_date,
            "processing_time_ms": processing_time
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting data provider phase: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start data provider identification phase"
        )

async def _get_data_provider_phase_status_internal(
    cycle_id: int,
    report_id: int,
    db: AsyncSession
) -> DataProviderPhaseStatus:
    """Internal helper function to get data provider phase status without permission checks"""
    try:
        logger.info(f"Starting status check for cycle_id={cycle_id}, report_id={report_id}")
        
        # Get attributes that need data provider assignment (only scoped non-primary key attributes)
        try:
            logger.info("Querying scoped attributes...")
            # First get primary key attributes
            primary_key_attributes = await db.execute(
                select(ReportAttribute)
                .where(and_(
                    ReportAttribute.cycle_id == cycle_id,
                    ReportAttribute.report_id == report_id,
                    ReportAttribute.is_primary_key == True
                ))
            )
            primary_key_attributes = primary_key_attributes.scalars().all()
            
            # Then get attributes selected for scoping (final_scoping=True)
            scoped_attributes = await db.execute(
                select(ReportAttribute)
                .join(TesterScopingDecision, ReportAttribute.attribute_id == TesterScopingDecision.attribute_id)
                .where(and_(
                    ReportAttribute.cycle_id == cycle_id,
                    ReportAttribute.report_id == report_id,
                    TesterScopingDecision.cycle_id == cycle_id,
                    TesterScopingDecision.report_id == report_id,
                    TesterScopingDecision.final_scoping == True,
                    ReportAttribute.is_primary_key == False  # Exclude primary keys (already included above)
                ))
            )
            scoped_attributes = scoped_attributes.scalars().all()
            
            # Combine both lists
            attributes = list(primary_key_attributes) + list(scoped_attributes)
            total_attributes = len(attributes)
            logger.info(f"Found {total_attributes} attributes")
        except Exception as e:
            logger.error(f"Error querying scoped attributes: {str(e)}")
            raise

        # Handle case where no attributes require data provider assignment yet
        if total_attributes == 0:
            try:
                logger.info("No attributes found for data provider phase, checking phase status...")
                # Get phase status
                phase = await db.execute(
                    select(WorkflowPhase)
                    .where(and_(
                        WorkflowPhase.cycle_id == cycle_id,
                        WorkflowPhase.report_id == report_id,
                        WorkflowPhase.phase_name == 'Data Owner Identification'
                    ))
                )
                phase = phase.scalar_one_or_none()
                phase_status = phase.status if phase else "Not Started"
                logger.info(f"Phase status: {phase_status}")

                return DataProviderPhaseStatus(
                    cycle_id=cycle_id,
                    report_id=report_id,
                    phase_status=phase_status,
                    total_attributes=0,
                    attributes_with_lob_assignments=0,
                    attributes_with_data_providers=0,
                    pending_cdo_assignments=0,
                    overdue_assignments=0,
                    can_submit_lob_assignments=True,  # No assignments needed
                    can_complete_phase=True,  # Can complete if no attributes require assignment
                    completion_requirements=["No attributes require data provider assignment yet - complete scoping phase first"]
                )
            except Exception as e:
                logger.error(f"Error in zero attributes case: {str(e)}")
                raise

        try:
            logger.info("Querying overdue assignments...")
            # Get overdue assignments
            current_time = datetime.utcnow()
            overdue_assignments = await db.execute(
                select(DataProviderSLAViolation)
                .where(and_(
                    DataProviderSLAViolation.cycle_id == cycle_id,
                    DataProviderSLAViolation.report_id == report_id,
                    DataProviderSLAViolation.is_resolved == False
                ))
            )
            overdue_assignments = overdue_assignments.scalars().all()
            logger.info(f"Found {len(overdue_assignments)} overdue assignments")
        except Exception as e:
            logger.error(f"Error querying overdue assignments: {str(e)}")
            raise

        try:
            logger.info("Querying data provider assignments...")
            # Get data provider assignments
            data_provider_assignments = await db.execute(
                select(DataProviderAssignment)
                .where(and_(
                    DataProviderAssignment.cycle_id == cycle_id,
                    DataProviderAssignment.report_id == report_id
                ))
            )
            data_provider_assignments = data_provider_assignments.scalars().all()
            logger.info(f"Found {len(data_provider_assignments)} data provider assignments")
        except Exception as e:
            logger.error(f"Error querying data provider assignments: {str(e)}")
            raise

        try:
            logger.info("Calculating metrics...")
            # Calculate metrics - only non-primary key attributes need data provider assignment
            non_pk_attributes = [attr for attr in attributes if not attr.is_primary_key]
            total_non_pk_attributes = len(non_pk_attributes)
            
            # Since we don't use AttributeLOBAssignment anymore, consider all scoped attributes as having LOB assignments
            # LOB assignments are determined from sample data, not explicit assignment records
            attributes_with_lob_assignments = total_non_pk_attributes
            
            # Count attributes that have data providers assigned
            attributes_with_data_providers = len(set(assignment.attribute_id for assignment in data_provider_assignments if assignment.data_provider_id))
            
            # Count assignments that exist but don't have data providers yet
            pending_cdo_assignments = len([a for a in data_provider_assignments if not a.data_provider_id])
            
            # Add any scoped attributes that don't have assignment records yet
            assigned_attribute_ids = set(assignment.attribute_id for assignment in data_provider_assignments)
            non_pk_attribute_ids = set(attr.attribute_id for attr in non_pk_attributes)
            unassigned_attributes = non_pk_attribute_ids - assigned_attribute_ids
            pending_cdo_assignments += len(unassigned_attributes)
            
            overdue_count = len(overdue_assignments)
            logger.info(f"Metrics: Total={total_attributes}, Non-PK={total_non_pk_attributes}, LOB={attributes_with_lob_assignments}, DP={attributes_with_data_providers}, Pending={pending_cdo_assignments}, Overdue={overdue_count}")
        except Exception as e:
            logger.error(f"Error calculating metrics: {str(e)}")
            raise

        try:
            logger.info("Querying phase status...")
            # Get phase status
            phase = await db.execute(
                select(WorkflowPhase)
                .where(and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == 'Data Owner Identification'
                ))
            )
            phase = phase.scalar_one_or_none()
            phase_status = phase.status if phase else "Not Started"
            logger.info(f"Phase status: {phase_status}")
        except Exception as e:
            logger.error(f"Error querying phase status: {str(e)}")
            raise

        try:
            logger.info("Determining completion requirements...")
            # Determine completion requirements - only non-primary key attributes need assignment
            completion_requirements = []
            
            # Since we don't use AttributeLOBAssignment anymore, LOB assignments are always considered complete
            can_submit_lob_assignments = True
            can_complete_phase = attributes_with_data_providers >= total_non_pk_attributes and overdue_count == 0

            if pending_cdo_assignments > 0:
                completion_requirements.append(f"Complete {pending_cdo_assignments} pending CDO assignments")

            if overdue_count > 0:
                completion_requirements.append(f"Resolve {overdue_count} overdue assignments")

            if not completion_requirements:
                completion_requirements.append("All requirements met - ready to complete phase")
            
            logger.info(f"Completion requirements: {completion_requirements}")
        except Exception as e:
            logger.error(f"Error determining completion requirements: {str(e)}")
            raise

        try:
            logger.info("Creating response object...")
            result = DataProviderPhaseStatus(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_status=phase_status,
                total_attributes=total_attributes,
                attributes_with_lob_assignments=attributes_with_lob_assignments,
                attributes_with_data_providers=attributes_with_data_providers,
                pending_cdo_assignments=pending_cdo_assignments,
                overdue_assignments=overdue_count,
                can_submit_lob_assignments=can_submit_lob_assignments,
                can_complete_phase=can_complete_phase,
                completion_requirements=completion_requirements
            )
            logger.info(f"Status check completed successfully")
            return result
        except Exception as e:
            logger.error(f"Error creating response object: {str(e)}")
            raise

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting data provider phase status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get data provider phase status"
        )

@router.get("/{cycle_id}/reports/{report_id}/status", response_model=DataProviderPhaseStatus)
@require_permission("data_provider", "read")
async def get_data_provider_phase_status(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """Get data provider identification phase status"""
    return await _get_data_provider_phase_status_internal(cycle_id, report_id, db)

# DEPRECATED: AttributeLOBAssignment table doesn't exist - entire function commented out
# @router.post("/{cycle_id}/reports/{report_id}/lob-assignments", response_model=dict)
# @require_permission("data_provider", "execute")
# async def submit_lob_assignments(
#     cycle_id: int,
#     report_id: int,
#     request_body: LOBAssignmentSubmission,
#     db: AsyncSession = Depends(get_db),
#     current_user: Any = Depends(get_current_user),
#     request: Request = None
# ):
#     """Submit LOB assignments for scoped attributes"""
#     start_time = time.time()
#
#     try:
#         # Verify all attributes are scoped
#         for assignment in request_body.assignments:
#             attribute = await db.execute(
#                 select(ReportAttribute)
#                 .where(and_(
#                     ReportAttribute.attribute_id == assignment.attribute_id,
#                     ReportAttribute.cycle_id == cycle_id,
#                     ReportAttribute.report_id == report_id,
#                     ReportAttribute.is_scoped == True
#                 ))
#             )
#             attribute = attribute.scalar_one_or_none()
#
#             if not attribute:
#                 raise HTTPException(
#                     status_code=status.HTTP_400_BAD_REQUEST,
#                     detail=f"Attribute {assignment.attribute_id} not found or not scoped"
#                 )
#
#         # Clear existing LOB assignments for this cycle/report
#         await db.execute(
#             delete(AttributeLOBAssignment)
#             .where(and_(
#                 AttributeLOBAssignment.cycle_id == cycle_id,
#                 AttributeLOBAssignment.report_id == report_id
#             ))
#         )
#
#         assignments_created = []
#         current_time = datetime.utcnow()
#
#         # Create new LOB assignments
#         for assignment in request_body.assignments:
#             for lob_id in assignment.lob_ids:
#                 lob_assignment = AttributeLOBAssignment(
#                     cycle_id=cycle_id,
#                     report_id=report_id,
#                     attribute_id=assignment.attribute_id,
#                     lob_id=lob_id,
#                     assigned_by=current_user.user_id,
#                     assigned_at=current_time,
#                     assignment_rationale=assignment.assignment_rationale
#                 )
#                 db.add(lob_assignment)
#                 assignments_created.append(lob_assignment)
#
#         await db.commit()
#
#         # If confirmed, notify CDOs
#         if request_body.confirm_submission:
#             await notify_cdos_for_assignments(db, cycle_id, report_id, current_user.user_id)
#
#         # Create audit log
#         await create_audit_log(
#             db, cycle_id, report_id, "submit_lob_assignments", "AttributeLOBAssignment", None,
#             current_user.user_id,
#             new_values={"assignments_count": len(assignments_created), "confirmed": request_body.confirm_submission},
#             notes=request_body.submission_notes, request=request
#         )
#
#         processing_time = round((time.time() - start_time) * 1000)
#
#         return {
#             "success": True,
#             "message": f"LOB assignments submitted successfully. {len(assignments_created)} assignments created.",
#             "assignments_created": len(assignments_created),
#             "cdo_notifications_sent": request_body.confirm_submission,
#             "processing_time_ms": processing_time
#         }
#
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Error submitting LOB assignments: {str(e)}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Failed to submit LOB assignments"
#         )

# DEPRECATED: AttributeLOBAssignment table doesn't exist - function commented out
# async def notify_cdos_for_assignments(db: AsyncSession, cycle_id: int, report_id: int, notified_by: int):
#     """Send notifications to CDOs for data provider assignments"""
#     try:
#         # Get unique LOBs from assignments
#         lob_assignments = await db.execute(
#             select(AttributeLOBAssignment.lob_id)
#             .where(and_(
#                 AttributeLOBAssignment.cycle_id == cycle_id,
#                 AttributeLOBAssignment.report_id == report_id
#             ))
#             .distinct()
#         )
#         unique_lob_ids = lob_assignments.scalars().all()
#
#         # Get CDOs for each LOB
#         for lob_id in unique_lob_ids:
#             cdos = await db.execute(
#                 select(User)
#                 .where(and_(
#                     User.lob_id == lob_id,
#                     User.role == 'CDO',
#                     User.is_active == True
#                 ))
#             )
#             cdos = cdos.scalars().all()
#
#             # Get attributes for this LOB
#             attributes = await db.execute(
#                 select(ReportAttribute)
#                 .join(AttributeLOBAssignment, ReportAttribute.attribute_id == AttributeLOBAssignment.attribute_id)
#                 .where(and_(
#                     AttributeLOBAssignment.cycle_id == cycle_id,
#                     AttributeLOBAssignment.report_id == report_id,
#                     AttributeLOBAssignment.lob_id == lob_id
#                 ))
#             )
#             attributes = attributes.scalars().all()

            for cdo in cdos:
                # Create notification
                current_time = datetime.utcnow()
                deadline = current_time + timedelta(hours=24)  # 24-hour SLA

                notification = CDONotification(
                    cycle_id=cycle_id,
                    report_id=report_id,
                    cdo_id=cdo.user_id,
                    lob_id=lob_id,
                    notification_sent_at=current_time,
                    assignment_deadline=deadline,
                    sla_hours=24,
                    notification_data={
                        "attributes": [
                            {
                                "attribute_id": attr.attribute_id,
                                "attribute_name": attr.attribute_name,
                                "description": attr.description
                            } for attr in attributes
                        ],
                        "notified_by": notified_by
                    }
                )
                db.add(notification)

        await db.commit()

    except Exception as e:
        logger.error(f"Error notifying CDOs: {str(e)}")
        raise

@router.get("/{cycle_id}/reports/{report_id}/historical-assignments", response_model=HistoricalAssignmentResponse)
@require_permission("data_provider", "read")
async def get_historical_assignments(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """Get historical data provider assignment suggestions"""
    try:
        # Get report name for historical lookup
        report = await db.execute(
            select(Report)
            .where(Report.report_id == report_id)
        )
        report = report.scalar_one_or_none()

        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )

        # Get scoped attributes for this cycle/report
        scoped_attributes = await db.execute(
            select(ReportAttribute)
            .where(and_(
                ReportAttribute.cycle_id == cycle_id,
                ReportAttribute.report_id == report_id,
                ReportAttribute.is_scoped == True
            ))
        )
        scoped_attributes = scoped_attributes.scalars().all()

        suggestions = []

        # For each scoped attribute, find historical assignments
        for attribute in scoped_attributes:
            historical = await db.execute(
                select(HistoricalDataProviderAssignment, User)
                .join(User, HistoricalDataProviderAssignment.data_provider_id == User.user_id)
                .where(and_(
                    HistoricalDataProviderAssignment.report_name == report.report_name,
                    HistoricalDataProviderAssignment.attribute_name == attribute.attribute_name
                ))
                .order_by(HistoricalDataProviderAssignment.assigned_at.desc())
                .limit(3)  # Top 3 most recent assignments
            )
            historical = historical.all()

            for hist_assignment, data_provider in historical:
                # Calculate assignment frequency
                frequency = await db.execute(
                    select(func.count(HistoricalDataProviderAssignment.history_id))
                    .where(and_(
                        HistoricalDataProviderAssignment.report_name == report.report_name,
                        HistoricalDataProviderAssignment.attribute_name == attribute.attribute_name,
                        HistoricalDataProviderAssignment.data_provider_id == hist_assignment.data_provider_id
                    ))
                )
                frequency = frequency.scalar() or 0

                # Calculate success rate
                success_rate = hist_assignment.success_rating or 0.8  # Default 80% if not tracked

                suggestions.append({
                    "attribute_name": attribute.attribute_name,
                    "data_provider_id": hist_assignment.data_provider_id,
                    "data_provider_name": data_provider.full_name,
                    "last_assigned_date": hist_assignment.assigned_at,
                    "assignment_frequency": frequency,
                    "success_rate": success_rate
                })

        return HistoricalAssignmentResponse(
            cycle_id=cycle_id,
            report_id=report_id,
            suggestions=suggestions,
            total_suggestions=len(suggestions)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting historical assignments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get historical assignments"
        )

# CDO assignments, SLA monitoring, escalation, and phase completion endpoints

@router.get("/{cycle_id}/reports/{report_id}/my-assignments", response_model=List[Dict[str, Any]])
@require_permission("data_provider", "read")
async def get_cdo_assignments(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """Get data provider assignments made by the current CDO"""
    try:
        # Verify user is a CDO
        if not current_user.is_cdo:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CDO role required"
            )

        # Get assignments made by this CDO
        assignments = await db.execute(
            select(DataProviderAssignment, ReportAttribute, User, LOB)
            .join(ReportAttribute, DataProviderAssignment.attribute_id == ReportAttribute.attribute_id)
            .join(User, DataProviderAssignment.data_provider_id == User.user_id)
            .join(LOB, DataProviderAssignment.lob_id == LOB.lob_id)
            .where(and_(
                DataProviderAssignment.cycle_id == cycle_id,
                DataProviderAssignment.report_id == report_id,
                DataProviderAssignment.assigned_by == current_user.user_id
            ))
            .order_by(DataProviderAssignment.assigned_at.desc())
        )
        assignments = assignments.all()

        assignment_list = []
        for dp_assignment, attribute, data_provider, lob in assignments:
            assignment_list.append({
                "assignment_id": dp_assignment.assignment_id,
                "attribute_id": attribute.attribute_id,
                "attribute_name": attribute.attribute_name,
                "attribute_description": attribute.description,
                "data_provider_id": data_provider.user_id,
                "data_provider_name": f"{data_provider.first_name} {data_provider.last_name}",
                "data_provider_email": data_provider.email,
                "lob_name": lob.lob_name,
                "assigned_at": dp_assignment.assigned_at,
                "status": dp_assignment.status,
                "cycle_id": cycle_id,
                "report_id": report_id
            })

        return assignment_list

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting CDO assignments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get CDO assignments"
        )

@router.get("/cdo/all-assignments", response_model=List[Dict[str, Any]])
@require_permission("data_provider", "read")
async def get_all_cdo_assignments(
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """Get all data provider assignments made by the current CDO across all cycles"""
    try:
        # Verify user is a CDO
        if not current_user.is_cdo:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CDO role required"
            )

        # Get all assignments made by this CDO across all cycles
        assignments = await db.execute(
            select(
                DataProviderAssignment, 
                ReportAttribute, 
                User, 
                LOB,
                TestCycle,
                Report
            )
            .join(ReportAttribute, DataProviderAssignment.attribute_id == ReportAttribute.attribute_id)
            .join(User, DataProviderAssignment.data_provider_id == User.user_id)
            .join(LOB, DataProviderAssignment.lob_id == LOB.lob_id)
            .join(TestCycle, DataProviderAssignment.cycle_id == TestCycle.cycle_id)
            .join(Report, DataProviderAssignment.report_id == Report.report_id)
            .where(DataProviderAssignment.assigned_by == current_user.user_id)
            .order_by(DataProviderAssignment.assigned_at.desc())
        )
        assignments = assignments.all()

        assignment_list = []
        for dp_assignment, attribute, data_provider, lob, cycle, report in assignments:
            assignment_list.append({
                "assignment_id": dp_assignment.assignment_id,
                "cycle_id": dp_assignment.cycle_id,
                "cycle_name": cycle.cycle_name,
                "report_id": dp_assignment.report_id,
                "report_name": report.report_name,
                "attribute_id": attribute.attribute_id,
                "attribute_name": attribute.attribute_name,
                "attribute_description": attribute.description,
                "data_provider_id": data_provider.user_id,
                "data_provider_name": f"{data_provider.first_name} {data_provider.last_name}",
                "data_provider_email": data_provider.email,
                "lob_name": lob.lob_name,
                "assigned_at": dp_assignment.assigned_at,
                "status": dp_assignment.status
            })

        return assignment_list

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting all CDO assignments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get CDO assignments"
        )

@router.get("/cdo/dashboard", response_model=Dict[str, Any])
@require_permission("data_provider", "read")
async def get_cdo_dashboard(
    time_filter: str = "last_30_days",
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """Get comprehensive CDO dashboard with workflow status and assignments"""
    try:
        logger.info(f"[CDO Dashboard] Request from user {current_user.user_id} ({current_user.email})")
        logger.info(f"[CDO Dashboard] User role: {current_user.role}, is_cdo: {current_user.is_cdo}")
        
        # Verify user is a CDO
        if not current_user.is_cdo:
            logger.warning(f"[CDO Dashboard] Access denied - user {current_user.user_id} is not a CDO")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CDO role required"
            )

        from app.services.cdo_dashboard_service import get_cdo_dashboard_service
        
        # Get dashboard service
        dashboard_service = get_cdo_dashboard_service()
        
        logger.info(f"[CDO Dashboard] Getting dashboard metrics for user {current_user.user_id} with filter {time_filter}")
        
        # Get comprehensive dashboard data
        dashboard_data = await dashboard_service.get_cdo_dashboard_metrics(
            current_user.user_id,
            db,
            time_filter
        )

        logger.info(f"[CDO Dashboard] Dashboard data keys: {list(dashboard_data.keys())}")
        logger.info(f"[CDO Dashboard] Assignment analytics: {dashboard_data.get('assignment_analytics')}")
        logger.info(f"[CDO Dashboard] LOB overview: {dashboard_data.get('lob_overview')}")
        logger.info(f"[CDO Dashboard] Workflow status count: {len(dashboard_data.get('workflow_status', []))}")
        
        if dashboard_data.get('assignment_analytics', {}).get('recent_activity'):
            logger.info(f"[CDO Dashboard] Recent activity count: {len(dashboard_data['assignment_analytics']['recent_activity'])}")
            for i, activity in enumerate(dashboard_data['assignment_analytics']['recent_activity']):
                logger.info(f"[CDO Dashboard] Activity {i}: {activity}")
        else:
            logger.warning("[CDO Dashboard] No recent activity found in assignment analytics")

        return dashboard_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CDO Dashboard] Error getting CDO dashboard: {str(e)}")
        logger.error(f"[CDO Dashboard] Exception details: {type(e).__name__}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get CDO dashboard"
        )

@router.post("/{cycle_id}/reports/{report_id}/cdo-assignments", response_model=dict)
@require_permission("data_provider", "assign")
async def submit_cdo_assignments(
    cycle_id: int,
    report_id: int,
    request_body: CDOAssignmentSubmission,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user),
    request: Request = None
):
    """CDO submits data provider assignments"""
    start_time = time.time()

    try:
        # Note: CDO notification check removed as notification system is not fully implemented
        # CDOs can submit assignments directly through the assignment interface
        
        assignments_created = []
        current_time = datetime.utcnow()

        for assignment_req in request_body.assignments:
            # Verify attribute exists and is scoped for assignment
            attribute = await db.execute(
                select(ReportAttribute)
                .where(and_(
                    ReportAttribute.cycle_id == cycle_id,
                    ReportAttribute.report_id == report_id,
                    ReportAttribute.attribute_id == assignment_req.attribute_id,
                    ReportAttribute.is_primary_key == False  # Only non-primary key attributes need data providers
                ))
            )
            attribute = attribute.scalar_one_or_none()

            if not attribute:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Attribute {assignment_req.attribute_id} not found or is a primary key"
                )

            # Verify attribute is scoped (has final_scoping=True in tester scoping decisions)
            scoping_decision = await db.execute(
                select(TesterScopingDecision)
                .where(and_(
                    TesterScopingDecision.cycle_id == cycle_id,
                    TesterScopingDecision.report_id == report_id,
                    TesterScopingDecision.attribute_id == assignment_req.attribute_id,
                    TesterScopingDecision.final_scoping == True
                ))
            )
            scoping_decision = scoping_decision.scalar_one_or_none()

            if not scoping_decision:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Attribute {assignment_req.attribute_id} is not scoped for testing"
                )

            # Verify data provider belongs to same LOB
            data_provider = await db.execute(
                select(User)
                .where(and_(
                    User.user_id == assignment_req.data_provider_id,
                    User.lob_id == current_user.lob_id,
                    User.role == 'Data Provider',
                    User.is_active == True
                ))
            )
            data_provider = data_provider.scalar_one_or_none()

            if not data_provider:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Data provider {assignment_req.data_provider_id} not found in your LOB"
                )

            # Check if assignment already exists
            existing_assignment = await db.execute(
                select(DataProviderAssignment)
                .where(and_(
                    DataProviderAssignment.cycle_id == cycle_id,
                    DataProviderAssignment.report_id == report_id,
                    DataProviderAssignment.attribute_id == assignment_req.attribute_id
                ))
            )
            existing_assignment = existing_assignment.scalar_one_or_none()

            if existing_assignment:
                # Update existing assignment
                existing_assignment.data_provider_id = assignment_req.data_provider_id
                existing_assignment.cdo_id = current_user.user_id  # Set CDO ID
                existing_assignment.assigned_by = current_user.user_id
                existing_assignment.assigned_at = current_time
                existing_assignment.status = 'Completed'  # CDO task is complete once data provider is assigned
                assignments_created.append(existing_assignment)
            else:
                # Create new assignment
                new_assignment = DataProviderAssignment(
                    cycle_id=cycle_id,
                    report_id=report_id,
                    attribute_id=assignment_req.attribute_id,
                    lob_id=current_user.lob_id,
                    cdo_id=current_user.user_id,  # Set CDO ID
                    data_provider_id=assignment_req.data_provider_id,
                    assigned_by=current_user.user_id,
                    assigned_at=current_time,
                    status='Completed'  # CDO task is complete once data provider is assigned
                )
                db.add(new_assignment)
                assignments_created.append(new_assignment)

            # Record historical assignment
            if assignment_req.use_historical_assignment:
                # Get report and attribute names
                report = await db.execute(select(Report).where(Report.report_id == report_id))
                report = report.scalar_one()

                attribute = await db.execute(select(ReportAttribute).where(ReportAttribute.attribute_id == assignment_req.attribute_id))
                attribute = attribute.scalar_one()

                historical_assignment = HistoricalDataProviderAssignment(
                    report_name=report.report_name,
                    attribute_name=attribute.attribute_name,
                    data_provider_id=assignment_req.data_provider_id,
                    assigned_by=current_user.user_id,
                    cycle_id=cycle_id,
                    assigned_at=current_time,
                    completion_status='Assigned',
                    notes=assignment_req.assignment_notes
                )
                db.add(historical_assignment)

        await db.commit()

        # Create audit log
        await create_audit_log(
            db, cycle_id, report_id, "submit_cdo_assignments", "DataProviderAssignment", None,
            current_user.user_id,
            new_values={"assignments_count": len(assignments_created)},
            notes=request_body.submission_notes, request=request
        )

        processing_time = round((time.time() - start_time) * 1000)

        return {
            "success": True,
            "message": f"Data provider assignments submitted successfully. {len(assignments_created)} assignments completed.",
            "assignments_completed": len(assignments_created),
            "processing_time_ms": processing_time
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting CDO assignments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit CDO assignments"
        )

@router.get("/{cycle_id}/reports/{report_id}/assignment-matrix", response_model=AssignmentMatrix)
@require_permission("data_provider", "read")
async def get_assignment_matrix(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """Get complete assignment matrix for data provider phase"""
    try:
        # Get attributes for data provider phase: 
        # 1. Primary key attributes (displayed but marked as completed)
        # 2. Attributes selected for scoping (final_scoping=True in tester scoping decisions)
        
        # First get primary key attributes
        primary_key_attributes = await db.execute(
            select(ReportAttribute)
            .where(and_(
                ReportAttribute.cycle_id == cycle_id,
                ReportAttribute.report_id == report_id,
                ReportAttribute.is_primary_key == True
            ))
        )
        primary_key_attributes = primary_key_attributes.scalars().all()
        
        # Then get attributes selected for scoping (final_scoping=True)
        scoped_attributes = await db.execute(
            select(ReportAttribute)
            .join(TesterScopingDecision, ReportAttribute.attribute_id == TesterScopingDecision.attribute_id)
            .where(and_(
                ReportAttribute.cycle_id == cycle_id,
                ReportAttribute.report_id == report_id,
                TesterScopingDecision.cycle_id == cycle_id,
                TesterScopingDecision.report_id == report_id,
                TesterScopingDecision.final_scoping == True,
                ReportAttribute.is_primary_key == False  # Exclude primary keys (already included above)
            ))
        )
        scoped_attributes = scoped_attributes.scalars().all()
        
        # Combine both lists
        attributes = list(primary_key_attributes) + list(scoped_attributes)

        assignment_statuses = []
        lob_summary = {}
        cdo_summary = {}
        status_summary = {"Assigned": 0, "In Progress": 0, "Completed": 0, "Overdue": 0}

        for attribute in attributes:
            # Get LOB assignments from approved sample records that contain this attribute
            # This reflects the actual LOBs involved based on sample data
            sample_lobs = await db.execute(
                select(SampleRecord.data_source_info)
                .join(SampleSet, SampleRecord.set_id == SampleSet.set_id)
                .where(and_(
                    SampleSet.cycle_id == cycle_id,
                    SampleSet.report_id == report_id,
                    SampleSet.status == 'Approved',  # Only approved sample sets
                    SampleRecord.sample_data.has_key(attribute.attribute_name)  # CycleReportSampleSelectionSamples contains this attribute
                ))
            )
            sample_lobs = sample_lobs.scalars().all()

            # Extract unique LOB names from sample records
            unique_lob_names = set()
            for data_source_info in sample_lobs:
                if data_source_info and 'lob_assignments' in data_source_info:
                    lob_list = data_source_info['lob_assignments']
                    if isinstance(lob_list, list):
                        unique_lob_names.update(lob_list)

            # Convert LOB names to LOB objects
            assigned_lobs = []
            if unique_lob_names:
                lob_objects = await db.execute(
                    select(LOB)
                    .where(LOB.lob_name.in_(list(unique_lob_names)))
                )
                lob_objects = lob_objects.scalars().all()
                assigned_lobs = [
                    {"lob_id": lob.lob_id, "lob_name": lob.lob_name}
                    for lob in lob_objects
                ]

            # Primary key attributes don't need data provider assignment but should show LOBs
            if attribute.is_primary_key:
                assignment_status = AttributeAssignmentStatus(
                    attribute_id=attribute.attribute_id,
                    attribute_name=attribute.attribute_name,
                    is_primary_key=True,  # Set primary key flag
                    assigned_lobs=assigned_lobs,  # Show LOBs for primary keys too
                    data_provider_id=None,
                    data_provider_name="N/A - Primary Key",
                    assigned_by=None,
                    assigned_at=None,
                    status=AssignmentStatus.COMPLETED,  # Primary keys are considered complete
                    assignment_notes="Primary key attribute - no data provider needed",
                    is_overdue=False,
                    sla_deadline=None,
                    hours_remaining=None
                )
                assignment_statuses.append(assignment_status)
                status_summary[AssignmentStatus.COMPLETED.value] += 1
                
                # Update LOB summary for primary keys too
                for lob in assigned_lobs:
                    lob_name = lob["lob_name"]
                    lob_summary[lob_name] = lob_summary.get(lob_name, 0) + 1
                continue

            # For scoped non-primary key attributes, get data provider assignment
            data_provider_assignment = await db.execute(
                select(DataProviderAssignment, User)
                .outerjoin(User, DataProviderAssignment.data_provider_id == User.user_id)
                .where(and_(
                    DataProviderAssignment.cycle_id == cycle_id,
                    DataProviderAssignment.report_id == report_id,
                    DataProviderAssignment.attribute_id == attribute.attribute_id
                ))
            )
            data_provider_assignment = data_provider_assignment.first()

            # Check for SLA violations
            sla_violation = await db.execute(
                select(DataProviderSLAViolation)
                .where(and_(
                    DataProviderSLAViolation.cycle_id == cycle_id,
                    DataProviderSLAViolation.report_id == report_id,
                    DataProviderSLAViolation.attribute_id == attribute.attribute_id,
                    DataProviderSLAViolation.is_resolved == False
                ))
            )
            sla_violation = sla_violation.scalar_one_or_none()

            # Determine status for scoped attributes
            if data_provider_assignment:
                dp_assignment, data_provider = data_provider_assignment
                if dp_assignment.data_provider_id:
                    # If a data provider is assigned, the CDO's task is complete
                    assignment_status_val = AssignmentStatus.COMPLETED
                else:
                    # If no data provider assigned yet, it's still assigned to CDO
                    assignment_status_val = AssignmentStatus.ASSIGNED
            else:
                # No assignment record exists yet
                assignment_status_val = AssignmentStatus.ASSIGNED
            
            is_overdue = sla_violation is not None

            assignment_status = AttributeAssignmentStatus(
                attribute_id=attribute.attribute_id,
                attribute_name=attribute.attribute_name,
                is_primary_key=False,  # Non-primary key attributes
                assigned_lobs=assigned_lobs,
                data_provider_id=data_provider_assignment[0].data_provider_id if data_provider_assignment and data_provider_assignment[0].data_provider_id else None,
                data_provider_name=data_provider_assignment[1].full_name if data_provider_assignment and data_provider_assignment[1] else None,
                assigned_by=data_provider_assignment[0].assigned_by if data_provider_assignment else None,
                assigned_at=data_provider_assignment[0].assigned_at if data_provider_assignment else None,
                status=assignment_status_val,
                assignment_notes=None,  # Can be added if needed
                is_overdue=is_overdue,
                sla_deadline=None,  # Remove SLA deadline as requested
                hours_remaining=None  # Remove hours remaining as requested
            )

            assignment_statuses.append(assignment_status)

            # Update summaries (for scoped non-primary key attributes)
            for lob in assigned_lobs:
                lob_name = lob["lob_name"]
                lob_summary[lob_name] = lob_summary.get(lob_name, 0) + 1

            status_summary[assignment_status_val.value] += 1

        # Get all LOBs involved in this cycle/report for CDO summary
        all_lobs = await db.execute(
            select(LOB)
            .join(User, LOB.lob_id == User.lob_id)
            .where(User.role == 'CDO')
        )
        all_lobs = all_lobs.scalars().all()
        
        # Get available data providers for CDO assignment interface
        data_providers = await db.execute(
            select(User, LOB)
            .join(LOB, User.lob_id == LOB.lob_id)
            .where(and_(
                User.role == 'Data Provider',
                User.is_active == True
            ))
        )
        data_providers = data_providers.all()
        
        # Format data providers for response
        data_provider_list = []
        for user, lob in data_providers:
            data_provider_list.append({
                "user_id": user.user_id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "lob_name": lob.lob_name
            })

        return AssignmentMatrix(
            cycle_id=cycle_id,
            report_id=report_id,
            assignments=assignment_statuses,
            data_providers=data_provider_list,
            lob_summary=lob_summary,
            cdo_summary=cdo_summary,
            status_summary=status_summary
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting assignment matrix: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get assignment matrix"
        )

@router.get("/{cycle_id}/reports/{report_id}/sla-violations", response_model=List[SLAViolation])
@require_permission("data_provider", "read")
async def get_sla_violations(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """Get current SLA violations for escalation"""
    try:
        violations = await db.execute(
            select(DataProviderSLAViolation, ReportAttribute, User, LOB)
            .join(ReportAttribute, DataProviderSLAViolation.attribute_id == ReportAttribute.attribute_id)
            .join(User, DataProviderSLAViolation.cdo_id == User.user_id)
            .join(LOB, User.lob_id == LOB.lob_id)
            .where(and_(
                DataProviderSLAViolation.cycle_id == cycle_id,
                DataProviderSLAViolation.report_id == report_id,
                DataProviderSLAViolation.is_resolved == False
            ))
            .order_by(DataProviderSLAViolation.hours_overdue.desc())
        )
        violations = violations.all()

        sla_violations = []
        for violation, attribute, cdo, lob in violations:
            sla_violations.append(SLAViolation(
                assignment_id=violation.assignment_id,
                attribute_id=violation.attribute_id,
                attribute_name=attribute.attribute_name,
                cdo_id=violation.cdo_id,
                cdo_name=cdo.full_name,
                lob_name=lob.lob_name,
                assignment_deadline=violation.original_deadline,
                hours_overdue=violation.hours_overdue,
                escalation_level=EscalationLevel(violation.escalation_level)
            ))

        return sla_violations

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting SLA violations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get SLA violations"
        )

@router.post("/{cycle_id}/reports/{report_id}/send-escalation", response_model=EscalationEmailResponse)
@require_permission("data_provider", "escalate")
async def send_escalation_email(
    cycle_id: int,
    report_id: int,
    request_body: EscalationEmailRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user),
    request: Request = None
):
    """Send escalation email for SLA violations"""
    start_time = time.time()

    try:
        # Get violations to escalate
        violations = await db.execute(
            select(DataProviderSLAViolation, ReportAttribute, User)
            .join(ReportAttribute, DataProviderSLAViolation.attribute_id == ReportAttribute.attribute_id)
            .join(User, DataProviderSLAViolation.cdo_id == User.user_id)
            .where(DataProviderSLAViolation.violation_id.in_(request_body.violation_ids))
        )
        violations = violations.all()

        if not violations:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No violations found"
            )

        # Get report owner for escalation
        report = await db.execute(
            select(Report, User)
            .join(User, Report.report_owner_id == User.user_id)
            .where(Report.report_id == report_id)
        )
        report, report_owner = report.first()

        recipients = []
        cc_recipients = []

        if request_body.send_to_report_owner:
            recipients.append(report_owner.email)

        if request_body.cc_cdo:
            # Add unique CDO emails to CC
            cdo_emails = list(set([cdo.email for _, _, cdo in violations]))
            cc_recipients.extend(cdo_emails)

        # Simulate email sending (in production, integrate with email service)
        email_subject = f"SLA Violation Escalation - {report.report_name} - Level {request_body.escalation_level.value}"
        email_body = f"""
        SLA Violation Escalation Notice

        Report: {report.report_name}
        Cycle ID: {cycle_id}
        Escalation Level: {request_body.escalation_level.value}

        Violations:
        {chr(10).join([f"- {attr.attribute_name} (CDO: {cdo.full_name}, {violation.hours_overdue:.1f}h overdue)" for violation, attr, cdo in violations])}

        {request_body.custom_message or 'Please address these overdue assignments urgently.'}

        Sent by: {current_user.full_name}
        """

        # Create escalation log
        escalation_log = DataProviderEscalationLog(
            cycle_id=cycle_id,
            report_id=report_id,
            violation_ids=request_body.violation_ids,
            escalation_level=request_body.escalation_level.value,
            sent_by=current_user.user_id,
            sent_to=recipients,
            cc_recipients=cc_recipients,
            email_subject=email_subject,
            email_body=email_body,
            sent_at=datetime.utcnow(),
            delivery_status='Sent',
            custom_message=request_body.custom_message
        )
        db.add(escalation_log)

        # Update violation escalation levels
        for violation, _, _ in violations:
            violation.escalation_level = request_body.escalation_level.value
            violation.last_escalation_at = datetime.utcnow()

        await db.commit()

        # Create audit log
        await create_audit_log(
            db, cycle_id, report_id, "send_escalation_email", "DataProviderEscalationLog", escalation_log.email_id,
            current_user.user_id,
            new_values={"violations_count": len(violations), "escalation_level": request_body.escalation_level.value},
            notes=request_body.custom_message, request=request
        )

        processing_time = round((time.time() - start_time) * 1000)

        return EscalationEmailResponse(
            email_sent=True,
            recipients=recipients + cc_recipients,
            violations_escalated=len(violations),
            escalation_level=request_body.escalation_level,
            sent_at=escalation_log.sent_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending escalation email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send escalation email"
        )

@router.post("/{cycle_id}/reports/{report_id}/complete", response_model=dict)
@require_permission("data_provider", "complete")
async def complete_data_provider_phase(
    cycle_id: int,
    report_id: int,
    request_body: DataProviderPhaseComplete,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user),
    request: Request = None
):
    """Complete data provider identification phase"""
    start_time = time.time()

    try:
        # Verify all requirements are met
        status_response = await _get_data_provider_phase_status_internal(cycle_id, report_id, db)

        if not status_response.can_complete_phase:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot complete phase. Requirements: {', '.join(status_response.completion_requirements)}"
            )

        if not request_body.confirm_completion:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Completion must be confirmed"
            )

        # Update workflow phase
        phase = await db.execute(
            select(WorkflowPhase)
            .where(and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == 'Data Owner Identification'
            ))
        )
        phase = phase.scalar_one_or_none()

        if not phase:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Data provider phase not found"
            )

        phase.status = 'Complete'
        phase.completed_at = datetime.utcnow()
        phase.completed_by = current_user.user_id

        await db.commit()

        # Create audit log
        await create_audit_log(
            db, cycle_id, report_id, "complete_data_provider_phase", "WorkflowPhase", phase.phase_id,
            current_user.user_id, notes=request_body.completion_notes, request=request
        )

        processing_time = round((time.time() - start_time) * 1000)

        return {
            "success": True,
            "message": "Data provider identification phase completed successfully",
            "phase_id": phase.phase_id,
            "completed_at": phase.completed_at,
            "total_attributes": status_response.total_attributes,
            "processing_time_ms": processing_time
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing data provider phase: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete data provider phase"
        )

@router.get("/{cycle_id}/reports/{report_id}/audit-log", response_model=DataProviderAssignmentAuditLog)
@require_permission("data_provider", "read")
async def get_data_provider_audit_log(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """Get data provider phase audit log"""
    try:
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

        audit_log_entries = []
        for audit_log, user in audit_entries:
            audit_log_entries.append({
                "assignment_id": audit_log.entity_id or 0,
                "attribute_id": 0,  # Can be extracted from new_values if needed
                "action": audit_log.action,
                "performed_by": audit_log.performed_by,
                "performed_at": audit_log.performed_at,
                "old_values": audit_log.old_values,
                "new_values": audit_log.new_values,
                "notes": audit_log.notes
            })

        return DataProviderAssignmentAuditLog(
            cycle_id=cycle_id,
            report_id=report_id,
            audit_entries=audit_log_entries,
            total_entries=len(audit_log_entries)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting audit log: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get audit log"
        )

async def create_data_provider_assignments(
    db: AsyncSession,
    cycle_id: int,
    report_id: int,
    created_by: int
):
    """Create UniversalAssignment records for non-primary key scoped attributes for data executives"""
    try:
        # Get non-primary key scoped attributes that need CDO assignments
        scoped_attributes = await db.execute(
            select(ReportAttribute)
            .join(TesterScopingDecision, ReportAttribute.attribute_id == TesterScopingDecision.attribute_id)
            .where(and_(
                ReportAttribute.cycle_id == cycle_id,
                ReportAttribute.report_id == report_id,
                TesterScopingDecision.cycle_id == cycle_id,
                TesterScopingDecision.report_id == report_id,
                TesterScopingDecision.final_scoping == True,
                ReportAttribute.is_primary_key == False  # Only non-primary keys need CDO assignment
            ))
        )
        scoped_attributes = scoped_attributes.scalars().all()
        
        logger.info(f"Creating UniversalAssignment records for {len(scoped_attributes)} attributes")
        
        # Get phase information
        phase_result = await db.execute(
            select(WorkflowPhase).where(and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == 'Sample Selection'
            ))
        )
        sample_phase = phase_result.scalar_one_or_none()
        
        if not sample_phase:
            logger.warning("Sample Selection phase not found")
            return
        
        # Get LOB assignments from sample selection phase data
        all_lobs_in_samples = set()
        if sample_phase.phase_data and 'cycle_report_sample_selection_samples' in sample_phase.phase_data:
            samples = sample_phase.phase_data['cycle_report_sample_selection_samples']
            for sample in samples:
                if sample.get('tester_decision') == 'approved' and sample.get('lob_assignment'):
                    all_lobs_in_samples.add(sample['lob_assignment'])
        
        if not all_lobs_in_samples:
            logger.warning("No LOB assignments found in approved samples")
            return
        
        logger.info(f"Found LOBs in samples: {list(all_lobs_in_samples)}")
        
        # Get LOB and CDO information
        from app.models.lob import LOB
        from app.models.user import User
        
        all_lobs = await db.execute(select(LOB))
        all_lobs = {lob.lob_name: lob for lob in all_lobs.scalars().all()}
        
        # Get Data Executives (CDO role has been renamed to Data Executive)
        all_data_executives = await db.execute(
            select(User).where(User.role.in_(['Data Executive', 'CDO']))
        )
        all_data_executives = {de.lob_id: de for de in all_data_executives.scalars().all()}
        
        # Get Data Owner Identification phase
        doi_phase_result = await db.execute(
            select(WorkflowPhase).where(and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == 'Data Owner Identification'
            ))
        )
        doi_phase = doi_phase_result.scalar_one_or_none()
        
        if not doi_phase:
            logger.error("Data Owner Identification phase not found")
            return
        
        # Create universal assignments for each attribute and LOB combination
        from app.models.universal_assignment import UniversalAssignment
        assignment_count = 0
        
        for attribute in scoped_attributes:
            for lob_name in all_lobs_in_samples:
                if lob_name in all_lobs:
                    lob = all_lobs[lob_name]
                    data_executive = all_data_executives.get(lob.lob_id)
                    
                    if data_executive:
                        # Check if assignment already exists
                        existing_assignment = await db.execute(
                            select(UniversalAssignment).where(and_(
                                UniversalAssignment.phase_id == doi_phase.phase_id,
                                UniversalAssignment.assignment_type == 'data_owner_identification',
                                UniversalAssignment.entity_type == 'attribute',
                                UniversalAssignment.entity_id == str(attribute.attribute_id),
                                UniversalAssignment.assigned_to_id == data_executive.user_id
                            ))
                        )
                        existing_assignment = existing_assignment.scalar_one_or_none()
                        
                        if not existing_assignment:
                            # Create new universal assignment
                            assignment = UniversalAssignment(
                                phase_id=doi_phase.phase_id,
                                assignment_type='data_owner_identification',
                                entity_type='attribute',
                                entity_id=str(attribute.attribute_id),
                                assigned_to_id=data_executive.user_id,
                                assigned_by_id=created_by,
                                status='pending',
                                metadata={
                                    'attribute_name': attribute.attribute_name,
                                    'lob_id': lob.lob_id,
                                    'lob_name': lob.lob_name,
                                    'is_primary_key': attribute.is_primary_key
                                }
                            )
                            db.add(assignment)
                            assignment_count += 1
                            logger.info(f"Created assignment for attribute {attribute.attribute_name} (ID: {attribute.attribute_id}), LOB {lob_name} (ID: {lob.lob_id}), Data Executive {data_executive.first_name} {data_executive.last_name} (ID: {data_executive.user_id})")
                        else:
                            logger.info(f"Assignment already exists for attribute {attribute.attribute_name} (ID: {attribute.attribute_id}), LOB {lob_name}")
                    else:
                        logger.warning(f"No Data Executive found for LOB {lob_name} (ID: {lob.lob_id})")
                else:
                    logger.warning(f"LOB '{lob_name}' not found in database")
        
        logger.info(f"Created {assignment_count} UniversalAssignment records successfully")
        
    except Exception as e:
        logger.error(f"Error creating DataProviderAssignment records: {str(e)}")
        raise
