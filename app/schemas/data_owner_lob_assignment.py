"""
Data Owner LOB Assignment Schemas

Pydantic schemas for the unified data owner LOB assignment system API.
These schemas support the business logic: Data Executives assign Data Owners to LOB-Attribute combinations.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator
from uuid import UUID


# Base schemas for responses
class DataOwnerLOBAttributeVersionBase(BaseModel):
    """Base schema for data owner LOB attribute version"""
    phase_id: int = Field(..., description="Phase ID")
    workflow_activity_id: Optional[int] = Field(None, description="Workflow activity ID")
    version_number: int = Field(..., description="Version number")
    version_status: str = Field(..., description="Version status")
    workflow_execution_id: Optional[str] = Field(None, description="Temporal workflow execution ID")
    workflow_run_id: Optional[str] = Field(None, description="Temporal workflow run ID")
    total_lob_attributes: int = Field(0, description="Total LOB-attribute combinations")
    assigned_lob_attributes: int = Field(0, description="Assigned LOB-attribute combinations")
    unassigned_lob_attributes: int = Field(0, description="Unassigned LOB-attribute combinations")
    data_executive_id: int = Field(..., description="Data executive who created this version")
    assignment_batch_date: datetime = Field(..., description="When assignments were created")
    assignment_notes: Optional[str] = Field(None, description="Notes from data executive")


class DataOwnerLOBAttributeMappingBase(BaseModel):
    """Base schema for data owner LOB attribute mapping"""
    phase_id: int = Field(..., description="Phase ID")
    sample_id: Optional[UUID] = Field(None, description="Sample ID")  # Changed to UUID to match database
    attribute_id: int = Field(..., description="Attribute ID")
    lob_id: int = Field(..., description="LOB ID")
    data_owner_id: Optional[int] = Field(None, description="Assigned data owner ID")
    data_executive_id: Optional[int] = Field(None, description="Data executive who made the assignment")  # Made optional to match database
    assigned_by_data_executive_at: Optional[datetime] = Field(None, description="When assignment was made")  # Made optional to match database
    assignment_rationale: Optional[str] = Field(None, description="Rationale for assignment")
    previous_data_owner_id: Optional[int] = Field(None, description="Previous data owner if changed")
    change_reason: Optional[str] = Field(None, description="Reason for change")
    assignment_status: str = Field(..., description="Assignment status")
    data_owner_acknowledged: bool = Field(False, description="Whether data owner acknowledged")
    data_owner_acknowledged_at: Optional[datetime] = Field(None, description="When acknowledged")
    data_owner_response_notes: Optional[str] = Field(None, description="Data owner response notes")


# Request schemas
class CreateVersionRequest(BaseModel):
    """Request to create a new data owner LOB assignment version"""
    phase_id: int = Field(..., description="Phase ID")
    assignment_notes: Optional[str] = Field(None, description="Notes about this assignment batch")
    workflow_activity_id: Optional[int] = Field(None, description="Associated workflow activity")
    workflow_execution_id: Optional[str] = Field(None, description="Temporal workflow execution ID")
    workflow_run_id: Optional[str] = Field(None, description="Temporal workflow run ID")


class AssignmentRequest(BaseModel):
    """Request to assign a data owner to a LOB-attribute combination"""
    phase_id: int = Field(..., description="Phase ID")
    sample_id: Optional[UUID] = Field(None, description="Sample ID")  # Changed to UUID to match database
    attribute_id: int = Field(..., description="Attribute ID")
    lob_id: int = Field(..., description="LOB ID")
    data_owner_id: Optional[int] = Field(None, description="Data owner to assign (null for unassign)")
    assignment_rationale: Optional[str] = Field(None, description="Rationale for this assignment")


class BulkAssignmentRequest(BaseModel):
    """Request to bulk assign data owners to multiple LOB-attribute combinations"""
    assignments: List[AssignmentRequest] = Field(..., description="List of assignments to create/update")
    
    @validator('assignments')
    def assignments_not_empty(cls, v):
        if not v:
            raise ValueError('Assignments list cannot be empty')
        return v


class AcknowledgeAssignmentRequest(BaseModel):
    """Request for data owner to acknowledge their assignment"""
    response_notes: Optional[str] = Field(None, description="Optional response notes from data owner")


class UnassignmentRequest(BaseModel):
    """Request to unassign a data owner from a LOB-attribute combination"""
    unassignment_reason: Optional[str] = Field(None, description="Reason for unassignment")


# Response schemas with full data
class DataOwnerLOBAttributeVersionResponse(DataOwnerLOBAttributeVersionBase):
    """Full response schema for data owner LOB attribute version"""
    version_id: UUID = Field(..., description="Version ID")
    parent_version_id: Optional[UUID] = Field(None, description="Parent version ID if this is a revision")
    created_at: datetime = Field(..., description="Creation timestamp")
    created_by_id: int = Field(..., description="User who created this version")
    updated_at: datetime = Field(..., description="Last update timestamp")
    updated_by_id: int = Field(..., description="User who last updated this version")
    
    class Config:
        from_attributes = True


class DataOwnerLOBAttributeMappingResponse(DataOwnerLOBAttributeMappingBase):
    """Full response schema for data owner LOB attribute assignment"""
    mapping_id: UUID = Field(..., description="Mapping ID")  # Changed from assignment_id to match model
    version_id: Optional[UUID] = Field(None, description="Version ID")  # Made optional since it can be NULL in database
    created_at: datetime = Field(..., description="Creation timestamp")
    created_by_id: int = Field(..., description="User who created this assignment")
    updated_at: datetime = Field(..., description="Last update timestamp")
    updated_by_id: int = Field(..., description="User who last updated this assignment")
    
    class Config:
        from_attributes = True


# Enhanced response schemas with related data
class AssignmentWithDetailsResponse(DataOwnerLOBAttributeMappingResponse):
    """Assignment response with related entity details"""
    lob_name: Optional[str] = Field(None, description="LOB name")
    attribute_name: Optional[str] = Field(None, description="Attribute name")
    data_owner_name: Optional[str] = Field(None, description="Data owner full name")
    data_executive_name: Optional[str] = Field(None, description="Data executive full name")
    sample_description: Optional[str] = Field(None, description="Sample description")


class VersionWithAssignmentsResponse(DataOwnerLOBAttributeVersionResponse):
    """Version response with assignments included"""
    assignments: List[AssignmentWithDetailsResponse] = Field(default_factory=list, description="Associated assignments")


# Bulk operation responses
class BulkAssignmentResponse(BaseModel):
    """Response for bulk assignment operations"""
    version_id: UUID = Field(..., description="Version ID")
    created_assignments: int = Field(..., description="Number of new assignments created")
    updated_assignments: int = Field(..., description="Number of existing assignments updated")
    errors: int = Field(..., description="Number of errors encountered")
    error_details: List[Dict[str, Any]] = Field(default_factory=list, description="Details of any errors")


# Dashboard and analytics schemas
class AssignmentSummary(BaseModel):
    """Summary statistics for assignments"""
    total_assignments: int = Field(..., description="Total number of assignments")
    assigned_count: int = Field(..., description="Number of assigned LOB-attributes")
    unassigned_count: int = Field(..., description="Number of unassigned LOB-attributes")
    acknowledged_count: int = Field(..., description="Number of acknowledged assignments")
    pending_acknowledgment_count: int = Field(..., description="Number of pending acknowledgments")


class LOBBreakdown(BaseModel):
    """Assignment breakdown by LOB"""
    lob_id: int = Field(..., description="LOB ID")
    lob_name: str = Field(..., description="LOB name")
    total_attributes: int = Field(..., description="Total attributes for this LOB")
    assigned_attributes: int = Field(..., description="Assigned attributes for this LOB")
    acknowledged_attributes: int = Field(..., description="Acknowledged attributes for this LOB")


class DataOwnerWorkload(BaseModel):
    """Workload summary for a data owner"""
    data_owner_id: int = Field(..., description="Data owner ID")
    data_owner_name: str = Field(..., description="Data owner full name")
    total_assignments: int = Field(..., description="Total assignments for this data owner")
    acknowledged_assignments: int = Field(..., description="Acknowledged assignments for this data owner")


class PhaseAssignmentDashboard(BaseModel):
    """Comprehensive dashboard for phase assignments"""
    phase_id: int = Field(..., description="Phase ID")
    current_version: Optional[Dict[str, Any]] = Field(None, description="Current version summary")
    assignment_summary: AssignmentSummary = Field(..., description="Assignment summary statistics")
    lob_breakdown: List[LOBBreakdown] = Field(default_factory=list, description="Breakdown by LOB")
    data_owner_workload: List[DataOwnerWorkload] = Field(default_factory=list, description="Data owner workload")


class DataOwnerWorkloadDetail(BaseModel):
    """Detailed workload for a specific data owner"""
    data_owner_id: int = Field(..., description="Data owner ID")
    phase_id: int = Field(..., description="Phase ID")
    version_id: Optional[UUID] = Field(None, description="Current version ID")
    total_assignments: int = Field(..., description="Total assignments")
    acknowledged_assignments: int = Field(..., description="Acknowledged assignments")
    pending_assignments: int = Field(..., description="Pending assignments")
    assignments: List[AssignmentWithDetailsResponse] = Field(default_factory=list, description="Detailed assignments")


# Change tracking schemas
class AssignmentChange(BaseModel):
    """Historical change in assignment"""
    version_number: int = Field(..., description="Version number when change occurred")
    version_date: datetime = Field(..., description="Date of version")
    data_executive_id: int = Field(..., description="Data executive who made the change")
    mapping_id: UUID = Field(..., description="Mapping ID")  # Changed from assignment_id to match model
    lob_id: int = Field(..., description="LOB ID")
    lob_name: Optional[str] = Field(None, description="LOB name")
    attribute_id: int = Field(..., description="Attribute ID")
    attribute_name: Optional[str] = Field(None, description="Attribute name")
    sample_id: Optional[UUID] = Field(None, description="Sample ID")  # Changed to UUID to match database
    data_owner_id: Optional[int] = Field(None, description="Current data owner ID")
    data_owner_name: Optional[str] = Field(None, description="Current data owner name")
    previous_data_owner_id: Optional[int] = Field(None, description="Previous data owner ID")
    previous_data_owner_name: Optional[str] = Field(None, description="Previous data owner name")
    change_reason: Optional[str] = Field(None, description="Reason for change")
    assignment_status: str = Field(..., description="Assignment status")
    assignment_rationale: Optional[str] = Field(None, description="Assignment rationale")


class AssignmentHistoryResponse(BaseModel):
    """Response for assignment change history"""
    phase_id: int = Field(..., description="Phase ID")
    changes: List[AssignmentChange] = Field(default_factory=list, description="List of changes")


# Filter schemas for queries
class AssignmentFilters(BaseModel):
    """Filters for assignment queries"""
    lob_id: Optional[int] = Field(None, description="Filter by LOB ID")
    data_owner_id: Optional[int] = Field(None, description="Filter by data owner ID")
    assignment_status: Optional[str] = Field(None, description="Filter by assignment status")
    acknowledged: Optional[bool] = Field(None, description="Filter by acknowledgment status")
    
    @validator('assignment_status')
    def validate_assignment_status(cls, v):
        if v is not None and v not in ['assigned', 'unassigned', 'changed', 'confirmed']:
            raise ValueError('Invalid assignment status')
        return v


# Error schemas
class AssignmentError(BaseModel):
    """Error details for assignment operations"""
    assignment_data: Dict[str, Any] = Field(..., description="Assignment data that failed")
    error: str = Field(..., description="Error message")


# Validation utilities
def validate_version_status(status: str) -> str:
    """Validate version status"""
    valid_statuses = ['draft', 'active', 'superseded']
    if status not in valid_statuses:
        raise ValueError(f'Status must be one of: {", ".join(valid_statuses)}')
    return status


def validate_assignment_status(status: str) -> str:
    """Validate assignment status"""
    valid_statuses = ['assigned', 'unassigned', 'changed', 'confirmed']
    if status not in valid_statuses:
        raise ValueError(f'Status must be one of: {", ".join(valid_statuses)}')
    return status