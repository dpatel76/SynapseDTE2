"""
New simplified sample selection models following the versioning framework
"""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, Float, ForeignKey, Enum, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid
import enum

from app.models.base import CustomPKModel


# Enums
class VersionStatus(str, enum.Enum):
    """Version status enumeration"""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class SampleCategory(str, enum.Enum):
    """Sample category enumeration for intelligent sampling"""
    CLEAN = "clean"
    ANOMALY = "anomaly"
    BOUNDARY = "boundary"


class SampleDecision(str, enum.Enum):
    """Sample decision enumeration"""
    INCLUDE = "include"
    EXCLUDE = "exclude"
    PENDING = "pending"


class SampleSource(str, enum.Enum):
    """Sample source enumeration"""
    TESTER = "tester"
    LLM = "llm"
    MANUAL = "manual"
    CARRIED_FORWARD = "carried_forward"


class SampleSelectionVersion(CustomPKModel):
    """Sample selection version model following the versioning framework"""
    
    __tablename__ = 'cycle_report_sample_selection_versions'
    
    # Primary key
    version_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    
    # Phase-based architecture (replaces cycle_id/report_id)
    phase_id = Column(Integer, ForeignKey('workflow_phases.phase_id'), nullable=False, index=True)
    
    # Version management
    version_number = Column(Integer, nullable=False)
    version_status = Column(Enum(VersionStatus), nullable=False, default=VersionStatus.DRAFT)
    parent_version_id = Column(UUID, ForeignKey('cycle_report_sample_selection_versions.version_id'), nullable=True)
    
    # Temporal workflow context (required for all versioned entities)
    workflow_execution_id = Column(String(255), nullable=False, index=True)
    workflow_run_id = Column(String(255), nullable=False)
    activity_name = Column(String(100), nullable=False)
    
    # Sample selection specific metadata
    selection_criteria = Column(JSONB, nullable=False)
    target_sample_size = Column(Integer, nullable=False)
    actual_sample_size = Column(Integer, nullable=False, default=0)
    
    # Intelligent sampling configuration
    intelligent_sampling_config = Column(JSONB, nullable=True)  # 30/50/20 distribution config
    distribution_metrics = Column(JSONB, nullable=True)  # Actual distribution achieved
    data_source_config = Column(JSONB, nullable=True)  # Data source configuration
    
    # Submission and approval
    submission_notes = Column(Text, nullable=True)
    approval_notes = Column(Text, nullable=True)
    
    # Timestamps and user tracking
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    submitted_by_id = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approved_by_id = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Relationships
    phase = relationship("WorkflowPhase", back_populates="sample_selection_versions")
    parent_version = relationship("SampleSelectionVersion", remote_side=[version_id], back_populates="child_versions")
    child_versions = relationship("SampleSelectionVersion", back_populates="parent_version")
    
    samples = relationship("SampleSelectionSample", back_populates="version", cascade="all, delete-orphan", foreign_keys="SampleSelectionSample.version_id")
    
    # User relationships
    created_by = relationship("User", foreign_keys=[created_by_id])
    submitted_by = relationship("User", foreign_keys=[submitted_by_id])
    approved_by = relationship("User", foreign_keys=[approved_by_id])
    
    # Indexes and constraints
    __table_args__ = (
        UniqueConstraint('phase_id', 'version_number', name='uq_sample_selection_version'),
        Index('idx_sample_selection_versions_phase', 'phase_id'),
        Index('idx_sample_selection_versions_status', 'version_status'),
        Index('idx_sample_selection_versions_workflow', 'workflow_execution_id'),
        Index('idx_sample_selection_versions_created_at', 'created_at'),
        Index('idx_sample_selection_versions_current', 'phase_id', 'version_status'),
    )
    
    def __repr__(self):
        return f"<SampleSelectionVersion(version_id={self.version_id}, version_number={self.version_number}, status={self.version_status})>"
    
    @property
    def is_current_version(self) -> bool:
        """Check if this is the current version"""
        return self.version_status in [VersionStatus.APPROVED, VersionStatus.PENDING_APPROVAL]
    
    @property
    def can_be_edited(self) -> bool:
        """Check if this version can be edited"""
        return self.version_status == VersionStatus.DRAFT
    
    @property
    def sample_distribution(self) -> Optional[Dict[str, int]]:
        """Get sample distribution by category"""
        if not self.distribution_metrics:
            return None
        return self.distribution_metrics.get('category_distribution', {})
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get version metadata"""
        return {
            'version_id': str(self.version_id),
            'version_number': self.version_number,
            'version_status': self.version_status.value,
            'target_sample_size': self.target_sample_size,
            'actual_sample_size': self.actual_sample_size,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'distribution_metrics': self.distribution_metrics,
            'intelligent_sampling_config': self.intelligent_sampling_config,
        }


class SampleSelectionSample(CustomPKModel):
    """Individual sample within a version"""
    
    __tablename__ = 'cycle_report_sample_selection_samples'
    
    # Primary key
    sample_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    
    # Version and phase relationship
    version_id = Column(UUID, ForeignKey('cycle_report_sample_selection_versions.version_id'), nullable=False, index=True)
    phase_id = Column(Integer, ForeignKey('workflow_phases.phase_id'), nullable=False, index=True)
    
    # Sample-specific LOB (allows different LOB per sample)
    lob_id = Column(Integer, ForeignKey('lobs.lob_id'), nullable=False, index=True)
    
    # Sample identification and data
    sample_identifier = Column(String(255), nullable=False, index=True)
    sample_data = Column(JSONB, nullable=False)
    
    # Intelligent sampling categorization
    sample_category = Column(Enum(SampleCategory), nullable=False, index=True)
    sample_source = Column(Enum(SampleSource), nullable=False, index=True)
    
    # Dual decision model (tester + report owner)
    tester_decision = Column(Enum(SampleDecision), nullable=False, default=SampleDecision.PENDING, index=True)
    tester_decision_notes = Column(Text, nullable=True)
    tester_decision_at = Column(DateTime(timezone=True), nullable=True)
    tester_decision_by_id = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    
    report_owner_decision = Column(Enum(SampleDecision), nullable=False, default=SampleDecision.PENDING, index=True)
    report_owner_decision_notes = Column(Text, nullable=True)
    report_owner_decision_at = Column(DateTime(timezone=True), nullable=True)
    report_owner_decision_by_id = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    
    # Sample metadata
    risk_score = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)
    generation_metadata = Column(JSONB, nullable=True)  # LLM params, generation context
    validation_results = Column(JSONB, nullable=True)  # Validation results
    
    # Carry-forward support
    carried_from_version_id = Column(UUID, ForeignKey('cycle_report_sample_selection_versions.version_id'), nullable=True)
    carried_from_sample_id = Column(UUID, ForeignKey('cycle_report_sample_selection_samples.sample_id'), nullable=True)
    carry_forward_reason = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Relationships
    version = relationship("SampleSelectionVersion", back_populates="samples", foreign_keys=[version_id])
    phase = relationship("WorkflowPhase")
    lob = relationship("LOB")
    
    # Carry-forward relationships
    carried_from_version = relationship("SampleSelectionVersion", foreign_keys=[carried_from_version_id])
    carried_from_sample = relationship("SampleSelectionSample", remote_side=[sample_id], foreign_keys=[carried_from_sample_id])
    
    # User relationships
    tester_decision_by = relationship("User", foreign_keys=[tester_decision_by_id])
    report_owner_decision_by = relationship("User", foreign_keys=[report_owner_decision_by_id])
    
    # Indexes
    __table_args__ = (
        Index('idx_sample_selection_samples_version', 'version_id'),
        Index('idx_sample_selection_samples_phase', 'phase_id'),
        Index('idx_sample_selection_samples_lob', 'lob_id'),
        Index('idx_sample_selection_samples_category', 'sample_category'),
        Index('idx_sample_selection_samples_source', 'sample_source'),
        Index('idx_sample_selection_samples_tester_decision', 'tester_decision'),
        Index('idx_sample_selection_samples_owner_decision', 'report_owner_decision'),
        Index('idx_sample_selection_samples_identifier', 'sample_identifier'),
        Index('idx_sample_selection_samples_created_at', 'created_at'),
        # Composite indexes for common queries
        Index('idx_sample_selection_samples_version_category', 'version_id', 'sample_category'),
        Index('idx_sample_selection_samples_version_decisions', 'version_id', 'tester_decision', 'report_owner_decision'),
        Index('idx_sample_selection_samples_phase_lob', 'phase_id', 'lob_id'),
    )
    
    def __repr__(self):
        return f"<SampleSelectionSample(sample_id={self.sample_id}, identifier={self.sample_identifier}, category={self.sample_category})>"
    
    @property
    def is_approved(self) -> bool:
        """Check if sample is approved by both tester and report owner"""
        return (self.tester_decision == SampleDecision.INCLUDE and 
                self.report_owner_decision == SampleDecision.INCLUDE)
    
    @property
    def is_rejected(self) -> bool:
        """Check if sample is rejected by either tester or report owner"""
        return (self.tester_decision == SampleDecision.EXCLUDE or 
                self.report_owner_decision == SampleDecision.EXCLUDE)
    
    @property
    def needs_review(self) -> bool:
        """Check if sample needs review"""
        return (self.tester_decision == SampleDecision.PENDING or 
                self.report_owner_decision == SampleDecision.PENDING)
    
    @property
    def is_carried_forward(self) -> bool:
        """Check if sample was carried forward from a previous version"""
        return self.sample_source == SampleSource.CARRIED_FORWARD
    
    def get_decision_summary(self) -> Dict[str, Any]:
        """Get summary of decisions"""
        return {
            'tester_decision': self.tester_decision.value,
            'tester_decision_at': self.tester_decision_at.isoformat() if self.tester_decision_at else None,
            'report_owner_decision': self.report_owner_decision.value,
            'report_owner_decision_at': self.report_owner_decision_at.isoformat() if self.report_owner_decision_at else None,
            'final_status': 'approved' if self.is_approved else 'rejected' if self.is_rejected else 'pending',
            'needs_review': self.needs_review,
        }
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get sample metadata"""
        return {
            'sample_id': str(self.sample_id),
            'sample_identifier': self.sample_identifier,
            'sample_category': self.sample_category.value,
            'sample_source': self.sample_source.value,
            'risk_score': self.risk_score,
            'confidence_score': self.confidence_score,
            'is_carried_forward': self.is_carried_forward,
            'carry_forward_reason': self.carry_forward_reason,
            'decision_summary': self.get_decision_summary(),
            'generation_metadata': self.generation_metadata,
            'validation_results': self.validation_results,
        }