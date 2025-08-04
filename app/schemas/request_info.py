"""
Request for Information phase schemas
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


class RequestInfoPhaseStatus(str, Enum):
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    COMPLETE = "Complete"


class TestCaseStatus(str, Enum):
    PENDING = "Pending"
    SUBMITTED = "Submitted"
    OVERDUE = "Overdue"


class DocumentType(str, Enum):
    SOURCE_DOCUMENT = "Source Document"
    SUPPORTING_EVIDENCE = "Supporting Evidence"
    DATA_EXTRACT = "Data Extract"
    QUERY_RESULT = "Query Result"
    OTHER = "Other"


class SubmissionStatus(str, Enum):
    PENDING = "Pending"
    IN_PROGRESS = "In Progress"
    SUBMITTED = "Submitted"
    VALIDATED = "Validated"
    REQUIRES_REVISION = "Requires Revision"
    OVERDUE = "Overdue"


# New enums for evidence management
class EvidenceType(str, Enum):
    DOCUMENT = "document"
    DATA_SOURCE = "data_source"


class EvidenceValidationStatus(str, Enum):
    PENDING = "pending"
    VALID = "valid"
    INVALID = "invalid"
    REQUIRES_REVIEW = "requires_review"


class ValidationResultEnum(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"


class TesterDecision(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUIRES_REVISION = "requires_revision"


# Base schemas
class RequestInfoPhaseBase(BaseModel):
    instructions: Optional[str] = None
    submission_deadline: Optional[datetime] = None


class RequestInfoPhaseCreate(RequestInfoPhaseBase):
    cycle_id: int
    report_id: int


class RequestInfoPhaseUpdate(BaseModel):
    instructions: Optional[str] = None
    submission_deadline: Optional[datetime] = None
    phase_status: Optional[str] = None


class RequestInfoPhaseResponse(RequestInfoPhaseBase):
    phase_id: str
    cycle_id: int
    report_id: int
    phase_status: str  # Match the actual database column
    
    # Timing
    started_by: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_by: Optional[int] = None
    completed_at: Optional[datetime] = None
    
    # Additional fields that match database schema
    reminder_schedule: Optional[List[int]] = None  # Database has list of integers
    planned_start_date: Optional[datetime] = None
    planned_end_date: Optional[datetime] = None
    
    # Metadata
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Test Case schemas
class TestCaseBase(BaseModel):
    attribute_name: str = Field(max_length=255)
    sample_identifier: str = Field(max_length=255)
    primary_key_attributes: Dict[str, Any]
    expected_evidence_type: Optional[str] = None
    special_instructions: Optional[str] = None
    submission_deadline: Optional[datetime] = None


class TestCaseCreate(TestCaseBase):
    phase_id: str
    cycle_id: int
    report_id: int
    attribute_id: int
    sample_id: str
    data_owner_id: int


class TestCaseUpdate(BaseModel):
    expected_evidence_type: Optional[str] = None
    special_instructions: Optional[str] = None
    submission_deadline: Optional[datetime] = None
    status: Optional[TestCaseStatus] = None


class TestCaseResponse(TestCaseBase):
    test_case_id: str
    phase_id: str
    cycle_id: int
    report_id: int
    attribute_id: int
    sample_id: str
    
    # Assignment details
    data_owner_id: int
    assigned_by: int
    assigned_at: datetime
    
    # Status and timing
    status: TestCaseStatus
    submitted_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    
    # Metadata
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TestCaseWithDetails(TestCaseResponse):
    """Test case with additional details for display"""
    data_owner_name: Optional[str] = None
    data_owner_email: Optional[str] = None
    assigned_by_name: Optional[str] = None
    document_count: int = 0
    has_submissions: bool = False
    cycle_name: Optional[str] = None
    report_name: Optional[str] = None


# Document Submission schemas
class DocumentSubmissionBase(BaseModel):
    original_filename: str = Field(max_length=255)
    document_type: DocumentType
    submission_notes: Optional[str] = None


class DocumentSubmissionCreate(DocumentSubmissionBase):
    test_case_id: str
    stored_filename: str
    file_path: str
    file_size_bytes: int
    mime_type: str


class DocumentSubmissionUpdate(BaseModel):
    submission_notes: Optional[str] = None
    is_valid: Optional[bool] = None
    validation_notes: Optional[str] = None


class DocumentSubmissionResponse(DocumentSubmissionBase):
    submission_id: str
    test_case_id: str
    data_owner_id: int
    stored_filename: str
    file_path: str
    file_size_bytes: int
    mime_type: str
    
    # Submission details
    submitted_at: datetime
    
    # Validation
    is_valid: bool = True
    validation_notes: Optional[str] = None
    validated_by: Optional[int] = None
    validated_at: Optional[datetime] = None
    
    # Metadata
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Data Provider Notification schemas
class DataProviderNotificationBase(BaseModel):
    assigned_attributes: List[str]
    sample_count: int
    submission_deadline: datetime
    portal_access_url: str = Field(max_length=500)
    custom_instructions: Optional[str] = None


class DataProviderNotificationCreate(DataProviderNotificationBase):
    phase_id: str
    cycle_id: int
    report_id: int
    data_owner_id: int


class DataProviderNotificationUpdate(BaseModel):
    custom_instructions: Optional[str] = None
    submission_deadline: Optional[datetime] = None
    is_acknowledged: Optional[bool] = None


class DataProviderNotificationResponse(DataProviderNotificationBase):
    notification_id: str
    phase_id: str
    cycle_id: int
    report_id: int
    data_owner_id: int
    
    # Tracking
    notification_sent_at: Optional[datetime] = None
    first_access_at: Optional[datetime] = None
    last_access_at: Optional[datetime] = None
    access_count: int = 0
    is_acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None
    
    # Status tracking
    status: SubmissionStatus
    
    # Metadata
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Composite schemas for complex operations
class StartPhaseRequest(BaseModel):
    instructions: Optional[str] = None
    submission_deadline: datetime
    auto_notify_data_owners: bool = True
    notify_immediately: bool = True


class PhaseProgressSummary(BaseModel):
    phase_id: str
    phase_name: str
    phase_status: str
    cycle_name: str
    report_name: str
    
    # Progress metrics
    total_test_cases: int
    submitted_test_cases: int
    pending_test_cases: int
    overdue_test_cases: int
    completion_percentage: float
    
    # Timing
    started_at: Optional[datetime] = None
    submission_deadline: Optional[datetime] = None
    days_remaining: Optional[int] = None
    
    # Data provider summary
    total_data_owners: int
    notified_data_owners: int
    active_data_owners: int


class DataProviderAssignmentSummary(BaseModel):
    data_owner_id: int
    data_owner_name: str
    data_owner_email: str
    
    # Assignment details
    assigned_attributes: List[str]
    total_test_cases: int
    submitted_test_cases: int
    pending_test_cases: int
    overdue_test_cases: int
    
    # Status
    overall_status: SubmissionStatus
    last_activity: Optional[datetime] = None
    notification_sent: bool = False
    portal_accessed: bool = False


class TestCaseListResponse(BaseModel):
    test_cases: List[TestCaseWithDetails]
    total_count: int
    submitted_count: int
    pending_count: int
    overdue_count: int
    
    # Filters applied
    data_owner_id: Optional[int] = None
    attribute_id: Optional[int] = None
    status_filter: Optional[TestCaseStatus] = None


class DataProviderPortalData(BaseModel):
    """Data for data provider portal view"""
    notification: DataProviderNotificationResponse
    test_cases: List[TestCaseResponse]
    cycle_name: str
    report_name: str
    phase_instructions: Optional[str] = None
    submission_deadline: datetime
    days_remaining: int
    
    # Progress summary
    total_test_cases: int
    submitted_test_cases: int
    pending_test_cases: int
    completion_percentage: float


class TesterPhaseView(BaseModel):
    """Complete phase view for testers"""
    phase: RequestInfoPhaseResponse
    cycle_name: str
    report_name: str
    
    # Progress summary
    progress_summary: PhaseProgressSummary
    data_owner_summaries: List[DataProviderAssignmentSummary]
    
    # Recent activity
    recent_submissions: List[DocumentSubmissionResponse]
    overdue_test_cases: List[TestCaseWithDetails]
    
    # Actions available
    can_start_phase: bool = False
    can_complete_phase: bool = False
    can_send_reminders: bool = False


class FileUploadResponse(BaseModel):
    """Response for file upload operations"""
    success: bool
    message: str
    submission_id: Optional[str] = None
    file_info: Optional[Dict[str, Any]] = None
    errors: Optional[List[str]] = None


class BulkTestCaseCreate(BaseModel):
    """For creating multiple test cases at once"""
    phase_id: str
    cycle_id: int
    report_id: int
    test_cases: List[Dict[str, Any]]  # Flexible structure for bulk creation


class PhaseCompletionRequest(BaseModel):
    """Request to complete a phase"""
    completion_notes: Optional[str] = None
    force_complete: bool = False  # Complete even if not all submissions received


# Validation schemas
class ValidationResult(BaseModel):
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    info: List[str] = []


class PhaseValidation(ValidationResult):
    """Validation result for phase operations"""
    can_start: bool = False
    can_complete: bool = False
    missing_assignments: List[str] = []
    overdue_submissions: List[str] = []


# Evidence Management Schemas

class EvidenceBase(BaseModel):
    """Base schema for evidence"""
    evidence_type: EvidenceType
    submission_notes: Optional[str] = None


class DocumentEvidenceCreate(EvidenceBase):
    """Schema for creating document evidence"""
    evidence_type: EvidenceType = EvidenceType.DOCUMENT
    # File details will be populated by the upload handler
    
    class Config:
        schema_extra = {
            "example": {
                "evidence_type": "document",
                "submission_notes": "Customer invoice supporting the transaction amount"
            }
        }


class DataSourceEvidenceCreate(EvidenceBase):
    """Schema for creating data source evidence"""
    evidence_type: EvidenceType = EvidenceType.DATA_SOURCE
    data_source_id: int = Field(..., description="ID of the data source")
    query_text: str = Field(..., min_length=10, description="SQL query text")
    query_parameters: Optional[Dict[str, Any]] = Field(None, description="Query parameters")
    
    class Config:
        schema_extra = {
            "example": {
                "evidence_type": "data_source",
                "data_source_id": 1,
                "query_text": "SELECT amount, customer_id FROM transactions WHERE transaction_id = ?",
                "query_parameters": {"transaction_id": "TXN-123"},
                "submission_notes": "Query to retrieve transaction amount from main database"
            }
        }


class EvidenceResponse(EvidenceBase):
    """Response schema for evidence"""
    id: int
    test_case_id: str
    sample_id: str
    attribute_id: int
    
    # Evidence details
    version_number: int
    is_current: bool
    validation_status: EvidenceValidationStatus
    validation_notes: Optional[str] = None
    
    # Submission details
    submitted_by: int
    submitted_at: datetime
    
    # Document-specific fields (populated if evidence_type is document)
    document_name: Optional[str] = None
    document_size: Optional[int] = None
    mime_type: Optional[str] = None
    
    # Data source-specific fields (populated if evidence_type is data_source)
    data_source_id: Optional[int] = None
    query_text: Optional[str] = None
    query_parameters: Optional[Dict[str, Any]] = None
    query_result_sample: Optional[Dict[str, Any]] = None
    
    # Audit fields
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class EvidenceWithValidation(EvidenceResponse):
    """Evidence response with validation details"""
    validation_results: List[Dict[str, Any]] = []
    tester_decisions: List[Dict[str, Any]] = []


class ValidationResultSchema(BaseModel):
    """Schema for validation results"""
    rule: str
    result: ValidationResultEnum
    message: str
    validated_at: datetime
    details: Optional[Dict[str, Any]] = None


class TesterDecisionCreate(BaseModel):
    """Schema for creating tester decisions"""
    decision: TesterDecision
    decision_notes: Optional[str] = None
    requires_resubmission: bool = False
    resubmission_deadline: Optional[datetime] = None
    follow_up_instructions: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "decision": "approved",
                "decision_notes": "Evidence is sufficient and meets requirements",
                "requires_resubmission": False
            }
        }


class TesterDecisionResponse(BaseModel):
    """Response schema for tester decisions"""
    id: int
    evidence_id: int
    decision: TesterDecision
    decision_notes: Optional[str] = None
    decision_date: datetime
    decided_by: int
    decided_by_name: str
    requires_resubmission: bool
    resubmission_deadline: Optional[datetime] = None
    follow_up_instructions: Optional[str] = None
    
    class Config:
        from_attributes = True


class EvidenceSubmissionResponse(BaseModel):
    """Response for evidence submission"""
    success: bool
    message: str
    evidence_id: Optional[int] = None
    version_number: Optional[int] = None
    validation_summary: Optional[Dict[str, Any]] = None
    errors: Optional[List[str]] = None


class TestCaseEvidenceResponse(BaseModel):
    """Response for test case evidence"""
    test_case_id: str
    has_evidence: bool
    evidence: Optional[EvidenceResponse] = None
    validation_results: List[ValidationResultSchema] = []
    tester_decisions: List[TesterDecisionResponse] = []


class EvidenceListResponse(BaseModel):
    """Response for evidence listing"""
    evidence_list: List[EvidenceWithValidation]
    total_count: int
    pending_review_count: int
    valid_count: int
    invalid_count: int
    requires_review_count: int


class PhaseEvidenceProgressResponse(BaseModel):
    """Response for phase evidence progress"""
    phase_id: int
    total_test_cases: int
    completed_test_cases: int
    completion_percentage: float
    can_complete_phase: bool
    evidence_statistics: Dict[str, Any]


class EvidenceValidationSummary(BaseModel):
    """Summary of evidence validation"""
    evidence_id: int
    total_rules: int
    passed: int
    failed: int
    warnings: int
    overall_status: EvidenceValidationStatus
    validation_results: List[ValidationResultSchema] = []


class DataOwnerEvidencePortalData(BaseModel):
    """Data for data owner evidence portal"""
    test_case: TestCaseResponse
    current_evidence: Optional[EvidenceResponse] = None
    validation_summary: Optional[EvidenceValidationSummary] = None
    available_data_sources: List[Dict[str, Any]] = []
    can_submit_evidence: bool = True
    can_resubmit: bool = False
    resubmission_deadline: Optional[datetime] = None


class TesterEvidenceReviewData(BaseModel):
    """Data for tester evidence review"""
    evidence: EvidenceWithValidation
    test_case: TestCaseWithDetails
    validation_summary: EvidenceValidationSummary
    can_approve: bool = True
    can_reject: bool = True
    can_request_revision: bool = True


# Query Validation Schemas
class QueryValidationRequest(BaseModel):
    """Request to validate a query before submission"""
    test_case_id: int
    data_source_id: str
    query_text: str
    query_parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    sample_size_limit: int = Field(default=10, description="Number of sample rows to return")
    execute_query: bool = Field(default=False, description="Whether to execute the query and return results")
    
    @validator('query_text')
    def validate_query_text(cls, v):
        if not v or not v.strip():
            raise ValueError("Query text cannot be empty")
        # Basic SQL injection prevention
        dangerous_keywords = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE', 'INSERT', 'UPDATE']
        query_upper = v.upper()
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                raise ValueError(f"Query contains prohibited keyword: {keyword}")
        return v


class QueryValidationResult(BaseModel):
    """Result of query validation"""
    validation_id: str
    test_case_id: int
    validation_status: str  # success | failed | timeout
    executed_at: datetime
    execution_time_ms: int
    row_count: int
    column_names: List[str]
    sample_rows: List[Dict[str, Any]]
    error_message: Optional[str] = None
    has_primary_keys: bool
    has_target_attribute: bool
    missing_columns: List[str] = Field(default_factory=list)
    validation_warnings: List[str] = Field(default_factory=list)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DataSourceConfiguration(BaseModel):
    """Configuration for a reusable data source"""
    data_source_id: Optional[str] = None
    source_name: str
    connection_type: str  # postgresql | mysql | oracle | csv | api
    connection_details: Dict[str, Any]  # Will be encrypted in DB
    is_active: bool = True
    test_query: Optional[str] = Field(None, description="Query to test connection")
    
    @validator('connection_details')
    def validate_connection_details(cls, v, values):
        conn_type = values.get('connection_type')
        required_fields = {
            'postgresql': ['host', 'port', 'database', 'username'],
            'mysql': ['host', 'port', 'database', 'username'],
            'oracle': ['host', 'port', 'service_name', 'username'],
            'csv': ['file_path'],
            'api': ['base_url', 'auth_type']
        }
        
        if conn_type in required_fields:
            missing = [f for f in required_fields[conn_type] if f not in v]
            if missing:
                raise ValueError(f"Missing required fields for {conn_type}: {missing}")
        return v


class DataSourceCreateRequest(DataSourceConfiguration):
    """Request to create a new data source"""
    created_by: int


class DataSourceResponse(DataSourceConfiguration):
    """Response for data source"""
    data_source_id: str
    created_by: int
    created_at: datetime
    updated_at: datetime
    last_validated_at: Optional[datetime] = None
    validation_status: Optional[str] = None
    usage_count: int = 0
    
    class Config:
        from_attributes = True


class SaveQueryRequest(BaseModel):
    """Request to save a validated query with evidence"""
    test_case_id: int
    data_source_id: str
    query_text: str
    submission_notes: Optional[str] = None


class QueryExecutionRequest(BaseModel):
    """Request to execute a saved query during test execution"""
    evidence_id: int
    include_all_rows: bool = Field(default=False, description="Return all rows or just sample")
    timeout_seconds: int = Field(default=30, ge=1, le=300) 