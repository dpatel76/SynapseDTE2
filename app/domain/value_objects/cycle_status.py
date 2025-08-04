"""Cycle Status Value Object"""
from enum import Enum


class CycleStatus(str, Enum):
    """
    Represents the status of a test cycle
    Immutable value object
    """
    PLANNING = "planning"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"
    
    def can_transition_to(self, new_status: 'CycleStatus') -> bool:
        """Check if transition to new status is allowed"""
        allowed_transitions = {
            CycleStatus.PLANNING: [CycleStatus.ACTIVE, CycleStatus.CANCELLED],
            CycleStatus.ACTIVE: [CycleStatus.COMPLETED, CycleStatus.ON_HOLD, CycleStatus.CANCELLED],
            CycleStatus.ON_HOLD: [CycleStatus.ACTIVE, CycleStatus.CANCELLED],
            CycleStatus.COMPLETED: [],  # No transitions from completed
            CycleStatus.CANCELLED: []   # No transitions from cancelled
        }
        
        return new_status in allowed_transitions.get(self, [])