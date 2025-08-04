"""
RFI Test Case Management API endpoints
Handles test case queries for Data Owners
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, text, update, or_
from datetime import datetime
import logging

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.workflow import WorkflowPhase
from app.models.cycle_report_data_source import CycleReportDataSource
from app.models.universal_assignment import UniversalAssignment
from app.models.request_info import CycleReportTestCase
from app.models.sample_selection import SampleSelectionSample
from app.schemas.rfi import (
    RFITestCaseResponse,
    TestCaseStatus,
    TestCasePriority,
    QueryValidationRequest,
    QueryValidationResponse
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/assignments/{assignment_id}/test-cases", response_model=List[RFITestCaseResponse])
async def get_assignment_test_cases(
    assignment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all test cases for a Data Owner assignment"""
    try:
        # Verify the assignment exists and belongs to the current user
        assignment = await db.execute(
            select(UniversalAssignment).where(
                and_(
                    UniversalAssignment.assignment_id == assignment_id,
                    UniversalAssignment.to_user_id == current_user.user_id,
                    UniversalAssignment.assignment_type == 'LOB Assignment',
                    UniversalAssignment.to_role == 'Data Owner'
                )
            )
        )
        assignment = assignment.scalar_one_or_none()
        
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found or not authorized"
            )
        
        # Get assignment context
        context_data = assignment.context_data or {}
        attribute_name = context_data.get('attribute_name')
        cycle_id = context_data.get('cycle_id')
        report_id = context_data.get('report_id')
        lob_name = context_data.get('lob_name')
        
        # Get RFI phase
        phase_query = await db.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == 'Request Info'
                )
            )
        )
        phase = phase_query.scalar_one_or_none()
        
        if not phase:
            return []
        
        # Get test cases for this attribute and LOB
        # First, get sample IDs for this LOB from sample selection
        samples_query = await db.execute(
            select(SampleSelectionSample).where(
                and_(
                    SampleSelectionSample.lob_id == context_data.get('lob_id'),
                    SampleSelectionSample.tester_decision == 'approved'
                )
            )
        )
        samples = samples_query.scalars().all()
        sample_ids = [str(s.sample_id) for s in samples]
        
        # Get test cases for these samples and attribute
        test_cases_query = await db.execute(
            select(CycleReportTestCase).where(
                and_(
                    CycleReportTestCase.phase_id == phase.phase_id,
                    CycleReportTestCase.attribute_name == attribute_name,
                    or_(
                        CycleReportTestCase.sample_id.in_([str(sid) for sid in sample_ids]),
                        CycleReportTestCase.lob_id == context_data.get('lob_id')
                    )
                )
            ).order_by(CycleReportTestCase.test_case_number)
        )
        test_cases = test_cases_query.scalars().all()
        
        # Convert to response format
        result = []
        for tc in test_cases:
            # Get sample identifier
            sample_identifier = None
            for sample in samples:
                if str(sample.sample_id) == tc.sample_id:
                    sample_identifier = sample.sample_identifier
                    break
            
            result.append(RFITestCaseResponse(
                id=str(tc.id),
                test_case_number=tc.test_case_number,
                sample_id=tc.sample_id,
                sample_identifier=sample_identifier or tc.sample_id,
                attribute_name=tc.attribute_name,
                status=TestCaseStatus(tc.status) if tc.status else TestCaseStatus.NOT_STARTED,
                priority=TestCasePriority.MEDIUM,  # Default priority
                query_text=tc.query_text,
                expected_value=None,  # To be populated from sample data
                actual_value=None,  # To be populated after query execution
                test_result=None
            ))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting test cases: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get test cases: {str(e)}"
        )


@router.put("/test-cases/{test_case_id}/query", response_model=Dict[str, Any])
async def update_test_case_query(
    test_case_id: str,
    query_text: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update query for a specific test case"""
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
        
        # TODO: Add authorization check to ensure user has access to this test case
        
        # Update query
        test_case.query_text = query_text
        test_case.updated_at = datetime.utcnow()
        
        await db.commit()
        
        return {
            "success": True,
            "test_case_id": test_case_id,
            "message": "Query updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating test case query: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update test case query: {str(e)}"
        )


@router.post("/test-cases/{test_case_id}/validate-query", response_model=QueryValidationResponse)
async def validate_test_case_query(
    test_case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Validate the query for a specific test case using its associated data source"""
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
        
        if not test_case.query_text:
            return QueryValidationResponse(
                is_valid=False,
                error="No query defined for this test case",
                columns=[],
                sample_data=None
            )
        
        # Get the assignment for this test case to find data source
        # This is a simplified approach - in production, you'd have a more direct link
        phase_result = await db.execute(
            select(WorkflowPhase).where(
                WorkflowPhase.phase_id == test_case.phase_id
            )
        )
        phase = phase_result.scalar_one_or_none()
        
        if not phase:
            return QueryValidationResponse(
                is_valid=False,
                error="Phase not found",
                columns=[],
                sample_data=None
            )
        
        # Get assignment for current user
        assignment_result = await db.execute(
            select(UniversalAssignment).where(
                and_(
                    UniversalAssignment.to_user_id == current_user.user_id,
                    UniversalAssignment.assignment_type == 'LOB Assignment',
                    UniversalAssignment.context_data['cycle_id'].astext == str(phase.cycle_id),
                    UniversalAssignment.context_data['report_id'].astext == str(phase.report_id),
                    UniversalAssignment.context_data['attribute_name'].astext == test_case.attribute_name
                )
            )
        )
        assignment = assignment_result.scalar_one_or_none()
        
        if not assignment:
            return QueryValidationResponse(
                is_valid=False,
                error="No assignment found for this test case",
                columns=[],
                sample_data=None
            )
        
        # Get data source from assignment
        data_source_id = assignment.context_data.get('data_source_id')
        if not data_source_id:
            return QueryValidationResponse(
                is_valid=False,
                error="No data source configured for this assignment",
                columns=[],
                sample_data=None
            )
        
        # Get data source
        data_source = await db.execute(
            select(CycleReportDataSource).where(
                CycleReportDataSource.id == data_source_id
            )
        )
        data_source = data_source.scalar_one_or_none()
        
        if not data_source:
            return QueryValidationResponse(
                is_valid=False,
                error="Data source not found",
                columns=[],
                sample_data=None
            )
        
        # Get sample data for parameter substitution
        sample_result = await db.execute(
            select(SampleSelectionSample).where(
                SampleSelectionSample.sample_id == test_case.sample_id
            )
        )
        sample = sample_result.scalar_one_or_none()
        
        # Replace placeholders in query
        query = test_case.query_text
        if sample:
            query = query.replace(':sample_identifier', f"'{sample.sample_identifier}'")
        
        # Validate query
        source_type_str = str(data_source.source_type)
        if hasattr(data_source.source_type, 'value'):
            source_type_str = data_source.source_type.value
        
        if source_type_str.upper() == "POSTGRESQL":
            try:
                # Execute query with LIMIT 1 to test
                test_query = f"SELECT * FROM ({query}) AS test_query LIMIT 1"
                result = await db.execute(text(test_query))
                row = result.first()
                
                # Get column names
                columns = list(result.keys())
                
                # Get sample data if available
                sample_data = None
                if row:
                    sample_data = dict(row._mapping)
                    # Convert any non-serializable values
                    for key, value in sample_data.items():
                        if isinstance(value, datetime):
                            sample_data[key] = value.isoformat()
                
                return QueryValidationResponse(
                    is_valid=True,
                    error=None,
                    columns=columns,
                    sample_data=sample_data
                )
                
            except Exception as e:
                return QueryValidationResponse(
                    is_valid=False,
                    error=f"Query execution failed: {str(e)}",
                    columns=[],
                    sample_data=None
                )
        else:
            return QueryValidationResponse(
                is_valid=False,
                error=f"Validation not implemented for {source_type_str}",
                columns=[],
                sample_data=None
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating test case query: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate test case query: {str(e)}"
        )


@router.post("/test-cases/{test_case_id}/execute-query", response_model=Dict[str, Any])
async def execute_test_case_query(
    test_case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Execute the query for a test case and store the result"""
    try:
        # Similar to validate but actually stores the result
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
        
        # Execute validation first
        validation_response = await validate_test_case_query(test_case_id, db, current_user)
        
        if not validation_response.is_valid:
            return {
                "success": False,
                "error": validation_response.error,
                "test_case_id": test_case_id
            }
        
        # Store the result (simplified - in production you'd store more details)
        if validation_response.sample_data:
            # Get the expected attribute value
            attribute_column = test_case.attribute_name.lower().replace(' ', '_')
            actual_value = validation_response.sample_data.get(attribute_column)
            
            # Update test case with result
            test_case.status = "In Progress"
            test_case.updated_at = datetime.utcnow()
            
            await db.commit()
            
            return {
                "success": True,
                "test_case_id": test_case_id,
                "columns": validation_response.columns,
                "data": validation_response.sample_data,
                "actual_value": actual_value
            }
        else:
            return {
                "success": False,
                "error": "No data returned from query",
                "test_case_id": test_case_id
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing test case query: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute test case query: {str(e)}"
        )