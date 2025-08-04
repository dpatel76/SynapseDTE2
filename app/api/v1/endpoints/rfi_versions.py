"""
RFI (Request for Information) Version API endpoints

This module contains the versioned API endpoints for the RFI phase,
following the same pattern as sample selection and scoping endpoints.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload, joinedload
from uuid import UUID
import logging

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.workflow import WorkflowPhase
from app.models.rfi_versions import RFIVersion, RFIEvidence as RFIEvidenceVersioned
from app.models.request_info import CycleReportTestCase
from app.schemas.rfi_versions import (
    RFIVersionCreate,
    RFIVersionUpdate,
    RFIVersionResponse,
    RFIVersionListResponse,
    RFIEvidenceCreate,
    RFIEvidenceUpdate,
    RFIEvidenceResponse,
    BulkEvidenceDecision,
    SendToReportOwnerRequest,
    ResubmitRequest,
    TestCaseSubmissionStatus,
    DataOwnerSubmissionSummary,
    QueryValidationRequest,
    QueryValidationResponse,
    VersionStatus,
    EvidenceStatus,
    Decision
)
from app.services.universal_assignment_service import UniversalAssignmentService
# from app.services.file_storage_service import FileStorageService  # TODO: Implement when file storage is available
from app.services.request_info_service import RequestInfoService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/rfi",
    tags=["rfi-versions"],
    responses={404: {"description": "Not found"}},
)


# Version Management Endpoints
@router.get("/cycles/{cycle_id}/reports/{report_id}/versions", response_model=List[RFIVersionListResponse])
async def get_rfi_versions(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all RFI versions for a cycle/report"""
    try:
        # Get phase
        phase_query = select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == "Request Info"
            )
        )
        phase_result = await db.execute(phase_query)
        phase = phase_result.scalar_one_or_none()
        
        if not phase:
            raise HTTPException(status_code=404, detail="Request Info phase not found")
        
        # Get all versions
        versions_query = select(RFIVersion).where(
            RFIVersion.phase_id == phase.phase_id
        ).order_by(RFIVersion.version_number.desc())
        
        versions_result = await db.execute(versions_query)
        versions = versions_result.scalars().all()
        
        # Determine current version
        current_version = next(
            (v for v in versions if v.version_status in [VersionStatus.APPROVED, VersionStatus.PENDING_APPROVAL]),
            versions[0] if versions else None
        )
        
        # Convert to response format
        return [
            RFIVersionListResponse(
                version_id=v.version_id,
                phase_id=v.phase_id,
                version_number=v.version_number,
                version_status=v.version_status,
                is_current=v == current_version,
                can_be_edited=v.can_be_edited,
                total_test_cases=v.total_test_cases,
                submitted_count=v.submitted_count,
                approved_count=v.approved_count,
                completion_percentage=v.completion_percentage,
                created_at=v.created_at,
                submitted_at=v.submitted_at,
                approved_at=v.approved_at
            )
            for v in versions
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting RFI versions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/versions/{version_id}", response_model=RFIVersionResponse)
async def get_rfi_version(
    version_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific RFI version with all evidence"""
    try:
        # Get version with evidence
        version_query = select(RFIVersion).where(
            RFIVersion.version_id == version_id
        ).options(
            selectinload(RFIVersion.evidence_items).selectinload(RFIEvidenceVersioned.test_case),
            selectinload(RFIVersion.evidence_items).selectinload(RFIEvidenceVersioned.data_owner),
            selectinload(RFIVersion.submitted_by),
            selectinload(RFIVersion.approved_by)
        )
        
        version_result = await db.execute(version_query)
        version = version_result.scalar_one_or_none()
        
        if not version:
            raise HTTPException(status_code=404, detail="Version not found")
        
        # Convert to response
        response = RFIVersionResponse.from_orm(version)
        
        # Add computed fields
        response.is_latest = version.is_latest
        response.completion_percentage = version.completion_percentage
        response.approval_percentage = version.approval_percentage
        response.can_be_edited = version.can_be_edited
        response.has_report_owner_feedback = version.has_report_owner_feedback
        
        # Add user names
        if version.submitted_by:
            response.submitted_by_name = f"{version.submitted_by.first_name} {version.submitted_by.last_name}"
        if version.approved_by:
            response.approved_by_name = f"{version.approved_by.first_name} {version.approved_by.last_name}"
        
        # Process evidence items
        for evidence in response.evidence_items:
            # Add computed properties
            evidence.is_approved = evidence.tester_decision == Decision.APPROVED and evidence.report_owner_decision == Decision.APPROVED
            evidence.is_rejected = evidence.tester_decision == Decision.REJECTED or evidence.report_owner_decision == Decision.REJECTED
            evidence.needs_resubmission = (evidence.requires_resubmission or 
                                          evidence.tester_decision == Decision.REQUEST_CHANGES or
                                          evidence.report_owner_decision == Decision.REQUEST_CHANGES)
            
            # Set final status
            if evidence.is_approved:
                evidence.final_status = "approved"
            elif evidence.is_rejected:
                evidence.final_status = "rejected"
            elif evidence.needs_resubmission:
                evidence.final_status = "request_changes"
            elif evidence.tester_decision or evidence.report_owner_decision:
                evidence.final_status = "partial_review"
            else:
                evidence.final_status = "pending"
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting RFI version: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cycles/{cycle_id}/reports/{report_id}/versions", response_model=RFIVersionResponse)
async def create_rfi_version(
    cycle_id: int,
    report_id: int,
    version_data: RFIVersionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new RFI version"""
    try:
        # Get phase
        phase_query = select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == "Request Info"
            )
        )
        phase_result = await db.execute(phase_query)
        phase = phase_result.scalar_one_or_none()
        
        if not phase:
            raise HTTPException(status_code=404, detail="Request Info phase not found")
        
        # Get current version if any
        current_version_query = select(RFIVersion).where(
            RFIVersion.phase_id == phase.phase_id
        ).order_by(RFIVersion.version_number.desc()).limit(1)
        
        current_version_result = await db.execute(current_version_query)
        current_version = current_version_result.scalar_one_or_none()
        
        # Create new version
        new_version = RFIVersion(
            phase_id=phase.phase_id,
            version_number=(current_version.version_number + 1) if current_version else 1,
            version_status=VersionStatus.DRAFT,
            parent_version_id=current_version.version_id if current_version else None,
            submission_deadline=version_data.submission_deadline,
            reminder_schedule=version_data.reminder_schedule,
            instructions=version_data.instructions,
            created_by_id=current_user.user_id,
            updated_by_id=current_user.user_id
        )
        
        db.add(new_version)
        await db.flush()
        
        # Get test cases for this phase
        test_cases_query = select(CycleReportTestCase).where(
            CycleReportTestCase.phase_id == phase.phase_id
        )
        test_cases_result = await db.execute(test_cases_query)
        test_cases = test_cases_result.scalars().all()
        
        new_version.total_test_cases = len(test_cases)
        
        # Carry forward evidence if requested and previous version exists
        if current_version and version_data.carry_forward_all:
            evidence_query = select(RFIEvidenceVersioned).where(
                RFIEvidenceVersioned.version_id == current_version.version_id
            )
            
            if version_data.carry_forward_approved_only:
                evidence_query = evidence_query.where(
                    and_(
                        RFIEvidenceVersioned.tester_decision == Decision.APPROVED,
                        RFIEvidenceVersioned.report_owner_decision == Decision.APPROVED
                    )
                )
            
            evidence_result = await db.execute(evidence_query)
            evidence_to_copy = evidence_result.scalars().all()
            
            # Copy evidence to new version
            for evidence in evidence_to_copy:
                new_evidence = RFIEvidenceVersioned(
                    version_id=new_version.version_id,
                    phase_id=evidence.phase_id,
                    test_case_id=evidence.test_case_id,
                    sample_id=evidence.sample_id,
                    attribute_id=evidence.attribute_id,
                    attribute_name=evidence.attribute_name,
                    evidence_type=evidence.evidence_type,
                    evidence_status=EvidenceStatus.PENDING if not version_data.carry_forward_approved_only else evidence.evidence_status,
                    data_owner_id=evidence.data_owner_id,
                    submitted_at=evidence.submitted_at,
                    submission_notes=evidence.submission_notes,
                    # Document fields
                    original_filename=evidence.original_filename,
                    stored_filename=evidence.stored_filename,
                    file_path=evidence.file_path,
                    file_size_bytes=evidence.file_size_bytes,
                    file_hash=evidence.file_hash,
                    mime_type=evidence.mime_type,
                    # Data source fields
                    data_source_id=evidence.data_source_id,
                    query_text=evidence.query_text,
                    query_parameters=evidence.query_parameters,
                    query_result_sample=evidence.query_result_sample,
                    row_count=evidence.row_count,
                    # Reset decisions if not carrying forward approved only
                    tester_decision=evidence.tester_decision if version_data.carry_forward_approved_only else None,
                    tester_notes=evidence.tester_notes if version_data.carry_forward_approved_only else None,
                    tester_decided_by=evidence.tester_decided_by if version_data.carry_forward_approved_only else None,
                    tester_decided_at=evidence.tester_decided_at if version_data.carry_forward_approved_only else None,
                    report_owner_decision=evidence.report_owner_decision if version_data.carry_forward_approved_only else None,
                    report_owner_notes=evidence.report_owner_notes if version_data.carry_forward_approved_only else None,
                    report_owner_decided_by=evidence.report_owner_decided_by if version_data.carry_forward_approved_only else None,
                    report_owner_decided_at=evidence.report_owner_decided_at if version_data.carry_forward_approved_only else None,
                    # Track parent
                    parent_evidence_id=evidence.evidence_id,
                    resubmission_count=evidence.resubmission_count + 1 if not version_data.carry_forward_approved_only else evidence.resubmission_count,
                    # Audit
                    created_by_id=current_user.user_id,
                    updated_by_id=current_user.user_id
                )
                db.add(new_evidence)
                
                # Update counts
                if new_evidence.submitted_at:
                    new_version.submitted_count += 1
                    if new_evidence.evidence_type == "document":
                        new_version.document_evidence_count += 1
                    else:
                        new_version.data_source_evidence_count += 1
                
                if new_evidence.is_approved:
                    new_version.approved_count += 1
                elif new_evidence.is_rejected:
                    new_version.rejected_count += 1
                else:
                    new_version.pending_count += 1
        
        await db.commit()
        
        # Reload with relationships
        return await get_rfi_version(new_version.version_id, db, current_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating RFI version: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/versions/{version_id}/submit-for-approval")
async def submit_version_for_approval(
    version_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit version for approval"""
    try:
        # Get version
        version_query = select(RFIVersion).where(
            RFIVersion.version_id == version_id
        )
        version_result = await db.execute(version_query)
        version = version_result.scalar_one_or_none()
        
        if not version:
            raise HTTPException(status_code=404, detail="Version not found")
        
        if version.version_status != VersionStatus.DRAFT:
            raise HTTPException(status_code=400, detail="Only draft versions can be submitted for approval")
        
        # Update status
        version.version_status = VersionStatus.PENDING_APPROVAL
        version.submitted_by_id = current_user.user_id
        version.submitted_at = datetime.utcnow()
        version.updated_by_id = current_user.user_id
        
        await db.commit()
        
        return {"message": "Version submitted for approval successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting version for approval: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# Evidence Management Endpoints
@router.get("/versions/{version_id}/evidence", response_model=List[RFIEvidenceResponse])
async def get_version_evidence(
    version_id: UUID,
    test_case_id: Optional[int] = None,
    data_owner_id: Optional[int] = None,
    evidence_status: Optional[EvidenceStatus] = None,
    tester_decision: Optional[Decision] = None,
    report_owner_decision: Optional[Decision] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get evidence for a version with optional filters"""
    try:
        # Build query
        query = select(RFIEvidenceVersioned).where(
            RFIEvidenceVersioned.version_id == version_id
        ).options(
            selectinload(RFIEvidenceVersioned.test_case),
            selectinload(RFIEvidenceVersioned.data_owner),
            selectinload(RFIEvidenceVersioned.tester_decided_by_user),
            selectinload(RFIEvidenceVersioned.report_owner_decided_by_user),
            selectinload(RFIEvidenceVersioned.validated_by_user)
        )
        
        # Apply filters
        if test_case_id:
            query = query.where(RFIEvidenceVersioned.test_case_id == test_case_id)
        if data_owner_id:
            query = query.where(RFIEvidenceVersioned.data_owner_id == data_owner_id)
        if evidence_status:
            query = query.where(RFIEvidenceVersioned.evidence_status == evidence_status)
        if tester_decision:
            query = query.where(RFIEvidenceVersioned.tester_decision == tester_decision)
        if report_owner_decision:
            query = query.where(RFIEvidenceVersioned.report_owner_decision == report_owner_decision)
        
        result = await db.execute(query)
        evidence_items = result.scalars().all()
        
        # Convert to response format with computed fields
        responses = []
        for evidence in evidence_items:
            response = RFIEvidenceResponse.from_orm(evidence)
            
            # Add user names
            if evidence.data_owner:
                response.data_owner_name = f"{evidence.data_owner.first_name} {evidence.data_owner.last_name}"
            if evidence.tester_decided_by_user:
                response.tester_decided_by_name = f"{evidence.tester_decided_by_user.first_name} {evidence.tester_decided_by_user.last_name}"
            if evidence.report_owner_decided_by_user:
                response.report_owner_decided_by_name = f"{evidence.report_owner_decided_by_user.first_name} {evidence.report_owner_decided_by_user.last_name}"
            if evidence.validated_by_user:
                response.validated_by_name = f"{evidence.validated_by_user.first_name} {evidence.validated_by_user.last_name}"
            if evidence.created_by_id:
                response.created_by_name = f"{evidence.created_by.first_name} {evidence.created_by.last_name}"
            if evidence.updated_by_id:
                response.updated_by_name = f"{evidence.updated_by.first_name} {evidence.updated_by.last_name}"
            
            # Add computed properties
            response.is_approved = evidence.is_approved
            response.is_rejected = evidence.is_rejected
            response.needs_resubmission = evidence.needs_resubmission
            response.final_status = evidence.final_status
            
            responses.append(response)
        
        return responses
        
    except Exception as e:
        logger.error(f"Error getting version evidence: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-cases/{test_case_id}/submit-evidence", response_model=RFIEvidenceResponse)
async def submit_evidence(
    test_case_id: int,
    evidence_type: str = Form(...),
    submission_notes: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    data_source_id: Optional[int] = Form(None),
    query_text: Optional[str] = Form(None),
    query_parameters: Optional[str] = Form(None),  # JSON string
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit evidence for a test case"""
    try:
        # Validate evidence type
        if evidence_type not in ["document", "data_source"]:
            raise HTTPException(status_code=400, detail="Invalid evidence type")
        
        # Validate requirements based on type
        if evidence_type == "document" and not file:
            raise HTTPException(status_code=400, detail="File is required for document evidence")
        if evidence_type == "data_source" and not query_text:
            raise HTTPException(status_code=400, detail="Query text is required for data source evidence")
        
        # Get test case
        test_case_query = select(CycleReportTestCase).where(
            CycleReportTestCase.id == test_case_id
        ).options(selectinload(CycleReportTestCase.phase))
        
        test_case_result = await db.execute(test_case_query)
        test_case = test_case_result.scalar_one_or_none()
        
        if not test_case:
            raise HTTPException(status_code=404, detail="Test case not found")
        
        # Verify user is the assigned data owner
        if test_case.data_owner_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="You are not the assigned data owner for this test case")
        
        # Get current draft version
        version_query = select(RFIVersion).where(
            and_(
                RFIVersion.phase_id == test_case.phase_id,
                RFIVersion.version_status == VersionStatus.DRAFT
            )
        ).order_by(RFIVersion.version_number.desc()).limit(1)
        
        version_result = await db.execute(version_query)
        version = version_result.scalar_one_or_none()
        
        if not version:
            raise HTTPException(status_code=400, detail="No draft version available for evidence submission")
        
        # Check if evidence already exists for this test case in this version
        existing_query = select(RFIEvidenceVersioned).where(
            and_(
                RFIEvidenceVersioned.version_id == version.version_id,
                RFIEvidenceVersioned.test_case_id == test_case_id
            )
        )
        existing_result = await db.execute(existing_query)
        existing_evidence = existing_result.scalar_one_or_none()
        
        if existing_evidence:
            raise HTTPException(status_code=400, detail="Evidence already submitted for this test case in the current version")
        
        # Create evidence record
        evidence = RFIEvidenceVersioned(
            version_id=version.version_id,
            phase_id=test_case.phase_id,
            test_case_id=test_case_id,
            sample_id=test_case.sample_id,
            attribute_id=test_case.attribute_id,
            attribute_name=test_case.attribute_name,
            evidence_type=evidence_type,
            evidence_status=EvidenceStatus.PENDING,
            data_owner_id=current_user.user_id,
            submitted_at=datetime.utcnow(),
            submission_notes=submission_notes,
            created_by_id=current_user.user_id,
            updated_by_id=current_user.user_id
        )
        
        # Handle document evidence
        if evidence_type == "document":
            # Save file
            # TODO: Implement file storage
            # file_storage = FileStorageService()
            # file_result = await file_storage.save_uploaded_file(
            #     file,
            #     f"rfi/{test_case.phase.cycle_id}/{test_case.phase.report_id}/{version.version_id}"
            # )
            
            evidence.original_filename = file.filename
            # TODO: Implement file storage
            # evidence.stored_filename = file_result["stored_filename"]
            # evidence.file_path = file_result["file_path"]  
            # evidence.file_size_bytes = file_result["file_size"]
            # evidence.file_hash = file_result["file_hash"]
            evidence.mime_type = file.content_type or "application/octet-stream"
            
            # Temporary placeholder values
            evidence.stored_filename = f"temp_{file.filename}"
            evidence.file_path = f"/temp/rfi/{file.filename}"
            evidence.file_size_bytes = 0
            evidence.file_hash = "placeholder_hash"
            
        # Handle data source evidence
        else:
            evidence.data_source_id = data_source_id
            evidence.query_text = query_text
            if query_parameters:
                import json
                evidence.query_parameters = json.loads(query_parameters)
            
            # TODO: Execute query and capture results
            # This would typically involve:
            # 1. Validating the query
            # 2. Executing it against the data source
            # 3. Capturing sample results and row count
        
        db.add(evidence)
        
        # Update version statistics
        version.submitted_count += 1
        if evidence_type == "document":
            version.document_evidence_count += 1
        else:
            version.data_source_evidence_count += 1
        version.pending_count += 1
        
        await db.commit()
        
        # Return response
        return await get_evidence_by_id(evidence.evidence_id, db, current_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting evidence: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/evidence/{evidence_id}/tester-decision")
async def update_tester_decision(
    evidence_id: UUID,
    decision_data: RFIEvidenceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update tester decision on evidence"""
    try:
        # Verify user is a tester
        if current_user.role != 'Tester':
            raise HTTPException(status_code=403, detail="Only testers can make tester decisions")
        
        # Get evidence
        evidence_query = select(RFIEvidenceVersioned).where(
            RFIEvidenceVersioned.evidence_id == evidence_id
        ).options(selectinload(RFIEvidenceVersioned.version))
        
        evidence_result = await db.execute(evidence_query)
        evidence = evidence_result.scalar_one_or_none()
        
        if not evidence:
            raise HTTPException(status_code=404, detail="Evidence not found")
        
        # Check version is editable
        if not evidence.version.can_be_edited:
            raise HTTPException(status_code=400, detail="Version is not editable")
        
        # Update tester decision
        if decision_data.tester_decision:
            evidence.tester_decision = decision_data.tester_decision
            evidence.tester_notes = decision_data.tester_notes
            evidence.tester_decided_by = current_user.user_id
            evidence.tester_decided_at = datetime.utcnow()
            
            # Update evidence status
            if decision_data.tester_decision == Decision.APPROVED:
                evidence.evidence_status = EvidenceStatus.APPROVED
            elif decision_data.tester_decision == Decision.REJECTED:
                evidence.evidence_status = EvidenceStatus.REJECTED
            elif decision_data.tester_decision == Decision.REQUEST_CHANGES:
                evidence.evidence_status = EvidenceStatus.REQUEST_CHANGES
                evidence.requires_resubmission = True
        
        # Update validation if provided
        if decision_data.validation_status:
            evidence.validation_status = decision_data.validation_status
            evidence.validation_notes = decision_data.validation_notes
            evidence.validated_by = current_user.user_id
            evidence.validated_at = datetime.utcnow()
        
        evidence.updated_by_id = current_user.user_id
        
        # Update version statistics
        await update_version_statistics(evidence.version, db)
        
        await db.commit()
        
        return {"message": "Tester decision updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating tester decision: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/evidence/{evidence_id}/report-owner-decision")
async def update_report_owner_decision(
    evidence_id: UUID,
    decision_data: RFIEvidenceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update report owner decision on evidence"""
    try:
        # Verify user is a report owner
        if current_user.role != 'Report Owner':
            raise HTTPException(status_code=403, detail="Only report owners can make report owner decisions")
        
        # Get evidence
        evidence_query = select(RFIEvidenceVersioned).where(
            RFIEvidenceVersioned.evidence_id == evidence_id
        ).options(selectinload(RFIEvidenceVersioned.version))
        
        evidence_result = await db.execute(evidence_query)
        evidence = evidence_result.scalar_one_or_none()
        
        if not evidence:
            raise HTTPException(status_code=404, detail="Evidence not found")
        
        # Check that tester has already made a decision
        if not evidence.tester_decision:
            raise HTTPException(status_code=400, detail="Tester must make a decision before report owner review")
        
        # Update report owner decision
        if decision_data.report_owner_decision:
            evidence.report_owner_decision = decision_data.report_owner_decision
            evidence.report_owner_notes = decision_data.report_owner_notes
            evidence.report_owner_decided_by = current_user.user_id
            evidence.report_owner_decided_at = datetime.utcnow()
            
            # Update evidence status based on final decision
            if evidence.is_approved:
                evidence.evidence_status = EvidenceStatus.APPROVED
            elif evidence.is_rejected:
                evidence.evidence_status = EvidenceStatus.REJECTED
            elif evidence.needs_resubmission:
                evidence.evidence_status = EvidenceStatus.REQUEST_CHANGES
                evidence.requires_resubmission = True
        
        evidence.updated_by_id = current_user.user_id
        
        # Update version statistics
        await update_version_statistics(evidence.version, db)
        
        await db.commit()
        
        return {"message": "Report owner decision updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating report owner decision: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/versions/{version_id}/bulk-tester-decision")
async def bulk_tester_decision(
    version_id: UUID,
    decision_data: BulkEvidenceDecision,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Apply tester decision to multiple evidence items"""
    try:
        # Verify user is a tester
        if current_user.role != 'Tester':
            raise HTTPException(status_code=403, detail="Only testers can make tester decisions")
        
        # Get version
        version_query = select(RFIVersion).where(
            RFIVersion.version_id == version_id
        )
        version_result = await db.execute(version_query)
        version = version_result.scalar_one_or_none()
        
        if not version:
            raise HTTPException(status_code=404, detail="Version not found")
        
        if not version.can_be_edited:
            raise HTTPException(status_code=400, detail="Version is not editable")
        
        # Get evidence items
        evidence_query = select(RFIEvidenceVersioned).where(
            and_(
                RFIEvidenceVersioned.version_id == version_id,
                RFIEvidenceVersioned.evidence_id.in_(decision_data.evidence_ids)
            )
        )
        evidence_result = await db.execute(evidence_query)
        evidence_items = evidence_result.scalars().all()
        
        if len(evidence_items) != len(decision_data.evidence_ids):
            raise HTTPException(status_code=400, detail="Some evidence items not found")
        
        # Apply decisions
        for evidence in evidence_items:
            evidence.tester_decision = decision_data.decision
            evidence.tester_notes = decision_data.notes
            evidence.tester_decided_by = current_user.user_id
            evidence.tester_decided_at = datetime.utcnow()
            
            # Update evidence status
            if decision_data.decision == Decision.APPROVED:
                evidence.evidence_status = EvidenceStatus.APPROVED
            elif decision_data.decision == Decision.REJECTED:
                evidence.evidence_status = EvidenceStatus.REJECTED
            elif decision_data.decision == Decision.REQUEST_CHANGES:
                evidence.evidence_status = EvidenceStatus.REQUEST_CHANGES
                evidence.requires_resubmission = True
            
            evidence.updated_by_id = current_user.user_id
        
        # Update version statistics
        await update_version_statistics(version, db)
        
        await db.commit()
        
        return {"message": f"Tester decision applied to {len(evidence_items)} evidence items"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error applying bulk tester decision: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/versions/{version_id}/send-to-report-owner")
async def send_to_report_owner(
    version_id: UUID,
    request_data: SendToReportOwnerRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send evidence to report owner for review"""
    try:
        # Get version with evidence
        version_query = select(RFIVersion).where(
            RFIVersion.version_id == version_id
        ).options(selectinload(RFIVersion.evidence_items))
        
        version_result = await db.execute(version_query)
        version = version_result.scalar_one_or_none()
        
        if not version:
            raise HTTPException(status_code=404, detail="Version not found")
        
        # Check all evidence has tester decisions
        evidence_without_decision = [e for e in version.evidence_items if not e.tester_decision]
        if evidence_without_decision:
            raise HTTPException(
                status_code=400,
                detail=f"{len(evidence_without_decision)} evidence items still need tester decisions"
            )
        
        # Get report owner
        phase_query = select(WorkflowPhase).where(
            WorkflowPhase.phase_id == version.phase_id
        ).options(
            selectinload(WorkflowPhase.report),
            selectinload(WorkflowPhase.cycle)
        )
        
        phase_result = await db.execute(phase_query)
        phase = phase_result.scalar_one_or_none()
        
        if not phase or not phase.report:
            raise HTTPException(status_code=404, detail="Phase or report not found")
        
        # Create assignment for report owner
        assignment_service = UniversalAssignmentService()
        
        # Count evidence by decision
        approved_count = len([e for e in version.evidence_items if e.tester_decision == Decision.APPROVED])
        rejected_count = len([e for e in version.evidence_items if e.tester_decision == Decision.REJECTED])
        request_changes_count = len([e for e in version.evidence_items if e.tester_decision == Decision.REQUEST_CHANGES])
        
        assignment = await assignment_service.create_assignment(
            db=db,
            assigned_to_id=phase.report.report_owner_id,
            assigned_by_id=current_user.user_id,
            assignment_type="RFI Evidence Review",
            priority="high",
            due_date=request_data.due_date or (datetime.utcnow() + timedelta(days=5)),
            context_data={
                "cycle_id": phase.cycle_id,
                "report_id": phase.report_id,
                "report_name": phase.report.report_name if phase.report else None,
                "cycle_name": phase.cycle.cycle_name if phase.cycle else None,
                "phase": "RFI",
                "version_id": str(version.version_id),
                "total_evidence": len(version.evidence_items),
                "approved_by_tester": approved_count,
                "rejected_by_tester": rejected_count,
                "changes_requested": request_changes_count,
                "message": request_data.message
            },
            description=f"Review RFI evidence for {phase.report.report_name}. "
                       f"{approved_count} approved, {rejected_count} rejected, "
                       f"{request_changes_count} need changes."
        )
        
        # Update version metadata
        version.report_owner_review_requested_at = datetime.utcnow()
        version.updated_by_id = current_user.user_id
        
        await db.commit()
        
        return {
            "message": "Evidence sent to report owner for review",
            "assignment_id": assignment.assignment_id,
            "evidence_count": len(version.evidence_items)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending to report owner: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/versions/{version_id}/resubmit-after-feedback")
async def resubmit_after_feedback(
    version_id: UUID,
    resubmit_data: ResubmitRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new version for resubmission after report owner feedback"""
    try:
        # Get current version
        version_query = select(RFIVersion).where(
            RFIVersion.version_id == version_id
        ).options(selectinload(RFIVersion.evidence_items))
        
        version_result = await db.execute(version_query)
        version = version_result.scalar_one_or_none()
        
        if not version:
            raise HTTPException(status_code=404, detail="Version not found")
        
        # Check that report owner has provided feedback
        if not version.report_owner_review_completed_at:
            raise HTTPException(status_code=400, detail="Report owner review not completed")
        
        # Create new version request
        version_create = RFIVersionCreate(
            carry_forward_all=True,
            carry_forward_approved_only=resubmit_data.carry_forward_approved,
            submission_deadline=version.submission_deadline,
            reminder_schedule=version.reminder_schedule,
            instructions=version.instructions
        )
        
        # Get cycle and report IDs
        phase_query = select(WorkflowPhase).where(
            WorkflowPhase.phase_id == version.phase_id
        )
        phase_result = await db.execute(phase_query)
        phase = phase_result.scalar_one_or_none()
        
        if not phase:
            raise HTTPException(status_code=404, detail="Phase not found")
        
        # Create new version
        new_version_response = await create_rfi_version(
            phase.cycle_id,
            phase.report_id,
            version_create,
            db,
            current_user
        )
        
        return new_version_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resubmitting after feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Submission Status Endpoints
@router.get("/cycles/{cycle_id}/reports/{report_id}/submission-status", response_model=List[DataOwnerSubmissionSummary])
async def get_submission_status(
    cycle_id: int,
    report_id: int,
    version_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get submission status by data owner"""
    try:
        # Get phase
        phase_query = select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == "Request Info"
            )
        )
        phase_result = await db.execute(phase_query)
        phase = phase_result.scalar_one_or_none()
        
        if not phase:
            raise HTTPException(status_code=404, detail="Request Info phase not found")
        
        # Get version
        if version_id:
            version_query = select(RFIVersion).where(
                RFIVersion.version_id == version_id
            )
        else:
            # Get latest version
            version_query = select(RFIVersion).where(
                RFIVersion.phase_id == phase.phase_id
            ).order_by(RFIVersion.version_number.desc()).limit(1)
        
        version_result = await db.execute(version_query)
        version = version_result.scalar_one_or_none()
        
        if not version:
            raise HTTPException(status_code=404, detail="No RFI version found")
        
        # Get test cases with evidence
        test_cases_query = select(CycleReportTestCase).where(
            CycleReportTestCase.phase_id == phase.phase_id
        ).options(
            selectinload(CycleReportTestCase.data_owner),
            selectinload(CycleReportTestCase.lob)
        ).order_by(
            CycleReportTestCase.data_owner_id,
            CycleReportTestCase.test_case_number
        )
        
        test_cases_result = await db.execute(test_cases_query)
        test_cases = test_cases_result.scalars().all()
        
        # Get all evidence for this version
        evidence_query = select(RFIEvidenceVersioned).where(
            RFIEvidenceVersioned.version_id == version.version_id
        )
        evidence_result = await db.execute(evidence_query)
        evidence_items = evidence_result.scalars().all()
        
        # Create evidence lookup
        evidence_by_test_case = {e.test_case_id: e for e in evidence_items}
        
        # Group by data owner
        data_owner_summaries = {}
        
        for test_case in test_cases:
            data_owner_id = test_case.data_owner_id
            
            if data_owner_id not in data_owner_summaries:
                data_owner = test_case.data_owner
                data_owner_summaries[data_owner_id] = DataOwnerSubmissionSummary(
                    data_owner_id=data_owner_id,
                    data_owner_name=f"{data_owner.first_name} {data_owner.last_name}",
                    data_owner_email=data_owner.email,
                    test_cases=[]
                )
            
            summary = data_owner_summaries[data_owner_id]
            evidence = evidence_by_test_case.get(test_case.id)
            
            # Create test case status
            test_case_status = TestCaseSubmissionStatus(
                test_case_id=test_case.id,
                test_case_number=test_case.test_case_number,
                test_case_name=test_case.test_case_name,
                sample_id=test_case.sample_id,
                attribute_name=test_case.attribute_name,
                data_owner_id=data_owner_id,
                data_owner_name=summary.data_owner_name,
                submission_deadline=test_case.submission_deadline,
                has_evidence=evidence is not None,
                evidence_type=evidence.evidence_type if evidence else None,
                submitted_at=evidence.submitted_at if evidence else None,
                evidence_status=evidence.evidence_status if evidence else None,
                tester_decision=evidence.tester_decision if evidence else None,
                report_owner_decision=evidence.report_owner_decision if evidence else None,
                final_status=evidence.final_status if evidence else None
            )
            
            # Calculate deadline info
            if test_case.submission_deadline:
                days_until = (test_case.submission_deadline - datetime.utcnow()).days
                test_case_status.days_until_deadline = days_until
                test_case_status.is_overdue = days_until < 0 and not evidence
            
            summary.test_cases.append(test_case_status)
            summary.total_assigned += 1
            
            if evidence:
                summary.submitted_count += 1
                if evidence.is_approved:
                    summary.approved_count += 1
                elif evidence.is_rejected:
                    summary.rejected_count += 1
                else:
                    summary.pending_count += 1
            else:
                summary.pending_count += 1
                if test_case_status.is_overdue:
                    summary.overdue_count += 1
            
            # Track earliest deadline
            if test_case.submission_deadline:
                if not summary.earliest_deadline or test_case.submission_deadline < summary.earliest_deadline:
                    summary.earliest_deadline = test_case.submission_deadline
        
        # Calculate percentages
        for summary in data_owner_summaries.values():
            if summary.total_assigned > 0:
                summary.submission_percentage = (summary.submitted_count / summary.total_assigned) * 100
                if summary.submitted_count > 0:
                    summary.approval_percentage = (summary.approved_count / summary.submitted_count) * 100
        
        return list(data_owner_summaries.values())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting submission status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Query Validation Endpoint
@router.post("/query-validation", response_model=QueryValidationResponse)
async def validate_query(
    validation_request: QueryValidationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Validate a query before submission"""
    try:
        # Get test case
        test_case_query = select(CycleReportTestCase).where(
            CycleReportTestCase.id == validation_request.test_case_id
        )
        test_case_result = await db.execute(test_case_query)
        test_case = test_case_result.scalar_one_or_none()
        
        if not test_case:
            raise HTTPException(status_code=404, detail="Test case not found")
        
        # Verify user is the assigned data owner
        if test_case.data_owner_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="You are not the assigned data owner for this test case")
        
        # TODO: Implement actual query validation
        # This would typically involve:
        # 1. Parsing the query
        # 2. Checking syntax
        # 3. Verifying table/column access permissions
        # 4. Executing with row limit
        # 5. Checking results contain required columns
        
        # For now, return mock response
        validation_response = QueryValidationResponse(
            validation_id=str(uuid.uuid4()),
            validation_status="success",
            execution_time_ms=150,
            row_count=100,
            column_names=["id", "name", "value", test_case.attribute_name],
            sample_rows=[
                {"id": 1, "name": "Sample 1", "value": 100, test_case.attribute_name: "Value 1"},
                {"id": 2, "name": "Sample 2", "value": 200, test_case.attribute_name: "Value 2"}
            ],
            has_primary_keys=True,
            has_target_attribute=True
        )
        
        return validation_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Helper Functions
async def get_evidence_by_id(
    evidence_id: UUID,
    db: AsyncSession,
    current_user: User
) -> RFIEvidenceResponse:
    """Get single evidence item by ID"""
    query = select(RFIEvidenceVersioned).where(
        RFIEvidenceVersioned.evidence_id == evidence_id
    ).options(
        selectinload(RFIEvidenceVersioned.test_case),
        selectinload(RFIEvidenceVersioned.data_owner),
        selectinload(RFIEvidenceVersioned.tester_decided_by_user),
        selectinload(RFIEvidenceVersioned.report_owner_decided_by_user),
        selectinload(RFIEvidenceVersioned.validated_by_user)
    )
    
    result = await db.execute(query)
    evidence = result.scalar_one_or_none()
    
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    
    response = RFIEvidenceResponse.from_orm(evidence)
    
    # Add user names
    if evidence.data_owner:
        response.data_owner_name = f"{evidence.data_owner.first_name} {evidence.data_owner.last_name}"
    if evidence.tester_decided_by_user:
        response.tester_decided_by_name = f"{evidence.tester_decided_by_user.first_name} {evidence.tester_decided_by_user.last_name}"
    if evidence.report_owner_decided_by_user:
        response.report_owner_decided_by_name = f"{evidence.report_owner_decided_by_user.first_name} {evidence.report_owner_decided_by_user.last_name}"
    
    # Add computed properties
    response.is_approved = evidence.is_approved
    response.is_rejected = evidence.is_rejected
    response.needs_resubmission = evidence.needs_resubmission
    response.final_status = evidence.final_status
    
    return response


async def update_version_statistics(version: RFIVersion, db: AsyncSession):
    """Update version statistics based on evidence"""
    # Get all evidence for this version
    evidence_query = select(RFIEvidenceVersioned).where(
        RFIEvidenceVersioned.version_id == version.version_id
    )
    evidence_result = await db.execute(evidence_query)
    evidence_items = evidence_result.scalars().all()
    
    # Reset counts
    version.submitted_count = 0
    version.approved_count = 0
    version.rejected_count = 0
    version.pending_count = 0
    version.document_evidence_count = 0
    version.data_source_evidence_count = 0
    
    # Calculate counts
    for evidence in evidence_items:
        if evidence.submitted_at:
            version.submitted_count += 1
            
            if evidence.evidence_type == "document":
                version.document_evidence_count += 1
            else:
                version.data_source_evidence_count += 1
            
            if evidence.is_approved:
                version.approved_count += 1
            elif evidence.is_rejected:
                version.rejected_count += 1
            else:
                version.pending_count += 1
    
    # Check if report owner review is complete
    if version.report_owner_review_requested_at and not version.report_owner_review_completed_at:
        # Check if all evidence has report owner decisions
        evidence_needing_review = [e for e in evidence_items 
                                 if e.tester_decision and not e.report_owner_decision]
        
        if not evidence_needing_review:
            # All evidence reviewed
            version.report_owner_review_completed_at = datetime.utcnow()
            
            # Create feedback summary
            approved_by_ro = len([e for e in evidence_items if e.report_owner_decision == Decision.APPROVED])
            rejected_by_ro = len([e for e in evidence_items if e.report_owner_decision == Decision.REJECTED])
            changes_by_ro = len([e for e in evidence_items if e.report_owner_decision == Decision.REQUEST_CHANGES])
            
            version.report_owner_feedback_summary = {
                "total_reviewed": len(evidence_items),
                "approved": approved_by_ro,
                "rejected": rejected_by_ro,
                "changes_requested": changes_by_ro,
                "completed_at": version.report_owner_review_completed_at.isoformat()
            }