"""
Planning phase endpoints for workflow management
"""

import os
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, text, cast, Integer
from sqlalchemy.orm import selectinload
import PyPDF2
import io
import json

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_management
from app.core.auth import UserRoles, RoleChecker
from app.core.permissions import require_permission
from app.models.user import User
from app.models.test_cycle import TestCycle
from app.models.report import Report
from app.models.cycle_report import CycleReport
from app.models.document import Document
from app.models.report_attribute import ReportAttribute
from app.models.workflow import WorkflowPhase
from app.schemas.planning import (
    DocumentUpload, DocumentResponse, DocumentType,
    ReportAttributeCreate, ReportAttributeUpdate, ReportAttributeResponse, ReportAttributeListResponse,
    LLMAttributeGenerationRequest, LLMAttributeGenerationResponse,
    PlanningPhaseStart, PlanningPhaseStatus, PlanningPhaseComplete,
    FileUploadResponse,
    # Add versioning schemas
    AttributeVersionCreateRequest, AttributeVersionApprovalRequest, AttributeVersionResponse,
    AttributeVersionHistoryResponse, AttributeVersionChangeLogResponse, 
    AttributeVersionComparisonRequest, AttributeVersionComparisonResponse,
    AttributeBulkVersionRequest, AttributeBulkVersionResponse
)
from app.core.exceptions import ValidationException
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Role-based access control
tester_roles = [UserRoles.TESTER]
management_roles = [UserRoles.TEST_EXECUTIVE, UserRoles.REPORT_OWNER_EXECUTIVE, UserRoles.ADMIN]

# File upload settings
UPLOAD_DIR = "uploads"
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB
ALLOWED_EXTENSIONS = {'.pdf', '.doc', '.docx', '.txt', '.csv', '.xlsx', '.xls'}


async def validate_cycle_report_access(
    cycle_id: int, 
    report_id: int, 
    current_user: User, 
    db: AsyncSession,
    require_tester: bool = True
) -> CycleReport:
    """Validate user has access to cycle report and return it"""
    
    # DEBUG: Log the incoming request details
    logger.info(f"🔍 DEBUGGING: validate_cycle_report_access called")
    logger.info(f"🔍 Request: cycle_id={cycle_id}, report_id={report_id}, require_tester={require_tester}")
    logger.info(f"🔍 Current user: user_id={current_user.user_id}, email={current_user.email}, role={current_user.role}")
    
    # Get cycle report assignment
    result = await db.execute(
        select(CycleReport).options(
            selectinload(CycleReport.cycle),
            selectinload(CycleReport.report),
            selectinload(CycleReport.tester)
        ).where(
            and_(
                CycleReport.cycle_id == cycle_id,
                CycleReport.report_id == report_id
            )
        )
    )
    cycle_report = result.scalar_one_or_none()
    
    if not cycle_report:
        logger.error(f"🔍 ERROR: CycleReport not found for cycle_id={cycle_id}, report_id={report_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found in this cycle"
        )
    
    logger.info(f"🔍 Found CycleReport: cycle_id={cycle_report.cycle_id}, report_id={cycle_report.report_id}, tester_id={cycle_report.tester_id}")
    
    # Check permissions
    logger.info(f"🔍 Permission check: current_user.role={current_user.role}, require_tester={require_tester}")
    logger.info(f"🔍 Available roles: tester_roles={tester_roles}, management_roles={management_roles}")
    
    if require_tester and current_user.role == UserRoles.TESTER:
        logger.info(f"🔍 User is TESTER, checking assignment: current_user.user_id={current_user.user_id}, cycle_report.tester_id={cycle_report.tester_id}")
        if cycle_report.tester_id != current_user.user_id:
            logger.error(f"🔍 ERROR: Tester assignment mismatch! Expected user_id={cycle_report.tester_id}, got user_id={current_user.user_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not assigned as tester for this report"
            )
        logger.info(f"🔍 SUCCESS: Tester assignment validated")
    elif current_user.role not in management_roles + tester_roles:
        logger.error(f"🔍 ERROR: Role not in allowed roles! current_user.role={current_user.role}, allowed_roles={management_roles + tester_roles}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    else:
        logger.info(f"🔍 SUCCESS: User has management role or is authorized")
    
    logger.info(f"🔍 VALIDATION PASSED: User {current_user.email} has access to cycle {cycle_id}, report {report_id}")
    return cycle_report


@router.post("/{cycle_id}/reports/{report_id}/start", response_model=PlanningPhaseStatus)
async def start_planning_phase(
    cycle_id: int,
    report_id: int,
    phase_data: PlanningPhaseStart,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Start planning phase for a report in a cycle (Tester only)
    """
    # Validate access
    cycle_report = await validate_cycle_report_access(cycle_id, report_id, current_user, db)
    
    # Check if planning phase already exists
    existing_phase = await db.execute(
        select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == 'Planning'
            )
        )
    )
    
    if existing_phase.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Planning phase already started for this report"
        )
    
    # Create planning phase
    planning_phase = WorkflowPhase(
        cycle_id=cycle_id,
        report_id=report_id,
        phase_name='Planning',
        status='In Progress',
        planned_start_date=phase_data.planned_start_date,
        planned_end_date=phase_data.planned_end_date,
        actual_start_date=func.now()
    )
    
    db.add(planning_phase)
    
    # Update cycle report status
    cycle_report.status = 'In Progress'
    cycle_report.started_at = func.now()
    
    await db.commit()
    
    logger.info(f"Planning phase started for report {report_id} in cycle {cycle_id} by {current_user.email}")
    
    # Return status
    return await get_planning_phase_status(cycle_id, report_id, current_user, db)


@router.get("/{cycle_id}/reports/{report_id}/status", response_model=PlanningPhaseStatus)
async def get_planning_phase_status(
    cycle_id: int,
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get planning phase status for a report
    """
    # Validate access
    await validate_cycle_report_access(cycle_id, report_id, current_user, db, require_tester=False)
    
    # Get phase status
    phase_result = await db.execute(
        select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == 'Planning'
            )
        )
    )
    phase = phase_result.scalar_one_or_none()
    
    if not phase:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Planning phase not started"
        )
    
    # Get attribute counts and metrics
    attr_count = await db.execute(
        select(func.count(ReportAttribute.attribute_id)).where(
            and_(
                ReportAttribute.cycle_id == cycle_id,
                ReportAttribute.report_id == report_id
            )
        )
    )
    attributes_count = attr_count.scalar()
    
    # Get approved attributes count
    approved_count_result = await db.execute(
        select(func.count(ReportAttribute.attribute_id)).where(
            and_(
                ReportAttribute.cycle_id == cycle_id,
                ReportAttribute.report_id == report_id,
                ReportAttribute.approval_status == 'approved'
            )
        )
    )
    approved_count = approved_count_result.scalar()
    
    # Get CDE attributes count
    cde_count_result = await db.execute(
        select(func.count(ReportAttribute.attribute_id)).where(
            and_(
                ReportAttribute.cycle_id == cycle_id,
                ReportAttribute.report_id == report_id,
                ReportAttribute.cde_flag == True
            )
        )
    )
    cde_count = cde_count_result.scalar()
    
    # Get historical issues attributes count
    historical_issues_count_result = await db.execute(
        select(func.count(ReportAttribute.attribute_id)).where(
            and_(
                ReportAttribute.cycle_id == cycle_id,
                ReportAttribute.report_id == report_id,
                ReportAttribute.historical_issues_flag == True
            )
        )
    )
    historical_issues_count = historical_issues_count_result.scalar()
    
    # Get LLM generated attributes count
    llm_count = await db.execute(
        select(func.count(ReportAttribute.attribute_id)).where(
            and_(
                ReportAttribute.cycle_id == cycle_id,
                ReportAttribute.report_id == report_id,
                ReportAttribute.llm_generated == True
            )
        )
    )
    llm_generated_count = llm_count.scalar()
    
    manual_added_count = attributes_count - llm_generated_count
    
    # Check completion requirements
    completion_requirements = []
    can_complete = True
    
    # Must have at least one attribute
    if attributes_count == 0:
        completion_requirements.append("Create at least one attribute")
        can_complete = False
    
    # All attributes must be approved or rejected (not pending)
    if attributes_count > 0:
        pending_attributes_count = await db.execute(
            select(func.count(ReportAttribute.attribute_id)).where(
                and_(
                    ReportAttribute.cycle_id == cycle_id,
                    ReportAttribute.report_id == report_id,
                    ReportAttribute.is_latest_version == True,
                    ReportAttribute.approval_status.in_(['pending', None])
                )
            )
        )
        
        pending_count = pending_attributes_count.scalar()
        if pending_count > 0:
            completion_requirements.append(f"Approve or reject {pending_count} pending attribute(s)")
            can_complete = False
    
    if can_complete:
        completion_requirements.append("All requirements met - ready to complete")
    
    return PlanningPhaseStatus(
        cycle_id=cycle_id,
        report_id=report_id,
        status=phase.status,
        planned_start_date=phase.planned_start_date,
        planned_end_date=phase.planned_end_date,
        actual_start_date=phase.actual_start_date,
        actual_end_date=phase.actual_end_date,
        started_at=phase.actual_start_date,  # Alias for frontend compatibility
        completed_at=phase.actual_end_date,  # Alias for frontend compatibility
        attributes_count=attributes_count,
        approved_count=approved_count,
        cde_count=cde_count,
        historical_issues_count=historical_issues_count,
        llm_generated_count=llm_generated_count,
        manual_added_count=manual_added_count,
        can_complete=can_complete,
        completion_requirements=completion_requirements
    )


@router.post("/{cycle_id}/reports/{report_id}/documents/upload", response_model=FileUploadResponse)
async def upload_document(
    cycle_id: int,
    report_id: int,
    file: UploadFile = File(...),
    document_type: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload document for planning phase (Tester only)
    """
    # Validate access
    await validate_cycle_report_access(cycle_id, report_id, current_user, db)
    
    # Validate document type
    try:
        doc_type = DocumentType(document_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid document type: {document_type}"
        )
    
    # Validate file
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )
    
    # Check file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Check file size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    # Create upload directory if it doesn't exist
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    # Generate unique filename
    file_uuid = str(uuid.uuid4())
    stored_filename = f"{file_uuid}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, stored_filename)
    
    # Save file
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Create document record
    document = Document(
        cycle_id=cycle_id,
        report_id=report_id,
        document_type=doc_type.value,
        document_name=file.filename,
        file_path=file_path,
        file_size=len(content),
        mime_type=file.content_type or "application/octet-stream",
        uploaded_by_user_id=current_user.user_id
    )
    
    db.add(document)
    await db.commit()
    await db.refresh(document)
    
    logger.info(f"Document uploaded: {file.filename} for report {report_id} in cycle {cycle_id}")
    
    return FileUploadResponse(
        success=True,
        document=DocumentResponse(
            document_id=document.document_id,
            cycle_id=document.cycle_id,
            report_id=document.report_id,
            document_type=document.document_type,
            original_filename=document.document_name,
            stored_filename=os.path.basename(document.file_path),
            file_size=document.file_size,
            version_number=document.version,
            uploaded_by=document.uploaded_by_user_id,
            is_latest=document.is_latest_version,
            created_at=document.created_at
        ),
        message=f"Document '{file.filename}' uploaded successfully"
    )


@router.get("/{cycle_id}/reports/{report_id}/documents", response_model=List[DocumentResponse])
async def list_documents(
    cycle_id: int,
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List documents for a report in planning phase
    """
    # Validate access
    await validate_cycle_report_access(cycle_id, report_id, current_user, db, require_tester=False)
    
    # Get documents
    result = await db.execute(
        select(Document).where(
            and_(
                Document.cycle_id == cycle_id,
                Document.report_id == report_id
            )
        ).order_by(Document.created_at.desc())
    )
    documents = result.scalars().all()
    
    return [DocumentResponse(
        document_id=doc.document_id,
        cycle_id=doc.cycle_id,
        report_id=doc.report_id,
        document_type=doc.document_type,
        original_filename=doc.document_name,
        stored_filename=os.path.basename(doc.file_path),
        file_size=doc.file_size,
        version_number=doc.version,
        uploaded_by=doc.uploaded_by_user_id,
        is_latest=doc.is_latest_version,
        created_at=doc.created_at
    ) for doc in documents]


@router.delete("/{cycle_id}/reports/{report_id}/documents/{document_id}")
async def delete_document(
    cycle_id: int,
    report_id: int,
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete document for planning phase (Tester only)
    """
    # Validate access
    await validate_cycle_report_access(cycle_id, report_id, current_user, db)
    
    # Get document
    result = await db.execute(
        select(Document).where(
            and_(
                Document.document_id == document_id,
                Document.cycle_id == cycle_id,
                Document.report_id == report_id
            )
        )
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    try:
        # Delete physical file if it exists
        if document.file_path and os.path.exists(document.file_path):
            os.remove(document.file_path)
        
        # Delete database record
        await db.delete(document)
        await db.commit()
        
        logger.info(f"Document deleted: {document.document_name} (ID: {document_id})")
        
        return {"message": "Document deleted successfully"}
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to delete document {document_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )


@router.post("/{cycle_id}/reports/{report_id}/attributes", response_model=ReportAttributeResponse)
async def create_attribute(
    cycle_id: int,
    report_id: int,
    attribute_data: ReportAttributeCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create report attribute manually (Tester only)
    """
    # DEBUG: Log the incoming attribute creation request
    logger.info(f"🔍 CREATE_ATTRIBUTE: cycle_id={cycle_id}, report_id={report_id}")
    logger.info(f"🔍 CREATE_ATTRIBUTE: current_user={current_user.user_id} ({current_user.email})")
    logger.info(f"🔍 CREATE_ATTRIBUTE: attribute_name={attribute_data.attribute_name}")
    
    # Validate access
    await validate_cycle_report_access(cycle_id, report_id, current_user, db)
    
    # Check if attribute name already exists for this report
    existing_attr = await db.execute(
        select(ReportAttribute).where(
            and_(
                ReportAttribute.cycle_id == cycle_id,
                ReportAttribute.report_id == report_id,
                ReportAttribute.attribute_name == attribute_data.attribute_name
            )
        )
    )
    
    if existing_attr.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Attribute with this name already exists for this report"
        )
    
    # Create attribute - handle both enum objects and string values
    data_type_value = None
    if attribute_data.data_type:
        if hasattr(attribute_data.data_type, 'value'):
            data_type_value = attribute_data.data_type.value
        else:
            data_type_value = str(attribute_data.data_type)
    
    mandatory_flag_value = attribute_data.mandatory_flag
    if hasattr(attribute_data.mandatory_flag, 'value'):
        mandatory_flag_value = attribute_data.mandatory_flag.value
    else:
        mandatory_flag_value = str(attribute_data.mandatory_flag)
    
    attribute = ReportAttribute(
        cycle_id=cycle_id,
        report_id=report_id,
        attribute_name=attribute_data.attribute_name,
        description=attribute_data.description,
        data_type=data_type_value,
        mandatory_flag=mandatory_flag_value,
        cde_flag=attribute_data.cde_flag,
        historical_issues_flag=attribute_data.historical_issues_flag,
        llm_generated=False,
        tester_notes=attribute_data.tester_notes,
        # Include enhanced LLM fields
        validation_rules=attribute_data.validation_rules,
        typical_source_documents=attribute_data.typical_source_documents,
        keywords_to_look_for=attribute_data.keywords_to_look_for,
        testing_approach=attribute_data.testing_approach,
        # Required versioning fields
        version_created_by=current_user.user_id,
        version_number=1,
        is_latest_version=True,
        is_active=True,
        approval_status='pending'
    )
    
    db.add(attribute)
    await db.commit()
    await db.refresh(attribute)
    
    logger.info(f"Manual attribute created: {attribute_data.attribute_name} for report {report_id}")
    
    return ReportAttributeResponse.model_validate(attribute)


@router.get("/{cycle_id}/reports/{report_id}/attributes", response_model=ReportAttributeListResponse)
async def list_attributes(
    cycle_id: int,
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List report attributes for planning phase
    """
    # Validate access
    await validate_cycle_report_access(cycle_id, report_id, current_user, db, require_tester=False)
    
    # Get attributes ordered by line item number incrementally
    result = await db.execute(
        select(ReportAttribute).where(
            and_(
                ReportAttribute.cycle_id == cycle_id,
                ReportAttribute.report_id == report_id
            )
        ).order_by(
            cast(ReportAttribute.line_item_number, Integer).nulls_last(),
            ReportAttribute.attribute_name
        )
    )
    attributes = result.scalars().all()
    
    return ReportAttributeListResponse(
        attributes=[ReportAttributeResponse.model_validate(attr) for attr in attributes],
        total=len(attributes)
    )


@router.put("/{cycle_id}/reports/{report_id}/attributes/{attribute_id}", response_model=ReportAttributeResponse)
async def update_attribute(
    cycle_id: int,
    report_id: int,
    attribute_id: int,
    attribute_data: ReportAttributeUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update report attribute directly (Tester only)
    During planning phase, all updates are direct - no automatic versioning.
    Use explicit versioning endpoints if version control is needed.
    """
    # Validate access
    await validate_cycle_report_access(cycle_id, report_id, current_user, db)
    
    # Get attribute
    result = await db.execute(
        select(ReportAttribute).where(
            and_(
                ReportAttribute.attribute_id == attribute_id,
                ReportAttribute.cycle_id == cycle_id,
                ReportAttribute.report_id == report_id
            )
        )
    )
    attribute = result.scalar_one_or_none()
    
    if not attribute:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attribute not found"
        )
    
    # Direct update for all attributes during planning phase
    logger.info(f"Direct update for attribute: {attribute.attribute_name} (status: {attribute.approval_status})")
    
    update_data = attribute_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field in ['data_type', 'mandatory_flag'] and value:
            if hasattr(value, 'value'):
                value = value.value
        setattr(attribute, field, value)
    
    await db.commit()
    await db.refresh(attribute)
    
    logger.info(f"Attribute updated: {attribute.attribute_name}")
    
    return ReportAttributeResponse.model_validate(attribute)


@router.delete("/{cycle_id}/reports/{report_id}/attributes/{attribute_id}")
async def delete_attribute(
    cycle_id: int,
    report_id: int,
    attribute_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete report attribute (Tester only)
    """
    # Validate access
    await validate_cycle_report_access(cycle_id, report_id, current_user, db)
    
    # Get attribute
    result = await db.execute(
        select(ReportAttribute).where(
            and_(
                ReportAttribute.attribute_id == attribute_id,
                ReportAttribute.cycle_id == cycle_id,
                ReportAttribute.report_id == report_id
            )
        )
    )
    attribute = result.scalar_one_or_none()
    
    try:
        # In planning phase, there should be no test executions yet
        # Use raw SQL delete to avoid loading relationships that have schema issues
        
        # First verify the attribute exists and belongs to this cycle/report
        if not attribute:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attribute not found"
            )
        
        # Delete using raw SQL to avoid relationship loading issues
        delete_query = text(
            "DELETE FROM report_attributes WHERE attribute_id = :attribute_id AND cycle_id = :cycle_id AND report_id = :report_id"
        )
        
        result = await db.execute(delete_query, {
            "attribute_id": attribute_id,
            "cycle_id": cycle_id,
            "report_id": report_id
        })
        
        if result.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attribute not found or already deleted"
            )
        
        await db.commit()
        
        logger.info(f"Attribute deleted: {attribute.attribute_name} (ID: {attribute_id})")
        
        return {"message": "Attribute deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to delete attribute {attribute_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete attribute: {str(e)}"
        )


@router.post("/{cycle_id}/reports/{report_id}/complete", response_model=PlanningPhaseStatus)
async def complete_planning_phase(
    cycle_id: int,
    report_id: int,
    completion_data: PlanningPhaseComplete,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Complete planning phase (Tester only)
    """
    # Validate access
    await validate_cycle_report_access(cycle_id, report_id, current_user, db)
    
    # Check completion requirements
    status_response = await get_planning_phase_status(cycle_id, report_id, current_user, db)
    
    if not status_response.can_complete:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot complete planning phase. Requirements: {', '.join(status_response.completion_requirements)}"
        )
    
    if not completion_data.attributes_confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must confirm that attributes have been reviewed"
        )
    
    if not completion_data.documents_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must confirm that documents have been verified"
        )
    
    # Update planning phase
    phase_result = await db.execute(
        select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == 'Planning'
            )
        )
    )
    phase = phase_result.scalar_one()
    
    phase.status = 'Complete'
    phase.actual_end_date = func.now()
    
    await db.commit()
    
    logger.info(f"Planning phase completed for report {report_id} in cycle {cycle_id}")
    
    return await get_planning_phase_status(cycle_id, report_id, current_user, db)


@router.post("/{cycle_id}/reports/{report_id}/set-in-progress", response_model=PlanningPhaseStatus)
async def set_planning_phase_in_progress(
    cycle_id: int,
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Manually set planning phase status to 'In Progress' (Tester only)
    """
    # Validate access
    await validate_cycle_report_access(cycle_id, report_id, current_user, db)
    
    # Get planning phase
    phase_result = await db.execute(
        select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == 'Planning'
            )
        )
    )
    phase = phase_result.scalar_one_or_none()
    
    if not phase:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Planning phase not found"
        )
    
    # Only allow setting to 'In Progress' if currently 'Not Started'
    if phase.status != 'Not Started':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot set phase to 'In Progress'. Current status: {phase.status}"
        )
    
    # Update phase status
    phase.status = 'In Progress'
    phase.actual_start_date = func.now()
    
    await db.commit()
    
    logger.info(f"Planning phase set to 'In Progress' for report {report_id} in cycle {cycle_id}")
    
    return await get_planning_phase_status(cycle_id, report_id, current_user, db)


@router.post("/{cycle_id}/reports/{report_id}/generate-attributes-llm-async")
async def generate_attributes_with_llm_async(
    cycle_id: int,
    report_id: int,
    request: LLMAttributeGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate attributes using LLM asynchronously - returns job ID immediately
    """
    from app.core.background_jobs import job_manager
    import asyncio
    
    # Validate access
    await validate_cycle_report_access(cycle_id, report_id, current_user, db)
    
    # Create background job
    job_id = job_manager.create_job(
        "llm_attribute_generation",
        metadata={
            "cycle_id": cycle_id,
            "report_id": report_id,
            "user_id": current_user.user_id,
            "provider": request.provider,
            "discovery_provider": request.discovery_provider,
            "details_provider": request.details_provider
        }
    )
    
    # Start the background task
    asyncio.create_task(
        _run_llm_generation_job(job_id, cycle_id, report_id, request, current_user.user_id)
    )
    
    return {
        "job_id": job_id,
        "message": "LLM attribute generation started",
        "status": "pending",
        "cycle_id": cycle_id,
        "report_id": report_id
    }

@router.post("/{cycle_id}/reports/{report_id}/generate-attributes-llm", response_model=LLMAttributeGenerationResponse)
async def generate_attributes_with_llm(
    cycle_id: int,
    report_id: int,
    request: LLMAttributeGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate attributes using LLM with CDE and historical issues matching
    """
    from app.services.llm_service import get_llm_service
    import json
    
    # Validate access
    await validate_cycle_report_access(cycle_id, report_id, current_user, db)
    
    # Get uploaded documents
    documents = await db.execute(
        select(Document).where(
            and_(
                Document.cycle_id == cycle_id,
                Document.report_id == report_id
            )
        )
    )
    docs = documents.scalars().all()
    
    # Find regulatory specification (optional)
    # No longer require any documents to be uploaded
    reg_spec = next((doc for doc in docs if doc.document_type == 'Regulatory Specification'), None)
    
    # Read regulatory specification content with proper file type handling
    regulatory_spec_content = ""
    if reg_spec and os.path.exists(reg_spec.file_path):
        logger.info(f"📖 Reading regulatory specification content from: {reg_spec.file_path}")
        try:
            file_extension = os.path.splitext(reg_spec.file_path)[1].lower()
            logger.info(f"📄 File type detected: {file_extension}")
            
            if file_extension == '.pdf':
                # Extract text from PDF file
                try:
                    with open(reg_spec.file_path, 'rb') as pdf_file:
                        pdf_reader = PyPDF2.PdfReader(pdf_file)
                        pdf_text = ""
                        
                        logger.info(f"📄 PDF file detected - extracting text from {len(pdf_reader.pages)} pages")
                        
                        for page_num, page in enumerate(pdf_reader.pages):
                            try:
                                page_text = page.extract_text()
                                if page_text:
                                    pdf_text += f"\n--- Page {page_num + 1} ---\n{page_text}"
                                logger.debug(f"📄 Extracted {len(page_text)} characters from page {page_num + 1}")
                            except Exception as e:
                                logger.warning(f"📄 Failed to extract text from page {page_num + 1}: {str(e)}")
                        
                        if pdf_text.strip():
                            regulatory_spec_content = f"PDF Document: {reg_spec.document_name}\n\nExtracted Content:\n{pdf_text}"
                            logger.info(f"📄 Successfully extracted {len(pdf_text)} characters from PDF file")
                        else:
                            # Fallback if no text could be extracted
                            regulatory_spec_content = f"PDF Document: {reg_spec.document_name}\n\nNote: PDF text extraction yielded no readable content. This may be a scanned/image-based PDF.\n\nDocument Type: {reg_spec.document_type}\nFile Size: {reg_spec.file_size} bytes"
                            logger.warning(f"📄 PDF text extraction yielded no readable content")
                            
                except Exception as e:
                    logger.error(f"📄 Failed to extract PDF content: {str(e)}")
                    # Fallback to placeholder content
                    regulatory_spec_content = f"PDF Document: {reg_spec.document_name}\n\nNote: PDF content extraction failed due to: {str(e)}\nUsing document metadata for context.\n\nDocument Type: {reg_spec.document_type}\nFile Size: {reg_spec.file_size} bytes"
                
                logger.info(f"📄 Final PDF content length: {len(regulatory_spec_content)} characters")
            elif file_extension in ['.txt', '.csv']:
                # Try different encodings for text files
                encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
                for encoding in encodings:
                    try:
                        with open(reg_spec.file_path, 'r', encoding=encoding) as f:
                            regulatory_spec_content = f.read()
                        logger.info(f"📖 Successfully read text file with {encoding} encoding ({len(regulatory_spec_content)} characters)")
                        break
                    except UnicodeDecodeError:
                        continue
                if not regulatory_spec_content:
                    raise Exception("Could not decode text file with any common encoding")
            else:
                # For other file types (DOC, DOCX, etc.), provide placeholder
                regulatory_spec_content = f"Document: {reg_spec.document_name}\n\nNote: {file_extension} files require specialized parsing. Using document metadata for context.\n\nDocument Type: {reg_spec.document_type}\nFile Size: {reg_spec.file_size} bytes"
                logger.info(f"📄 {file_extension} file detected - using placeholder content ({len(regulatory_spec_content)} characters)")
                
        except Exception as e:
            logger.error(f"❌ Failed to read regulatory specification: {str(e)}")
            # Provide fallback content instead of failing completely
            regulatory_spec_content = f"Document: {reg_spec.document_name}\n\nNote: Could not read file content due to: {str(e)}\nUsing document metadata for context.\n\nDocument Type: {reg_spec.document_type}\nFile Size: {reg_spec.file_size} bytes"
            logger.info(f"📄 Using fallback content due to read error ({len(regulatory_spec_content)} characters)")
    elif reg_spec:
        logger.error(f"❌ Regulatory specification file not found: {reg_spec.file_path}")
        regulatory_spec_content = f"Regulatory Specification file uploaded but not accessible: {reg_spec.document_name}"
    else:
        logger.info("📄 No regulatory specification document provided - using generic context")
        regulatory_spec_content = "No regulatory specification document provided. Generating attributes based on user context and regulatory report/schedule information."
    
    # Parse CDE list if provided
    cde_attributes = []
    if request.include_cde_matching:
        cde_doc = next((doc for doc in docs if doc.document_type == 'CDE List'), None)
        if cde_doc and os.path.exists(cde_doc.file_path):
            try:
                with open(cde_doc.file_path, 'r') as f:
                    content = f.read()
                    # Simple parsing - assume one attribute per line or JSON array
                    if content.strip().startswith('['):
                        cde_attributes = json.loads(content)
                    else:
                        cde_attributes = [line.strip() for line in content.split('\n') if line.strip()]
            except Exception as e:
                logger.warning(f"Failed to parse CDE list: {str(e)}")
    
    # Parse historical issues list if provided
    historical_attributes = []
    if request.include_historical_matching:
        hist_doc = next((doc for doc in docs if doc.document_type == 'Historical Issues'), None)
        if hist_doc and os.path.exists(hist_doc.file_path):
            try:
                with open(hist_doc.file_path, 'r') as f:
                    content = f.read()
                    # Simple parsing - assume one attribute per line or JSON array
                    if content.strip().startswith('['):
                        historical_attributes = json.loads(content)
                    else:
                        historical_attributes = [line.strip() for line in content.split('\n') if line.strip()]
            except Exception as e:
                logger.warning(f"Failed to parse historical issues list: {str(e)}")
    
    # Call LLM service
    try:
        llm_service = get_llm_service()
        
        # Build comprehensive regulatory context with document content
        user_context = request.regulatory_context or f"Generate attributes for cycle {cycle_id} report {report_id}"
        
        # Combine user context with actual document content
        regulatory_context = f"""
USER CONTEXT:
{user_context}

REGULATORY SPECIFICATION DOCUMENT:
{regulatory_spec_content}

ADDITIONAL INFORMATION:
- CDE Attributes Available: {len(cde_attributes)} attributes
- Historical Issues Available: {len(historical_attributes)} issues
- Report: {request.regulatory_report or 'Not specified'}
- Schedule: {request.schedule or 'Not specified'}
"""
        
        logger.info(f"📋 Built comprehensive regulatory context for sync call:")
        logger.info(f"   👤 User context length: {len(user_context)} characters")
        logger.info(f"   📄 Document content length: {len(regulatory_spec_content)} characters") 
        logger.info(f"   📋 Total context length: {len(regulatory_context)} characters")
        logger.info(f"   🏷️ CDE attributes: {len(cde_attributes)}")
        logger.info(f"   📜 Historical issues: {len(historical_attributes)}")
        
        # Use the appropriate generation method based on provider selection
        if request.provider == 'hybrid' or (request.discovery_provider and request.details_provider):
            # Explicit hybrid mode: Gemini discovery + Claude details
            result = await llm_service._generate_attributes_two_phase(
                regulatory_context=regulatory_context,
                report_type="Regulatory Report",
                preferred_discovery=request.discovery_provider or 'gemini',
                preferred_details=request.details_provider or 'claude',
                regulatory_report=request.regulatory_report,
                schedule=request.schedule
            )
        elif request.provider == 'hybrid_legacy':
            # Legacy hybrid approach
            result = await llm_service.generate_test_attributes_hybrid(
                regulatory_context=regulatory_context,
                report_type="Regulatory Report",
                regulatory_report=request.regulatory_report,
                schedule=request.schedule
            )
        else:
            # Standard generation with preferred provider
            result = await llm_service.generate_test_attributes(
                regulatory_context=regulatory_context,
                report_type="Regulatory Report",
                preferred_provider=request.provider,
                regulatory_report=request.regulatory_report,
                schedule=request.schedule
            )
        
        if not result.get("success") or not result.get("attributes"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"LLM generation failed: {result.get('error', 'No attributes generated')}"
            )
        
        # Process generated attributes and match against CDE/historical lists
        saved_attributes = []
        for attr in result.get("attributes", []):
            try:
                # Check for CDE match
                is_cde = False
                if cde_attributes:
                    attr_name = attr.get("attribute_name", "").lower()
                    is_cde = any(cde.lower() in attr_name or attr_name in cde.lower() 
                               for cde in cde_attributes)
                
                # Check for historical issues match
                has_historical = False
                if historical_attributes:
                    attr_name = attr.get("attribute_name", "").lower()
                    has_historical = any(hist.lower() in attr_name or attr_name in hist.lower() 
                                       for hist in historical_attributes)
                
                # Create attribute in database
                db_attribute = ReportAttribute(
                    cycle_id=cycle_id,
                    report_id=report_id,
                    attribute_name=attr.get("attribute_name", ""),
                    description=attr.get("description", ""),
                    data_type=attr.get("data_type", "String"),
                    mandatory_flag=attr.get("mandatory_flag", "Optional"),
                    cde_flag=is_cde,
                    historical_issues_flag=has_historical,
                    llm_generated=True,
                    llm_rationale=attr.get("llm_rationale", "Generated by LLM"),
                    validation_rules=attr.get("validation_rules", ""),
                    typical_source_documents=attr.get("typical_source_documents", ""),
                    keywords_to_look_for=attr.get("keywords_to_look_for", ""),
                    testing_approach=attr.get("testing_approach", ""),
                    risk_score=attr.get("risk_score"),
                    llm_risk_rationale=attr.get("llm_risk_rationale"),
                    # Required versioning fields
                    version_created_by=current_user.user_id,
                    version_number=1,
                    is_latest_version=True,
                    is_active=True,
                    approval_status='pending'
                )
                
                db.add(db_attribute)
                saved_attributes.append(db_attribute)
                
            except Exception as e:
                logger.error(f"Failed to save attribute {attr.get('attribute_name')}: {str(e)}")
        
        await db.commit()
        
        # Refresh saved attributes to get IDs
        for attr in saved_attributes:
            await db.refresh(attr)
        
        # Prepare response
        return LLMAttributeGenerationResponse(
            success=True,
            attributes=[ReportAttributeResponse.model_validate(attr) for attr in saved_attributes],
            total_generated=len(result.get("attributes", [])),
            total_saved=len(saved_attributes),
            cde_matches=sum(1 for attr in saved_attributes if attr.cde_flag),
            historical_matches=sum(1 for attr in saved_attributes if attr.historical_issues_flag),
            provider_used=result.get("discovery_provider", "unknown") + " + " + result.get("details_provider", "unknown") if result.get("method") == "two_phase" else result.get("provider", "unknown"),
            method=result.get("method", "standard")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"LLM attribute generation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate attributes: {str(e)}"
        )

async def _run_llm_generation_job(job_id: str, cycle_id: int, report_id: int, request: LLMAttributeGenerationRequest, user_id: int):
    """
    Background job function for LLM attribute generation with comprehensive logging
    """
    from app.core.background_jobs import job_manager
    from app.services.llm_service import get_llm_service
    from app.core.database import get_db
    import json
    
    logger.info(f"🚀 STARTING BACKGROUND LLM JOB {job_id}")
    logger.info(f"📊 JOB PARAMETERS: cycle_id={cycle_id}, report_id={report_id}, user_id={user_id}")
    logger.info(f"🔧 REQUEST DETAILS: provider={request.provider}, regulatory_report={request.regulatory_report}, schedule={request.schedule}")
    logger.info(f"📝 REGULATORY CONTEXT: {request.regulatory_context}")
    
    try:
        # Get database session
        logger.info(f"🔌 Getting database session for job {job_id}")
        async for db in get_db():
            logger.info(f"✅ Database session acquired for job {job_id}")
            
            # Get uploaded documents
            logger.info(f"📄 Fetching documents for cycle {cycle_id}, report {report_id}")
            documents = await db.execute(
                select(Document).where(
                    and_(
                        Document.cycle_id == cycle_id,
                        Document.report_id == report_id
                    )
                )
            )
            docs = documents.scalars().all()
            logger.info(f"📄 Found {len(docs)} documents: {[doc.document_type for doc in docs]}")
            
            # Find regulatory specification (optional)
            # No longer require any documents to be uploaded
            reg_spec = next((doc for doc in docs if doc.document_type == 'Regulatory Specification'), None)
            logger.info(f"📋 Regulatory specification: {'Found' if reg_spec else 'NOT FOUND'}")
            
            # Read regulatory specification content with proper file type handling
            regulatory_spec_content = ""
            if reg_spec and os.path.exists(reg_spec.file_path):
                logger.info(f"📖 Reading regulatory specification content from: {reg_spec.file_path}")
                try:
                    file_extension = os.path.splitext(reg_spec.file_path)[1].lower()
                    logger.info(f"📄 File type detected: {file_extension}")
                    
                    if file_extension == '.pdf':
                        # Extract text from PDF file
                        try:
                            with open(reg_spec.file_path, 'rb') as pdf_file:
                                pdf_reader = PyPDF2.PdfReader(pdf_file)
                                pdf_text = ""
                                
                                logger.info(f"📄 PDF file detected - extracting text from {len(pdf_reader.pages)} pages")
                                
                                for page_num, page in enumerate(pdf_reader.pages):
                                    try:
                                        page_text = page.extract_text()
                                        if page_text:
                                            pdf_text += f"\n--- Page {page_num + 1} ---\n{page_text}"
                                        logger.debug(f"📄 Extracted {len(page_text)} characters from page {page_num + 1}")
                                    except Exception as e:
                                        logger.warning(f"📄 Failed to extract text from page {page_num + 1}: {str(e)}")
                        
                        except Exception as e:
                            logger.error(f"📄 Failed to extract PDF content: {str(e)}")
                            # Fallback to placeholder content
                            regulatory_spec_content = f"PDF Document: {reg_spec.document_name}\n\nNote: PDF content extraction failed due to: {str(e)}\nUsing document metadata for context.\n\nDocument Type: {reg_spec.document_type}\nFile Size: {reg_spec.file_size} bytes"
                        
                        logger.info(f"📄 Final PDF content length: {len(regulatory_spec_content)} characters")
                    elif file_extension in ['.txt', '.csv']:
                        # Try different encodings for text files
                        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
                        for encoding in encodings:
                            try:
                                with open(reg_spec.file_path, 'r', encoding=encoding) as f:
                                    regulatory_spec_content = f.read()
                                logger.info(f"📖 Successfully read text file with {encoding} encoding ({len(regulatory_spec_content)} characters)")
                                break
                            except UnicodeDecodeError:
                                continue
                        if not regulatory_spec_content:
                            raise Exception("Could not decode text file with any common encoding")
                    else:
                        # For other file types (DOC, DOCX, etc.), provide placeholder
                        regulatory_spec_content = f"Document: {reg_spec.document_name}\n\nNote: {file_extension} files require specialized parsing. Using document metadata for context.\n\nDocument Type: {reg_spec.document_type}\nFile Size: {reg_spec.file_size} bytes"
                        logger.info(f"📄 {file_extension} file detected - using placeholder content ({len(regulatory_spec_content)} characters)")
                    
                    logger.info(f"📖 First 200 characters: {regulatory_spec_content[:200]}...")
                except Exception as e:
                    logger.error(f"❌ Failed to read regulatory specification: {str(e)}")
                    # Provide fallback content instead of failing completely
                    regulatory_spec_content = f"Document: {reg_spec.document_name}\n\nNote: Could not read file content due to: {str(e)}\nUsing document metadata for context.\n\nDocument Type: {reg_spec.document_type}\nFile Size: {reg_spec.file_size} bytes"
                    logger.info(f"📄 Using fallback content due to read error ({len(regulatory_spec_content)} characters)")
            elif reg_spec:
                logger.error(f"❌ Regulatory specification file not found: {reg_spec.file_path}")
                regulatory_spec_content = f"Regulatory Specification file uploaded but not accessible: {reg_spec.document_name}"
            else:
                logger.info("📄 No regulatory specification document provided - using generic context")
                regulatory_spec_content = "No regulatory specification document provided. Generating attributes based on user context and regulatory report/schedule information."
            
            # Parse CDE and historical lists (same logic as sync version)
            logger.info(f"🔍 Parsing CDE and historical lists...")
            cde_attributes = []
            if request.include_cde_matching:
                logger.info(f"🏷️ CDE matching enabled")
                cde_doc = next((doc for doc in docs if doc.document_type == 'CDE List'), None)
                if cde_doc and os.path.exists(cde_doc.file_path):
                    logger.info(f"🏷️ Found CDE document: {cde_doc.file_path}")
                    try:
                        with open(cde_doc.file_path, 'r') as f:
                            content = f.read()
                            if content.strip().startswith('['):
                                cde_attributes = json.loads(content)
                            else:
                                cde_attributes = [line.strip() for line in content.split('\n') if line.strip()]
                        logger.info(f"🏷️ Loaded {len(cde_attributes)} CDE attributes")
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to parse CDE list: {str(e)}")
                else:
                    logger.info(f"🏷️ No CDE document found or file doesn't exist")
            else:
                logger.info(f"🏷️ CDE matching disabled")
            
            historical_attributes = []
            if request.include_historical_matching:
                logger.info(f"📜 Historical matching enabled")
                hist_doc = next((doc for doc in docs if doc.document_type == 'Historical Issues'), None)
                if hist_doc and os.path.exists(hist_doc.file_path):
                    logger.info(f"📜 Found historical document: {hist_doc.file_path}")
                    try:
                        with open(hist_doc.file_path, 'r') as f:
                            content = f.read()
                            if content.strip().startswith('['):
                                historical_attributes = json.loads(content)
                            else:
                                historical_attributes = [line.strip() for line in content.split('\n') if line.strip()]
                        logger.info(f"📜 Loaded {len(historical_attributes)} historical attributes")
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to parse historical issues list: {str(e)}")
                else:
                    logger.info(f"📜 No historical document found or file doesn't exist")
            else:
                logger.info(f"📜 Historical matching disabled")
            
            # Call LLM service with job tracking
            logger.info(f"🤖 Initializing LLM service for job {job_id}")
            llm_service = get_llm_service()
            
            # Build comprehensive regulatory context with document content
            user_context = request.regulatory_context or f"Generate attributes for cycle {cycle_id} report {report_id}"
            
            # Combine user context with actual document content
            full_regulatory_context = f"""
USER CONTEXT:
{user_context}

REGULATORY SPECIFICATION DOCUMENT:
{regulatory_spec_content}

ADDITIONAL INFORMATION:
- CDE Attributes Available: {len(cde_attributes)} attributes
- Historical Issues Available: {len(historical_attributes)} issues
- Report: {request.regulatory_report or 'Not specified'}
- Schedule: {request.schedule or 'Not specified'}
"""
            
            logger.info(f"📋 Built comprehensive regulatory context:")
            logger.info(f"   👤 User context length: {len(user_context)} characters")
            logger.info(f"   📄 Document content length: {len(regulatory_spec_content)} characters") 
            logger.info(f"   📋 Total context length: {len(full_regulatory_context)} characters")
            logger.info(f"   🏷️ CDE attributes: {len(cde_attributes)}")
            logger.info(f"   📜 Historical issues: {len(historical_attributes)}")
            
            # Use the appropriate generation method based on provider selection
            logger.info(f"🔀 Determining LLM generation method...")
            if request.provider == 'hybrid' or (request.discovery_provider and request.details_provider):
                # Explicit hybrid mode: Gemini discovery + Claude details
                logger.info(f"🔀 Using explicit hybrid mode: discovery={request.discovery_provider or 'gemini'}, details={request.details_provider or 'claude'}")
                result = await llm_service._generate_attributes_two_phase(
                    regulatory_context=full_regulatory_context,
                    report_type="Regulatory Report",
                    preferred_discovery=request.discovery_provider or 'gemini',
                    preferred_details=request.details_provider or 'claude',
                    regulatory_report=request.regulatory_report,
                    schedule=request.schedule,
                    job_id=job_id  # Pass job ID for progress tracking
                )
            elif request.provider == 'hybrid_legacy':
                # Legacy hybrid approach
                logger.info(f"🔀 Using legacy hybrid approach")
                result = await llm_service.generate_test_attributes_hybrid(
                    regulatory_context=full_regulatory_context,
                    report_type="Regulatory Report",
                    regulatory_report=request.regulatory_report,
                    schedule=request.schedule
                )
            else:
                # Standard generation with preferred provider
                logger.info(f"🔀 Using standard generation with provider: {request.provider}")
                result = await llm_service.generate_test_attributes(
                    regulatory_context=full_regulatory_context,
                    report_type="Regulatory Report",
                    preferred_provider=request.provider,
                    regulatory_report=request.regulatory_report,
                    schedule=request.schedule
                )
            
            logger.info(f"🤖 LLM generation completed for job {job_id}")
            logger.info(f"🎯 LLM result summary: success={result.get('success')}, attributes_count={len(result.get('attributes', []))}, method={result.get('method', 'unknown')}")
            if result.get('discovery_provider'):
                logger.info(f"🎯 LLM providers used: discovery={result.get('discovery_provider')}, details={result.get('details_provider')}")
            else:
                logger.info(f"🎯 LLM provider used: {result.get('provider', 'unknown')}")
            
            if not result.get("success") or not result.get("attributes"):
                error_msg = f"LLM generation failed: {result.get('error', 'No attributes generated')}"
                logger.error(f"❌ {error_msg}")
                job_manager.complete_job(job_id, error=error_msg)
                return
            
            # Process and save attributes to database
            logger.info(f"💾 Starting database save process for {len(result.get('attributes', []))} attributes")
            logger.info(f"👤 Using user_id {user_id} for version_created_by field")
            saved_attributes = []
            failed_attributes = []
            
            for i, attr in enumerate(result.get("attributes", [])):
                attr_name = attr.get("attribute_name", f"unknown_attribute_{i}")
                logger.info(f"💾 Processing attribute {i+1}/{len(result.get('attributes', []))}: {attr_name}")
                try:
                    # Check for CDE match
                    is_cde = False
                    if cde_attributes:
                        attr_name_lower = attr.get("attribute_name", "").lower()
                        is_cde = any(cde.lower() in attr_name_lower or attr_name_lower in cde.lower() 
                                   for cde in cde_attributes)
                        if is_cde:
                            logger.info(f"🏷️ CDE match found for: {attr_name}")
                    
                    # Check for historical issues match
                    has_historical = False
                    if historical_attributes:
                        attr_name_lower = attr.get("attribute_name", "").lower()
                        has_historical = any(hist.lower() in attr_name_lower or attr_name_lower in hist.lower() 
                                           for hist in historical_attributes)
                        if has_historical:
                            logger.info(f"📜 Historical match found for: {attr_name}")
                    
                    # Log the attribute data being created
                    logger.info(f"🏗️ Creating ReportAttribute object for: {attr_name}")
                    logger.info(f"   📋 Data type: {attr.get('data_type', 'String')}")
                    logger.info(f"   📋 Mandatory: {attr.get('mandatory_flag', 'Optional')}")
                    logger.info(f"   📋 CDE flag: {is_cde}")
                    logger.info(f"   📋 Historical flag: {has_historical}")
                    logger.info(f"   📋 Version fields: user_id={user_id}, version=1, latest=True, active=True")
                    
                    # Create attribute in database
                    db_attribute = ReportAttribute(
                        cycle_id=cycle_id,
                        report_id=report_id,
                        attribute_name=attr.get("attribute_name", ""),
                        description=attr.get("description", ""),
                        data_type=attr.get("data_type", "String"),
                        mandatory_flag=attr.get("mandatory_flag", "Optional"),
                        cde_flag=is_cde,
                        historical_issues_flag=has_historical,
                        llm_generated=True,
                        llm_rationale=attr.get("llm_rationale", "Generated by LLM"),
                        validation_rules=attr.get("validation_rules", ""),
                        typical_source_documents=attr.get("typical_source_documents", ""),
                        keywords_to_look_for=attr.get("keywords_to_look_for", ""),
                        testing_approach=attr.get("testing_approach", ""),
                        risk_score=attr.get("risk_score"),
                        llm_risk_rationale=attr.get("llm_risk_rationale"),
                        # Required versioning fields
                        version_created_by=user_id,
                        version_number=1,
                        is_latest_version=True,
                        is_active=True,
                        approval_status='pending'
                    )
                    
                    logger.info(f"📦 Adding attribute to database session: {attr_name}")
                    db.add(db_attribute)
                    
                    logger.info(f"🔄 Flushing to database to check for errors: {attr_name}")
                    # Try to flush to catch any immediate database errors
                    await db.flush()
                    
                    saved_attributes.append(db_attribute)
                    logger.info(f"✅ Successfully saved attribute: {attr_name} (ID will be assigned after commit)")
                    
                except Exception as e:
                    failed_attributes.append(attr_name)
                    logger.error(f"❌ Failed to save attribute {attr_name}: {str(e)}")
                    logger.error(f"❌ Exception type: {type(e).__name__}")
                    logger.error(f"❌ Full exception details: {repr(e)}")
                    logger.error(f"❌ Attribute data: {attr}")
                    
                    # Rollback the current transaction to continue with other attributes
                    logger.info(f"🔄 Rolling back transaction due to error with {attr_name}")
                    await db.rollback()
                    
                    # Re-add the successfully created attributes
                    logger.info(f"🔄 Re-adding {len(saved_attributes)} previously successful attributes")
                    for saved_attr in saved_attributes:
                        db.add(saved_attr)
            
            # Final commit
            logger.info(f"💾 Committing transaction with {len(saved_attributes)} attributes")
            if failed_attributes:
                logger.warning(f"⚠️ Failed to save {len(failed_attributes)} attributes: {failed_attributes}")
            
            await db.commit()
            logger.info(f"✅ Transaction committed successfully")
            
            # Get final counts
            cde_matches = sum(1 for attr in saved_attributes if attr.cde_flag)
            historical_matches = sum(1 for attr in saved_attributes if attr.historical_issues_flag)
            
            # Complete the job with results
            job_result = {
                "success": True,
                "total_generated": len(result.get("attributes", [])),
                "total_saved": len(saved_attributes),
                "total_failed": len(failed_attributes),
                "cde_matches": cde_matches,
                "historical_matches": historical_matches,
                "provider_used": result.get("discovery_provider", "unknown") + " + " + result.get("details_provider", "unknown") if result.get("method") == "two_phase" else result.get("provider", "unknown"),
                "method": result.get("method", "standard"),
                "failed_attributes": failed_attributes
            }
            
            logger.info(f"🎯 JOB COMPLETION SUMMARY:")
            logger.info(f"   📊 Total generated: {job_result['total_generated']}")
            logger.info(f"   ✅ Total saved: {job_result['total_saved']}")
            logger.info(f"   ❌ Total failed: {job_result['total_failed']}")
            logger.info(f"   🏷️ CDE matches: {job_result['cde_matches']}")
            logger.info(f"   📜 Historical matches: {job_result['historical_matches']}")
            logger.info(f"   🤖 Provider used: {job_result['provider_used']}")
            logger.info(f"   🔧 Method: {job_result['method']}")
            
            job_manager.complete_job(job_id, result=job_result)
            
            logger.info(f"🎉 Background LLM job {job_id} completed successfully!")
            break
            
    except Exception as e:
        logger.error(f"💥 Background LLM job {job_id} failed with exception: {str(e)}")
        logger.error(f"💥 Exception type: {type(e).__name__}")
        logger.error(f"💥 Full exception details: {repr(e)}")
        import traceback
        logger.error(f"💥 Traceback:\n{traceback.format_exc()}")
        job_manager.complete_job(job_id, error=str(e))


# ATTRIBUTE VERSIONING ENDPOINTS

@router.post("/{cycle_id}/reports/{report_id}/attributes/{attribute_id}/versions", response_model=ReportAttributeResponse)
async def create_attribute_version(
    cycle_id: int,
    report_id: int,
    attribute_id: int,
    version_request: AttributeVersionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new version of an attribute with updated data
    """
    # Import here to avoid circular imports
    from app.services.attribute_versioning_service import AttributeVersioningService
    
    # Validate access
    await validate_cycle_report_access(cycle_id, report_id, current_user, db)
    
    # Verify attribute belongs to this cycle/report
    result = await db.execute(
        select(ReportAttribute).where(
            and_(
                ReportAttribute.attribute_id == attribute_id,
                ReportAttribute.cycle_id == cycle_id,
                ReportAttribute.report_id == report_id
            )
        )
    )
    
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attribute not found in this cycle/report"
        )
    
    try:
        versioning_service = AttributeVersioningService(db)
        
        # Extract updated data from request
        updated_data = {}
        for field, value in version_request.model_dump(exclude_unset=True).items():
            if field not in ['change_reason', 'version_notes'] and value is not None:
                updated_data[field] = value
        
        # Create new version
        new_version = await versioning_service.create_new_version(
            attribute_id=attribute_id,
            updated_by_user_id=current_user.user_id,
            updated_data=updated_data,
            change_reason=version_request.change_reason,
            version_notes=version_request.version_notes
        )
        
        logger.info(f"Created attribute version {new_version.attribute_id} v{new_version.version_number} by {current_user.email}")
        
        return ReportAttributeResponse.model_validate(new_version)
        
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create attribute version: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create attribute version"
        )


@router.post("/{cycle_id}/reports/{report_id}/attributes/{attribute_id}/approval")
async def approve_reject_attribute_version(
    cycle_id: int,
    report_id: int,
    attribute_id: int,
    approval_request: AttributeVersionApprovalRequest,
    current_user: User = Depends(require_management),
    db: AsyncSession = Depends(get_db)
):
    """
    Approve or reject an attribute version (Management only)
    """
    # Import here to avoid circular imports
    from app.services.attribute_versioning_service import AttributeVersioningService
    
    # Validate access  
    await validate_cycle_report_access(cycle_id, report_id, current_user, db, require_tester=False)
    
    # Verify attribute belongs to this cycle/report
    result = await db.execute(
        select(ReportAttribute).where(
            and_(
                ReportAttribute.attribute_id == attribute_id,
                ReportAttribute.cycle_id == cycle_id,
                ReportAttribute.report_id == report_id
            )
        )
    )
    
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attribute not found in this cycle/report"
        )
    
    try:
        versioning_service = AttributeVersioningService(db)
        
        if approval_request.action == "approve":
            change_log = await versioning_service.approve_version(
                attribute_id=attribute_id,
                approved_by_user_id=current_user.user_id,
                approval_notes=approval_request.approval_notes
            )
            action_text = "approved"
        else:  # reject
            change_log = await versioning_service.reject_version(
                attribute_id=attribute_id,
                rejected_by_user_id=current_user.user_id,
                rejection_reason=approval_request.approval_notes
            )
            action_text = "rejected"
        
        logger.info(f"Attribute {attribute_id} {action_text} by {current_user.email}")
        
        return {
            "success": True,
            "message": f"Attribute version {action_text} successfully",
            "change_log_id": change_log.log_id
        }
        
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to {approval_request.action} attribute version: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to {approval_request.action} attribute version"
        )


@router.get("/{cycle_id}/reports/{report_id}/attributes/{master_attribute_id}/history", response_model=AttributeVersionHistoryResponse)
async def get_attribute_version_history(
    cycle_id: int,
    report_id: int,
    master_attribute_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get complete version history for an attribute
    """
    # Import here to avoid circular imports
    from app.services.attribute_versioning_service import AttributeVersioningService
    
    # Validate access
    await validate_cycle_report_access(cycle_id, report_id, current_user, db, require_tester=False)
    
    try:
        versioning_service = AttributeVersioningService(db)
        history = await versioning_service.get_version_history(master_attribute_id)
        
        return AttributeVersionHistoryResponse.model_validate(history)
        
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get version history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get version history"
        )


@router.post("/{cycle_id}/reports/{report_id}/attributes/compare-versions", response_model=AttributeVersionComparisonResponse)
async def compare_attribute_versions(
    cycle_id: int,
    report_id: int,
    comparison_request: AttributeVersionComparisonRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Compare two versions of an attribute
    """
    # Import here to avoid circular imports
    from app.services.attribute_versioning_service import AttributeVersioningService
    
    # Validate access
    await validate_cycle_report_access(cycle_id, report_id, current_user, db, require_tester=False)
    
    # Verify both attributes belong to this cycle/report
    for attr_id in [comparison_request.version_a_id, comparison_request.version_b_id]:
        result = await db.execute(
            select(ReportAttribute).where(
                and_(
                    ReportAttribute.attribute_id == attr_id,
                    ReportAttribute.cycle_id == cycle_id,
                    ReportAttribute.report_id == report_id
                )
            )
        )
        
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Attribute {attr_id} not found in this cycle/report"
            )
    
    try:
        versioning_service = AttributeVersioningService(db)
        
        comparison = await versioning_service.compare_versions(
            version_a_id=comparison_request.version_a_id,
            version_b_id=comparison_request.version_b_id,
            compared_by_user_id=current_user.user_id,
            comparison_notes=comparison_request.comparison_notes
        )
        
        return AttributeVersionComparisonResponse.model_validate(comparison)
        
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to compare versions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compare versions"
        )


@router.get("/{cycle_id}/reports/{report_id}/attributes/by-status")
async def get_attributes_by_status(
    cycle_id: int,
    report_id: int,
    status_filter: Optional[str] = Query(None, description="Filter by approval status: pending, approved, rejected"),
    version_filter: Optional[str] = Query("latest", description="Version filter: latest, active, all"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get attributes filtered by approval status and version type
    """
    # Import here to avoid circular imports
    from app.services.attribute_versioning_service import AttributeVersioningService
    
    # Validate access
    await validate_cycle_report_access(cycle_id, report_id, current_user, db, require_tester=False)
    
    try:
        versioning_service = AttributeVersioningService(db)
        
        attributes = await versioning_service.get_attributes_by_status(
            cycle_id=cycle_id,
            report_id=report_id,
            status=status_filter,
            version_filter=version_filter or "latest"
        )
        
        return {
            "attributes": [ReportAttributeResponse.model_validate(attr) for attr in attributes],
            "total": len(attributes),
            "filter_applied": {
                "status": status_filter,
                "version": version_filter or "latest"
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get attributes by status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get attributes by status"
        ) 