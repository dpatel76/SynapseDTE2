"""Request Info Document Submission Endpoints"""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status as http_status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.core.database import get_db
from app.models.user import User
from app.api.v1.deps import get_current_user
from app.models.request_info import TestCaseEvidence, CycleReportTestCase
from app.core.permissions import require_permission

router = APIRouter()


@router.get("/test-cases/{test_case_id}/document-submissions", response_model=List[Dict[str, Any]])
@require_permission("request_info", "read")
async def get_test_case_document_submissions(
    test_case_id: str,
    include_all_versions: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get document submissions for a test case"""
    try:
        # Convert test_case_id to int
        test_case_id_int = int(test_case_id)
        
        # Verify test case exists and user has access
        test_case_result = await db.execute(
            select(CycleReportTestCase).where(CycleReportTestCase.id == test_case_id_int)
        )
        test_case = test_case_result.scalar_one_or_none()
        
        if not test_case:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Test case not found"
            )
        
        # Check if user is data owner or has permission
        if current_user.role == 'Data Owner' and test_case.data_owner_id != current_user.user_id:
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this test case"
            )
        
        # Build query for document submissions from unified evidence table
        query = select(TestCaseEvidence).where(
            and_(
                TestCaseEvidence.test_case_id == test_case_id_int,
                TestCaseEvidence.evidence_type == 'document'
            )
        )
        
        if not include_all_versions:
            query = query.where(TestCaseEvidence.is_current == True)
        
        query = query.order_by(TestCaseEvidence.submission_number.desc())
        
        result = await db.execute(query)
        submissions = result.scalars().all()
        
        # Format response
        submissions_data = []
        for submission in submissions:
            # Get submitter name
            from app.models.user import User
            submitter_result = await db.execute(
                select(User).where(User.user_id == submission.data_owner_id)
            )
            submitter = submitter_result.scalar_one_or_none()
            
            submissions_data.append({
                "submission_id": str(submission.id),  # Using evidence id
                "submission_number": submission.submission_number,
                "is_current": submission.is_current,
                "is_revision": submission.is_revision,
                "document_type": submission.document_type.value if submission.document_type else "Source Document",
                "original_filename": submission.original_filename,
                "file_size_bytes": submission.file_size_bytes,
                "mime_type": submission.mime_type,
                "submitted_at": submission.submitted_at.isoformat() if submission.submitted_at else None,
                "submission_notes": submission.submission_notes,
                "validation_status": submission.validation_status,
                "validation_notes": submission.validation_notes,
                "validated_at": submission.validated_at.isoformat() if submission.validated_at else None,
                "submitted_by_name": f"{submitter.first_name} {submitter.last_name}" if submitter else "Unknown",
                "submitted_by_email": submitter.email if submitter else None,
                "download_url": f"/api/v1/request-info/evidence/{submission.id}/download"  # Updated URL
            })
        
        return submissions_data
        
    except ValueError:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Invalid test case ID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document submissions: {str(e)}"
        )