"""
Pydantic schemas for Activity State Management
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

from app.core.activity_states import ActivityState


class ActivityTransitionRequest(BaseModel):
    """Request model for activity state transition"""
    cycle_id: str = Field(..., description="Test cycle ID")
    report_id: str = Field(..., description="Report ID")
    phase_name: str = Field(..., description="Workflow phase name")
    activity_name: str = Field(..., description="Activity name to transition")
    target_state: ActivityState = Field(..., description="Target state for the activity")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for validation")


class ActivityEventRequest(BaseModel):
    """Request model for workflow events"""
    cycle_id: str = Field(..., description="Test cycle ID")
    report_id: str = Field(..., description="Report ID")
    phase_name: str = Field(..., description="Workflow phase name")
    event_type: str = Field(..., description="Type of event (submission, approval_decision, etc.)")
    event_data: Optional[Dict[str, Any]] = Field(None, description="Event-specific data")


class ActivityInfo(BaseModel):
    """Information about a single activity"""
    name: str = Field(..., description="Activity name")
    state: ActivityState = Field(..., description="Current state")
    dependency: Optional[str] = Field(None, description="Dependency activity")
    started_at: Optional[datetime] = Field(None, description="When activity was started")
    completed_at: Optional[datetime] = Field(None, description="When activity was completed")
    started_by: Optional[str] = Field(None, description="User who started the activity")
    completed_by: Optional[str] = Field(None, description="User who completed the activity")


class PhaseProgress(BaseModel):
    """Phase progress information"""
    total_activities: int = Field(..., description="Total number of activities")
    completed: int = Field(..., description="Number of completed activities")
    in_progress: int = Field(..., description="Number of activities in progress")
    not_started: int = Field(..., description="Number of activities not started")
    completion_percentage: float = Field(..., description="Percentage of completion")
    current_activity: Optional[str] = Field(None, description="Next activity to be started")


class ActivityStateResponse(BaseModel):
    """Response model for activity state transitions"""
    success: bool = Field(..., description="Whether the transition was successful")
    activity_state: Optional[ActivityState] = Field(None, description="New activity state")
    phase_progress: Optional[PhaseProgress] = Field(None, description="Updated phase progress")
    error: Optional[str] = Field(None, description="Error message if transition failed")
    auto_started: Optional[str] = Field(None, description="Activity that was auto-started")
    next_activity_manual: Optional[str] = Field(None, description="Next manual activity")


class PhaseActivitiesResponse(BaseModel):
    """Response model for phase activities query"""
    phase_name: str = Field(..., description="Workflow phase name")
    activities: Dict[str, ActivityInfo] = Field(..., description="All activities in the phase")
    progress: PhaseProgress = Field(..., description="Overall phase progress")
    next_activity: Optional[str] = Field(None, description="Next activity to be started")


class ActivityMetrics(BaseModel):
    """Metrics for activity execution"""
    activity_name: str = Field(..., description="Activity name")
    avg_duration_minutes: float = Field(..., description="Average completion time in minutes")
    min_duration_minutes: float = Field(..., description="Minimum completion time")
    max_duration_minutes: float = Field(..., description="Maximum completion time")
    total_executions: int = Field(..., description="Total number of executions")
    on_time_completions: int = Field(..., description="Number of on-time completions")
    late_completions: int = Field(..., description="Number of late completions")


class PhaseActivityMetrics(BaseModel):
    """Activity metrics for a phase"""
    phase_name: str = Field(..., description="Workflow phase name")
    activities: List[ActivityMetrics] = Field(..., description="Metrics for each activity")
    total_phase_duration_avg: float = Field(..., description="Average total phase duration")
    bottleneck_activities: List[str] = Field(..., description="Activities causing delays")


# Configuration models

class ActivityConfiguration(BaseModel):
    """Configuration for an activity"""
    name: str = Field(..., description="Activity name")
    type: str = Field(..., description="Activity type")
    manual: bool = Field(..., description="Whether activity requires manual start")
    allowed_roles: List[str] = Field(..., description="Roles allowed to transition")
    auto_complete_triggers: List[str] = Field(..., description="Events that auto-complete")
    sla_hours: Optional[int] = Field(None, description="SLA in hours for completion")
    
    
class PhaseConfiguration(BaseModel):
    """Configuration for a phase"""
    phase_name: str = Field(..., description="Phase name")
    activities: List[ActivityConfiguration] = Field(..., description="Activities in phase")
    dependencies: List[tuple[str, Optional[str]]] = Field(..., description="Activity dependencies")
    required_for_completion: List[str] = Field(..., description="Activities that must complete")