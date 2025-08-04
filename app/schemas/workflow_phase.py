"""
Workflow Phase schemas
"""

from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, Field, computed_field
from enum import Enum

# Enums for validation
class WorkflowPhaseState(str, Enum):
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    COMPLETE = "Complete"

class WorkflowPhaseStatus(str, Enum):
    ON_TRACK = "On Track"
    AT_RISK = "At Risk"
    PAST_DUE = "Past Due"

class LegacyPhaseStatus(str, Enum):
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    COMPLETE = "Complete"
    PENDING_APPROVAL = "Pending Approval"

class WorkflowPhase(BaseModel):
    """Workflow phase response model"""
    phase_id: int
    cycle_id: int
    report_id: int
    phase_name: str
    
    # Legacy status (for backward compatibility)
    status: LegacyPhaseStatus
    
    # Enhanced state and status tracking
    state: WorkflowPhaseState
    schedule_status: WorkflowPhaseStatus
    
    # Override capabilities
    state_override: Optional[WorkflowPhaseState] = None
    status_override: Optional[WorkflowPhaseStatus] = None
    override_reason: Optional[str] = None
    override_by: Optional[int] = None
    override_at: Optional[datetime] = None
    
    # Date tracking
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    actual_start_date: Optional[datetime] = None
    actual_end_date: Optional[datetime] = None
    
    # User tracking
    started_by: Optional[int] = None
    completed_by: Optional[int] = None
    notes: Optional[str] = None
    
    # Computed fields for UI
    @computed_field
    @property
    def effective_state(self) -> WorkflowPhaseState:
        """Return the effective state (override if present, otherwise actual state)"""
        return self.state_override if self.state_override else self.state
    
    @computed_field
    @property
    def effective_status(self) -> WorkflowPhaseStatus:
        """Return the effective status (override if present, otherwise actual status)"""
        return self.status_override if self.status_override else self.schedule_status
    
    @computed_field
    @property
    def has_overrides(self) -> bool:
        """Check if any overrides are active"""
        return self.state_override is not None or self.status_override is not None
    
    @computed_field
    @property
    def days_until_due(self) -> Optional[int]:
        """Calculate days until planned end date"""
        if not self.planned_end_date:
            return None
        
        from datetime import date
        today = date.today()
        delta = self.planned_end_date - today
        return delta.days
    
    @computed_field
    @property
    def is_overdue(self) -> bool:
        """Check if phase is past due"""
        if not self.planned_end_date or self.effective_state == WorkflowPhaseState.COMPLETE:
            return False
        
        from datetime import date
        return date.today() > self.planned_end_date
    
    @computed_field
    @property
    def is_at_risk(self) -> bool:
        """Check if phase is at risk (within 7 days of due date)"""
        if not self.planned_end_date or self.effective_state == WorkflowPhaseState.COMPLETE:
            return False
        
        days_until = self.days_until_due
        return days_until is not None and 0 <= days_until <= 7
    
    class Config:
        from_attributes = True


class WorkflowPhaseUpdate(BaseModel):
    """Schema for updating workflow phase"""
    state: Optional[WorkflowPhaseState] = None
    schedule_status: Optional[WorkflowPhaseStatus] = None
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    actual_start_date: Optional[datetime] = None
    actual_end_date: Optional[datetime] = None
    notes: Optional[str] = None


class WorkflowPhaseOverride(BaseModel):
    """Schema for overriding workflow phase state/status"""
    state_override: Optional[WorkflowPhaseState] = None
    status_override: Optional[WorkflowPhaseStatus] = None
    override_reason: str = Field(..., min_length=1, max_length=500, description="Reason for override is required")


class PhaseTransitionRequest(BaseModel):
    """Schema for phase transitions with date planning"""
    action: str = Field(..., description="Action to perform: start, complete, update_dates, override")
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    notes: Optional[str] = None
    
    # Override fields
    state_override: Optional[WorkflowPhaseState] = None
    status_override: Optional[WorkflowPhaseStatus] = None
    override_reason: Optional[str] = None


class WorkflowStatusResponse(BaseModel):
    """Enhanced workflow status response"""
    cycle_id: int
    report_id: int
    overall_state: WorkflowPhaseState
    overall_status: WorkflowPhaseStatus
    overall_progress: float = Field(..., ge=0, le=100)
    current_phase: Optional[str] = None
    completed_phases: int
    total_phases: int
    phases: List[WorkflowPhase]
    
    # Summary statistics
    @computed_field
    @property
    def phase_summary(self) -> dict:
        """Compute phase distribution summary"""
        state_counts = {}
        status_counts = {}
        override_count = 0
        
        for phase in self.phases:
            # Count effective states
            effective_state = phase.effective_state
            state_counts[effective_state] = state_counts.get(effective_state, 0) + 1
            
            # Count effective statuses
            effective_status = phase.effective_status
            status_counts[effective_status] = status_counts.get(effective_status, 0) + 1
            
            # Count overrides
            if phase.has_overrides:
                override_count += 1
        
        return {
            "state_distribution": state_counts,
            "status_distribution": status_counts,
            "total_overrides": override_count,
            "overdue_phases": status_counts.get(WorkflowPhaseStatus.PAST_DUE, 0),
            "at_risk_phases": status_counts.get(WorkflowPhaseStatus.AT_RISK, 0)
        } 