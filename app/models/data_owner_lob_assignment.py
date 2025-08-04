"""
Data Owner LOB Assignment Models

This module implements the unified data owner LOB assignment system with 2-table architecture:
1. DataOwnerLOBAttributeVersion - Version management for data owner assignments
2. DataOwnerLOBAttributeAssignment - Individual data owner assignments to LOB-Attribute combinations

Business Logic: Data Executives assign Data Owners to LOB-Attribute combinations
"""

import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import CustomPKModel
from app.models.audit import AuditMixin


class DataOwnerLOBAttributeVersion(CustomPKModel, AuditMixin):
    """
    Version management for data owner LOB attribute assignments
    Tracks assignment batches by Data Executives with version control
    """
    __tablename__ = 'cycle_report_data_owner_lob_mapping_versions'
    
    # Primary Key
    version_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    
    # Phase Integration (only phase_id needed)
    phase_id = Column(Integer, ForeignKey('workflow_phases.phase_id'), nullable=False)
    workflow_activity_id = Column(Integer, ForeignKey('workflow_activities.activity_id'), nullable=True)
    
    # Version Management
    version_number = Column(Integer, nullable=False)
    version_status = Column(String(50), nullable=False, default='draft', server_default='draft')
    parent_version_id = Column(UUID(as_uuid=True), ForeignKey('cycle_report_data_owner_lob_mapping_versions.version_id'), nullable=True)
    
    # Temporal Workflow Context
    workflow_execution_id = Column(String(255), nullable=True)
    workflow_run_id = Column(String(255), nullable=True)
    
    # Assignment Summary
    total_lob_attributes = Column(Integer, nullable=False, default=0, server_default='0')
    assigned_lob_attributes = Column(Integer, nullable=False, default=0, server_default='0')
    unassigned_lob_attributes = Column(Integer, nullable=False, default=0, server_default='0')
    
    # Data Executive Information
    data_executive_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    assignment_batch_date = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, server_default=func.current_timestamp())
    assignment_notes = Column(Text, nullable=True)
    
    # Relationships
    assignments = relationship("DataOwnerLOBAttributeMapping", back_populates="version", cascade="all, delete-orphan")
    phase = relationship("WorkflowPhase", foreign_keys=[phase_id])
    workflow_activity = relationship("WorkflowActivity", foreign_keys=[workflow_activity_id])
    data_executive = relationship("User", foreign_keys=[data_executive_id])
    parent_version = relationship(
        "DataOwnerLOBAttributeVersion", 
        remote_side=[version_id],
        primaryjoin="DataOwnerLOBAttributeVersion.parent_version_id==DataOwnerLOBAttributeVersion.version_id"
    )
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('phase_id', 'version_number', name='uq_data_owner_version_phase_number'),
        CheckConstraint("version_status IN ('draft', 'active', 'superseded')", name='ck_data_owner_version_status'),
    )
    
    def __repr__(self):
        return f"<DataOwnerLOBAttributeVersion(version_id={self.version_id}, phase_id={self.phase_id}, version_number={self.version_number}, status={self.version_status})>"


class DataOwnerLOBAttributeMapping(CustomPKModel, AuditMixin):
    """
    Individual data owner mappings to LOB-Attribute combinations
    Represents the core business logic: Data Executive assigns Data Owner to LOB-Attribute
    This is a mapping table, not an assignment in the universal assignments sense.
    """
    __tablename__ = 'cycle_report_data_owner_lob_mapping'
    
    # Primary Key
    mapping_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    
    # Version Reference (optional in database)
    version_id = Column(UUID(as_uuid=True), ForeignKey('cycle_report_data_owner_lob_mapping_versions.version_id', ondelete='CASCADE'), nullable=True)
    
    # Core Business Keys
    phase_id = Column(Integer, ForeignKey('workflow_phases.phase_id'), nullable=False)
    sample_id = Column(Integer, ForeignKey('cycle_report_sample_selection_samples.sample_id'), nullable=True)
    attribute_id = Column(Integer, ForeignKey("cycle_report_planning_attributes.id"), nullable=False)
    lob_id = Column(Integer, ForeignKey('lobs.lob_id'), nullable=False)
    
    # Data Owner Assignment
    data_owner_id = Column(Integer, ForeignKey('users.user_id'), nullable=True)  # Can be NULL if unassigned
    
    # Data Executive Assignment Information
    data_executive_id = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    assigned_by_data_executive_at = Column(DateTime(timezone=True), nullable=True)
    assignment_rationale = Column(Text, nullable=True)
    
    # Change Tracking
    previous_data_owner_id = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    change_reason = Column(Text, nullable=True)
    
    # Status
    assignment_status = Column(String(50), nullable=False, default='unassigned', server_default='unassigned')
    
    # Data Owner Response (if applicable)
    data_owner_acknowledged = Column(Boolean, nullable=False, default=False, server_default='false')
    data_owner_acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    data_owner_response_notes = Column(Text, nullable=True)
    
    # Relationships
    version = relationship("DataOwnerLOBAttributeVersion", back_populates="assignments")
    phase = relationship("WorkflowPhase", foreign_keys=[phase_id])
    sample = relationship("SampleSelectionSample", foreign_keys=[sample_id])
    attribute = relationship("ReportAttribute", foreign_keys=[attribute_id])
    lob = relationship("LOB", foreign_keys=[lob_id])
    data_owner = relationship("User", foreign_keys=[data_owner_id])
    previous_data_owner = relationship("User", foreign_keys=[previous_data_owner_id])
    data_executive = relationship("User", foreign_keys=[data_executive_id])
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('version_id', 'phase_id', 'sample_id', 'attribute_id', 'lob_id', 
                        name='uq_data_owner_assignment_version_phase_sample_attr_lob'),
        CheckConstraint("assignment_status IN ('assigned', 'unassigned', 'changed', 'confirmed')", 
                       name='ck_data_owner_assignment_status'),
    )
    
    def __repr__(self):
        return f"<DataOwnerLOBAttributeMapping(mapping_id={self.mapping_id}, phase_id={self.phase_id}, lob_id={self.lob_id}, attribute_id={self.attribute_id}, data_owner_id={self.data_owner_id})>"
    
    @property
    def is_assigned(self) -> bool:
        """Check if this assignment has a data owner assigned"""
        return self.data_owner_id is not None
    
    @property
    def has_changed(self) -> bool:
        """Check if this assignment has been changed from a previous data owner"""
        return self.previous_data_owner_id is not None and self.previous_data_owner_id != self.data_owner_id
    
    @property
    def is_acknowledged(self) -> bool:
        """Check if the data owner has acknowledged this assignment"""
        return self.data_owner_acknowledged and self.data_owner_acknowledged_at is not None


# Enums for better type safety (if needed for API/validation)
class VersionStatus:
    DRAFT = 'draft'
    ACTIVE = 'active'
    SUPERSEDED = 'superseded'


class AssignmentStatus:
    ASSIGNED = 'assigned'
    UNASSIGNED = 'unassigned'
    CHANGED = 'changed'
    CONFIRMED = 'confirmed'