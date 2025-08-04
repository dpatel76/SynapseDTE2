"""
Report DTOs
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ReportDTO(BaseModel):
    """DTO for report data"""
    report_id: int
    report_name: str
    regulation: Optional[str] = None
    frequency: Optional[str] = None
    description: Optional[str] = None
    lob_id: int
    report_owner_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    lob_name: Optional[str] = None
    owner_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class ReportCreateDTO(BaseModel):
    """DTO for creating a report"""
    report_name: str = Field(..., min_length=1, max_length=255)
    lob_id: int
    report_owner_id: int
    description: Optional[str] = None
    frequency: Optional[str] = None
    regulation: Optional[str] = None


class ReportUpdateDTO(BaseModel):
    """DTO for updating a report"""
    report_name: Optional[str] = Field(None, min_length=1, max_length=255)
    lob_id: Optional[int] = None
    report_owner_id: Optional[int] = None
    description: Optional[str] = None
    frequency: Optional[str] = None
    regulation: Optional[str] = None
    is_active: Optional[bool] = None


class ReportListResponseDTO(BaseModel):
    """DTO for report list response"""
    reports: list[ReportDTO]
    total: int
    skip: int = 0
    limit: int = 100