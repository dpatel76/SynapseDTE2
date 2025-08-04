"""Workflow domain events"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any

from .base import DomainEvent


@dataclass
class WorkflowPhaseStarted(DomainEvent):
    """Event raised when a workflow phase is started"""
    cycle_id: int
    report_id: int
    phase_name: str
    started_by: int
    started_at: datetime = None

    def __post_init__(self):
        super().__post_init__()
        if not self.started_at:
            self.started_at = datetime.utcnow()


@dataclass
class WorkflowPhaseCompleted(DomainEvent):
    """Event raised when a workflow phase is completed"""
    cycle_id: int
    report_id: int
    phase_name: str
    completed_by: int
    completed_at: datetime = None
    completion_data: Dict[str, Any] = None

    def __post_init__(self):
        super().__post_init__()
        if not self.completed_at:
            self.completed_at = datetime.utcnow()


@dataclass
class WorkflowPhaseSkipped(DomainEvent):
    """Event raised when a workflow phase is skipped"""
    cycle_id: int
    report_id: int
    phase_name: str
    skipped_by: int
    reason: str
    skipped_at: datetime = None

    def __post_init__(self):
        super().__post_init__()
        if not self.skipped_at:
            self.skipped_at = datetime.utcnow()


@dataclass
class WorkflowPhaseOverridden(DomainEvent):
    """Event raised when a workflow phase state/status is overridden"""
    cycle_id: int
    report_id: int
    phase_name: str
    state_override: Optional[str]
    status_override: Optional[str]
    override_reason: str
    overridden_by: int
    overridden_at: datetime = None

    def __post_init__(self):
        super().__post_init__()
        if not self.overridden_at:
            self.overridden_at = datetime.utcnow()


@dataclass
class WorkflowPhaseApproved(DomainEvent):
    """Event raised when a workflow phase is approved"""
    cycle_id: int
    report_id: int
    phase_name: str
    approved_by: int
    approval_notes: Optional[str] = None
    approved_at: datetime = None

    def __post_init__(self):
        super().__post_init__()
        if not self.approved_at:
            self.approved_at = datetime.utcnow()


@dataclass
class WorkflowPhaseRejected(DomainEvent):
    """Event raised when a workflow phase is rejected"""
    cycle_id: int
    report_id: int
    phase_name: str
    rejected_by: int
    rejection_reason: str
    rejected_at: datetime = None

    def __post_init__(self):
        super().__post_init__()
        if not self.rejected_at:
            self.rejected_at = datetime.utcnow()