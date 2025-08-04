"""
Sample Selection phase models for workflow management - Consolidated Version Management System

This module contains the consolidated sample selection models that implement the versioning framework pattern
used across the application, providing comprehensive sample selection decision management.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, String, Integer, Text, Boolean, ForeignKey, DateTime, Float, DECIMAL
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM as PgEnum 
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
from sqlalchemy.ext.hybrid import hybrid_property
from enum import Enum
import json

from app.models.base import CustomPKModel
from app.models.audit_mixin import AuditMixin


def _serialize_for_jsonb(obj):
    """Convert non-serializable types for JSONB storage"""
    if isinstance(obj, Decimal):
        return str(obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: _serialize_for_jsonb(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_serialize_for_jsonb(item) for item in obj]
    return obj

# Enums for sample selection system
class VersionStatus(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"

class SampleCategory(str, Enum):
    CLEAN = "clean"
    ANOMALY = "anomaly"
    BOUNDARY = "boundary"
    
class SampleDecision(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    PENDING = "pending"
    
class SampleSource(str, Enum):
    TESTER = "tester"
    LLM = "llm"
    MANUAL = "manual"
    CARRIED_FORWARD = "carried_forward"

# Legacy PostgreSQL enum types (for backward compatibility)
sample_generation_method_enum = PgEnum('LLM Generated', 'Manual Upload', 'Hybrid', name='sample_generation_method_enum')
sample_status_enum = PgEnum('Draft', 'Pending Approval', 'Approved', 'Rejected', 'Revision Required', name='sample_status_enum')
sample_validation_status_enum = PgEnum('Valid', 'Invalid', 'Warning', 'Needs Review', name='sample_validation_status_enum')
sample_type_enum = PgEnum('Population Sample', 'Targeted Sample', 'Exception Sample', 'Control Sample', name='sample_type_enum')

# New consolidated enum types
version_status_enum = PgEnum(
    'draft', 'pending_approval', 'approved', 'rejected', 'superseded',
    name='sample_selection_version_status_enum'
)

sample_category_enum = PgEnum(
    'clean', 'anomaly', 'boundary',
    name='sample_category_enum'
)

sample_decision_enum = PgEnum(
    'approved', 'rejected', 'pending',
    name='sample_decision_enum'
)

sample_source_enum = PgEnum(
    'tester', 'llm', 'manual', 'carried_forward',
    name='sample_source_enum'
)


class SampleSelectionVersion(CustomPKModel, AuditMixin):
    """
    Consolidated sample selection version model following the versioning framework pattern.
    
    This model manages sample selection decisions at the version level, providing:
    - Version management with draft → pending → approved/rejected → superseded lifecycle
    - Temporal workflow integration
    - Sample selection criteria and metadata
    - Submission and approval workflow
    """
    
    __tablename__ = "cycle_report_sample_selection_versions"
    
    # Primary key
    version_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Phase context (replaces cycle_id/report_id pattern)
    phase_id = Column(Integer, ForeignKey('workflow_phases.phase_id'), nullable=False)
    workflow_activity_id = Column(Integer, ForeignKey('workflow_activities.activity_id'), nullable=True)
    
    # Version Management
    version_number = Column(Integer, nullable=False)
    version_status = Column(version_status_enum, nullable=False)
    parent_version_id = Column(UUID(as_uuid=True), ForeignKey('cycle_report_sample_selection_versions.version_id'), nullable=True)
    
    # Temporal Workflow Context
    workflow_execution_id = Column(String(255), nullable=False)
    workflow_run_id = Column(String(255), nullable=False)
    activity_name = Column(String(100), nullable=False)
    
    # Sample Selection Metadata
    selection_criteria = Column(JSONB, nullable=False)
    target_sample_size = Column(Integer, nullable=False)
    actual_sample_size = Column(Integer, nullable=False, default=0)
    intelligent_sampling_config = Column(JSONB, nullable=True)
    distribution_metrics = Column(JSONB, nullable=True)
    data_source_config = Column(JSONB, nullable=True)
    version_metadata = Column('metadata', JSONB, nullable=True, default=dict)
    
    # Submission and Approval Workflow
    submission_notes = Column(Text, nullable=True)
    submitted_by_id = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    
    approval_notes = Column(Text, nullable=True)
    approved_by_id = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Report Owner Feedback Fields
    report_owner_decision = Column(String(20), nullable=True)
    report_owner_feedback = Column(Text, nullable=True)
    report_owner_reviewed_at = Column(DateTime(timezone=True), nullable=True)
    report_owner_reviewed_by_id = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    
    # Relationships
    phase = relationship("app.models.workflow.WorkflowPhase", back_populates="sample_selection_versions")
    workflow_activity = relationship("app.models.workflow_activity.WorkflowActivity")
    parent_version = relationship("SampleSelectionVersion", remote_side=[version_id])
    child_versions = relationship("SampleSelectionVersion", back_populates="parent_version")
    
    # Sample records in this version
    samples = relationship("SampleSelectionSample", foreign_keys="SampleSelectionSample.version_id", back_populates="version", cascade="all, delete-orphan")
    
    # User relationships
    submitted_by = relationship("app.models.user.User", foreign_keys=[submitted_by_id])
    approved_by = relationship("app.models.user.User", foreign_keys=[approved_by_id])
    report_owner_reviewed_by = relationship("app.models.user.User", foreign_keys=[report_owner_reviewed_by_id])
    
    # Validation
    @validates('version_number')
    def validate_version_number(self, key, value):
        if value <= 0:
            raise ValueError("Version number must be positive")
        return value
    
    @validates('target_sample_size', 'actual_sample_size')
    def validate_sample_sizes(self, key, value):
        if value < 0:
            raise ValueError(f"{key} cannot be negative")
        return value
    
    @validates('intelligent_sampling_config', 'distribution_metrics', 'selection_criteria', 'data_source_config', 'version_metadata')
    def validate_jsonb_fields(self, key, value):
        """Ensure JSONB fields are serializable"""
        if value is not None:
            return _serialize_for_jsonb(value)
        return value
    
    # Properties for version lifecycle management
    @hybrid_property
    def is_draft(self) -> bool:
        """Check if this version is in draft status"""
        return self.version_status == VersionStatus.DRAFT
    
    @hybrid_property
    def is_pending_approval(self) -> bool:
        """Check if this version is pending approval"""
        return self.version_status == VersionStatus.PENDING_APPROVAL
    
    @hybrid_property
    def is_approved(self) -> bool:
        """Check if this version is approved"""
        return self.version_status == VersionStatus.APPROVED
    
    @hybrid_property
    def can_be_edited(self) -> bool:
        """Check if this version can be edited"""
        return self.version_status in [VersionStatus.DRAFT, VersionStatus.REJECTED]
    
    @hybrid_property
    def can_be_submitted(self) -> bool:
        """Check if this version can be submitted for approval"""
        return self.version_status == VersionStatus.DRAFT and self.actual_sample_size > 0
    
    @hybrid_property
    def is_current(self) -> bool:
        """Check if this is the current active version"""
        return self.version_status == VersionStatus.APPROVED
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get comprehensive summary statistics for this version"""
        return {
            "version_id": str(self.version_id),
            "version_number": self.version_number,
            "status": self.version_status.value,
            "target_sample_size": self.target_sample_size,
            "actual_sample_size": self.actual_sample_size,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "can_be_edited": self.can_be_edited,
            "can_be_submitted": self.can_be_submitted,
            "is_current": self.is_current
        }
    
    def __repr__(self):
        return f"<SampleSelectionVersion(version_id={self.version_id}, phase_id={self.phase_id}, version_number={self.version_number}, status={self.version_status})>"


class SampleSelectionSample(CustomPKModel, AuditMixin):
    """
    Individual sample record model within a sample selection version.
    
    This model stores individual samples with their decision tracking,
    category classification, and metadata.
    """
    
    __tablename__ = "cycle_report_sample_selection_samples"
    
    # Primary key
    sample_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Context
    version_id = Column(UUID(as_uuid=True), ForeignKey('cycle_report_sample_selection_versions.version_id'), nullable=False)
    phase_id = Column(Integer, ForeignKey('workflow_phases.phase_id'), nullable=False)
    lob_id = Column(Integer, ForeignKey('lobs.lob_id'), nullable=True)  # Made nullable - tester assigns LOB
    
    # Sample identification
    sample_identifier = Column(String(255), nullable=False)
    sample_data = Column(JSONB, nullable=False)
    sample_category = Column(sample_category_enum, nullable=False)
    sample_source = Column(sample_source_enum, nullable=False)
    
    # Decision tracking
    tester_decision = Column(sample_decision_enum, nullable=False, default='pending')
    tester_decision_notes = Column(Text, nullable=True)
    tester_decision_at = Column(DateTime(timezone=True), nullable=True)
    tester_decision_by_id = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    
    report_owner_decision = Column(sample_decision_enum, nullable=False, default='pending')
    report_owner_decision_notes = Column(Text, nullable=True)
    report_owner_decision_at = Column(DateTime(timezone=True), nullable=True)
    report_owner_decision_by_id = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    
    # Metadata
    risk_score = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)
    generation_metadata = Column(JSONB, nullable=True)
    validation_results = Column(JSONB, nullable=True)
    
    # Carry-forward tracking
    carried_from_version_id = Column(UUID(as_uuid=True), ForeignKey('cycle_report_sample_selection_versions.version_id'), nullable=True)
    carried_from_sample_id = Column(UUID(as_uuid=True), ForeignKey('cycle_report_sample_selection_samples.sample_id'), nullable=True)
    carry_forward_reason = Column(Text, nullable=True)
    
    # Relationships
    version = relationship("SampleSelectionVersion", foreign_keys=[version_id], back_populates="samples")
    phase = relationship("app.models.workflow.WorkflowPhase")
    lob = relationship("app.models.lob.LOB")
    
    # User relationships
    tester_decided_by = relationship("app.models.user.User", foreign_keys=[tester_decision_by_id])
    report_owner_decided_by = relationship("app.models.user.User", foreign_keys=[report_owner_decision_by_id])
    
    # Carry-forward relationships
    carried_from_version = relationship("SampleSelectionVersion", foreign_keys=[carried_from_version_id])
    carried_from_sample = relationship("SampleSelectionSample", foreign_keys=[carried_from_sample_id])
    
    # Validation
    @validates('risk_score', 'confidence_score')
    def validate_scores(self, key, value):
        if value is not None and (value < 0 or value > 1):
            raise ValueError(f"{key} must be between 0 and 1")
        return value
    
    @validates('sample_data', 'generation_metadata', 'validation_results')
    def validate_jsonb_fields(self, key, value):
        """Ensure JSONB fields are serializable"""
        if value is not None:
            return _serialize_for_jsonb(value)
        return value
    
    # Properties
    @hybrid_property
    def has_tester_decision(self) -> bool:
        """Check if tester has made a decision"""
        return self.tester_decision != SampleDecision.PENDING
    
    @hybrid_property
    def has_report_owner_decision(self) -> bool:
        """Check if report owner has made a decision"""
        return self.report_owner_decision != SampleDecision.PENDING
    
    @hybrid_property
    def is_approved(self) -> bool:
        """Check if this sample is approved in the final selection"""
        return self.tester_decision == SampleDecision.APPROVEDD
    
    @hybrid_property
    def is_rejected(self) -> bool:
        """Check if this sample is rejected from the final selection"""
        return self.tester_decision == SampleDecision.REJECTEDED
    
    @hybrid_property
    def is_carried_forward(self) -> bool:
        """Check if this sample was carried forward from a previous version"""
        return self.sample_source == SampleSource.CARRIED_FORWARD
    
    def get_decision_summary(self) -> Dict[str, Any]:
        """Get a comprehensive summary of all decisions for this sample"""
        return {
            "sample_id": str(self.sample_id),
            "sample_identifier": self.sample_identifier,
            "sample_category": self.sample_category.value,
            "sample_source": self.sample_source.value,
            "tester_decision": {
                "decision": self.tester_decision.value,
                "notes": self.tester_decision_notes,
                "decided_by_id": self.tester_decision_by_id,
                "decided_at": self.tester_decision_at.isoformat() if self.tester_decision_at else None
            },
            "report_owner_decision": {
                "decision": self.report_owner_decision.value,
                "notes": self.report_owner_decision_notes,
                "decided_by_id": self.report_owner_decision_by_id,
                "decided_at": self.report_owner_decision_at.isoformat() if self.report_owner_decision_at else None
            },
            "metadata": {
                "risk_score": self.risk_score,
                "confidence_score": self.confidence_score,
                "generation_metadata": self.generation_metadata,
                "validation_results": self.validation_results
            },
            "carry_forward": {
                "is_carried_forward": self.is_carried_forward,
                "carried_from_version_id": str(self.carried_from_version_id) if self.carried_from_version_id else None,
                "carried_from_sample_id": str(self.carried_from_sample_id) if self.carried_from_sample_id else None,
                "reason": self.carry_forward_reason
            }
        }
    
    def __repr__(self):
        return f"<SampleSelectionSample(sample_id={self.sample_id}, identifier={self.sample_identifier}, tester_decision={self.tester_decision})>"


# Legacy aliases for backward compatibility (tables removed)
# SampleSet and SampleRecord tables were removed - functionality moved to metadata-based approach


# SampleValidationResult table was removed - functionality moved to metadata-based approach
# Validation results are now stored in SampleSelectionVersion.distribution_metrics (JSONB)


# SampleValidationIssue table was removed - functionality moved to metadata-based approach
# Validation issues are now stored in SampleSelectionSample.validation_results (JSONB)


# SampleApprovalHistory table was removed - functionality moved to metadata-based approach
# Approval history is now stored in SampleSelectionVersion.approval_notes and tracked via LLMAuditLog


# LLMSampleGeneration table was removed - functionality moved to metadata-based approach
# LLM generation tracking is now handled through SampleSelectionVersion.generation_metadata


# SampleUploadHistory table was removed - functionality moved to metadata-based approach
# Upload history is now stored in SampleSelectionVersion.generation_metadata (JSONB)


# SampleSelectionAuditLog table was removed - functionality moved to unified LLMAuditLog system
# Audit tracking is now handled through the centralized audit logging system