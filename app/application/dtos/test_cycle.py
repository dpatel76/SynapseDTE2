"""
Test Cycle DTOs
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date


class TestCycleDTO(BaseModel):
    """DTO for test cycle data"""
    cycle_id: int
    cycle_name: str
    cycle_type: Optional[str] = "Regulatory"  # Made optional with default
    start_date: date
    end_date: Optional[date] = None
    status: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    test_executive_id: Optional[int] = None
    created_by: Optional[int] = None  # User ID who created the cycle
    
    # Enhanced metrics fields
    total_reports: Optional[int] = 0
    completed_reports: Optional[int] = 0
    at_risk_count: Optional[int] = 0
    observations_count: Optional[int] = 0
    
    # Phase distribution
    phase_counts: Optional[dict[str, int]] = None
    phase_at_risk: Optional[dict[str, int]] = None
    
    class Config:
        from_attributes = True


class TestCycleCreateDTO(BaseModel):
    """DTO for creating a test cycle"""
    cycle_name: str = Field(..., min_length=1, max_length=255)
    cycle_type: Optional[str] = "Regulatory"  # Made optional with default
    start_date: date
    end_date: Optional[date] = None
    status: Optional[str] = "Planning"
    description: Optional[str] = None


class TestCycleUpdateDTO(BaseModel):
    """DTO for updating a test cycle"""
    cycle_name: Optional[str] = Field(None, min_length=1, max_length=255)
    cycle_type: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class TestCycleListResponseDTO(BaseModel):
    """DTO for test cycle list response"""
    cycles: list[TestCycleDTO]
    total: int
    skip: int = 0
    limit: int = 100