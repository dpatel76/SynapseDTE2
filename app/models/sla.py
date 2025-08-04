"""
SLA Configuration and Management Models
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from enum import Enum
from app.models.base import CustomPKModel
from app.models.audit_mixin import AuditMixin
import logging

logger = logging.getLogger(__name__)


class SLAType(Enum):
    """SLA types for different phases and activities"""
    DATA_PROVIDER_IDENTIFICATION = "data_owner_identification"
    DATA_PROVIDER_RESPONSE = "data_owner_response"
    DOCUMENT_SUBMISSION = "document_submission"
    TESTING_COMPLETION = "testing_completion"
    OBSERVATION_RESPONSE = "observation_response"
    ISSUE_RESOLUTION = "issue_resolution"


class EscalationLevel(Enum):
    """Escalation levels for SLA violations"""
    LEVEL_1 = "level_1"  # Team Lead
    LEVEL_2 = "level_2"  # Manager
    LEVEL_3 = "level_3"  # Director
    LEVEL_4 = "level_4"  # Executive


class SLAConfiguration(CustomPKModel, AuditMixin):
    """SLA configuration settings"""
    
    __tablename__ = "universal_sla_configurations"
    
    sla_config_id = Column(Integer, primary_key=True, index=True)
    sla_type = Column(SQLEnum(SLAType), nullable=False, index=True)
    sla_hours = Column(Integer, nullable=False)  # SLA duration in hours
    warning_hours = Column(Integer, nullable=True)  # Warning threshold before breach
    escalation_enabled = Column(Boolean, default=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Business hours configuration
    business_hours_only = Column(Boolean, default=True, nullable=False)
    weekend_excluded = Column(Boolean, default=True, nullable=False)
    
    # Auto-escalation settings
    auto_escalate_on_breach = Column(Boolean, default=True, nullable=False)
    escalation_interval_hours = Column(Integer, default=24, nullable=False)  # Time between escalation levels
    
    # Relationships
    escalation_rules = relationship("SLAEscalationRule", back_populates="sla_config")
    violations = relationship("SLAViolationTracking", back_populates="sla_config")
    
    def calculate_due_date(self, start_time: datetime) -> datetime:
        """Calculate SLA due date considering business hours and weekends"""
        try:
            due_date = start_time
            remaining_hours = self.sla_hours
            
            while remaining_hours > 0:
                due_date += timedelta(hours=1)
                
                # Skip weekends if configured
                if self.weekend_excluded and due_date.weekday() >= 5:  # Saturday=5, Sunday=6
                    continue
                
                # Skip non-business hours if configured
                if self.business_hours_only:
                    hour = due_date.hour
                    if hour < 9 or hour >= 17:  # Outside 9 AM - 5 PM
                        continue
                
                remaining_hours -= 1
            
            return due_date
            
        except Exception as e:
            logger.error(f"Error calculating SLA due date: {str(e)}")
            # Fallback to simple calculation
            return start_time + timedelta(hours=self.sla_hours)
    
    def get_warning_date(self, start_time: datetime) -> datetime:
        """Calculate warning notification date"""
        if not self.warning_hours:
            return self.calculate_due_date(start_time)
        
        # Calculate warning time before due date
        due_date = self.calculate_due_date(start_time)
        warning_date = due_date - timedelta(hours=self.warning_hours)
        
        return max(warning_date, start_time)  # Warning can't be before start time
    
    def __repr__(self):
        return f"<SLAConfiguration(id={self.sla_config_id}, type='{self.sla_type}', hours={self.sla_hours})>"


class SLAEscalationRule(CustomPKModel, AuditMixin):
    """Escalation rules for SLA violations"""
    
    __tablename__ = "universal_sla_escalation_rules"
    
    escalation_rule_id = Column(Integer, primary_key=True, index=True)
    sla_config_id = Column(Integer, ForeignKey('universal_sla_configurations.sla_config_id'), nullable=False)
    escalation_level = Column(SQLEnum(EscalationLevel), nullable=False)
    escalation_order = Column(Integer, nullable=False)  # Order of escalation (1, 2, 3, 4)
    escalate_to_role = Column(String(100), nullable=False)  # Role to escalate to
    escalate_to_user_id = Column(Integer, ForeignKey('users.user_id'), nullable=True)  # Specific user (optional)
    hours_after_breach = Column(Integer, default=0, nullable=False)  # Hours after SLA breach to escalate
    
    # Email template settings
    email_template_subject = Column(String(255), nullable=False)
    email_template_body = Column(Text, nullable=False)
    include_managers = Column(Boolean, default=False, nullable=False)  # CC managers
    
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    sla_config = relationship("SLAConfiguration", back_populates="escalation_rules")
    escalate_to_user = relationship("User", foreign_keys=[escalate_to_user_id])
    escalation_logs = relationship("EscalationEmailLog", back_populates="escalation_rule")
    
    def __repr__(self):
        return f"<SLAEscalationRule(id={self.escalation_rule_id}, level='{self.escalation_level}', order={self.escalation_order})>"


class SLAViolationTracking(CustomPKModel, AuditMixin):
    """Track SLA violations and their resolution"""
    
    __tablename__ = "universal_sla_violation_trackings"
    
    violation_id = Column(Integer, primary_key=True, index=True)
    sla_config_id = Column(Integer, ForeignKey('universal_sla_configurations.sla_config_id'), nullable=False)
    report_id = Column(Integer, ForeignKey('reports.id'), nullable=False)
    cycle_id = Column(Integer, ForeignKey('test_cycles.cycle_id'), nullable=False)
    
    # Tracking details
    started_at = Column(DateTime, nullable=False)
    due_date = Column(DateTime, nullable=False)
    warning_date = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Violation status
    is_violated = Column(Boolean, default=False, nullable=False)
    violated_at = Column(DateTime, nullable=True)
    violation_hours = Column(Integer, nullable=True)  # Hours overdue
    
    # Escalation tracking
    current_escalation_level = Column(SQLEnum(EscalationLevel), nullable=True)
    escalation_count = Column(Integer, default=0, nullable=False)
    last_escalated_at = Column(DateTime, nullable=True)
    
    # Resolution
    is_resolved = Column(Boolean, default=False, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    # Relationships
    sla_config = relationship("SLAConfiguration", back_populates="violations")
    report = relationship("Report", foreign_keys=[report_id])
    cycle = relationship("TestCycle", foreign_keys=[cycle_id])
    escalation_emails = relationship("EscalationEmailLog", back_populates="sla_violation")
    
    def check_and_update_violation(self) -> bool:
        """Check if SLA is violated and update status"""
        try:
            current_time = datetime.utcnow()
            
            # Skip if already completed
            if self.completed_at:
                return False
            
            # Check if violated
            if current_time > self.due_date and not self.is_violated:
                self.is_violated = True
                self.violated_at = current_time
                self.violation_hours = int((current_time - self.due_date).total_seconds() / 3600)
                logger.warning(f"SLA violation detected: {self.violation_id}, overdue by {self.violation_hours} hours")
                return True
            
            # Update violation hours if already violated
            elif self.is_violated and not self.completed_at:
                self.violation_hours = int((current_time - self.due_date).total_seconds() / 3600)
                return False
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking SLA violation {self.violation_id}: {str(e)}")
            return False
    
    def should_escalate(self) -> bool:
        """Check if escalation is needed"""
        try:
            if not self.is_violated or self.is_resolved:
                return False
            
            current_time = datetime.utcnow()
            
            # Check if enough time has passed since last escalation
            if self.last_escalated_at:
                hours_since_escalation = (current_time - self.last_escalated_at).total_seconds() / 3600
                if hours_since_escalation < self.sla_config.escalation_interval_hours:
                    return False
            
            # Check if there are more escalation levels available
            available_rules = [r for r in self.sla_config.escalation_rules 
                             if r.escalation_order > self.escalation_count and r.is_active]
            
            return len(available_rules) > 0
            
        except Exception as e:
            logger.error(f"Error checking escalation for SLA violation {self.violation_id}: {str(e)}")
            return False
    
    def mark_completed(self, completion_time: datetime = None) -> None:
        """Mark SLA tracking as completed"""
        try:
            if not completion_time:
                completion_time = datetime.utcnow()
            
            self.completed_at = completion_time
            
            # If completed after due date, mark as violated
            if completion_time > self.due_date and not self.is_violated:
                self.is_violated = True
                self.violated_at = completion_time
                self.violation_hours = int((completion_time - self.due_date).total_seconds() / 3600)
            
            logger.info(f"SLA tracking completed: {self.violation_id}")
            
        except Exception as e:
            logger.error(f"Error marking SLA tracking completed {self.violation_id}: {str(e)}")
    
    def resolve_violation(self, resolution_notes: str = None) -> None:
        """Resolve the SLA violation"""
        try:
            self.is_resolved = True
            self.resolved_at = datetime.utcnow()
            self.resolution_notes = resolution_notes
            
            logger.info(f"SLA violation resolved: {self.violation_id}")
            
        except Exception as e:
            logger.error(f"Error resolving SLA violation {self.violation_id}: {str(e)}")
    
    def __repr__(self):
        return f"<SLAViolationTracking(id={self.violation_id}, violated={self.is_violated}, hours={self.violation_hours})>"


class EscalationEmailLog(CustomPKModel, AuditMixin):
    """Log of escalation emails sent"""
    
    __tablename__ = "escalation_email_logs"
    
    log_id = Column(Integer, primary_key=True, index=True)
    sla_violation_id = Column(Integer, ForeignKey('universal_sla_violation_trackings.violation_id'), nullable=False)
    escalation_rule_id = Column(Integer, ForeignKey('universal_sla_escalation_rules.escalation_rule_id'), nullable=False)
    report_id = Column(Integer, ForeignKey('reports.id'), nullable=False)
    
    # Email details
    sent_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    sent_to_emails = Column(Text, nullable=False)  # JSON array of email addresses
    email_subject = Column(String(255), nullable=False)
    email_body = Column(Text, nullable=False)
    
    # Delivery status
    delivery_status = Column(String(50), default="sent", nullable=False)  # sent, delivered, failed
    delivery_error = Column(Text, nullable=True)
    
    # Relationships
    sla_violation = relationship("SLAViolationTracking", back_populates="escalation_emails")
    escalation_rule = relationship("SLAEscalationRule", back_populates="escalation_logs")
    report = relationship("Report", foreign_keys=[report_id])
    
    def __repr__(self):
        return f"<EscalationEmailLog(id={self.log_id}, sent_at='{self.sent_at}', status='{self.delivery_status}')>" 