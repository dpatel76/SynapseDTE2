"""
Schemas for Activity Management
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ActivityStateResponse(BaseModel):
    """Response model for individual activity state"""
    activity_id: str = Field(..., description="Activity code/identifier")
    name: str = Field(..., description="Activity display name")
    description: Optional[str] = Field(None, description="Activity description")
    status: str = Field(..., description="Current status: pending, active, completed, blocked, skipped")
    can_start: bool = Field(..., description="Whether the activity can be started")
    can_complete: bool = Field(..., description="Whether the activity can be completed")
    can_reset: bool = Field(..., description="Whether the activity can be reset")
    completion_percentage: int = Field(..., description="Completion percentage (0-100)")
    blocking_reason: Optional[str] = Field(None, description="Reason why activity is blocked")
    last_updated: Optional[datetime] = Field(None, description="Last update timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional activity metadata")


class PhaseActivitiesResponse(BaseModel):
    """Response model for all activities in a phase"""
    phase_name: str
    cycle_id: int
    report_id: int
    activities: List[ActivityStateResponse]


class ActivityTransitionRequest(BaseModel):
    """Request model for activity state transition"""
    target_status: str = Field(..., description="Target status: active, completed, blocked, skipped")
    cycle_id: int = Field(..., description="Cycle ID")
    report_id: int = Field(..., description="Report ID")
    phase_name: str = Field(..., description="Phase name")
    notes: Optional[str] = Field(None, description="Transition notes")
    completion_data: Optional[Dict[str, Any]] = Field(None, description="Data to store on completion")


class ActivityResetRequest(BaseModel):
    """Request model for activity reset"""
    cycle_id: int = Field(..., description="Cycle ID")
    report_id: int = Field(..., description="Report ID")
    phase_name: str = Field(..., description="Phase name")
    cascade: bool = Field(True, description="Whether to cascade reset to dependent activities")


class ActivityDefinitionResponse(BaseModel):
    """Response model for activity definition"""
    id: int
    phase_name: str
    activity_name: str
    activity_code: str
    description: Optional[str]
    activity_type: str
    sequence_order: int
    button_text: Optional[str]
    success_message: Optional[str]
    instructions: Optional[str]
    can_skip: bool
    can_reset: bool
    is_active: bool