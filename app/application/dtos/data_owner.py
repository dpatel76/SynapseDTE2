"""
Data Owner (Data Provider Identification) DTOs for clean architecture
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class AssignmentStatusEnum(str, Enum):
    """Assignment status values"""
    ASSIGNED = "Assigned"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    OVERDUE = "Overdue"


class EscalationLevelEnum(str, Enum):
    """Escalation levels"""
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    L4 = "L4"


class DataProviderPhaseStartDTO(BaseModel):
    """DTO for starting data provider phase"""
    planned_start_date: Optional[datetime] = None
    planned_end_date: Optional[datetime] = None
    notes: Optional[str] = None


class AttributeLOBAssignmentDTO(BaseModel):
    """DTO for attribute LOB assignment"""
    attribute_id: int
    lob_ids: List[int]
    assignment_rationale: Optional[str] = None


class LOBAssignmentSubmissionDTO(BaseModel):
    """DTO for LOB assignment submission"""
    assignments: List[AttributeLOBAssignmentDTO]
    confirm_submission: bool = False
    submission_notes: Optional[str] = None


class DataOwnerAssignmentRequestDTO(BaseModel):
    """DTO for data owner assignment request"""
    attribute_id: str  # Attribute ID as string (should be numeric)
    attribute_name: Optional[str] = None  # Attribute name for fallback matching
    data_owner_id: int
    assignment_notes: Optional[str] = None
    use_historical_assignment: bool = False


class CDOAssignmentSubmissionDTO(BaseModel):
    """DTO for CDO assignment submission"""
    assignments: List[DataOwnerAssignmentRequestDTO]
    submission_notes: Optional[str] = None


class DataProviderPhaseStatusDTO(BaseModel):
    """DTO for data provider phase status"""
    cycle_id: int
    report_id: int
    phase_status: str
    total_attributes: int
    scoped_attributes: int  # Non-PK scoped attributes count
    total_samples: int      # Total approved samples count
    total_lobs: int = 0     # Total unique LOBs from approved samples
    assigned_data_providers: int = 0  # Number of assigned data providers
    total_data_providers: int = 0     # Total available data providers
    attributes_with_lob_assignments: int
    attributes_with_data_owners: int
    pending_cdo_assignments: int
    overdue_assignments: int
    can_submit_lob_assignments: bool
    can_complete_phase: bool
    completion_requirements: List[str]
    started_at: Optional[datetime] = None  # Phase start date


class HistoricalAssignmentSuggestionDTO(BaseModel):
    """DTO for historical assignment suggestion"""
    attribute_name: str
    data_owner_id: int
    data_owner_name: str
    last_assigned_date: datetime
    assignment_frequency: int
    success_rate: float


class HistoricalAssignmentResponseDTO(BaseModel):
    """DTO for historical assignment response"""
    cycle_id: int
    report_id: int
    suggestions: List[HistoricalAssignmentSuggestionDTO]
    total_suggestions: int


class AttributeAssignmentStatusDTO(BaseModel):
    """DTO for attribute assignment status"""
    attribute_id: str  # UUID as string
    attribute_name: str
    is_primary_key: bool
    assigned_lobs: List[Dict[str, Any]]
    data_owner_id: Optional[int]
    data_owner_name: Optional[str]
    assigned_by: Optional[int]
    assigned_at: Optional[datetime]
    status: AssignmentStatusEnum
    assignment_notes: Optional[str]
    is_overdue: bool
    sla_deadline: Optional[datetime]
    hours_remaining: Optional[float]


class AssignmentMatrixDTO(BaseModel):
    """DTO for assignment matrix"""
    cycle_id: int
    report_id: int
    assignments: List[AttributeAssignmentStatusDTO]
    data_owners: List[Dict[str, Any]]
    lob_summary: Dict[str, int]
    cdo_summary: Dict[str, Any]
    status_summary: Dict[str, int]


class SLAViolationDTO(BaseModel):
    """DTO for SLA violation"""
    assignment_id: int
    attribute_id: int
    attribute_name: str
    cdo_id: int
    cdo_name: str
    lob_name: str
    assignment_deadline: datetime
    hours_overdue: float
    escalation_level: EscalationLevelEnum


class EscalationEmailRequestDTO(BaseModel):
    """DTO for escalation email request"""
    violation_ids: List[int]
    escalation_level: EscalationLevelEnum
    send_to_report_owner: bool = True
    cc_cdo: bool = True
    custom_message: Optional[str] = None


class EscalationEmailResponseDTO(BaseModel):
    """DTO for escalation email response"""
    email_sent: bool
    recipients: List[str]
    violations_escalated: int
    escalation_level: EscalationLevelEnum
    sent_at: datetime


class DataProviderPhaseCompleteDTO(BaseModel):
    """DTO for completing data provider phase"""
    confirm_completion: bool
    completion_notes: Optional[str] = None


class DataOwnerAssignmentDTO(BaseModel):
    """DTO for data owner assignment"""
    assignment_id: int
    cycle_id: int
    report_id: int
    attribute_id: int
    attribute_name: str
    attribute_description: Optional[str]
    data_owner_id: int
    data_owner_name: str
    data_owner_email: str
    lob_name: str
    assigned_at: datetime
    status: str


class CDODashboardMetricsDTO(BaseModel):
    """DTO for CDO dashboard metrics"""
    total_assignments: int
    completed_assignments: int
    pending_assignments: int
    overdue_assignments: int
    compliance_rate: float


class CDOWorkflowStatusDTO(BaseModel):
    """DTO for CDO workflow status"""
    cycle_id: int
    cycle_name: str
    report_id: int
    report_name: str
    phase_status: str
    attributes_pending: int
    attributes_completed: int
    last_updated: datetime


class CDOAssignmentActivityDTO(BaseModel):
    """DTO for CDO assignment activity"""
    activity_date: datetime
    activity_type: str
    attribute_name: str
    data_owner_name: str
    cycle_name: str
    report_name: str


class CDODashboardResponseDTO(BaseModel):
    """DTO for CDO dashboard response"""
    overview_metrics: CDODashboardMetricsDTO
    workflow_status: List[CDOWorkflowStatusDTO]
    recent_activity: List[CDOAssignmentActivityDTO]
    assignment_analytics: Dict[str, Any]
    lob_overview: Dict[str, Any]


class AuditLogEntryDTO(BaseModel):
    """DTO for audit log entry"""
    assignment_id: int
    attribute_id: int
    action: str
    performed_by: int
    performed_at: datetime
    old_values: Optional[Dict[str, Any]]
    new_values: Optional[Dict[str, Any]]
    notes: Optional[str]


class DataOwnerAssignmentAuditLogDTO(BaseModel):
    """DTO for data owner assignment audit log"""
    cycle_id: int
    report_id: int
    audit_entries: List[AuditLogEntryDTO]
    total_entries: int