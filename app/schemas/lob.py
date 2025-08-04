"""
LOB (Lines of Business) related Pydantic schemas
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class LOBBase(BaseModel):
    """Base LOB schema with common fields"""
    lob_name: str = Field(..., min_length=1, max_length=255, description="LOB name")


class LOBCreate(LOBBase):
    """Schema for creating a new LOB"""
    pass


class LOBUpdate(BaseModel):
    """Schema for updating LOB information"""
    lob_name: Optional[str] = Field(None, min_length=1, max_length=255, description="LOB name")


class LOBResponse(LOBBase):
    """Schema for LOB response"""
    lob_id: int = Field(..., description="LOB ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class LOBDetailResponse(LOBResponse):
    """Extended LOB response with additional details"""
    user_count: int = Field(..., description="Number of users in this LOB")
    report_count: int = Field(..., description="Number of reports in this LOB")
    active_cycles: int = Field(..., description="Number of active test cycles")


class LOBListResponse(BaseModel):
    """Schema for LOB list response"""
    lobs: List[LOBDetailResponse] = Field(..., description="List of LOBs with details")
    total: int = Field(..., description="Total number of LOBs")


class LOBStatsResponse(BaseModel):
    """LOB statistics response"""
    total_lobs: int = Field(..., description="Total number of LOBs")
    users_by_lob: dict = Field(..., description="User count by LOB")
    reports_by_lob: dict = Field(..., description="Report count by LOB")
    active_cycles_by_lob: dict = Field(..., description="Active cycles by LOB") 