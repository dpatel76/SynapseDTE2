"""
Universal Assignment API Endpoints
Handles all role-to-role interactions and task assignments
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import asyncio

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.core.auth import UserRoles
from app.core.logging import get_logger
from app.models.user import User
from app.services.universal_assignment_service import UniversalAssignmentService
from app.services.email_service import EmailService

logger = get_logger(__name__)
router = APIRouter()


# Pydantic schemas
class UniversalAssignmentCreate(BaseModel):
    assignment_type: str
    from_role: str
    to_role: str
    to_user_id: Optional[int] = None
    title: str
    description: str
    task_instructions: Optional[str] = None
    context_type: str
    context_data: Dict[str, Any]
    priority: str = "Medium"
    due_date: Optional[datetime] = None
    requires_approval: bool = False
    approval_role: Optional[str] = None
    assignment_metadata: Optional[Dict[str, Any]] = None


class UniversalAssignmentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    task_instructions: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[datetime] = None
    assignment_metadata: Optional[Dict[str, Any]] = None


class AssignmentAction(BaseModel):
    notes: Optional[str] = None
    completion_data: Optional[Dict[str, Any]] = None
    completion_attachments: Optional[List[Dict[str, Any]]] = None


class AssignmentDelegation(BaseModel):
    delegated_to_user_id: int
    delegation_reason: Optional[str] = None


class AssignmentEscalation(BaseModel):
    escalation_reason: str
    escalated_to_user_id: Optional[int] = None


class UserSummary(BaseModel):
    user_id: int
    first_name: str
    last_name: str
    email: str
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

class UniversalAssignmentResponse(BaseModel):
    assignment_id: str
    assignment_type: str
    from_role: str
    to_role: str
    from_user_id: int
    to_user_id: Optional[int]
    # Enhanced user details
    from_user: Optional[UserSummary]
    to_user: Optional[UserSummary]
    title: str
    description: str
    task_instructions: Optional[str]
    context_type: str
    context_data: Dict[str, Any]
    status: str
    priority: str
    assigned_at: datetime
    due_date: Optional[datetime]
    acknowledged_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    completion_notes: Optional[str]
    completion_data: Optional[Dict[str, Any]]
    requires_approval: bool
    approval_role: Optional[str]
    approved_by_user_id: Optional[int]
    approved_at: Optional[datetime]
    approval_notes: Optional[str]
    is_overdue: bool
    days_until_due: int
    is_active: bool
    is_completed: bool
    
    # Context information for display
    cycle_id: Optional[int] = None
    report_id: Optional[int] = None
    report_name: Optional[str] = None
    
    # Navigation
    action_url: Optional[str] = None
    
    class Config:
        from_attributes = True


class AssignmentMetrics(BaseModel):
    total_assignments: int
    pending_assignments: int
    acknowledged_assignments: int
    in_progress_assignments: int
    completed_assignments: int
    approved_assignments: int
    rejected_assignments: int
    escalated_assignments: int
    overdue_assignments: int
    completion_rate: float
    status_breakdown: Dict[str, int]


@router.post("/assignments", response_model=UniversalAssignmentResponse)
async def create_assignment(
    assignment_data: UniversalAssignmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new universal assignment"""
    
    try:
        email_service = EmailService()
        service = UniversalAssignmentService(db, email_service)
        
        assignment = await service.create_assignment(
            assignment_type=assignment_data.assignment_type,
            from_role=assignment_data.from_role,
            to_role=assignment_data.to_role,
            from_user_id=current_user.user_id,
            to_user_id=assignment_data.to_user_id,
            title=assignment_data.title,
            description=assignment_data.description,
            task_instructions=assignment_data.task_instructions,
            context_type=assignment_data.context_type,
            context_data=assignment_data.context_data,
            priority=assignment_data.priority,
            due_date=assignment_data.due_date,
            requires_approval=assignment_data.requires_approval,
            approval_role=assignment_data.approval_role,
            assignment_metadata=assignment_data.assignment_metadata
        )
        
        return await _format_assignment_response(assignment, db)
        
    except Exception as e:
        logger.error(f"Error creating assignment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create assignment: {str(e)}"
        )


@router.get("/assignments/metrics", response_model=AssignmentMetrics)
async def get_assignment_metrics(
    user_id: Optional[int] = Query(None),
    role: Optional[str] = Query(None),
    assignment_type: Optional[str] = Query(None),
    context_type: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get assignment metrics"""
    
    # If user_id not provided, default to current user unless admin
    if not user_id and current_user.role not in ["Admin", "Test Executive"]:
        user_id = current_user.user_id
    
    service = UniversalAssignmentService(db)
    
    try:
        metrics = await service.get_assignment_metrics(
            user_id=user_id,
            role=role,
            assignment_type=assignment_type,
            context_type=context_type,
            date_from=date_from,
            date_to=date_to
        )
        
        return AssignmentMetrics(**metrics)
        
    except Exception as e:
        logger.error(f"Error getting assignment metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get assignment metrics: {str(e)}"
        )


@router.get("/assignments/{assignment_id}", response_model=UniversalAssignmentResponse)
async def get_assignment(
    assignment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get assignment by ID"""
    
    service = UniversalAssignmentService(db)
    assignment = await service.get_assignment(assignment_id)
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    # Check if user has access to this assignment
    if (assignment.from_user_id != current_user.user_id and 
        assignment.to_user_id != current_user.user_id and
        assignment.delegated_to_user_id != current_user.user_id and
        current_user.role not in ["Admin", "Test Executive"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this assignment"
        )
    
    return await _format_assignment_response(assignment, db)


@router.get("/assignments", response_model=List[UniversalAssignmentResponse])
async def get_user_assignments(
    status_filter: Optional[str] = Query(None, description="Comma-separated status values"),
    assignment_type_filter: Optional[str] = Query(None),
    context_type_filter: Optional[str] = Query(None),
    role_filter: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get assignments for current user"""
    
    service = UniversalAssignmentService(db)
    
    status_list = None
    if status_filter:
        status_list = [s.strip() for s in status_filter.split(",")]
    
    # Handle comma-separated assignment types
    assignment_type_list = None
    if assignment_type_filter:
        assignment_type_list = [s.strip() for s in assignment_type_filter.split(",")]
    
    assignments = await service.get_assignments_for_user(
        user_id=current_user.user_id,
        status_filter=status_list,
        assignment_type_filter=assignment_type_list,
        context_type_filter=context_type_filter,
        role_filter=role_filter,
        limit=limit
    )
    
    logger.info(f"Found {len(assignments)} assignments to format")
    formatted_assignments = await asyncio.gather(
        *[_format_assignment_response(assignment, db) for assignment in assignments]
    )
    logger.info(f"Formatted {len(formatted_assignments)} assignments")
    return formatted_assignments


@router.get("/assignments/context/{context_type}", response_model=List[UniversalAssignmentResponse])
async def get_assignments_by_context(
    context_type: str,
    cycle_id: Optional[int] = Query(None),
    report_id: Optional[int] = Query(None),
    phase_name: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, description="Comma-separated status values"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get assignments by context (cycle, report, phase, etc.)"""
    
    service = UniversalAssignmentService(db)
    
    # Build context data
    context_data = {}
    if cycle_id:
        context_data["cycle_id"] = cycle_id
    if report_id:
        context_data["report_id"] = report_id
    if phase_name:
        context_data["phase_name"] = phase_name
    
    status_list = None
    if status_filter:
        status_list = [s.strip() for s in status_filter.split(",")]
    
    assignments = await service.get_assignments_by_context(
        context_type=context_type,
        context_data=context_data,
        status_filter=status_list
    )
    
    formatted_assignments = await asyncio.gather(
        *[_format_assignment_response(assignment, db) for assignment in assignments]
    )
    return formatted_assignments


@router.get("/context/{context_type}", response_model=List[UniversalAssignmentResponse])
async def get_assignments_by_context(
    context_type: str,
    cycle_id: int = Query(...),
    report_id: int = Query(...),
    phase_name: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
    assignment_type_filter: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get assignments by context type and filters"""
    
    service = UniversalAssignmentService(db)
    
    # Parse status filter
    status_list = None
    if status_filter:
        status_list = [s.strip() for s in status_filter.split(",")]
    
    try:
        # Build context data filter
        context_data = {
            "cycle_id": cycle_id,
            "report_id": report_id
        }
        
        if phase_name:
            context_data["phase_name"] = phase_name
        
        # Get assignments filtered by context
        assignments = await service.get_assignments_by_context(
            context_type=context_type,
            context_data=context_data,
            status_filter=status_list
        )
        
        # Filter by current user and assignment type if needed
        if assignments:
            # Filter by to_user_id
            assignments = [a for a in assignments if a.to_user_id == current_user.user_id]
            
            # Filter by assignment type if specified
            if assignment_type_filter:
                assignments = [a for a in assignments if a.assignment_type == assignment_type_filter]
        
        formatted_assignments = await asyncio.gather(
            *[_format_assignment_response(assignment, db) for assignment in assignments]
        )
        return formatted_assignments
        
    except Exception as e:
        logger.error(f"Error getting assignments by context: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get assignments: {str(e)}"
        )


@router.put("/assignments/{assignment_id}", response_model=UniversalAssignmentResponse)
async def update_assignment(
    assignment_id: str,
    update_data: UniversalAssignmentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update assignment details"""
    
    service = UniversalAssignmentService(db)
    assignment = await service.get_assignment(assignment_id)
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    # Check permissions - only creator or admin can update
    if (assignment.from_user_id != current_user.user_id and 
        current_user.role not in ["Admin", "Test Executive"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only assignment creator or admin can update"
        )
    
    try:
        # TODO: Implement update logic in service
        # For now, return the assignment as-is
        return await _format_assignment_response(assignment, db)
        
    except Exception as e:
        logger.error(f"Error updating assignment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update assignment: {str(e)}"
        )


@router.post("/assignments/{assignment_id}/acknowledge", response_model=UniversalAssignmentResponse)
async def acknowledge_assignment(
    assignment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Acknowledge an assignment"""
    
    service = UniversalAssignmentService(db)
    
    try:
        assignment = await service.acknowledge_assignment(assignment_id, current_user.user_id)
        return await _format_assignment_response(assignment, db)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error acknowledging assignment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to acknowledge assignment: {str(e)}"
        )


@router.post("/assignments/{assignment_id}/start", response_model=UniversalAssignmentResponse)
async def start_assignment(
    assignment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Start working on an assignment"""
    
    service = UniversalAssignmentService(db)
    
    try:
        assignment = await service.start_assignment(assignment_id, current_user.user_id)
        return await _format_assignment_response(assignment, db)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error starting assignment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start assignment: {str(e)}"
        )


@router.post("/assignments/{assignment_id}/complete", response_model=UniversalAssignmentResponse)
async def complete_assignment(
    assignment_id: str,
    action_data: AssignmentAction,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Complete an assignment"""
    
    service = UniversalAssignmentService(db)
    
    try:
        assignment = await service.complete_assignment(
            assignment_id=assignment_id,
            user_id=current_user.user_id,
            completion_notes=action_data.notes,
            completion_data=action_data.completion_data,
            completion_attachments=action_data.completion_attachments
        )
        return await _format_assignment_response(assignment, db)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error completing assignment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete assignment: {str(e)}"
        )


@router.post("/assignments/{assignment_id}/approve", response_model=UniversalAssignmentResponse)
async def approve_assignment(
    assignment_id: str,
    action_data: AssignmentAction,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Approve a completed assignment"""
    
    service = UniversalAssignmentService(db)
    
    try:
        # First check if assignment needs to be completed
        assignment = await service.get_assignment(assignment_id)
        if assignment and assignment.status != "Completed":
            # For Sample Selection Review assignments, auto-complete before approval
            if "Sample Selection" in assignment.title or assignment.assignment_type == "Sample Selection Approval":
                logger.info(f"Auto-completing Sample Selection assignment {assignment_id} before approval")
                assignment = await service.complete_assignment(
                    assignment_id=assignment_id,
                    user_id=current_user.user_id,
                    completion_notes="Completed review of all samples"
                )
        
        # Now approve the assignment
        assignment = await service.approve_assignment(
            assignment_id=assignment_id,
            user_id=current_user.user_id,
            approval_notes=action_data.notes
        )
        return await _format_assignment_response(assignment, db)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error approving assignment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve assignment: {str(e)}"
        )


@router.post("/assignments/{assignment_id}/reject", response_model=UniversalAssignmentResponse)
async def reject_assignment(
    assignment_id: str,
    action_data: AssignmentAction,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Reject a completed assignment"""
    
    if not action_data.notes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rejection reason is required"
        )
    
    service = UniversalAssignmentService(db)
    
    try:
        assignment = await service.reject_assignment(
            assignment_id=assignment_id,
            user_id=current_user.user_id,
            rejection_reason=action_data.notes
        )
        return await _format_assignment_response(assignment, db)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error rejecting assignment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reject assignment: {str(e)}"
        )


@router.post("/assignments/{assignment_id}/escalate", response_model=UniversalAssignmentResponse)
async def escalate_assignment(
    assignment_id: str,
    escalation_data: AssignmentEscalation,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Escalate an assignment"""
    
    service = UniversalAssignmentService(db)
    
    try:
        assignment = await service.escalate_assignment(
            assignment_id=assignment_id,
            user_id=current_user.user_id,
            escalation_reason=escalation_data.escalation_reason,
            escalated_to_user_id=escalation_data.escalated_to_user_id
        )
        return await _format_assignment_response(assignment, db)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error escalating assignment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to escalate assignment: {str(e)}"
        )


@router.post("/assignments/{assignment_id}/delegate", response_model=UniversalAssignmentResponse)
async def delegate_assignment(
    assignment_id: str,
    delegation_data: AssignmentDelegation,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delegate an assignment to another user"""
    
    service = UniversalAssignmentService(db)
    
    try:
        assignment = await service.delegate_assignment(
            assignment_id=assignment_id,
            user_id=current_user.user_id,
            delegated_to_user_id=delegation_data.delegated_to_user_id,
            delegation_reason=delegation_data.delegation_reason
        )
        return await _format_assignment_response(assignment, db)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error delegating assignment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delegate assignment: {str(e)}"
        )


# Metrics route moved to before parameterized route


# Helper functions
async def _format_assignment_response(assignment, db: AsyncSession = None) -> UniversalAssignmentResponse:
    """Format assignment for API response"""
    
    # Generate action URL based on assignment context
    action_url = _generate_action_url(assignment)
    
    # Extract context information
    context_data = assignment.context_data or {}
    cycle_id = context_data.get("cycle_id")
    report_id = context_data.get("report_id")
    
    logger.info(f"Formatting assignment {assignment.assignment_id}, db={db is not None}, context_data={context_data}")
    
    # Convert string IDs to int if needed
    if cycle_id and isinstance(cycle_id, str):
        try:
            cycle_id = int(cycle_id)
        except ValueError:
            cycle_id = None
    if report_id and isinstance(report_id, str):
        try:
            report_id = int(report_id)
        except ValueError:
            report_id = None
    
    # Get report name from context data or fetch if missing
    report_name = context_data.get("report_name")
    cycle_name = context_data.get("cycle_name")
    
    # If we have IDs but missing names, and db session is provided, fetch them
    if db and report_id and not report_name:
        from app.models.report import Report
        from app.models.test_cycle import TestCycle
        from sqlalchemy import select
        
        try:
            logger.info(f"Fetching report name for report_id: {report_id}")
            # Fetch report name
            report_query = await db.execute(
                select(Report.report_name).where(Report.report_id == report_id)
            )
            report_result = report_query.scalar_one_or_none()
            if report_result:
                report_name = report_result
                # Update context_data with the fetched name
                context_data["report_name"] = report_name
                logger.info(f"Found report name: {report_name}")
            
            # Fetch cycle name if cycle_id exists
            if cycle_id and not cycle_name:
                logger.debug(f"Fetching cycle name for cycle_id: {cycle_id}")
                cycle_query = await db.execute(
                    select(TestCycle.cycle_name).where(TestCycle.cycle_id == cycle_id)
                )
                cycle_result = cycle_query.scalar_one_or_none()
                if cycle_result:
                    cycle_name = cycle_result
                    context_data["cycle_name"] = cycle_name
                    logger.debug(f"Found cycle name: {cycle_name}")
        except Exception as e:
            logger.warning(f"Failed to fetch report/cycle names: {e}")
    
    # Update context_data if names were fetched
    if report_name and "report_name" not in assignment.context_data:
        assignment.context_data["report_name"] = report_name
    if cycle_name and "cycle_name" not in assignment.context_data:
        assignment.context_data["cycle_name"] = cycle_name
    
    return UniversalAssignmentResponse(
        assignment_id=assignment.assignment_id,
        assignment_type=assignment.assignment_type,
        from_role=assignment.from_role,
        to_role=assignment.to_role,
        from_user_id=assignment.from_user_id,
        to_user_id=assignment.to_user_id,
        # Add user details
        from_user=UserSummary(
            user_id=assignment.from_user.user_id,
            first_name=assignment.from_user.first_name,
            last_name=assignment.from_user.last_name,
            email=assignment.from_user.email
        ) if assignment.from_user else None,
        to_user=UserSummary(
            user_id=assignment.to_user.user_id,
            first_name=assignment.to_user.first_name,
            last_name=assignment.to_user.last_name,
            email=assignment.to_user.email
        ) if assignment.to_user else None,
        title=assignment.title,
        description=assignment.description,
        task_instructions=assignment.task_instructions,
        context_type=assignment.context_type,
        context_data=assignment.context_data,
        status=assignment.status,
        priority=assignment.priority,
        assigned_at=assignment.assigned_at,
        due_date=assignment.due_date,
        acknowledged_at=assignment.acknowledged_at,
        started_at=assignment.started_at,
        completed_at=assignment.completed_at,
        completion_notes=assignment.completion_notes,
        completion_data=assignment.completion_data,
        requires_approval=assignment.requires_approval,
        approval_role=assignment.approval_role,
        approved_by_user_id=assignment.approved_by_user_id,
        approved_at=assignment.approved_at,
        approval_notes=assignment.approval_notes,
        is_overdue=assignment.is_overdue,
        days_until_due=assignment.days_until_due,
        is_active=assignment.is_active,
        is_completed=assignment.is_completed,
        # Add the generated action URL
        action_url=action_url
    )


def _generate_action_url(assignment) -> Optional[str]:
    """Generate action URL based on assignment context"""
    
    context_data = assignment.context_data or {}
    
    # Data Upload Request - navigate to data profiling page
    if assignment.assignment_type == "Data Upload Request" and assignment.context_type == "Report":
        cycle_id = context_data.get("cycle_id")
        report_id = context_data.get("report_id")
        if cycle_id and report_id:
            return f"/cycles/{cycle_id}/reports/{report_id}/data-profiling"
    
    # Sample Selection assignments
    elif assignment.assignment_type in ["CycleReportSampleSelectionSamples Selection", "CycleReportSampleSelectionSamples Review"]:
        cycle_id = context_data.get("cycle_id")
        report_id = context_data.get("report_id")
        if cycle_id and report_id:
            return f"/cycles/{cycle_id}/reports/{report_id}/sample-selection"
    
    # Sample Selection Approval - Report Owner reviews samples on dedicated review page
    elif assignment.assignment_type == "Sample Selection Approval":
        cycle_id = context_data.get("cycle_id")
        report_id = context_data.get("report_id")
        version_id = context_data.get("version_id")
        if cycle_id and report_id and version_id:
            return f"/cycles/{cycle_id}/reports/{report_id}/sample-review/{version_id}"
    
    # Scoping assignments
    elif assignment.assignment_type in ["Scoping", "Scoping Review", "Scoping Approval"]:
        cycle_id = context_data.get("cycle_id")
        report_id = context_data.get("report_id")
        if cycle_id and report_id:
            # Report Owners should go to scoping-review page for approvals
            if assignment.assignment_type == "Scoping Approval" and assignment.to_role == "Report Owner":
                return f"/cycles/{cycle_id}/reports/{report_id}/scoping-review"
            return f"/cycles/{cycle_id}/reports/{report_id}/scoping"
    
    # Testing assignments
    elif assignment.assignment_type in ["Testing", "Test Execution"]:
        cycle_id = context_data.get("cycle_id")
        report_id = context_data.get("report_id")
        if cycle_id and report_id:
            return f"/cycles/{cycle_id}/reports/{report_id}/test-execution"
    
    # Rule Approval assignments - navigate to data profiling review page for Report Owner
    elif assignment.assignment_type == "Rule Approval":
        cycle_id = context_data.get("cycle_id")
        report_id = context_data.get("report_id")
        if cycle_id and report_id:
            return f"/cycles/{cycle_id}/reports/{report_id}/data-profiling-review"
    
    # Default to assignments page
    return "/assignments"


# Convenience endpoints for common assignment patterns
@router.post("/assignments/data-upload", response_model=UniversalAssignmentResponse)
async def create_data_upload_assignment(
    cycle_id: int,
    report_id: int,
    description: str,
    priority: str = "High",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a data upload assignment (convenience endpoint)"""
    
    from app.services.universal_assignment_service import create_data_upload_assignment
    
    try:
        email_service = EmailService()
        assignment = await create_data_upload_assignment(
            db=db,
            cycle_id=cycle_id,
            report_id=report_id,
            from_user_id=current_user.user_id,
            description=description,
            priority=priority,
            email_service=email_service
        )
        
        return await _format_assignment_response(assignment, db)
        
    except Exception as e:
        logger.error(f"Error creating data upload assignment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create data upload assignment: {str(e)}"
        )


@router.post("/assignments/approval", response_model=UniversalAssignmentResponse)
async def create_approval_assignment(
    cycle_id: int,
    report_id: int,
    approval_type: str,
    item_description: str,
    approver_role: str,
    priority: str = "Medium",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create an approval assignment (convenience endpoint)"""
    
    from app.services.universal_assignment_service import create_approval_assignment
    
    try:
        email_service = EmailService()
        assignment = await create_approval_assignment(
            db=db,
            cycle_id=cycle_id,
            report_id=report_id,
            from_user_id=current_user.user_id,
            approval_type=approval_type,
            item_description=item_description,
            approver_role=approver_role,
            priority=priority,
            email_service=email_service
        )
        
        return await _format_assignment_response(assignment, db)
        
    except Exception as e:
        logger.error(f"Error creating approval assignment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create approval assignment: {str(e)}"
        )