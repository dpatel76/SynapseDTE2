"""Workflow Tracking Models for Temporal Integration

Tracks workflow steps, substeps, transitions, and timing metrics
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, DateTime, Float, 
    ForeignKey, Text, JSON, Boolean, Enum as SQLEnum,
    Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from enum import Enum

from app.models.base import CustomPKModel
from app.models.audit_mixin import AuditMixin


class WorkflowExecutionStatus(str, Enum):
    """Status of workflow execution"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"


class StepType(str, Enum):
    """Type of workflow step"""
    PHASE = "phase"
    ACTIVITY = "activity"
    TRANSITION = "transition"
    DECISION = "decision"
    PARALLEL_BRANCH = "parallel_branch"
    SUB_WORKFLOW = "sub_workflow"


class WorkflowExecution(CustomPKModel, AuditMixin):
    """Tracks overall workflow execution"""
    __tablename__ = "workflow_executions"
    
    execution_id = Column(String(36), primary_key=True)
    workflow_id = Column(String(100), nullable=False)  # Temporal workflow ID
    workflow_run_id = Column(String(100), nullable=False)  # Temporal run ID
    workflow_type = Column(String(100), nullable=False)  # e.g., "TestCycleWorkflow"
    workflow_version = Column(String(20), default="1.0")
    
    # Business context
    cycle_id = Column(Integer, ForeignKey("test_cycles.cycle_id"), nullable=False)
    report_id = Column(Integer, ForeignKey("reports.id"))
    initiated_by = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    
    # Execution details
    status = Column(SQLEnum(WorkflowExecutionStatus), default=WorkflowExecutionStatus.PENDING)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Float)
    
    # Metadata
    input_data = Column(JSON)
    output_data = Column(JSON)
    error_details = Column(JSON)
    
    # Relationships
    cycle = relationship("TestCycle")
    report = relationship("Report")
    user = relationship("User", foreign_keys=[initiated_by])
    steps = relationship("WorkflowStep", back_populates="execution", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_workflow_executions_cycle', 'cycle_id'),
        Index('idx_workflow_executions_status', 'status'),
        Index('idx_workflow_executions_started', 'started_at'),
    )


class WorkflowStep(CustomPKModel, AuditMixin):
    """Tracks individual steps within a workflow execution"""
    __tablename__ = "workflow_steps"
    
    step_id = Column(String(36), primary_key=True)
    execution_id = Column(String(36), ForeignKey("workflow_executions.execution_id"), nullable=False)
    parent_step_id = Column(String(36), ForeignKey("workflow_steps.step_id"))
    
    # Step details
    step_name = Column(String(100), nullable=False)
    step_type = Column(SQLEnum(StepType), nullable=False)
    phase_name = Column(String(50))  # Maps to workflow phase
    activity_name = Column(String(100))  # Specific activity within phase
    
    # Execution details
    status = Column(SQLEnum(WorkflowExecutionStatus), default=WorkflowExecutionStatus.PENDING)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Float)
    
    # Retry information
    attempt_number = Column(Integer, default=1)
    max_attempts = Column(Integer, default=3)
    retry_delay_seconds = Column(Integer)
    
    # Step data
    input_data = Column(JSON)
    output_data = Column(JSON)
    error_details = Column(JSON)
    
    # Relationships
    execution = relationship("WorkflowExecution", back_populates="steps")
    parent_step = relationship("WorkflowStep", remote_side=[step_id], backref="substeps")
    transitions = relationship("WorkflowTransition", foreign_keys="WorkflowTransition.from_step_id", back_populates="from_step")
    
    # Indexes
    __table_args__ = (
        Index('idx_workflow_steps_execution', 'execution_id'),
        Index('idx_workflow_steps_status', 'status'),
        Index('idx_workflow_steps_phase', 'phase_name'),
    )


class WorkflowTransition(CustomPKModel, AuditMixin):
    """Tracks transitions between workflow steps"""
    __tablename__ = "workflow_transitions"
    
    transition_id = Column(String(36), primary_key=True)
    execution_id = Column(String(36), ForeignKey("workflow_executions.execution_id"), nullable=False)
    
    # Transition details
    from_step_id = Column(String(36), ForeignKey("workflow_steps.step_id"))
    to_step_id = Column(String(36), ForeignKey("workflow_steps.step_id"))
    transition_type = Column(String(50))  # sequential, parallel_fork, parallel_join, conditional
    
    # Timing
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Float)
    
    # Transition logic
    condition_evaluated = Column(String(200))  # For conditional transitions
    condition_result = Column(Boolean)
    
    # Relationships
    from_step = relationship("WorkflowStep", foreign_keys=[from_step_id], back_populates="transitions")
    to_step = relationship("WorkflowStep", foreign_keys=[to_step_id])
    
    # Indexes
    __table_args__ = (
        Index('idx_workflow_transitions_execution', 'execution_id'),
        Index('idx_workflow_transitions_timing', 'started_at', 'completed_at'),
    )


class WorkflowMetrics(CustomPKModel, AuditMixin):
    """Aggregated metrics for workflow performance analysis"""
    __tablename__ = "workflow_metrics"
    
    metric_id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Aggregation level
    workflow_type = Column(String(100), nullable=False)
    phase_name = Column(String(50))
    activity_name = Column(String(100))
    step_type = Column(SQLEnum(StepType))
    
    # Time period
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    
    # Metrics
    execution_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    
    # Duration statistics (in seconds)
    avg_duration = Column(Float)
    min_duration = Column(Float)
    max_duration = Column(Float)
    p50_duration = Column(Float)  # Median
    p90_duration = Column(Float)
    p95_duration = Column(Float)
    p99_duration = Column(Float)
    
    # Additional metrics
    avg_retry_count = Column(Float)
    timeout_count = Column(Integer, default=0)
    
    # Indexes
    __table_args__ = (
        Index('idx_workflow_metrics_type_period', 'workflow_type', 'period_start'),
        Index('idx_workflow_metrics_phase_period', 'phase_name', 'period_start'),
        UniqueConstraint('workflow_type', 'phase_name', 'activity_name', 'step_type', 'period_start', 'period_end'),
    )


class WorkflowAlert(CustomPKModel, AuditMixin):
    """Alerts for workflow performance issues"""
    __tablename__ = "workflow_alerts"
    
    alert_id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Alert context
    execution_id = Column(String(36), ForeignKey("workflow_executions.execution_id"))
    workflow_type = Column(String(100))
    phase_name = Column(String(50))
    
    # Alert details
    alert_type = Column(String(50), nullable=False)  # slow_execution, high_failure_rate, sla_breach
    severity = Column(String(20), nullable=False)  # low, medium, high, critical
    
    # Alert data
    threshold_value = Column(Float)
    actual_value = Column(Float)
    alert_message = Column(Text)
    
    # Status
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(Integer, ForeignKey("users.user_id"))
    acknowledged_at = Column(DateTime(timezone=True))
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime(timezone=True))
    
    # Indexes
    __table_args__ = (
        Index('idx_workflow_alerts_unresolved', 'resolved', 'created_at'),
        Index('idx_workflow_alerts_severity', 'severity', 'created_at'),
    )