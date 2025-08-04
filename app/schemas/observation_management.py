"""
Pydantic schemas for Observation Management
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime
from app.models.observation_management import (
    ObservationTypeEnum, ObservationSeverityEnum, ObservationStatusEnum,
    ImpactCategoryEnum, ResolutionStatusEnum
)


# Base schemas
class ObservationManagementPhaseStart(BaseModel):
    """Schema for starting observation management phase"""
    planned_start_date: Optional[datetime] = None
    planned_end_date: Optional[datetime] = None
    observation_deadline: datetime = Field(..., description="Deadline for completing observations")
    observation_strategy: Optional[str] = Field(None, description="Strategy for observation management")
    detection_criteria: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Auto-detection criteria")
    approval_threshold: float = Field(0.7, ge=0.0, le=1.0, description="Confidence threshold for auto-approval")
    instructions: Optional[str] = Field(None, description="Instructions for testers")
    notes: Optional[str] = Field(None, description="Additional notes")
    assigned_testers: Optional[List[int]] = Field(default_factory=list, description="List of assigned tester IDs")

    model_config = ConfigDict(from_attributes=True)


class ObservationManagementPhaseStatus(BaseModel):
    """Schema for observation management phase status"""
    cycle_id: int
    report_id: int
    phase_id: str
    phase_status: str
    observation_deadline: datetime
    days_until_deadline: int
    total_observations: int
    auto_detected_observations: int
    manual_observations: int
    approved_observations: int
    rejected_observations: int
    pending_observations: int
    completion_percentage: float
    detection_rate: float
    approval_rate: float
    average_resolution_time: float
    critical_observations: int
    high_severity_observations: int
    medium_severity_observations: int
    low_severity_observations: int
    can_complete_phase: bool
    completion_requirements: List[str]

    model_config = ConfigDict(from_attributes=True)


class AutoDetectionRequest(BaseModel):
    """Schema for auto-detection request"""
    scan_scope: str = Field("All", description="Scope of the detection scan")
    detection_criteria: Dict[str, Any] = Field(default_factory=dict, description="Detection criteria configuration")
    confidence_threshold: float = Field(0.7, ge=0.0, le=1.0, description="Minimum confidence for detection")
    include_test_executions: bool = Field(True, description="Include test execution data in scan")
    include_sample_data: bool = Field(True, description="Include sample data in scan")

    model_config = ConfigDict(from_attributes=True)


class ObservationCreate(BaseModel):
    """Schema for creating observations"""
    observation_title: str = Field(..., description="Title of the observation")
    observation_description: str = Field(..., description="Detailed description")
    observation_type: ObservationTypeEnum
    severity: ObservationSeverityEnum
    source_test_execution_id: Optional[int] = None
    source_sample_record_id: Optional[str] = None
    source_attribute_id: Optional[int] = None
    detection_method: str = Field("Manual", description="Method used to detect observation")
    detection_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    impact_description: Optional[str] = None
    impact_categories: Optional[List[str]] = Field(default_factory=list)
    financial_impact_estimate: Optional[float] = None
    regulatory_risk_level: Optional[str] = None
    affected_processes: Optional[List[str]] = Field(default_factory=list)
    affected_systems: Optional[List[str]] = Field(default_factory=list)
    evidence_documents: Optional[List[str]] = Field(default_factory=list)
    supporting_data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    screenshots: Optional[List[str]] = Field(default_factory=list)
    related_observations: Optional[List[int]] = Field(default_factory=list)
    assigned_to: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class ObservationResponse(BaseModel):
    """Schema for observation response"""
    observation_id: int
    phase_id: str
    cycle_id: int
    report_id: int
    observation_title: str
    observation_description: str
    observation_type: ObservationTypeEnum
    severity: ObservationSeverityEnum
    status: ObservationStatusEnum
    source_test_execution_id: Optional[int] = None
    source_sample_record_id: Optional[str] = None
    source_attribute_id: Optional[int] = None
    detection_method: Optional[str] = None
    detection_confidence: Optional[float] = None
    impact_description: Optional[str] = None
    financial_impact_estimate: Optional[float] = None
    regulatory_risk_level: Optional[str] = None
    detected_by: Optional[int] = None
    assigned_to: Optional[int] = None
    detected_at: Optional[datetime] = None
    assigned_at: Optional[datetime] = None
    auto_detection_score: Optional[float] = None
    manual_validation_required: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


class AutoDetectionResponse(BaseModel):
    """Schema for auto-detection response"""
    detection_id: str
    observations_detected: int
    detection_confidence_avg: float
    detection_duration_ms: int
    detected_observations: List[ObservationResponse]
    scan_summary: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)


class ImpactAssessmentCreate(BaseModel):
    """Schema for creating impact assessments"""
    impact_category: ImpactCategoryEnum
    impact_severity: str
    impact_likelihood: str
    impact_score: float = Field(..., ge=0.0, le=10.0)
    financial_impact_min: Optional[float] = None
    financial_impact_max: Optional[float] = None
    financial_impact_currency: str = "USD"
    regulatory_requirements_affected: Optional[List[str]] = Field(default_factory=list)
    regulatory_deadlines: Optional[List[str]] = Field(default_factory=list)
    potential_penalties: Optional[float] = None
    process_disruption_level: Optional[str] = None
    system_availability_impact: Optional[str] = None
    resource_requirements: Optional[Dict[str, Any]] = Field(default_factory=dict)
    resolution_time_estimate: Optional[int] = None
    business_disruption_duration: Optional[int] = None
    assessment_method: str = "Manual"
    assessment_confidence: float = Field(0.8, ge=0.0, le=1.0)
    assessment_rationale: Optional[str] = None
    assessment_assumptions: Optional[List[str]] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ImpactAssessmentResponse(BaseModel):
    """Schema for impact assessment response"""
    assessment_id: int
    observation_id: int
    impact_category: ImpactCategoryEnum
    impact_severity: str
    impact_likelihood: str
    impact_score: float
    financial_impact_min: Optional[float] = None
    financial_impact_max: Optional[float] = None
    assessment_method: str
    assessment_confidence: float
    assessed_by: int
    assessed_at: datetime
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ObservationApprovalRequest(BaseModel):
    """Schema for observation approval request"""
    approval_status: str = Field(..., description="Approval status: Approved, Rejected, Needs More Info")
    approver_comments: Optional[str] = None
    approval_rationale: Optional[str] = None
    severity_assessment: Optional[str] = None
    impact_validation: bool = Field(True, description="Whether impact assessment is validated")
    evidence_sufficiency: bool = Field(True, description="Whether evidence is sufficient")
    regulatory_significance: bool = Field(False, description="Whether observation has regulatory significance")
    requires_escalation: bool = Field(False, description="Whether observation requires escalation")
    recommended_action: Optional[str] = None
    priority_level: Optional[str] = None
    estimated_effort: Optional[str] = None
    target_resolution_date: Optional[datetime] = None
    approval_criteria_met: Optional[List[str]] = Field(default_factory=list)
    conditional_approval: bool = Field(False, description="Whether approval is conditional")
    conditions: Optional[List[str]] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ObservationApprovalResponse(BaseModel):
    """Schema for observation approval response"""
    approval_id: int
    observation_id: int
    approval_status: str
    approval_level: str
    approver_comments: Optional[str] = None
    recommended_action: Optional[str] = None
    requires_escalation: bool
    priority_level: Optional[str] = None
    target_resolution_date: Optional[datetime] = None
    approved_by: int
    approved_at: datetime
    escalated_to: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class ResolutionCreate(BaseModel):
    """Schema for creating observation resolutions"""
    resolution_strategy: str
    resolution_description: Optional[str] = None
    resolution_steps: List[str] = Field(default_factory=list)
    success_criteria: List[str] = Field(default_factory=list)
    validation_requirements: List[str] = Field(default_factory=list)
    planned_start_date: Optional[datetime] = None
    planned_completion_date: Optional[datetime] = None
    assigned_resources: Optional[List[str]] = Field(default_factory=list)
    estimated_effort_hours: Optional[int] = None
    budget_allocated: Optional[float] = None
    implemented_controls: Optional[List[str]] = Field(default_factory=list)
    process_changes: Optional[List[str]] = Field(default_factory=list)
    system_changes: Optional[List[str]] = Field(default_factory=list)
    documentation_updates: Optional[List[str]] = Field(default_factory=list)
    training_requirements: Optional[List[str]] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ResolutionResponse(BaseModel):
    """Schema for resolution response"""
    resolution_id: int
    observation_id: int
    resolution_strategy: str
    resolution_status: ResolutionStatusEnum
    progress_percentage: float
    current_step: Optional[str] = None
    planned_start_date: Optional[datetime] = None
    planned_completion_date: Optional[datetime] = None
    actual_start_date: Optional[datetime] = None
    actual_completion_date: Optional[datetime] = None
    estimated_effort_hours: Optional[int] = None
    actual_effort_hours: Optional[int] = None
    budget_allocated: Optional[float] = None
    budget_spent: Optional[float] = None
    resolution_owner: Optional[int] = None
    created_by: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ObservationAnalytics(BaseModel):
    """Schema for observation analytics"""
    cycle_id: int
    report_id: int
    phase_id: str
    total_observations: int
    detection_methods_breakdown: Dict[str, int]
    type_distribution: Dict[str, int]
    severity_distribution: Dict[str, int]
    status_distribution: Dict[str, int]
    average_detection_time: float
    average_approval_time: float
    average_resolution_time: float
    detection_accuracy: float
    total_financial_impact: float
    average_financial_impact: float
    financial_impact_by_category: Dict[str, float]
    observations_by_day: List[Dict[str, Any]]
    resolution_timeline: List[Dict[str, Any]]
    approval_rate: float
    escalation_rate: float
    resolution_success_rate: float

    model_config = ConfigDict(from_attributes=True)


class ObservationManagementPhaseComplete(BaseModel):
    """Schema for completing observation management phase"""
    completion_notes: Optional[str] = None
    override_validation: bool = Field(False, description="Override completion validation requirements")
    override_reason: Optional[str] = Field(None, description="Reason for overriding validation")

    model_config = ConfigDict(from_attributes=True)


class ObservationManagementAuditLog(BaseModel):
    """Schema for observation management audit logs"""
    log_id: int
    cycle_id: int
    report_id: int
    phase_id: Optional[str] = None
    observation_id: Optional[int] = None
    action: str
    entity_type: str
    entity_id: Optional[str] = None
    performed_by: int
    performed_at: datetime
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    changes_summary: Optional[str] = None
    notes: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    execution_time_ms: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class ObservationBatchReviewRequest(BaseModel):
    """Request schema for batch reviewing observations"""
    observation_ids: List[int]
    approval_status: str  # "Approved" or "Rejected"
    comments: Optional[str] = None
    rationale: Optional[str] = None
    
    @field_validator('approval_status')
    def validate_approval_status(cls, v):
        if v not in ["Approved", "Rejected"]:
            raise ValueError("approval_status must be 'Approved' or 'Rejected'")
        return v 