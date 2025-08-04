"""
Data Provider Identification phase schemas
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class AssignmentStatus(str, Enum):
    """Assignment status enumeration"""
    ASSIGNED = "Assigned"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    OVERDUE = "Overdue"


class EscalationLevel(str, Enum):
    """Escalation level enumeration"""
    NONE = "None"
    LEVEL_1 = "Level 1"
    LEVEL_2 = "Level 2"
    LEVEL_3 = "Level 3"


# Data Provider ID Phase Start
class DataProviderPhaseStart(BaseModel):
    """Schema for starting data provider identification phase"""
    planned_start_date: Optional[datetime] = Field(None, description="Planned start date")
    planned_end_date: Optional[datetime] = Field(None, description="Planned end date")
    notes: Optional[str] = Field(None, description="Data provider phase notes")


# LOB Assignment Schemas
class AttributeLOBAssignment(BaseModel):
    """Schema for assigning LOBs to an attribute"""
    attribute_id: int = Field(..., description="Attribute ID")
    lob_ids: List[int] = Field(..., description="List of LOB IDs assigned to attribute")
    assignment_rationale: Optional[str] = Field(None, description="Rationale for LOB assignment")


class LOBAssignmentSubmission(BaseModel):
    """Schema for submitting all LOB assignments"""
    assignments: List[AttributeLOBAssignment] = Field(..., description="List of LOB assignments")
    submission_notes: Optional[str] = Field(None, description="Overall submission notes")
    confirm_submission: bool = Field(..., description="Confirm submission to CDOs")


# CDO Notification and Assignment Schemas
class CDONotificationData(BaseModel):
    """Schema for CDO notification data"""
    cdo_id: int = Field(..., description="CDO user ID")
    lob_id: int = Field(..., description="LOB ID")
    attributes: List[Dict[str, Any]] = Field(..., description="Attributes requiring data provider assignment")
    assignment_deadline: datetime = Field(..., description="Assignment deadline")
    sla_hours: int = Field(default=24, description="SLA in hours")


class DataProviderAssignmentRequest(BaseModel):
    """Schema for CDO data provider assignment"""
    attribute_id: int = Field(..., description="Attribute ID")
    data_owner_id: int = Field(..., description="Data Provider user ID")
    assignment_notes: Optional[str] = Field(None, description="Assignment notes or instructions")
    use_historical_assignment: bool = Field(default=False, description="Using historical assignment")


class CDOAssignmentSubmission(BaseModel):
    """Schema for CDO submitting all assignments"""
    assignments: List[DataProviderAssignmentRequest] = Field(..., description="List of data provider assignments")
    submission_notes: Optional[str] = Field(None, description="Overall submission notes")


# Historical Assignment Schemas
class HistoricalAssignment(BaseModel):
    """Schema for historical assignment suggestion"""
    attribute_name: str = Field(..., description="Attribute name")
    data_owner_id: int = Field(..., description="Previously assigned data provider ID")
    data_owner_name: str = Field(..., description="Data provider name")
    last_assigned_date: datetime = Field(..., description="Last assignment date")
    assignment_frequency: int = Field(..., description="Number of times assigned")
    success_rate: float = Field(..., description="Success rate percentage")


class HistoricalAssignmentResponse(BaseModel):
    """Schema for historical assignment response"""
    cycle_id: int = Field(..., description="Cycle ID")
    report_id: int = Field(..., description="Report ID")
    suggestions: List[HistoricalAssignment] = Field(..., description="Historical assignment suggestions")
    total_suggestions: int = Field(..., description="Total number of suggestions")


# Assignment Status and Progress Schemas
class AttributeAssignmentStatus(BaseModel):
    """Schema for individual attribute assignment status"""
    attribute_id: int = Field(..., description="Attribute ID")
    attribute_name: str = Field(..., description="Attribute name")
    is_primary_key: bool = Field(default=False, description="Is this a primary key attribute")
    assigned_lobs: List[Dict[str, Any]] = Field(..., description="Assigned LOBs")
    data_owner_id: Optional[int] = Field(None, description="Assigned data provider ID")
    data_owner_name: Optional[str] = Field(None, description="Data provider name")
    assigned_by: Optional[int] = Field(None, description="CDO who made assignment")
    assigned_at: Optional[datetime] = Field(None, description="Assignment timestamp")
    status: AssignmentStatus = Field(..., description="Assignment status")
    assignment_notes: Optional[str] = Field(None, description="Assignment notes")
    is_overdue: bool = Field(default=False, description="Is assignment overdue")
    sla_deadline: Optional[datetime] = Field(None, description="SLA deadline")
    hours_remaining: Optional[float] = Field(None, description="Hours remaining until SLA breach")


class DataProviderPhaseStatus(BaseModel):
    """Schema for data provider phase status"""
    cycle_id: int = Field(..., description="Cycle ID")
    report_id: int = Field(..., description="Report ID")
    phase_status: str = Field(..., description="Phase status")
    total_attributes: int = Field(..., description="Total scoped attributes")
    attributes_with_lob_assignments: int = Field(..., description="Attributes with LOB assignments")
    attributes_with_data_owners: int = Field(..., description="Attributes with assigned data providers")
    pending_cdo_assignments: int = Field(..., description="Pending CDO assignments")
    overdue_assignments: int = Field(..., description="Overdue assignments")
    can_submit_lob_assignments: bool = Field(..., description="Can submit LOB assignments")
    can_complete_phase: bool = Field(..., description="Can complete data provider phase")
    completion_requirements: List[str] = Field(..., description="Requirements to complete phase")


# SLA and Escalation Schemas
class SLAViolation(BaseModel):
    """Schema for SLA violation"""
    assignment_id: int = Field(..., description="Assignment ID")
    attribute_id: int = Field(..., description="Attribute ID")
    attribute_name: str = Field(..., description="Attribute name")
    cdo_id: int = Field(..., description="CDO user ID")
    cdo_name: str = Field(..., description="CDO name")
    lob_name: str = Field(..., description="LOB name")
    assignment_deadline: datetime = Field(..., description="Original deadline")
    hours_overdue: float = Field(..., description="Hours overdue")
    escalation_level: EscalationLevel = Field(..., description="Current escalation level")


class EscalationEmailRequest(BaseModel):
    """Schema for escalation email request"""
    violation_ids: List[int] = Field(..., description="List of violation IDs to escalate")
    escalation_level: EscalationLevel = Field(..., description="Escalation level")
    custom_message: Optional[str] = Field(None, description="Custom escalation message")
    send_to_report_owner: bool = Field(default=True, description="Send to Report Owner")
    cc_cdo: bool = Field(default=True, description="CC the CDO")


class EscalationEmailResponse(BaseModel):
    """Schema for escalation email response"""
    email_sent: bool = Field(..., description="Email sent successfully")
    recipients: List[str] = Field(..., description="Email recipients")
    violations_escalated: int = Field(..., description="Number of violations escalated")
    escalation_level: EscalationLevel = Field(..., description="Escalation level used")
    sent_at: datetime = Field(..., description="Email sent timestamp")


# Phase Completion Schema
class DataProviderPhaseComplete(BaseModel):
    """Schema for completing data provider phase"""
    completion_notes: Optional[str] = Field(None, description="Completion notes")
    confirm_completion: bool = Field(..., description="Confirm completion")


# Assignment Matrix and Summary Schemas
class DataOwnerInfo(BaseModel):
    """Schema for data owner information"""
    user_id: int = Field(..., description="User ID")
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    email: str = Field(..., description="Email address")
    lob_name: str = Field(..., description="LOB name")


class AssignmentMatrix(BaseModel):
    """Schema for assignment matrix view"""
    cycle_id: int = Field(..., description="Cycle ID")
    report_id: int = Field(..., description="Report ID")
    assignments: List[AttributeAssignmentStatus] = Field(..., description="All attribute assignments")
    data_owners: List[DataOwnerInfo] = Field(..., description="Available data owners")
    lob_summary: Dict[str, int] = Field(..., description="Summary by LOB")
    cdo_summary: Dict[str, int] = Field(..., description="Summary by CDO")
    status_summary: Dict[str, int] = Field(..., description="Summary by status")


class CDOWorkloadSummary(BaseModel):
    """Schema for CDO workload summary"""
    cdo_id: int = Field(..., description="CDO user ID")
    cdo_name: str = Field(..., description="CDO name")
    lob_name: str = Field(..., description="LOB name")
    total_assignments: int = Field(..., description="Total assignments")
    completed_assignments: int = Field(..., description="Completed assignments")
    pending_assignments: int = Field(..., description="Pending assignments")
    overdue_assignments: int = Field(..., description="Overdue assignments")
    average_completion_time: Optional[float] = Field(None, description="Average completion time in hours")
    sla_compliance_rate: float = Field(..., description="SLA compliance rate percentage")


# Data Provider Assignment Audit
class AssignmentAuditEntry(BaseModel):
    """Schema for assignment audit entry"""
    assignment_id: int = Field(..., description="Assignment ID")
    attribute_id: int = Field(..., description="Attribute ID")
    action: str = Field(..., description="Action performed")
    performed_by: int = Field(..., description="User who performed action")
    performed_at: datetime = Field(..., description="Action timestamp")
    old_values: Optional[Dict[str, Any]] = Field(None, description="Previous values")
    new_values: Optional[Dict[str, Any]] = Field(None, description="New values")
    notes: Optional[str] = Field(None, description="Action notes")


class DataOwnerAssignmentAuditLog(BaseModel):
    """Schema for complete assignment audit log"""
    cycle_id: int = Field(..., description="Cycle ID")
    report_id: int = Field(..., description="Report ID")
    audit_entries: List[AssignmentAuditEntry] = Field(..., description="Audit trail entries")
    total_entries: int = Field(..., description="Total audit entries") 