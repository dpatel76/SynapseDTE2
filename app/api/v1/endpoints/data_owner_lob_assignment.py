"""
Data Owner LOB Assignment API Endpoints

This module provides REST API endpoints for the unified data owner LOB assignment system.
Business Logic: Data Executives assign Data Owners to LOB-Attribute combinations.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User
from app.services.data_owner_lob_assignment_service import DataOwnerLOBAssignmentService
from app.schemas.data_owner_lob_assignment import (
    # Version schemas
    CreateVersionRequest, DataOwnerLOBAttributeVersionResponse, VersionWithAssignmentsResponse,
    # Assignment schemas
    AssignmentRequest, BulkAssignmentRequest, BulkAssignmentResponse,
    AssignmentWithDetailsResponse, AcknowledgeAssignmentRequest, UnassignmentRequest,
    # Dashboard schemas
    PhaseAssignmentDashboard, DataOwnerWorkloadDetail, AssignmentHistoryResponse,
    # Filter schemas
    AssignmentFilters
)

router = APIRouter(prefix="/data-owner-lob-assignments", tags=["Data Owner LOB Assignments"])


# Version Management Endpoints

@router.post("/versions", response_model=DataOwnerLOBAttributeVersionResponse)
async def create_assignment_version(
    request: CreateVersionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["Data Executive"]))
):
    """
    Create a new data owner LOB assignment version
    
    Only Data Executives can create assignment versions
    """
    service = DataOwnerLOBAssignmentService(db)
    
    try:
        version = await service.create_version(
            phase_id=request.phase_id,
            data_executive_id=current_user.user_id,
            assignment_notes=request.assignment_notes,
            workflow_activity_id=request.workflow_activity_id,
            workflow_execution_id=request.workflow_execution_id,
            workflow_run_id=request.workflow_run_id
        )
        return version
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/versions/{version_id}", response_model=VersionWithAssignmentsResponse)
async def get_version_with_assignments(
    version_id: str = Path(..., description="Version ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get version details with all assignments"""
    service = DataOwnerLOBAssignmentService(db)
    
    try:
        version = await service.get_version_by_id(version_id)
        return version
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/phases/{phase_id}/current-version", response_model=Optional[DataOwnerLOBAttributeVersionResponse])
async def get_current_version(
    phase_id: int = Path(..., description="Phase ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the current active version for a phase"""
    service = DataOwnerLOBAssignmentService(db)
    
    version = await service.get_current_version(phase_id)
    return version


@router.get("/phases/{phase_id}/version-history", response_model=List[DataOwnerLOBAttributeVersionResponse])
async def get_version_history(
    phase_id: int = Path(..., description="Phase ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all versions for a phase ordered by version number"""
    service = DataOwnerLOBAssignmentService(db)
    
    versions = await service.get_version_history(phase_id)
    return versions


# Assignment Management Endpoints

@router.post("/versions/{version_id}/assignments", response_model=AssignmentWithDetailsResponse)
async def create_assignment(
    version_id: str = Path(..., description="Version ID"),
    request: AssignmentRequest = ...,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["Data Executive"]))
):
    """
    Assign a data owner to a LOB-Attribute combination
    
    Only Data Executives can create assignments
    """
    service = DataOwnerLOBAssignmentService(db)
    
    try:
        assignment = await service.assign_data_owner_to_lob_attribute(
            version_id=version_id,
            phase_id=request.phase_id,
            sample_id=request.sample_id,
            attribute_id=request.attribute_id,
            lob_id=request.lob_id,
            data_owner_id=request.data_owner_id,
            assignment_rationale=request.assignment_rationale,
            data_executive_id=current_user.user_id
        )
        return assignment
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/versions/{version_id}/bulk-assignments", response_model=BulkAssignmentResponse)
async def bulk_assign_data_owners(
    version_id: str = Path(..., description="Version ID"),
    request: BulkAssignmentRequest = ...,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["Data Executive"]))
):
    """
    Bulk assign data owners to multiple LOB-Attribute combinations
    
    Only Data Executives can create bulk assignments
    """
    service = DataOwnerLOBAssignmentService(db)
    
    try:
        # Convert assignments to dict format for service
        assignments_data = [
            {
                "phase_id": assignment.phase_id,
                "sample_id": assignment.sample_id,
                "attribute_id": assignment.attribute_id,
                "lob_id": assignment.lob_id,
                "data_owner_id": assignment.data_owner_id,
                "assignment_rationale": assignment.assignment_rationale
            }
            for assignment in request.assignments
        ]
        
        result = await service.bulk_assign_data_owners(
            version_id=version_id,
            assignments=assignments_data,
            data_executive_id=current_user.user_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/assignments/{assignment_id}", response_model=AssignmentWithDetailsResponse)
async def unassign_data_owner(
    assignment_id: str = Path(..., description="Assignment ID"),
    request: UnassignmentRequest = ...,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["Data Executive"]))
):
    """
    Unassign a data owner from a LOB-Attribute combination
    
    Only Data Executives can unassign data owners
    """
    service = DataOwnerLOBAssignmentService(db)
    
    try:
        assignment = await service.unassign_data_owner(
            assignment_id=assignment_id,
            data_executive_id=current_user.user_id,
            unassignment_reason=request.unassignment_reason
        )
        return assignment
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Data Owner Acknowledgment Endpoints

@router.post("/assignments/{assignment_id}/acknowledge", response_model=AssignmentWithDetailsResponse)
async def acknowledge_assignment(
    assignment_id: str = Path(..., description="Assignment ID"),
    request: AcknowledgeAssignmentRequest = ...,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["Data Owner"]))
):
    """
    Data owner acknowledges their assignment
    
    Only Data Owners can acknowledge assignments
    """
    service = DataOwnerLOBAssignmentService(db)
    
    try:
        assignment = await service.acknowledge_assignment(
            assignment_id=assignment_id,
            data_owner_id=current_user.user_id,
            response_notes=request.response_notes
        )
        return assignment
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Query and Dashboard Endpoints

@router.get("/phases/{phase_id}/assignments", response_model=List[AssignmentWithDetailsResponse])
async def get_lob_attribute_assignments(
    phase_id: int = Path(..., description="Phase ID"),
    version_id: Optional[str] = Query(None, description="Version ID (defaults to current active version)"),
    lob_id: Optional[int] = Query(None, description="Filter by LOB ID"),
    data_owner_id: Optional[int] = Query(None, description="Filter by Data Owner ID"),
    assignment_status: Optional[str] = Query(None, description="Filter by assignment status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get LOB attribute assignments with optional filters"""
    service = DataOwnerLOBAssignmentService(db)
    
    # If current user is a Data Executive, filter by their LOB
    data_executive_id = None
    if current_user.role == 'Data Executive':
        data_executive_id = current_user.user_id
    
    assignments = await service.get_lob_attribute_assignments(
        phase_id=phase_id,
        version_id=version_id,
        lob_id=lob_id,
        data_owner_id=data_owner_id,
        assignment_status=assignment_status,
        data_executive_id=data_executive_id
    )
    
    # Enrich assignments with relationship data for response
    enriched_assignments = []
    for assignment in assignments:
        enriched = {
            "mapping_id": assignment.mapping_id,
            "version_id": assignment.version_id,
            "phase_id": assignment.phase_id,
            "sample_id": assignment.sample_id,
            "attribute_id": assignment.attribute_id,
            "lob_id": assignment.lob_id,
            "data_owner_id": assignment.data_owner_id,
            "data_executive_id": assignment.data_executive_id,
            "assigned_by_data_executive_at": assignment.assigned_by_data_executive_at,
            "assignment_rationale": assignment.assignment_rationale,
            "previous_data_owner_id": assignment.previous_data_owner_id,
            "change_reason": assignment.change_reason,
            "assignment_status": assignment.assignment_status,
            "data_owner_acknowledged": assignment.data_owner_acknowledged,
            "data_owner_acknowledged_at": assignment.data_owner_acknowledged_at,
            "data_owner_response_notes": assignment.data_owner_response_notes,
            "created_at": assignment.created_at,
            "created_by_id": assignment.created_by_id,
            "updated_at": assignment.updated_at,
            "updated_by_id": assignment.updated_by_id,
            # Add relationship data
            "lob_name": assignment.lob.lob_name if assignment.lob else None,
            "attribute_name": assignment.attribute.attribute_name if assignment.attribute else None,
            "data_owner_name": f"{assignment.data_owner.first_name} {assignment.data_owner.last_name}" if assignment.data_owner else None,
            "data_executive_name": f"{assignment.data_executive.first_name} {assignment.data_executive.last_name}" if assignment.data_executive else None,
            "sample_description": None  # Sample description can be added if needed
        }
        enriched_assignments.append(enriched)
    
    return enriched_assignments


@router.get("/phases/{phase_id}/dashboard", response_model=PhaseAssignmentDashboard)
async def get_phase_assignment_dashboard(
    phase_id: int = Path(..., description="Phase ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive dashboard data for phase assignments"""
    service = DataOwnerLOBAssignmentService(db)
    
    dashboard = await service.get_phase_assignment_dashboard(phase_id)
    return dashboard


@router.get("/phases/{phase_id}/data-owners/{data_owner_id}/workload", response_model=DataOwnerWorkloadDetail)
async def get_data_owner_workload(
    phase_id: int = Path(..., description="Phase ID"),
    data_owner_id: int = Path(..., description="Data Owner ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get workload summary for a specific data owner"""
    service = DataOwnerLOBAssignmentService(db)
    
    workload = await service.get_data_owner_workload(phase_id, data_owner_id)
    return workload


@router.get("/data-owners/my-assignments/{phase_id}", response_model=DataOwnerWorkloadDetail)
async def get_my_assignments(
    phase_id: int = Path(..., description="Phase ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["Data Owner"]))
):
    """Get assignments for the current data owner"""
    service = DataOwnerLOBAssignmentService(db)
    
    workload = await service.get_data_owner_workload(phase_id, current_user.user_id)
    return workload


@router.get("/phases/{phase_id}/history", response_model=AssignmentHistoryResponse)
async def get_assignment_history(
    phase_id: int = Path(..., description="Phase ID"),
    lob_id: Optional[int] = Query(None, description="Filter by LOB ID"),
    attribute_id: Optional[int] = Query(None, description="Filter by Attribute ID"),
    sample_id: Optional[int] = Query(None, description="Filter by Sample ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get history of assignment changes across versions"""
    service = DataOwnerLOBAssignmentService(db)
    
    changes = await service.get_assignment_changes_history(
        phase_id=phase_id,
        lob_id=lob_id,
        attribute_id=attribute_id,
        sample_id=sample_id
    )
    
    return {
        "phase_id": phase_id,
        "changes": changes
    }


# Utility Endpoints

@router.get("/assignments/{assignment_id}", response_model=AssignmentWithDetailsResponse)
async def get_assignment_by_id(
    assignment_id: str = Path(..., description="Assignment ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get assignment by ID"""
    service = DataOwnerLOBAssignmentService(db)
    
    try:
        assignment = await service.get_assignment_by_id(assignment_id)
        return assignment
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


# Health Check Endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "data_owner_lob_assignment"}