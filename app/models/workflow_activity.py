"""
Workflow Activity Models
For tracking individual activity status within workflow phases
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, JSON,
    ForeignKey, UniqueConstraint, Index, Enum as SQLEnum, ForeignKeyConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum
from datetime import datetime

from app.models.base import Base, TimestampMixin
from app.models.audit_mixin import AuditMixin


class ActivityStatus(str, Enum):
    """Activity status enumeration"""
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    REVISION_REQUESTED = "REVISION_REQUESTED"
    BLOCKED = "BLOCKED"
    SKIPPED = "SKIPPED"


class ActivityType(str, Enum):
    """Activity type enumeration"""
    START = "START"
    TASK = "TASK"
    REVIEW = "REVIEW"
    APPROVAL = "APPROVAL"
    COMPLETE = "COMPLETE"
    CUSTOM = "CUSTOM"


class WorkflowActivity(Base, TimestampMixin, AuditMixin):
    """Tracks individual activity status within workflow phases"""
    __tablename__ = "workflow_activities"
    
    activity_id = Column(Integer, primary_key=True, index=True)
    cycle_id = Column(Integer, ForeignKey('test_cycles.cycle_id'), nullable=False)
    report_id = Column(Integer, ForeignKey('reports.id'), nullable=False)
    phase_id = Column(Integer, ForeignKey('workflow_phases.phase_id'), nullable=False)
    phase_name = Column(String(100), nullable=False)  # Denormalized for convenience
    activity_name = Column(String(255), nullable=False)
    activity_type = Column(SQLEnum(ActivityType), nullable=False)
    activity_order = Column(Integer, nullable=False)
    status = Column(SQLEnum(ActivityStatus), nullable=False, default=ActivityStatus.NOT_STARTED)
    
    # Control flags
    can_start = Column(Boolean, nullable=False, default=False)
    can_complete = Column(Boolean, nullable=False, default=False)
    is_manual = Column(Boolean, nullable=False, default=True)
    is_optional = Column(Boolean, nullable=False, default=False)
    
    # Tracking fields
    started_at = Column(DateTime(timezone=True), nullable=True)
    started_by = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    completed_by = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    revision_requested_at = Column(DateTime(timezone=True), nullable=True)
    revision_requested_by = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    revision_reason = Column(Text, nullable=True)
    blocked_at = Column(DateTime(timezone=True), nullable=True)
    blocked_reason = Column(Text, nullable=True)
    
    # Metadata for extensibility
    activity_metadata = Column('metadata', JSON, nullable=True)
    
    # Timestamps are inherited from TimestampMixin
    
    # Relationships
    phase = relationship("WorkflowPhase", back_populates="activities")
    cycle = relationship("TestCycle", foreign_keys=[cycle_id])
    report = relationship("Report", foreign_keys=[report_id])
    started_by_user = relationship("User", foreign_keys=[started_by], backref="started_activities")
    completed_by_user = relationship("User", foreign_keys=[completed_by], backref="completed_activities")
    revision_requested_by_user = relationship("User", foreign_keys=[revision_requested_by], backref="revision_requested_activities")
    history = relationship("WorkflowActivityHistory", back_populates="activity", cascade="all, delete-orphan")
    
    # New unified planning phase relationships
    planning_versions = relationship("app.models.planning.PlanningVersion", back_populates="workflow_activity")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("cycle_id", "report_id", "phase_id", "activity_name", name="uq_workflow_activities_unique_activity"),
        Index("ix_workflow_activities_cycle_report", "cycle_id", "report_id"),
        Index("ix_workflow_activities_phase_id", "phase_id"),
        Index("ix_workflow_activities_status", "status"),
        Index("ix_workflow_activities_activity_name", "activity_name"),
        Index("ix_workflow_activities_cycle_report_phase", "cycle_id", "report_id", "phase_id"),
    )
    
    @property
    def duration_minutes(self) -> int:
        """Calculate duration in minutes if completed"""
        if self.completed_at and self.started_at:
            return int((self.completed_at - self.started_at).total_seconds() / 60)
        return 0
    
    @property
    def is_overdue(self) -> bool:
        """Check if activity is overdue based on metadata SLA"""
        if self.status in [ActivityStatus.COMPLETED, ActivityStatus.SKIPPED]:
            return False
        
        if self.activity_metadata and "sla_deadline" in self.activity_metadata:
            deadline = datetime.fromisoformat(self.activity_metadata["sla_deadline"])
            return datetime.utcnow() > deadline
        
        return False
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation"""
        return {
            "activity_id": self.activity_id,
            "cycle_id": self.cycle_id,
            "report_id": self.report_id,
            "phase_name": self.phase_name,
            "activity_name": self.activity_name,
            "activity_type": self.activity_type.value if self.activity_type else None,
            "activity_order": self.activity_order,
            "status": self.status.value if self.status else None,
            "can_start": self.can_start,
            "can_complete": self.can_complete,
            "is_manual": self.is_manual,
            "is_optional": self.is_optional,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "started_by": self.started_by,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "completed_by": self.completed_by,
            "duration_minutes": self.duration_minutes,
            "is_overdue": self.is_overdue,
            "revision_requested_at": self.revision_requested_at.isoformat() if self.revision_requested_at else None,
            "revision_reason": self.revision_reason,
            "blocked_reason": self.blocked_reason,
            "metadata": self.activity_metadata,
        }


class WorkflowActivityHistory(Base, TimestampMixin, AuditMixin):
    """Audit trail for workflow activity status changes"""
    __tablename__ = "workflow_activity_history"
    
    history_id = Column(Integer, primary_key=True, index=True)
    activity_id = Column(Integer, ForeignKey("workflow_activities.activity_id"), nullable=False)
    cycle_id = Column(Integer, nullable=False)
    report_id = Column(Integer, nullable=False)
    phase_name = Column(String(100), nullable=False)
    activity_name = Column(String(255), nullable=False)
    from_status = Column(String(50), nullable=True)
    to_status = Column(String(50), nullable=False)
    changed_by = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    changed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    change_reason = Column(Text, nullable=True)
    history_metadata = Column('metadata', JSON, nullable=True)
    
    # Relationships
    activity = relationship("WorkflowActivity", back_populates="history")
    changed_by_user = relationship("User", foreign_keys=[changed_by], backref="activity_changes")
    
    # Indexes
    __table_args__ = (
        Index("ix_workflow_activity_history_activity", "activity_id"),
        Index("ix_workflow_activity_history_changed_at", "changed_at"),
    )


class WorkflowActivityDependency(Base, TimestampMixin, AuditMixin):
    """Defines dependencies between activities"""
    __tablename__ = "workflow_activity_dependencies"
    
    dependency_id = Column(Integer, primary_key=True, index=True)
    phase_name = Column(String(100), nullable=False)
    activity_name = Column(String(255), nullable=False)
    depends_on_activity = Column(String(255), nullable=False)
    dependency_type = Column(String(50), nullable=False, default="completion")  # completion, approval, any
    is_active = Column(Boolean, nullable=False, default=True)
    # created_at is inherited from TimestampMixin
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("phase_name", "activity_name", "depends_on_activity", name="uq_activity_dependencies_unique"),
    )


class WorkflowActivityTemplate(Base, TimestampMixin, AuditMixin):
    """Templates for standard activities per phase"""
    __tablename__ = "workflow_activity_templates"
    
    template_id = Column(Integer, primary_key=True, index=True)
    phase_name = Column(String(100), nullable=False)
    activity_name = Column(String(255), nullable=False)
    activity_type = Column(SQLEnum(ActivityType), nullable=False)
    activity_order = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    is_manual = Column(Boolean, nullable=False, default=True)
    is_optional = Column(Boolean, nullable=False, default=False)
    required_role = Column(String(100), nullable=True)
    auto_complete_on_event = Column(String(100), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    # Timestamps are inherited from TimestampMixin
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("phase_name", "activity_name", name="uq_activity_templates_unique"),
        Index("ix_workflow_activity_templates_phase", "phase_name"),
    )
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation"""
        return {
            "template_id": self.template_id,
            "phase_name": self.phase_name,
            "activity_name": self.activity_name,
            "activity_type": self.activity_type.value if self.activity_type else None,
            "activity_order": self.activity_order,
            "description": self.description,
            "is_manual": self.is_manual,
            "is_optional": self.is_optional,
            "required_role": self.required_role,
            "auto_complete_on_event": self.auto_complete_on_event,
            "is_active": self.is_active,
        }