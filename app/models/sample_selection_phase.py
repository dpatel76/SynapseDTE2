"""Sample Selection Phase model"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, JSON, Float
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.base import BaseModel
from app.models.audit_mixin import AuditMixin


class SampleSelectionPhase(BaseModel, AuditMixin):
    """Model for sample selection phase configuration and state"""
    __tablename__ = 'sample_selection_phases'
    
    # Primary key
    phase_id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign keys
    cycle_id = Column(Integer, ForeignKey('test_cycles.cycle_id'), nullable=False)
    report_id = Column(Integer, ForeignKey('reports.id'), nullable=False)
    
    # Phase configuration
    phase_status = Column(String(50), default='Not Started')
    planned_start_date = Column(DateTime)
    planned_end_date = Column(DateTime)
    actual_start_date = Column(DateTime)
    actual_end_date = Column(DateTime)
    
    # Sample selection parameters
    target_sample_size = Column(Integer, default=25)
    sampling_methodology = Column(String(100), default='Risk-based sampling')
    sampling_criteria = Column(JSON)
    
    # LLM configuration
    llm_generation_enabled = Column(Boolean, default=True)
    llm_provider = Column(String(50))
    llm_model = Column(String(100))
    llm_confidence_threshold = Column(Float, default=0.8)
    
    # Manual upload configuration
    manual_upload_enabled = Column(Boolean, default=True)
    upload_template_url = Column(String(500))
    
    # Status tracking
    samples_generated = Column(Integer, default=0)
    samples_validated = Column(Integer, default=0)
    samples_approved = Column(Integer, default=0)
    
    # Additional fields
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.user_id'))
    updated_by = Column(Integer, ForeignKey('users.user_id'))
    
    # Relationships
    cycle = relationship("TestCycle", back_populates="sample_selection_phases")
    report = relationship("Report", back_populates="sample_selection_phases")
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])