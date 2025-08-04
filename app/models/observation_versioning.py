"""
Observation Versioning Models

This module implements versioning for the observation management phase,
following the same pattern as scoping versioning.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, Boolean, ForeignKey, DateTime, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM as PgEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum

from app.models.base import CustomPKModel
from app.models.audit_mixin import AuditMixin


# Enums for observation versioning
class ObservationVersionStatus(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class ObservationApprovalStatus(str, Enum):
    PENDING = "pending"
    TESTER_APPROVED = "tester_approved"
    REPORT_OWNER_APPROVED = "report_owner_approved"
    FULLY_APPROVED = "fully_approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"


# PostgreSQL enum types
observation_version_status_enum = PgEnum(
    'draft', 'pending_approval', 'approved', 'rejected', 'superseded',
    name='observation_version_status_enum'
)

observation_approval_status_enum = PgEnum(
    'pending', 'tester_approved', 'report_owner_approved', 
    'fully_approved', 'rejected', 'needs_revision',
    name='observation_approval_status_enum'
)


class ObservationVersion(CustomPKModel, AuditMixin):
    """
    Observation version model for tracking versions of observation submissions.
    
    Provides:
    - Version management with lifecycle tracking
    - Approval workflow with multiple approval levels
    - Summary statistics of observations
    - Integration with workflow phases
    """
    
    __tablename__ = "cycle_report_observation_versions"
    
    # Primary key
    version_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Phase context
    phase_id = Column(Integer, ForeignKey('workflow_phases.phase_id'), nullable=False)
    
    # Version Management
    version_number = Column(Integer, nullable=False)
    version_status = Column(observation_version_status_enum, nullable=False, default='draft')
    parent_version_id = Column(UUID(as_uuid=True), ForeignKey('cycle_report_observation_versions.version_id'), nullable=True)
    
    # Submission Information
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    submitted_by = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    submission_notes = Column(Text, nullable=True)
    
    # Approval Workflow
    approval_status = Column(observation_approval_status_enum, nullable=False, default='pending')
    tester_approval_at = Column(DateTime(timezone=True), nullable=True)
    tester_approval_by = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    tester_approval_comments = Column(Text, nullable=True)
    
    report_owner_approval_at = Column(DateTime(timezone=True), nullable=True)
    report_owner_approval_by = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    report_owner_approval_comments = Column(Text, nullable=True)
    
    # Summary Statistics
    total_observations = Column(Integer, nullable=False, default=0)
    high_priority_observations = Column(Integer, nullable=False, default=0)
    medium_priority_observations = Column(Integer, nullable=False, default=0)
    low_priority_observations = Column(Integer, nullable=False, default=0)
    
    total_samples_impacted = Column(Integer, nullable=False, default=0)
    total_attributes_impacted = Column(Integer, nullable=False, default=0)
    
    # Risk Assessment
    overall_risk_rating = Column(String(20), nullable=True)  # 'high', 'medium', 'low'
    risk_assessment_notes = Column(Text, nullable=True)
    
    # Metadata
    observation_summary = Column(JSONB, nullable=True)  # Summary of observations by type/category
    version_metadata = Column(JSONB, nullable=True)  # Additional version metadata
    
    # Relationships
    phase = relationship("WorkflowPhase", foreign_keys=[phase_id])
    parent_version = relationship("ObservationVersion", remote_side=[version_id], foreign_keys=[parent_version_id])
    submitter = relationship("User", foreign_keys=[submitted_by])
    tester_approver = relationship("User", foreign_keys=[tester_approval_by])
    report_owner_approver = relationship("User", foreign_keys=[report_owner_approval_by])
    
    # Child relationships
    observation_items = relationship("ObservationVersionItem", back_populates="version", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ObservationVersion(version_id={self.version_id}, version_number={self.version_number}, status={self.version_status})>"


class ObservationVersionItem(CustomPKModel, AuditMixin):
    """
    Individual observation items within a version.
    
    Links observations to specific versions for tracking changes
    and approval status at the observation level.
    """
    
    __tablename__ = "cycle_report_observation_version_items"
    
    # Primary key
    item_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Version reference
    version_id = Column(UUID(as_uuid=True), ForeignKey('cycle_report_observation_versions.version_id'), nullable=False)
    
    # Observation reference
    observation_id = Column(Integer, ForeignKey('cycle_report_observation_mgmt_observation_records.observation_id'), nullable=False)
    
    # Item-level approval tracking
    item_status = Column(String(50), nullable=False, default='pending')  # 'pending', 'approved', 'rejected'
    approval_notes = Column(Text, nullable=True)
    
    # Priority and risk
    priority = Column(String(20), nullable=False, default='medium')  # 'high', 'medium', 'low'
    risk_rating = Column(String(20), nullable=True)
    
    # Grouping information
    group_id = Column(Integer, nullable=True)  # For grouping related observations
    group_name = Column(String(255), nullable=True)
    
    # Metadata
    item_metadata = Column(JSONB, nullable=True)
    
    # Relationships
    version = relationship("ObservationVersion", back_populates="observation_items")
    observation = relationship("ObservationRecord", foreign_keys=[observation_id])
    
    def __repr__(self):
        return f"<ObservationVersionItem(item_id={self.item_id}, observation_id={self.observation_id}, status={self.item_status})>"


class ObservationVersionChangeLog(CustomPKModel, AuditMixin):
    """
    Tracks changes between observation versions.
    
    Records what changed between versions for audit trail
    and change management.
    """
    
    __tablename__ = "cycle_report_observation_version_changelog"
    
    # Primary key
    change_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Version references
    from_version_id = Column(UUID(as_uuid=True), ForeignKey('cycle_report_observation_versions.version_id'), nullable=True)
    to_version_id = Column(UUID(as_uuid=True), ForeignKey('cycle_report_observation_versions.version_id'), nullable=False)
    
    # Change details
    change_type = Column(String(50), nullable=False)  # 'created', 'updated', 'approved', 'rejected', 'revision'
    change_summary = Column(Text, nullable=False)
    change_details = Column(JSONB, nullable=True)
    
    # Change metadata
    changed_by = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    changed_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    change_reason = Column(Text, nullable=True)
    
    # Relationships
    from_version = relationship("ObservationVersion", foreign_keys=[from_version_id])
    to_version = relationship("ObservationVersion", foreign_keys=[to_version_id])
    changer = relationship("User", foreign_keys=[changed_by])
    
    def __repr__(self):
        return f"<ObservationVersionChangeLog(change_id={self.change_id}, type={self.change_type})>"