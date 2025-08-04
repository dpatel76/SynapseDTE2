"""Workflow DTOs"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List


@dataclass
class PhaseStatusDTO:
    """DTO for workflow phase status"""
    cycle_id: int
    report_id: int
    phase_name: str
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    updated_by: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class UpdatePhaseStatusDTO:
    """DTO for updating phase status"""
    cycle_id: int
    report_id: int
    phase_name: str
    status: str
    updated_by: int
    metadata: Optional[Dict[str, Any]] = None
    comments: Optional[str] = None


@dataclass
class WorkflowTransitionDTO:
    """DTO for workflow transition request"""
    cycle_id: int
    report_id: int
    from_phase: str
    to_phase: str
    requested_by: int
    override_dependencies: bool = False
    reason: Optional[str] = None


@dataclass
class WorkflowStateDTO:
    """DTO for complete workflow state"""
    cycle_id: int
    report_id: int
    current_phase: str
    phases: List[PhaseStatusDTO]
    can_advance: bool
    next_available_phases: List[str]
    sla_status: Optional[Dict[str, Any]] = None