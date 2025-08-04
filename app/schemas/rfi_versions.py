"""
RFI (Request for Information) Version Schemas

This module contains the Pydantic schemas for the RFI version models,
following the same pattern as sample selection and scoping schemas.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, UUID4
from enum import Enum


# Enums
class VersionStatus(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class EvidenceStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUEST_CHANGES = "request_changes"


class EvidenceType(str, Enum):
    DOCUMENT = "document"
    DATA_SOURCE = "data_source"


class Decision(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUEST_CHANGES = "request_changes"


class ValidationStatus(str, Enum):
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"


# Base schemas
class RFIVersionBase(BaseModel):
    """Base schema for RFI versions"""
    submission_deadline: Optional[datetime] = None
    reminder_schedule: Optional[Dict[str, Any]] = None
    instructions: Optional[str] = None


class RFIEvidenceBase(BaseModel):
    """Base schema for RFI evidence"""
    test_case_id: int
    sample_id: str
    attribute_id: int
    attribute_name: str
    evidence_type: EvidenceType
    submission_notes: Optional[str] = None
    
    # Document specific fields
    original_filename: Optional[str] = None
    mime_type: Optional[str] = None
    
    # Data source specific fields
    data_source_id: Optional[int] = None
    query_text: Optional[str] = None
    query_parameters: Optional[Dict[str, Any]] = None


# Create schemas
class RFIVersionCreate(RFIVersionBase):
    """Schema for creating a new RFI version"""
    carry_forward_all: bool = Field(True, description="Whether to carry forward all evidence from previous version")
    carry_forward_approved_only: bool = Field(False, description="Whether to carry forward only approved evidence")


class RFIEvidenceCreate(RFIEvidenceBase):
    """Schema for creating new evidence"""
    file_content: Optional[bytes] = Field(None, description="File content for document evidence")


# Update schemas
class RFIVersionUpdate(BaseModel):
    """Schema for updating RFI version"""
    submission_deadline: Optional[datetime] = None
    reminder_schedule: Optional[Dict[str, Any]] = None
    instructions: Optional[str] = None
    version_status: Optional[VersionStatus] = None
    rejection_reason: Optional[str] = None


class RFIEvidenceUpdate(BaseModel):
    """Schema for updating evidence"""
    submission_notes: Optional[str] = None
    tester_decision: Optional[Decision] = None
    tester_notes: Optional[str] = None
    report_owner_decision: Optional[Decision] = None
    report_owner_notes: Optional[str] = None
    validation_status: Optional[ValidationStatus] = None
    validation_notes: Optional[str] = None


# Response schemas
class RFIEvidenceResponse(RFIEvidenceBase):
    """Response schema for RFI evidence"""
    evidence_id: UUID4
    version_id: UUID4
    phase_id: int
    evidence_status: EvidenceStatus
    
    # Submission info
    data_owner_id: int
    data_owner_name: Optional[str] = None
    submitted_at: Optional[datetime] = None
    
    # Document specific fields
    stored_filename: Optional[str] = None
    file_path: Optional[str] = None
    file_size_bytes: Optional[int] = None
    file_hash: Optional[str] = None
    
    # Data source specific fields
    query_result_sample: Optional[Dict[str, Any]] = None
    row_count: Optional[int] = None
    
    # Decisions
    tester_decision: Optional[Decision] = None
    tester_notes: Optional[str] = None
    tester_decided_by: Optional[int] = None
    tester_decided_by_name: Optional[str] = None
    tester_decided_at: Optional[datetime] = None
    
    report_owner_decision: Optional[Decision] = None
    report_owner_notes: Optional[str] = None
    report_owner_decided_by: Optional[int] = None
    report_owner_decided_by_name: Optional[str] = None
    report_owner_decided_at: Optional[datetime] = None
    
    # Resubmission tracking
    requires_resubmission: bool = False
    resubmission_deadline: Optional[datetime] = None
    resubmission_count: int = 0
    parent_evidence_id: Optional[UUID4] = None
    
    # Validation
    validation_status: Optional[str] = None
    validation_notes: Optional[str] = None
    validated_by: Optional[int] = None
    validated_by_name: Optional[str] = None
    validated_at: Optional[datetime] = None
    
    # Computed properties
    is_approved: bool = Field(False, description="Whether evidence is approved by both tester and report owner")
    is_rejected: bool = Field(False, description="Whether evidence is rejected by either party")
    needs_resubmission: bool = Field(False, description="Whether evidence needs resubmission")
    final_status: Optional[str] = Field(None, description="Final status based on decisions")
    
    # Audit fields
    created_at: datetime
    updated_at: datetime
    created_by_id: Optional[int] = None
    created_by_name: Optional[str] = None
    updated_by_id: Optional[int] = None
    updated_by_name: Optional[str] = None
    
    class Config:
        orm_mode = True
        from_attributes = True


class RFIVersionResponse(RFIVersionBase):
    """Response schema for RFI version"""
    version_id: UUID4
    phase_id: int
    version_number: int
    version_status: VersionStatus
    parent_version_id: Optional[UUID4] = None
    
    # Summary statistics
    total_test_cases: int = 0
    submitted_count: int = 0
    approved_count: int = 0
    rejected_count: int = 0
    pending_count: int = 0
    
    # Evidence type breakdown
    document_evidence_count: int = 0
    data_source_evidence_count: int = 0
    
    # Approval workflow
    submitted_by_id: Optional[int] = None
    submitted_by_name: Optional[str] = None
    submitted_at: Optional[datetime] = None
    approved_by_id: Optional[int] = None
    approved_by_name: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    
    # Report owner review metadata
    report_owner_review_requested_at: Optional[datetime] = None
    report_owner_review_completed_at: Optional[datetime] = None
    report_owner_feedback_summary: Optional[Dict[str, Any]] = None
    
    # Workflow tracking
    workflow_execution_id: Optional[str] = None
    workflow_run_id: Optional[str] = None
    
    # Computed properties
    is_latest: bool = Field(False, description="Whether this is the latest version")
    completion_percentage: float = Field(0.0, description="Evidence submission completion percentage")
    approval_percentage: float = Field(0.0, description="Evidence approval percentage")
    can_be_edited: bool = Field(False, description="Whether version can be edited")
    has_report_owner_feedback: bool = Field(False, description="Whether report owner has provided feedback")
    
    # Relationships
    evidence_items: List[RFIEvidenceResponse] = Field(default_factory=list)
    
    # Audit fields
    created_at: datetime
    updated_at: datetime
    created_by_id: Optional[int] = None
    created_by_name: Optional[str] = None
    updated_by_id: Optional[int] = None
    updated_by_name: Optional[str] = None
    
    class Config:
        orm_mode = True
        from_attributes = True


# List response schemas
class RFIVersionListResponse(BaseModel):
    """Response schema for listing RFI versions"""
    version_id: UUID4
    phase_id: int
    version_number: int
    version_status: VersionStatus
    is_current: bool = Field(False, description="Whether this is the current/latest version")
    can_be_edited: bool = Field(False, description="Whether version can be edited")
    
    # Summary
    total_test_cases: int = 0
    submitted_count: int = 0
    approved_count: int = 0
    completion_percentage: float = 0.0
    
    # Timestamps
    created_at: datetime
    submitted_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True
        from_attributes = True


# Submission tracking schemas
class TestCaseSubmissionStatus(BaseModel):
    """Status of test case evidence submission"""
    test_case_id: int
    test_case_number: str
    test_case_name: str
    sample_id: str
    attribute_name: str
    data_owner_id: int
    data_owner_name: str
    
    # Submission status
    has_evidence: bool = False
    evidence_type: Optional[EvidenceType] = None
    submitted_at: Optional[datetime] = None
    evidence_status: Optional[EvidenceStatus] = None
    
    # Decisions
    tester_decision: Optional[Decision] = None
    report_owner_decision: Optional[Decision] = None
    final_status: Optional[str] = None
    
    # Deadline tracking
    submission_deadline: Optional[datetime] = None
    is_overdue: bool = False
    days_until_deadline: Optional[int] = None
    
    class Config:
        orm_mode = True


class DataOwnerSubmissionSummary(BaseModel):
    """Summary of submissions by data owner"""
    data_owner_id: int
    data_owner_name: str
    data_owner_email: str
    
    # Assignment counts
    total_assigned: int = 0
    submitted_count: int = 0
    pending_count: int = 0
    approved_count: int = 0
    rejected_count: int = 0
    
    # Progress
    submission_percentage: float = 0.0
    approval_percentage: float = 0.0
    
    # Deadline tracking
    earliest_deadline: Optional[datetime] = None
    overdue_count: int = 0
    
    # Test cases
    test_cases: List[TestCaseSubmissionStatus] = Field(default_factory=list)
    
    class Config:
        orm_mode = True


# Bulk action schemas
class BulkEvidenceDecision(BaseModel):
    """Schema for bulk evidence decisions"""
    evidence_ids: List[UUID4] = Field(..., min_items=1)
    decision: Decision
    notes: Optional[str] = None


class SendToReportOwnerRequest(BaseModel):
    """Request to send evidence to report owner for review"""
    message: Optional[str] = Field(None, description="Optional message to include with the assignment")
    due_date: Optional[datetime] = Field(None, description="Optional custom due date for review")


class ResubmitRequest(BaseModel):
    """Request to create new version for resubmission after report owner feedback"""
    carry_forward_approved: bool = Field(True, description="Carry forward approved evidence")
    reset_rejected: bool = Field(True, description="Reset rejected evidence to pending")


# Query validation schemas
class QueryValidationRequest(BaseModel):
    """Request to validate a query before submission"""
    test_case_id: int
    data_source_id: int
    query_text: str
    query_parameters: Optional[Dict[str, Any]] = None


class QueryValidationResponse(BaseModel):
    """Response from query validation"""
    validation_id: UUID4
    validation_status: str
    execution_time_ms: Optional[int] = None
    row_count: Optional[int] = None
    column_names: Optional[List[str]] = None
    sample_rows: Optional[List[Dict[str, Any]]] = None
    error_message: Optional[str] = None
    has_primary_keys: Optional[bool] = None
    has_target_attribute: Optional[bool] = None
    missing_columns: Optional[List[str]] = None
    
    class Config:
        orm_mode = True