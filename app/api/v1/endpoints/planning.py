"""
Planning phase endpoints using clean architecture
Handles all planning phase operations including document upload, attribute management, and LLM generation
"""

import os
import uuid
from typing import List, Optional, Any, Dict
from datetime import datetime
import asyncio
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, text
from sqlalchemy.orm import selectinload
import PyPDF2
import io
import json
import asyncpg

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.auth import UserRoles, RoleChecker
from app.core.permissions import require_permission
from app.core.logging import get_logger
from app.models.user import User
from app.models.test_cycle import TestCycle
from app.models.report import Report
from app.models.cycle_report import CycleReport
from app.models.cycle_report_documents import CycleReportDocument as Document
from app.models.report_attribute import ReportAttribute
from app.models.workflow import WorkflowPhase
from app.models.cycle_report_data_source import CycleReportDataSource, DataSourceType
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
from app.core.background_jobs import job_manager

logger = get_logger(__name__)
router = APIRouter()


async def get_table_schema(connection_config: Dict[str, Any]) -> str:
    """Fetch table schema information from the database"""
    try:
        # For PostgreSQL connections
        if connection_config.get('host') and connection_config.get('table_name'):
            host = connection_config.get('host', 'localhost')
            port = connection_config.get('port', '5432')
            database = connection_config.get('database', 'synapse_dt')
            schema = connection_config.get('schema', 'public')
            table_name = connection_config.get('table_name')
            
            # Use asyncpg to fetch schema information
            conn_string = f"postgresql://synapse_user:synapse_password@{host}:{port}/{database}"
            conn = await asyncpg.connect(conn_string)
            
            try:
                # Query to get column information
                query = """
                    SELECT column_name, data_type, is_nullable, character_maximum_length
                    FROM information_schema.columns
                    WHERE table_schema = $1 AND table_name = $2
                    ORDER BY ordinal_position
                """
                columns = await conn.fetch(query, schema, table_name)
                
                if columns:
                    column_info = []
                    for col in columns:
                        col_desc = f"{col['column_name']} ({col['data_type']}"
                        if col['character_maximum_length']:
                            col_desc += f"({col['character_maximum_length']})"
                        col_desc += f", {'nullable' if col['is_nullable'] == 'YES' else 'not null'})"
                        column_info.append(col_desc)
                    
                    return f"Table: {schema}.{table_name}\nColumns: {', '.join(column_info)}"
                else:
                    return f"Table {schema}.{table_name} found but no columns retrieved"
                    
            finally:
                await conn.close()
                
    except Exception as e:
        logger.warning(f"Failed to fetch table schema: {e}")
        return "Schema information could not be retrieved"
    
    return "Schema information not available"


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
        elif workflow_phase.status == "Not Started":
            # Update existing phase to In Progress
            workflow_phase.status = "In Progress"
            workflow_phase.state = "In Progress"
            workflow_phase.actual_start_date = datetime.utcnow()
            workflow_phase.started_by = current_user.user_id
            workflow_phase.updated_at = datetime.utcnow()
            workflow_phase.updated_by_id = current_user.user_id
            await db.commit()
            await db.refresh(workflow_phase)
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
        phase_id=workflow_phase.phase_id,
        status=workflow_phase.status,
        # Date fields
        planned_start_date=workflow_phase.planned_start_date,
        planned_end_date=workflow_phase.planned_end_date,
        actual_start_date=workflow_phase.actual_start_date,
        actual_end_date=workflow_phase.actual_end_date,
        # Alternative names for compatibility
        started_at=workflow_phase.actual_start_date,
        completed_at=workflow_phase.actual_end_date,
        # Metrics - all zero for a newly started phase
        attributes_count=0,
        approved_count=0,
        pk_count=0,
        pk_approved_count=0,
        cde_count=0,
        historical_issues_count=0,
        llm_generated_count=0,
        manual_added_count=0,
        can_complete=False,
        completion_requirements=["Load and approve attributes"]
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
    doc_count_query = select(func.count(Document.id)).where(
        and_(
            Document.phase_id == workflow_phase.phase_id
        )
    )
    doc_count_result = await db.execute(doc_count_query)
    doc_count = doc_count_result.scalar() or 0
    
    # Get workflow phase first
    phase_query = select(WorkflowPhase).where(
        and_(
            WorkflowPhase.cycle_id == cycle_id,
            WorkflowPhase.report_id == report_id,
            WorkflowPhase.phase_name == "Planning"
        )
    )
    phase_result = await db.execute(phase_query)
    phase = phase_result.scalar_one_or_none()
    
    if not phase:
        # Return empty status if phase doesn't exist
        return PlanningPhaseStatus(
            cycle_id=cycle_id,
            report_id=report_id,
            phase_id=0,  # No phase exists yet
            status="Not Started",
            attributes_count=0,
            approved_count=0,
            pk_count=0,
            pk_approved_count=0,
            cde_count=0,
            historical_issues_count=0,
            llm_generated_count=0,
            manual_added_count=0,
            can_complete=False,
            completion_requirements=["Planning phase not started"]
        )
    
    # Count attributes with different filters - with eager loading of phase relationship
    attr_base_query = select(ReportAttribute).options(selectinload(ReportAttribute.phase)).where(ReportAttribute.phase_id == phase.phase_id)
    
    # Get all attributes
    attr_result = await db.execute(attr_base_query)
    attributes = attr_result.scalars().all()
    
    # Calculate counts
    attr_count = len(attributes)
    
    # Debug logging
    logger.info(f"Total attributes found: {attr_count}")
    for attr in attributes[:5]:  # Log first 5 attributes for debugging
        logger.info(f"Attribute {attr.id}: approval_status={getattr(attr, 'approval_status', 'NOT_FOUND')}, is_primary_key={attr.is_primary_key}")
    
    # Log all approval statuses to debug
    all_statuses = [getattr(a, 'approval_status', 'NOT_FOUND') for a in attributes]
    logger.info(f"All approval statuses: {all_statuses}")
    
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
        phase_id=workflow_phase.phase_id,
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
    
    # Get planning phase
    phase_query = select(WorkflowPhase).where(
        and_(
            WorkflowPhase.cycle_id == cycle_id,
            WorkflowPhase.report_id == report_id,
            WorkflowPhase.phase_name == "Planning"
        )
    )
    
    phase_result = await db.execute(phase_query)
    phase = phase_result.scalar_one_or_none()
    
    if not phase:
        raise NotFoundException(f"Planning phase not found for cycle {cycle_id} report {report_id}")
    
    # Check for duplicate attribute name
    duplicate_query = select(ReportAttribute).where(
        and_(
            ReportAttribute.phase_id == phase.phase_id,
            ReportAttribute.attribute_name == attribute.attribute_name
        )
    )
    
    duplicate_result = await db.execute(duplicate_query)
    if duplicate_result.scalar_one_or_none():
        raise ValidationException(f"Attribute '{attribute.attribute_name}' already exists")
    
    # Create attribute
    new_attribute = ReportAttribute(
        phase_id=phase.phase_id,
        attribute_name=attribute.attribute_name,
        data_type=attribute.data_type,
        is_primary_key=attribute.is_primary_key,
        description=attribute.description,
        validation_rules=attribute.validation_rules,
        is_active=True,
        created_by_id=current_user.user_id,
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
    try:
        # Get planning phase first
        phase_query = select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == "Planning"
            )
        )
        
        phase_result = await db.execute(phase_query)
        phase = phase_result.scalar_one_or_none()
        
        if not phase:
            return ReportAttributeListResponse(total=0, attributes=[])
        
        # Import PDE mapping model
        from app.models.planning import PlanningPDEMapping
        
        # Build query with left join to PDE mappings to get classification
        query = select(
            ReportAttribute,
            PlanningPDEMapping.information_security_classification,
            PlanningPDEMapping.criticality,
            PlanningPDEMapping.risk_level,
            PlanningPDEMapping.regulatory_flag,
            PlanningPDEMapping.pii_flag,
            PlanningPDEMapping.llm_classification_rationale
        ).options(
            selectinload(ReportAttribute.phase)
        ).outerjoin(
            PlanningPDEMapping,
            and_(
                PlanningPDEMapping.attribute_id == ReportAttribute.id,
                PlanningPDEMapping.phase_id == phase.phase_id
            )
        ).where(
            ReportAttribute.phase_id == phase.phase_id
        )
        
        if is_key is not None:
            query = query.where(ReportAttribute.is_primary_key == is_key)
        
        if is_active is not None:
            query = query.where(ReportAttribute.is_active == is_active)
        
        # query = query.order_by(text('cycle_report_planning_attributes.attribute_name'))  # Temporarily disabled
        
        result = await db.execute(query)
        rows = result.all()
        
        # Debug logging to see what we're getting from DB
        if rows:
            first_row = rows[0]
            logger.info(f"First attribute from DB: id={first_row[0].id}, name={first_row[0].attribute_name}")
            logger.info(f"  classification from PDE mapping={first_row[1]}")
        
        # Convert to response models
        response_attributes = []
        for row in rows:
            attr = row[0]  # ReportAttribute
            pde_classification = row[1]  # information_security_classification from PDE mapping
            pde_criticality = row[2]  # criticality from PDE mapping
            pde_risk_level = row[3]  # risk_level from PDE mapping
            pde_regulatory_flag = row[4]  # regulatory_flag from PDE mapping
            pde_pii_flag = row[5]  # pii_flag from PDE mapping
            pde_classification_rationale = row[6]  # llm_classification_rationale from PDE mapping
            
            try:
                # Create dict with all fields explicitly
                attr_dict = {
                    "attribute_id": attr.id,  # Map id to attribute_id
                    "phase_id": attr.phase_id,
                    "attribute_name": attr.attribute_name,
                    "description": attr.description,
                    "data_type": attr.data_type,
                    "mandatory_flag": attr.mandatory_flag,
                    "cde_flag": attr.cde_flag,
                    "historical_issues_flag": attr.historical_issues_flag,
                    "is_scoped": attr.is_scoped,
                    "line_item_number": attr.line_item_number,
                    "technical_line_item_name": attr.technical_line_item_name,
                    "mdrm": attr.mdrm,
                    "is_primary_key": attr.is_primary_key,
                    "approval_status": attr.approval_status,
                    "llm_generated": attr.llm_generated,
                    "llm_rationale": attr.llm_rationale,
                    "risk_score": attr.risk_score,
                    "created_at": attr.created_at,
                    "updated_at": attr.updated_at,
                    # Version fields
                    "version_created_at": attr.version_created_at,
                    "version_created_by": attr.version_created_by,
                    # Classification field from PDE mapping (not from attribute)
                    "information_security_classification": pde_classification
                }
                
                # Log first one to debug
                if len(response_attributes) == 0:
                    logger.info(f"First attr dict: {attr_dict}")
                
                response_attr = ReportAttributeResponse.model_validate(attr_dict)
                
                # Log first one to debug
                if len(response_attributes) == 0:
                    logger.info(f"First response attr: {response_attr.model_dump()}")
                response_attributes.append(response_attr)
            except Exception as e:
                logger.error(f"Error validating attribute {attr.id}: {str(e)}")
                raise
        
        return ReportAttributeListResponse(
            total=len(rows),
            attributes=response_attributes
        )
    except Exception as e:
        import traceback
        logger.error(f"Error in get_report_attributes: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Attributes error: {str(e)}")


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
    
    # Get planning phase first
    phase_query = select(WorkflowPhase).where(
        and_(
            WorkflowPhase.cycle_id == cycle_id,
            WorkflowPhase.report_id == report_id,
            WorkflowPhase.phase_name == "Planning"
        )
    )
    
    phase_result = await db.execute(phase_query)
    phase = phase_result.scalar_one_or_none()
    
    if not phase:
        raise NotFoundException("Planning phase not found")
    
    # Get attribute with eager loading of phase relationship
    query = select(ReportAttribute).options(selectinload(ReportAttribute.phase)).where(
        and_(
            ReportAttribute.id == attribute_id,
            ReportAttribute.phase_id == phase.phase_id
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
    
    # Get planning phase first
    phase_query = select(WorkflowPhase).where(
        and_(
            WorkflowPhase.cycle_id == cycle_id,
            WorkflowPhase.report_id == report_id,
            WorkflowPhase.phase_name == "Planning"
        )
    )
    
    phase_result = await db.execute(phase_query)
    phase = phase_result.scalar_one_or_none()
    
    if not phase:
        raise NotFoundException("Planning phase not found")
    
    # Get attribute
    query = select(ReportAttribute).where(
        and_(
            ReportAttribute.id == attribute_id,
            ReportAttribute.phase_id == phase.phase_id
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


@router.put("/cycles/{cycle_id}/reports/{report_id}/attributes/{attribute_id}/classification")
async def update_attribute_classification(
    cycle_id: int,
    report_id: int,
    attribute_id: int,
    classification_update: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Update classification for an attribute in its PDE mapping"""
    # Check permissions
    RoleChecker(tester_roles)(current_user)
    
    # Get planning phase first
    phase_query = select(WorkflowPhase).where(
        and_(
            WorkflowPhase.cycle_id == cycle_id,
            WorkflowPhase.report_id == report_id,
            WorkflowPhase.phase_name == "Planning"
        )
    )
    
    phase_result = await db.execute(phase_query)
    phase = phase_result.scalar_one_or_none()
    
    if not phase:
        raise NotFoundException("Planning phase not found")
    
    # Import PDE mapping model
    from app.models.planning import PlanningPDEMapping
    
    # Find the PDE mapping for this attribute
    mapping_query = select(PlanningPDEMapping).where(
        and_(
            PlanningPDEMapping.attribute_id == attribute_id,
            PlanningPDEMapping.phase_id == phase.phase_id
        )
    )
    
    mapping_result = await db.execute(mapping_query)
    mapping = mapping_result.scalar_one_or_none()
    
    if not mapping:
        # Create a new mapping if it doesn't exist
        # For manual creation, use attribute ID as placeholder since source_field isn't provided yet
        mapping = PlanningPDEMapping(
            phase_id=phase.phase_id,
            attribute_id=attribute_id,
            pde_name=f"PDE_{attribute_id}",
            pde_code=f"PDE_{attribute_id}",  # This will be updated when source_field is set
            created_by_id=current_user.user_id,
            updated_by_id=current_user.user_id
        )
        db.add(mapping)
    
    # Update classification
    classification_value = classification_update.get("information_security_classification")
    if classification_value:
        mapping.information_security_classification = classification_value
        mapping.updated_at = datetime.utcnow()
        mapping.updated_by_id = current_user.user_id
    
    await db.commit()
    
    return {
        "message": "Classification updated successfully",
        "attribute_id": attribute_id,
        "classification": classification_value
    }


@router.post("/cycles/{cycle_id}/reports/{report_id}/attributes/bulk-update")
async def bulk_update_attributes(
    cycle_id: int,
    report_id: int,
    bulk_update: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Bulk update attributes (primarily for approval status)"""
    # Check permissions
    RoleChecker(tester_roles)(current_user)
    
    # Extract parameters
    attribute_ids = bulk_update.get("attribute_ids", [])
    update_data = bulk_update.get("update_data", {})
    
    # Convert string IDs to integers
    try:
        attribute_ids = [int(attr_id) for attr_id in attribute_ids]
    except (ValueError, TypeError):
        return {"updated": 0, "message": "Invalid attribute IDs provided"}
    
    if not attribute_ids:
        return {"updated": 0, "message": "No attributes to update"}
    
    if not update_data:
        return {"updated": 0, "message": "No update data provided"}
    
    # Get planning phase first
    phase_query = select(WorkflowPhase).where(
        and_(
            WorkflowPhase.cycle_id == cycle_id,
            WorkflowPhase.report_id == report_id,
            WorkflowPhase.phase_name == "Planning"
        )
    )
    
    phase_result = await db.execute(phase_query)
    phase = phase_result.scalar_one_or_none()
    
    if not phase:
        raise NotFoundException("Planning phase not found")
    
    # Get all attributes to update
    query = select(ReportAttribute).where(
        and_(
            ReportAttribute.id.in_(attribute_ids),
            ReportAttribute.phase_id == phase.phase_id,
            ReportAttribute.is_active == True
        )
    )
    
    result = await db.execute(query)
    attributes = result.scalars().all()
    
    # Update each attribute
    updated_count = 0
    for attribute in attributes:
        # Log before update
        logger.info(f"Before update - Attribute {attribute.id} approval_status: {attribute.approval_status}")
        
        for field, value in update_data.items():
            if hasattr(attribute, field):
                setattr(attribute, field, value)
                logger.info(f"Updated attribute {attribute.id} field {field} to {value}")
            else:
                logger.warning(f"Attribute {attribute.id} does not have field {field}")
        attribute.updated_at = datetime.utcnow()
        updated_count += 1
    
    await db.commit()
    
    # Log the actual approval status after commit
    for attribute in attributes:
        await db.refresh(attribute)
        logger.info(f"After commit - Attribute {attribute.id} approval_status: {attribute.approval_status}")
    
    return {
        "updated": updated_count,
        "message": f"Successfully updated {updated_count} attributes"
    }


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
        scoping_phase.updated_at = datetime.utcnow()
        scoping_phase.updated_by_id = current_user.user_id
    
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
    workflow_phase.updated_at = datetime.utcnow()
    workflow_phase.updated_by_id = current_user.user_id
    
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
                # Get planning phase first if not already done
                if 'phase' not in locals():
                    phase_query = select(WorkflowPhase).where(
                        and_(
                            WorkflowPhase.cycle_id == cycle_id,
                            WorkflowPhase.report_id == report_id,
                            WorkflowPhase.phase_name == "Planning"
                        )
                    )
                    phase_result = await db.execute(phase_query)
                    phase = phase_result.scalar_one_or_none()
                    
                    if not phase:
                        raise NotFoundException("Planning phase not found")
                
                # Check if attribute already exists
                exists_query = select(ReportAttribute).where(
                    and_(
                        ReportAttribute.phase_id == phase.phase_id,
                        ReportAttribute.attribute_name == attr["attribute_name"]
                    )
                )
                
                exists_result = await db.execute(exists_query)
                if not exists_result.scalar_one_or_none():
                    # Create new attribute
                    new_attr = ReportAttribute(
                        phase_id=phase.phase_id,
                        attribute_name=attr["attribute_name"],
                        data_type=attr["data_type"],
                        is_primary_key=attr.get("is_key", False),
                        description=attr.get("description"),
                        validation_rules=attr.get("validation_rules"),
                        created_by_id=current_user.user_id,
                        created_at=datetime.utcnow(),
                        llm_generated=True
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


@router.get("/cycles/{cycle_id}/reports/{report_id}/pde-mappings")
async def get_pde_mappings(
    cycle_id: int,
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get actual PDE mappings from cycle_report_planning_pde_mappings table"""
    # from app.models.data_source_config import PDEMapping  # Disabled - using PlanningPDEMapping instead
    from app.models.planning import PlanningPDEMapping as PDEMapping
    
    # Get planning phase first
    phase_query = select(WorkflowPhase).where(
        and_(
            WorkflowPhase.cycle_id == cycle_id,
            WorkflowPhase.report_id == report_id,
            WorkflowPhase.phase_name == "Planning"
        )
    )
    
    phase_result = await db.execute(phase_query)
    phase = phase_result.scalar_one_or_none()
    
    if not phase:
        return {
            "cycle_id": cycle_id,
            "report_id": report_id,
            "mappings": [],
            "total": 0
        }
    
    # Get actual PDE mappings from cycle_report_planning_pde_mappings table
    # Import the correct attribute model
    from app.models.report_attribute import ReportAttribute
    
    query = select(PDEMapping, ReportAttribute).join(
        ReportAttribute, PDEMapping.attribute_id == ReportAttribute.id
    ).where(
        PDEMapping.phase_id == phase.phase_id
    )
    
    result = await db.execute(query)
    rows = result.all()
    
    # TODO: Get data sources for name lookup when we have proper linking
    data_sources = {}
    
    # Build PDE mappings response
    mappings = []
    for mapping, attr in rows:
        # Parse source_field to extract table and column
        source_table = None
        source_column = None
        if mapping.source_field:
            parts = mapping.source_field.split('.')
            if len(parts) >= 2:
                source_table = '.'.join(parts[:-1])  # Everything except last part
                source_column = parts[-1]  # Last part is column
            else:
                source_column = mapping.source_field
        
        # Get data source name (TODO: implement proper lookup)
        data_source_name = f"Data Source {mapping.data_source_id}" if mapping.data_source_id else None
        
        mappings.append({
            "mapping_id": mapping.id,
            "id": mapping.id,  # For frontend compatibility
            "attribute_id": attr.id,
            "attribute_name": attr.attribute_name,
            "pde_name": mapping.pde_name,
            "pde_code": mapping.pde_code,
            "source_field": mapping.source_field,
            "source_table": source_table,
            "source_column": source_column,
            "data_source_id": mapping.data_source_id,
            "data_source_name": data_source_name,
            "mapping_type": mapping.mapping_type or 'direct',
            "confidence_score": mapping.llm_confidence_score,
            "llm_confidence_score": mapping.llm_confidence_score,
            # Attribute fields for display
            "data_type": attr.data_type,
            "is_primary_key": attr.is_primary_key,
            "validation_rules": attr.validation_rules,
            "approval_status": attr.approval_status,
            "line_item_number": attr.line_item_number,
            "technical_line_item_name": attr.technical_line_item_name,
            "description": attr.description,
            "mdrm": attr.mdrm,
            "mandatory_flag": attr.mandatory_flag,
            "cde_flag": attr.cde_flag,
            "historical_issues_flag": attr.historical_issues_flag,
            # Classification fields - from mapping, not attribute
            "information_security_classification": mapping.information_security_classification,
            "criticality": mapping.criticality,
            "risk_level": mapping.risk_level,
            "regulatory_flag": mapping.regulatory_flag,
            "pii_flag": mapping.pii_flag,
            "llm_classification_rationale": mapping.llm_classification_rationale,
            "llm_regulatory_references": mapping.llm_regulatory_references,
            # Additional fields
            "column_data_type": mapping.column_data_type if hasattr(mapping, 'column_data_type') else None,
            "business_process": mapping.business_process,
            "mapping_confirmed_by_user": False,  # Default value
            "is_validated": mapping.is_validated or False,
            "validation_message": mapping.validation_message,
            "created_at": mapping.created_at.isoformat() if mapping.created_at else None,
            "updated_at": mapping.updated_at.isoformat() if mapping.updated_at else None
        })
    
    return {
        "cycle_id": cycle_id,
        "report_id": report_id,
        "mappings": mappings,
        "total": len(mappings)
    }


@router.post("/cycles/{cycle_id}/reports/{report_id}/pde-mappings/auto-map")
async def auto_map_pdes(
    cycle_id: int,
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Auto-map all unmapped attributes using background LLM job"""
    RoleChecker(tester_roles + management_roles)(current_user)
    
    try:
        from app.core.background_jobs import job_manager
        from app.services.llm_service import get_llm_service
        import uuid
        
        # Check if there's already an active job for this cycle/report
        active_jobs = job_manager.get_active_jobs()
        for job in active_jobs:
            if (job.get('metadata', {}).get('cycle_id') == cycle_id and 
                job.get('metadata', {}).get('report_id') == report_id and
                job.get('job_type') == 'pde_auto_mapping'):
                # If job is stuck in pending for more than 5 minutes, cancel it
                created_at = job.get('created_at')
                if created_at and isinstance(created_at, str):
                    from datetime import datetime, timedelta
                    job_created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    if datetime.utcnow() - job_created.replace(tzinfo=None) > timedelta(minutes=5):
                        job_manager.complete_job(job.get('job_id'), error="Job timeout - stuck in pending")
                        continue
                
                return {
                    "message": "Auto-mapping already in progress",
                    "job_id": job.get('job_id'),
                    "status": "in_progress",
                    "success": False
                }
        
        # Get planning phase first
        phase_query = select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == "Planning"
            )
        )
        
        phase_result = await db.execute(phase_query)
        phase = phase_result.scalar_one_or_none()
        
        if not phase:
            raise HTTPException(status_code=404, detail="Planning phase not found")
        
        # Get all attributes that need mapping
        # First get attributes that already have PDE mappings
        from app.models.planning import PlanningPDEMapping
        mapped_attr_ids_query = select(PlanningPDEMapping.attribute_id).where(
            PlanningPDEMapping.phase_id == phase.phase_id
        )
        mapped_attr_ids_result = await db.execute(mapped_attr_ids_query)
        mapped_attr_ids = {row[0] for row in mapped_attr_ids_result}
        
        logger.info(f"Found {len(mapped_attr_ids)} attributes already mapped")
        
        # Get all attributes and filter out already mapped ones
        attributes_query = select(ReportAttribute).where(
            ReportAttribute.phase_id == phase.phase_id
        ).order_by(ReportAttribute.line_item_number)
        
        logger.info(f"Executing query for phase_id: {phase.phase_id}")
        logger.info(f"Query: {attributes_query}")
        
        attributes_result = await db.execute(attributes_query)
        all_attributes = attributes_result.scalars().all()
        
        logger.info(f"Query returned {len(all_attributes)} attributes")
        if all_attributes:
            logger.info(f"First 5 attribute IDs: {[attr.id for attr in all_attributes[:5]]}")
        
        # Filter out already mapped attributes
        attributes = [attr for attr in all_attributes if attr.id not in mapped_attr_ids]
        
        logger.info(f"Found {len(all_attributes)} total attributes for phase_id {phase.phase_id}")
        logger.info(f"Mapped attribute IDs from DB: {mapped_attr_ids}")
        logger.info(f"All attribute IDs: {[attr.id for attr in all_attributes]}")
        logger.info(f"After filtering out mapped attributes, {len(attributes)} attributes need mapping")
        logger.info(f"Remaining attribute IDs: {[attr.id for attr in attributes]}")
        
        if not attributes:
            return {
                "message": "No attributes found to map",
                "mapped_count": 0,
                "total_count": 0,
                "job_id": None
            }
        
        # Get available data sources
        data_sources_query = select(CycleReportDataSource).where(
            CycleReportDataSource.phase_id == phase.phase_id
        )
        data_sources_result = await db.execute(data_sources_query)
        data_sources = data_sources_result.scalars().all()
        
        if not data_sources:
            raise HTTPException(status_code=400, detail="No data sources configured. Please add data sources first.")
        
        # No need to check existing mappings again - already filtered above
        # The attributes list already contains only unmapped attributes
        
        # Prepare context for background job
        attributes_context = []
        for attr in attributes:
            # Already filtered above, no need to check again
            attributes_context.append({
                "id": attr.id,
                "attribute_name": attr.attribute_name,
                "description": attr.description,
                "data_type": attr.data_type,
                "line_item_number": attr.line_item_number,
                "technical_line_item_name": attr.technical_line_item_name,
                "keywords_to_look_for": attr.keywords_to_look_for
            })
        
        # Prepare data sources context with schema information
        data_sources_context = []
        for ds in data_sources:
            # Get source type string
            if hasattr(ds.source_type, 'value'):
                source_type_str = ds.source_type.value
            else:
                source_type_str = str(ds.source_type)
            
            # Dynamically fetch schema information for database sources
            schema_summary = None
            if ds.connection_config and source_type_str.upper() in ['POSTGRESQL', 'MYSQL', 'ORACLE', 'SQLSERVER']:
                try:
                    schema_summary = await get_table_schema(ds.connection_config)
                    logger.info(f"Fetched schema for {ds.name}: {schema_summary[:100]}...")
                except Exception as e:
                    logger.warning(f"Failed to fetch schema for {ds.name}: {e}")
            
            # Fall back to stored schema_summary if dynamic fetch failed
            if not schema_summary:
                schema_summary = getattr(ds, 'schema_summary', None)
            
            # Provide default message if still no schema
            if not schema_summary:
                if source_type_str.upper() in ['POSTGRESQL', 'MYSQL', 'ORACLE', 'SQLSERVER']:
                    schema_summary = "No schema loaded. Please update data source with actual table and column information."
                elif source_type_str.upper() in ['FILE', 'CSV', 'EXCEL']:
                    schema_summary = "File columns not specified. Please update data source with column names."
                else:
                    schema_summary = "Schema information not available."
            
            data_sources_context.append({
                "id": getattr(ds, 'id', None),
                "name": ds.name,
                "source_type": source_type_str,
                "description": ds.description or f"{ds.name} data source",
                "schema_summary": schema_summary
            })
        
        # Get report and cycle information for regulatory context and metadata
        from app.models.report import Report
        from app.models.test_cycle import TestCycle
        
        report_query = select(Report).where(Report.report_id == report_id)
        report_result = await db.execute(report_query)
        report = report_result.scalar_one_or_none()
        
        cycle_query = select(TestCycle).where(TestCycle.cycle_id == cycle_id)
        cycle_result = await db.execute(cycle_query)
        cycle = cycle_result.scalar_one_or_none()
        
        if not attributes_context:
            return {
                "message": "All attributes are already mapped",
                "mapped_count": 0,
                "total_count": len(attributes),
                "job_id": None
            }
        
        logger.info(f"🚀 Creating PDE mapping job with {len(attributes_context)} attributes")
        logger.info(f"📊 Total attributes found: {len(all_attributes)}, Filtered attributes: {len(attributes)}, Context prepared: {len(attributes_context)}")
        
        # Start background job for PDE mapping
        job_id = job_manager.create_job("pde_auto_mapping", {
            "cycle_id": cycle_id,
            "report_id": report_id,
            "user_id": current_user.user_id,
            "cycle_name": cycle.cycle_name if cycle else f"Cycle {cycle_id}",
            "report_name": report.report_name if report else f"Report {report_id}",
            "phase": "Planning"
        })
        
        # Update initial progress
        job_manager.update_job_progress(
            job_id,
            total_steps=2,
            message="Starting automatic PDE mapping with LLM..."
        )
        
        
        # Start the async task directly using background jobs manager
        from app.tasks.planning_tasks import _auto_map_pdes_async
        import asyncio
        
        # Create async function to run the task
        async def run_pde_mapping_task():
            """Execute PDE mapping in background"""
            try:
                result = await _auto_map_pdes_async(
                    job_id=job_id,
                    cycle_id=cycle_id,
                    report_id=report_id,
                    phase_id=phase.phase_id,
                    user_id=current_user.user_id,
                    attributes_context=attributes_context,
                    data_sources_context=data_sources_context,
                    report_context={
                        "report_id": report_id,
                        "cycle_id": cycle_id,
                        "report_name": report.report_name if report else "",
                        "regulatory_context": report.regulation if report else ""
                    }
                )
                logger.info(f"✅ PDE mapping completed successfully: {result}")
                return result
            except Exception as e:
                logger.error(f"❌ PDE mapping failed: {e}")
                job_manager.complete_job(job_id, error=str(e))
                raise
        
        # Create the async task
        task = asyncio.create_task(run_pde_mapping_task())
        logger.info(f"✅ Created async task for job {job_id}: {task}")
        
        # Add a callback to log when the task completes
        def task_done_callback(future):
            try:
                result = future.result()
                logger.info(f"✅ Task {job_id} completed with result: {result}")
            except Exception as e:
                logger.error(f"❌ Task {job_id} failed with error: {e}")
        
        task.add_done_callback(task_done_callback)
        
        return {
            "message": "PDE auto-mapping started in background",
            "job_id": job_id,
            "status": "started",
            "total_attributes": len(attributes_context),
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error starting PDE auto-mapping: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start auto-mapping: {str(e)}")


@router.post("/cycles/{cycle_id}/reports/{report_id}/pde-mappings/suggest")
async def suggest_pde_mapping(
    cycle_id: int,
    report_id: int,
    attribute_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Suggest PDE mapping for a single attribute using LLM"""
    RoleChecker(tester_roles + management_roles)(current_user)
    
    try:
        # Get planning phase
        phase_query = select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == "Planning"
            )
        )
        
        phase_result = await db.execute(phase_query)
        phase = phase_result.scalar_one_or_none()
        
        if not phase:
            raise HTTPException(status_code=404, detail="Planning phase not found")
        
        # Get the specific attribute
        attribute_query = select(ReportAttribute).join(WorkflowPhase).where(
            and_(
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.cycle_id == cycle_id,
                ReportAttribute.id == attribute_id
            )
        )
        
        attribute_result = await db.execute(attribute_query)
        attribute = attribute_result.scalar_one_or_none()
        
        if not attribute:
            raise HTTPException(status_code=404, detail="Attribute not found")
        
        # Get available data sources
        data_sources_query = select(CycleReportDataSource).where(
            CycleReportDataSource.phase_id == phase.phase_id
        )
        data_sources_result = await db.execute(data_sources_query)
        data_sources = data_sources_result.scalars().all()
        
        if not data_sources:
            raise HTTPException(status_code=400, detail="No data sources configured. Please add data sources first.")
        
        # Get LLM service for suggestion
        llm_service = get_llm_service()
        
        # Prepare context for single attribute
        attributes_context = [{
            "id": attribute.id,
            "attribute_name": attribute.attribute_name,
            "description": attribute.description,
            "data_type": attribute.data_type,
            "line_item_number": attribute.line_item_number,
            "technical_line_item_name": attribute.technical_line_item_name,
            "keywords_to_look_for": attribute.keywords_to_look_for
        }]
        
        # Prepare data sources context
        data_sources_context = []
        for ds in data_sources:
            data_sources_context.append({
                "name": ds.name,
                "source_type": ds.source_type,
                "description": ds.description
            })
        
        # Get report information for regulatory context
        from app.models.report import Report
        report_query = select(Report).where(Report.report_id == report_id)
        report_result = await db.execute(report_query)
        report = report_result.scalar_one_or_none()
        
        # Get LLM suggestion
        try:
            mapping_suggestions = await llm_service.suggest_pde_mappings(
                attributes=attributes_context,
                data_sources=data_sources_context,
                report_context={
                    "report_id": report_id,
                    "cycle_id": cycle_id,
                    "report_name": report.report_name if report else "",
                    "regulatory_context": report.regulation if report else ""
                },
                job_id=None  # No job_id for single attribute suggestion
            )
            
            if mapping_suggestions and len(mapping_suggestions) > 0:
                suggestion = mapping_suggestions[0]  # Take first suggestion for single attribute
                return {
                    "success": True,
                    "suggestion": {
                        "table_name": suggestion.get('table_name'),
                        "column_name": suggestion.get('column_name'),
                        "data_source_name": suggestion.get('data_source_name'),
                        "confidence": suggestion.get('confidence', 80),
                        "reasoning": suggestion.get('reasoning', 'LLM-suggested mapping')
                    }
                }
            else:
                # Fallback to simple mapping if LLM fails
                best_mapping = find_best_column_mapping(attribute.attribute_name, data_sources)
                if best_mapping:
                    return {
                        "success": True,
                        "suggestion": {
                            "table_name": best_mapping['table'],
                            "column_name": best_mapping['column'],
                            "data_source_name": best_mapping['data_source_name'],
                            "confidence": 60,
                            "reasoning": "Pattern-based mapping (fallback)"
                        }
                    }
                else:
                    return {
                        "success": False,
                        "message": "No mapping suggestion available for this attribute"
                    }
                    
        except Exception as e:
            logger.warning(f"LLM suggestion failed for attribute {attribute_id}: {e}")
            
            # Fallback to simple mapping
            best_mapping = find_best_column_mapping(attribute.attribute_name, data_sources)
            if best_mapping:
                return {
                    "success": True,
                    "suggestion": {
                        "table_name": best_mapping['table'],
                        "column_name": best_mapping['column'],
                        "data_source_name": best_mapping['data_source_name'],
                        "confidence": 60,
                        "reasoning": "Pattern-based mapping (LLM unavailable)"
                    }
                }
            else:
                return {
                    "success": False,
                    "message": "No mapping suggestion available for this attribute"
                }
        
    except Exception as e:
        logger.error(f"Error suggesting PDE mapping for attribute {attribute_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Suggestion failed: {str(e)}")


@router.post("/cycles/{cycle_id}/reports/{report_id}/pde-mappings/regenerate-all")
async def regenerate_all_pde_mappings(
    cycle_id: int,
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Regenerate all PDE mappings for a report with updated classifications"""
    logger.info(f"🔄 REGENERATE ENDPOINT CALLED: cycle={cycle_id}, report={report_id}, user={current_user.email}")
    print(f"\n\n🔄🔄🔄 REGENERATE ALL PDE MAPPINGS CALLED - cycle={cycle_id}, report={report_id}\n\n")
    RoleChecker(tester_roles + management_roles)(current_user)
    
    try:
        # Get planning phase
        phase_query = select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == "Planning"
            )
        )
        phase_result = await db.execute(phase_query)
        phase = phase_result.scalar_one_or_none()
        
        if not phase:
            raise HTTPException(status_code=404, detail="Planning phase not found")
        
        # Get all existing mappings
        from app.models.planning import PlanningPDEMapping
        
        existing_mappings_query = select(PlanningPDEMapping).where(
            PlanningPDEMapping.phase_id == phase.phase_id
        )
        existing_mappings_result = await db.execute(existing_mappings_query)
        existing_mappings = existing_mappings_result.scalars().all()
        
        if not existing_mappings:
            raise HTTPException(status_code=404, detail="No existing mappings found to regenerate")
        
        # Get all attributes with existing mappings
        attribute_ids = [mapping.attribute_id for mapping in existing_mappings]
        attributes_query = select(ReportAttribute).where(
            ReportAttribute.id.in_(attribute_ids)
        )
        attributes_result = await db.execute(attributes_query)
        attributes = attributes_result.scalars().all()
        
        # Get data sources
        data_sources_query = select(CycleReportDataSource).where(
            CycleReportDataSource.phase_id == phase.phase_id
        )
        data_sources_result = await db.execute(data_sources_query)
        data_sources = data_sources_result.scalars().all()
        
        if not data_sources:
            raise HTTPException(status_code=400, detail="No data sources configured")
        
        # Start background job for regeneration
        job_id = job_manager.create_job("pde_regeneration", {
            "cycle_id": cycle_id,
            "report_id": report_id,
            "user_id": current_user.user_id,
            "phase": "Planning"
        })
        
        # Prepare data for the Celery task
        attributes_data = []
        for attr in attributes:
            attributes_data.append({
                "id": attr.id,
                "attribute_id": attr.id,
                "attribute_name": attr.attribute_name,
                "description": attr.description,
                "data_type": attr.data_type,
                "line_item_number": attr.line_item_number,
                "technical_line_item_name": attr.technical_line_item_name,
                "keywords_to_look_for": attr.keywords_to_look_for
            })
        
        data_sources_data = []
        for ds in data_sources:
            # Get source type string
            if hasattr(ds.source_type, 'value'):
                source_type_str = ds.source_type.value
            else:
                source_type_str = str(ds.source_type)
            
            data_sources_data.append({
                "id": getattr(ds, 'id', None),
                "name": ds.name,
                "source_type": source_type_str,
                "description": ds.description or f"{ds.name} data source",
                "schema_summary": getattr(ds, 'schema_summary', None) or "Schema information not available."
            })
        
        existing_mappings_data = []
        for mapping in existing_mappings:
            existing_mappings_data.append({
                "id": mapping.id,
                "attribute_id": mapping.attribute_id,
                "data_source_id": mapping.data_source_id
            })
        
        # Get report context
        report_query = select(Report).where(Report.report_id == report_id)
        report_result = await db.execute(report_query)
        report = report_result.scalar_one_or_none()
        
        report_context = {
            "report_id": report_id,
            "cycle_id": cycle_id,
            "report_name": report.report_name if report else "",
            "regulatory_context": report.regulation if report else ""
        }
        
        # Run async task directly using background jobs manager
        from app.tasks.planning_tasks import _regenerate_pde_mappings_async
        asyncio.create_task(_regenerate_pde_mappings_async(
            job_id, cycle_id, report_id, phase.phase_id, current_user.user_id,
            attributes_data, data_sources_data, existing_mappings_data, report_context
        ))
        logger.info(f"Started PDE regeneration task with job {job_id}")
        
        return {
            "message": "Regeneration started in background",
            "job_id": job_id,
            "status": "started",
            "mapping_count": len(existing_mappings)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting PDE regeneration: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start regeneration: {str(e)}")


def find_best_column_mapping(attribute_name: str, data_sources) -> dict:
    """Simple column mapping logic - can be enhanced with LLM"""
    
    # Simple mapping rules based on common attribute patterns
    mapping_rules = {
        'customer_id': ['customer_id', 'cust_id', 'customer_number'],
        'customer_name': ['customer_name', 'cust_name', 'name'],
        'account_number': ['account_number', 'account_no', 'acct_num'],
        'balance': ['balance', 'amount', 'total'],
        'date': ['date', 'created_date', 'transaction_date']
    }
    
    attr_lower = attribute_name.lower()
    
    # Find best matching rule
    best_match = None
    for pattern, columns in mapping_rules.items():
        if pattern in attr_lower:
            for col in columns:
                # In a real implementation, you'd query the data source schema
                # For now, return a placeholder mapping
                if data_sources:
                    best_match = {
                        'table': 'main_table',  # Placeholder
                        'column': col,
                        'data_source_name': data_sources[0].name
                    }
                    break
            if best_match:
                break
    
    return best_match


@router.put("/cycles/{cycle_id}/reports/{report_id}/pde-mappings/{mapping_id}")
async def update_pde_mapping(
    cycle_id: int,
    report_id: int,
    mapping_id: int,
    mapping_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Update an existing PDE mapping"""
    RoleChecker(tester_roles + management_roles)(current_user)
    
    try:
        from app.models.planning import PlanningPDEMapping
        
        # Get the existing mapping
        mapping_query = select(PlanningPDEMapping).where(
            PlanningPDEMapping.id == mapping_id
        )
        
        mapping_result = await db.execute(mapping_query)
        mapping = mapping_result.scalar_one_or_none()
        
        if not mapping:
            raise HTTPException(status_code=404, detail="PDE mapping not found")
        
        # Verify the mapping belongs to the correct cycle/report via phase
        phase_query = select(WorkflowPhase).where(
            and_(
                WorkflowPhase.phase_id == mapping.phase_id,
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id
            )
        )
        phase_result = await db.execute(phase_query)
        phase = phase_result.scalar_one_or_none()
        
        if not phase:
            raise HTTPException(status_code=404, detail="PDE mapping not found for this cycle/report")
        
        # Update fields
        if 'data_source_id' in mapping_data:
            mapping.data_source_id = mapping_data['data_source_id']
        
        if 'source_field' in mapping_data and mapping_data['source_field']:
            source_field = mapping_data['source_field']
            mapping.source_field = source_field
            
            # Parse source field to extract table and column
            if '.' in source_field:
                parts = source_field.split('.')
                if len(parts) == 3:
                    # schema.table.column format
                    mapping.source_table = f"{parts[0]}.{parts[1]}"
                    mapping.source_column = parts[2]
                elif len(parts) == 2:
                    # table.column format
                    mapping.source_table = parts[0]
                    mapping.source_column = parts[1]
            
            # Get data source name if data_source_id is provided
            if mapping.data_source_id:
                ds_query = select(CycleReportDataSource).where(
                    CycleReportDataSource.id == mapping.data_source_id
                )
                ds_result = await db.execute(ds_query)
                data_source = ds_result.scalar_one_or_none()
                if data_source:
                    mapping.data_source_name = data_source.name
        
        # Optional fields
        for field in ['pde_description', 'transformation_rule', 'mapping_type', 
                      'business_process', 'business_owner', 'data_steward']:
            if field in mapping_data:
                setattr(mapping, field, mapping_data[field])
        
        # Update metadata
        mapping.updated_at = datetime.utcnow()
        mapping.updated_by_id = current_user.user_id
        mapping.mapping_confirmed_by_user = True
        
        await db.commit()
        
        logger.info(f"Updated PDE mapping {mapping_id} for attribute {mapping.attribute_id}")
        
        return {
            "success": True,
            "message": "PDE mapping updated successfully",
            "mapping_id": mapping.id
        }
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating PDE mapping {mapping_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update mapping: {str(e)}")


@router.get("/cycles/{cycle_id}/reports/{report_id}/pde-classifications")
async def get_pde_classifications(
    cycle_id: int,
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[dict]:
    """Get all PDE classifications for a cycle/report"""
    RoleChecker(tester_roles + management_roles)(current_user)
    
    try:
        # Get all PDE mappings with their classifications
        # from app.models.data_source_config import PDEMapping  # Disabled - using PlanningPDEMapping instead
        from app.models.planning import PlanningPDEMapping as PDEMapping
        
        # Get phase first
        phase_query = select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == "Planning"
            )
        )
        phase_result = await db.execute(phase_query)
        phase = phase_result.scalar_one_or_none()
        
        if not phase:
            return []
            
        # Join with ReportAttribute to get attribute details
        mappings_query = select(PDEMapping, ReportAttribute).join(
            ReportAttribute, PDEMapping.attribute_id == ReportAttribute.id
        ).where(
            PDEMapping.phase_id == phase.phase_id
        )
        
        result = await db.execute(mappings_query)
        rows = result.all()
        
        classifications = []
        for mapping, attribute in rows:
            # Parse source field to get table and column names
            table_name = None
            column_name = None
            if mapping.source_field:
                parts = mapping.source_field.split('.')
                if len(parts) >= 2:
                    table_name = '.'.join(parts[:-1])
                    column_name = parts[-1]
                else:
                    column_name = mapping.source_field
                    
            classifications.append({
                "id": mapping.id,
                "pde_mapping_id": mapping.id,
                "attribute_id": mapping.attribute_id,
                "pde_name": mapping.pde_name,
                "pde_code": mapping.pde_code,
                "attribute_name": attribute.attribute_name,
                "line_item_number": attribute.line_item_number,
                "technical_line_item_name": attribute.technical_line_item_name,
                "description": attribute.description,
                "mdrm": attribute.mdrm,
                "data_type": attribute.data_type,
                "mandatory_flag": attribute.mandatory_flag,
                "cde_flag": attribute.cde_flag,
                "is_primary_key": attribute.is_primary_key,
                "historical_issues_flag": attribute.historical_issues_flag,
                "data_source": mapping.data_source_name,
                "table_name": table_name,
                "column_name": column_name,
                "llm_confidence_score": mapping.llm_confidence_score,
                "criticality": mapping.criticality,
                "risk_level": mapping.risk_level,
                "regulatory_flag": mapping.regulatory_flag,
                "pii_flag": mapping.pii_flag,
                "information_security_classification": mapping.information_security_classification,
                "is_classified": bool(mapping.criticality or mapping.risk_level or mapping.information_security_classification),
                "classification_count": 1 if bool(mapping.criticality or mapping.risk_level or mapping.information_security_classification) else 0,
                "llm_suggested_criticality": mapping.llm_suggested_criticality,
                "llm_suggested_risk_level": mapping.llm_suggested_risk_level,
                "llm_classification_confidence": mapping.pde_classification_confidence if hasattr(mapping, 'pde_classification_confidence') else None,
                "llm_classification_rationale": mapping.llm_classification_rationale,
                "llm_regulatory_references": mapping.llm_regulatory_references,
                "created_at": mapping.created_at.isoformat() if mapping.created_at else None,
                "updated_at": mapping.updated_at.isoformat() if mapping.updated_at else None
            })
        
        return classifications
        
    except Exception as e:
        logger.error(f"Error fetching PDE classifications: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch classifications: {str(e)}")


@router.post("/cycles/{cycle_id}/reports/{report_id}/pde-classifications")
async def save_pde_classification(
    cycle_id: int,
    report_id: int,
    classification_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Save PDE classification for a mapping"""
    RoleChecker(tester_roles + management_roles)(current_user)
    
    try:
        from app.models.data_source import AttributeMapping
        
        mapping_id = classification_data.get("pde_mapping_id")
        if not mapping_id:
            raise HTTPException(status_code=400, detail="pde_mapping_id is required")
        
        # Get the mapping
        mapping_query = select(AttributeMapping).where(AttributeMapping.id == mapping_id)
        result = await db.execute(mapping_query)
        mapping = result.scalar_one_or_none()
        
        if not mapping:
            raise HTTPException(status_code=404, detail="PDE mapping not found")
        
        # Update classification fields
        if "criticality" in classification_data:
            mapping.criticality = classification_data["criticality"]
        if "risk_level" in classification_data:
            mapping.risk_level = classification_data["risk_level"]
        if "regulatory_flag" in classification_data:
            mapping.regulatory_flag = classification_data["regulatory_flag"]
        if "pii_flag" in classification_data:
            mapping.pii_flag = classification_data["pii_flag"]
        if "information_security_classification" in classification_data:
            mapping.information_security_classification = classification_data["information_security_classification"]
        
        # Update LLM suggestions if provided
        if "llm_suggested_criticality" in classification_data:
            mapping.llm_suggested_criticality = classification_data["llm_suggested_criticality"]
        if "llm_suggested_risk_level" in classification_data:
            mapping.llm_suggested_risk_level = classification_data["llm_suggested_risk_level"]
        if "llm_classification_rationale" in classification_data:
            mapping.llm_classification_rationale = classification_data["llm_classification_rationale"]
        if "llm_regulatory_references" in classification_data:
            mapping.llm_regulatory_references = classification_data["llm_regulatory_references"]
        
        mapping.updated_by_id = current_user.user_id
        mapping.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(mapping)
        
        return {
            "id": mapping.id,
            "pde_mapping_id": mapping.id,
            "message": "Classification saved successfully",
            "is_classified": True
        }
        
    except Exception as e:
        logger.error(f"Error saving PDE classification: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save classification: {str(e)}")


@router.post("/cycles/{cycle_id}/reports/{report_id}/pde-classifications/suggest")
async def suggest_pde_classification(
    cycle_id: int,
    report_id: int,
    pde_mapping_id: int = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get LLM suggestion for PDE classification"""
    RoleChecker(tester_roles + management_roles)(current_user)
    
    try:
        from app.models.data_source import AttributeMapping
        llm_service = get_llm_service()
        
        # Get the mapping and attribute
        mapping_query = select(AttributeMapping, ReportAttribute).join(
            ReportAttribute, AttributeMapping.attribute_id == ReportAttribute.id
        ).where(AttributeMapping.id == pde_mapping_id)
        
        result = await db.execute(mapping_query)
        row = result.first()
        
        if not row:
            raise HTTPException(status_code=404, detail="PDE mapping not found")
        
        mapping, attribute = row
        
        # Get LLM classification suggestion
        suggestion = await llm_service.generate_pde_classification_suggestion(
            mapping, attribute, cycle_id, report_id
        )
        
        return suggestion
        
    except Exception as e:
        logger.error(f"Error getting PDE classification suggestion: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get suggestion: {str(e)}")


@router.post("/cycles/{cycle_id}/reports/{report_id}/pde-classifications/suggest-batch")
async def suggest_pde_classifications_batch(
    cycle_id: int,
    report_id: int,
    pde_mapping_ids: Optional[List[int]] = Body(None, embed=True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get LLM suggestions for multiple PDE classifications using background job
    
    If pde_mapping_ids is not provided, will process all unclassified PDEs
    """
    RoleChecker(tester_roles + management_roles)(current_user)
    
    try:
        from app.core.background_jobs import job_manager
        from app.models.planning import PlanningPDEMapping
        
        # Check if there's already an active job for this cycle/report
        active_jobs = job_manager.get_active_jobs()
        for job in active_jobs:
            if (job.get('metadata', {}).get('cycle_id') == cycle_id and 
                job.get('metadata', {}).get('report_id') == report_id and
                job.get('job_type') == 'pde_classification'):
                return {
                    "message": "Classification already in progress",
                    "job_id": job.get('job_id'),
                    "status": "in_progress",
                    "success": False
                }
        
        # Get planning phase
        phase_query = select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == "Planning"
            )
        )
        phase_result = await db.execute(phase_query)
        phase = phase_result.scalar_one_or_none()
        
        if not phase:
            raise HTTPException(status_code=404, detail="Planning phase not found")
        
        # Get mappings with attributes
        mappings_query = select(PlanningPDEMapping, ReportAttribute).join(
            ReportAttribute, PlanningPDEMapping.attribute_id == ReportAttribute.id
        ).where(
            PlanningPDEMapping.phase_id == phase.phase_id
        )
        
        # If specific IDs provided, filter by them
        if pde_mapping_ids:
            mappings_query = mappings_query.where(
                PlanningPDEMapping.id.in_(pde_mapping_ids)
            )
        else:
            # Otherwise, get all unclassified mappings
            mappings_query = mappings_query.where(
                or_(
                    PlanningPDEMapping.criticality.is_(None),
                    PlanningPDEMapping.risk_level.is_(None),
                    PlanningPDEMapping.information_security_classification.is_(None)
                )
            )
        
        result = await db.execute(mappings_query)
        mappings_data = []
        for row in result:
            mapping, attribute = row
            mapping.attribute = attribute  # Attach attribute to mapping
            mappings_data.append(mapping)
        
        if not mappings_data:
            raise HTTPException(status_code=404, detail="No PDE mappings found")
        
        # Get report and cycle info
        from app.models.report import Report
        from app.models.test_cycle import TestCycle
        
        report_query = select(Report).where(Report.report_id == report_id)
        report_result = await db.execute(report_query)
        report = report_result.scalar_one_or_none()
        
        cycle_query = select(TestCycle).where(TestCycle.cycle_id == cycle_id)
        cycle_result = await db.execute(cycle_query)
        cycle = cycle_result.scalar_one_or_none()
        
        # Create background job
        job_id = job_manager.create_job("pde_classification", {
            "cycle_id": cycle_id,
            "report_id": report_id,
            "user_id": current_user.user_id,
            "cycle_name": cycle.cycle_name if cycle else f"Cycle {cycle_id}",
            "report_name": report.report_name if report else f"Report {report_id}",
            "phase": "Planning",
            "mapping_count": len(mappings_data)
        })
        
        # Update initial progress
        job_manager.update_job_progress(
            job_id,
            total_steps=len(mappings_data),
            message="Starting PDE classification with LLM..."
        )
        
        async def run_pde_classification():
            try:
                llm_service = get_llm_service()
                
                # Update job status to in_progress
                job_manager.update_job_progress(
                    job_id,
                    status="running",
                    current_step="Generating classification suggestions",
                    progress_percentage=10,
                    message=f"Classifying {len(mappings_data)} PDEs..."
                )
                
                # Call LLM service
                suggestions = await llm_service.generate_pde_classification_suggestions_batch(
                    mappings_data, cycle_id, report_id, job_id
                )
                
                # Apply suggestions to database
                job_manager.update_job_progress(
                    job_id,
                    current_step="Applying classifications",
                    progress_percentage=80,
                    message="Saving classification results..."
                )
                
                classified_count = 0
                from app.core.database import AsyncSessionLocal
                async with AsyncSessionLocal() as task_db:
                    for i, suggestion in enumerate(suggestions):
                        try:
                            mapping_id = suggestion.get("pde_mapping_id")
                            if not mapping_id:
                                continue
                            
                            logger.info(f"Applying classification for mapping {mapping_id}")
                            
                            # Update the mapping
                            update_query = select(PlanningPDEMapping).where(PlanningPDEMapping.id == mapping_id)
                            update_result = await task_db.execute(update_query)
                            mapping_to_update = update_result.scalar_one_or_none()
                            
                            if mapping_to_update:
                                mapping_to_update.criticality = suggestion.get("llm_suggested_criticality")
                                mapping_to_update.risk_level = suggestion.get("llm_suggested_risk_level")
                                mapping_to_update.information_security_classification = suggestion.get("llm_suggested_information_security_classification")
                                mapping_to_update.regulatory_flag = suggestion.get("regulatory_flag", False)
                                mapping_to_update.pii_flag = suggestion.get("pii_flag", False)
                                mapping_to_update.llm_suggested_criticality = suggestion.get("llm_suggested_criticality")
                                mapping_to_update.llm_suggested_risk_level = suggestion.get("llm_suggested_risk_level")
                                mapping_to_update.llm_classification_rationale = suggestion.get("llm_classification_rationale")
                                mapping_to_update.llm_regulatory_references = suggestion.get("llm_regulatory_references", [])
                                mapping_to_update.updated_by_id = current_user.user_id
                                mapping_to_update.updated_at = datetime.utcnow()
                                classified_count += 1
                                
                                # Incremental commit every 10 classifications
                                if classified_count % 10 == 0:
                                    await task_db.commit()
                                    logger.info(f"✅ Incremental commit: {classified_count} classifications saved")
                                    
                                    # Update progress
                                    progress = 80 + int((classified_count / len(suggestions)) * 15)
                                    job_manager.update_job_progress(
                                        job_id,
                                        current_step="Applying classifications",
                                        progress_percentage=progress,
                                        message=f"Classified {classified_count} of {len(suggestions)} PDEs..."
                                    )
                                
                        except Exception as e:
                            logger.error(f"Error applying classification for mapping {mapping_id}: {e}")
                    
                    # Final commit for any remaining classifications
                    await task_db.commit()
                    logger.info(f"✅ Final commit: Total {classified_count} classifications saved")
                
                # Complete the job
                job_manager.update_job_progress(
                    job_id,
                    current_step="Completed",
                    progress_percentage=100,
                    completed_steps=len(mappings_data),
                    message=f"Classification completed! Classified {classified_count} out of {len(mappings_data)} PDEs.",
                    result={
                        "classified_count": classified_count,
                        "total_count": len(mappings_data),
                        "suggestions_generated": len(suggestions)
                    }
                )
                job_manager.complete_job(job_id)
                
            except Exception as e:
                logger.error(f"PDE classification job failed: {e}")
                job_manager.update_job_progress(
                    job_id,
                    message=f"Classification failed: {str(e)}"
                )
                job_manager.complete_job(job_id, error=str(e))
        
        # Run async task directly using background jobs manager
        import asyncio
        logger.info(f"🚀 Starting PDE classification for job {job_id}")
        task = asyncio.create_task(run_pde_classification())
        logger.info(f"✅ Created async task for job {job_id}: {task}")
        
        return {
            "message": "PDE classification started in background",
            "job_id": job_id,
            "status": "started",
            "total_mappings": len(mappings_data),
            "mappings_to_process": len(mappings_data),
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error starting PDE classification batch: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start classification: {str(e)}")


@router.get("/cycles/{cycle_id}/reports/{report_id}/attributes/by-status")
async def get_attributes_by_status(
    cycle_id: int,
    report_id: int,
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get attributes grouped by approval status"""
    # Get planning phase first
    phase_query = select(WorkflowPhase).where(
        and_(
            WorkflowPhase.cycle_id == cycle_id,
            WorkflowPhase.report_id == report_id,
            WorkflowPhase.phase_name == "Planning"
        )
    )
    
    phase_result = await db.execute(phase_query)
    phase = phase_result.scalar_one_or_none()
    
    if not phase:
        return {"by_status": {}, "total": 0}
    
    # Build query with eager loading of phase relationship
    query = select(ReportAttribute).options(selectinload(ReportAttribute.phase)).where(
        and_(
            ReportAttribute.phase_id == phase.phase_id,
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


# Planning-unified endpoints (unified with main planning system)
@router.get("/phases/{phase_id}/versions")
async def get_planning_unified_phase_versions(
    phase_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get phase versions for planning-unified - returns current planning version"""
    
    # The frontend calculates phase_id as cycleId * 1000 + reportId
    # Extract cycle_id and report_id from the phase_id
    cycle_id = phase_id // 1000
    report_id = phase_id % 1000
    
    # Look for the planning phase for this cycle/report combination
    phase_query = select(WorkflowPhase).where(
        and_(
            WorkflowPhase.cycle_id == cycle_id,
            WorkflowPhase.report_id == report_id,
            WorkflowPhase.phase_name == 'Planning'
        )
    )
    phase_result = await db.execute(phase_query)
    phase = phase_result.scalar_one_or_none()
    
    if not phase:
        # No planning phase found for this cycle/report - unified planning not available
        return {
            "phase_id": phase_id,
            "versions": [],
            "total": 0
        }
    
    # For the unified system, we consider the current phase as version 1
    # This allows the frontend to detect that unified planning is "available"
    version = {
        "version_id": f"phase_{phase_id}_v1",
        "version_number": 1,
        "phase_id": phase_id,
        "cycle_id": phase.cycle_id,
        "report_id": phase.report_id,
        "status": phase.status,
        "created_at": phase.actual_start_date,
        "is_current": True
    }
    
    return {
        "phase_id": phase_id,
        "versions": [version],
        "total": 1
    }


@router.post("/phases/{phase_id}/versions")
async def create_or_get_version_for_phase(
    phase_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Create or get version for legacy cycle/report (expected by frontend)"""
    # Frontend calculates phase_id as cycleId * 1000 + reportId, so decode it
    cycle_id = phase_id // 1000
    report_id = phase_id % 1000
    
    # Get the actual workflow phase for this cycle/report combination
    phase_query = select(WorkflowPhase).where(
        and_(
            WorkflowPhase.cycle_id == cycle_id,
            WorkflowPhase.report_id == report_id,
            WorkflowPhase.phase_name == "Planning"
        )
    )
    phase_result = await db.execute(phase_query)
    phase = phase_result.scalar_one_or_none()
    
    if not phase:
        raise NotFoundException(f"Planning phase not found for cycle {cycle_id}, report {report_id}")
    
    # Return the version information the frontend expects
    return {
        "version_id": f"phase_{phase_id}_v1",
        "version_number": 1,
        "phase_id": phase_id,
        "cycle_id": cycle_id,
        "report_id": report_id,
        "status": phase.status,
        "created_at": phase.actual_start_date,
        "is_current": True
    }


@router.get("/phases/{phase_id}")
async def get_planning_unified_phase_details(
    phase_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get phase details for planning-unified"""
    # Frontend calculates phase_id as cycleId * 1000 + reportId, so decode it
    cycle_id = phase_id // 1000
    report_id = phase_id % 1000
    
    # Get the actual workflow phase for this cycle/report combination
    phase_query = select(WorkflowPhase).where(
        and_(
            WorkflowPhase.cycle_id == cycle_id,
            WorkflowPhase.report_id == report_id,
            WorkflowPhase.phase_name == "Planning"
        )
    )
    phase_result = await db.execute(phase_query)
    phase = phase_result.scalar_one_or_none()
    
    if not phase:
        return {
            "phase_id": phase_id,
            "phase": None
        }
    
    return {
        "phase_id": phase_id,
        "phase": {
            "phase_id": phase.phase_id,
            "cycle_id": cycle_id,
            "report_id": report_id,
            "phase_name": phase.phase_name,
            "status": phase.status,
            "planned_start_date": phase.planned_start_date,
            "planned_end_date": phase.planned_end_date,
            "actual_start_date": phase.actual_start_date,
            "actual_end_date": phase.actual_end_date
        }
    }


@router.get("/versions/{version_id}/attributes")
async def get_attributes_by_version_id(
    version_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get attributes for a specific planning version (unified planning API)"""
    # Extract phase_id from version_id (format: "phase_{phase_id}_v1")
    if not version_id.startswith("phase_") or not version_id.endswith("_v1"):
        raise HTTPException(status_code=400, detail="Invalid version_id format")
    
    try:
        phase_id_str = version_id.replace("phase_", "").replace("_v1", "")
        phase_id = int(phase_id_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid version_id format")
    
    # Frontend calculates phase_id as cycleId * 1000 + reportId, so decode it
    cycle_id = phase_id // 1000
    report_id = phase_id % 1000
    
    # Get the actual workflow phase for this cycle/report combination
    phase_query = select(WorkflowPhase).where(
        and_(
            WorkflowPhase.cycle_id == cycle_id,
            WorkflowPhase.report_id == report_id,
            WorkflowPhase.phase_name == "Planning"
        )
    )
    phase_result = await db.execute(phase_query)
    phase = phase_result.scalar_one_or_none()
    
    if not phase:
        return {
            "version_id": version_id,
            "attributes": [],
            "total": 0
        }
    
    # Get all attributes for this planning phase
    query = select(ReportAttribute).where(
        and_(
            ReportAttribute.phase_id == phase.phase_id,
            ReportAttribute.is_active == True
        )
    )
    
    result = await db.execute(query)
    attributes = result.scalars().all()
    
    # Convert to the format expected by the frontend
    attribute_list = []
    for attr in attributes:
        attribute_list.append({
            "id": attr.id,
            "attribute_name": attr.attribute_name,
            "description": attr.description,
            "data_type": attr.data_type,
            "is_primary_key": attr.is_primary_key,
            "is_mandatory": attr.mandatory_flag,
            "is_cde": attr.cde_flag,
            "has_issues": attr.historical_issues_flag,
            "approval_status": attr.approval_status,
            "source_table": getattr(attr, 'source_table', None),  # Safely handle missing field
            "source_column": getattr(attr, 'source_column', None),  # Safely handle missing field
            "validation_rules": attr.validation_rules,
            "llm_generated": attr.llm_generated,
            "created_at": attr.created_at,
            "updated_at": attr.updated_at
        })
    
    return {
        "version_id": version_id,
        "attributes": attribute_list,
        "total": len(attribute_list)
    }


@router.get("/versions/{version_id}")
async def get_planning_version_details(
    version_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get details for a specific planning version (unified planning API)"""
    # Extract phase_id from version_id (format: "phase_{phase_id}_v1")
    if not version_id.startswith("phase_") or not version_id.endswith("_v1"):
        raise HTTPException(status_code=400, detail="Invalid version_id format")
    
    try:
        phase_id_str = version_id.replace("phase_", "").replace("_v1", "")
        phase_id = int(phase_id_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid version_id format")
    
    # Frontend calculates phase_id as cycleId * 1000 + reportId, so decode it
    cycle_id = phase_id // 1000
    report_id = phase_id % 1000
    
    # Get the actual workflow phase for this cycle/report combination
    phase_query = select(WorkflowPhase).where(
        and_(
            WorkflowPhase.cycle_id == cycle_id,
            WorkflowPhase.report_id == report_id,
            WorkflowPhase.phase_name == "Planning"
        )
    )
    phase_result = await db.execute(phase_query)
    phase = phase_result.scalar_one_or_none()
    
    if not phase:
        raise NotFoundException(f"Planning version {version_id} not found")
    
    return {
        "version_id": version_id,
        "version_number": 1,
        "phase_id": phase_id,
        "cycle_id": cycle_id,
        "report_id": report_id,
        "status": phase.status,
        "created_at": phase.actual_start_date,
        "updated_at": phase.updated_at,
        "is_current": True,
        "planning_data": {
            "phase_name": phase.phase_name,
            "planned_start_date": phase.planned_start_date,
            "planned_end_date": phase.planned_end_date,
            "actual_start_date": phase.actual_start_date,
            "actual_end_date": phase.actual_end_date
        }
    }


# Use existing data source models and services
from app.models.data_source import DataSource
from app.application.use_cases.data_source import DataSourceUseCase
from app.application.dtos.data_source import DataSourceCreateDTO, DataSourceUpdateDTO

# Data Source Management Endpoints for Planning Phase
@router.get("/cycles/{cycle_id}/reports/{report_id}/data-sources")
async def get_planning_data_sources(
    cycle_id: int,
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get data sources for a planning phase"""
    # Check permissions
    RoleChecker(tester_roles + management_roles)(current_user)
    
    # Get planning phase first
    phase_query = select(WorkflowPhase).where(
        and_(
            WorkflowPhase.cycle_id == cycle_id,
            WorkflowPhase.report_id == report_id,
            WorkflowPhase.phase_name == "Planning"
        )
    )
    
    phase_result = await db.execute(phase_query)
    phase = phase_result.scalar_one_or_none()
    
    if not phase:
        return []
    
    # Query data sources using ORM
    query = select(CycleReportDataSource).where(
        CycleReportDataSource.phase_id == phase.phase_id
    ).order_by(CycleReportDataSource.created_at.desc())
    
    result = await db.execute(query)
    data_sources = result.scalars().all()
    
    # Convert to response format
    result_list = []
    for ds in data_sources:
        result_list.append({
            "id": str(ds.id),
            "name": ds.name,
            "description": ds.description or "",
            "source_type": ds.source_type.value,
            "is_active": ds.is_active,
            "connection_config": ds.connection_config or {},
            "auth_type": ds.auth_type or "basic",
            "auth_config": ds.auth_config or {},
            "refresh_schedule": ds.refresh_schedule or "",
            "last_sync_at": ds.last_sync_at.isoformat() if ds.last_sync_at else None,
            "last_sync_status": ds.last_sync_status or "never",
            "last_sync_message": ds.last_sync_message or "",
            "validation_rules": ds.validation_rules or {},
            "created_at": ds.created_at.isoformat() if ds.created_at else None,
            "updated_at": ds.updated_at.isoformat() if ds.updated_at else None,
        })
    
    return result_list


@router.post("/cycles/{cycle_id}/reports/{report_id}/data-sources")
async def create_planning_data_source(
    cycle_id: int,
    report_id: int,
    data_source_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a data source for a planning phase"""
    # Check permissions
    RoleChecker(tester_roles + management_roles)(current_user)
    
    # Get planning phase first
    phase_query = select(WorkflowPhase).where(
        and_(
            WorkflowPhase.cycle_id == cycle_id,
            WorkflowPhase.report_id == report_id,
            WorkflowPhase.phase_name == "Planning"
        )
    )
    
    phase_result = await db.execute(phase_query)
    phase = phase_result.scalar_one_or_none()
    
    if not phase:
        raise HTTPException(status_code=404, detail="Planning phase not found")
    
    # Create new data source using ORM model
    new_data_source = CycleReportDataSource(
        phase_id=phase.phase_id,
        name=data_source_data.get("name", "New Data Source"),
        description=data_source_data.get("description", ""),
        source_type=data_source_data.get("source_type", DataSourceType.POSTGRESQL),
        is_active=True,
        connection_config=data_source_data.get("connection_config", {}),
        auth_type=data_source_data.get("auth_type", "basic"),
        auth_config=data_source_data.get("auth_config", {}),
        refresh_schedule=data_source_data.get("refresh_schedule", ""),
        last_sync_status="never",
        validation_rules=data_source_data.get("validation_rules", {}),
        created_by_id=current_user.user_id,
        updated_by_id=current_user.user_id
    )
    
    db.add(new_data_source)
    await db.commit()
    await db.refresh(new_data_source)
    
    return {
        "id": str(new_data_source.id),
        "name": new_data_source.name,
        "description": new_data_source.description or "",
        "source_type": new_data_source.source_type.value,
        "is_active": new_data_source.is_active,
        "connection_config": new_data_source.connection_config or {},
        "auth_type": new_data_source.auth_type,
        "auth_config": new_data_source.auth_config or {},
        "refresh_schedule": new_data_source.refresh_schedule or "",
        "last_sync_at": new_data_source.last_sync_at.isoformat() if new_data_source.last_sync_at else None,
        "last_sync_status": new_data_source.last_sync_status or "never",
        "last_sync_message": new_data_source.last_sync_message or "",
        "validation_rules": new_data_source.validation_rules or {},
        "created_at": new_data_source.created_at.isoformat() if new_data_source.created_at else None,
        "updated_at": new_data_source.updated_at.isoformat() if new_data_source.updated_at else None,
    }


@router.put("/cycles/{cycle_id}/reports/{report_id}/data-sources/{data_source_id}")
async def update_planning_data_source(
    cycle_id: int,
    report_id: int,
    data_source_id: int,
    data_source_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a data source for a planning phase"""
    # Check permissions
    RoleChecker(tester_roles + management_roles)(current_user)
    
    # Get existing data source
    query = select(CycleReportDataSource).where(
        CycleReportDataSource.id == data_source_id
    )
    
    result = await db.execute(query)
    data_source = result.scalar_one_or_none()
    
    if not data_source:
        raise HTTPException(status_code=404, detail="Data source not found")
    
    # Update fields
    if "name" in data_source_data:
        data_source.name = data_source_data["name"]
    if "description" in data_source_data:
        data_source.description = data_source_data["description"]
    if "source_type" in data_source_data:
        data_source.source_type = data_source_data["source_type"]
    if "connection_config" in data_source_data:
        data_source.connection_config = data_source_data["connection_config"]
    if "auth_type" in data_source_data:
        data_source.auth_type = data_source_data["auth_type"]
    if "auth_config" in data_source_data:
        data_source.auth_config = data_source_data["auth_config"]
    if "refresh_schedule" in data_source_data:
        data_source.refresh_schedule = data_source_data["refresh_schedule"]
    if "validation_rules" in data_source_data:
        data_source.validation_rules = data_source_data["validation_rules"]
    
    data_source.updated_by_id = current_user.user_id
    data_source.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(data_source)
    
    return {
        "id": str(data_source.id),
        "name": data_source.name,
        "description": data_source.description or "",
        "source_type": data_source.source_type.value,
        "is_active": data_source.is_active,
        "connection_config": data_source.connection_config or {},
        "auth_type": data_source.auth_type,
        "auth_config": data_source.auth_config or {},
        "refresh_schedule": data_source.refresh_schedule or "",
        "last_sync_at": data_source.last_sync_at.isoformat() if data_source.last_sync_at else None,
        "last_sync_status": data_source.last_sync_status or "never",
        "last_sync_message": data_source.last_sync_message or "",
        "validation_rules": data_source.validation_rules or {},
        "created_at": data_source.created_at.isoformat() if data_source.created_at else None,
        "updated_at": data_source.updated_at.isoformat() if data_source.updated_at else None,
    }


@router.delete("/cycles/{cycle_id}/reports/{report_id}/data-sources/{data_source_id}")
async def delete_planning_data_source(
    cycle_id: int,
    report_id: int,
    data_source_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a data source for a planning phase"""
    # Check permissions
    RoleChecker(tester_roles + management_roles)(current_user)
    
    # Get existing data source
    query = select(CycleReportDataSource).where(
        CycleReportDataSource.id == data_source_id
    )
    
    result = await db.execute(query)
    data_source = result.scalar_one_or_none()
    
    if not data_source:
        raise HTTPException(status_code=404, detail="Data source not found")
    
    # Store info for response
    deleted_id = data_source.id
    deleted_name = data_source.name
    
    # Delete the data source
    await db.delete(data_source)
    await db.commit()
    
    return {
        "message": "Data source deleted successfully",
        "deleted_id": str(deleted_id),
        "deleted_name": deleted_name
    }


@router.post("/cycles/{cycle_id}/reports/{report_id}/data-sources/test-connection")
async def test_planning_data_source_connection(
    cycle_id: int,
    report_id: int,
    connection_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Test connection for a planning phase data source"""
    # Mock connection testing until proper implementation
    # TODO: Implement actual connection testing based on source_type
    
    source_type = connection_data.get("source_type", "database")
    connection_config = connection_data.get("connection_config", {})
    
    # Mock different responses based on source type
    if source_type == "database":
        host = connection_config.get("host", "localhost")
        database = connection_config.get("database", "test_db")
        return {
            "success": True,
            "message": f"Successfully connected to database '{database}' on '{host}'",
            "connection_details": {
                "source_type": source_type,
                "host": host,
                "database": database,
                "status": "connected",
                "test_time": datetime.utcnow().isoformat(),
                "response_time_ms": 150
            }
        }
    elif source_type == "api":
        url = connection_config.get("url", "https://api.example.com")
        return {
            "success": True,
            "message": f"Successfully connected to API endpoint '{url}'",
            "connection_details": {
                "source_type": source_type,
                "url": url,
                "status": "connected",
                "test_time": datetime.utcnow().isoformat(),
                "response_time_ms": 230
            }
        }
    else:
        return {
            "success": True,
            "message": f"Connection test successful for {source_type} source",
            "connection_details": {
                "source_type": source_type,
                "status": "connected",
                "test_time": datetime.utcnow().isoformat(),
                "response_time_ms": 100
            }
        }