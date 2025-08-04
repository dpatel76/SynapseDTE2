"""
Clean Architecture Request for Information API endpoints
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status as http_status, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.permissions import require_permission
from app.models.user import User
from app.application.dtos.request_info import (
    RequestInfoPhaseStartDTO,
    TestCaseCreateDTO,
    TestCaseResponseDTO,
    TestCaseWithDetailsDTO,
    DocumentSubmissionCreateDTO,
    DocumentSubmissionResponseDTO,
    FileUploadResponseDTO,
    DataOwnerNotificationDTO,
    RequestInfoPhaseStatusDTO,
    DataOwnerPortalDataDTO,
    PhaseProgressSummaryDTO,
    DataOwnerAssignmentSummaryDTO,
    PhaseCompletionRequestDTO,
    ResendTestCaseRequestDTO,
    BulkTestCaseAssignmentDTO,
    TestCaseUpdateDTO,
    TestCaseStatusEnum,
    DocumentTypeEnum
)
from app.application.use_cases.request_info import (
    StartRequestInfoPhaseUseCase,
    CreateTestCaseUseCase,
    BulkCreateTestCasesUseCase,
    GetDataOwnerTestCasesUseCase,
    SubmitDocumentUseCase,
    ReuploadDocumentUseCase,
    GetRequestInfoPhaseStatusUseCase,
    CompleteRequestInfoPhaseUseCase,
    ResendTestCaseUseCase,
    GetPhaseProgressSummaryUseCase,
    GetDataOwnerAssignmentSummaryUseCase
)

router = APIRouter()


# Phase Management Endpoints
@router.post("/{cycle_id}/reports/{report_id}/start", response_model=RequestInfoPhaseStatusDTO)
@require_permission("request_info", "execute")
async def start_request_info_phase(
    cycle_id: int,
    report_id: int,
    start_data: RequestInfoPhaseStartDTO,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start request for information phase"""
    try:
        use_case = StartRequestInfoPhaseUseCase()
        status = await use_case.execute(
            cycle_id, report_id, start_data, current_user.user_id, db
        )
        return status
        
    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start request info phase: {str(e)}"
        )


@router.get("/{cycle_id}/reports/{report_id}/status", response_model=RequestInfoPhaseStatusDTO)
@require_permission("request_info", "read")
async def get_request_info_phase_status(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get request for information phase status"""
    try:
        use_case = GetRequestInfoPhaseStatusUseCase()
        return await use_case.execute(cycle_id, report_id, db)
        
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get phase status: {str(e)}"
        )


@router.post("/{cycle_id}/reports/{report_id}/complete")
@require_permission("request_info", "execute")
async def complete_request_info_phase(
    cycle_id: int,
    report_id: int,
    completion_data: PhaseCompletionRequestDTO,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Complete request for information phase"""
    try:
        use_case = CompleteRequestInfoPhaseUseCase()
        result = await use_case.execute(
            cycle_id, report_id, completion_data, current_user.user_id, db
        )
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete phase: {str(e)}"
        )


# Test Case Management Endpoints
@router.post("/{cycle_id}/reports/{report_id}/test-cases", response_model=TestCaseResponseDTO)
@require_permission("request_info", "create")
async def create_test_case(
    cycle_id: int,
    report_id: int,
    test_case_data: TestCaseCreateDTO,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a test case for data collection"""
    try:
        use_case = CreateTestCaseUseCase()
        test_case = await use_case.execute(
            cycle_id, report_id, test_case_data, current_user.user_id, db
        )
        return test_case
        
    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create test case: {str(e)}"
        )


@router.post("/{cycle_id}/reports/{report_id}/test-cases/bulk", response_model=List[TestCaseResponseDTO])
@require_permission("request_info", "create")
async def bulk_create_test_cases(
    cycle_id: int,
    report_id: int,
    bulk_data: BulkTestCaseAssignmentDTO,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Bulk create test cases"""
    try:
        use_case = BulkCreateTestCasesUseCase()
        test_cases = await use_case.execute(
            cycle_id, report_id, bulk_data, current_user.user_id, db
        )
        return test_cases
        
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk create test cases: {str(e)}"
        )


@router.post("/test-cases/{test_case_id}/resend", response_model=TestCaseResponseDTO)
@require_permission("request_info", "update")
async def resend_test_case(
    test_case_id: str,
    resend_data: ResendTestCaseRequestDTO,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Resend test case to data owner"""
    try:
        use_case = ResendTestCaseUseCase()
        test_case = await use_case.execute(
            test_case_id, resend_data, current_user.user_id, db
        )
        return test_case
        
    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resend test case: {str(e)}"
        )


# Data Owner Endpoints
@router.get("/data-owner/test-cases", response_model=DataOwnerPortalDataDTO)
@require_permission("request_info", "read")
async def get_data_owner_test_cases(
    status: Optional[TestCaseStatusEnum] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get test cases assigned to current data owner"""
    try:
        # Verify user is a data owner
        if current_user.role != 'Data Owner':
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="Data Owner role required"
            )
        
        use_case = GetDataOwnerTestCasesUseCase()
        portal_data = await use_case.execute(
            current_user.user_id, status, db
        )
        return portal_data
        
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get test cases: {str(e)}"
        )


@router.post("/test-cases/{test_case_id}/submit", response_model=FileUploadResponseDTO)
@require_permission("request_info", "upload")
async def submit_document(
    test_case_id: str,
    file: UploadFile = File(...),
    document_type: DocumentTypeEnum = Form(...),
    submission_notes: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit document for test case"""
    try:
        use_case = SubmitDocumentUseCase()
        upload_response = await use_case.execute(
            test_case_id, file, document_type, submission_notes,
            current_user.user_id, db
        )
        return upload_response
        
    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit document: {str(e)}"
        )


@router.post("/submissions/{submission_id}/reupload", response_model=FileUploadResponseDTO)
@require_permission("request_info", "upload")
async def reupload_document(
    submission_id: str,
    file: UploadFile = File(...),
    revision_notes: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reupload document (creates a new version)"""
    try:
        use_case = ReuploadDocumentUseCase()
        upload_response = await use_case.execute(
            submission_id, file, revision_notes,
            current_user.user_id, db
        )
        return upload_response
        
    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reupload document: {str(e)}"
        )


# Progress and Analytics Endpoints
@router.get("/{cycle_id}/reports/{report_id}/progress", response_model=PhaseProgressSummaryDTO)
@require_permission("request_info", "read")
async def get_phase_progress(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get phase progress summary"""
    try:
        use_case = GetPhaseProgressSummaryUseCase()
        return await use_case.execute(cycle_id, report_id, db)
        
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get progress: {str(e)}"
        )


@router.get("/{cycle_id}/reports/{report_id}/assignments", response_model=List[DataOwnerAssignmentSummaryDTO])
@require_permission("request_info", "read")
async def get_data_owner_assignments(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get data owner assignment summary"""
    try:
        use_case = GetDataOwnerAssignmentSummaryUseCase()
        return await use_case.execute(cycle_id, report_id, db)
        
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get assignments: {str(e)}"
        )


# Additional endpoints for backwards compatibility
@router.get("/{cycle_id}/reports/{report_id}/test-cases", response_model=List[TestCaseWithDetailsDTO])
@require_permission("request_info", "read")
async def list_test_cases(
    cycle_id: int,
    report_id: int,
    status: Optional[TestCaseStatusEnum] = None,
    data_owner_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List test cases for cycle/report with optional filters"""
    try:
        from sqlalchemy import select, and_
        from sqlalchemy.orm import selectinload
        from app.models import TestCase, User as UserModel, Report
        
        query = select(TestCase).where(
            and_(
                TestCase.cycle_id == cycle_id,
                TestCase.report_id == report_id
            )
        ).options(
            selectinload(TestCase.data_owner),
            selectinload(TestCase.report),
            selectinload(TestCase.document_submissions)
        )
        
        if status:
            query = query.where(TestCase.status == status)
        if data_owner_id:
            query = query.where(TestCase.data_owner_id == data_owner_id)
        
        query = query.order_by(TestCase.created_at.desc())
        
        result = await db.execute(query)
        test_cases = result.scalars().all()
        
        # Convert to DTOs with details
        test_case_dtos = []
        for tc in test_cases:
            submission_count = len([s for s in tc.document_submissions if s.is_current])
            latest_submission = max(
                (s.submitted_at for s in tc.document_submissions if s.is_current),
                default=None
            )
            
            test_case_dtos.append(TestCaseWithDetailsDTO(
                test_case_id=tc.test_case_id,
                phase_id=tc.phase_id,
                cycle_id=tc.cycle_id,
                report_id=tc.report_id,
                attribute_id=tc.attribute_id,
                sample_id=tc.sample_id,
                sample_identifier=tc.sample_identifier,
                data_owner_id=tc.data_owner_id,
                assigned_by=tc.assigned_by,
                assigned_at=tc.assigned_at,
                attribute_name=tc.attribute_name,
                primary_key_attributes=tc.primary_key_attributes,
                expected_evidence_type=tc.expected_evidence_type,
                special_instructions=tc.special_instructions,
                status=tc.status,
                submission_deadline=tc.submission_deadline,
                submitted_at=tc.submitted_at,
                acknowledged_at=tc.acknowledged_at,
                created_at=tc.created_at,
                updated_at=tc.updated_at,
                data_owner_name=tc.data_owner.full_name,
                data_owner_email=tc.data_owner.email,
                report_name=tc.report.report_name,
                submission_count=submission_count,
                latest_submission_at=latest_submission
            ))
        
        return test_case_dtos
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list test cases: {str(e)}"
        )


@router.get("/test-cases/{test_case_id}", response_model=TestCaseWithDetailsDTO)
@require_permission("request_info", "read")
async def get_test_case(
    test_case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get test case details"""
    try:
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from app.models import TestCase
        
        result = await db.execute(
            select(TestCase)
            .where(TestCase.test_case_id == test_case_id)
            .options(
                selectinload(TestCase.data_owner),
                selectinload(TestCase.report),
                selectinload(TestCase.document_submissions)
            )
        )
        tc = result.scalar_one_or_none()
        
        if not tc:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Test case {test_case_id} not found"
            )
        
        submission_count = len([s for s in tc.document_submissions if s.is_current])
        latest_submission = max(
            (s.submitted_at for s in tc.document_submissions if s.is_current),
            default=None
        )
        
        return TestCaseWithDetailsDTO(
            test_case_id=tc.test_case_id,
            phase_id=tc.phase_id,
            cycle_id=tc.cycle_id,
            report_id=tc.report_id,
            attribute_id=tc.attribute_id,
            sample_id=tc.sample_id,
            sample_identifier=tc.sample_identifier,
            data_owner_id=tc.data_owner_id,
            assigned_by=tc.assigned_by,
            assigned_at=tc.assigned_at,
            attribute_name=tc.attribute_name,
            primary_key_attributes=tc.primary_key_attributes,
            expected_evidence_type=tc.expected_evidence_type,
            special_instructions=tc.special_instructions,
            status=tc.status,
            submission_deadline=tc.submission_deadline,
            submitted_at=tc.submitted_at,
            acknowledged_at=tc.acknowledged_at,
            created_at=tc.created_at,
            updated_at=tc.updated_at,
            data_owner_name=tc.data_owner.full_name,
            data_owner_email=tc.data_owner.email,
            report_name=tc.report.report_name,
            submission_count=submission_count,
            latest_submission_at=latest_submission
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get test case: {str(e)}"
        )


@router.get("/test-cases/{test_case_id}/submissions", response_model=List[DocumentSubmissionResponseDTO])
@require_permission("request_info", "read")
async def get_test_case_submissions(
    test_case_id: str,
    include_all_revisions: bool = Query(False, description="Include all document revisions"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get document submissions for test case"""
    try:
        from sqlalchemy import select, and_
        from app.models import DocumentSubmission
        
        query = select(DocumentSubmission).where(
            DocumentSubmission.test_case_id == test_case_id
        )
        
        if not include_all_revisions:
            query = query.where(DocumentSubmission.is_current == True)
        
        query = query.order_by(
            DocumentSubmission.revision_number.desc(),
            DocumentSubmission.submitted_at.desc()
        )
        
        result = await db.execute(query)
        submissions = result.scalars().all()
        
        return [
            DocumentSubmissionResponseDTO(
                submission_id=sub.submission_id,
                test_case_id=sub.test_case_id,
                data_owner_id=sub.data_owner_id,
                original_filename=sub.original_filename,
                stored_filename=sub.stored_filename,
                file_path=sub.file_path,
                file_size_bytes=sub.file_size_bytes,
                document_type=sub.document_type,
                mime_type=sub.mime_type,
                submission_notes=sub.submission_notes,
                submitted_at=sub.submitted_at,
                revision_number=sub.revision_number,
                parent_submission_id=sub.parent_submission_id,
                is_current=sub.is_current,
                notes=sub.notes,
                is_valid=sub.is_valid,
                validation_notes=sub.validation_notes,
                validated_by=sub.validated_by,
                validated_at=sub.validated_at
            )
            for sub in submissions
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get submissions: {str(e)}"
        )


@router.get("/cycles/{cycle_id}/reports/{report_id}/test-cases")
@require_permission("request_info", "read")
async def get_cycle_report_test_cases(
    cycle_id: int,
    report_id: int,
    data_owner_id: Optional[int] = Query(None, description="Filter by data owner"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get test cases for a specific cycle and report"""
    try:
        from sqlalchemy import select, and_
        from sqlalchemy.orm import selectinload
        from app.models.request_info import TestCase
        
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
        
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get test cases: {str(e)}"
        )