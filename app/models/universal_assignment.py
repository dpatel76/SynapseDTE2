"""
Universal Assignment Framework
Handles all role-to-role interactions, approvals, and task assignments across the system
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ENUM, JSONB
from app.models.base import CustomPKModel
from app.models.audit_mixin import AuditMixin
from datetime import datetime
import uuid

# Universal assignment types - covers all possible interactions
assignment_type_enum = ENUM(
    # Data & File Management
    'Data Upload Request',
    'File Review', 
    'File Approval',
    'Document Review',
    'Data Validation',
    
    # Approval Workflows
    'Scoping Approval',
    'Sample Selection Approval', 
    'Rule Approval',
    'Observation Approval',
    'Report Approval',
    'Version Approval',
    
    # Phase Management
    'Phase Review',
    'Phase Approval',
    'Phase Completion',
    'Workflow Progression',
    
    # Specialized Tasks
    'LOB Assignment',
    'Test Execution Review',
    'Quality Review',
    'Compliance Review',
    'Risk Assessment',
    
    # Information Requests
    'Information Request',
    'Clarification Required',
    'Additional Data Required',
    
    # Administrative
    'Role Assignment',
    'Permission Grant',
    'System Configuration',
    
    name='universal_assignment_type_enum'
)

# Universal assignment status
assignment_status_enum = ENUM(
    'Assigned',        # Initial state - assigned to recipient
    'Acknowledged',    # Recipient has seen the assignment
    'In Progress',     # Work has started
    'Completed',       # Work completed by recipient
    'Approved',        # Reviewed and approved (if approval needed)
    'Rejected',        # Reviewed and rejected (if approval needed)
    'Cancelled',       # Assignment cancelled by originator
    'Overdue',         # Past due date
    'Escalated',       # Escalated to higher authority
    'On Hold',         # Temporarily paused
    'Delegated',       # Reassigned to someone else
    name='universal_assignment_status_enum'
)

# Priority levels
assignment_priority_enum = ENUM(
    'Low',
    'Medium', 
    'High',
    'Critical',
    'Urgent',
    name='universal_assignment_priority_enum'
)

# Context types to categorize assignments
context_type_enum = ENUM(
    'Test Cycle',      # Related to a specific test cycle
    'Report',          # Related to a specific report
    'Phase',           # Related to a workflow phase
    'Attribute',       # Related to a report attribute
    'Sample',          # Related to sample selection
    'Rule',            # Related to profiling rules
    'Observation',     # Related to observations
    'File',            # Related to file management
    'System',          # System-wide assignments
    'User',            # User-specific assignments
    name='universal_context_type_enum'
)


class UniversalAssignment(CustomPKModel, AuditMixin):
    """
    Universal assignment model for all role-to-role interactions
    Replaces all specific assignment tables with a unified approach
    """
    
    __tablename__ = "universal_assignments"
    
    # Core Identity
    assignment_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    assignment_type = Column(assignment_type_enum, nullable=False, index=True)
    
    # Role Information
    from_role = Column(String(50), nullable=False, index=True)    # Role creating the assignment
    to_role = Column(String(50), nullable=False, index=True)      # Role receiving the assignment
    from_user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)  # Specific user creating
    to_user_id = Column(Integer, ForeignKey('users.user_id'), nullable=True)     # Specific user assigned (null = any user with to_role)
    
    # Assignment Details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    task_instructions = Column(Text, nullable=True)  # Detailed instructions for the task
    
    # Context Information
    context_type = Column(context_type_enum, nullable=False, index=True)
    context_data = Column(JSONB, nullable=True)  # Flexible context: cycle_id, report_id, phase_name, etc.
    
    # Status & Priority
    status = Column(assignment_status_enum, default='Assigned', nullable=False, index=True)
    priority = Column(assignment_priority_enum, default='Medium', nullable=False)
    
    # Timing
    assigned_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.utcnow())
    due_date = Column(DateTime(timezone=True), nullable=True, index=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Completion Information
    completed_by_user_id = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    completion_notes = Column(Text, nullable=True)
    completion_data = Column(JSONB, nullable=True)  # Structured completion data
    completion_attachments = Column(JSONB, nullable=True)  # File attachments
    
    # Approval Workflow (if required)
    requires_approval = Column(Boolean, default=False, nullable=False)
    approval_role = Column(String(50), nullable=True)  # Role that needs to approve
    approved_by_user_id = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approval_notes = Column(Text, nullable=True)
    
    # Escalation & Delegation
    escalated = Column(Boolean, default=False, nullable=False)
    escalated_at = Column(DateTime(timezone=True), nullable=True)
    escalated_to_user_id = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    escalation_reason = Column(Text, nullable=True)
    
    delegated_to_user_id = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    delegated_at = Column(DateTime(timezone=True), nullable=True)
    delegation_reason = Column(Text, nullable=True)
    
    # System Fields
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.utcnow())
    
    # Metadata
    assignment_metadata = Column(JSONB, nullable=True)  # Flexible metadata for specific use cases
    workflow_step = Column(String(100), nullable=True)  # Which step in the workflow this represents
    parent_assignment_id = Column(String(36), ForeignKey('universal_assignments.assignment_id'), nullable=True)  # For sub-assignments
    
    # Relationships
    from_user = relationship("User", foreign_keys=[from_user_id], back_populates="created_assignments")
    to_user = relationship("User", foreign_keys=[to_user_id], back_populates="received_assignments")
    completed_by_user = relationship("User", foreign_keys=[completed_by_user_id], back_populates="completed_assignments")
    approved_by_user = relationship("User", foreign_keys=[approved_by_user_id], back_populates="approved_assignments")
    escalated_to_user = relationship("User", foreign_keys=[escalated_to_user_id], back_populates="escalated_assignments")
    delegated_to_user = relationship("User", foreign_keys=[delegated_to_user_id], back_populates="delegated_assignments")
    
    # Self-referential for parent/child assignments
    parent_assignment = relationship("UniversalAssignment", remote_side=[assignment_id], back_populates="child_assignments")
    child_assignments = relationship("UniversalAssignment", back_populates="parent_assignment")
    
    def __repr__(self):
        return f"<UniversalAssignment(id={self.assignment_id}, type='{self.assignment_type}', from={self.from_role}, to={self.to_role}, status='{self.status}')>"
    
    # Computed Properties
    @property
    def is_overdue(self) -> bool:
        """Check if assignment is overdue"""
        if not self.due_date or self.status in ['Completed', 'Approved', 'Cancelled']:
            return False
        from datetime import timezone
        now = datetime.now(timezone.utc)
        return now > self.due_date
    
    @property
    def days_until_due(self) -> int:
        """Calculate days until due date"""
        if not self.due_date:
            return 999  # No due date
        from datetime import timezone
        now = datetime.now(timezone.utc)
        delta = self.due_date - now
        return delta.days
    
    @property
    def is_active(self) -> bool:
        """Check if assignment is in an active state"""
        return self.status in ['Assigned', 'Acknowledged', 'In Progress']
    
    @property
    def is_completed(self) -> bool:
        """Check if assignment is completed (regardless of approval)"""
        return self.status in ['Completed', 'Approved', 'Rejected']
    
    # Action Methods
    def acknowledge(self, user_id: int):
        """Mark assignment as acknowledged"""
        if self.status == 'Assigned':
            self.status = 'Acknowledged'
            self.acknowledged_at = datetime.utcnow()
            self.updated_at = datetime.utcnow()
    
    def start_work(self, user_id: int):
        """Mark assignment as in progress"""
        if self.status in ['Assigned', 'Acknowledged']:
            self.status = 'In Progress'
            self.started_at = datetime.utcnow()
            self.updated_at = datetime.utcnow()
    
    def complete(self, user_id: int, completion_notes: str = None, completion_data: dict = None):
        """Mark assignment as completed"""
        self.status = 'Completed'
        self.completed_at = datetime.utcnow()
        self.completed_by_user_id = user_id
        if completion_notes:
            self.completion_notes = completion_notes
        if completion_data:
            self.completion_data = completion_data
        self.updated_at = datetime.utcnow()
    
    def approve(self, user_id: int, approval_notes: str = None):
        """Approve the assignment"""
        self.status = 'Approved'
        self.approved_by_user_id = user_id
        self.approved_at = datetime.utcnow()
        if approval_notes:
            self.approval_notes = approval_notes
        self.updated_at = datetime.utcnow()
    
    def reject(self, user_id: int, rejection_reason: str):
        """Reject the assignment"""
        self.status = 'Rejected'
        self.approved_by_user_id = user_id
        self.approved_at = datetime.utcnow()
        self.approval_notes = rejection_reason
        self.updated_at = datetime.utcnow()
    
    def escalate(self, user_id: int, escalation_reason: str, escalated_to_user_id: int = None):
        """Escalate the assignment"""
        self.escalated = True
        self.escalated_at = datetime.utcnow()
        self.escalation_reason = escalation_reason
        if escalated_to_user_id:
            self.escalated_to_user_id = escalated_to_user_id
        self.status = 'Escalated'
        self.updated_at = datetime.utcnow()
    
    def delegate(self, user_id: int, delegated_to_user_id: int, delegation_reason: str = None):
        """Delegate the assignment to another user"""
        self.delegated_to_user_id = delegated_to_user_id
        self.delegated_at = datetime.utcnow()
        self.delegation_reason = delegation_reason
        self.status = 'Delegated'
        self.updated_at = datetime.utcnow()


class UniversalAssignmentHistory(CustomPKModel, AuditMixin):
    """
    History/audit trail for all assignment changes
    """
    
    __tablename__ = "universal_assignment_history"
    
    history_id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(String(36), ForeignKey('universal_assignments.assignment_id'), nullable=False)
    changed_by_user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    changed_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.utcnow())
    
    # Change Details
    action = Column(String(50), nullable=False)  # 'created', 'acknowledged', 'started', 'completed', 'approved', etc.
    field_changed = Column(String(100), nullable=True)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    change_reason = Column(Text, nullable=True)
    change_metadata = Column(JSONB, nullable=True)
    
    # Relationships
    assignment = relationship("UniversalAssignment")
    changed_by_user = relationship("User", foreign_keys=[changed_by_user_id], back_populates="assignment_changes")
    
    def __repr__(self):
        return f"<UniversalAssignmentHistory(id={self.history_id}, action='{self.action}', assignment='{self.assignment_id}')>"


class AssignmentTemplate(CustomPKModel, AuditMixin):
    """
    Templates for common assignment types to ensure consistency
    """
    
    __tablename__ = "assignment_templates"
    
    template_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    template_name = Column(String(255), nullable=False)
    assignment_type = Column(assignment_type_enum, nullable=False)
    from_role = Column(String(50), nullable=False)
    to_role = Column(String(50), nullable=False)
    
    # Template Content
    title_template = Column(String(255), nullable=False)  # Can use placeholders like {report_name}
    description_template = Column(Text, nullable=True)
    task_instructions_template = Column(Text, nullable=True)
    
    # Default Settings
    default_priority = Column(assignment_priority_enum, default='Medium', nullable=False)
    default_due_days = Column(Integer, nullable=True)  # Days from creation
    requires_approval = Column(Boolean, default=False, nullable=False)
    approval_role = Column(String(50), nullable=True)
    
    # Template Metadata
    context_type = Column(context_type_enum, nullable=False)
    workflow_step = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.utcnow())
    
    def __repr__(self):
        return f"<AssignmentTemplate(id={self.template_id}, name='{self.template_name}', type='{self.assignment_type}')>"