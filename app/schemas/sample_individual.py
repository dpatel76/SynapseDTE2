"""
Individual Sample schemas
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class SampleStatusEnum(str, Enum):
    DRAFT = "Draft"
    SUBMITTED = "Submitted"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    REVISION_REQUIRED = "Revision Required"


class TesterDecisionEnum(str, Enum):
    INCLUDE = "Include"
    EXCLUDE = "Exclude"
    REVIEW_REQUIRED = "Review Required"


class SampleTypeEnum(str, Enum):
    POPULATION = "Population Sample"
    TARGETED = "Targeted Sample"
    EXCEPTION = "Exception Sample"
    CONTROL = "Control Sample"
    RISK_BASED = "Risk-Based Sample"


class GenerationMethodEnum(str, Enum):
    LLM_GENERATED = "LLM Generated"
    MANUAL_ENTRY = "Manual Entry"
    UPLOADED = "Uploaded"
    HYBRID = "Hybrid"


class SubmissionStatusEnum(str, Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    REVISION_REQUIRED = "Revision Required"


class FeedbackTypeEnum(str, Enum):
    APPROVAL = "Approval"
    REJECTION = "Rejection"
    CHANGE_REQUEST = "Change Request"
    COMMENT = "Comment"


# Base schemas
class SampleBase(BaseModel):
    sample_identifier: str
    primary_key_value: str
    sample_name: Optional[str] = None
    sample_description: Optional[str] = None
    sample_type: SampleTypeEnum
    generation_method: GenerationMethodEnum
    sample_data: Dict[str, Any]
    risk_score: Optional[float] = None
    risk_factors: Optional[Dict[str, Any]] = None
    selection_rationale: Optional[str] = None
    sequence_number: Optional[int] = None
    data_source_info: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class SampleCreate(SampleBase):
    """Schema for creating a new sample"""
    pass


class SampleUpdate(BaseModel):
    """Schema for updating a sample"""
    sample_name: Optional[str] = None
    sample_description: Optional[str] = None
    sample_data: Optional[Dict[str, Any]] = None
    risk_score: Optional[float] = None
    risk_factors: Optional[Dict[str, Any]] = None
    selection_rationale: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class TesterDecisionUpdate(BaseModel):
    """Schema for updating tester decision on a sample"""
    tester_decision: TesterDecisionEnum
    tester_decision_rationale: Optional[str] = None


class SampleResponse(SampleBase):
    """Schema for sample response"""
    sample_id: str
    cycle_id: int
    report_id: int
    tester_decision: TesterDecisionEnum
    tester_decision_rationale: Optional[str] = None
    tester_decision_by: Optional[int] = None
    tester_decision_at: Optional[datetime] = None
    status: SampleStatusEnum
    created_by: int
    created_at: datetime
    updated_by: Optional[int] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True


class SampleListResponse(BaseModel):
    """Response schema for listing samples"""
    samples: List[SampleResponse]
    total: int
    included: int
    excluded: int
    review_required: int


# Sample generation schemas
class SampleGenerationRequest(BaseModel):
    """Request schema for generating samples"""
    target_sample_size: int = Field(..., ge=1, le=1000)
    sample_type: SampleTypeEnum
    selection_criteria: Optional[Dict[str, Any]] = None
    risk_focus_areas: Optional[List[str]] = None
    exclude_criteria: Optional[Dict[str, Any]] = None
    include_edge_cases: bool = True


class SampleGenerationResponse(BaseModel):
    """Response schema for sample generation"""
    samples_generated: int
    samples: List[SampleResponse]
    generation_rationale: str
    llm_model_used: Optional[str] = None
    confidence_score: Optional[float] = None


# Sample submission schemas
class SampleSubmissionCreate(BaseModel):
    """Schema for creating a sample submission"""
    submission_name: str
    submission_notes: Optional[str] = None
    sample_ids: List[str]  # List of sample IDs to include in submission


class SampleSubmissionResponse(BaseModel):
    """Schema for sample submission response"""
    submission_id: str
    cycle_id: int
    report_id: int
    submission_name: str
    submission_notes: Optional[str] = None
    total_samples: int
    included_samples: int
    excluded_samples: int
    status: SubmissionStatusEnum
    submitted_by: int
    submitted_at: datetime
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    samples: Optional[List[SampleResponse]] = None
    
    class Config:
        orm_mode = True


# Feedback schemas
class SampleFeedbackCreate(BaseModel):
    """Schema for creating feedback"""
    sample_id: Optional[str] = None  # None for submission-level feedback
    feedback_type: FeedbackTypeEnum
    feedback_text: str
    requested_changes: Optional[Dict[str, Any]] = None
    is_blocking: bool = False


class SampleFeedbackUpdate(BaseModel):
    """Schema for updating feedback resolution"""
    is_resolved: bool
    resolution_notes: Optional[str] = None


class SampleFeedbackResponse(BaseModel):
    """Schema for feedback response"""
    feedback_id: str
    submission_id: str
    sample_id: Optional[str] = None
    feedback_type: FeedbackTypeEnum
    feedback_text: str
    requested_changes: Optional[Dict[str, Any]] = None
    is_blocking: bool
    is_resolved: bool
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[int] = None
    resolution_notes: Optional[str] = None
    created_by: int
    created_at: datetime
    
    class Config:
        orm_mode = True


class FeedbackListResponse(BaseModel):
    """Response schema for listing feedback"""
    feedbacks: List[SampleFeedbackResponse]
    total: int
    unresolved: int
    blocking: int


# Bulk operations
class BulkTesterDecisionUpdate(BaseModel):
    """Schema for bulk updating tester decisions"""
    sample_ids: List[str]
    tester_decision: TesterDecisionEnum
    tester_decision_rationale: Optional[str] = None


class BulkSampleCreate(BaseModel):
    """Schema for bulk creating samples"""
    samples: List[SampleCreate]


# Analytics
class SampleAnalytics(BaseModel):
    """Analytics for samples in a report"""
    total_samples: int
    by_status: Dict[str, int]
    by_tester_decision: Dict[str, int]
    by_sample_type: Dict[str, int]
    by_generation_method: Dict[str, int]
    average_risk_score: Optional[float] = None
    submissions: int
    pending_submissions: int
    approved_submissions: int