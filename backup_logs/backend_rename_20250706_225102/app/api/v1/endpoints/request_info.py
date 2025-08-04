"""
Request for Information phase API endpoints
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, and_, func, update, delete, or_
import logging
import time
import os
import hashlib
import uuid
import mimetypes
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.test_cycle import TestCycle
from app.models.cycle_report import CycleReport
from app.models.report import Report
from app.models.workflow import WorkflowPhase
from app.models.report_attribute import ReportAttribute
from app.models.testing import DataProviderAssignment
from app.models.sample_selection import SampleSet, SampleRecord
from app.models.request_info import (
    RequestInfoPhase, TestCase, DataProviderNotification, DocumentSubmission,
    RequestInfoAuditLog
)
from app.schemas.request_info import (
    RequestInfoPhaseStatus, TestCaseStatus, DocumentType, SubmissionStatus,
    RequestInfoPhaseCreate, RequestInfoPhaseUpdate, RequestInfoPhaseResponse,
    TestCaseResponse, TestCaseWithDetails, TestCaseListResponse,
    DocumentSubmissionResponse, DataProviderPortalData,
    StartPhaseRequest, TesterPhaseView, PhaseCompletionRequest,
    FileUploadResponse, PhaseProgressSummary, DataProviderAssignmentSummary,
    TestCaseUpdate
)
from app.services.request_info_service import RequestInfoService

logger = logging.getLogger(__name__)
router = APIRouter()

# File upload configuration
UPLOAD_DIR = "uploads/request_info"
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB
ALLOWED_EXTENSIONS = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.txt', '.csv', '.png', '.jpg', '.jpeg'}

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Role dependency functions
def require_tester(current_user: User = Depends(get_current_user)):
    """Require tester role"""
    if not current_user.is_tester:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tester role required"
        )
    return True

def require_data_provider(current_user: User = Depends(get_current_user)):
    """Require data provider role"""
    if current_user.role != 'Data Provider':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Data Provider role required"
        )
    return True

def require_tester_or_data_provider(current_user: User = Depends(get_current_user)):
    """Require tester or data provider role"""
    if not current_user.is_tester and current_user.role != 'Data Provider':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tester or Data Provider role required"
        )
    return True

async def create_audit_log(
    db: AsyncSession, cycle_id: int, report_id: int, action: str, entity_type: str, 
    entity_id: str, performed_by: int, old_values: Dict = None, new_values: Dict = None, 
    notes: str = None, request: Request = None
):
    """Create audit log entry"""
    audit_log = RequestInfoAuditLog(
        cycle_id=cycle_id,
        report_id=report_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        performed_by=performed_by,
        old_values=old_values,
        new_values=new_values,
        notes=notes,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None
    )
    db.add(audit_log)

def calculate_file_hash(file_path: str) -> str:
    """Calculate SHA-256 hash of file"""
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

# async def validate_submission_data(submission: SampleSubmissionRequest, db: AsyncSession) -> List[str]:
#     """Validate submission data and return validation messages"""
#     messages = []
#     
#     # Validate sample record exists
#     sample_exists = await db.execute(
#         select(SampleRecord).where(SampleRecord.record_id == submission.sample_record_id)
#     )
#     if not sample_exists.scalar_one_or_none():
#         messages.append(f"Sample record {submission.sample_record_id} not found")
#     
#     # Validate attribute exists
#     attribute_exists = await db.execute(
#         select(ReportAttribute).where(ReportAttribute.attribute_id == submission.attribute_id)
#     )
#     if not attribute_exists.scalar_one_or_none():
#         messages.append(f"Attribute {submission.attribute_id} not found")
#     
#     # Validate document IDs if provided
#     if submission.document_ids:
#         for doc_id in submission.document_ids:
#             doc_exists = await db.execute(
#                 select(DocumentSubmission).where(DocumentSubmission.submission_id == doc_id)
#             )
#             if not doc_exists.scalar_one_or_none():
#                 messages.append(f"Document {doc_id} not found")
#     
#     # Validate confidence level
#     if submission.confidence_level and submission.confidence_level not in ['High', 'Medium', 'Low']:
#         messages.append("Confidence level must be High, Medium, or Low")
#     
#     return messages


@router.post("/phases", response_model=RequestInfoPhaseResponse)
def create_request_info_phase(
    phase_data: RequestInfoPhaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new Request for Information phase"""
    service = RequestInfoService(db)
    return service.create_phase(phase_data, current_user.user_id)


@router.get("/phases/{phase_id}", response_model=RequestInfoPhaseResponse)
def get_request_info_phase(
    phase_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get Request for Information phase details"""
    service = RequestInfoService(db)
    return service.get_phase(phase_id)


@router.post("/phases/{phase_id}/start", response_model=RequestInfoPhaseResponse)
async def start_request_info_phase(
    phase_id: str,
    start_request: StartPhaseRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start the Request for Information phase"""
    
    # Get the phase
    result = await db.execute(
        select(RequestInfoPhase).where(RequestInfoPhase.phase_id == phase_id)
    )
    phase = result.scalar_one_or_none()
    
    if not phase:
        raise HTTPException(status_code=404, detail="Phase not found")
    
    if phase.phase_status != "Not Started":
        raise HTTPException(status_code=400, detail="Phase has already been started")
    
    try:
        # Generate test cases from data provider assignments
        logger.info(f"Starting test case generation for phase {phase_id}")
        test_cases_created = await _generate_test_cases_async(db, phase, current_user.user_id, start_request.submission_deadline)
        logger.info(f"Created {test_cases_created} test cases for phase {phase_id}")
    except Exception as e:
        logger.error(f"Error generating test cases for phase {phase_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate test cases: {str(e)}")
    
    # Update phase to started
    phase.phase_status = "In Progress"
    phase.started_by = current_user.user_id
    phase.started_at = datetime.utcnow()
    phase.instructions = start_request.instructions
    phase.submission_deadline = start_request.submission_deadline
    
    await db.commit()
    await db.refresh(phase)
    
    # Send notifications if requested
    if start_request.auto_notify_data_providers and start_request.notify_immediately:
        try:
            logger.info(f"Sending notifications for phase {phase_id}")
            await _send_data_provider_notifications_async(db, phase)
            logger.info(f"Notifications sent for phase {phase_id}")
        except Exception as e:
            logger.error(f"Error sending notifications for phase {phase_id}: {str(e)}")
            # Don't fail the whole operation if notifications fail
    
    return RequestInfoPhaseResponse.from_orm(phase)


async def _generate_test_cases_async(db: AsyncSession, phase: RequestInfoPhase, user_id: int, submission_deadline: datetime) -> int:
    """Generate test cases from data provider assignments (async version)"""
    
    logger.info(f"Generating test cases for phase {phase.phase_id}, cycle {phase.cycle_id}, report {phase.report_id}")
    
    # Get all data provider assignments for this cycle/report (non-PK attributes only)
    assignments_result = await db.execute(
        select(DataProviderAssignment)
        .options(selectinload(DataProviderAssignment.attribute))
        .where(
            and_(
                DataProviderAssignment.cycle_id == phase.cycle_id,
                DataProviderAssignment.report_id == phase.report_id
            )
        )
    )
    assignments = assignments_result.scalars().all()
    logger.info(f"Found {len(assignments)} total data provider assignments")
    
    if not assignments:
        raise HTTPException(
            status_code=400, 
            detail="No data provider assignments found"
        )
    
    # Filter to only non-primary key attributes
    non_pk_assignments = [a for a in assignments if a.attribute and not a.attribute.is_primary_key]
    logger.info(f"Found {len(non_pk_assignments)} non-PK assignments")
    
    if not non_pk_assignments:
        raise HTTPException(
            status_code=400, 
            detail="No data provider assignments found for non-primary key attributes"
        )
    
    # Get sample records for this cycle/report through SampleSet relationship
    samples_result = await db.execute(
        select(SampleRecord)
        .join(SampleSet)
        .where(
            and_(
                SampleSet.cycle_id == phase.cycle_id,
                SampleSet.report_id == phase.report_id
            )
        )
    )
    samples = samples_result.scalars().all()
    logger.info(f"Found {len(samples)} sample records")
    
    if not samples:
        raise HTTPException(
            status_code=400, 
            detail="No sample records found for this cycle and report"
        )
    
    # Get primary key attributes from scoping decisions (not assignments)
    from app.models.scoping import TesterScopingDecision
    pk_scoping_result = await db.execute(
        select(TesterScopingDecision)
        .options(selectinload(TesterScopingDecision.attribute))
        .where(
            and_(
                TesterScopingDecision.cycle_id == phase.cycle_id,
                TesterScopingDecision.report_id == phase.report_id,
                TesterScopingDecision.final_scoping == True
            )
        )
    )
    pk_scoping_decisions = pk_scoping_result.scalars().all()
    pk_attributes = [s.attribute for s in pk_scoping_decisions if s.attribute and s.attribute.is_primary_key]
    logger.info(f"Found {len(pk_attributes)} PK attributes from scoping for context")
    
    test_cases_created = 0
    
    # Create test cases: one per non-PK attribute per sample
    for assignment in non_pk_assignments:
        logger.info(f"Processing assignment for attribute {assignment.attribute.attribute_name} (ID: {assignment.attribute_id})")
        for sample in samples:
            # Build primary key context for this sample
            pk_context = {}
            for pk_attr in pk_attributes:
                # Get the sample value for this PK attribute
                pk_context[pk_attr.attribute_name] = sample.sample_data.get(
                    pk_attr.attribute_name, "N/A"
                )
            
            test_case = TestCase(
                phase_id=phase.phase_id,
                cycle_id=phase.cycle_id,
                report_id=phase.report_id,
                attribute_id=assignment.attribute_id,
                sample_id=sample.record_id,
                sample_identifier=sample.sample_identifier,
                data_provider_id=assignment.data_provider_id,
                assigned_by=user_id,
                attribute_name=assignment.attribute.attribute_name,
                primary_key_attributes=pk_context,
                submission_deadline=submission_deadline,
                expected_evidence_type="Document",
                special_instructions=f"Please provide evidence for {assignment.attribute.attribute_name} for the sample identified by: {', '.join([f'{k}: {v}' for k, v in pk_context.items()])}"
            )
            
            db.add(test_case)
            test_cases_created += 1
            logger.info(f"Created test case {test_case.test_case_id} for attribute {assignment.attribute.attribute_name}, sample {sample.sample_identifier}")
    
    logger.info(f"Total test cases created: {test_cases_created}")
    await db.commit()
    return test_cases_created


async def _send_data_provider_notifications_async(db: AsyncSession, phase: RequestInfoPhase):
    """Send notifications to data providers (async version)"""
    
    # Get unique data providers and their assignments
    result = await db.execute(
        select(
            TestCase.data_owner_id,
            func.array_agg(TestCase.attribute_name.distinct()).label('attributes'),
            func.count(TestCase.test_case_id).label('test_case_count')
        )
        .where(TestCase.phase_id == phase.phase_id)
        .group_by(TestCase.data_owner_id)
    )
    data_providers = result.all()
    
    for dp_id, attributes, test_case_count in data_providers:
        # Create notification
        notification = DataProviderNotification(
            phase_id=phase.phase_id,
            cycle_id=phase.cycle_id,
            report_id=phase.report_id,
            data_provider_id=dp_id,
            assigned_attributes=attributes,
            sample_count=test_case_count,
            submission_deadline=phase.submission_deadline,
            portal_access_url=f"/data-provider/request-info/{phase.phase_id}",
            custom_instructions=phase.instructions
        )
        
        db.add(notification)
    
    await db.commit()


@router.post("/phases/{phase_id}/complete", response_model=RequestInfoPhaseResponse)
def complete_request_info_phase(
    phase_id: str,
    completion_request: PhaseCompletionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Complete the Request for Information phase"""
    service = RequestInfoService(db)
    return service.complete_phase(phase_id, completion_request, current_user.user_id)


@router.get("/phases/{phase_id}/tester-view", response_model=TesterPhaseView)
async def get_tester_phase_view(
    phase_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive phase view for testers"""
    # Get phase details
    result = await db.execute(
        select(RequestInfoPhase).where(RequestInfoPhase.phase_id == phase_id)
    )
    phase = result.scalar_one_or_none()
    
    if not phase:
        raise HTTPException(status_code=404, detail="Phase not found")
    
    # For Tester/Admin users, return comprehensive tester view
    
    # DEBUG: Simple test return
    return {"debug": "tester_view_reached", "phase_status": phase.phase_status, "can_start_phase": phase.phase_status == 'Not Started'}


@router.get("/phases/{phase_id}/test-cases", response_model=TestCaseListResponse)
async def get_test_cases(
    phase_id: str,
    data_provider_id: Optional[int] = Query(None, description="Filter by data provider"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get test cases for a phase"""
    # Get test cases with basic filtering and relationships
    query = select(TestCase).options(
        selectinload(TestCase.data_owner),
        selectinload(TestCase.attribute),
        selectinload(TestCase.document_submissions),
        selectinload(TestCase.cycle),
        selectinload(TestCase.report),
        selectinload(TestCase.assigned_by_user)
    ).where(TestCase.phase_id == phase_id)
    
    if data_provider_id:
        query = query.where(TestCase.data_owner_id == data_provider_id)
    
    if status_filter:
        query = query.where(TestCase.status == status_filter)
    
    result = await db.execute(query)
    test_cases = result.scalars().all()
    
    # Convert to TestCaseWithDetails format
    test_cases_with_details = []
    for tc in test_cases:
        # Safely access relationships
        data_provider_name = None
        data_provider_email = None
        assigned_by_name = None
        
        if tc.data_owner:
            data_provider_name = f"{tc.data_owner.first_name} {tc.data_owner.last_name}"
            data_provider_email = tc.data_owner.email
            
        if tc.assigned_by_user:
            assigned_by_name = f"{tc.assigned_by_user.first_name} {tc.assigned_by_user.last_name}"
        
        # Count documents
        doc_count = len(tc.document_submissions) if tc.document_submissions else 0
        
        # Get cycle and report names
        cycle_name = tc.cycle.cycle_name if tc.cycle else f"Cycle {tc.cycle_id}"
        report_name = tc.report.report_name if tc.report else f"Report {tc.report_id}"
        
        test_case_detail = {
            "test_case_id": tc.test_case_id,
            "phase_id": tc.phase_id,
            "cycle_id": tc.cycle_id,
            "cycle_name": cycle_name,
            "report_id": tc.report_id,
            "report_name": report_name,
            "attribute_id": tc.attribute_id,
            "sample_id": tc.sample_id,
            "data_owner_id": tc.data_owner_id,
            "assigned_by": tc.assigned_by,
            "assigned_at": tc.assigned_at.isoformat() if tc.assigned_at else None,
            "attribute_name": tc.attribute_name,
            "sample_identifier": tc.sample_identifier,
            "primary_key_attributes": tc.primary_key_attributes,
            "expected_evidence_type": tc.expected_evidence_type,
            "special_instructions": tc.special_instructions,
            "submission_deadline": tc.submission_deadline.isoformat() if tc.submission_deadline else None,
            "status": tc.status,
            "submitted_at": tc.submitted_at.isoformat() if tc.submitted_at else None,
            "acknowledged_at": tc.acknowledged_at.isoformat() if tc.acknowledged_at else None,
            "created_at": tc.created_at.isoformat(),
            "updated_at": tc.updated_at.isoformat(),
            "data_provider_name": data_provider_name,
            "data_provider_email": data_provider_email,
            "assigned_by_name": assigned_by_name,
            "document_count": doc_count,
            "has_submissions": doc_count > 0
        }
        test_cases_with_details.append(test_case_detail)
    
    # Calculate counts
    total_count = len(test_cases)
    submitted_count = len([tc for tc in test_cases if tc.status == 'Submitted'])
    pending_count = len([tc for tc in test_cases if tc.status == 'Pending'])
    overdue_count = len([tc for tc in test_cases if tc.status == 'Overdue'])
    
    return TestCaseListResponse(
        test_cases=test_cases_with_details,
        total_count=total_count,
        submitted_count=submitted_count,
        pending_count=pending_count,
        overdue_count=overdue_count,
        data_provider_id=data_provider_id,
        status_filter=status_filter
    )


# Data Provider Portal Endpoints
@router.get("/phases/{phase_id}/data-provider-portal", response_model=DataProviderPortalData)
def get_data_provider_portal(
    phase_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get data provider portal data"""
    service = RequestInfoService(db)
    return service.get_data_provider_portal_data(phase_id, current_user.user_id)


@router.post("/test-cases/{test_case_id}/upload", response_model=FileUploadResponse)
async def upload_document(
    test_case_id: str,
    file: UploadFile = File(...),
    submission_notes: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload document for a test case"""
    from app.models.request_info import TestCase, DocumentSubmission
    from sqlalchemy import select
    import os
    import shutil
    import uuid
    import mimetypes
    from datetime import datetime, timezone
    
    try:
        # Get test case
        result = await db.execute(select(TestCase).where(TestCase.test_case_id == test_case_id))
        test_case = result.scalar_one_or_none()
        
        if not test_case:
            raise HTTPException(status_code=404, detail="Test case not found")
        
        # Check authorization
        if (current_user.role not in ["TESTER", "ADMIN"] and 
            test_case.data_provider_id != current_user.user_id):
            raise HTTPException(status_code=403, detail="Not authorized to upload for this test case")
        
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Determine document type and validate
        mime_type, _ = mimetypes.guess_type(file.filename)
        document_type = _determine_document_type(file.filename, mime_type)
        
        # Ensure upload directory exists
        upload_dir = "uploads/request_info"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1]
        stored_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(upload_dir, stored_filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Create document submission record
        submission = DocumentSubmission(
            test_case_id=test_case_id,
            data_provider_id=current_user.user_id,
            original_filename=file.filename,
            stored_filename=stored_filename,
            file_path=file_path,
            file_size_bytes=file_size,
            document_type=document_type,
            mime_type=mime_type or "application/octet-stream",
            submission_notes=submission_notes
        )
        
        db.add(submission)
        await db.commit()
        await db.refresh(submission)
        
        return FileUploadResponse(
            success=True,
            message="Document uploaded successfully",
            submission_id=submission.submission_id,
            file_info={
                "original_filename": file.filename,
                "file_size": file_size,
                "document_type": document_type
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # Clean up file if it was created
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        
        print(f"[Upload Document] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to upload document: {str(e)}")


def _determine_document_type(filename: str, mime_type: Optional[str]) -> str:
    """Determine document type from filename and mime type"""
    
    filename_lower = filename.lower()
    
    # Map file types to the database enum values
    if filename_lower.endswith('.pdf') or (mime_type and 'pdf' in mime_type):
        return "Source Document"  # PDFs are typically source documents
    elif filename_lower.endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff')) or (mime_type and 'image' in mime_type):
        return "Supporting Evidence"  # Images are typically supporting evidence
    elif filename_lower.endswith(('.xls', '.xlsx', '.csv')) or (mime_type and ('excel' in mime_type or 'spreadsheet' in mime_type)):
        return "Data Extract"  # Spreadsheets are typically data extracts
    elif filename_lower.endswith(('.doc', '.docx', '.txt')) or (mime_type and ('word' in mime_type or 'text' in mime_type)):
        return "Supporting Evidence"  # Word docs are typically supporting evidence
    else:
        return "Other"


@router.get("/test-cases/{test_case_id}", response_model=TestCaseWithDetails)
def get_test_case(
    test_case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get test case details"""
    service = RequestInfoService(db)
    
    # Get the test case
    from app.models.request_info import TestCase
    test_case = db.query(TestCase).filter(TestCase.test_case_id == test_case_id).first()
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")
    
    # Check authorization
    if current_user.role not in ["TESTER", "ADMIN"] and test_case.data_provider_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this test case")
    
    return service._test_case_with_details(test_case)


@router.get("/test-cases/{test_case_id}/documents", response_model=List[DocumentSubmissionResponse])
def get_test_case_documents(
    test_case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get documents for a test case"""
    from app.models.request_info import TestCase, DocumentSubmission
    
    # Verify test case exists and user has access
    test_case = db.query(TestCase).filter(TestCase.test_case_id == test_case_id).first()
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")
    
    if current_user.role not in ["TESTER", "ADMIN"] and test_case.data_provider_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this test case")
    
    # Get documents
    documents = db.query(DocumentSubmission).filter(
        DocumentSubmission.test_case_id == test_case_id
    ).all()
    
    return [DocumentSubmissionResponse.from_orm(doc) for doc in documents]


# Cycle-level endpoints for integration with existing workflow
@router.get("/cycles/{cycle_id}/reports/{report_id}/request-info-phase")
async def get_cycle_report_request_info_phase(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get Request for Information phase for a specific cycle and report"""
    from app.models.request_info import RequestInfoPhase, TestCase, DocumentSubmission
    from app.models.testing import DataProviderAssignment
    from app.schemas.request_info import TesterPhaseView, PhaseProgressSummary, DataProviderAssignmentSummary
    from sqlalchemy.orm import selectinload
    
    # Get phase details
    result = await db.execute(
        select(RequestInfoPhase).where(
            and_(
                RequestInfoPhase.cycle_id == cycle_id,
                RequestInfoPhase.report_id == report_id
            )
        )
    )
    phase = result.scalar_one_or_none()
    
    if not phase:
        return None
    
    # For Data Provider users, return portal data
    if current_user.role == 'Data Provider':
        service = RequestInfoService(db)
        return service.get_data_provider_portal_data(phase.phase_id, current_user.user_id)
    
    # For Tester/Admin users, return comprehensive tester view
    
    # Get cycle and report names
    cycle_result = await db.execute(select(TestCycle).where(TestCycle.cycle_id == cycle_id))
    cycle = cycle_result.scalar_one_or_none()
    cycle_name = cycle.cycle_name if cycle else f"Cycle {cycle_id}"
    
    report_result = await db.execute(select(Report).where(Report.report_id == report_id))
    report = report_result.scalar_one_or_none()
    report_name = report.report_name if report else f"Report {report_id}"
    
    # Get test cases with details
    test_cases_result = await db.execute(
        select(TestCase)
        .options(
            selectinload(TestCase.data_owner),
            selectinload(TestCase.attribute),
            selectinload(TestCase.document_submissions)
        )
        .where(TestCase.phase_id == phase.phase_id)
    )
    test_cases = test_cases_result.scalars().all()
    
    # Calculate progress summary
    total_test_cases = len(test_cases)
    submitted_test_cases = len([tc for tc in test_cases if tc.status == 'Submitted'])
    pending_test_cases = len([tc for tc in test_cases if tc.status == 'Pending'])
    overdue_test_cases = len([tc for tc in test_cases if tc.status == 'Overdue'])
    completion_percentage = (submitted_test_cases / total_test_cases * 100) if total_test_cases > 0 else 0
    
    # Get unique data providers
    data_providers = {}
    for tc in test_cases:
        dp_id = tc.data_owner_id
        if dp_id not in data_providers:
            data_providers[dp_id] = {
                'data_provider_id': dp_id,
                'data_provider_name': tc.data_owner.full_name if tc.data_owner else 'Unknown',
                'data_provider_email': tc.data_owner.email if tc.data_owner else '',
                'assigned_attributes': [],
                'total_test_cases': 0,
                'submitted_test_cases': 0,
                'pending_test_cases': 0,
                'overdue_test_cases': 0,
                'overall_status': 'PENDING',
                'last_activity': None,
                'notification_sent': False,
                'portal_accessed': False
            }
        
        # Update counts
        data_providers[dp_id]['total_test_cases'] += 1
        if tc.status == 'Submitted':
            data_providers[dp_id]['submitted_test_cases'] += 1
        elif tc.status == 'Pending':
            data_providers[dp_id]['pending_test_cases'] += 1
        elif tc.status == 'Overdue':
            data_providers[dp_id]['overdue_test_cases'] += 1
        
        # Add attribute if not already present
        if tc.attribute and tc.attribute.attribute_name not in data_providers[dp_id]['assigned_attributes']:
            data_providers[dp_id]['assigned_attributes'].append(tc.attribute.attribute_name)
    
    # Update overall status for each data provider
    for dp_data in data_providers.values():
        if dp_data['submitted_test_cases'] == dp_data['total_test_cases']:
            dp_data['overall_status'] = 'Submitted'
        elif dp_data['overdue_test_cases'] > 0:
            dp_data['overall_status'] = 'Overdue'
        else:
            dp_data['overall_status'] = 'In Progress'
    
    # Convert to simple dictionaries instead of Pydantic objects to avoid validation issues
    data_provider_summaries = [
        {
            "data_provider_id": dp['data_provider_id'],
            "data_provider_name": dp['data_provider_name'],
            "data_provider_email": dp['data_provider_email'],
            "assigned_attributes": dp['assigned_attributes'],
            "total_test_cases": dp['total_test_cases'],
            "submitted_test_cases": dp['submitted_test_cases'],
            "pending_test_cases": dp['pending_test_cases'],
            "overdue_test_cases": dp['overdue_test_cases'],
            "overall_status": dp['overall_status'],
            "last_activity": dp['last_activity'],
            "notification_sent": dp['notification_sent'],
            "portal_accessed": dp['portal_accessed']
        }
        for dp in data_providers.values()
    ]
    
    data_providers_count = len(data_provider_summaries)
    data_providers_completed = len([dp for dp in data_provider_summaries if dp['overall_status'] == 'Submitted'])
    
    progress_summary = PhaseProgressSummary(
        phase_id=phase.phase_id,
        phase_name="Request for Information",
        phase_status=phase.phase_status,
        cycle_name=cycle_name,
        report_name=report_name,
        total_test_cases=total_test_cases,
        submitted_test_cases=submitted_test_cases,
        pending_test_cases=pending_test_cases,
        overdue_test_cases=overdue_test_cases,
        completion_percentage=completion_percentage,
        started_at=phase.started_at,
        submission_deadline=phase.submission_deadline,
        days_remaining=None,  # Calculate if needed
        total_data_owners=data_providers_count,
        notified_data_owners=0,  # TODO: Calculate from notifications
        active_data_owners=len([dp for dp in data_provider_summaries if dp['overall_status'] != 'Submitted'])
    )
    
    # Get recent submissions (last 10)
    recent_submissions_result = await db.execute(
        select(DocumentSubmission)
        .join(TestCase)
        .where(TestCase.phase_id == phase.phase_id)
        .order_by(DocumentSubmission.submitted_at.desc())
        .limit(10)
    )
    recent_submissions = recent_submissions_result.scalars().all()
    
    # Get overdue test cases
    overdue_test_cases_list = [tc for tc in test_cases if tc.status == 'Overdue']
    
    # Determine capabilities
    can_start_phase = phase.phase_status == 'Not Started'
    can_complete_phase = (phase.phase_status == 'In Progress' and 
                         submitted_test_cases == total_test_cases and 
                         total_test_cases > 0)
    can_send_reminders = phase.phase_status == 'In Progress' and pending_test_cases > 0
    
    # Return simple structure that matches frontend interfaces
    return {
        "phase": {
            "phase_id": phase.phase_id,
            "cycle_id": phase.cycle_id,
            "report_id": phase.report_id,
            "phase_status": phase.phase_status,
            "instructions": phase.instructions,
            "submission_deadline": phase.submission_deadline.isoformat() if phase.submission_deadline else None,
            "started_by": phase.started_by,
            "started_at": phase.started_at.isoformat() if phase.started_at else None,
            "completed_by": phase.completed_by,
            "completed_at": phase.completed_at.isoformat() if phase.completed_at else None,
            "created_at": phase.created_at.isoformat(),
            "updated_at": phase.updated_at.isoformat()
        },
        "cycle_name": cycle_name,
        "report_name": report_name,
        "progress_summary": {
            "total_test_cases": total_test_cases,
            "submitted_test_cases": submitted_test_cases,
            "pending_test_cases": pending_test_cases,
            "overdue_test_cases": overdue_test_cases,
            "completion_percentage": completion_percentage,
            "data_providers_count": data_providers_count,
            "data_providers_completed": data_providers_completed
        },
        "data_provider_summaries": data_provider_summaries,
        "recent_submissions": [],  # Empty for now
        "overdue_test_cases": [],  # Empty for now
        "can_start_phase": can_start_phase,
        "can_complete_phase": can_complete_phase,
        "can_send_reminders": can_send_reminders
    }


@router.post("/cycles/{cycle_id}/reports/{report_id}/request-info-phase", response_model=RequestInfoPhaseResponse)
async def create_cycle_report_request_info_phase(
    cycle_id: int,
    report_id: int,
    phase_data: RequestInfoPhaseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create Request for Information phase for a specific cycle and report"""
    # Override cycle_id and report_id from URL
    phase_data.cycle_id = cycle_id
    phase_data.report_id = report_id
    
    # Validate cycle and report exist
    cycle_result = await db.execute(select(TestCycle).where(TestCycle.cycle_id == cycle_id))
    cycle = cycle_result.scalar_one_or_none()
    if not cycle:
        raise HTTPException(status_code=404, detail="Test cycle not found")
    
    report_result = await db.execute(select(Report).where(Report.report_id == report_id))
    report = report_result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Check if phase already exists for this cycle/report
    existing_result = await db.execute(
        select(RequestInfoPhase).where(
            and_(
                RequestInfoPhase.cycle_id == cycle_id,
                RequestInfoPhase.report_id == report_id
            )
        )
    )
    existing_phase = existing_result.scalar_one_or_none()
    
    if existing_phase:
        raise HTTPException(
            status_code=400, 
            detail="Request for Information phase already exists for this cycle and report"
        )
    
    # Create phase
    phase = RequestInfoPhase(
        cycle_id=cycle_id,
        report_id=report_id,
        instructions=phase_data.instructions,
        submission_deadline=phase_data.submission_deadline
    )
    
    db.add(phase)
    await db.commit()
    await db.refresh(phase)
    
    return RequestInfoPhaseResponse.model_validate(phase)


@router.get("/cycles/{cycle_id}/reports/{report_id}/test-cases")
async def get_cycle_report_test_cases(
    cycle_id: int,
    report_id: int,
    data_owner_id: Optional[int] = Query(None, description="Filter by data owner"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get test cases for a specific cycle and report"""
    from sqlalchemy.orm import selectinload
    
    # Build query to get test cases for this cycle/report
    query = select(TestCase).options(
        selectinload(TestCase.data_owner),
        selectinload(TestCase.attribute),
        selectinload(TestCase.document_submissions),
        selectinload(TestCase.cycle),
        selectinload(TestCase.report),
        selectinload(TestCase.assigned_by_user)
    ).where(
        and_(
            TestCase.cycle_id == cycle_id,
            TestCase.report_id == report_id
        )
    )
    
    # Apply filters
    if data_owner_id:
        query = query.where(TestCase.data_owner_id == data_owner_id)
    
    if status:
        query = query.where(TestCase.status == status)
    
    result = await db.execute(query)
    test_cases = result.scalars().all()
    
    # Convert to response format with data owner information
    test_cases_data = []
    for tc in test_cases:
        # Safely access relationships
        data_owner_name = None
        data_owner_email = None
        assigned_by_name = None
        
        if tc.data_owner:
            data_owner_name = f"{tc.data_owner.first_name} {tc.data_owner.last_name}"
            data_owner_email = tc.data_owner.email
            
        if tc.assigned_by_user:
            assigned_by_name = f"{tc.assigned_by_user.first_name} {tc.assigned_by_user.last_name}"
        
        # Count documents
        doc_count = len(tc.document_submissions) if tc.document_submissions else 0
        
        test_case_data = {
            "test_case_id": tc.test_case_id,
            "phase_id": tc.phase_id,
            "cycle_id": tc.cycle_id,
            "report_id": tc.report_id,
            "attribute_id": tc.attribute_id,
            "sample_id": tc.sample_id,
            "sample_identifier": tc.sample_identifier,
            "data_owner_id": tc.data_owner_id,
            "assigned_by": tc.assigned_by,
            "assigned_at": tc.assigned_at.isoformat() if tc.assigned_at else None,
            "attribute_name": tc.attribute_name,
            "primary_key_attributes": tc.primary_key_attributes,
            "expected_evidence_type": tc.expected_evidence_type,
            "special_instructions": tc.special_instructions,
            "submission_deadline": tc.submission_deadline.isoformat() if tc.submission_deadline else None,
            "status": tc.status,
            "submitted_at": tc.submitted_at.isoformat() if tc.submitted_at else None,
            "acknowledged_at": tc.acknowledged_at.isoformat() if tc.acknowledged_at else None,
            "created_at": tc.created_at.isoformat(),
            "updated_at": tc.updated_at.isoformat(),
            "data_owner_name": data_owner_name,
            "data_owner_email": data_owner_email,
            "assigned_by_name": assigned_by_name,
            "document_count": doc_count,
            "has_submissions": doc_count > 0
        }
        test_cases_data.append(test_case_data)
    
    return test_cases_data


# Data Provider specific endpoints
@router.get("/data-provider/phases/{phase_id}/portal", response_model=DataProviderPortalData)
def data_provider_portal(
    phase_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Data provider portal access"""
    service = RequestInfoService(db)
    return service.get_data_provider_portal_data(phase_id, current_user.user_id)


@router.get("/data-provider/test-cases", response_model=List[TestCaseWithDetails])
async def get_my_test_cases(
    phase_id: Optional[str] = Query(None, description="Filter by phase"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get test cases assigned to current data provider"""
    from app.models.request_info import TestCase, DocumentSubmission
    from sqlalchemy.orm import selectinload
    from sqlalchemy import select, func
    
    try:
        # Build the query using SQLAlchemy 2.0 syntax
        query = select(TestCase).options(
            selectinload(TestCase.data_owner),
            selectinload(TestCase.assigned_by_user),
            selectinload(TestCase.document_submissions),
            selectinload(TestCase.cycle),
            selectinload(TestCase.report)
        ).where(TestCase.data_owner_id == current_user.user_id)
        
        if phase_id:
            query = query.where(TestCase.phase_id == phase_id)
        
        if status:
            query = query.where(TestCase.status == status)
        
        result = await db.execute(query)
        test_cases = result.scalars().all()
        
        # Convert to TestCaseWithDetails format directly
        test_cases_with_details = []
        for tc in test_cases:
            # Safely access relationships
            data_provider_name = None
            data_provider_email = None
            assigned_by_name = None
            
            if tc.data_owner:
                data_provider_name = f"{tc.data_owner.first_name} {tc.data_owner.last_name}"
                data_provider_email = tc.data_owner.email
                
            if tc.assigned_by_user:
                assigned_by_name = f"{tc.assigned_by_user.first_name} {tc.assigned_by_user.last_name}"
            
            # Count documents
            doc_count = len(tc.document_submissions) if tc.document_submissions else 0
            
            # Get cycle and report names
            cycle_name = tc.cycle.cycle_name if tc.cycle else f"Cycle {tc.cycle_id}"
            report_name = tc.report.report_name if tc.report else f"Report {tc.report_id}"
            
            test_case_detail = {
                "test_case_id": tc.test_case_id,
                "phase_id": tc.phase_id,
                "cycle_id": tc.cycle_id,
                "cycle_name": cycle_name,
                "report_id": tc.report_id,
                "report_name": report_name,
                "attribute_id": tc.attribute_id,
                "sample_id": tc.sample_id,
                "data_owner_id": tc.data_owner_id,
                "assigned_by": tc.assigned_by,
                "assigned_at": tc.assigned_at.isoformat() if tc.assigned_at else None,
                "attribute_name": tc.attribute_name,
                "sample_identifier": tc.sample_identifier,
                "primary_key_attributes": tc.primary_key_attributes,
                "expected_evidence_type": tc.expected_evidence_type,
                "special_instructions": tc.special_instructions,
                "submission_deadline": tc.submission_deadline.isoformat() if tc.submission_deadline else None,
                "status": tc.status,
                "submitted_at": tc.submitted_at.isoformat() if tc.submitted_at else None,
                "acknowledged_at": tc.acknowledged_at.isoformat() if tc.acknowledged_at else None,
                "created_at": tc.created_at.isoformat(),
                "updated_at": tc.updated_at.isoformat(),
                "data_provider_name": data_provider_name,
                "data_provider_email": data_provider_email,
                "assigned_by_name": assigned_by_name,
                "document_count": doc_count,
                "has_submissions": doc_count > 0
            }
            test_cases_with_details.append(test_case_detail)
        
        return test_cases_with_details
        
    except Exception as e:
        print(f"[Data Provider Test Cases] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to load test cases: {str(e)}")


# File download endpoint
@router.get("/documents/{submission_id}/download")
def download_document(
    submission_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download a submitted document"""
    from app.models.request_info import DocumentSubmission, TestCase
    from fastapi.responses import FileResponse
    import os
    
    # Get document submission
    submission = db.query(DocumentSubmission).join(TestCase).filter(
        DocumentSubmission.submission_id == submission_id
    ).first()
    
    if not submission:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check authorization
    test_case = submission.test_case
    if (current_user.role not in ["TESTER", "ADMIN"] and 
        test_case.data_provider_id != current_user.user_id):
        raise HTTPException(status_code=403, detail="Not authorized to download this document")
    
    # Check if file exists
    if not os.path.exists(submission.file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    return FileResponse(
        path=submission.file_path,
        filename=submission.original_filename,
        media_type=submission.mime_type
    )


# Admin/Tester endpoints for managing submissions
@router.put("/documents/{submission_id}/validate", response_model=DocumentSubmissionResponse)
def validate_document_submission(
    submission_id: str,
    is_valid: bool = Form(...),
    validation_notes: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Validate a document submission (Tester/Admin only)"""
    from app.models.request_info import DocumentSubmission
    from datetime import datetime
    
    # Check authorization
    if current_user.role not in ["TESTER", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Not authorized to validate submissions")
    
    submission = db.query(DocumentSubmission).filter(
        DocumentSubmission.submission_id == submission_id
    ).first()
    
    if not submission:
        raise HTTPException(status_code=404, detail="Document submission not found")
    
    # Update validation
    submission.is_valid = is_valid
    submission.validation_notes = validation_notes
    submission.validated_by = current_user.user_id
    submission.validated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(submission)
    
    return DocumentSubmissionResponse.from_orm(submission)


@router.get("/debug/test")
async def debug_test():
    """Debug endpoint to test if server is picking up changes"""
    return {"debug": "server_updated", "timestamp": "2025-06-14T17:00:00Z"}


@router.put("/test-cases/{test_case_id}", response_model=TestCaseWithDetails)
async def update_test_case(
    test_case_id: str,
    update_data: TestCaseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update test case status and other fields"""
    from app.models.request_info import TestCase
    from sqlalchemy.orm import selectinload
    from sqlalchemy import select
    from datetime import datetime
    
    try:
        # Get the test case with relationships
        query = select(TestCase).options(
            selectinload(TestCase.data_owner),
            selectinload(TestCase.assigned_by_user),
            selectinload(TestCase.document_submissions),
            selectinload(TestCase.cycle),
            selectinload(TestCase.report)
        ).where(TestCase.test_case_id == test_case_id)
        
        result = await db.execute(query)
        test_case = result.scalar_one_or_none()
        
        if not test_case:
            raise HTTPException(status_code=404, detail="Test case not found")
        
        # Check authorization - only data provider assigned to this test case can update it
        if (current_user.role not in ["TESTER", "ADMIN"] and 
            test_case.data_provider_id != current_user.user_id):
            raise HTTPException(status_code=403, detail="Not authorized to update this test case")
        
        # Update fields
        if update_data.status is not None:
            test_case.status = update_data.status
            if update_data.status == "Submitted":
                test_case.submitted_at = datetime.utcnow()
        
        if update_data.expected_evidence_type is not None:
            test_case.expected_evidence_type = update_data.expected_evidence_type
            
        if update_data.special_instructions is not None:
            test_case.special_instructions = update_data.special_instructions
            
        if update_data.submission_deadline is not None:
            test_case.submission_deadline = update_data.submission_deadline
        
        test_case.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(test_case)
        
        # Build response in same format as get_my_test_cases
        data_provider_name = None
        data_provider_email = None
        assigned_by_name = None
        
        if test_case.data_provider:
            data_provider_name = f"{test_case.data_provider.first_name} {test_case.data_provider.last_name}"
            data_provider_email = test_case.data_provider.email
            
        if test_case.assigned_by_user:
            assigned_by_name = f"{test_case.assigned_by_user.first_name} {test_case.assigned_by_user.last_name}"
        
        # Count documents
        doc_count = len(test_case.document_submissions) if test_case.document_submissions else 0
        
        # Get cycle and report names
        cycle_name = test_case.cycle.cycle_name if test_case.cycle else f"Cycle {test_case.cycle_id}"
        report_name = test_case.report.report_name if test_case.report else f"Report {test_case.report_id}"
        
        return {
            "test_case_id": test_case.test_case_id,
            "phase_id": test_case.phase_id,
            "cycle_id": test_case.cycle_id,
            "cycle_name": cycle_name,
            "report_id": test_case.report_id,
            "report_name": report_name,
            "attribute_id": test_case.attribute_id,
            "sample_id": test_case.sample_id,
            "data_provider_id": test_case.data_provider_id,
            "assigned_by": test_case.assigned_by,
            "assigned_at": test_case.assigned_at.isoformat() if test_case.assigned_at else None,
            "attribute_name": test_case.attribute_name,
            "sample_identifier": test_case.sample_identifier,
            "primary_key_attributes": test_case.primary_key_attributes,
            "expected_evidence_type": test_case.expected_evidence_type,
            "special_instructions": test_case.special_instructions,
            "submission_deadline": test_case.submission_deadline.isoformat() if test_case.submission_deadline else None,
            "status": test_case.status,
            "submitted_at": test_case.submitted_at.isoformat() if test_case.submitted_at else None,
            "acknowledged_at": test_case.acknowledged_at.isoformat() if test_case.acknowledged_at else None,
            "created_at": test_case.created_at.isoformat(),
            "updated_at": test_case.updated_at.isoformat(),
            "data_provider_name": data_provider_name,
            "data_provider_email": data_provider_email,
            "assigned_by_name": assigned_by_name,
            "document_count": doc_count,
            "has_submissions": doc_count > 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[Update Test Case] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to update test case: {str(e)}") 