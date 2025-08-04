"""
SLA (Service Level Agreement) related Pydantic schemas
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, validator, ConfigDict

# SLA Configuration Schemas

class SLAConfigurationBase(BaseModel):
    sla_type: str = Field(..., description="Type of SLA (e.g., data_owner_identification)")
    sla_hours: int = Field(..., ge=1, description="SLA deadline in hours")
    warning_hours: Optional[int] = Field(None, ge=0, description="Hours before deadline to send warning")
    escalation_enabled: bool = Field(True, description="Whether escalation is enabled")
    business_hours_only: bool = Field(True, description="Whether to calculate SLA during business hours only")
    weekend_excluded: bool = Field(True, description="Whether to exclude weekends from SLA calculation")
    auto_escalate_on_breach: bool = Field(True, description="Whether to automatically escalate on SLA breach")
    escalation_interval_hours: int = Field(24, ge=1, description="Hours between escalation levels")

    @validator('sla_type')
    def validate_sla_type(cls, v):
        valid_types = [
            'data_owner_identification',
            'data_owner_response',
            'document_submission',
            'testing_completion',
            'observation_response',
            'issue_resolution'
        ]
        if v not in valid_types:
            raise ValueError(f'SLA type must be one of: {", ".join(valid_types)}')
        return v

    @validator('warning_hours')
    def validate_warning_hours(cls, v, values):
        if v is not None and 'sla_hours' in values and v >= values['sla_hours']:
            raise ValueError('Warning hours must be less than SLA hours')
        return v

class SLAConfigurationCreate(SLAConfigurationBase):
    pass

class SLAConfigurationUpdate(BaseModel):
    sla_hours: Optional[int] = Field(None, ge=1)
    warning_hours: Optional[int] = Field(None, ge=0)
    escalation_enabled: Optional[bool] = None
    business_hours_only: Optional[bool] = None
    weekend_excluded: Optional[bool] = None
    auto_escalate_on_breach: Optional[bool] = None
    escalation_interval_hours: Optional[int] = Field(None, ge=1)
    is_active: Optional[bool] = None

class SLAConfigurationResponse(SLAConfigurationBase):
    sla_config_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: int
    updated_by: Optional[int]

    model_config = ConfigDict(from_attributes=True)

# Escalation Rule Schemas

class EscalationRuleBase(BaseModel):
    sla_config_id: int = Field(..., description="Associated SLA configuration ID")
    escalation_level: str = Field(..., description="Escalation level (level_1, level_2, etc.)")
    escalation_order: int = Field(..., ge=1, le=4, description="Order of escalation (1-4)")
    escalate_to_role: str = Field(..., description="Role to escalate to")
    escalate_to_user_id: Optional[int] = Field(None, description="Specific user to escalate to")
    hours_after_breach: int = Field(0, ge=0, description="Hours after SLA breach to trigger escalation")
    email_template_subject: str = Field(..., min_length=1, description="Email subject template")
    email_template_body: str = Field(..., min_length=1, description="Email body template")
    include_managers: bool = Field(False, description="Whether to include managers in escalation")

    @validator('escalation_level')
    def validate_escalation_level(cls, v):
        valid_levels = ['level_1', 'level_2', 'level_3', 'level_4']
        if v not in valid_levels:
            raise ValueError(f'Escalation level must be one of: {", ".join(valid_levels)}')
        return v

    @validator('escalate_to_role')
    def validate_escalate_to_role(cls, v):
        valid_roles = ['Test Executive', 'Report Owner', 'Report Owner Executive', 'Data Executive']
        if v not in valid_roles:
            raise ValueError(f'Escalate to role must be one of: {", ".join(valid_roles)}')
        return v

class EscalationRuleCreate(EscalationRuleBase):
    pass

class EscalationRuleUpdate(BaseModel):
    escalation_level: Optional[str] = None
    escalation_order: Optional[int] = Field(None, ge=1, le=4)
    escalate_to_role: Optional[str] = None
    escalate_to_user_id: Optional[int] = None
    hours_after_breach: Optional[int] = Field(None, ge=0)
    email_template_subject: Optional[str] = Field(None, min_length=1)
    email_template_body: Optional[str] = Field(None, min_length=1)
    include_managers: Optional[bool] = None
    is_active: Optional[bool] = None

class EscalationRuleResponse(EscalationRuleBase):
    escalation_rule_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: int
    updated_by: Optional[int]

    model_config = ConfigDict(from_attributes=True)

# SLA Violation Schemas

class SLAViolationBase(BaseModel):
    report_id: int
    sla_type: str
    started_at: datetime
    due_date: datetime
    is_violated: bool = False
    violation_hours: Optional[float] = None
    current_escalation_level: Optional[str] = None
    escalation_count: int = 0

class SLAViolationCreate(SLAViolationBase):
    pass

class SLAViolationUpdate(BaseModel):
    due_date: Optional[datetime] = None
    is_violated: Optional[bool] = None
    violation_hours: Optional[float] = None
    current_escalation_level: Optional[str] = None
    escalation_count: Optional[int] = None
    is_resolved: Optional[bool] = None
    resolution_notes: Optional[str] = None

class SLAViolationResponse(SLAViolationBase):
    violation_id: int
    is_resolved: bool
    resolved_at: Optional[datetime]
    resolved_by: Optional[int]
    resolution_notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

# SLA Escalation Log Schemas

class SLAEscalationLogBase(BaseModel):
    violation_id: int
    escalation_level: str
    escalated_to_role: str
    escalated_to_user_id: Optional[int]
    escalation_reason: str
    email_sent: bool = False
    email_subject: Optional[str] = None
    email_body: Optional[str] = None

class SLAEscalationLogCreate(SLAEscalationLogBase):
    pass

class SLAEscalationLogResponse(SLAEscalationLogBase):
    escalation_log_id: int
    escalated_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Summary and Analytics Schemas

class SLAViolationSummary(BaseModel):
    total_violations: int
    by_severity: dict
    by_sla_type: dict

class SLAMetrics(BaseModel):
    sla_type: str
    total_instances: int
    violations_count: int
    compliance_rate: float
    average_completion_hours: float
    breach_rate: float

class SLADashboardData(BaseModel):
    summary: SLAViolationSummary
    recent_violations: List[SLAViolationResponse]
    metrics_by_type: List[SLAMetrics]
    escalation_trends: dict

# Business Hours Configuration Schema

class BusinessHoursConfig(BaseModel):
    start_hour: int = Field(9, ge=0, le=23, description="Business day start hour (24-hour format)")
    end_hour: int = Field(17, ge=0, le=23, description="Business day end hour (24-hour format)")
    business_days: List[int] = Field([1, 2, 3, 4, 5], description="Business days (1=Monday, 7=Sunday)")
    timezone: str = Field("UTC", description="Timezone for business hours calculation")
    holidays: List[str] = Field([], description="List of holiday dates (YYYY-MM-DD)")

    @validator('end_hour')
    def validate_end_hour(cls, v, values):
        if 'start_hour' in values and v <= values['start_hour']:
            raise ValueError('End hour must be after start hour')
        return v

    @validator('business_days')
    def validate_business_days(cls, v):
        if not all(1 <= day <= 7 for day in v):
            raise ValueError('Business days must be between 1 (Monday) and 7 (Sunday)')
        return v

class BusinessHoursConfigResponse(BusinessHoursConfig):
    config_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True) 