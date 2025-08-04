"""Metrics tracking models for SynapseDTE."""
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.models.base import CustomPKModel
from app.models.audit_mixin import AuditMixin


class PhaseMetrics(CustomPKModel, AuditMixin):
    """Stores aggregated metrics for each phase of the testing workflow."""
    
    __tablename__ = "metrics_phases"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    cycle_id = Column(Integer, ForeignKey("test_cycles.cycle_id"), nullable=False)
    report_id = Column(Integer, ForeignKey("reports.id"), nullable=False)
    phase_name = Column(String(50), nullable=False)
    lob_name = Column(String(100), nullable=True)
    
    # Attribute metrics
    total_attributes = Column(Integer, default=0)
    approved_attributes = Column(Integer, default=0)
    attributes_with_issues = Column(Integer, default=0)
    primary_keys = Column(Integer, default=0)
    non_pk_attributes = Column(Integer, default=0)
    
    # Sample metrics
    total_samples = Column(Integer, default=0)
    approved_samples = Column(Integer, default=0)
    failed_samples = Column(Integer, default=0)
    
    # Test case metrics
    total_test_cases = Column(Integer, default=0)
    completed_test_cases = Column(Integer, default=0)
    passed_test_cases = Column(Integer, default=0)
    failed_test_cases = Column(Integer, default=0)
    
    # Observation metrics
    total_observations = Column(Integer, default=0)
    approved_observations = Column(Integer, default=0)
    
    # Time and efficiency metrics
    completion_time_minutes = Column(Float, nullable=True)
    on_time_completion = Column(Boolean, nullable=True)
    submissions_for_approval = Column(Integer, default=0)
    
    # Data provider metrics
    data_providers_assigned = Column(Integer, default=0)
    changes_to_data_providers = Column(Integer, default=0)
    
    # RFI metrics
    rfi_sent = Column(Integer, default=0)
    rfi_completed = Column(Integer, default=0)
    rfi_pending = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    cycle = relationship("TestCycle", back_populates="phase_metrics")
    report = relationship("Report", back_populates="phase_metrics")


class ExecutionMetrics(CustomPKModel, AuditMixin):
    """Tracks execution time for individual activities within phases."""
    
    __tablename__ = "metrics_execution"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    cycle_id = Column(Integer, ForeignKey("test_cycles.cycle_id"), nullable=False)
    report_id = Column(Integer, ForeignKey("reports.id"), nullable=False)
    phase_name = Column(String(50), nullable=False)
    activity_name = Column(String(100), nullable=False)
    user_id = Column(String(255), nullable=True)
    
    # Timing information
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    duration_minutes = Column(Float, nullable=True)
    status = Column(String(50), nullable=False)  # started, completed, failed
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    cycle = relationship("TestCycle", back_populates="execution_metrics")
    report = relationship("Report", back_populates="execution_metrics")