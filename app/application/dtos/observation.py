"""
Observation Management DTOs for clean architecture
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ObservationTypeEnum(str, Enum):
    """Types of observations"""
    DATA_QUALITY = "Data Quality"
    DOCUMENTATION = "Documentation"
    PROCESS_CONTROL = "Process Control"
    SYSTEM_CONTROL = "System Control"
    COMPLIANCE = "Compliance"
    OTHER = "Other"


class ObservationSeverityEnum(str, Enum):
    """Severity levels for observations"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFORMATIONAL = "INFORMATIONAL"


class ObservationStatusEnum(str, Enum):
    """Status of observations"""
    DETECTED = "Detected"
    UNDER_REVIEW = "Under Review"
    CONFIRMED = "Confirmed"
    DISPUTED = "Disputed"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    IN_REMEDIATION = "In Remediation"
    RESOLVED = "Resolved"
    CLOSED = "Closed"


class ImpactCategoryEnum(str, Enum):
    """Impact categories"""
    FINANCIAL = "Financial"
    REGULATORY = "Regulatory"
    OPERATIONAL = "Operational"
    REPUTATIONAL = "Reputational"
    STRATEGIC = "Strategic"


class ResolutionStatusEnum(str, Enum):
    """Resolution status"""
    PENDING = "Pending"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    VERIFIED = "Verified"


class ObservationCreateDTO(BaseModel):
    """DTO for creating an observation"""
    observation_title: str = Field(..., min_length=5, max_length=200)
    observation_description: str = Field(..., min_length=10, max_length=2000)
    observation_type: ObservationTypeEnum
    severity: ObservationSeverityEnum
    source_attribute_id: Optional[int] = None
    source_sample_id: Optional[str] = None
    test_execution_id: Optional[str] = None
    evidence_urls: Optional[List[str]] = []
    suggested_action: Optional[str] = None
    financial_impact_estimate: Optional[float] = None
    affected_records_count: Optional[int] = None
    grouping_key: Optional[str] = None


class ObservationResponseDTO(BaseModel):
    """DTO for observation response"""
    observation_id: str
    phase_id: str
    cycle_id: int
    report_id: int
    observation_number: str
    observation_title: str
    observation_description: str
    observation_type: ObservationTypeEnum
    severity: ObservationSeverityEnum
    status: ObservationStatusEnum
    source_attribute_id: Optional[int]
    source_sample_id: Optional[str]
    test_execution_id: Optional[str]
    grouped_count: int
    supporting_data: Optional[Dict[str, Any]] = None
    created_by: int
    created_at: datetime
    updated_at: datetime
    submitted_at: Optional[datetime]
    reviewed_by: Optional[int]
    reviewed_at: Optional[datetime]
    resolution_status: Optional[ResolutionStatusEnum]


class ObservationUpdateDTO(BaseModel):
    """DTO for updating an observation"""
    observation_title: Optional[str] = Field(None, min_length=5, max_length=200)
    observation_description: Optional[str] = Field(None, min_length=10, max_length=2000)
    severity: Optional[ObservationSeverityEnum] = None
    suggested_action: Optional[str] = None
    financial_impact_estimate: Optional[float] = None
    affected_records_count: Optional[int] = None


class ImpactAssessmentCreateDTO(BaseModel):
    """DTO for creating impact assessment"""
    impact_category: ImpactCategoryEnum
    impact_description: str
    estimated_financial_impact: Optional[float] = None
    affected_users_count: Optional[int] = None
    regulatory_implications: Optional[str] = None
    remediation_timeline_days: Optional[int] = None
    remediation_cost_estimate: Optional[float] = None


class ImpactAssessmentResponseDTO(BaseModel):
    """DTO for impact assessment response"""
    assessment_id: str
    observation_id: str
    impact_category: ImpactCategoryEnum
    impact_description: str
    estimated_financial_impact: Optional[float]
    affected_users_count: Optional[int]
    regulatory_implications: Optional[str]
    remediation_timeline_days: Optional[int]
    remediation_cost_estimate: Optional[float]
    assessed_by: int
    assessed_at: datetime


class ObservationApprovalRequestDTO(BaseModel):
    """DTO for observation approval request"""
    action: str = Field(..., pattern="^(approve|reject)$")
    review_notes: Optional[str] = None
    require_remediation: bool = False
    target_resolution_date: Optional[datetime] = None


class ObservationApprovalResponseDTO(BaseModel):
    """DTO for observation approval response"""
    approval_id: str
    observation_id: str
    reviewed_by: int
    review_decision: str
    review_notes: Optional[str]
    reviewed_at: datetime
    require_remediation: bool
    target_resolution_date: Optional[datetime]


class ObservationBatchReviewRequestDTO(BaseModel):
    """DTO for batch review of observations"""
    observation_ids: List[str]
    action: str = Field(..., pattern="^(approve|reject)$")
    review_notes: Optional[str] = None
    require_remediation: bool = False
    target_resolution_date: Optional[datetime] = None


class ResolutionCreateDTO(BaseModel):
    """DTO for creating resolution"""
    resolution_description: str
    resolution_type: str = Field(..., pattern="^(corrected|accepted_risk|process_change|system_fix|other)$")
    implemented_by: Optional[str] = None
    implementation_date: Optional[datetime] = None
    verification_method: Optional[str] = None
    supporting_documents: Optional[List[str]] = []


class ResolutionResponseDTO(BaseModel):
    """DTO for resolution response"""
    resolution_id: str
    observation_id: str
    resolution_description: str
    resolution_type: str
    resolution_status: ResolutionStatusEnum
    implemented_by: Optional[str]
    implementation_date: Optional[datetime]
    verified_by: Optional[int]
    verified_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class ObservationPhaseStartDTO(BaseModel):
    """DTO for starting observation phase"""
    phase_notes: Optional[str] = None


class ObservationPhaseStatusDTO(BaseModel):
    """DTO for observation phase status"""
    phase_id: str
    cycle_id: int
    report_id: int
    phase_status: str
    total_observations: int
    observations_by_status: Dict[str, int]
    observations_by_severity: Dict[str, int]
    observations_by_type: Dict[str, int]
    can_complete: bool
    completion_requirements: List[str]


class ObservationPhaseCompleteDTO(BaseModel):
    """DTO for completing observation phase"""
    completion_notes: Optional[str] = None
    override_checks: bool = False


class ObservationAnalyticsDTO(BaseModel):
    """DTO for observation analytics"""
    total_observations: int
    by_status: Dict[str, int]
    by_severity: Dict[str, int]
    by_type: Dict[str, int]
    average_resolution_time_days: Optional[float]
    grouping_effectiveness: Dict[str, Any]
    top_issues: List[Dict[str, Any]]
    trend_analysis: Dict[str, Any]


class AutoDetectionRequestDTO(BaseModel):
    """DTO for auto-detection request"""
    include_test_failures: bool = True
    severity_threshold: Optional[ObservationSeverityEnum] = None