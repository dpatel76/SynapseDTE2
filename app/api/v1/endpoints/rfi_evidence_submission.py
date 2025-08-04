"""
RFI Evidence Submission API endpoints
Handles evidence submission by Data Owners for test cases
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, text, update, insert
from datetime import datetime
import json
import logging
import uuid

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.workflow import WorkflowPhase
from app.models.request_info import TestCaseSourceEvidence, CycleReportTestCase
from app.models.universal_assignment import UniversalAssignment

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/test-cases/{test_case_id}/submit-evidence", response_model=Dict[str, Any])
async def submit_test_case_evidence(
    test_case_id: str,
    evidence_type: str = Form(..., description="Type of evidence: 'data_source' or 'document'"),
    query_text: Optional[str] = Form(None, description="SQL query for data source evidence"),
    query_result: Optional[str] = Form(None, description="Query execution result as JSON"),
    submission_notes: Optional[str] = Form(None, description="Notes about the submission"),
    document: Optional[UploadFile] = File(None, description="Document evidence file"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit evidence for a test case - either data source query or document"""
    try:
        # Get test case
        tc_id = int(test_case_id)
        test_case = await db.execute(
            select(CycleReportTestCase).where(
                CycleReportTestCase.id == tc_id
            )
        )
        test_case = test_case.scalar_one_or_none()
        
        if not test_case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Test case not found"
            )
        
        # Get phase
        phase = await db.execute(
            select(WorkflowPhase).where(
                WorkflowPhase.phase_id == test_case.phase_id
            )
        )
        phase = phase.scalar_one_or_none()
        
        if not phase:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phase not found"
            )
        
        # Check if user has access (simplified - should verify assignment)
        # In production, verify the user is assigned to this test case
        
        # Check if evidence already exists
        existing_evidence = await db.execute(
            select(TestCaseSourceEvidence).where(
                and_(
                    TestCaseSourceEvidence.test_case_id == tc_id,
                    TestCaseSourceEvidence.is_current == True
                )
            )
        )
        existing = existing_evidence.scalar_one_or_none()
        
        # If exists, mark as not current
        if existing:
            existing.is_current = False
            existing.replaced_by = None  # Will be updated after creating new one
        
        # Create new evidence record
        evidence_data = {
            "phase_id": test_case.phase_id,
            "test_case_id": tc_id,
            "sample_id": test_case.sample_id,
            "attribute_id": test_case.attribute_id,
            "evidence_type": evidence_type,
            "submitted_by": current_user.user_id,
            "submitted_at": datetime.utcnow(),
            "submission_notes": submission_notes,
            "validation_status": "pending",
            "version_number": (existing.version_number + 1) if existing else 1,
            "is_current": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "created_by": current_user.user_id,
            "updated_by": current_user.user_id
        }
        
        if evidence_type == "data_source":
            # Handle data source evidence
            if not query_text:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Query text is required for data source evidence"
                )
            
            evidence_data["query_text"] = query_text
            
            # Parse query result if provided
            if query_result:
                try:
                    result_json = json.loads(query_result)
                    evidence_data["query_result_sample"] = result_json
                except json.JSONDecodeError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid JSON format for query result"
                    )
            
            # Get data source ID from assignment
            assignment = await db.execute(
                select(UniversalAssignment).where(
                    and_(
                        UniversalAssignment.to_user_id == current_user.user_id,
                        UniversalAssignment.context_data['attribute_name'].astext == test_case.attribute_name
                    )
                ).order_by(UniversalAssignment.created_at.desc())
            )
            assignment = assignment.scalar_one_or_none()
            
            if assignment and assignment.context_data.get('data_source_id'):
                evidence_data["data_source_id"] = assignment.context_data['data_source_id']
        
        elif evidence_type == "document":
            # Handle document evidence
            if not document:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Document file is required for document evidence"
                )
            
            # In production, save the file and get its path
            evidence_data["document_name"] = document.filename
            evidence_data["document_path"] = f"/uploads/rfi/{phase.cycle_id}/{phase.report_id}/{uuid.uuid4()}_{document.filename}"
            evidence_data["document_size"] = 0  # Would be actual file size
            evidence_data["mime_type"] = document.content_type
            # evidence_data["document_hash"] = calculate_file_hash(document)
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid evidence type. Must be 'data_source' or 'document'"
            )
        
        # Insert new evidence
        insert_stmt = insert(TestCaseSourceEvidence).values(**evidence_data).returning(TestCaseSourceEvidence.id)
        result = await db.execute(insert_stmt)
        new_evidence_id = result.scalar_one()
        
        # Update previous evidence with replaced_by
        if existing:
            existing.replaced_by = new_evidence_id
        
        # Update test case status to Submitted when evidence is submitted
        test_case.status = "Submitted"
        test_case.updated_at = datetime.utcnow()
        
        await db.commit()
        
        return {
            "success": True,
            "evidence_id": new_evidence_id,
            "test_case_id": test_case_id,
            "evidence_type": evidence_type,
            "version": evidence_data["version_number"],
            "message": f"Evidence submitted successfully for {test_case.test_case_number}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting evidence: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit evidence: {str(e)}"
        )


@router.get("/test-cases/{test_case_id}/evidence", response_model=Optional[Dict[str, Any]])
async def get_test_case_evidence(
    test_case_id: str,
    version: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get evidence for a test case"""
    try:
        tc_id = int(test_case_id)
        
        # Build query
        query = select(TestCaseSourceEvidence).where(
            TestCaseSourceEvidence.test_case_id == tc_id
        )
        
        if version:
            query = query.where(TestCaseSourceEvidence.version_number == version)
        else:
            query = query.where(TestCaseSourceEvidence.is_current == True)
        
        evidence = await db.execute(query)
        evidence = evidence.scalar_one_or_none()
        
        if not evidence:
            return None
        
        return {
            "evidence_id": evidence.id,
            "test_case_id": evidence.test_case_id,
            "evidence_type": evidence.evidence_type,
            "version": evidence.version_number,
            "is_current": evidence.is_current,
            "submitted_by": evidence.submitted_by,
            "submitted_at": evidence.submitted_at.isoformat() if evidence.submitted_at else None,
            "validation_status": evidence.validation_status,
            "query_text": evidence.query_text,
            "query_result_sample": evidence.query_result_sample,
            "document_name": evidence.document_name,
            "document_path": evidence.document_path,
            "submission_notes": evidence.submission_notes
        }
        
    except Exception as e:
        logger.error(f"Error getting evidence: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get evidence: {str(e)}"
        )


@router.post("/test-cases/{test_case_id}/evidence/{evidence_id}/validate", response_model=Dict[str, Any])
async def validate_evidence(
    test_case_id: str,
    evidence_id: str,
    validation_status: str,
    validation_notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Validate submitted evidence (for testers)"""
    try:
        # Get evidence
        ev_id = int(evidence_id)
        evidence = await db.execute(
            select(TestCaseSourceEvidence).where(
                and_(
                    TestCaseSourceEvidence.id == ev_id,
                    TestCaseSourceEvidence.test_case_id == int(test_case_id)
                )
            )
        )
        evidence = evidence.scalar_one_or_none()
        
        if not evidence:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evidence not found"
            )
        
        # Update validation status
        evidence.validation_status = validation_status
        evidence.validation_notes = validation_notes
        evidence.validated_by = current_user.user_id
        evidence.validated_at = datetime.utcnow()
        evidence.updated_at = datetime.utcnow()
        
        await db.commit()
        
        return {
            "success": True,
            "evidence_id": evidence_id,
            "validation_status": validation_status,
            "message": f"Evidence validation updated to {validation_status}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating evidence: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate evidence: {str(e)}"
        )