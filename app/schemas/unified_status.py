"""
Pydantic schemas for Unified Status System
"""

from typing import Dict, List, Optional, Literal, Any
from datetime import datetime
from pydantic import BaseModel, Field

PhaseStatusType = Literal["not_started", "in_progress", "completed", "blocked"]
ActivityStatusType = Literal["pending", "active", "completed", "blocked", "skipped"]

class ActivityStatusSchema(BaseModel):
    """Schema for activity status within a phase"""
    activity_id: str = Field(..., description="Unique activity identifier")
    name: str = Field(..., description="Activity name")
    description: str = Field(..., description="Activity description")
    status: ActivityStatusType = Field(..., description="Current activity status")
    can_start: bool = Field(..., description="Whether activity can be started")
    can_complete: bool = Field(..., description="Whether activity can be completed")
    can_reset: Optional[bool] = Field(False, description="Whether activity can be reset")
    completion_percentage: Optional[int] = Field(None, description="Completion percentage (0-100)")
    blocking_reason: Optional[str] = Field(None, description="Reason if blocked")
    last_updated: Optional[datetime] = Field(None, description="Last update timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class PhaseStatusSchema(BaseModel):
    """Schema for unified phase status including all activities"""
    phase_name: str = Field(..., description="Name of the phase")
    cycle_id: int = Field(..., description="Cycle ID")
    report_id: int = Field(..., description="Report ID")
    phase_status: PhaseStatusType = Field(..., description="Overall phase status")
    overall_completion_percentage: int = Field(..., description="Overall completion percentage")
    activities: List[ActivityStatusSchema] = Field(..., description="List of activities in this phase")
    can_proceed_to_next: bool = Field(..., description="Whether can proceed to next phase")
    blocking_issues: List[str] = Field(..., description="List of blocking issues")
    last_updated: datetime = Field(..., description="Last update timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class AllPhasesStatusSchema(BaseModel):
    """Schema for all phases status response"""
    phases: Dict[str, PhaseStatusSchema] = Field(..., description="Status for all phases")