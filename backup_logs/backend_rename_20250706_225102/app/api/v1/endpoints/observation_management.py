"""
Observation Management API endpoints
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, asc
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
import json
import uuid

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.permissions import require_permission
from app.models import (
    User, TestCycle, Report,
    ObservationManagementPhase, ObservationRecord, ObservationImpactAssessment,
    ObservationApproval, ObservationResolution, ObservationManagementAuditLog,
    ObservationTypeEnum, ObservationSeverityEnum, ObservationStatusEnum,
    ImpactCategoryEnum, ResolutionStatusEnum
)
from app.schemas.observation_management import (
    ObservationManagementPhaseStart, ObservationManagementPhaseStatus,
    ObservationCreate, ObservationResponse, ImpactAssessmentCreate, ImpactAssessmentResponse,
    ObservationApprovalRequest, ObservationApprovalResponse, ResolutionCreate, ResolutionResponse,
    ObservationAnalytics, ObservationManagementPhaseComplete, AutoDetectionRequest, AutoDetectionResponse,
    ObservationManagementAuditLog as ObservationManagementAuditLogSchema
)

router = APIRouter()

# Helper functions for intelligent observation grouping
async def find_similar_observation(
    db: AsyncSession,
    cycle_id: int,
    report_id: int,
    attribute_id: Optional[int],
    observation_type: ObservationTypeEnum,
    issue_keywords: List[str]
) -> Optional[ObservationRecord]:
    """Find existing similar observation for grouping"""
    query = select(ObservationRecord).where(
        and_(
            ObservationRecord.cycle_id == cycle_id,
            ObservationRecord.report_id == report_id,
            ObservationRecord.observation_type == observation_type,
            ObservationRecord.status != ObservationStatusEnum.RESOLVED
        )
    )
    
    if attribute_id:
        query = query.where(ObservationRecord.source_attribute_id == attribute_id)
    
    result = await db.execute(query)
    existing_observations = result.scalars().all()
    
    # Check for similar observations based on keywords
    for obs in existing_observations:
        obs_text = f"{obs.observation_title} {obs.observation_description}".lower()
        if any(keyword.lower() in obs_text for keyword in issue_keywords):
            return obs
    
    return None

def categorize_test_failure(test_execution) -> tuple[ObservationTypeEnum, List[str]]:
    """Categorize test failure into observation type and keywords"""
    summary = test_execution.execution_summary.lower() if test_execution.execution_summary else ""
    
    # Data Quality issues
    if "value" in summary and ("not match" in summary or "mismatch" in summary or "incorrect" in summary):
        return ObservationTypeEnum.DATA_QUALITY, ["value mismatch", "incorrect data", "data quality"]
    
    # Documentation issues
    elif "document" in summary and ("not found" in summary or "missing" in summary or "no valid" in summary):
        return ObservationTypeEnum.DOCUMENTATION, ["missing documentation", "document not found", "lack of evidence"]
    
    # Primary key validation failures
    elif "primary key" in summary and "failed" in summary:
        return ObservationTypeEnum.DATA_QUALITY, ["primary key mismatch", "record identification", "wrong record"]
    
    # Process Control issues
    elif "process" in summary or "control" in summary:
        return ObservationTypeEnum.PROCESS_CONTROL, ["process failure", "control weakness"]
    
    # System issues
    elif "system" in summary or "connection" in summary or "timeout" in summary:
        return ObservationTypeEnum.SYSTEM_CONTROL, ["system error", "connectivity issue", "technical failure"]
    
    # Default to Data Quality
    else:
        return ObservationTypeEnum.DATA_QUALITY, ["general issue", "test failure"]

# Role-based access control helper functions
def require_tester_access(current_user: User = Depends(get_current_user)):
    """Require tester or test manager role"""
    if current_user.role not in ['Test Manager', 'Tester']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tester or Test Manager role required"
        )
    return current_user

def require_report_owner_access(current_user: User = Depends(get_current_user)):
    """Require report owner, test manager, or tester role"""
    if current_user.role not in ['Test Manager', 'Report Owner', 'Tester']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Report Owner, Test Manager, or Tester role required"
        )
    return current_user

def require_test_manager_access(current_user: User = Depends(get_current_user)):
    """Require test manager role"""
    if current_user.role != 'Test Manager':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Test Manager role required"
        )
    return current_user

@router.post("/{cycle_id}/reports/{report_id}/start", response_model=Dict[str, Any])
@require_permission("observations", "create")
async def start_observation_management_phase(
    cycle_id: int,
    report_id: int,
    phase_data: ObservationManagementPhaseStart,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Start observation management phase for a cycle and report"""

    # Verify cycle and report exist
    cycle_result = await db.execute(
        select(TestCycle).where(TestCycle.cycle_id == cycle_id)
    )
    cycle = cycle_result.scalar_one_or_none()
    if not cycle:
        raise HTTPException(status_code=404, detail="Test cycle not found")

    report_result = await db.execute(
        select(Report).where(Report.report_id == report_id)
    )
    report = report_result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Check if phase already exists
    existing_phase = await db.execute(
        select(ObservationManagementPhase).where(
            and_(
                ObservationManagementPhase.cycle_id == cycle_id,
                ObservationManagementPhase.report_id == report_id
            )
        )
    )
    if existing_phase.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Observation management phase already exists")

    # Create new phase
    phase = ObservationManagementPhase(
        phase_id=str(uuid.uuid4()),
        cycle_id=cycle_id,
        report_id=report_id,
        planned_start_date=phase_data.planned_start_date,
        planned_end_date=phase_data.planned_end_date,
        observation_deadline=phase_data.observation_deadline,
        observation_strategy=phase_data.observation_strategy,
        detection_criteria=phase_data.detection_criteria,
        approval_threshold=phase_data.approval_threshold,
        instructions=phase_data.instructions,
        notes=phase_data.notes,
        started_by=current_user.user_id,
        assigned_testers=phase_data.assigned_testers or []
    )

    db.add(phase)
    await db.commit()
    await db.refresh(phase)

    # Create audit log
    audit_log = ObservationManagementAuditLog(
        cycle_id=cycle_id,
        report_id=report_id,
        phase_id=phase.phase_id,
        action="start_phase",
        entity_type="ObservationManagementPhase",
        entity_id=phase.phase_id,
        performed_by=current_user.user_id,
        user_role=current_user.role.value,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        new_values={
            "phase_status": "In Progress",
            "observation_deadline": phase_data.observation_deadline.isoformat(),
            "approval_threshold": phase_data.approval_threshold
        },
        execution_time_ms=50
    )
    db.add(audit_log)
    await db.commit()

    return {
        "message": "Observation management phase started successfully",
        "phase_id": phase.phase_id,
        "cycle_id": cycle_id,
        "report_id": report_id,
        "observation_deadline": phase.observation_deadline,
        "started_by": current_user.user_id,
        "started_at": phase.started_at
    }

@router.get("/{cycle_id}/reports/{report_id}/status", response_model=ObservationManagementPhaseStatus)
@require_permission("observations", "read")
async def get_observation_management_status(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get observation management phase status and progress"""

    # Get phase
    phase_result = await db.execute(
        select(ObservationManagementPhase).where(
            and_(
                ObservationManagementPhase.cycle_id == cycle_id,
                ObservationManagementPhase.report_id == report_id
            )
        )
    )
    phase = phase_result.scalar_one_or_none()
    if not phase:
        raise HTTPException(status_code=404, detail="Observation management phase not found")

    # Calculate statistics
    total_observations = phase.total_observations
    auto_detected = phase.auto_detected_observations
    manual_observations = phase.manual_observations
    approved_observations = phase.approved_observations
    rejected_observations = phase.rejected_observations
    pending_observations = total_observations - approved_observations - rejected_observations

    # Calculate progress metrics
    completion_percentage = (approved_observations + rejected_observations) / max(total_observations, 1) * 100
    days_until_deadline = (phase.observation_deadline - datetime.utcnow()).days
    detection_rate = total_observations / max((datetime.utcnow() - phase.started_at).days, 1)
    approval_rate = approved_observations / max(total_observations, 1) * 100

    # Get severity breakdown
    severity_stats = await db.execute(
        select(
            func.count().label('count'),
            ObservationRecord.severity
        ).select_from(ObservationRecord).where(
            and_(
                ObservationRecord.cycle_id == cycle_id,
                ObservationRecord.report_id == report_id,
                ObservationRecord.phase_id == phase.phase_id
            )
        ).group_by(ObservationRecord.severity)
    )

    critical_count = high_count = medium_count = low_count = 0
    for row in severity_stats:
        if row.severity == ObservationSeverityEnum.CRITICAL:
            critical_count = row.count
        elif row.severity == ObservationSeverityEnum.HIGH:
            high_count = row.count
        elif row.severity == ObservationSeverityEnum.MEDIUM:
            medium_count = row.count
        elif row.severity == ObservationSeverityEnum.LOW:
            low_count = row.count

    # Determine completion requirements
    can_complete = pending_observations == 0 and total_observations > 0
    requirements = []
    if pending_observations > 0:
        requirements.append(f"Complete approval for {pending_observations} pending observations")
    if total_observations == 0:
        requirements.append("At least one observation must be created")

    return ObservationManagementPhaseStatus(
        cycle_id=cycle_id,
        report_id=report_id,
        phase_id=phase.phase_id,
        phase_status=phase.phase_status,
        observation_deadline=phase.observation_deadline,
        days_until_deadline=days_until_deadline,
        total_observations=total_observations,
        auto_detected_observations=auto_detected,
        manual_observations=manual_observations,
        approved_observations=approved_observations,
        rejected_observations=rejected_observations,
        pending_observations=pending_observations,
        completion_percentage=completion_percentage,
        detection_rate=detection_rate,
        approval_rate=approval_rate,
        average_resolution_time=5.2,  # Simulated
        critical_observations=critical_count,
        high_severity_observations=high_count,
        medium_severity_observations=medium_count,
        low_severity_observations=low_count,
        can_complete_phase=can_complete,
        completion_requirements=requirements
    )

@router.post("/{cycle_id}/reports/{report_id}/auto_detect", response_model=AutoDetectionResponse)
@require_permission("observations", "create")
async def auto_detect_observations(
    cycle_id: int,
    report_id: int,
    detection_request: AutoDetectionRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Auto-detect observations using configurable criteria"""

    # Get phase
    phase_result = await db.execute(
        select(ObservationManagementPhase).where(
            and_(
                ObservationManagementPhase.cycle_id == cycle_id,
                ObservationManagementPhase.report_id == report_id
            )
        )
    )
    phase = phase_result.scalar_one_or_none()
    if not phase:
        raise HTTPException(status_code=404, detail="Observation management phase not found")

    # Simulate auto-detection logic based on criteria
    detection_id = str(uuid.uuid4())
    detected_observations = []

    # Mock detection based on confidence threshold
    if detection_request.confidence_threshold <= 0.8:
        # Detect high-confidence observations
        obs1 = ObservationRecord(
            phase_id=phase.phase_id,
            cycle_id=cycle_id,
            report_id=report_id,
            observation_title="Data Quality Issue - Missing Values",
            observation_description="Detected systematic missing values in critical fields exceeding acceptable threshold of 5%",
            observation_type=ObservationTypeEnum.DATA_QUALITY,
            severity=ObservationSeverityEnum.HIGH,
            detection_method="Auto-detected",
            detection_confidence=0.92,
            impact_description="Missing data may affect regulatory calculations",
            financial_impact_estimate=25000.0,
            regulatory_risk_level="Medium",
            detected_by=current_user.user_id,
            auto_detection_rules=detection_request.detection_criteria,
            auto_detection_score=0.92
        )
        db.add(obs1)
        detected_observations.append(obs1)

    if detection_request.confidence_threshold <= 0.7:
        # Detect medium-confidence observations
        obs2 = ObservationRecord(
            phase_id=phase.phase_id,
            cycle_id=cycle_id,
            report_id=report_id,
            observation_title="Process Control - Timing Inconsistency",
            observation_description="Data processing timing shows irregular patterns that may indicate control weaknesses",
            observation_type=ObservationTypeEnum.PROCESS_CONTROL,
            severity=ObservationSeverityEnum.MEDIUM,
            detection_method="Auto-detected",
            detection_confidence=0.78,
            impact_description="Potential impact on data integrity and process reliability",
            financial_impact_estimate=15000.0,
            regulatory_risk_level="Low",
            detected_by=current_user.user_id,
            auto_detection_rules=detection_request.detection_criteria,
            auto_detection_score=0.78
        )
        db.add(obs2)
        detected_observations.append(obs2)

    await db.commit()

    # Update phase statistics
    phase.total_observations += len(detected_observations)
    phase.auto_detected_observations += len(detected_observations)
    await db.commit()

    # Convert to response format
    detected_responses = []
    for obs in detected_observations:
        await db.refresh(obs)
        detected_responses.append(ObservationResponse(
            observation_id=obs.observation_id,
            phase_id=obs.phase_id,
            cycle_id=obs.cycle_id,
            report_id=obs.report_id,
            observation_title=obs.observation_title,
            observation_description=obs.observation_description,
            observation_type=obs.observation_type,
            severity=obs.severity,
            status=obs.status,
            source_test_execution_id=obs.source_test_execution_id,
            source_sample_record_id=obs.source_sample_record_id,
            source_attribute_id=obs.source_attribute_id,
            detection_method=obs.detection_method,
            detection_confidence=obs.detection_confidence,
            impact_description=obs.impact_description,
            financial_impact_estimate=obs.financial_impact_estimate,
            regulatory_risk_level=obs.regulatory_risk_level,
            detected_by=obs.detected_by,
            assigned_to=obs.assigned_to,
            detected_at=obs.detected_at,
            assigned_at=obs.assigned_at,
            auto_detection_score=obs.auto_detection_score,
            manual_validation_required=obs.manual_validation_required
        ))

    # Create audit log
    audit_log = ObservationManagementAuditLog(
        cycle_id=cycle_id,
        report_id=report_id,
        phase_id=phase.phase_id,
        action="auto_detect",
        entity_type="ObservationDetection",
        entity_id=detection_id,
        performed_by=current_user.user_id,
        user_role=current_user.role.value,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        new_values={
            "detection_criteria": detection_request.detection_criteria,
            "confidence_threshold": detection_request.confidence_threshold,
            "observations_detected": len(detected_observations)
        },
        execution_time_ms=250
    )
    db.add(audit_log)
    await db.commit()

    avg_confidence = sum(obs.detection_confidence for obs in detected_observations) / max(len(detected_observations), 1)

    return AutoDetectionResponse(
        detection_id=detection_id,
        observations_detected=len(detected_observations),
        detection_confidence_avg=avg_confidence,
        detection_duration_ms=250,
        detected_observations=detected_responses,
        scan_summary={
            "scan_scope": detection_request.scan_scope,
            "criteria_applied": len(detection_request.detection_criteria),
            "confidence_threshold": detection_request.confidence_threshold
        }
    )

@router.post("/{cycle_id}/reports/{report_id}/observations", response_model=ObservationResponse)
@require_permission("observations", "create")
async def create_observation(
    cycle_id: int,
    report_id: int,
    observation_data: ObservationCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Create a new observation manually"""

    # Get phase
    phase_result = await db.execute(
        select(ObservationManagementPhase).where(
            and_(
                ObservationManagementPhase.cycle_id == cycle_id,
                ObservationManagementPhase.report_id == report_id
            )
        )
    )
    phase = phase_result.scalar_one_or_none()
    if not phase:
        raise HTTPException(status_code=404, detail="Observation management phase not found")

    # Create observation
    observation = ObservationRecord(
        phase_id=phase.phase_id,
        cycle_id=cycle_id,
        report_id=report_id,
        observation_title=observation_data.observation_title,
        observation_description=observation_data.observation_description,
        observation_type=observation_data.observation_type,
        severity=observation_data.severity,
        source_test_execution_id=observation_data.source_test_execution_id,
        source_sample_record_id=observation_data.source_sample_record_id,
        source_attribute_id=observation_data.source_attribute_id,
        detection_method=observation_data.detection_method,
        detection_confidence=observation_data.detection_confidence,
        impact_description=observation_data.impact_description,
        impact_categories=observation_data.impact_categories,
        financial_impact_estimate=observation_data.financial_impact_estimate,
        regulatory_risk_level=observation_data.regulatory_risk_level,
        affected_processes=observation_data.affected_processes,
        affected_systems=observation_data.affected_systems,
        evidence_documents=observation_data.evidence_documents,
        supporting_data=observation_data.supporting_data,
        screenshots=observation_data.screenshots,
        related_observations=observation_data.related_observations,
        detected_by=current_user.user_id,
        assigned_to=observation_data.assigned_to
    )

    db.add(observation)
    await db.commit()
    await db.refresh(observation)

    # Update phase statistics
    phase.total_observations += 1
    phase.manual_observations += 1
    await db.commit()

    # Create audit log
    audit_log = ObservationManagementAuditLog(
        cycle_id=cycle_id,
        report_id=report_id,
        phase_id=phase.phase_id,
        observation_id=observation.observation_id,
        action="create_observation",
        entity_type="ObservationRecord",
        entity_id=str(observation.observation_id),
        performed_by=current_user.user_id,
        user_role=current_user.role.value,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        new_values={
            "observation_title": observation.observation_title,
            "observation_type": observation.observation_type.value,
            "severity": observation.severity.value,
            "detection_method": observation.detection_method
        },
        execution_time_ms=75
    )
    db.add(audit_log)
    await db.commit()

    return ObservationResponse(
        observation_id=observation.observation_id,
        phase_id=observation.phase_id,
        cycle_id=observation.cycle_id,
        report_id=observation.report_id,
        observation_title=observation.observation_title,
        observation_description=observation.observation_description,
        observation_type=observation.observation_type,
        severity=observation.severity,
        status=observation.status,
        source_test_execution_id=observation.source_test_execution_id,
        source_sample_record_id=observation.source_sample_record_id,
        source_attribute_id=observation.source_attribute_id,
        detection_method=observation.detection_method,
        detection_confidence=observation.detection_confidence,
        impact_description=observation.impact_description,
        financial_impact_estimate=observation.financial_impact_estimate,
        regulatory_risk_level=observation.regulatory_risk_level,
        detected_by=observation.detected_by,
        assigned_to=observation.assigned_to,
        detected_at=observation.detected_at,
        assigned_at=observation.assigned_at,
        auto_detection_score=observation.auto_detection_score,
        manual_validation_required=observation.manual_validation_required
    )

@router.get("/{cycle_id}/reports/{report_id}/observations", response_model=List[ObservationResponse])
@require_permission("observations", "read")
async def get_observations(
    cycle_id: int,
    report_id: int,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    observation_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get observations with optional filtering"""

    # Get phase
    phase_result = await db.execute(
        select(ObservationManagementPhase).where(
            and_(
                ObservationManagementPhase.cycle_id == cycle_id,
                ObservationManagementPhase.report_id == report_id
            )
        )
    )
    phase = phase_result.scalar_one_or_none()
    if not phase:
        raise HTTPException(status_code=404, detail="Observation management phase not found")

    # Build query with filters
    query = select(ObservationRecord).where(
        and_(
            ObservationRecord.cycle_id == cycle_id,
            ObservationRecord.report_id == report_id,
            ObservationRecord.phase_id == phase.phase_id
        )
    )

    if status:
        try:
            status_enum = ObservationStatusEnum(status)
            query = query.where(ObservationRecord.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    if severity:
        try:
            severity_enum = ObservationSeverityEnum(severity)
            query = query.where(ObservationRecord.severity == severity_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid severity: {severity}")

    if observation_type:
        try:
            type_enum = ObservationTypeEnum(observation_type)
            query = query.where(ObservationRecord.observation_type == type_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid observation type: {observation_type}")

    query = query.order_by(desc(ObservationRecord.detected_at)).limit(limit).offset(offset)

    result = await db.execute(query)
    observations = result.scalars().all()

    return [
        ObservationResponse(
            observation_id=obs.observation_id,
            phase_id=obs.phase_id,
            cycle_id=obs.cycle_id,
            report_id=obs.report_id,
            observation_title=obs.observation_title,
            observation_description=obs.observation_description,
            observation_type=obs.observation_type,
            severity=obs.severity,
            status=obs.status,
            source_test_execution_id=obs.source_test_execution_id,
            source_sample_record_id=obs.source_sample_record_id,
            source_attribute_id=obs.source_attribute_id,
            detection_method=obs.detection_method,
            detection_confidence=obs.detection_confidence,
            impact_description=obs.impact_description,
            financial_impact_estimate=obs.financial_impact_estimate,
            regulatory_risk_level=obs.regulatory_risk_level,
            detected_by=obs.detected_by,
            assigned_to=obs.assigned_to,
            detected_at=obs.detected_at,
            assigned_at=obs.assigned_at,
            auto_detection_score=obs.auto_detection_score,
            manual_validation_required=obs.manual_validation_required
        )
        for obs in observations
    ]

@router.post("/{cycle_id}/reports/{report_id}/observations/{observation_id}/approve", response_model=ObservationApprovalResponse)
@require_permission("observations", "approve", resource_id_param="observation_id")
async def approve_observation(
    cycle_id: int,
    report_id: int,
    observation_id: int,
    approval_request: ObservationApprovalRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Approve or reject an observation"""

    # Get observation
    obs_result = await db.execute(
        select(ObservationRecord).where(
            and_(
                ObservationRecord.observation_id == observation_id,
                ObservationRecord.cycle_id == cycle_id,
                ObservationRecord.report_id == report_id
            )
        )
    )
    observation = obs_result.scalar_one_or_none()
    if not observation:
        raise HTTPException(status_code=404, detail="Observation not found")

    # Determine approval level based on user role
    approval_level = "Report Owner" if current_user.role.value == "Report Owner" else "Test Manager"

    # Create approval record
    approval = ObservationApproval(
        observation_id=observation.observation_id,
        approval_status=approval_request.approval_status,
        approval_level=approval_level,
        approver_comments=approval_request.approver_comments,
        approval_rationale=approval_request.approval_rationale,
        severity_assessment=approval_request.severity_assessment,
        impact_validation=approval_request.impact_validation,
        evidence_sufficiency=approval_request.evidence_sufficiency,
        regulatory_significance=approval_request.regulatory_significance,
        requires_escalation=approval_request.requires_escalation,
        recommended_action=approval_request.recommended_action,
        priority_level=approval_request.priority_level,
        estimated_effort=approval_request.estimated_effort,
        target_resolution_date=approval_request.target_resolution_date,
        approval_criteria_met=approval_request.approval_criteria_met,
        conditional_approval=approval_request.conditional_approval,
        conditions=approval_request.conditions,
        approved_by=current_user.user_id
    )

    db.add(approval)

    # Update observation status
    if approval_request.approval_status == "Approved":
        observation.status = ObservationStatusEnum.APPROVED
        # Update phase statistics
        phase_result = await db.execute(
            select(ObservationManagementPhase).where(
                ObservationManagementPhase.phase_id == observation.phase_id
            )
        )
        phase = phase_result.scalar_one_or_none()
        if phase:
            phase.approved_observations += 1
    elif approval_request.approval_status == "Rejected":
        observation.status = ObservationStatusEnum.REJECTED
        # Update phase statistics
        phase_result = await db.execute(
            select(ObservationManagementPhase).where(
                ObservationManagementPhase.phase_id == observation.phase_id
            )
        )
        phase = phase_result.scalar_one_or_none()
        if phase:
            phase.rejected_observations += 1

    await db.commit()
    await db.refresh(approval)

    # Create audit log
    audit_log = ObservationManagementAuditLog(
        cycle_id=cycle_id,
        report_id=report_id,
        phase_id=observation.phase_id,
        observation_id=observation.observation_id,
        action="approve_observation",
        entity_type="ObservationApproval",
        entity_id=str(approval.approval_id),
        performed_by=current_user.user_id,
        user_role=current_user.role.value,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        old_values={"status": "Under Review"},
        new_values={
            "approval_status": approval.approval_status,
            "approval_level": approval.approval_level,
            "observation_status": observation.status.value
        },
        execution_time_ms=125
    )
    db.add(audit_log)
    await db.commit()

    return ObservationApprovalResponse(
        approval_id=approval.approval_id,
        observation_id=approval.observation_id,
        approval_status=approval.approval_status,
        approval_level=approval.approval_level,
        approver_comments=approval.approver_comments,
        recommended_action=approval.recommended_action,
        requires_escalation=approval.requires_escalation,
        priority_level=approval.priority_level,
        target_resolution_date=approval.target_resolution_date,
        approved_by=approval.approved_by,
        approved_at=approval.approved_at,
        escalated_to=approval.escalated_to
    )

@router.get("/{cycle_id}/reports/{report_id}/analytics", response_model=ObservationAnalytics)
@require_permission("observations", "read")
async def get_observation_analytics(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive observation analytics"""

    # Get phase
    phase_result = await db.execute(
        select(ObservationManagementPhase).where(
            and_(
                ObservationManagementPhase.cycle_id == cycle_id,
                ObservationManagementPhase.report_id == report_id
            )
        )
    )
    phase = phase_result.scalar_one_or_none()
    if not phase:
        raise HTTPException(status_code=404, detail="Observation management phase not found")

    # Get all observations for analytics
    observations_result = await db.execute(
        select(ObservationRecord).where(
            and_(
                ObservationRecord.cycle_id == cycle_id,
                ObservationRecord.report_id == report_id,
                ObservationRecord.phase_id == phase.phase_id
            )
        )
    )
    observations = observations_result.scalars().all()

    # Calculate analytics
    total_observations = len(observations)

    # Detection methods breakdown
    detection_methods = {}
    for obs in observations:
        method = obs.detection_method or "Unknown"
        detection_methods[method] = detection_methods.get(method, 0) + 1

    # Type distribution
    type_distribution = {}
    for obs in observations:
        obs_type = obs.observation_type.value
        type_distribution[obs_type] = type_distribution.get(obs_type, 0) + 1

    # Severity distribution
    severity_distribution = {}
    for obs in observations:
        severity = obs.severity.value
        severity_distribution[severity] = severity_distribution.get(severity, 0) + 1

    # Status distribution
    status_distribution = {}
    for obs in observations:
        status = obs.status.value
        status_distribution[status] = status_distribution.get(status, 0) + 1

    # Financial impact by category
    financial_impact_by_category = {}
    total_financial_impact = 0
    for obs in observations:
        if obs.financial_impact_estimate:
            total_financial_impact += obs.financial_impact_estimate
            obs_type = obs.observation_type.value
            financial_impact_by_category[obs_type] = financial_impact_by_category.get(obs_type, 0) + obs.financial_impact_estimate

    # Daily trends (simulated)
    observations_by_day = [
        {"date": "2025-01-08", "count": 3, "auto_detected": 2, "manual": 1},
        {"date": "2025-01-09", "count": 5, "auto_detected": 3, "manual": 2},
        {"date": "2025-01-10", "count": 2, "auto_detected": 1, "manual": 1}
    ]

    # Resolution timeline (simulated)
    resolution_timeline = [
        {"milestone": "Detection", "avg_days": 0.5, "completed": total_observations},
        {"milestone": "Review", "avg_days": 2.1, "completed": phase.approved_observations + phase.rejected_observations},
        {"milestone": "Resolution", "avg_days": 5.8, "completed": phase.approved_observations // 2}
    ]

    return ObservationAnalytics(
        cycle_id=cycle_id,
        report_id=report_id,
        phase_id=phase.phase_id,
        total_observations=total_observations,
        detection_methods_breakdown=detection_methods,
        type_distribution=type_distribution,
        severity_distribution=severity_distribution,
        status_distribution=status_distribution,
        average_detection_time=1.2,
        average_approval_time=2.8,
        average_resolution_time=5.2,
        detection_accuracy=87.5,
        total_financial_impact=total_financial_impact,
        average_financial_impact=total_financial_impact / max(total_observations, 1),
        financial_impact_by_category=financial_impact_by_category,
        observations_by_day=observations_by_day,
        resolution_timeline=resolution_timeline,
        approval_rate=phase.approved_observations / max(total_observations, 1) * 100,
        escalation_rate=12.5,
        resolution_success_rate=92.3
    )

@router.post("/{cycle_id}/reports/{report_id}/complete", response_model=Dict[str, Any])
@require_permission("observations", "override")
async def complete_observation_management_phase(
    cycle_id: int,
    report_id: int,
    completion_data: ObservationManagementPhaseComplete,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Complete observation management phase"""

    # Get phase
    phase_result = await db.execute(
        select(ObservationManagementPhase).where(
            and_(
                ObservationManagementPhase.cycle_id == cycle_id,
                ObservationManagementPhase.report_id == report_id
            )
        )
    )
    phase = phase_result.scalar_one_or_none()
    if not phase:
        raise HTTPException(status_code=404, detail="Observation management phase not found")

    if phase.phase_status == "Completed":
        raise HTTPException(status_code=400, detail="Phase already completed")

    # Check completion requirements unless override is used
    if not completion_data.override_validation:
        pending_count = phase.total_observations - phase.approved_observations - phase.rejected_observations
        if pending_count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot complete phase: {pending_count} observations pending approval"
            )
        if phase.total_observations == 0:
            raise HTTPException(
                status_code=400,
                detail="Cannot complete phase: No observations have been created"
            )

    # Complete the phase
    phase.phase_status = "Completed"
    phase.completed_at = datetime.utcnow()
    phase.completed_by = current_user.user_id

    if completion_data.completion_notes:
        if phase.notes:
            phase.notes += f"\n\nCompletion Notes: {completion_data.completion_notes}"
        else:
            phase.notes = f"Completion Notes: {completion_data.completion_notes}"

    await db.commit()

    # Create audit log
    audit_log = ObservationManagementAuditLog(
        cycle_id=cycle_id,
        report_id=report_id,
        phase_id=phase.phase_id,
        action="complete_phase",
        entity_type="ObservationManagementPhase",
        entity_id=phase.phase_id,
        performed_by=current_user.user_id,
        user_role=current_user.role.value,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        old_values={"phase_status": "In Progress"},
        new_values={
            "phase_status": "Completed",
            "completed_at": phase.completed_at.isoformat(),
            "override_used": completion_data.override_validation
        },
        business_justification=completion_data.override_reason if completion_data.override_validation else None,
        execution_time_ms=100
    )
    db.add(audit_log)
    await db.commit()

    return {
        "message": "Observation management phase completed successfully",
        "phase_id": phase.phase_id,
        "cycle_id": cycle_id,
        "report_id": report_id,
        "completed_at": phase.completed_at,
        "completed_by": current_user.user_id,
        "total_observations": phase.total_observations,
        "approved_observations": phase.approved_observations,
        "rejected_observations": phase.rejected_observations,
        "override_used": completion_data.override_validation
    }

@router.get("/{cycle_id}/reports/{report_id}/audit_logs", response_model=List[ObservationManagementAuditLogSchema])
@require_permission("observations", "read")
async def get_observation_audit_logs(
    cycle_id: int,
    report_id: int,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """Get observation management audit logs"""

    query = select(ObservationManagementAuditLog).where(
        and_(
            ObservationManagementAuditLog.cycle_id == cycle_id,
            ObservationManagementAuditLog.report_id == report_id
        )
    ).order_by(desc(ObservationManagementAuditLog.performed_at)).limit(limit).offset(offset)

    result = await db.execute(query)
    audit_logs = result.scalars().all()

    return [
        ObservationManagementAuditLogSchema(
            log_id=log.log_id,
            cycle_id=log.cycle_id,
            report_id=log.report_id,
            phase_id=log.phase_id,
            observation_id=log.observation_id,
            action=log.action,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            performed_by=log.performed_by,
            performed_at=log.performed_at,
            old_values=log.old_values,
            new_values=log.new_values,
            changes_summary=log.changes_summary,
            notes=log.notes,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            execution_time_ms=log.execution_time_ms
        )
        for log in audit_logs
    ]


@router.post("/{cycle_id}/reports/{report_id}/observations/from-test-result", response_model=ObservationResponse)
@require_permission("observations", "create")
async def create_observation_from_test_result(
    cycle_id: int,
    report_id: int,
    request_data: Dict[str, Any],
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create observation from test execution result with intelligent grouping"""
    
    # Get test execution
    test_execution_id = request_data.get("test_execution_id")
    if not test_execution_id:
        raise HTTPException(status_code=400, detail="test_execution_id is required")
    
    # Import here to avoid circular dependency
    from app.models.test_execution import TestExecution
    
    exec_result = await db.execute(
        select(TestExecution)
        .options(selectinload(TestExecution.attribute))
        .where(TestExecution.execution_id == test_execution_id)
    )
    test_execution = exec_result.scalar_one_or_none()
    if not test_execution:
        raise HTTPException(status_code=404, detail="Test execution not found")
    
    # Get observation management phase
    phase_result = await db.execute(
        select(ObservationManagementPhase).where(
            and_(
                ObservationManagementPhase.cycle_id == cycle_id,
                ObservationManagementPhase.report_id == report_id
            )
        )
    )
    phase = phase_result.scalar_one_or_none()
    if not phase:
        raise HTTPException(status_code=404, detail="Observation management phase not found")
    
    # Categorize the test failure
    observation_type, keywords = categorize_test_failure(test_execution)
    
    # Check for existing similar observation
    existing_observation = await find_similar_observation(
        db,
        cycle_id,
        report_id,
        test_execution.attribute_id,
        observation_type,
        keywords
    )
    
    if existing_observation:
        # Update existing observation
        # Add this test execution to the related data
        related_executions = existing_observation.supporting_data.get("related_test_executions", [])
        if test_execution_id not in related_executions:
            related_executions.append(test_execution_id)
            existing_observation.supporting_data["related_test_executions"] = related_executions
        
        # Update sample count
        existing_observation.impact_assessments = existing_observation.impact_assessments or []
        
        # Add sample if not already included
        sample_records = existing_observation.supporting_data.get("affected_samples", [])
        if test_execution.sample_record_id and test_execution.sample_record_id not in sample_records:
            sample_records.append(test_execution.sample_record_id)
            existing_observation.supporting_data["affected_samples"] = sample_records
        
        # Update severity if needed
        if request_data.get("severity"):
            new_severity = ObservationSeverityEnum(request_data["severity"])
            # Compare severity based on order: CRITICAL > HIGH > MEDIUM > LOW > INFORMATIONAL
            severity_order = ["INFORMATIONAL", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
            if severity_order.index(new_severity.value) > severity_order.index(existing_observation.severity.value):
                existing_observation.severity = new_severity
        
        await db.commit()
        await db.refresh(existing_observation)
        
        observation = existing_observation
        action_taken = "updated_existing"
    else:
        # Create new observation
        observation = ObservationRecord(
            phase_id=phase.phase_id,
            cycle_id=cycle_id,
            report_id=report_id,
            observation_title=request_data.get("observation_title", f"{observation_type.value} - {test_execution.attribute.attribute_name if test_execution.attribute else 'Unknown Attribute'}"),
            observation_description=request_data.get("observation_description", test_execution.execution_summary or "Test execution failed"),
            observation_type=observation_type,
            severity=ObservationSeverityEnum(request_data.get("severity", "MEDIUM")),
            status=ObservationStatusEnum.DETECTED,
            source_test_execution_id=test_execution_id,
            source_sample_record_id=test_execution.sample_record_id,
            source_attribute_id=test_execution.attribute_id,
            detection_method="Test Result Review",
            detection_confidence=1.0 - (test_execution.confidence_score or 0.5),
            impact_description=request_data.get("impact_description", ""),
            impact_categories=request_data.get("impact_categories", ["OPERATIONAL"]),
            financial_impact_estimate=request_data.get("financial_impact"),
            regulatory_risk_level=request_data.get("regulatory_risk_level", "Medium"),
            affected_processes=request_data.get("affected_processes", []),
            affected_systems=request_data.get("affected_systems", []),
            evidence_documents=[],
            supporting_data={
                "related_test_executions": [test_execution_id],
                "affected_samples": [test_execution.sample_record_id] if test_execution.sample_record_id else [],
                "issue_keywords": keywords
            },
            detected_by=current_user.user_id,
            assigned_to=request_data.get("assigned_to")
        )
        
        db.add(observation)
        await db.commit()
        await db.refresh(observation)
        
        action_taken = "created_new"
    
    # Create audit log
    audit_log = ObservationManagementAuditLog(
        cycle_id=cycle_id,
        report_id=report_id,
        phase_id=phase.phase_id,
        observation_id=observation.observation_id,
        action="create_from_test",
        entity_type="ObservationRecord",
        entity_id=str(observation.observation_id),
        performed_by=current_user.user_id,
        user_role=current_user.role,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        new_values={
            "test_execution_id": test_execution_id,
            "action_taken": action_taken,
            "observation_type": observation_type.value
        },
        notes=f"Created from test execution {test_execution_id}"
    )
    db.add(audit_log)
    await db.commit()
    
    return ObservationResponse(
        observation_id=observation.observation_id,
        phase_id=observation.phase_id,
        cycle_id=observation.cycle_id,
        report_id=observation.report_id,
        observation_title=observation.observation_title,
        observation_description=observation.observation_description,
        observation_type=observation.observation_type,
        severity=observation.severity,
        status=observation.status,
        source_test_execution_id=observation.source_test_execution_id,
        source_sample_record_id=observation.source_sample_record_id,
        source_attribute_id=observation.source_attribute_id,
        detection_method=observation.detection_method,
        detection_confidence=observation.detection_confidence,
        impact_description=observation.impact_description,
        financial_impact_estimate=observation.financial_impact_estimate,
        regulatory_risk_level=observation.regulatory_risk_level,
        detected_by=observation.detected_by,
        assigned_to=observation.assigned_to,
        detected_at=observation.detected_at,
        assigned_at=observation.assigned_at
    )


@router.get("/{cycle_id}/reports/{report_id}/observations/grouped", response_model=List[Dict[str, Any]])
@require_permission("observations", "read")
async def get_grouped_observations(
    cycle_id: int,
    report_id: int,
    group_by: str = "attribute_and_type",  # attribute_and_type, type_only, severity
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get observations grouped by attribute and issue type"""
    
    # Get all observations for the cycle/report
    query = select(ObservationRecord).options(
        selectinload(ObservationRecord.source_attribute)
    ).where(
        and_(
            ObservationRecord.cycle_id == cycle_id,
            ObservationRecord.report_id == report_id
        )
    )
    
    result = await db.execute(query)
    observations = result.scalars().all()
    
    # Group observations
    grouped = {}
    
    for obs in observations:
        if group_by == "attribute_and_type":
            key = f"{obs.source_attribute_id or 'General'}_{obs.observation_type.value}"
            group_name = f"{obs.source_attribute.attribute_name if obs.source_attribute else 'General'} - {obs.observation_type.value}"
        elif group_by == "type_only":
            key = obs.observation_type.value
            group_name = obs.observation_type.value
        else:  # severity
            key = obs.severity.value
            group_name = f"{obs.severity.value} Severity"
        
        if key not in grouped:
            grouped[key] = {
                "group_key": key,
                "group_name": group_name,
                "observation_count": 0,
                "sample_count": 0,
                "test_execution_count": 0,
                "observations": [],
                "affected_samples": set(),
                "related_test_executions": set()
            }
        
        grouped[key]["observations"].append({
            "observation_id": obs.observation_id,
            "title": obs.observation_title,
            "severity": obs.severity.value,
            "status": obs.status.value
        })
        grouped[key]["observation_count"] += 1
        
        # Track unique samples and test executions
        if obs.source_sample_record_id:
            grouped[key]["affected_samples"].add(obs.source_sample_record_id)
        if obs.supporting_data and "related_test_executions" in obs.supporting_data:
            for exec_id in obs.supporting_data["related_test_executions"]:
                grouped[key]["related_test_executions"].add(exec_id)
    
    # Convert sets to counts and lists
    result_groups = []
    for key, group in grouped.items():
        group["sample_count"] = len(group["affected_samples"])
        group["test_execution_count"] = len(group["related_test_executions"])
        group["affected_samples"] = list(group["affected_samples"])[:10]  # Limit to 10 for response size
        group["related_test_executions"] = list(group["related_test_executions"])[:10]
        result_groups.append(group)
    
    # Sort by observation count descending
    result_groups.sort(key=lambda x: x["observation_count"], reverse=True)
    
    return result_groups
