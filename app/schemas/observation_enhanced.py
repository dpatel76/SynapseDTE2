"""
Enhanced Observation Management Schemas
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ObservationRating(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class ObservationApprovalStatus(str, Enum):
    PENDING_REVIEW = "Pending Review"
    PENDING_REPORT_OWNER_APPROVAL = "Pending Report Owner Approval"
    PENDING_DATA_EXECUTIVE_APPROVAL = "Pending Data Executive Approval"
    APPROVED_BY_REPORT_OWNER = "Approved by Report Owner"
    APPROVED_BY_DATA_EXECUTIVE = "Approved by Data Executive"
    FULLY_APPROVED = "Fully Approved"
    REJECTED_BY_REPORT_OWNER = "Rejected by Report Owner"
    REJECTED_BY_DATA_EXECUTIVE = "Rejected by Data Executive"
    NEEDS_CLARIFICATION = "Needs Clarification"
    FINALIZED = "Finalized"


class DocumentRevisionStatus(str, Enum):
    PENDING_UPLOAD = "Pending Upload"
    UPLOADED = "Uploaded"
    REVIEWED = "Reviewed"


# Document Revision Schemas
class DocumentRevisionCreate(BaseModel):
    test_case_id: int
    revision_reason: str
    
    model_config = ConfigDict(from_attributes=True)


class DocumentRevisionUpload(BaseModel):
    document_id: int
    upload_notes: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class DocumentRevisionReview(BaseModel):
    review_notes: str
    status: DocumentRevisionStatus
    
    model_config = ConfigDict(from_attributes=True)


class DocumentRevisionResponse(BaseModel):
    revision_id: int
    test_case_id: int
    document_id: Optional[int]
    revision_number: int
    revision_reason: str
    requested_by: int
    requested_at: datetime
    uploaded_by: Optional[int]
    uploaded_at: Optional[datetime]
    upload_notes: Optional[str]
    previous_document_id: Optional[int]
    status: str
    reviewed_by: Optional[int]
    reviewed_at: Optional[datetime]
    review_notes: Optional[str]
    
    model_config = ConfigDict(from_attributes=True)


# Observation Group Schemas
class ObservationRecordCreate(BaseModel):
    attribute_id: int
    issue_type: str
    rating: Optional[ObservationRating] = None
    
    model_config = ConfigDict(from_attributes=True)


class ObservationRecordUpdate(BaseModel):
    rating: Optional[ObservationRating] = None
    
    model_config = ConfigDict(from_attributes=True)


class ObservationRecordApproval(BaseModel):
    approved: bool
    comments: str
    
    model_config = ConfigDict(from_attributes=True)


class ObservationRecordResponse(BaseModel):
    group_id: int
    cycle_id: int
    report_id: int
    attribute_id: int
    issue_type: str
    first_detected_at: datetime
    last_updated_at: datetime
    total_test_cases: int
    total_samples: int
    rating: Optional[ObservationRating]
    approval_status: ObservationApprovalStatus
    report_owner_approved: bool
    report_owner_approved_by: Optional[int]
    report_owner_approved_at: Optional[datetime]
    report_owner_comments: Optional[str]
    data_executive_approved: bool
    data_executive_approved_by: Optional[int]
    data_executive_approved_at: Optional[datetime]
    data_executive_comments: Optional[str]
    finalized: bool
    finalized_by: Optional[int]
    finalized_at: Optional[datetime]
    observations: Optional[List['ObservationResponse']] = []
    clarifications: Optional[List['ObservationClarificationResponse']] = []
    
    model_config = ConfigDict(from_attributes=True)


# Observation Schemas
class ObservationCreate(BaseModel):
    test_execution_id: int
    test_case_id: int
    sample_id: int
    attribute_id: int
    issue_type: str
    description: str
    evidence_files: Optional[List[str]] = []
    
    model_config = ConfigDict(from_attributes=True)


class ObservationResponse(BaseModel):
    observation_id: int
    group_id: int
    test_execution_id: int
    test_case_id: int
    sample_id: int
    description: str
    evidence_files: Optional[List[str]]
    created_by: int
    created_at: datetime
    status: str
    
    model_config = ConfigDict(from_attributes=True)


# Clarification Schemas
class ObservationClarificationCreate(BaseModel):
    clarification_text: str
    supporting_documents: Optional[List[str]] = []
    
    model_config = ConfigDict(from_attributes=True)


class ObservationClarificationResponse(BaseModel):
    clarification_id: int
    group_id: int
    clarification_text: str
    supporting_documents: Optional[List[str]]
    requested_by_role: str
    requested_by_user_id: int
    requested_at: datetime
    response_text: Optional[str]
    response_documents: Optional[List[str]]
    responded_by: Optional[int]
    responded_at: Optional[datetime]
    status: str
    
    model_config = ConfigDict(from_attributes=True)


class ClarificationResponse(BaseModel):
    response_text: str
    response_documents: Optional[List[str]] = []
    
    model_config = ConfigDict(from_attributes=True)


# Test Report Phase Schemas
class TestReportPhaseCreate(BaseModel):
    include_executive_summary: bool = True
    include_phase_artifacts: bool = True
    include_detailed_observations: bool = True
    include_metrics_dashboard: bool = True
    report_title: Optional[str] = None
    report_period: Optional[str] = None
    regulatory_references: Optional[List[str]] = []
    
    model_config = ConfigDict(from_attributes=True)


class TestReportPhaseResponse(BaseModel):
    phase_id: str
    cycle_id: int
    report_id: int
    started_at: datetime
    completed_at: Optional[datetime]
    include_executive_summary: bool
    include_phase_artifacts: bool
    include_detailed_observations: bool
    include_metrics_dashboard: bool
    report_title: Optional[str]
    report_period: Optional[str]
    regulatory_references: Optional[List[str]]
    final_report_document_id: Optional[int]
    report_generated_at: Optional[datetime]
    report_approved_by: Optional[List[int]]
    status: str
    report_sections: Optional[List['TestReportSectionResponse']] = []
    
    model_config = ConfigDict(from_attributes=True)


class TestReportSectionCreate(BaseModel):
    section_name: str
    section_order: int
    section_type: str  # Summary, PhaseDetail, Metrics, Observations
    content_text: Optional[str] = None
    content_data: Optional[Dict[str, Any]] = None
    artifacts: Optional[List[str]] = []
    metrics_summary: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(from_attributes=True)


class TestReportSectionResponse(BaseModel):
    section_id: int
    phase_id: str
    section_name: str
    section_order: int
    section_type: str
    content_text: Optional[str]
    content_data: Optional[Dict[str, Any]]
    artifacts: Optional[List[str]]
    metrics_summary: Optional[Dict[str, Any]]
    
    model_config = ConfigDict(from_attributes=True)


# Summary schemas for dashboards
class ObservationPhaseSummary(BaseModel):
    total_test_cases_reviewed: int
    total_documents_sent_back: int
    total_observation_groups: int
    observations_by_rating: Dict[str, int]
    observations_by_status: Dict[str, int]
    pending_approvals: int
    finalized_observations: int
    
    model_config = ConfigDict(from_attributes=True)


class TestReportPhaseSummary(BaseModel):
    report_status: str
    total_phases_completed: int
    total_observations: int
    high_risk_observations: int
    total_test_cases_executed: int
    test_coverage_percentage: float
    key_metrics: Dict[str, Any]
    
    model_config = ConfigDict(from_attributes=True)


# Forward references
ObservationRecordResponse.model_rebuild()
TestReportPhaseResponse.model_rebuild()