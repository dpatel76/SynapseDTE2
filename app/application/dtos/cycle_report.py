from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class CycleReportDTO(BaseModel):
    cycle_report_id: int
    cycle_id: int
    report_id: int
    tester_id: Optional[int]
    data_owner_id: Optional[int]
    status: str
    created_at: datetime
    updated_at: Optional[datetime]
    assigned_at: Optional[datetime]
    completed_at: Optional[datetime]
    overall_progress: float = 0.0
    
    # Related data
    report_name: Optional[str] = None
    lob_name: Optional[str] = None
    cycle_name: Optional[str] = None
    tester_name: Optional[str] = None
    data_owner_name: Optional[str] = None
    current_phase: Optional[str] = None
    
    # Aggregated data
    total_phases: int = 7
    completed_phases: int = 0
    issue_count: int = 0
    
    class Config:
        from_attributes = True


class CycleReportDetailDTO(CycleReportDTO):
    """Extended DTO with full details including phases and observations"""
    workflow_phases: List[Dict[str, Any]] = []
    observations: List[Dict[str, Any]] = []
    recent_activities: List[Dict[str, Any]] = []


class TesterReportFilterDTO(BaseModel):
    tester_id: int
    status: Optional[List[str]] = None
    cycle_id: Optional[int] = None
    lob_id: Optional[int] = None


class DataOwnerReportFilterDTO(BaseModel):
    data_owner_id: int
    status: Optional[List[str]] = None
    cycle_id: Optional[int] = None
    lob_id: Optional[int] = None


class CycleReportWorkflowStatusDTO(BaseModel):
    cycle_report_id: int
    report_name: str
    workflow_phases: List[Dict[str, Any]]
    overall_progress: float
    current_phase: str
    phase_statuses: Dict[str, str]
    phase_progress: Dict[str, float]
    is_blocked: bool
    blocked_reason: Optional[str]


class CycleReportActivityDTO(BaseModel):
    activity_id: int
    cycle_report_id: int
    phase_name: str
    action: str
    details: Optional[str]
    user_name: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class CycleReportObservationDTO(BaseModel):
    observation_id: int
    cycle_report_id: int
    observation_type: str
    title: str
    description: str
    severity: str
    status: str
    remediation_status: Optional[str]
    created_by_name: str
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class CycleReportUpdateDTO(BaseModel):
    status: Optional[str] = None
    tester_id: Optional[int] = None
    data_owner_id: Optional[int] = None


class CycleReportBulkAssignDTO(BaseModel):
    cycle_report_ids: List[int]
    tester_id: Optional[int] = None
    data_owner_id: Optional[int] = None


class CycleReportMetricsDTO(BaseModel):
    total_reports: int
    by_status: Dict[str, int]
    by_phase: Dict[str, int]
    average_progress: float
    overdue_count: int
    at_risk_count: int
    on_track_count: int