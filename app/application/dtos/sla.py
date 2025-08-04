from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


# SLA Configuration DTOs
class SLAConfigurationCreateDTO(BaseModel):
    sla_type: str
    sla_hours: int
    warning_hours: int
    escalation_enabled: bool = True
    business_hours_only: bool = True
    weekend_excluded: bool = True
    auto_escalate_on_breach: bool = True
    escalation_interval_hours: int = 24


class SLAConfigurationUpdateDTO(BaseModel):
    sla_type: Optional[str] = None
    sla_hours: Optional[int] = None
    warning_hours: Optional[int] = None
    escalation_enabled: Optional[bool] = None
    business_hours_only: Optional[bool] = None
    weekend_excluded: Optional[bool] = None
    auto_escalate_on_breach: Optional[bool] = None
    escalation_interval_hours: Optional[int] = None
    is_active: Optional[bool] = None


class SLAConfigurationDTO(BaseModel):
    sla_config_id: int
    sla_type: str
    sla_hours: int
    warning_hours: int
    escalation_enabled: bool
    business_hours_only: bool
    weekend_excluded: bool
    auto_escalate_on_breach: bool
    escalation_interval_hours: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: int
    updated_by: Optional[int]

    class Config:
        from_attributes = True


# Escalation Rule DTOs
class EscalationRuleCreateDTO(BaseModel):
    sla_config_id: int
    escalation_level: str
    escalation_order: int
    escalate_to_role: Optional[str] = None
    escalate_to_user_id: Optional[int] = None
    hours_after_breach: int
    email_template_subject: str
    email_template_body: str
    include_managers: bool = True


class EscalationRuleUpdateDTO(BaseModel):
    escalation_level: Optional[str] = None
    escalation_order: Optional[int] = None
    escalate_to_role: Optional[str] = None
    escalate_to_user_id: Optional[int] = None
    hours_after_breach: Optional[int] = None
    email_template_subject: Optional[str] = None
    email_template_body: Optional[str] = None
    include_managers: Optional[bool] = None
    is_active: Optional[bool] = None


class EscalationRuleDTO(BaseModel):
    escalation_rule_id: int
    sla_config_id: int
    escalation_level: str
    escalation_order: int
    escalate_to_role: Optional[str]
    escalate_to_user_id: Optional[int]
    hours_after_breach: int
    email_template_subject: str
    email_template_body: str
    include_managers: bool
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: int
    updated_by: Optional[int]

    class Config:
        from_attributes = True


# SLA Violation DTOs
class SLAViolationDTO(BaseModel):
    violation_id: int
    report_name: str
    sla_type: str
    started_at: Optional[datetime]
    due_date: Optional[datetime]
    is_violated: bool
    violation_hours: float
    current_escalation_level: Optional[str]
    escalation_count: int
    is_resolved: bool
    resolved_at: Optional[datetime]
    resolution_notes: Optional[str]

    class Config:
        from_attributes = True


class SLAViolationSummaryDTO(BaseModel):
    total_violations: int
    by_severity: Dict[str, int]
    by_sla_type: Dict[str, int]


class ResolveViolationDTO(BaseModel):
    resolution_notes: Optional[str] = None


class EscalationLogDTO(BaseModel):
    email_log_id: int
    sla_violation_id: int
    escalation_rule_id: int
    sent_to: str
    sent_at: datetime
    email_status: str
    failure_reason: Optional[str]

    class Config:
        from_attributes = True


# Filter DTOs
class SLAConfigurationFilterDTO(BaseModel):
    active_only: bool = False
    skip: int = 0
    limit: int = 100


class EscalationRuleFilterDTO(BaseModel):
    sla_config_id: Optional[int] = None
    active_only: bool = False


class SLAViolationFilterDTO(BaseModel):
    active_only: bool = True
    sla_type: Optional[str] = None
    severity: Optional[str] = None
    skip: int = 0
    limit: int = 100