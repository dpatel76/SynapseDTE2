"""
Test cycle-related Pydantic schemas
"""

from typing import Optional, List, Dict
from datetime import datetime, date
from pydantic import BaseModel, Field, validator, ConfigDict


class TestCycleBase(BaseModel):
    """Base test cycle schema with common fields"""
    cycle_name: str = Field(..., min_length=1, max_length=255, description="Cycle name")
    description: Optional[str] = Field(None, description="Cycle description")
    start_date: date = Field(..., description="Cycle start date")
    end_date: Optional[date] = Field(None, description="Cycle end date")
    status: Optional[str] = Field(default="Active", description="Cycle status")


class TestCycleCreate(TestCycleBase):
    """Schema for creating a new test cycle"""
    
    @validator('end_date')
    def validate_end_date(cls, v, values):
        if v is not None and 'start_date' in values and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v
    
    @validator('status')
    def validate_status(cls, v):
        if v is not None:
            valid_statuses = ["Active", "Completed", "Cancelled", "On Hold"]
            if v not in valid_statuses:
                raise ValueError(f'Invalid status. Must be one of: {valid_statuses}')
        return v


class TestCycleUpdate(BaseModel):
    """Schema for updating test cycle information"""
    cycle_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Cycle name")
    description: Optional[str] = Field(None, description="Cycle description")
    start_date: Optional[date] = Field(None, description="Cycle start date")
    end_date: Optional[date] = Field(None, description="Cycle end date")
    status: Optional[str] = Field(None, description="Cycle status")
    
    @validator('status')
    def validate_status(cls, v):
        if v is not None:
            valid_statuses = ["Active", "Completed", "Cancelled", "On Hold"]
            if v not in valid_statuses:
                raise ValueError(f'Invalid status. Must be one of: {valid_statuses}')
        return v


class TestCycleResponse(TestCycleBase):
    """Schema for test cycle response"""
    cycle_id: int = Field(..., description="Cycle ID")
    test_executive_id: int = Field(..., description="Test manager ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    # Related data
    test_executive_name: Optional[str] = Field(None, description="Test manager name")
    total_reports: Optional[int] = Field(None, description="Total reports assigned")
    completed_reports: Optional[int] = Field(None, description="Completed reports count")
    at_risk_count: Optional[int] = Field(None, description="At risk reports count")
    observations_count: Optional[int] = Field(None, description="Total observations count")
    
    model_config = ConfigDict(from_attributes=True)


class TestCycleListResponse(BaseModel):
    """Schema for test cycle list response with pagination"""
    cycles: List[TestCycleResponse] = Field(..., description="List of test cycles")
    total: int = Field(..., description="Total number of cycles")
    skip: int = Field(..., description="Number of records skipped")
    limit: int = Field(..., description="Number of records returned")


class CycleReportAssignment(BaseModel):
    """Schema for assigning a report to a cycle"""
    report_id: int = Field(..., description="Report ID")
    tester_id: Optional[int] = Field(None, description="Tester ID")


class CycleReportResponse(BaseModel):
    """Schema for cycle report assignment response"""
    cycle_id: int = Field(..., description="Cycle ID")
    report_id: int = Field(..., description="Report ID")
    tester_id: Optional[int] = Field(None, description="Tester ID")
    status: str = Field(..., description="Assignment status")
    started_at: Optional[datetime] = Field(None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    
    # Related data
    report_name: Optional[str] = Field(None, description="Report name")
    tester_name: Optional[str] = Field(None, description="Tester name")
    lob_name: Optional[str] = Field(None, description="LOB name")
    current_phase: Optional[str] = Field(None, description="Current workflow phase")
    overall_progress: Optional[int] = Field(None, description="Overall progress percentage")
    issues_count: Optional[int] = Field(None, description="Number of issues")
    cycle_name: Optional[str] = Field(None, description="Cycle name")
    
    # Report owner information
    report_owner_id: Optional[int] = Field(None, description="Report owner ID")
    report_owner_name: Optional[str] = Field(None, description="Report owner name")
    report_owner_email: Optional[str] = Field(None, description="Report owner email")
    
    model_config = ConfigDict(from_attributes=True)


class CycleStatsResponse(BaseModel):
    """Schema for cycle statistics response"""
    cycle_id: int = Field(..., description="Cycle ID")
    total_reports: int = Field(..., description="Total reports in cycle")
    reports_by_status: dict = Field(..., description="Report count by status")
    reports_by_tester: dict = Field(..., description="Report count by tester")


class CycleSummary(BaseModel):
    """Summary information for a test cycle"""
    cycle_id: int = Field(..., description="Cycle ID")
    cycle_name: str = Field(..., description="Cycle name")
    status: str = Field(..., description="Cycle status")
    start_date: date = Field(..., description="Start date")
    end_date: Optional[date] = Field(None, description="End date")
    test_executive_name: str = Field(..., description="Test manager name")
    total_reports: int = Field(..., description="Total reports")
    completed_reports: int = Field(..., description="Completed reports")
    progress_percentage: float = Field(..., description="Progress percentage")
    
    model_config = ConfigDict(from_attributes=True)


class TesterAssignment(BaseModel):
    """Schema for tester assignment"""
    tester_id: int = Field(..., description="Tester ID")
    reason: Optional[str] = Field(None, description="Reason for assignment")


class CycleStatusUpdate(BaseModel):
    """Schema for updating cycle status"""
    status: str = Field(..., description="New status")
    reason: Optional[str] = Field(None, description="Reason for status change")
    
    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ["Active", "Completed", "Cancelled", "On Hold"]
        if v not in valid_statuses:
            raise ValueError(f'Invalid status. Must be one of: {valid_statuses}')
        return v


class CycleReportFilters(BaseModel):
    """Schema for filtering cycle reports"""
    status: Optional[str] = Field(None, description="Filter by status")
    tester_id: Optional[int] = Field(None, description="Filter by tester")
    lob_id: Optional[int] = Field(None, description="Filter by LOB")


class CycleProgressResponse(BaseModel):
    """Schema for cycle progress response"""
    cycle_id: int = Field(..., description="Cycle ID")
    cycle_name: str = Field(..., description="Cycle name")
    total_reports: int = Field(..., description="Total reports")
    not_started: int = Field(..., description="Reports not started")
    in_progress: int = Field(..., description="Reports in progress")
    completed: int = Field(..., description="Reports completed")
    progress_percentage: float = Field(..., description="Overall progress percentage")
    days_remaining: Optional[int] = Field(None, description="Days remaining in cycle")
    on_track: bool = Field(..., description="Whether cycle is on track")


class TesterAssignmentData(BaseModel):
    """Request schema for assigning a tester to a report"""
    tester_id: int


# === LEGACY ALIASES FOR BACKWARD COMPATIBILITY ===
class CycleCreate(BaseModel):
    """Alias for TestCycleCreate - for backward compatibility"""
    cycle_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    status: Optional[str] = "Active"


class CycleUpdate(BaseModel):  
    """Alias for TestCycleUpdate - for backward compatibility"""
    cycle_name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = None


class CycleResponse(BaseModel):
    """Alias for TestCycleResponse - for backward compatibility"""
    cycle_id: int
    cycle_name: str
    description: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    status: str
    test_executive_id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class CycleSearchFilter(BaseModel):
    """Search filter for cycles"""
    status: Optional[str] = None
    test_executive_id: Optional[int] = None
    search: Optional[str] = None


class ReportAssignmentData(BaseModel):
    """Data for report assignment"""
    report_id: int
    tester_id: Optional[int] = None


class CycleDetailResponse(BaseModel):
    """Detailed cycle response with additional info"""
    cycle_id: int
    cycle_name: str
    description: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    status: str
    test_executive_id: int
    test_executive_name: Optional[str] = None
    created_at: datetime
    total_reports: int = 0
    completed_reports: int = 0
    progress_percentage: float = 0.0
    
    model_config = ConfigDict(from_attributes=True)


class CycleMetrics(BaseModel):
    """Cycle metrics and statistics"""
    cycle_id: int
    total_reports: int = 0
    reports_by_status: Dict[str, int] = {}
    reports_by_phase: Dict[str, int] = {}
    average_completion_time: Optional[float] = None
    on_track_reports: int = 0
    delayed_reports: int = 0
    
# === END LEGACY ALIASES === 