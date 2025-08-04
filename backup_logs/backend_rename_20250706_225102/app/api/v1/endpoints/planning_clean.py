"""
Planning phase endpoints using clean architecture
Handles all planning phase operations including document upload, attribute management, and LLM generation
"""

import os
import uuid
from typing import List, Optional, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
import PyPDF2
import io
import json

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.auth import UserRoles, RoleChecker
from app.core.permissions import require_permission
from app.core.logging import get_logger
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
    AttributeVersionCreateRequest, AttributeVersionApprovalRequest, AttributeVersionResponse,
    AttributeVersionHistoryResponse, AttributeVersionChangeLogResponse, 
    AttributeVersionComparisonRequest, AttributeVersionComparisonResponse,
    AttributeBulkVersionRequest, AttributeBulkVersionResponse
)
from app.services.llm_service import get_llm_service
from app.services.workflow_orchestrator import WorkflowOrchestrator
from app.services.attribute_versioning_service import AttributeVersioningService
from app.core.exceptions import ValidationException, NotFoundException, BusinessLogicException

logger = get_logger(__name__)
router = APIRouter()

# File upload settings
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Role-based access control
tester_roles = [UserRoles.TESTER]
management_roles = [UserRoles.TEST_EXECUTIVE, UserRoles.REPORT_OWNER_EXECUTIVE, UserRoles.ADMIN]


@router.post("/cycles/{cycle_id}/reports/{report_id}/start", response_model=PlanningPhaseStatus)
async def start_planning_phase(
    cycle_id: int,
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> PlanningPhaseStatus:
    """Start planning phase for a report"""
    # Check permissions
    RoleChecker(tester_roles + management_roles)(current_user)
    
    # Verify cycle and report exist
    cycle_query = select(TestCycle).where(TestCycle.cycle_id == cycle_id)
    cycle_result = await db.execute(cycle_query)
    cycle = cycle_result.scalar_one_or_none()
    
    if not cycle:
        raise NotFoundException(f"Test cycle {cycle_id} not found")
    
    # Verify report exists in this cycle
    cycle_report_query = select(CycleReport).where(
        and_(
            CycleReport.cycle_id == cycle_id,
            CycleReport.report_id == report_id
        )
    ).options(selectinload(CycleReport.report))
    
    cycle_report_result = await db.execute(cycle_report_query)
    cycle_report = cycle_report_result.scalar_one_or_none()
    
    if not cycle_report:
        raise NotFoundException(f"Report {report_id} not found in cycle {cycle_id}")
    
    # Get or create workflow phase
    workflow_phase_query = select(WorkflowPhase).where(
        and_(
            WorkflowPhase.cycle_id == cycle_id,
            WorkflowPhase.report_id == report_id,
            WorkflowPhase.phase_name == "Planning"
        )
    )
    
    workflow_phase_result = await db.execute(workflow_phase_query)
    workflow_phase = workflow_phase_result.scalar_one_or_none()
    
    if workflow_phase:
        if workflow_phase.status == "Complete":
            raise BusinessLogicException("Planning phase already completed")
    else:
        # Create new workflow phase
        workflow_phase = WorkflowPhase(
            cycle_id=cycle_id,
            report_id=report_id,
            phase_name="Planning",
            status="In Progress",
            state="In Progress",
            actual_start_date=datetime.utcnow(),
            started_by=current_user.user_id
        )
        db.add(workflow_phase)
        await db.commit()
        await db.refresh(workflow_phase)
    
    return PlanningPhaseStatus(
        cycle_id=cycle_id,
        report_id=report_id,
        phase_name="Planning",
        status=workflow_phase.status,
        started_at=workflow_phase.actual_start_date,
        completed_at=workflow_phase.actual_end_date,
        documents_uploaded=0,
        attributes_created=0,
        is_complete=False
    )


@router.get("/cycles/{cycle_id}/reports/{report_id}/status", response_model=PlanningPhaseStatus)
async def get_planning_status(
    cycle_id: int,
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> PlanningPhaseStatus:
    """Get planning phase status for a report"""
    # Get workflow phase
    workflow_phase_query = select(WorkflowPhase).where(
        and_(
            WorkflowPhase.cycle_id == cycle_id,
            WorkflowPhase.report_id == report_id,
            WorkflowPhase.phase_name == "Planning"
        )
    )
    
    workflow_phase_result = await db.execute(workflow_phase_query)
    workflow_phase = workflow_phase_result.scalar_one_or_none()
    
    if not workflow_phase:
        raise NotFoundException("Planning phase not started")
    
    # Count documents
    doc_count_query = select(func.count(Document.document_id)).where(
        and_(
            Document.cycle_id == cycle_id,
            Document.report_id == report_id
        )
    )
    doc_count_result = await db.execute(doc_count_query)
    doc_count = doc_count_result.scalar() or 0
    
    # Count attributes with different filters
    attr_base_query = select(ReportAttribute).where(
        and_(
            ReportAttribute.cycle_id == cycle_id,
            ReportAttribute.report_id == report_id
        )
    )
    
    # Get all attributes
    attr_result = await db.execute(attr_base_query)
    attributes = attr_result.scalars().all()
    
    # Calculate counts
    attr_count = len(attributes)
    approved_count = sum(1 for a in attributes if getattr(a, 'approval_status', None) == 'approved')
    pk_count = sum(1 for a in attributes if a.is_primary_key)
    pk_approved_count = sum(1 for a in attributes if a.is_primary_key and getattr(a, 'approval_status', None) == 'approved')
    non_pk_approved_count = sum(1 for a in attributes if not a.is_primary_key and getattr(a, 'approval_status', None) == 'approved')
    cde_count = sum(1 for a in attributes if a.cde_flag)
    historical_issues_count = sum(1 for a in attributes if a.historical_issues_flag)
    llm_generated_count = sum(1 for a in attributes if a.llm_generated)
    manual_added_count = attr_count - llm_generated_count
    
    # Check if can complete based on new requirements:
    # 1. At least one PK attribute identified
    # 2. All PK attributes approved
    # 3. At least one non-PK attribute approved
    # 4. Document upload is NOT required
    can_complete = (
        pk_count > 0 and  # At least one PK attribute
        pk_approved_count == pk_count and  # All PK attributes approved
        non_pk_approved_count > 0  # At least one non-PK attribute approved
    )
    
    completion_requirements = []
    if pk_count == 0:
        completion_requirements.append("At least one Primary Key attribute must be identified")
    elif pk_approved_count < pk_count:
        completion_requirements.append(f"All {pk_count} Primary Key attribute(s) must be approved ({pk_approved_count}/{pk_count} approved)")
    if non_pk_approved_count == 0:
        completion_requirements.append("At least one non-Primary Key attribute must be approved")
    
    return PlanningPhaseStatus(
        cycle_id=cycle_id,
        report_id=report_id,
        status=workflow_phase.status,
        # Date fields
        planned_start_date=workflow_phase.planned_start_date,
        planned_end_date=workflow_phase.planned_end_date,
        actual_start_date=workflow_phase.actual_start_date,
        actual_end_date=workflow_phase.actual_end_date,
        # Alternative names for compatibility
        started_at=workflow_phase.actual_start_date,
        completed_at=workflow_phase.actual_end_date,
        # Metrics
        attributes_count=attr_count,
        approved_count=approved_count,
        pk_count=pk_count,
        pk_approved_count=pk_approved_count,
        cde_count=cde_count,
        historical_issues_count=historical_issues_count,
        llm_generated_count=llm_generated_count,
        manual_added_count=manual_added_count,
        can_complete=can_complete,
        completion_requirements=completion_requirements
    )


@router.post("/cycles/{cycle_id}/reports/{report_id}/documents/upload", response_model=FileUploadResponse)
async def upload_planning_document(
    cycle_id: int,
    report_id: int,
    file: UploadFile = File(...),
    document_type: str = Form(...),
    description: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> FileUploadResponse:
    """Upload planning phase documents"""
    # Check permissions
    RoleChecker(tester_roles)(current_user)
    
    # Validate file
    if not file.filename:
        raise ValidationException("No file provided")
    
    # Validate document type
    valid_types = ["planning", "regulatory", "schedule", "other"]
    if document_type not in valid_types:
        raise ValidationException(f"Invalid document type. Must be one of: {valid_types}")
    
    # Create unique filename
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    # Save file
    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        logger.error(f"Failed to save file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save file"
        )
    
    # Extract text if PDF
    extracted_text = None
    if file.content_type == "application/pdf":
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            extracted_text = ""
            for page in pdf_reader.pages:
                extracted_text += page.extract_text() + "\n"
        except Exception as e:
            logger.warning(f"Failed to extract PDF text: {e}")
    
    # Create document record
    document = Document(
        cycle_id=cycle_id,
        report_id=report_id,
        phase="Planning",
        document_type=document_type,
        document_name=file.filename,
        file_path=file_path,
        file_size=len(content),
        mime_type=file.content_type,
        description=description,
        extracted_text=extracted_text,
        uploaded_by=current_user.user_id,
        uploaded_at=datetime.utcnow()
    )
    
    db.add(document)
    await db.commit()
    await db.refresh(document)
    
    return FileUploadResponse(
        document_id=document.document_id,
        document_name=document.document_name,
        document_type=document.document_type,
        file_size=document.file_size,
        mime_type=document.mime_type,
        uploaded_at=document.uploaded_at,
        uploaded_by_name=current_user.full_name
    )


@router.get("/cycles/{cycle_id}/reports/{report_id}/documents", response_model=List[DocumentResponse])
async def get_planning_documents(
    cycle_id: int,
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[DocumentResponse]:
    """Get all planning phase documents"""
    # Query documents
    query = select(Document).where(
        and_(
            Document.cycle_id == cycle_id,
            Document.report_id == report_id,
        )
    ).order_by(Document.uploaded_at.desc())
    
    result = await db.execute(query)
    documents = result.scalars().all()
    
    return [
        DocumentResponse(
            document_id=doc.document_id,
            document_name=doc.document_name,
            document_type=doc.document_type,
            file_size=doc.file_size,
            mime_type=doc.mime_type,
            description=doc.description,
            uploaded_at=doc.uploaded_at,
            uploaded_by=doc.uploaded_by,
            phase=doc.phase,
            extracted_text=doc.extracted_text
        )
        for doc in documents
    ]


@router.delete("/cycles/{cycle_id}/reports/{report_id}/documents/{document_id}")
async def delete_planning_document(
    cycle_id: int,
    report_id: int,
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Delete a planning document"""
    # Check permissions
    RoleChecker(tester_roles + management_roles)(current_user)
    
    # Get document
    query = select(Document).where(
        and_(
            Document.document_id == document_id,
            Document.cycle_id == cycle_id,
            Document.report_id == report_id,
        )
    )
    
    result = await db.execute(query)
    document = result.scalar_one_or_none()
    
    if not document:
        raise NotFoundException("Document not found")
    
    # Check if user can delete (uploader or management)
    if document.uploaded_by != current_user.user_id and current_user.role not in management_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete documents you uploaded"
        )
    
    # Delete file from disk
    try:
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
    except Exception as e:
        logger.warning(f"Failed to delete file from disk: {e}")
    
    # Delete from database
    await db.delete(document)
    await db.commit()
    
    return {"message": "Document deleted successfully"}


@router.post("/cycles/{cycle_id}/reports/{report_id}/attributes", response_model=ReportAttributeResponse)
async def create_report_attribute(
    cycle_id: int,
    report_id: int,
    attribute: ReportAttributeCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ReportAttributeResponse:
    """Create a new report attribute"""
    # Check permissions
    RoleChecker(tester_roles)(current_user)
    
    # Verify cycle and report
    cycle_report_query = select(CycleReport).where(
        and_(
            CycleReport.cycle_id == cycle_id,
            CycleReport.report_id == report_id
        )
    )
    
    cycle_report_result = await db.execute(cycle_report_query)
    cycle_report = cycle_report_result.scalar_one_or_none()
    
    if not cycle_report:
        raise NotFoundException(f"Report {report_id} not found in cycle {cycle_id}")
    
    # Check for duplicate attribute name
    duplicate_query = select(ReportAttribute).where(
        and_(
            ReportAttribute.cycle_id == cycle_id,
            ReportAttribute.report_id == report_id,
            ReportAttribute.attribute_name == attribute.attribute_name
        )
    )
    
    duplicate_result = await db.execute(duplicate_query)
    if duplicate_result.scalar_one_or_none():
        raise ValidationException(f"Attribute '{attribute.attribute_name}' already exists")
    
    # Create attribute
    new_attribute = ReportAttribute(
        cycle_id=cycle_id,
        report_id=report_id,
        attribute_name=attribute.attribute_name,
        data_type=attribute.data_type,
        is_key=attribute.is_key,
        description=attribute.description,
        validation_rules=attribute.validation_rules,
        source_system=attribute.source_system,
        source_table=attribute.source_table,
        source_column=attribute.source_column,
        transformation_logic=attribute.transformation_logic,
        sample_values=attribute.sample_values,
        is_active=True,
        created_by=current_user.user_id,
        created_at=datetime.utcnow()
    )
    
    db.add(new_attribute)
    await db.commit()
    await db.refresh(new_attribute)
    
    return ReportAttributeResponse.from_orm(new_attribute)


@router.get("/cycles/{cycle_id}/reports/{report_id}/attributes", response_model=ReportAttributeListResponse)
async def get_report_attributes(
    cycle_id: int,
    report_id: int,
    is_key: Optional[bool] = Query(None),
    is_active: Optional[bool] = Query(True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ReportAttributeListResponse:
    """Get all attributes for a report"""
    # Build query
    query = select(ReportAttribute).where(
        and_(
            ReportAttribute.cycle_id == cycle_id,
            ReportAttribute.report_id == report_id
        )
    )
    
    if is_key is not None:
        query = query.where(ReportAttribute.is_key == is_key)
    
    if is_active is not None:
        query = query.where(ReportAttribute.is_active == is_active)
    
    query = query.order_by(ReportAttribute.attribute_name)
    
    result = await db.execute(query)
    attributes = result.scalars().all()
    
    return ReportAttributeListResponse(
        total=len(attributes),
        attributes=[ReportAttributeResponse.from_orm(attr) for attr in attributes]
    )


@router.put("/cycles/{cycle_id}/reports/{report_id}/attributes/{attribute_id}", response_model=ReportAttributeResponse)
async def update_report_attribute(
    cycle_id: int,
    report_id: int,
    attribute_id: int,
    attribute_update: ReportAttributeUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ReportAttributeResponse:
    """Update a report attribute"""
    # Check permissions
    RoleChecker(tester_roles)(current_user)
    
    # Get attribute
    query = select(ReportAttribute).where(
        and_(
            ReportAttribute.attribute_id == attribute_id,
            ReportAttribute.cycle_id == cycle_id,
            ReportAttribute.report_id == report_id
        )
    )
    
    result = await db.execute(query)
    attribute = result.scalar_one_or_none()
    
    if not attribute:
        raise NotFoundException("Attribute not found")
    
    # Update fields
    update_data = attribute_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(attribute, field, value)
    
    attribute.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(attribute)
    
    return ReportAttributeResponse.from_orm(attribute)


@router.delete("/cycles/{cycle_id}/reports/{report_id}/attributes/{attribute_id}")
async def delete_report_attribute(
    cycle_id: int,
    report_id: int,
    attribute_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Delete a report attribute (soft delete)"""
    # Check permissions
    RoleChecker(tester_roles + management_roles)(current_user)
    
    # Get attribute
    query = select(ReportAttribute).where(
        and_(
            ReportAttribute.attribute_id == attribute_id,
            ReportAttribute.cycle_id == cycle_id,
            ReportAttribute.report_id == report_id
        )
    )
    
    result = await db.execute(query)
    attribute = result.scalar_one_or_none()
    
    if not attribute:
        raise NotFoundException("Attribute not found")
    
    # Soft delete
    attribute.is_active = False
    attribute.updated_at = datetime.utcnow()
    
    await db.commit()
    
    return {"message": "Attribute deleted successfully"}


@router.post("/cycles/{cycle_id}/reports/{report_id}/complete", response_model=PlanningPhaseStatus)
async def complete_planning_phase(
    cycle_id: int,
    report_id: int,
    request_data: PlanningPhaseComplete,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> PlanningPhaseStatus:
    """Complete planning phase and move to scoping"""
    # Check permissions
    RoleChecker(tester_roles)(current_user)
    
    # Get current planning phase
    phase_query = select(WorkflowPhase).where(
        and_(
            WorkflowPhase.cycle_id == cycle_id,
            WorkflowPhase.report_id == report_id,
            WorkflowPhase.phase_name == "Planning"
        )
    )
    
    phase_result = await db.execute(phase_query)
    planning_phase = phase_result.scalar_one_or_none()
    
    if not planning_phase:
        raise NotFoundException("Planning phase not found")
    
    if planning_phase.status == "Complete":
        raise BusinessLogicException("Planning phase is already complete")
    
    # Check completion requirements first
    status = await get_planning_status(cycle_id, report_id, current_user, db)
    if not status.can_complete:
        raise BusinessLogicException(f"Cannot complete planning phase. Requirements: {', '.join(status.completion_requirements)}")
    
    # Complete planning phase
    planning_phase.status = "Complete"
    planning_phase.state = "Complete"
    planning_phase.actual_end_date = datetime.utcnow()
    planning_phase.completed_by = current_user.user_id
    if request_data.completion_notes:
        planning_phase.notes = request_data.completion_notes
    
    # Start scoping phase if it exists
    scoping_query = select(WorkflowPhase).where(
        and_(
            WorkflowPhase.cycle_id == cycle_id,
            WorkflowPhase.report_id == report_id,
            WorkflowPhase.phase_name == "Scoping"
        )
    )
    
    scoping_result = await db.execute(scoping_query)
    scoping_phase = scoping_result.scalar_one_or_none()
    
    if scoping_phase and scoping_phase.status == "Not Started":
        scoping_phase.status = "In Progress"
        scoping_phase.state = "In Progress"
        scoping_phase.actual_start_date = datetime.utcnow()
        scoping_phase.started_by = current_user.user_id
    
    await db.commit()
    
    # Get updated status
    return await get_planning_status(cycle_id, report_id, current_user, db)


@router.post("/cycles/{cycle_id}/reports/{report_id}/set-in-progress", response_model=PlanningPhaseStatus)
async def set_planning_in_progress(
    cycle_id: int,
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> PlanningPhaseStatus:
    """Set planning phase back to in progress"""
    # Check permissions
    RoleChecker(tester_roles + management_roles)(current_user)
    
    # Get workflow phase
    query = select(WorkflowPhase).where(
        and_(
            WorkflowPhase.cycle_id == cycle_id,
            WorkflowPhase.report_id == report_id,
            WorkflowPhase.phase_name == "Planning"
        )
    )
    
    result = await db.execute(query)
    workflow_phase = result.scalar_one_or_none()
    
    if not workflow_phase:
        raise NotFoundException("Planning phase not found")
    
    if workflow_phase.status == "In Progress":
        raise BusinessLogicException("Planning phase is already in progress")
    
    # Update status
    workflow_phase.status = "In Progress"
    workflow_phase.actual_end_date = None
    # workflow_phase doesn't have updated_at field
    
    await db.commit()
    
    return await get_planning_status(cycle_id, report_id, current_user, db)


@router.post("/cycles/{cycle_id}/reports/{report_id}/generate-attributes-llm", response_model=LLMAttributeGenerationResponse)
async def generate_attributes_with_llm(
    cycle_id: int,
    report_id: int,
    request_data: LLMAttributeGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> LLMAttributeGenerationResponse:
    """Generate attributes using LLM based on uploaded documents"""
    # Check permissions
    RoleChecker(tester_roles)(current_user)
    
    # Get LLM service
    llm_service = get_llm_service()
    
    # Get documents if not provided
    document_contents = []
    if request_data.use_uploaded_documents:
        docs_query = select(Document).where(
            and_(
                Document.cycle_id == cycle_id,
                Document.report_id == report_id,
                )
        )
        
        docs_result = await db.execute(docs_query)
        documents = docs_result.scalars().all()
        
        for doc in documents:
            if doc.extracted_text:
                document_contents.append({
                    "name": doc.document_name,
                    "type": doc.document_type,
                    "content": doc.extracted_text[:5000]  # Limit content
                })
    
    # Get report info
    report_query = select(Report).join(CycleReport).where(
        and_(
            CycleReport.cycle_id == cycle_id,
            CycleReport.report_id == report_id
        )
    )
    
    report_result = await db.execute(report_query)
    report = report_result.scalar_one_or_none()
    
    if not report:
        raise NotFoundException("Report not found")
    
    # Generate attributes
    try:
        result = await llm_service.generate_test_attributes(
            regulatory_context=request_data.regulatory_context or report.regulation_name,
            report_type=report.report_type,
            document_contents=document_contents,
            additional_context=request_data.additional_context,
            existing_attributes=request_data.existing_attributes
        )
        
        # Create attributes if requested
        created_attributes = []
        if request_data.auto_create:
            for attr in result["attributes"]:
                # Check if attribute already exists
                exists_query = select(ReportAttribute).where(
                    and_(
                        ReportAttribute.cycle_id == cycle_id,
                        ReportAttribute.report_id == report_id,
                        ReportAttribute.attribute_name == attr["attribute_name"]
                    )
                )
                
                exists_result = await db.execute(exists_query)
                if not exists_result.scalar_one_or_none():
                    # Create new attribute
                    new_attr = ReportAttribute(
                        cycle_id=cycle_id,
                        report_id=report_id,
                        attribute_name=attr["attribute_name"],
                        data_type=attr["data_type"],
                        is_key=attr.get("is_key", False),
                        description=attr.get("description"),
                        validation_rules=attr.get("validation_rules"),
                        source_system=attr.get("source_system"),
                        created_by=current_user.user_id,
                        created_at=datetime.utcnow(),
                        is_llm_suggested=True,
                        llm_confidence_score=attr.get("confidence_score", 0.8)
                    )
                    db.add(new_attr)
                    created_attributes.append(new_attr)
            
            if created_attributes:
                await db.commit()
        
        return LLMAttributeGenerationResponse(
            attributes=result["attributes"],
            total_generated=len(result["attributes"]),
            total_created=len(created_attributes),
            generation_metadata={
                "model": result.get("model", "unknown"),
                "timestamp": datetime.utcnow().isoformat(),
                "documents_used": len(document_contents)
            }
        )
        
    except Exception as e:
        logger.error(f"LLM generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate attributes: {str(e)}"
        )


# Attribute versioning endpoints
@router.post("/cycles/{cycle_id}/reports/{report_id}/attributes/{attribute_id}/versions", response_model=ReportAttributeResponse)
async def create_attribute_version(
    cycle_id: int,
    report_id: int,
    attribute_id: int,
    version_request: AttributeVersionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ReportAttributeResponse:
    """Create a new version of an attribute"""
    # Check permissions
    RoleChecker(tester_roles)(current_user)
    
    # Get versioning service
    versioning_service = AttributeVersioningService(db)
    
    # Create version
    new_version = await versioning_service.create_new_version(
        attribute_id=attribute_id,
        changes=version_request.changes,
        change_reason=version_request.reason,
        created_by=current_user.user_id
    )
    
    return ReportAttributeResponse.from_orm(new_version)


@router.post("/cycles/{cycle_id}/reports/{report_id}/attributes/{attribute_id}/approval")
async def approve_attribute_version(
    cycle_id: int,
    report_id: int,
    attribute_id: int,
    approval_request: AttributeVersionApprovalRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Approve or reject an attribute version"""
    # Check permissions - only management can approve
    RoleChecker(management_roles)(current_user)
    
    # Get versioning service
    versioning_service = AttributeVersioningService(db)
    
    # Process approval
    if approval_request.approved:
        result = await versioning_service.approve_version(
            version_id=approval_request.version_id,
            approved_by=current_user.user_id,
            approval_notes=approval_request.approval_notes
        )
    else:
        result = await versioning_service.reject_version(
            version_id=approval_request.version_id,
            rejected_by=current_user.user_id,
            rejection_reason=approval_request.approval_notes
        )
    
    return {
        "message": "Version approved successfully" if approval_request.approved else "Version rejected",
        "version_id": approval_request.version_id
    }


@router.get("/cycles/{cycle_id}/reports/{report_id}/attributes/{master_attribute_id}/history", response_model=AttributeVersionHistoryResponse)
async def get_attribute_version_history(
    cycle_id: int,
    report_id: int,
    master_attribute_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> AttributeVersionHistoryResponse:
    """Get version history for an attribute"""
    # Get versioning service
    versioning_service = AttributeVersioningService(db)
    
    # Get history
    history_result = await versioning_service.get_version_history(
        master_attribute_id=master_attribute_id
    )
    history = history_result.get("versions", [])
    
    return AttributeVersionHistoryResponse(
        master_attribute_id=master_attribute_id,
        versions=history,
        total_versions=len(history)
    )


@router.post("/cycles/{cycle_id}/reports/{report_id}/attributes/compare-versions", response_model=AttributeVersionComparisonResponse)
async def compare_attribute_versions(
    cycle_id: int,
    report_id: int,
    comparison_request: AttributeVersionComparisonRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> AttributeVersionComparisonResponse:
    """Compare two attribute versions"""
    # Get versioning service
    versioning_service = AttributeVersioningService(db)
    
    # Compare versions
    comparison = await versioning_service.compare_versions(
        version1_id=comparison_request.version1_id,
        version2_id=comparison_request.version2_id
    )
    
    return AttributeVersionComparisonResponse(**comparison)


@router.get("/cycles/{cycle_id}/reports/{report_id}/attributes/by-status")
async def get_attributes_by_status(
    cycle_id: int,
    report_id: int,
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get attributes grouped by approval status"""
    # Build query
    query = select(ReportAttribute).where(
        and_(
            ReportAttribute.cycle_id == cycle_id,
            ReportAttribute.report_id == report_id,
            ReportAttribute.is_active == True
        )
    )
    
    if status:
        query = query.where(ReportAttribute.approval_status == status)
    
    result = await db.execute(query)
    attributes = result.scalars().all()
    
    # Group by status
    by_status = {}
    for attr in attributes:
        status = attr.approval_status or "pending"
        if status not in by_status:
            by_status[status] = []
        by_status[status].append(ReportAttributeResponse.from_orm(attr))
    
    return {
        "by_status": by_status,
        "total": len(attributes)
    }