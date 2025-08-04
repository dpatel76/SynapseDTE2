"""
Unified Test Execution API Endpoints
Handles test execution management with evidence integration and tester approval workflow
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Body, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, and_, or_, func, desc

from app.core.database import get_db
from app.core.auth import get_current_user
from app.core.exceptions import ValidationError, ResourceNotFoundError, BusinessLogicError
from app.models.user import User
from app.models.test_execution import TestExecution, TestExecutionReview, TestExecutionAudit
from app.schemas.test_execution_unified import (
    TestExecutionCreateRequest, TestExecutionUpdateRequest, TestExecutionReviewRequest,
    BulkTestExecutionRequest, BulkReviewRequest, TestExecutionResponse, TestExecutionReviewResponse,
    TestExecutionAuditResponse, TestExecutionListResponse, TestExecutionReviewListResponse,
    TestExecutionDashboardResponse, TestExecutionCompletionStatusResponse,
    BulkTestExecutionResponse, BulkReviewResponse, TestExecutionConfigurationResponse,
    TestType, AnalysisMethod, ExecutionReason, ExecutionMethod
)
from app.services.test_execution_service import TestExecutionService
from app.services.llm_service import HybridLLMService
from app.services.database_connection_service import DatabaseConnectionService
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


def get_test_execution_service(
    db: AsyncSession = Depends(get_db),
    llm_service: HybridLLMService = Depends(),
    db_service: DatabaseConnectionService = Depends()
) -> TestExecutionService:
    """Get test execution service instance"""
    return TestExecutionService(db, llm_service, db_service)


@router.post("/{cycle_id}/reports/{report_id}/execute", response_model=BulkTestExecutionResponse)
async def execute_test_cases_for_report(
    cycle_id: int = Path(..., description="Cycle ID"),
    report_id: int = Path(..., description="Report ID"),
    request: BulkTestExecutionRequest = Body(..., description="Bulk execution request"),
    current_user: User = Depends(get_current_user),
    service: TestExecutionService = Depends(get_test_execution_service)
):
    """
    Execute multiple test cases for a report
    Start test execution for all approved test cases
    """
    logger.info(f"Bulk execution request: cycle_id={cycle_id}, report_id={report_id}, request={request.dict()}")
    
    try:
        # Get phase ID for test execution
        phase_id = await service._get_phase_id_for_cycle_report(cycle_id, report_id, "Testing")
        logger.info(f"Found phase_id: {phase_id} for Testing phase")
        
        execution_results = []
        errors = []
        
        for test_case_id in request.test_case_ids:
            try:
                # Get approved evidence for test case
                try:
                    # First, check if test_case_id is empty or invalid
                    if not test_case_id or test_case_id == "":
                        errors.append({
                            "test_case_id": test_case_id,
                            "error": "Empty or invalid test case ID"
                        })
                        continue
                        
                    evidence = await service._get_approved_evidence_for_test_case(test_case_id)
                    if not evidence:
                        errors.append({
                            "test_case_id": test_case_id,
                            "error": "No approved evidence found"
                        })
                        continue
                except Exception as e:
                    logger.error(f"Error getting evidence for test case {test_case_id}: {str(e)}")
                    errors.append({
                        "test_case_id": test_case_id,
                        "error": f"Failed to get evidence: {str(e)}"
                    })
                    continue
                
                # Determine test type and analysis method based on evidence
                evidence_type = evidence.get("evidence_type", "document")
                if evidence_type == "data_source":
                    test_type = "database_test"
                    analysis_method = "database_query"
                else:
                    test_type = "document_analysis"
                    analysis_method = "llm_analysis"
                
                # Create execution request
                execution_request = TestExecutionCreateRequest(
                    test_case_id=test_case_id,
                    evidence_id=evidence["id"],
                    execution_reason=request.execution_reason,
                    test_type=test_type,
                    analysis_method=analysis_method,
                    execution_method=request.execution_method,
                    configuration=request.configuration
                )
                
                # Create execution
                logger.info(f"Creating execution for test case {test_case_id} with evidence {evidence['id']}")
                execution = await service.create_test_execution(
                    execution_request,
                    phase_id,
                    cycle_id,
                    report_id,
                    current_user.user_id,
                    current_user.user_id
                )
                logger.info(f"Successfully created execution {execution.id} for test case {test_case_id}")
                
                execution_results.append(execution.id)
                
            except Exception as e:
                errors.append({
                    "test_case_id": test_case_id,
                    "error": str(e)
                })
        
        return BulkTestExecutionResponse(
            total_requested=len(request.test_case_ids),
            successful_executions=len(execution_results),
            failed_executions=len(errors),
            execution_ids=execution_results,
            errors=errors,
            job_id=None  # Not using background processing for now
        )
        
    except Exception as e:
        import traceback
        logger.error(f"Error executing test cases for report: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to execute test cases: {str(e)}")


@router.post("/test-cases/{test_case_id}/execute", response_model=TestExecutionResponse)
async def execute_specific_test_case(
    test_case_id: str = Path(..., description="Test case ID"),
    request: TestExecutionCreateRequest = Body(..., description="Test execution request"),
    current_user: User = Depends(get_current_user),
    service: TestExecutionService = Depends(get_test_execution_service)
):
    """
    Execute specific test case with approved evidence
    """
    try:
        # Get phase information from test case
        phase_info = await service._get_phase_info_for_test_case(test_case_id)
        
        execution = await service.create_test_execution(
            request,
            phase_info["phase_id"],
            phase_info["cycle_id"],
            phase_info["report_id"],
            current_user.user_id,
            current_user.user_id
        )
        
        return execution
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        import traceback
        logger.error(f"Error executing test case: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to execute test case: {str(e)}")


@router.get("/test-cases/{test_case_id}/results")
async def get_latest_test_execution_results(
    test_case_id: str = Path(..., description="Test case ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get latest execution results for test case
    """
    try:
        result = await db.execute(
            select(TestExecution)
            .options(
                selectinload(TestExecution.phase),
                selectinload(TestExecution.executor)
            )
            .where(TestExecution.test_case_id == test_case_id)
            .where(TestExecution.is_latest_execution == True)
        )
        
        execution = result.scalar_one_or_none()
        if not execution:
            raise HTTPException(status_code=404, detail="No execution found for test case")
        
        # Build response manually to avoid greenlet issues
        return {
            "id": execution.id,
            "test_case_id": execution.test_case_id,
            "phase_id": execution.phase_id,
            "evidence_id": execution.evidence_id,
            "execution_number": execution.execution_number,
            "is_latest_execution": execution.is_latest_execution,
            "execution_reason": execution.execution_reason,
            "analysis_method": execution.analysis_method,
            "execution_status": execution.execution_status,
            "test_result": execution.test_result,
            "sample_value": execution.sample_value,
            "extracted_value": execution.extracted_value,
            "expected_value": execution.expected_value,
            "analysis_results": execution.analysis_results,
            "created_at": execution.created_at,
            "updated_at": execution.updated_at
        }
        
    except Exception as e:
        logger.error(f"Error getting test execution results: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get results: {str(e)}")


@router.get("/test-cases/{test_case_id}/executions", response_model=TestExecutionListResponse)
async def get_test_case_execution_history(
    test_case_id: str = Path(..., description="Test case ID"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all executions for test case (history)
    """
    try:
        # Get total count
        count_result = await db.execute(
            select(func.count(TestExecution.id))
            .where(TestExecution.test_case_id == test_case_id)
        )
        total = count_result.scalar_one()
        
        # Get executions
        result = await db.execute(
            select(TestExecution)
            .where(TestExecution.test_case_id == test_case_id)
            .order_by(desc(TestExecution.execution_number))
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        
        executions = result.scalars().all()
        
        return TestExecutionListResponse(
            executions=[TestExecutionResponse.from_orm(exe) for exe in executions],
            total=total,
            page=page,
            per_page=per_page,
            total_pages=(total + per_page - 1) // per_page
        )
        
    except Exception as e:
        logger.error(f"Error getting test case execution history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get execution history: {str(e)}")


@router.get("/{cycle_id}/reports/{report_id}/submitted-test-cases")
async def get_submitted_test_cases(
    cycle_id: int = Path(..., description="Cycle ID"),
    report_id: int = Path(..., description="Report ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get submitted test cases from Request Info phase for testing execution
    """
    try:
        from sqlalchemy import select, and_
        from sqlalchemy.orm import selectinload
        from app.models.request_info import CycleReportTestCase as TestCase
        
        # Get submitted test cases - need to join with WorkflowPhase to filter by cycle_id and report_id
        from app.models.workflow import WorkflowPhase
        
        query = select(TestCase).options(
            selectinload(TestCase.data_owner),
            selectinload(TestCase.evidence_submissions),
            selectinload(TestCase.sample),
            selectinload(TestCase.attribute)
        ).join(
            WorkflowPhase, TestCase.phase_id == WorkflowPhase.phase_id
        ).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                TestCase.status.in_(['Pending Approval', 'Complete'])  # Use correct status values
            )
        )
        
        result = await db.execute(query)
        test_cases = result.scalars().all()
        
        # Format response to match frontend expectations
        formatted_test_cases = []
        for tc in test_cases:
            # Extract primary key values from sample data if available
            primary_key_values = {}
            sample_value = None
            
            if tc.sample and tc.sample.sample_data:
                # The sample_data JSONB field contains the full record including PK values
                sample_data = tc.sample.sample_data
                
                # Get the attribute value from sample data
                if tc.attribute and tc.attribute.attribute_name:
                    sample_value = sample_data.get(tc.attribute.attribute_name)
                
                # Extract primary key columns - all fields that are not the attribute being tested
                # and are likely to be identifiers (ending with _id, _number, _code, etc.)
                for key, value in sample_data.items():
                    # Skip the attribute being tested
                    if key == tc.attribute.attribute_name:
                        continue
                    
                    # Include fields that look like primary keys
                    if (key.endswith('_id') or 
                        key.endswith('_number') or 
                        key.endswith('_code') or 
                        key.endswith('_key') or
                        key in ['id', 'customer_id', 'account_id', 'transaction_id', 
                               'order_id', 'product_id', 'loan_id', 'policy_id',
                               'claim_id', 'invoice_id', 'payment_id', 'reference_id']):
                        primary_key_values[key] = value
            
            formatted_test_cases.append({
                "id": tc.id,
                "test_case_id": tc.id,  # Use id as test_case_id
                "test_name": tc.test_case_name,
                "sample_id": tc.sample_id,
                "sample_identifier": tc.sample.sample_identifier if tc.sample else tc.sample_id,
                "attribute_id": tc.attribute_id,
                "attribute_name": tc.attribute_name,  # Direct field, not relationship
                "data_owner_id": tc.data_owner_id,
                "data_owner_name": f"{tc.data_owner.first_name} {tc.data_owner.last_name}" if tc.data_owner else None,
                "status": tc.status,
                "has_evidence": len(tc.evidence_submissions) > 0,
                "evidence_count": len(tc.evidence_submissions),
                "document_count": len(tc.evidence_submissions),
                "created_at": tc.created_at.isoformat() if hasattr(tc, 'created_at') and tc.created_at else None,
                "updated_at": tc.updated_at.isoformat() if hasattr(tc, 'updated_at') and tc.updated_at else None,
                # Add missing fields
                "primary_key_values": primary_key_values,
                "sample_value": sample_value,
                "expected_value": sample_value,  # In test execution, expected value is the sample value
                "is_scoped": tc.attribute.is_scoped if tc.attribute else True,
                "data_type": tc.attribute.data_type if tc.attribute else None,
                "special_instructions": tc.special_instructions,
                # Include evidence submissions with basic info for test execution
                "evidence_submissions": [
                    {
                        "id": str(ev.id),
                        "evidence_id": ev.id,
                        "evidence_type": ev.evidence_type,
                        "is_current": ev.is_current,
                        "validation_status": ev.validation_status.value if hasattr(ev.validation_status, 'value') else ev.validation_status
                    }
                    for ev in tc.evidence_submissions
                    if ev.is_current  # Only include current evidence
                ]
            })
        
        return {
            "test_cases": formatted_test_cases,
            "total": len(test_cases)
        }
        
    except Exception as e:
        logger.error(f"Error getting submitted test cases: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get submitted test cases: {str(e)}")


@router.get("/{cycle_id}/reports/{report_id}/executions")
async def get_test_executions(
    cycle_id: int = Path(..., description="Cycle ID"),
    report_id: int = Path(..., description="Report ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get test execution results for a specific report
    """
    try:
        from sqlalchemy import select, and_
        from sqlalchemy.orm import selectinload
        from app.models.request_info import CycleReportTestCase as TestCase
        from app.models.report_attribute import ReportAttribute as Attribute
        
        # Get test executions from unified model - need to join with WorkflowPhase
        from app.models.workflow import WorkflowPhase
        
        query = select(TestExecution).options(
            selectinload(TestExecution.executor),
            selectinload(TestExecution.phase)
        ).join(
            WorkflowPhase, TestExecution.phase_id == WorkflowPhase.phase_id
        ).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                TestExecution.is_latest_execution == True
            )
        )
        
        result = await db.execute(query)
        executions = result.scalars().all()
        
        # Format execution results to match legacy format expected by frontend
        execution_results = []
        for exec in executions:
            # Get test case to find attribute info
            try:
                test_case_id_int = int(exec.test_case_id)
                test_case_result = await db.execute(
                    select(TestCase).where(TestCase.id == test_case_id_int)
                )
                test_case = test_case_result.scalar_one_or_none()
            except (ValueError, TypeError):
                test_case = None
            
            exec_data = {
                "execution_id": exec.id,
                "sample_record_id": test_case.sample_id if test_case else None,
                "sample_id": test_case.sample_id if test_case else None,  # Frontend expects sample_id
                "attribute_id": test_case.attribute_id if test_case else None,
                "attribute_name": test_case.attribute_name if test_case else f"Attribute {test_case.attribute_id if test_case else 'Unknown'}",
                "status": exec.execution_status.capitalize() if exec.execution_status else "Pending",
                "result": exec.test_result.capitalize() if exec.test_result else "Pending",
                "test_case_id": exec.test_case_id,
                "evidence_files": [],  # TODO: Add actual evidence files when available
                "notes": exec.execution_summary or "",
                "retrieved_value": exec.extracted_value or exec.execution_summary or "",
                "confidence_score": exec.llm_confidence_score,
                "started_at": exec.started_at.isoformat() if exec.started_at else None,
                "completed_at": exec.completed_at.isoformat() if exec.completed_at else None,
                "processing_time_ms": exec.processing_time_ms,
                "error_message": exec.error_message,
                # Add the full analysis_results which contains primary key values
                "analysis_results": exec.analysis_results or {},
                "extracted_value": exec.extracted_value,
                "expected_value": exec.expected_value,
                "sample_value": exec.sample_value,
                "test_result": exec.test_result,
                "execution_status": exec.execution_status,
                "llm_analysis_rationale": exec.llm_analysis_rationale,
                "database_result_sample": exec.database_result_sample,
            }
            execution_results.append(exec_data)
        
        return execution_results
        
    except Exception as e:
        logger.error(f"Error fetching test executions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch test executions: {str(e)}"
        )


@router.get("/{cycle_id}/reports/{report_id}/pending-review", response_model=TestExecutionListResponse)
async def get_executions_pending_review(
    cycle_id: int = Path(..., description="Cycle ID"),
    report_id: int = Path(..., description="Report ID"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get executions pending tester review
    """
    try:
        # Get total count of pending reviews
        from app.models.workflow import WorkflowPhase
        
        count_result = await db.execute(
            select(func.count(TestExecution.id))
            .join(
                WorkflowPhase, TestExecution.phase_id == WorkflowPhase.phase_id
            )
            .where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    TestExecution.execution_status == "completed",
                    TestExecution.is_latest_execution == True
                )
            )
            .where(
                ~TestExecution.id.in_(
                    select(TestExecutionReview.execution_id)
                    .where(TestExecutionReview.review_status == "approved")
                )
            )
        )
        total = count_result.scalar_one()
        
        # Get pending executions
        result = await db.execute(
            select(TestExecution)
            .join(
                WorkflowPhase, TestExecution.phase_id == WorkflowPhase.phase_id
            )
            .where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    TestExecution.execution_status == "completed",
                    TestExecution.is_latest_execution == True
                )
            )
            .where(
                ~TestExecution.id.in_(
                    select(TestExecutionReview.execution_id)
                    .where(TestExecutionReview.review_status == "approved")
                )
            )
            .order_by(desc(TestExecution.completed_at))
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        
        executions = result.scalars().all()
        
        return TestExecutionListResponse(
            executions=[TestExecutionResponse.from_orm(exe) for exe in executions],
            total=total,
            page=page,
            per_page=per_page,
            total_pages=(total + per_page - 1) // per_page
        )
        
    except Exception as e:
        logger.error(f"Error getting pending reviews: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get pending reviews: {str(e)}")


@router.post("/executions/{execution_id}/review", response_model=TestExecutionReviewResponse)
async def submit_test_execution_review(
    execution_id: int = Path(..., description="Execution ID"),
    request: TestExecutionReviewRequest = Body(..., description="Review request"),
    current_user: User = Depends(get_current_user),
    service: TestExecutionService = Depends(get_test_execution_service)
):
    """
    Submit tester review for execution
    """
    try:
        # Get phase ID for execution
        phase_id = await service._get_phase_id_for_execution(execution_id)
        
        review = await service.create_test_execution_review(
            execution_id,
            request,
            phase_id,
            current_user.user_id
        )
        
        return review
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Error submitting review: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to submit review: {str(e)}")


@router.get("/executions/{execution_id}/review", response_model=TestExecutionReviewResponse)
async def get_test_execution_review(
    execution_id: int = Path(..., description="Execution ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get review details for execution
    """
    try:
        result = await db.execute(
            select(TestExecutionReview)
            .where(TestExecutionReview.execution_id == execution_id)
            .order_by(desc(TestExecutionReview.reviewed_at))
            .limit(1)
        )
        
        review = result.scalar_one_or_none()
        if not review:
            raise HTTPException(status_code=404, detail="No review found for execution")
        
        return TestExecutionReviewResponse.from_orm(review)
        
    except Exception as e:
        logger.error(f"Error getting review: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get review: {str(e)}")


@router.get("/{cycle_id}/reports/{report_id}/completion-status", response_model=TestExecutionCompletionStatusResponse)
async def get_test_execution_completion_status(
    cycle_id: int = Path(..., description="Cycle ID"),
    report_id: int = Path(..., description="Report ID"),
    current_user: User = Depends(get_current_user),
    service: TestExecutionService = Depends(get_test_execution_service)
):
    """
    Check if phase can be completed (all test cases approved)
    """
    try:
        # Get phase ID for test execution
        phase_id = await service._get_phase_id_for_cycle_report(cycle_id, report_id, "Testing")
        
        status = await service.check_phase_completion(cycle_id, report_id, phase_id)
        return status
        
    except Exception as e:
        logger.error(f"Error checking completion status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to check completion: {str(e)}")


@router.post("/{cycle_id}/reports/{report_id}/complete")
async def complete_test_execution_phase(
    cycle_id: int = Path(..., description="Cycle ID"),
    report_id: int = Path(..., description="Report ID"),
    current_user: User = Depends(get_current_user),
    service: TestExecutionService = Depends(get_test_execution_service)
):
    """
    Mark phase as complete (requires all test cases approved)
    """
    try:
        # Check if phase can be completed
        phase_id = await service._get_phase_id_for_cycle_report(cycle_id, report_id, "Testing")
        completion_status = await service.check_phase_completion(cycle_id, report_id, phase_id)
        
        if not completion_status.can_complete:
            raise HTTPException(
                status_code=422,
                detail={
                    "message": "Phase cannot be completed",
                    "requirements": completion_status.completion_requirements,
                    "blocking_issues": completion_status.blocking_issues
                }
            )
        
        # Mark phase as complete
        await service._mark_phase_complete(cycle_id, report_id, phase_id, current_user.user_id)
        
        return {"message": "Test execution phase completed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing phase: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to complete phase: {str(e)}")


@router.get("/{cycle_id}/reports/{report_id}/status")
async def get_test_execution_status(
    cycle_id: int = Path(..., description="Cycle ID"),
    report_id: int = Path(..., description="Report ID"),
    current_user: User = Depends(get_current_user),
    service: TestExecutionService = Depends(get_test_execution_service),
    db: AsyncSession = Depends(get_db)
):
    """
    Get test execution phase status for frontend compatibility
    """
    try:
        # Get phase
        from app.models.workflow import WorkflowPhase
        from sqlalchemy import select, and_
        
        phase_query = await db.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Testing"
                )
            )
        )
        phase = phase_query.scalar_one_or_none()
        
        if not phase:
            raise HTTPException(status_code=404, detail="Test execution phase not found")
        
        # Get dashboard data
        dashboard = await service.get_test_execution_dashboard(cycle_id, report_id, phase.phase_id)
        
        # Format response for frontend
        return {
            "phase_id": phase.phase_id,
            "cycle_id": cycle_id,
            "report_id": report_id,
            "phase_name": "Test Execution",  # Frontend expects this name
            "status": phase.status,
            "total_test_cases": dashboard.summary.total_executions,
            "completed_test_cases": dashboard.summary.completed_executions,
            "pending_test_cases": dashboard.summary.pending_executions,
            "failed_test_cases": dashboard.summary.failed_executions,
            "approved_reviews": dashboard.summary.approved_reviews,
            "pending_reviews": dashboard.summary.pending_reviews,
            "completion_percentage": dashboard.summary.completion_percentage,
            "can_complete": dashboard.summary.approved_reviews == dashboard.summary.total_executions and dashboard.summary.total_executions > 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting test execution status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.get("/{cycle_id}/reports/{report_id}/dashboard", response_model=TestExecutionDashboardResponse)
async def get_test_execution_dashboard(
    cycle_id: int = Path(..., description="Cycle ID"),
    report_id: int = Path(..., description="Report ID"),
    current_user: User = Depends(get_current_user),
    service: TestExecutionService = Depends(get_test_execution_service)
):
    """
    Get test execution dashboard with summary statistics
    """
    try:
        # Get phase ID for test execution
        phase_id = await service._get_phase_id_for_cycle_report(cycle_id, report_id, "Testing")
        
        dashboard = await service.get_test_execution_dashboard(cycle_id, report_id, phase_id)
        return dashboard
        
    except Exception as e:
        logger.error(f"Error getting dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard: {str(e)}")


@router.post("/bulk-review", response_model=BulkReviewResponse)
async def bulk_review_test_executions(
    request: BulkReviewRequest = Body(..., description="Bulk review request"),
    current_user: User = Depends(get_current_user),
    service: TestExecutionService = Depends(get_test_execution_service)
):
    """
    Review multiple test executions at once
    """
    try:
        review_results = []
        errors = []
        
        for execution_id in request.execution_ids:
            try:
                # Get phase ID for execution
                phase_id = await service._get_phase_id_for_execution(execution_id)
                
                # Create review request
                review_request = TestExecutionReviewRequest(
                    review_status=request.review_status,
                    review_notes=request.review_notes,
                    reviewer_comments=request.reviewer_comments,
                    recommended_action=request.recommended_action
                )
                
                # Create review
                review = await service.create_test_execution_review(
                    execution_id,
                    review_request,
                    phase_id,
                    current_user.user_id
                )
                
                review_results.append(review.id)
                
            except Exception as e:
                errors.append({
                    "execution_id": execution_id,
                    "error": str(e)
                })
        
        return BulkReviewResponse(
            total_requested=len(request.execution_ids),
            successful_reviews=len(review_results),
            failed_reviews=len(errors),
            review_ids=review_results,
            errors=errors
        )
        
    except Exception as e:
        logger.error(f"Error in bulk review: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to perform bulk review: {str(e)}")


@router.get("/executions/{execution_id}/audit", response_model=List[TestExecutionAuditResponse])
async def get_test_execution_audit_log(
    execution_id: int = Path(..., description="Execution ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get audit log for test execution
    """
    try:
        result = await db.execute(
            select(TestExecutionAudit)
            .where(TestExecutionAudit.execution_id == execution_id)
            .order_by(desc(TestExecutionAudit.performed_at))
        )
        
        audit_logs = result.scalars().all()
        return [TestExecutionAuditResponse.from_orm(log) for log in audit_logs]
        
    except Exception as e:
        logger.error(f"Error getting audit log: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get audit log: {str(e)}")


@router.get("/configuration", response_model=TestExecutionConfigurationResponse)
async def get_test_execution_configuration(
    current_user: User = Depends(get_current_user)
):
    """
    Get test execution configuration options
    """
    try:
        return TestExecutionConfigurationResponse(
            available_test_types=["document_analysis", "database_test", "manual_test", "hybrid"],
            available_analysis_methods=["llm_analysis", "database_query", "manual_review"],
            available_execution_methods=["automatic", "manual", "scheduled"],
            default_configuration={
                "test_type": "document_analysis",
                "analysis_method": "llm_analysis",
                "execution_method": "automatic",
                "timeout_seconds": 300,
                "retry_count": 3
            },
            quality_criteria={
                "accuracy_weight": 0.4,
                "completeness_weight": 0.3,
                "consistency_weight": 0.3,
                "minimum_threshold": 0.8,
                "auto_approve_threshold": 0.95
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get configuration: {str(e)}")


@router.put("/executions/{execution_id}", response_model=TestExecutionResponse)
async def update_test_execution(
    execution_id: int = Path(..., description="Execution ID"),
    request: TestExecutionUpdateRequest = Body(..., description="Update request"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update test execution details
    """
    try:
        # Get execution
        result = await db.execute(
            select(TestExecution).where(TestExecution.id == execution_id)
        )
        execution = result.scalar_one_or_none()
        
        if not execution:
            raise HTTPException(status_code=404, detail="Execution not found")
        
        # Update fields
        if request.execution_summary is not None:
            execution.execution_summary = request.execution_summary
        if request.processing_notes is not None:
            execution.processing_notes = request.processing_notes
        if request.error_message is not None:
            execution.error_message = request.error_message
        if request.error_details is not None:
            execution.error_details = request.error_details
        
        execution.updated_by = current_user.user_id
        execution.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(execution)
        
        return TestExecutionResponse.from_orm(execution)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating execution: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update execution: {str(e)}")


@router.delete("/executions/{execution_id}")
async def delete_test_execution(
    execution_id: int = Path(..., description="Execution ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete test execution (soft delete by marking as cancelled)
    """
    try:
        # Get execution
        result = await db.execute(
            select(TestExecution).where(TestExecution.id == execution_id)
        )
        execution = result.scalar_one_or_none()
        
        if not execution:
            raise HTTPException(status_code=404, detail="Execution not found")
        
        # Mark as cancelled instead of hard delete
        execution.execution_status = "cancelled"
        execution.updated_by = current_user.user_id
        execution.updated_at = datetime.utcnow()
        
        await db.commit()
        
        return {"message": "Test execution cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting execution: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete execution: {str(e)}")


@router.post("/executions/{execution_id}/retry", response_model=TestExecutionResponse)
async def retry_test_execution(
    execution_id: int = Path(..., description="Execution ID"),
    current_user: User = Depends(get_current_user),
    service: TestExecutionService = Depends(get_test_execution_service)
):
    """
    Retry failed test execution
    """
    try:
        # Get original execution
        original_execution = await service._get_execution(execution_id)
        
        # Create retry request
        retry_request = TestExecutionCreateRequest(
            test_case_id=original_execution.test_case_id,
            evidence_id=original_execution.evidence_id,
            execution_reason="retry",
            test_type=original_execution.test_type,
            analysis_method=original_execution.analysis_method,
            execution_method=original_execution.execution_method,
            configuration=original_execution.analysis_results.get("configuration", {}),
            processing_notes=f"Retry of execution {execution_id}"
        )
        
        # Create new execution
        new_execution = await service.create_test_execution(
            retry_request,
            original_execution.phase_id,
            original_execution.cycle_id,
            original_execution.report_id,
            current_user.user_id,
            current_user.user_id
        )
        
        return new_execution
        
    except Exception as e:
        logger.error(f"Error retrying execution: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retry execution: {str(e)}")