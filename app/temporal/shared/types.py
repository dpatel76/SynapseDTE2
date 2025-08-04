"""Temporal workflow data types"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class WorkflowStatus(str, Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class PhaseStatus(str, Enum):
    """Individual phase status"""
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    COMPLETE = "Complete"
    BLOCKED = "Blocked"
    SKIPPED = "Skipped"


@dataclass
class WorkflowContext:
    """Context passed between workflow activities"""
    cycle_id: int
    report_id: int
    cycle_report_id: int
    user_id: int
    metadata: Dict[str, Any]


@dataclass
class PhaseResult:
    """Result of a workflow phase execution"""
    phase_name: str
    status: PhaseStatus
    started_at: datetime
    completed_at: Optional[datetime]
    result_data: Dict[str, Any]
    error_message: Optional[str] = None


@dataclass
class TestCycleWorkflowInput:
    """Input for test cycle workflow"""
    cycle_id: int
    initiated_by_user_id: int
    report_ids: List[int] = None
    auto_assign_testers: bool = True
    auto_generate_attributes: bool = True
    skip_phases: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.report_ids is None:
            self.report_ids = []
        if self.skip_phases is None:
            self.skip_phases = []
        if self.metadata is None:
            self.metadata = {}
    
    def dict(self):
        """Convert to dictionary"""
        return {
            "cycle_id": self.cycle_id,
            "initiated_by_user_id": self.initiated_by_user_id,
            "report_ids": self.report_ids,
            "auto_assign_testers": self.auto_assign_testers,
            "auto_generate_attributes": self.auto_generate_attributes,
            "skip_phases": self.skip_phases,
            "metadata": self.metadata
        }


@dataclass
class ReportTestingWorkflowInput:
    """Input for individual report testing workflow"""
    cycle_report_id: int
    report_id: int
    tester_id: int
    start_from_phase: Optional[str] = None


@dataclass
class LLMAnalysisWorkflowInput:
    """Input for LLM analysis workflow"""
    document_text: str
    document_type: str
    analysis_type: str  # "attributes", "test_recommendations", "pattern_analysis"
    metadata: Dict[str, Any]


@dataclass
class NotificationData:
    """Data for notification activities"""
    recipient_user_ids: List[int]
    notification_type: str
    subject: str
    message: str
    metadata: Dict[str, Any]


@dataclass
class SLAMonitoringInput:
    """Input for SLA monitoring workflow"""
    report_id: int
    sla_type: str
    started_at: datetime
    due_date: datetime


@dataclass
class ActivityResult:
    """Generic activity result"""
    success: bool
    data: Dict[str, Any]
    error_message: Optional[str] = None


@dataclass
class TestExecutionData:
    """Data for test execution activities"""
    test_case_id: int
    sample_id: int
    attribute_id: int
    test_type: str  # "document", "database"
    expected_value: Any
    actual_value: Optional[Any] = None
    test_passed: Optional[bool] = None


@dataclass
class ObservationData:
    """Data for observation management"""
    cycle_report_id: int
    observation_type: str
    title: str
    description: str
    severity: str
    created_by: int
    attribute_id: Optional[int] = None
    test_result_id: Optional[int] = None