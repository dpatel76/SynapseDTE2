"""
Report-related Pydantic schemas
"""

from typing import Optional, List, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator, ConfigDict


class ReportBase(BaseModel):
    """Base report schema with common fields"""
    report_name: str = Field(..., min_length=1, max_length=255, description="Report name")
    regulation: Optional[str] = Field(None, max_length=255, description="Regulation")
    description: Optional[str] = Field(None, description="Report description")
    frequency: Optional[str] = Field(None, description="Report frequency")
    lob_id: int = Field(..., description="LOB ID")
    report_owner_id: Optional[int] = Field(None, description="Report owner ID")
    is_active: bool = Field(default=True, description="Report active status")


class ReportCreate(ReportBase):
    """Schema for creating a new report"""
    pass


class ReportUpdate(BaseModel):
    """Schema for updating report information"""
    report_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Report name")
    regulation: Optional[str] = Field(None, max_length=255, description="Regulation")
    description: Optional[str] = Field(None, description="Report description")
    frequency: Optional[str] = Field(None, description="Report frequency")
    lob_id: Optional[int] = Field(None, description="LOB ID")
    report_owner_id: Optional[int] = Field(None, description="Report owner ID")
    is_active: Optional[bool] = Field(None, description="Report active status")


# Nested schemas for relationships
class LOBInReport(BaseModel):
    """LOB data for report response"""
    lob_id: int
    lob_name: str
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserInReport(BaseModel):
    """User data for report response"""
    user_id: int
    first_name: str
    last_name: str
    email: str
    role: str
    lob_id: Optional[int]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ReportResponse(ReportBase):
    """Schema for report response"""
    report_id: int = Field(..., description="Report ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    # Related data
    lob_name: Optional[str] = Field(None, description="LOB name")
    owner_name: Optional[str] = Field(None, description="Report owner name")
    
    model_config = ConfigDict(from_attributes=True)


class ReportListResponse(BaseModel):
    """Schema for report list response with pagination"""
    reports: List[ReportResponse] = Field(..., description="List of reports")
    total: int = Field(..., description="Total number of reports")
    skip: int = Field(..., description="Number of records skipped")
    limit: int = Field(..., description="Number of records returned")


class ReportSearchFilters(BaseModel):
    """Schema for report search filters"""
    lob_id: Optional[int] = Field(None, description="Filter by LOB ID")
    report_owner_id: Optional[int] = Field(None, description="Filter by report owner")
    regulation: Optional[str] = Field(None, description="Filter by regulation")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    search: Optional[str] = Field(None, description="Search in report name or regulation")


class ReportStatsResponse(BaseModel):
    """Report statistics response"""
    total_active_reports: int = Field(..., description="Total number of active reports")
    total_inactive_reports: int = Field(..., description="Total number of inactive reports")
    reports_by_lob: dict = Field(..., description="Report count by LOB")
    reports_by_regulation: dict = Field(..., description="Report count by regulation")
    reports_by_owner: dict = Field(..., description="Report count by owner")


class ReportOwnerAssignment(BaseModel):
    """Schema for assigning report owner"""
    report_owner_id: int = Field(..., description="New report owner ID")
    reason: Optional[str] = Field(None, description="Reason for assignment change")


class ReportLOBTransfer(BaseModel):
    """Schema for transferring report to different LOB"""
    new_lob_id: int = Field(..., description="New LOB ID")
    reason: str = Field(..., description="Reason for LOB transfer")


class ReportSummary(BaseModel):
    """Summary information for a report"""
    report_id: int = Field(..., description="Report ID")
    report_name: str = Field(..., description="Report name")
    regulation: Optional[str] = Field(None, description="Regulation")
    lob_name: str = Field(..., description="LOB name")
    owner_name: Optional[str] = Field(None, description="Report owner name")
    is_active: bool = Field(..., description="Report active status")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class ReportTestingStart(BaseModel):
    """Schema for starting testing for a report"""
    report_id: int = Field(..., description="Report ID")
    cycle_id: int = Field(..., description="Test cycle ID")
    planned_start_date: Optional[datetime] = Field(None, description="Planned start date")
    planned_end_date: Optional[datetime] = Field(None, description="Planned end date")
    testing_deadline: datetime = Field(..., description="Testing deadline")
    test_strategy: Optional[str] = Field(None, description="Test strategy")
    instructions: Optional[str] = Field(None, description="Testing instructions")


class ReportPhaseUpdate(BaseModel):
    """Schema for updating phase dates"""
    phase_id: str = Field(..., description="Phase ID")
    planned_start_date: Optional[datetime] = Field(None, description="Planned start date")
    planned_end_date: Optional[datetime] = Field(None, description="Planned end date")
    testing_deadline: Optional[datetime] = Field(None, description="Testing deadline")
    test_strategy: Optional[str] = Field(None, description="Test strategy")
    instructions: Optional[str] = Field(None, description="Testing instructions") 