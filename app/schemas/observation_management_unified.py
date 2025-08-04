"""
Pydantic schemas for Unified Observation Management APIs
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


# Enums for validation
class SeverityLevelEnum(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IssueTypeEnum(str, Enum):
    DATA_QUALITY = "data_quality"
    PROCESS_FAILURE = "process_failure"
    SYSTEM_ERROR = "system_error"
    COMPLIANCE_GAP = "compliance_gap"


class ObservationRecordStatusEnum(str, Enum):
    DRAFT = "draft"
    PENDING_TESTER_REVIEW = "pending_tester_review"
    TESTER_APPROVED = "tester_approved"
    PENDING_REPORT_OWNER_APPROVAL = "pending_report_owner_approval"
    REPORT_OWNER_APPROVED = "report_owner_approved"
    REJECTED = "rejected"
    RESOLVED = "resolved"
    CLOSED = "closed"


class ReviewDecisionEnum(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_CLARIFICATION = "needs_clarification"


class ResolutionStatusEnum(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DEFERRED = "deferred"


class DetectionMethodEnum(str, Enum):
    AUTO_DETECTED = "auto_detected"
    MANUAL_REVIEW = "manual_review"
    ESCALATION = "escalation"


class TestResultEnum(str, Enum):
    FAIL = "fail"
    INCONCLUSIVE = "inconclusive"


class FrequencyEstimateEnum(str, Enum):
    ISOLATED = "isolated"
    OCCASIONAL = "occasional"
    FREQUENT = "frequent"
    SYSTEMATIC = "systematic"


# ============================================
# Base Schemas
# ============================================

class UserSummary(BaseModel):
    """User summary for relationships"""
    id: int
    name: str
    email: str


class AttributeSummary(BaseModel):
    """Attribute summary for relationships"""
    id: int
    name: str
    description: Optional[str] = None


class LOBSummary(BaseModel):
    """LOB summary for relationships"""
    id: int
    name: str
    description: Optional[str] = None


class PaginationInfo(BaseModel):
    """Pagination information"""
    page: int
    page_size: int
    total_count: int
    total_pages: int
    has_next: bool
    has_previous: bool


# ============================================
# Observation Group Schemas
# ============================================

class ObservationRecordBase(BaseModel):
    """Base observation group schema"""
    group_name: str = Field(..., min_length=1, max_length=255)
    group_description: Optional[str] = Field(None, max_length=1000)
    issue_summary: str = Field(..., min_length=1)
    impact_description: Optional[str] = None
    proposed_resolution: Optional[str] = None
    severity_level: SeverityLevelEnum
    issue_type: IssueTypeEnum


class ObservationRecordCreate(ObservationRecordBase):
    """Schema for creating observation group"""
    phase_id: int = Field(..., gt=0)
    cycle_id: int = Field(..., gt=0)
    report_id: int = Field(..., gt=0)
    attribute_id: int = Field(..., gt=0)
    lob_id: int = Field(..., gt=0)


class ObservationRecordUpdate(BaseModel):
    """Schema for updating observation group"""
    group_name: Optional[str] = Field(None, min_length=1, max_length=255)
    group_description: Optional[str] = Field(None, max_length=1000)
    issue_summary: Optional[str] = Field(None, min_length=1)
    impact_description: Optional[str] = None
    proposed_resolution: Optional[str] = None
    severity_level: Optional[SeverityLevelEnum] = None
    issue_type: Optional[IssueTypeEnum] = None


class ObservationRecordResponse(ObservationRecordBase):
    """Schema for observation group response"""
    id: int
    phase_id: int
    cycle_id: int
    report_id: int
    attribute_id: int
    lob_id: int
    observation_count: int
    status: ObservationRecordStatusEnum
    
    # Tester review fields
    tester_review_status: Optional[ReviewDecisionEnum] = None
    tester_review_notes: Optional[str] = None
    tester_review_score: Optional[int] = Field(None, ge=1, le=100)
    tester_reviewed_by: Optional[int] = None
    tester_reviewed_at: Optional[datetime] = None
    
    # Report owner approval fields
    report_owner_approval_status: Optional[ReviewDecisionEnum] = None
    report_owner_approval_notes: Optional[str] = None
    report_owner_approved_by: Optional[int] = None
    report_owner_approved_at: Optional[datetime] = None
    
    # Clarification fields
    clarification_requested: bool = False
    clarification_request_text: Optional[str] = None
    clarification_response: Optional[str] = None
    clarification_due_date: Optional[datetime] = None
    
    # Resolution fields
    resolution_status: ResolutionStatusEnum
    resolution_approach: Optional[str] = None
    resolution_timeline: Optional[str] = None
    resolution_owner: Optional[int] = None
    resolution_notes: Optional[str] = None
    resolved_by: Optional[int] = None
    resolved_at: Optional[datetime] = None
    
    # Detection fields
    detection_method: DetectionMethodEnum
    detected_by: int
    detected_at: datetime
    
    # Audit fields
    created_at: datetime
    updated_at: datetime
    created_by: int
    updated_by: int
    
    # Related objects
    attribute: Optional[AttributeSummary] = None
    lob: Optional[LOBSummary] = None
    detector: Optional[UserSummary] = None
    tester_reviewer: Optional[UserSummary] = None
    report_owner_approver: Optional[UserSummary] = None
    
    # Optional observations (for detailed view)
    observations: Optional[List['ObservationResponse']] = None

    class Config:
        from_attributes = True


class ObservationRecordList(BaseModel):
    """Schema for observation group list with pagination"""
    groups: List[ObservationRecordResponse]
    pagination: PaginationInfo


# ============================================
# Individual Observation Schemas
# ============================================

class ObservationBase(BaseModel):
    """Base observation schema"""
    observation_title: str = Field(..., min_length=1, max_length=255)
    observation_description: str = Field(..., min_length=1)
    expected_value: Optional[str] = None
    actual_value: Optional[str] = None
    variance_details: Optional[Dict[str, Any]] = None
    test_result: Optional[TestResultEnum] = None
    evidence_files: Optional[Dict[str, Any]] = None
    supporting_documentation: Optional[str] = None
    confidence_level: Optional[float] = Field(None, ge=0.0, le=1.0)
    reproducible: bool = False
    frequency_estimate: Optional[FrequencyEstimateEnum] = None
    business_impact: Optional[str] = None
    technical_impact: Optional[str] = None
    regulatory_impact: Optional[str] = None


class ObservationCreate(ObservationBase):
    """Schema for creating observation"""
    group_id: int = Field(..., gt=0)
    test_execution_id: int = Field(..., gt=0)
    test_case_id: str = Field(..., min_length=1, max_length=255)
    attribute_id: int = Field(..., gt=0)
    sample_id: str = Field(..., min_length=1, max_length=255)
    lob_id: int = Field(..., gt=0)


class ObservationUpdate(BaseModel):
    """Schema for updating observation"""
    observation_title: Optional[str] = Field(None, min_length=1, max_length=255)
    observation_description: Optional[str] = Field(None, min_length=1)
    expected_value: Optional[str] = None
    actual_value: Optional[str] = None
    variance_details: Optional[Dict[str, Any]] = None
    test_result: Optional[TestResultEnum] = None
    evidence_files: Optional[Dict[str, Any]] = None
    supporting_documentation: Optional[str] = None
    confidence_level: Optional[float] = Field(None, ge=0.0, le=1.0)
    reproducible: Optional[bool] = None
    frequency_estimate: Optional[FrequencyEstimateEnum] = None
    business_impact: Optional[str] = None
    technical_impact: Optional[str] = None
    regulatory_impact: Optional[str] = None


class ObservationResponse(ObservationBase):
    """Schema for observation response"""
    id: int
    group_id: int
    test_execution_id: int
    test_case_id: str
    attribute_id: int
    sample_id: str
    lob_id: int
    
    # Audit fields
    created_at: datetime
    updated_at: datetime
    created_by: int
    updated_by: int

    class Config:
        from_attributes = True


class ObservationList(BaseModel):
    """Schema for observation list with pagination"""
    observations: List[ObservationResponse]
    pagination: PaginationInfo


# ============================================
# Review and Approval Schemas
# ============================================

class TesterReviewRequest(BaseModel):
    """Schema for tester review request"""
    review_decision: ReviewDecisionEnum
    review_notes: Optional[str] = Field(None, max_length=1000)
    review_score: Optional[int] = Field(None, ge=1, le=100)

    @validator('review_notes')
    def validate_review_notes(cls, v, values):
        if values.get('review_decision') == ReviewDecisionEnum.NEEDS_CLARIFICATION and not v:
            raise ValueError('Review notes are required when requesting clarification')
        return v


class ReportOwnerApprovalRequest(BaseModel):
    """Schema for report owner approval request"""
    approval_decision: ReviewDecisionEnum
    approval_notes: Optional[str] = Field(None, max_length=1000)

    @validator('approval_notes')
    def validate_approval_notes(cls, v, values):
        if values.get('approval_decision') == ReviewDecisionEnum.NEEDS_CLARIFICATION and not v:
            raise ValueError('Approval notes are required when requesting clarification')
        return v


class ClarificationRequest(BaseModel):
    """Schema for clarification request"""
    clarification_text: str = Field(..., min_length=1, max_length=1000)
    due_date: Optional[datetime] = None

    @validator('due_date')
    def validate_due_date(cls, v):
        if v and v <= datetime.utcnow():
            raise ValueError('Due date must be in the future')
        return v


class ClarificationResponse(BaseModel):
    """Schema for clarification response"""
    clarification_response: str = Field(..., min_length=1, max_length=1000)


class ResolutionStart(BaseModel):
    """Schema for starting resolution"""
    resolution_approach: str = Field(..., min_length=1, max_length=1000)
    resolution_timeline: Optional[str] = Field(None, max_length=500)


class ResolutionComplete(BaseModel):
    """Schema for completing resolution"""
    resolution_notes: str = Field(..., min_length=1, max_length=1000)


# ============================================
# Statistics and Dashboard Schemas
# ============================================

class ObservationStatistics(BaseModel):
    """Schema for observation statistics"""
    total_groups: int
    total_observations: int
    status_distribution: Dict[str, int]
    severity_distribution: Dict[str, int]
    issue_type_distribution: Dict[str, int]
    average_observations_per_group: float


class DetectionStatistics(BaseModel):
    """Schema for detection statistics"""
    total_failed_executions: int
    failed_with_observations: int
    failed_without_observations: int
    detection_coverage: float
    observation_groups: int
    total_observations: int


class DetectionResults(BaseModel):
    """Schema for detection results"""
    processed_count: int
    groups_created: int
    observations_created: int
    errors: List[str]
    phase_id: Optional[int] = None
    cycle_id: Optional[int] = None
    report_id: Optional[int] = None
    detection_timestamp: Optional[str] = None
    detection_user_id: Optional[int] = None


# ============================================
# Filter and Query Schemas
# ============================================

class ObservationRecordFilter(BaseModel):
    """Schema for observation group filtering"""
    phase_id: Optional[int] = None
    cycle_id: Optional[int] = None
    report_id: Optional[int] = None
    status: Optional[ObservationRecordStatusEnum] = None
    severity_level: Optional[SeverityLevelEnum] = None
    assigned_to: Optional[int] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class ObservationFilter(BaseModel):
    """Schema for observation filtering"""
    group_id: Optional[int] = None
    test_result: Optional[TestResultEnum] = None
    frequency_estimate: Optional[FrequencyEstimateEnum] = None
    confidence_level_min: Optional[float] = Field(None, ge=0.0, le=1.0)
    confidence_level_max: Optional[float] = Field(None, ge=0.0, le=1.0)
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)

    @validator('confidence_level_max')
    def validate_confidence_range(cls, v, values):
        if v is not None and values.get('confidence_level_min') is not None:
            if v < values['confidence_level_min']:
                raise ValueError('confidence_level_max must be greater than confidence_level_min')
        return v


# ============================================
# Bulk Operations Schemas
# ============================================

class BulkObservationRecordUpdate(BaseModel):
    """Schema for bulk observation group updates"""
    group_ids: List[int] = Field(..., min_items=1, max_items=100)
    update_data: ObservationRecordUpdate


class BulkTesterReview(BaseModel):
    """Schema for bulk tester review"""
    group_ids: List[int] = Field(..., min_items=1, max_items=50)
    review_data: TesterReviewRequest


class BulkReportOwnerApproval(BaseModel):
    """Schema for bulk report owner approval"""
    group_ids: List[int] = Field(..., min_items=1, max_items=50)
    approval_data: ReportOwnerApprovalRequest


# ============================================
# Detection Job Schemas
# ============================================

class DetectionJobRequest(BaseModel):
    """Schema for detection job request"""
    phase_id: Optional[int] = None
    cycle_id: Optional[int] = None
    report_id: Optional[int] = None
    batch_size: int = Field(100, ge=1, le=1000)
    force_redetection: bool = False


class DetectionJobResponse(BaseModel):
    """Schema for detection job response"""
    job_id: str
    status: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    results: Optional[DetectionResults] = None
    error_message: Optional[str] = None


# ============================================
# Response Schemas
# ============================================

class StandardResponse(BaseModel):
    """Standard API response"""
    success: bool
    message: str
    data: Optional[Any] = None
    errors: Optional[List[str]] = None


class ObservationRecordDetailResponse(BaseModel):
    """Detailed observation group response with observations"""
    group: ObservationRecordResponse
    observations: ObservationList
    statistics: Optional[Dict[str, Any]] = None


class WorkflowStatusResponse(BaseModel):
    """Workflow status response"""
    phase_id: int
    cycle_id: int
    report_id: int
    total_groups: int
    pending_tester_review: int
    pending_report_owner_approval: int
    approved_groups: int
    rejected_groups: int
    resolved_groups: int
    workflow_completion_percentage: float
    next_actions: List[str]
    overdue_reviews: List[int]
    overdue_approvals: List[int]


# ============================================
# Audit and Tracking Schemas
# ============================================

class AuditLogEntry(BaseModel):
    """Audit log entry"""
    id: int
    entity_type: str
    entity_id: int
    action: str
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    performed_by: int
    performed_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class AuditLogResponse(BaseModel):
    """Audit log response with pagination"""
    entries: List[AuditLogEntry]
    pagination: PaginationInfo


# Forward reference resolution
ObservationRecordResponse.model_rebuild()