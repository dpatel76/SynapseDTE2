"""
RFI (Request for Information) Version Models

This module contains the versioned models for the RFI phase, following the same 
versioning pattern as sample selection and scoping phases.

Key Features:
- Version management with draft → pending → approved/rejected → superseded lifecycle
- Dual decision model (tester + report owner)
- Support for both document and data source evidence
- Report owner feedback and resubmission workflow
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy import Column, String, Integer, BigInteger, Text, Boolean, ForeignKey, DateTime, Float, DECIMAL, JSON, CheckConstraint, func
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM as PgEnum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from enum import Enum
import uuid

from app.models.base import CustomPKModel
from app.models.audit_mixin import AuditMixin


# Enums for RFI versioning system
class VersionStatus(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class EvidenceStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUEST_CHANGES = "request_changes"


class EvidenceType(str, Enum):
    DOCUMENT = "document"
    DATA_SOURCE = "data_source"


class Decision(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUEST_CHANGES = "request_changes"


# PostgreSQL enum types
version_status_enum = PgEnum(
    'draft', 'pending_approval', 'approved', 'rejected', 'superseded',
    name='version_status_enum',
    create_type=False  # Already exists from other phases
)

evidence_status_enum = PgEnum(
    'pending', 'approved', 'rejected', 'request_changes',
    name='evidence_status_enum'
)

decision_enum = PgEnum(
    'approved', 'rejected', 'request_changes',
    name='decision_enum',
    create_type=False  # Already exists from other phases
)


class RFIVersion(CustomPKModel, AuditMixin):
    """
    RFI Version model following the same pattern as sample selection/scoping.
    
    This model manages RFI evidence at the version level, providing:
    - Version management with draft → pending → approved/rejected → superseded lifecycle
    - Evidence submission tracking
    - Report owner review workflow
    - Summary statistics and progress tracking
    """
    
    __tablename__ = "cycle_report_request_info_evidence_versions"
    
    # Primary key
    version_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Phase Integration
    phase_id = Column(Integer, ForeignKey('workflow_phases.phase_id'), nullable=False, index=True)
    
    # Version Management
    version_number = Column(Integer, nullable=False)
    version_status = Column(version_status_enum, nullable=False, server_default='draft')
    parent_version_id = Column(UUID(as_uuid=True), ForeignKey('cycle_report_request_info_evidence_versions.version_id'), nullable=True)
    
    # Summary statistics
    total_test_cases = Column(Integer, nullable=False, server_default='0')
    submitted_count = Column(Integer, nullable=False, server_default='0')
    approved_count = Column(Integer, nullable=False, server_default='0')
    rejected_count = Column(Integer, nullable=False, server_default='0')
    pending_count = Column(Integer, nullable=False, server_default='0')
    
    # Evidence type breakdown
    document_evidence_count = Column(Integer, nullable=False, server_default='0')
    data_source_evidence_count = Column(Integer, nullable=False, server_default='0')
    
    # Submission tracking
    submission_deadline = Column(DateTime(timezone=True), nullable=True)
    reminder_schedule = Column(JSONB, nullable=True)
    instructions = Column(Text, nullable=True)
    
    # Approval workflow
    submitted_by_id = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    approved_by_id = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # Report owner review metadata
    report_owner_review_requested_at = Column(DateTime(timezone=True), nullable=True)
    report_owner_review_completed_at = Column(DateTime(timezone=True), nullable=True)
    report_owner_feedback_summary = Column(JSONB, nullable=True)
    
    # Workflow tracking
    workflow_execution_id = Column(String(255), nullable=True)
    workflow_run_id = Column(String(255), nullable=True)
    
    # Relationships
    evidence_items = relationship("RFIEvidence", back_populates="version", cascade="all, delete-orphan")
    phase = relationship("WorkflowPhase", foreign_keys=[phase_id])
    parent_version = relationship("RFIVersion", remote_side=[version_id])
    child_versions = relationship("RFIVersion", back_populates="parent_version")
    
    # User relationships
    submitted_by = relationship("User", foreign_keys=[submitted_by_id])
    approved_by = relationship("User", foreign_keys=[approved_by_id])
    
    @hybrid_property
    def is_latest(self) -> bool:
        """Check if this is the latest version for the phase"""
        return self.version_status in [VersionStatus.APPROVED, VersionStatus.PENDING_APPROVAL]
    
    @hybrid_property
    def completion_percentage(self) -> float:
        """Calculate evidence submission completion percentage"""
        if self.total_test_cases == 0:
            return 0.0
        return (self.submitted_count / self.total_test_cases) * 100
    
    @hybrid_property
    def approval_percentage(self) -> float:
        """Calculate evidence approval percentage"""
        if self.submitted_count == 0:
            return 0.0
        return (self.approved_count / self.submitted_count) * 100
    
    @hybrid_property
    def can_be_edited(self) -> bool:
        """Check if version can be edited (only draft versions are editable)"""
        return self.version_status == VersionStatus.DRAFT or self.version_status == 'draft'
    
    @hybrid_property
    def has_report_owner_feedback(self) -> bool:
        """Check if report owner has provided feedback"""
        return self.report_owner_review_completed_at is not None
    
    def __repr__(self) -> str:
        return f"<RFIVersion(version_id={self.version_id}, phase_id={self.phase_id}, version_number={self.version_number}, status={self.version_status})>"


class RFIEvidence(CustomPKModel, AuditMixin):
    """
    Individual RFI Evidence model (versioned).
    
    This model stores evidence submissions (documents or data sources) with decisions,
    following the dual decision model used in scoping (tester + report owner decisions).
    """
    
    __tablename__ = "cycle_report_request_info_evidence"
    
    # Primary key
    evidence_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Version Reference
    version_id = Column(UUID(as_uuid=True), ForeignKey('cycle_report_request_info_evidence_versions.version_id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Phase Integration
    phase_id = Column(Integer, ForeignKey('workflow_phases.phase_id'), nullable=False)
    
    # Test case reference
    test_case_id = Column(Integer, ForeignKey('cycle_report_test_cases.id'), nullable=False, index=True)
    sample_id = Column(String(255), nullable=False, index=True)
    attribute_id = Column(Integer, ForeignKey('cycle_report_planning_attributes.id'), nullable=False)
    attribute_name = Column(String(255), nullable=False)
    
    # Evidence type and details
    evidence_type = Column(String(20), nullable=False)  # 'document' or 'data_source'
    evidence_status = Column(evidence_status_enum, nullable=False, server_default='pending')
    
    # Common submission fields
    data_owner_id = Column(Integer, ForeignKey('users.user_id'), nullable=False, index=True)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    submission_notes = Column(Text, nullable=True)
    
    # Document specific fields
    original_filename = Column(String(255), nullable=True)
    stored_filename = Column(String(255), nullable=True)
    file_path = Column(String(500), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    file_hash = Column(String(64), nullable=True)
    mime_type = Column(String(100), nullable=True)
    
    # Data source specific fields
    data_source_id = Column(Integer, ForeignKey('cycle_report_planning_data_sources.id'), nullable=True)
    query_text = Column(Text, nullable=True)
    query_parameters = Column(JSONB, nullable=True)
    query_result_sample = Column(JSONB, nullable=True)
    row_count = Column(Integer, nullable=True)
    
    # Dual Decision Model (same as scoping)
    tester_decision = Column(decision_enum, nullable=True)
    tester_notes = Column(Text, nullable=True)
    tester_decided_by = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    tester_decided_at = Column(DateTime(timezone=True), nullable=True)
    
    report_owner_decision = Column(decision_enum, nullable=True)
    report_owner_notes = Column(Text, nullable=True)
    report_owner_decided_by = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    report_owner_decided_at = Column(DateTime(timezone=True), nullable=True)
    
    # Resubmission tracking
    requires_resubmission = Column(Boolean, nullable=False, server_default='false')
    resubmission_deadline = Column(DateTime(timezone=True), nullable=True)
    resubmission_count = Column(Integer, nullable=False, server_default='0')
    parent_evidence_id = Column(UUID(as_uuid=True), ForeignKey('cycle_report_request_info_evidence.evidence_id'), nullable=True)
    
    # Validation tracking
    validation_status = Column(String(50), nullable=True, server_default='pending')
    validation_notes = Column(Text, nullable=True)
    validated_by = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    validated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    version = relationship("RFIVersion", back_populates="evidence_items")
    phase = relationship("WorkflowPhase", foreign_keys=[phase_id])
    test_case = relationship("CycleReportTestCase", foreign_keys=[test_case_id])
    attribute = relationship("ReportAttribute", foreign_keys=[attribute_id])
    data_source = relationship("CycleReportDataSource", foreign_keys=[data_source_id])
    data_owner = relationship("User", foreign_keys=[data_owner_id])
    
    # User relationships
    tester_decided_by_user = relationship("User", foreign_keys=[tester_decided_by])
    report_owner_decided_by_user = relationship("User", foreign_keys=[report_owner_decided_by])
    validated_by_user = relationship("User", foreign_keys=[validated_by])
    
    # Self-referential relationship for resubmissions
    parent_evidence = relationship("RFIEvidence", remote_side=[evidence_id], foreign_keys=[parent_evidence_id])
    child_evidence = relationship("RFIEvidence", back_populates="parent_evidence", foreign_keys=[parent_evidence_id])
    
    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "(evidence_type = 'document' AND original_filename IS NOT NULL AND file_path IS NOT NULL) OR "
            "(evidence_type = 'data_source' AND query_text IS NOT NULL)",
            name='check_evidence_type_fields_versioned'
        ),
    )
    
    @hybrid_property
    def is_approved(self) -> bool:
        """Check if evidence is approved by both tester and report owner"""
        return (self.tester_decision == Decision.APPROVED and 
                self.report_owner_decision == Decision.APPROVED)
    
    @hybrid_property
    def is_rejected(self) -> bool:
        """Check if evidence is rejected by either tester or report owner"""
        return (self.tester_decision == Decision.REJECTED or 
                self.report_owner_decision == Decision.REJECTED)
    
    @hybrid_property
    def needs_resubmission(self) -> bool:
        """Check if evidence needs resubmission"""
        return (self.requires_resubmission or 
                self.tester_decision == Decision.REQUEST_CHANGES or
                self.report_owner_decision == Decision.REQUEST_CHANGES)
    
    @hybrid_property
    def final_status(self) -> Optional[str]:
        """Get the final status based on both tester and report owner decisions"""
        if self.is_approved:
            return "approved"
        elif self.is_rejected:
            return "rejected"
        elif self.needs_resubmission:
            return "request_changes"
        elif self.tester_decision or self.report_owner_decision:
            return "partial_review"
        else:
            return "pending"
    
    def __repr__(self) -> str:
        return f"<RFIEvidence(evidence_id={self.evidence_id}, test_case_id={self.test_case_id}, evidence_type={self.evidence_type}, status={self.evidence_status})>"