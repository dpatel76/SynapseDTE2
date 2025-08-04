"""
Request for Information DTOs for clean architecture
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class SubmissionTypeEnum(str, Enum):
    """Types of submissions"""
    DOCUMENT = "Document"
    DATABASE = "Database"
    MIXED = "Mixed"


class SubmissionStatusEnum(str, Enum):
    """Status of submissions"""
    PENDING = "Pending"
    IN_PROGRESS = "In Progress"
    SUBMITTED = "Submitted"
    VALIDATED = "Validated"
    REQUIRES_REVISION = "Requires Revision"
    OVERDUE = "Overdue"


class DocumentTypeEnum(str, Enum):
    """Types of documents"""
    SOURCE_DOCUMENT = "Source Document"
    SUPPORTING_EVIDENCE = "Supporting Evidence"
    DATA_EXTRACT = "Data Extract"
    QUERY_RESULT = "Query Result"
    OTHER = "Other"


class TestCaseStatusEnum(str, Enum):
    """Test case status"""
    PENDING = "Pending"
    SUBMITTED = "Submitted"
    OVERDUE = "Overdue"
    IN_PROGRESS = "In Progress"
    COMPLETE = "Complete"


class RequestInfoPhaseStartDTO(BaseModel):
    """DTO for starting request info phase"""
    instructions: Optional[str] = None
    submission_deadline: Optional[datetime] = None


class TestCaseCreateDTO(BaseModel):
    """DTO for creating test case"""
    attribute_id: int
    sample_id: str
    sample_identifier: str
    data_owner_id: int
    attribute_name: str
    primary_key_attributes: Dict[str, Any]
    expected_evidence_type: Optional[str] = None
    special_instructions: Optional[str] = None
    submission_deadline: Optional[datetime] = None


class TestCaseResponseDTO(BaseModel):
    """DTO for test case response"""
    test_case_id: str
    phase_id: str
    cycle_id: int
    report_id: int
    attribute_id: int
    sample_id: str
    sample_identifier: str
    data_owner_id: int
    assigned_by: int
    assigned_at: datetime
    attribute_name: str
    primary_key_attributes: Dict[str, Any]
    expected_evidence_type: Optional[str]
    special_instructions: Optional[str]
    status: TestCaseStatusEnum
    submission_deadline: Optional[datetime]
    submitted_at: Optional[datetime]
    acknowledged_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class TestCaseWithDetailsDTO(TestCaseResponseDTO):
    """DTO for test case with additional details"""
    data_owner_name: str
    data_owner_email: str
    cycle_name: str
    report_name: str
    submission_count: int
    latest_submission_at: Optional[datetime]
    requires_revision: Optional[bool] = False
    revision_reason: Optional[str] = None
    revision_deadline: Optional[datetime] = None
    can_resubmit: Optional[bool] = True
    approval_status: Optional[str] = None  # 'Approved', 'Rejected', 'Requires Revision', or None


class DocumentSubmissionCreateDTO(BaseModel):
    """DTO for document submission"""
    test_case_id: str
    document_type: DocumentTypeEnum
    submission_notes: Optional[str] = None


class DocumentSubmissionResponseDTO(BaseModel):
    """DTO for document submission response"""
    submission_id: str
    test_case_id: str
    data_owner_id: int
    original_filename: str
    stored_filename: str
    file_path: str
    file_size_bytes: int
    document_type: DocumentTypeEnum
    mime_type: str
    submission_notes: Optional[str]
    submitted_at: datetime
    revision_number: int
    parent_submission_id: Optional[str]
    is_current: bool
    notes: Optional[str]
    is_valid: bool
    validation_notes: Optional[str]
    validated_by: Optional[int]
    validated_at: Optional[datetime]


class FileUploadResponseDTO(BaseModel):
    """DTO for file upload response"""
    submission_id: str
    filename: str
    file_size: int
    mime_type: str
    upload_timestamp: datetime
    storage_path: str


class DataOwnerNotificationDTO(BaseModel):
    """DTO for data owner notification"""
    notification_id: str
    phase_id: str
    cycle_id: int
    report_id: int
    data_owner_id: int
    assigned_attributes: List[str]
    sample_count: int
    submission_deadline: datetime
    portal_access_url: str
    custom_instructions: Optional[str]
    notification_sent_at: Optional[datetime]
    first_access_at: Optional[datetime]
    last_access_at: Optional[datetime]
    access_count: int
    is_acknowledged: bool
    acknowledged_at: Optional[datetime]
    status: SubmissionStatusEnum


class RequestInfoPhaseStatusDTO(BaseModel):
    """DTO for request info phase status"""
    phase_id: str
    cycle_id: int
    report_id: int
    phase_status: str
    total_test_cases: int
    submitted_test_cases: int
    pending_test_cases: int
    overdue_test_cases: int
    data_owners_notified: int
    total_submissions: int
    can_complete: bool
    completion_requirements: List[str]
    # Additional statistics for frontend
    total_attributes: int = 0
    scoped_attributes: int = 0
    total_samples: int = 0
    total_lobs: int = 0
    total_data_providers: int = 0
    uploaded_test_cases: int = 0
    started_at: Optional[datetime] = None


class DataOwnerPortalDataDTO(BaseModel):
    """DTO for data owner portal view"""
    test_cases: List[TestCaseWithDetailsDTO]
    total_assigned: int
    total_submitted: int
    total_pending: int
    total_overdue: int
    submission_deadline: Optional[datetime]
    instructions: Optional[str]


class PhaseProgressSummaryDTO(BaseModel):
    """DTO for phase progress summary"""
    total_attributes: int
    total_test_cases: int
    test_cases_by_status: Dict[str, int]
    data_owners_assigned: int
    data_owners_responded: int
    average_response_time_hours: Optional[float]
    completion_percentage: float


class DataOwnerAssignmentSummaryDTO(BaseModel):
    """DTO for data owner assignment summary"""
    data_owner_id: int
    data_owner_name: str
    data_owner_email: str
    assigned_test_cases: int
    submitted_test_cases: int
    pending_test_cases: int
    overdue_test_cases: int
    last_submission_at: Optional[datetime]
    average_submission_time_hours: Optional[float]


class PhaseCompletionRequestDTO(BaseModel):
    """DTO for phase completion request"""
    completion_notes: Optional[str] = None
    override_checks: bool = False


class ResendTestCaseRequestDTO(BaseModel):
    """DTO for resending test case"""
    reason: str
    additional_instructions: Optional[str] = None
    new_deadline: Optional[datetime] = None
    evidence_type: Optional[str] = None  # 'document', 'data_source', or None for all
    invalidate_previous: Optional[bool] = True  # Whether to invalidate previous submissions


class BulkTestCaseAssignmentDTO(BaseModel):
    """DTO for bulk test case assignment"""
    assignments: List[TestCaseCreateDTO]


class TestCaseUpdateDTO(BaseModel):
    """DTO for updating test case"""
    special_instructions: Optional[str] = None
    submission_deadline: Optional[datetime] = None
    expected_evidence_type: Optional[str] = None