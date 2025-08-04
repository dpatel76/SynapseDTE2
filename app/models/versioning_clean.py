"""
Clean versioning models without backward compatibility
All versioning is handled through Temporal workflows
"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, Date, Float, ForeignKey, Enum, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, JSONBUUID
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional
import uuid
import enum

from app.models.base import CustomPKModel


# Enums
class VersionStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"


class SampleSource(str, enum.Enum):
    TESTER = "tester"
    LLM = "llm"
    MANUAL = "manual"
    CARRIED_FORWARD = "carried_forward"


# Base class for all versioned entities
class VersionedEntity(CustomPKModel):
    """Base class for all versioned entities in the system"""
    __abstract__ = True
    
    # Core versioning
    version_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    version_number = Column(Integer, nullable=False)
    version_status = Column(Enum(VersionStatus), nullable=False, default=VersionStatus.DRAFT)
    parent_version_id = Column(UUID)
    
    # Temporal workflow context (required)
    workflow_execution_id = Column(String(255), nullable=False, index=True)
    workflow_run_id = Column(String(255), nullable=False)
    activity_name = Column(String(100), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    approved_at = Column(DateTime)
    approved_by_id = Column(Integer, ForeignKey('users.user_id'))
    
    # Common fields
    cycle_id = Column(Integer, ForeignKey('test_cycles.cycle_id'), nullable=False, index=True)
    report_id = Column(Integer, ForeignKey('reports.id'), nullable=False, index=True)
    phase_name = Column(String(50), nullable=False)


# 1. Planning Phase
class PlanningVersion(VersionedEntity):
    """Planning phase versions"""
    __tablename__ = 'planning_versions'
    
    # Planning specific
    total_attributes = Column(Integer, nullable=False, default=0)
    included_attributes = Column(Integer, nullable=False, default=0)
    
    # Relationships
    attribute_decisions = relationship("AttributeDecision", back_populates="version", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint('cycle_id', 'report_id', 'version_number', name='uq_planning_version'),
        Index('idx_planning_current', 'cycle_id', 'report_id', 'version_status'),
    )


class AttributeDecision(CustomPKModel):
    """Attribute decisions within planning version"""
    __tablename__ = 'attribute_decisions'
    
    decision_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    version_id = Column(UUID, ForeignKey('planning_versions.version_id'), nullable=False)
    
    # Attribute data
    attribute_id = Column(UUID(as_uuid=True), ForeignKey("cycle_report_planning_attributes.id"), nullable=False)
    attribute_name = Column(String(255), nullable=False)
    include_in_testing = Column(Boolean, nullable=False, default=True)
    
    # Decision metadata
    decision_reason = Column(Text)
    risk_rating = Column(String(20))  # high, medium, low
    
    # Relationships
    version = relationship("PlanningVersion", back_populates="attribute_decisions")
    
    __table_args__ = (
        Index('idx_attr_decision_version', 'version_id'),
    )


# 2. Data Profiling Phase
class DataProfilingVersion(VersionedEntity):
    """Data profiling versions"""
    __tablename__ = 'data_profiling_versions'
    
    # Profiling specific
    source_files = Column(JSONB, nullable=False)  # List of uploaded files
    total_rules = Column(Integer, nullable=False, default=0)
    approved_rules = Column(Integer, nullable=False, default=0)
    
    # Relationships
    profiling_rules = relationship("ProfilingRule", back_populates="version", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint('cycle_id', 'report_id', 'version_number', name='uq_profiling_version'),
    )


class VersionedProfilingRule(CustomPKModel):
    """Profiling rules within version"""
    __tablename__ = 'versioned_profiling_rules_v2'
    
    rule_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    version_id = Column(UUID, ForeignKey('data_profiling_versions.version_id'), nullable=False)
    
    # Rule definition
    rule_name = Column(String(255), nullable=False)
    rule_type = Column(String(50), nullable=False)  # validation, transformation, quality
    rule_definition = Column(JSONB, nullable=False)
    
    # Approval
    approval_status = Column(Enum(ApprovalStatus), nullable=False, default=ApprovalStatus.PENDING)
    approval_notes = Column(Text)
    
    # Relationships
    version = relationship("DataProfilingVersion", back_populates="cycle_report_data_profiling_rules")


# 3. Scoping Phase
class ScopingVersion(VersionedEntity):
    """Scoping versions"""
    __tablename__ = 'scoping_versions'
    
    # Scoping specific
    total_attributes = Column(Integer, nullable=False, default=0)
    in_scope_count = Column(Integer, nullable=False, default=0)
    
    # Relationships
    scoping_decisions = relationship("ScopingDecision", back_populates="version", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint('cycle_id', 'report_id', 'version_number', name='uq_scoping_version'),
    )


class ScopingDecision(CustomPKModel):
    """Scoping decisions within version"""
    __tablename__ = 'scoping_decisions'
    
    decision_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    version_id = Column(UUID, ForeignKey('scoping_versions.version_id'), nullable=False)
    
    # Scoping data
    attribute_id = Column(UUID(as_uuid=True), ForeignKey("cycle_report_planning_attributes.id"), nullable=False)
    is_in_scope = Column(Boolean, nullable=False)
    scoping_rationale = Column(Text)
    risk_assessment = Column(String(20))  # high, medium, low
    
    # Approval
    approval_status = Column(Enum(ApprovalStatus), nullable=False, default=ApprovalStatus.PENDING)
    
    # Relationships
    version = relationship("ScopingVersion", back_populates="scoping_decisions")


# 4. Sample Selection Phase (with individual tracking)
class SampleSelectionVersion(VersionedEntity):
    """Sample selection versions"""
    __tablename__ = 'sample_selection_versions'
    
    # Selection specific
    selection_criteria = Column(JSONB, nullable=False)
    target_sample_size = Column(Integer, nullable=False)
    actual_sample_size = Column(Integer, nullable=False)
    
    # Relationships
    sample_decisions = relationship("SampleDecision", back_populates="version", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint('cycle_id', 'report_id', 'version_number', name='uq_sample_version'),
    )


class SampleDecision(CustomPKModel):
    """Individual sample decisions"""
    __tablename__ = 'sample_decisions'
    
    decision_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    version_id = Column(UUID, ForeignKey('sample_selection_versions.version_id'), nullable=False)
    
    # Sample data
    sample_identifier = Column(String(255), nullable=False)
    sample_data = Column(JSONB, nullable=False)
    sample_type = Column(String(50), nullable=False)  # population, targeted, risk_based
    
    # Source tracking
    source = Column(Enum(SampleSource), nullable=False)
    source_metadata = Column(JSONB)  # LLM params, upload ref, etc.
    
    # Decision
    decision_status = Column(Enum(ApprovalStatus), nullable=False, default=ApprovalStatus.PENDING)
    decision_notes = Column(Text)
    
    # Lineage (for carried forward samples)
    carried_from_version_id = Column(UUID)
    carried_from_decision_id = Column(UUID)
    
    # Relationships
    version = relationship("SampleSelectionVersion", back_populates="sample_decisions")
    
    __table_args__ = (
        Index('idx_sample_decision_version', 'version_id'),
        Index('idx_sample_decision_status', 'decision_status'),
    )


# 5. Data Owner ID Phase (Audit tracking)
# NOTE: Commented out - DataOwnerAssignment is defined in testing.py
# class DataOwnerAssignment(CustomPKModel):
#     """Data owner assignments with audit trail"""
#     __tablename__ = 'data_owner_assignments'
#     
#     assignment_id = Column(UUID, primary_key=True, default=uuid.uuid4)
#     cycle_id = Column(Integer, ForeignKey('test_cycles.cycle_id'), nullable=False, index=True)
#     report_id = Column(Integer, ForeignKey('reports.id'), nullable=False, index=True)
#     
#     # Temporal context (required)
#     workflow_execution_id = Column(String(255), nullable=False, index=True)
#     
#     # Assignment
#     lob_id = Column(UUID, ForeignKey('lobs.lob_id'), nullable=False)
#     data_owner_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
#     assignment_type = Column(String(50), nullable=False, default='primary')
#     
#     # Tracking
#     assigned_at = Column(DateTime, nullable=False, default=datetime.utcnow)
#     assigned_by_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
#     is_active = Column(Boolean, nullable=False, default=True)
#     
#     # Change tracking
#     previous_assignment_id = Column(UUID, ForeignKey('data_owner_assignments.assignment_id'))
#     change_reason = Column(Text)
#     
#     __table_args__ = (
#         Index('idx_owner_active', 'cycle_id', 'report_id', 'lob_id', 'is_active'),
#     )


# 6. Request Info Phase (Document tracking)
# NOTE: Commented out - DocumentSubmission is defined in request_info.py
# class DocumentSubmission(CustomPKModel):
#     """Document submissions with version tracking"""
#     __tablename__ = 'document_submissions'
#     
#     submission_id = Column(UUID, primary_key=True, default=uuid.uuid4)
#     cycle_id = Column(Integer, ForeignKey('test_cycles.cycle_id'), nullable=False, index=True)
#     report_id = Column(Integer, ForeignKey('reports.id'), nullable=False, index=True)
#     lob_id = Column(UUID, ForeignKey('lobs.lob_id'), nullable=False)
#     
#     # Temporal context
#     workflow_execution_id = Column(String(255), nullable=False, index=True)
#     
#     # Document info
#     document_name = Column(String(255), nullable=False)
#     document_type = Column(String(100), nullable=False)
#     document_path = Column(String(500), nullable=False)
#     document_metadata = Column(JSONB)
#     
#     # Version tracking
#     document_version = Column(Integer, nullable=False, default=1)
#     replaces_submission_id = Column(UUID, ForeignKey('document_submissions.submission_id'))
#     
#     # Submission tracking
#     submitted_at = Column(DateTime, nullable=False, default=datetime.utcnow)
#     submitted_by_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
#     is_current = Column(Boolean, nullable=False, default=True)
#     
#     __table_args__ = (
#         Index('idx_doc_current', 'cycle_id', 'report_id', 'lob_id', 'is_current'),
#     )


# 7. Test Execution Phase (Audit tracking)
class TestExecutionAudit(CustomPKModel):
    """Test execution audit entries"""
    __tablename__ = 'test_execution_audit'
    
    audit_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    cycle_id = Column(Integer, ForeignKey('test_cycles.cycle_id'), nullable=False, index=True)
    report_id = Column(Integer, ForeignKey('reports.id'), nullable=False, index=True)
    test_execution_id = Column(Integer, ForeignKey('cycle_report_test_executions.execution_id'), nullable=False)
    
    # Temporal context
    workflow_execution_id = Column(String(255), nullable=False, index=True)
    
    # Action tracking
    action_type = Column(String(50), nullable=False)  # document_request, retest, update
    action_details = Column(JSONB, nullable=False)
    
    # Request/Response
    requested_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    requested_by_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    
    responded_at = Column(DateTime)
    responded_by_id = Column(Integer, ForeignKey('users.user_id'))
    response_status = Column(String(50))  # fulfilled, rejected, partial
    
    # Metrics
    turnaround_hours = Column(Float)
    
    __table_args__ = (
        Index('idx_test_audit_execution', 'test_execution_id'),
    )


# 8. Observation Management Phase
class ObservationVersion(VersionedEntity):
    """Observation versions"""
    __tablename__ = 'observation_versions'
    
    # Observation specific
    observation_period_start = Column(Date, nullable=False)
    observation_period_end = Column(Date, nullable=False)
    total_observations = Column(Integer, nullable=False, default=0)
    
    # Relationships
    observations = relationship("ObservationDecision", back_populates="version", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint('cycle_id', 'report_id', 'version_number', name='uq_observation_version'),
    )


class ObservationDecision(CustomPKModel):
    """Individual observation decisions"""
    __tablename__ = 'observation_decisions'
    
    decision_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    version_id = Column(UUID, ForeignKey('observation_versions.version_id'), nullable=False)
    
    # Observation data
    observation_type = Column(String(50), nullable=False)  # finding, recommendation, issue
    severity = Column(String(20), nullable=False)  # critical, high, medium, low
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    evidence_references = Column(JSONB)
    
    # Approval
    approval_status = Column(Enum(ApprovalStatus), nullable=False, default=ApprovalStatus.PENDING)
    
    # Remediation
    requires_remediation = Column(Boolean, nullable=False, default=False)
    remediation_deadline = Column(Date)
    
    # Relationships
    version = relationship("ObservationVersion", back_populates="observations")


# 9. Test Report Phase
class TestReportVersion(VersionedEntity):
    """Test report versions"""
    __tablename__ = 'test_report_versions'
    
    # Report specific
    report_title = Column(String(500), nullable=False)
    report_period = Column(String(100), nullable=False)
    executive_summary = Column(Text)
    
    # Document references
    draft_document_path = Column(String(500))
    final_document_path = Column(String(500))
    
    # Sign-off tracking
    requires_executive_signoff = Column(Boolean, nullable=False, default=True)
    executive_signoff_complete = Column(Boolean, nullable=False, default=False)
    
    # Relationships
    sections = relationship("ReportSection", back_populates="version", cascade="all, delete-orphan")
    signoffs = relationship("ReportSignoff", back_populates="version", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint('cycle_id', 'report_id', 'version_number', name='uq_report_version'),
    )


class ReportSection(CustomPKModel):
    """Report sections"""
    __tablename__ = 'report_sections'
    
    section_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    version_id = Column(UUID, ForeignKey('test_report_versions.version_id'), nullable=False)
    
    # Section data
    section_type = Column(String(50), nullable=False)
    section_title = Column(String(255), nullable=False)
    section_content = Column(Text)
    section_order = Column(Integer, nullable=False)
    
    # Relationships
    version = relationship("TestReportVersion", back_populates="sections")


class ReportSignoff(CustomPKModel):
    """Report signoffs"""
    __tablename__ = 'report_signoffs'
    
    signoff_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    version_id = Column(UUID, ForeignKey('test_report_versions.version_id'), nullable=False)
    
    # Signoff data
    signoff_role = Column(String(50), nullable=False)  # test_lead, test_executive, report_owner
    signoff_user_id = Column(Integer, ForeignKey('users.user_id'))
    signoff_status = Column(String(20), nullable=False, default='pending')  # pending, signed, rejected
    signoff_date = Column(DateTime)
    signoff_notes = Column(Text)
    
    # Relationships
    version = relationship("TestReportVersion", back_populates="signoffs")
    
    __table_args__ = (
        UniqueConstraint('version_id', 'signoff_role', name='uq_report_signoff'),
    )