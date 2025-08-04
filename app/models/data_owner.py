"""
Data Provider Identification phase models
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ENUM, JSONB, UUID
from app.models.base import CustomPKModel
from app.models.audit_mixin import AuditMixin

# Escalation level enum
escalation_level_enum = ENUM(
    'None',
    'Level 1',
    'Level 2',
    'Level 3',
    name='escalation_level_enum'
)


class AttributeLOBAssignment_DEPRECATED(CustomPKModel, AuditMixin):
    """DEPRECATED - Table doesn't exist. Attribute to LOB assignments model"""
    
    __tablename__ = "attribute_lob_assignments_deprecated"
    
    assignment_id = Column(Integer, primary_key=True, index=True)
    cycle_id = Column(Integer, ForeignKey('test_cycles.cycle_id'), nullable=False)
    phase_id = Column(Integer, ForeignKey('workflow_phases.phase_id'), nullable=False)
    attribute_id = Column(UUID(as_uuid=True), ForeignKey("cycle_report_planning_attributes.id"), nullable=False)
    lob_id = Column(Integer, ForeignKey('lobs.lob_id'), nullable=False)
    assigned_by = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    assigned_at = Column(DateTime(timezone=True), nullable=False)
    assignment_rationale = Column(Text, nullable=True)
    
    # Relationships - DEPRECATED: Commented out as table doesn't exist
    # cycle = relationship("TestCycle", back_populates="attribute_lob_assignments")
    # phase = relationship("WorkflowPhase", foreign_keys=[phase_id])
    # attribute = relationship("ReportAttribute", foreign_keys=[attribute_id])
    # lob = relationship("LOB", back_populates="attribute_assignments")
    # assigned_by_user = relationship("User", foreign_keys=[assigned_by])
    
    def __repr__(self):
        return f"<AttributeLOBAssignment(id={self.assignment_id}, attribute_id={self.attribute_id}, lob_id={self.lob_id})>"


# CDONotification model has been deprecated and replaced by universal assignments
# The table has been renamed to data_executive_notifications but is no longer used
# Keeping this comment for historical reference
#
# class CDONotification(CustomPKModel, AuditMixin):
#     """DEPRECATED: CDO notification tracking model - replaced by universal assignments"""
#     
#     __tablename__ = "data_executive_notifications"  # Renamed table
#     
#     notification_id = Column(Integer, primary_key=True, index=True)
#     cycle_id = Column(Integer, ForeignKey('test_cycles.cycle_id'), nullable=False)
#     report_id = Column(Integer, ForeignKey('reports.id'), nullable=False)
#     data_executive_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
#     lob_id = Column(Integer, ForeignKey('lobs.lob_id'), nullable=False)
#     notification_sent_at = Column(DateTime(timezone=True), nullable=False)
#     assignment_deadline = Column(DateTime(timezone=True), nullable=False)
#     sla_hours = Column(Integer, default=24, nullable=False)
#     notification_data = Column(JSONB, nullable=True)  # Store notification details
#     responded_at = Column(DateTime(timezone=True), nullable=True)
#     is_complete = Column(Boolean, default=False, nullable=False)
#     
#     # Relationships
#     cycle = relationship("TestCycle")
#     report = relationship("Report")
#     data_executive = relationship("User")
#     lob = relationship("LOB")
#     
#     def __repr__(self):
#         return f"<CDONotification(id={self.notification_id}, data_executive_id={self.data_executive_id}, lob_id={self.lob_id})>"


# DEPRECATED: HistoricalDataOwnerAssignment - table doesn't exist
# Using universal assignments instead
class HistoricalDataOwnerAssignment(CustomPKModel, AuditMixin):
    """DEPRECATED - Table doesn't exist. Historical data owner assignments for knowledge tracking"""
    
    __tablename__ = "historical_data_owner_assignments_deprecated"
    
    history_id = Column(Integer, primary_key=True, index=True)
    report_name = Column(String(255), nullable=False, index=True)
    attribute_name = Column(String(255), nullable=False, index=True)
    data_owner_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    assigned_by = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    cycle_id = Column(Integer, ForeignKey('test_cycles.cycle_id'), nullable=False)
    assigned_at = Column(DateTime(timezone=True), nullable=False)
    completion_status = Column(String(50), nullable=False)  # Completed, Failed, Incomplete
    completion_time_hours = Column(Float, nullable=True)
    success_rating = Column(Float, nullable=True)  # 0.0 to 1.0
    notes = Column(Text, nullable=True)
    
    # Relationships - DEPRECATED: Commented out as table doesn't exist
    # data_owner = relationship("User", foreign_keys=[data_owner_id], back_populates="historical_assignments")
    # assigned_by_user = relationship("User", foreign_keys=[assigned_by], back_populates="historical_assignments_made")
    # cycle = relationship("TestCycle", back_populates="historical_assignments")
    
    def __repr__(self):
        return f"<HistoricalDataOwnerAssignment(id={self.history_id}, report='{self.report_name}', attribute='{self.attribute_name}')>"


class DataOwnerSLAViolation(CustomPKModel, AuditMixin):
    """Data Owner SLA violation tracking model"""
    
    __tablename__ = "data_owner_sla_violations"
    
    violation_id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey('data_owner_assignments.assignment_id'), nullable=False)
    cycle_id = Column(Integer, ForeignKey('test_cycles.cycle_id'), nullable=False)
    phase_id = Column(Integer, ForeignKey('workflow_phases.phase_id'), nullable=False)
    attribute_id = Column(UUID(as_uuid=True), ForeignKey("cycle_report_planning_attributes.id"), nullable=False)
    cdo_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    violation_detected_at = Column(DateTime(timezone=True), nullable=False)
    original_deadline = Column(DateTime(timezone=True), nullable=False)
    hours_overdue = Column(Float, nullable=False)
    escalation_level = Column(escalation_level_enum, default='None', nullable=False)
    last_escalation_at = Column(DateTime(timezone=True), nullable=True)
    is_resolved = Column(Boolean, default=False, nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships - Connected through WorkflowPhase, not directly to Report
    # assignment = relationship("DataOwnerAssignment", back_populates="sla_violations")  # DataOwnerAssignment removed
    # cycle = relationship("TestCycle")  # back_populates removed - TestCycle doesn't have sla_violations
    phase = relationship("WorkflowPhase", foreign_keys=[phase_id])
    attribute = relationship("ReportAttribute", foreign_keys=[attribute_id])
    cdo = relationship("User", foreign_keys=[cdo_id])
    
    def __repr__(self):
        return f"<DataOwnerSLAViolation(id={self.violation_id}, hours_overdue={self.hours_overdue})>"


class DataOwnerEscalationLog(CustomPKModel, AuditMixin):
    """Data Owner escalation email tracking model"""
    
    __tablename__ = "data_owner_escalation_log"
    
    email_id = Column(Integer, primary_key=True, index=True)
    phase_id = Column(Integer, ForeignKey('workflow_phases.phase_id'), nullable=False)
    violation_ids = Column(JSONB, nullable=False)  # List of violation IDs
    escalation_level = Column(escalation_level_enum, nullable=False)
    sent_by = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    sent_to = Column(JSONB, nullable=False)  # List of recipient email addresses
    cc_recipients = Column(JSONB, nullable=True)  # List of CC recipients
    email_subject = Column(String(255), nullable=False)
    email_body = Column(Text, nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=False)
    delivery_status = Column(String(50), default='Sent', nullable=False)
    custom_message = Column(Text, nullable=True)
    
    # Relationships - Connected through WorkflowPhase only
    phase = relationship("WorkflowPhase", foreign_keys=[phase_id])
    sent_by_user = relationship("User", foreign_keys=[sent_by])
    
    def __repr__(self):
        return f"<DataOwnerEscalationLog(id={self.email_id}, level='{self.escalation_level}', sent_at={self.sent_at})>"


class DataOwnerPhaseAuditLog(CustomPKModel, AuditMixin):
    """Audit log for data owner phase actions"""
    
    __tablename__ = "data_owner_phase_audit_log"
    
    audit_id = Column(Integer, primary_key=True, index=True)
    phase_id = Column(Integer, ForeignKey('workflow_phases.phase_id'), nullable=False)
    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)  # AttributeLOBAssignment, DataOwnerAssignment, etc.
    entity_id = Column(Integer, nullable=True)
    performed_by = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    performed_at = Column(DateTime(timezone=True), nullable=False)
    old_values = Column(JSONB, nullable=True)
    new_values = Column(JSONB, nullable=True)
    notes = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Relationships - Connected through WorkflowPhase only
    phase = relationship("WorkflowPhase", foreign_keys=[phase_id])
    user = relationship("User", foreign_keys=[performed_by])
    
    def __repr__(self):
        return f"<DataOwnerPhaseAuditLog(id={self.audit_id}, action='{self.action}', performed_by={self.performed_by})>" 