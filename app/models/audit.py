"""
Audit and configuration models
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from app.models.base import CustomPKModel, Base
from app.models.audit_mixin import AuditMixin


class LLMAuditLog(CustomPKModel, AuditMixin):
    """LLM audit trail model"""
    
    __tablename__ = "llm_audit_log"
    
    log_id = Column(Integer, primary_key=True, index=True)
    cycle_id = Column(Integer, ForeignKey('test_cycles.cycle_id'), nullable=True)
    report_id = Column(Integer, ForeignKey('reports.id'), nullable=True)
    llm_provider = Column(String(50), nullable=False, index=True)
    prompt_template = Column(String(255), nullable=False)
    request_payload = Column(JSONB, nullable=False)
    response_payload = Column(JSONB, nullable=False)
    execution_time_ms = Column(Integer, nullable=True)
    token_usage = Column(JSONB, nullable=True)
    executed_at = Column(DateTime(timezone=True), nullable=False)
    executed_by = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    
    # Relationships
    cycle = relationship("TestCycle", back_populates="llm_audit_logs")
    executed_by_user = relationship("User", foreign_keys=[executed_by], back_populates="llm_audit_logs")
    
    def __repr__(self):
        return f"<LLMAuditLog(id={self.log_id}, provider='{self.llm_provider}', template='{self.prompt_template}')>"


class AuditLog(Base):
    """System audit log model"""
    
    __tablename__ = "audit_logs"
    
    audit_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    action = Column(String(100), nullable=False, index=True)
    table_name = Column(String(100), nullable=True)
    record_id = Column(Integer, nullable=True)
    old_values = Column(JSONB, nullable=True)
    new_values = Column(JSONB, nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    session_id = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="audit_logs")
    
    def __repr__(self):
        return f"<AuditLog(id={self.audit_id}, action='{self.action}', table='{self.table_name}')>" 