"""
Complete versioning models for all 9 phases with Temporal integration
"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, Date, Float, ForeignKey, Enum, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional
import uuid
import enum

from app.models.base import CustomPKModel
from app.models.audit import AuditMixin
from app.models.versioning import VersionedMixin


# Enums
class VersionStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class DecisionType(str, enum.Enum):
    INCLUDE = "include"
    EXCLUDE = "exclude"
    MODIFY = "modify"


class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_CHANGES = "needs_changes"


class SampleSource(str, enum.Enum):
    TESTER = "tester"
    LLM = "llm"
    MANUAL = "manual"
    CARRIED_FORWARD = "carried_forward"


# Enhanced Base Mixin with Temporal Integration
class TemporalVersionedMixin(VersionedMixin):
    """Enhanced versioning mixin with Temporal workflow integration"""
    
    __abstract__ = True
    
    # Temporal integration fields
    workflow_execution_id = Column(String(255), index=True)
    workflow_run_id = Column(String(255))
    workflow_step_id = Column(UUID, ForeignKey('workflow_steps.step_id'))
    activity_name = Column(String(100))
    
    # Master record tracking
    master_record_id = Column(UUID, index=True)
    
    # Relationships
    workflow_step = relationship("WorkflowStep", back_populates="versions", lazy="select")


# 1. Planning Phase Models
class PlanningPhaseVersion(CustomPKModel, TemporalVersionedMixin):
    """Versioned planning phase with attribute decisions"""
    __tablename__ = 'planning_phase_versions'
    
    version_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    cycle_id = Column(Integer, ForeignKey('test_cycles.cycle_id'), nullable=False)
    report_id = Column(Integer, ForeignKey('reports.report_id'), nullable=False)
    
    # Phase metadata
    phase_name = Column(String(50), default="Planning")
    planning_metadata = Column(JSONB)
    
    # Planning specific fields
    total_attributes = Column(Integer, default=0)
    included_attributes = Column(Integer, default=0)
    excluded_attributes = Column(Integer, default=0)
    
    # Relationships
    attribute_decisions = relationship("AttributeDecision", back_populates="planning_version", lazy="select")
    
    __table_args__ = (
        UniqueConstraint('cycle_id', 'report_id', 'version_number'),
        Index('idx_planning_cycle_report', 'cycle_id', 'report_id'),
        Index('idx_planning_workflow', 'workflow_execution_id'),
    )


class AttributeDecision(CustomPKModel, AuditMixin):
    """Individual attribute decisions within a planning version"""
    __tablename__ = 'attribute_decisions'
    
    decision_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    planning_version_id = Column(UUID, ForeignKey('planning_phase_versions.version_id'), nullable=False)
    
    # Attribute reference
    attribute_id = Column(Integer, ForeignKey('report_attributes.attribute_id'), nullable=False)
    attribute_data = Column(JSONB, nullable=False)
    
    # Decision tracking
    decision_type = Column(Enum(DecisionType), default=DecisionType.INCLUDE)
    decision_reason = Column(Text)
    decision_metadata = Column(JSONB)
    
    # Lineage tracking
    carried_from_version_id = Column(UUID)
    modification_history = Column(JSONB)  # Array of changes
    
    # Relationships
    planning_version = relationship("PlanningPhaseVersion", back_populates="attribute_decisions")
    
    __table_args__ = (
        Index('idx_attr_decision_version', 'planning_version_id'),
        Index('idx_attr_decision_attribute', 'attribute_id'),
    )


# 2. Data Profiling Phase Models
class DataProfilingVersion(CustomPKModel, TemporalVersionedMixin):
    """Versioned data profiling rules"""
    __tablename__ = 'data_profiling_versions'
    
    version_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    cycle_id = Column(Integer, ForeignKey('test_cycles.cycle_id'), nullable=False)
    report_id = Column(Integer, ForeignKey('reports.report_id'), nullable=False)
    
    # Phase metadata
    phase_name = Column(String(50), default="Data Profiling")
    
    # Profiling context
    source_data_reference = Column(JSONB)  # Files, tables, etc.
    profiling_parameters = Column(JSONB)
    total_rules = Column(Integer, default=0)
    approved_rules = Column(Integer, default=0)
    
    # Relationships
    profiling_rules = relationship("ProfilingRuleDecision", back_populates="profiling_version", lazy="select")
    
    __table_args__ = (
        UniqueConstraint('cycle_id', 'report_id', 'version_number'),
        Index('idx_profiling_cycle_report', 'cycle_id', 'report_id'),
    )


class ProfilingRuleDecision(CustomPKModel, AuditMixin):
    """Individual profiling rule decisions"""
    __tablename__ = 'profiling_rule_decisions'
    
    decision_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    profiling_version_id = Column(UUID, ForeignKey('data_profiling_versions.version_id'), nullable=False)
    
    # Rule definition
    rule_type = Column(String(50))  # 'validation', 'transformation', 'quality_check'
    rule_definition = Column(JSONB, nullable=False)
    rule_name = Column(String(255))
    rule_description = Column(Text)
    
    # Recommendation and approval
    recommended_by_id = Column(Integer, ForeignKey('users.user_id'))
    recommendation_reason = Column(Text)
    
    approval_status = Column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING)
    approved_by_id = Column(Integer, ForeignKey('users.user_id'))
    approval_notes = Column(Text)
    approval_timestamp = Column(DateTime)
    
    # Relationships
    profiling_version = relationship("DataProfilingVersion", back_populates="cycle_report_data_profiling_rules")


# 3. Scoping Phase Models
class ScopingVersion(CustomPKModel, TemporalVersionedMixin):
    """Versioned scoping decisions"""
    __tablename__ = 'scoping_versions'
    
    version_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    cycle_id = Column(Integer, ForeignKey('test_cycles.cycle_id'), nullable=False)
    report_id = Column(Integer, ForeignKey('reports.report_id'), nullable=False)
    
    # Phase metadata
    phase_name = Column(String(50), default="Scoping")
    
    # Scoping context
    scoping_criteria = Column(JSONB)
    total_attributes = Column(Integer, default=0)
    scoped_attributes = Column(Integer, default=0)
    out_of_scope_attributes = Column(Integer, default=0)
    
    # Relationships
    scoping_decisions = relationship("ScopingDecision", back_populates="scoping_version", lazy="select")
    
    __table_args__ = (
        UniqueConstraint('cycle_id', 'report_id', 'version_number'),
        Index('idx_scoping_cycle_report', 'cycle_id', 'report_id'),
    )


class ScopingDecision(CustomPKModel, AuditMixin):
    """Individual attribute scoping decisions"""
    __tablename__ = 'scoping_decisions'
    
    decision_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    scoping_version_id = Column(UUID, ForeignKey('scoping_versions.version_id'), nullable=False)
    
    # Attribute reference
    attribute_id = Column(Integer, ForeignKey('report_attributes.attribute_id'), nullable=False)
    
    # Scoping decision
    is_in_scope = Column(Boolean, nullable=False)
    scoping_rationale = Column(Text)
    risk_rating = Column(String(20))  # 'high', 'medium', 'low'
    
    # Recommendation and approval tracking
    recommended_by_id = Column(Integer, ForeignKey('users.user_id'))
    recommendation_type = Column(String(50))  # 'tester', 'automated', 'carryforward'
    
    approval_status = Column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING)
    approved_by_id = Column(Integer, ForeignKey('users.user_id'))
    approval_timestamp = Column(DateTime)
    
    # Relationships
    scoping_version = relationship("ScopingVersion", back_populates="scoping_decisions")


# 4. Sample Selection Phase Models
class SampleSelectionVersion(CustomPKModel, TemporalVersionedMixin):
    """Enhanced sample selection versioning"""
    __tablename__ = 'sample_selection_versions'
    
    version_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    cycle_id = Column(Integer, ForeignKey('test_cycles.cycle_id'), nullable=False)
    report_id = Column(Integer, ForeignKey('reports.report_id'), nullable=False)
    
    # Phase metadata
    phase_name = Column(String(50), default="Sample Selection")
    
    # Selection metadata
    selection_criteria = Column(JSONB)
    target_sample_size = Column(Integer)
    actual_sample_size = Column(Integer)
    
    # Generation tracking
    generation_methods = Column(JSONB)  # Array of methods used
    
    # Relationships
    sample_decisions = relationship("SampleDecision", back_populates="selection_version", lazy="select")
    
    __table_args__ = (
        UniqueConstraint('cycle_id', 'report_id', 'version_number'),
        Index('idx_sample_sel_cycle_report', 'cycle_id', 'report_id'),
    )


class SampleDecision(CustomPKModel, AuditMixin):
    """Enhanced sample decision tracking"""
    __tablename__ = 'sample_decisions'
    
    decision_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    selection_version_id = Column(UUID, ForeignKey('sample_selection_versions.version_id'), nullable=False)
    
    # Sample data
    sample_identifier = Column(String(255), nullable=False)
    sample_data = Column(JSONB, nullable=False)
    sample_type = Column(String(50))  # 'population', 'targeted', 'risk_based'
    
    # Recommendation tracking
    recommendation_source = Column(Enum(SampleSource), nullable=False)
    recommended_by_id = Column(Integer, ForeignKey('users.user_id'))
    recommendation_timestamp = Column(DateTime)
    recommendation_metadata = Column(JSONB)  # LLM params, manual upload ref, etc.
    
    # Approval tracking
    decision_status = Column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING)
    decided_by_id = Column(Integer, ForeignKey('users.user_id'))
    decision_timestamp = Column(DateTime)
    decision_notes = Column(Text)
    
    # Lineage
    carried_from_version_id = Column(UUID)
    carried_from_decision_id = Column(UUID)
    modification_reason = Column(Text)
    
    # Relationships
    selection_version = relationship("SampleSelectionVersion", back_populates="sample_decisions")
    
    __table_args__ = (
        Index('idx_sample_decision_version', 'selection_version_id'),
        Index('idx_sample_decision_status', 'decision_status'),
    )


# 5. Data Owner ID Phase Models (Audit Only)
class DataOwnerAssignment(CustomPKModel, AuditMixin):
    """Data owner assignments with full audit trail"""
    __tablename__ = 'data_owner_assignments'
    
    assignment_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    cycle_id = Column(Integer, ForeignKey('test_cycles.cycle_id'), nullable=False)
    report_id = Column(Integer, ForeignKey('reports.report_id'), nullable=False)
    
    # Temporal context
    workflow_execution_id = Column(String(255), index=True)
    workflow_step_id = Column(UUID, ForeignKey('workflow_steps.step_id'))
    
    # Assignment details
    data_owner_id = Column(Integer, ForeignKey('users.user_id'))
    lob_id = Column(UUID, ForeignKey('lobs.lob_id'))
    assignment_type = Column(String(50))  # 'primary', 'backup', 'delegate'
    
    # Status tracking
    status = Column(String(50), default='active')  # 'active', 'inactive', 'transferred'
    effective_from = Column(DateTime, default=datetime.utcnow)
    effective_to = Column(DateTime)
    
    # Change tracking
    previous_assignment_id = Column(UUID, ForeignKey('data_owner_assignments.assignment_id'))
    change_reason = Column(Text)
    
    # Relationships
    change_history = relationship("DataOwnerChangeHistory", back_populates="assignment", lazy="select")
    
    __table_args__ = (
        Index('idx_owner_assign_cycle', 'cycle_id', 'report_id'),
        Index('idx_owner_assign_workflow', 'workflow_execution_id'),
    )


class DataOwnerChangeHistory(CustomPKModel):
    """Detailed history of data owner changes"""
    __tablename__ = 'data_owner_change_history'
    
    history_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    assignment_id = Column(UUID, ForeignKey('data_owner_assignments.assignment_id'), nullable=False)
    
    # Change details
    change_type = Column(String(50))  # 'created', 'transferred', 'deactivated'
    changed_by_id = Column(Integer, ForeignKey('users.user_id'))
    changed_at = Column(DateTime, default=datetime.utcnow)
    
    # Before/after state
    previous_state = Column(JSONB)
    new_state = Column(JSONB)
    change_metadata = Column(JSONB)
    
    # Relationships
    assignment = relationship("DataOwnerAssignment", back_populates="change_history")


# 6. Request for Information Phase Models (Audit Only)
class DocumentSubmission(CustomPKModel, AuditMixin):
    """Document submissions with version tracking"""
    __tablename__ = 'document_submissions'
    
    submission_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    cycle_id = Column(Integer, ForeignKey('test_cycles.cycle_id'), nullable=False)
    report_id = Column(Integer, ForeignKey('reports.report_id'), nullable=False)
    
    # Temporal context
    workflow_execution_id = Column(String(255), index=True)
    workflow_step_id = Column(UUID, ForeignKey('workflow_steps.step_id'))
    
    # Document reference
    document_id = Column(UUID, nullable=False)
    document_version = Column(Integer, default=1)
    document_metadata = Column(JSONB)
    
    # Submission tracking
    submitted_by_id = Column(Integer, ForeignKey('users.user_id'))
    submitted_at = Column(DateTime, default=datetime.utcnow)
    submission_type = Column(String(50))  # 'initial', 'revision', 'supplemental'
    
    # Status
    status = Column(String(50), default='pending_review')
    reviewed_by_id = Column(Integer, ForeignKey('users.user_id'))
    review_notes = Column(Text)
    
    # Version chain
    replaces_submission_id = Column(UUID, ForeignKey('document_submissions.submission_id'))
    is_current = Column(Boolean, default=True)
    
    # LOB context
    lob_id = Column(UUID, ForeignKey('lobs.lob_id'))
    
    # Relationships
    revision_history = relationship("DocumentRevisionHistory", back_populates="submission", lazy="select")
    
    __table_args__ = (
        Index('idx_doc_submit_cycle', 'cycle_id', 'report_id'),
        Index('idx_doc_submit_workflow', 'workflow_execution_id'),
        Index('idx_doc_submit_current', 'is_current'),
    )


class DocumentRevisionHistory(CustomPKModel):
    """Track all document changes"""
    __tablename__ = 'document_revision_history'
    
    history_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    submission_id = Column(UUID, ForeignKey('document_submissions.submission_id'), nullable=False)
    
    # Revision details
    revision_type = Column(String(50))  # 'content_update', 'metadata_change', 'resubmission'
    revision_reason = Column(Text)
    changed_fields = Column(JSONB)  # List of what changed
    
    # Tracking
    revised_by_id = Column(Integer, ForeignKey('users.user_id'))
    revised_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    submission = relationship("DocumentSubmission", back_populates="revision_history")


# 7. Test Execution Phase Models (Audit Only)
class TestExecutionAudit(CustomPKModel, AuditMixin):
    """Audit trail for test execution phase"""
    __tablename__ = 'test_execution_audit'
    
    audit_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    cycle_id = Column(Integer, ForeignKey('test_cycles.cycle_id'), nullable=False)
    report_id = Column(Integer, ForeignKey('reports.report_id'), nullable=False)
    test_execution_id = Column(Integer, ForeignKey("cycle_report_test_execution_test_executions.execution_id"))
    
    # Temporal context
    workflow_execution_id = Column(String(255), index=True)
    workflow_step_id = Column(UUID, ForeignKey('workflow_steps.step_id'))
    
    # Action tracking
    action_type = Column(String(50))  # 'document_request', 'data_update_request', 'test_rerun'
    action_details = Column(JSONB)
    
    # Request tracking
    requested_by_id = Column(Integer, ForeignKey('users.user_id'))
    requested_at = Column(DateTime, default=datetime.utcnow)
    request_reason = Column(Text)
    
    # Response tracking
    responded_by_id = Column(Integer, ForeignKey('users.user_id'))
    responded_at = Column(DateTime)
    response_status = Column(String(50))  # 'fulfilled', 'rejected', 'partial'
    response_notes = Column(Text)
    
    # Metrics
    turnaround_time_hours = Column(Float)
    impact_on_timeline = Column(String(50))  # 'none', 'minor_delay', 'major_delay'
    
    __table_args__ = (
        Index('idx_test_exec_audit_cycle', 'cycle_id', 'report_id'),
        Index('idx_test_exec_audit_workflow', 'workflow_execution_id'),
    )


# 8. Observation Management Phase Models
class ObservationVersion(CustomPKModel, TemporalVersionedMixin):
    """Versioned observations"""
    __tablename__ = 'observation_versions'
    
    version_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    cycle_id = Column(Integer, ForeignKey('test_cycles.cycle_id'), nullable=False)
    report_id = Column(Integer, ForeignKey('reports.report_id'), nullable=False)
    
    # Phase metadata
    phase_name = Column(String(50), default="Observation Management")
    
    # Observation context
    observation_period_start = Column(Date)
    observation_period_end = Column(Date)
    total_observations = Column(Integer, default=0)
    approved_observations = Column(Integer, default=0)
    
    # Relationships
    observations = relationship("ObservationDecision", back_populates="observation_version", lazy="select")
    
    __table_args__ = (
        UniqueConstraint('cycle_id', 'report_id', 'version_number'),
        Index('idx_observation_cycle_report', 'cycle_id', 'report_id'),
    )


class ObservationDecision(CustomPKModel, AuditMixin):
    """Individual observation decisions"""
    __tablename__ = 'observation_decisions'
    
    decision_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    observation_version_id = Column(UUID, ForeignKey('observation_versions.version_id'), nullable=False)
    
    # Link to existing observation
    observation_id = Column(Integer, ForeignKey('observations.observation_id'))
    
    # Observation details (denormalized for versioning)
    observation_type = Column(String(50))  # 'finding', 'recommendation', 'compliance_issue'
    severity = Column(String(20))  # 'critical', 'high', 'medium', 'low'
    observation_data = Column(JSONB)
    
    # Creation and approval
    created_by_id = Column(Integer, ForeignKey('users.user_id'))
    creation_timestamp = Column(DateTime)
    
    approval_status = Column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING)
    approved_by_id = Column(Integer, ForeignKey('users.user_id'))
    approval_timestamp = Column(DateTime)
    approval_notes = Column(Text)
    
    # Evidence and remediation
    evidence_references = Column(JSONB)  # Links to supporting documents
    remediation_status = Column(String(50))
    remediation_deadline = Column(Date)
    
    # Relationships
    observation_version = relationship("ObservationVersion", back_populates="observations")


# 9. Finalize Test Report Phase Models
class TestReportVersion(CustomPKModel, TemporalVersionedMixin):
    """Versioned test report finalization"""
    __tablename__ = 'test_report_versions'
    
    version_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    cycle_id = Column(Integer, ForeignKey('test_cycles.cycle_id'), nullable=False)
    report_id = Column(Integer, ForeignKey('reports.report_id'), nullable=False)
    
    # Phase metadata
    phase_name = Column(String(50), default="Finalize Test Report")
    
    # Report metadata
    report_title = Column(String(255), nullable=False)
    report_period_start = Column(Date)
    report_period_end = Column(Date)
    executive_summary = Column(Text)
    
    # Report components
    included_sections = Column(JSONB)  # List of sections to include
    report_template_id = Column(UUID)
    
    # Generation details
    generated_at = Column(DateTime)
    generation_method = Column(String(50))  # 'manual', 'automated', 'hybrid'
    
    # Final document references
    draft_document_id = Column(UUID)
    final_document_id = Column(UUID)
    
    # Sign-off tracking
    requires_executive_approval = Column(Boolean, default=True)
    executive_approved_by_id = Column(Integer, ForeignKey('users.user_id'))
    executive_approval_date = Column(DateTime)
    
    # Relationships
    report_sections = relationship("TestReportSection", back_populates="report_version", lazy="select")
    sign_offs = relationship("TestReportSignOff", back_populates="report_version", lazy="select")
    
    __table_args__ = (
        UniqueConstraint('cycle_id', 'report_id', 'version_number'),
        Index('idx_test_report_cycle_report', 'cycle_id', 'report_id'),
    )


class TestReportSection(CustomPKModel, AuditMixin):
    """Individual sections within a test report"""
    __tablename__ = "cycle_report_test_report_sections"
    
    section_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    report_version_id = Column(UUID, ForeignKey('test_report_versions.version_id'), nullable=False)
    
    # Section details
    section_type = Column(String(50))  # 'executive_summary', 'findings', 'recommendations', etc.
    section_title = Column(String(255))
    section_content = Column(Text)
    section_order = Column(Integer)
    
    # Content tracking
    content_source = Column(String(50))  # 'manual', 'generated', 'imported'
    source_references = Column(JSONB)  # Links to observations, test results, etc.
    
    # Review status
    reviewed_by_id = Column(Integer, ForeignKey('users.user_id'))
    review_status = Column(String(50), default='pending')
    review_notes = Column(Text)
    
    # Relationships
    report_version = relationship("TestReportVersion", back_populates="report_sections")


class TestReportSignOff(CustomPKModel, AuditMixin):
    """Track all required sign-offs for test report"""
    __tablename__ = 'test_report_signoffs'
    
    signoff_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    report_version_id = Column(UUID, ForeignKey('test_report_versions.version_id'), nullable=False)
    
    # Sign-off details
    signoff_role = Column(String(50))  # 'test_lead', 'test_executive', 'report_owner'
    signoff_user_id = Column(Integer, ForeignKey('users.user_id'))
    signoff_status = Column(String(50), default='pending')  # 'pending', 'signed', 'rejected'
    signoff_date = Column(DateTime)
    signoff_comments = Column(Text)
    
    # Delegation support
    delegated_from_id = Column(Integer, ForeignKey('users.user_id'))
    delegation_reason = Column(Text)
    
    # Relationships
    report_version = relationship("TestReportVersion", back_populates="sign_offs")


# Workflow Version Operations Tracking
class WorkflowVersionOperation(CustomPKModel):
    """Track version operations within workflows"""
    __tablename__ = 'workflow_version_operations'
    
    operation_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    workflow_execution_id = Column(String(255), nullable=False, index=True)
    workflow_step_id = Column(UUID, ForeignKey('workflow_steps.step_id'))
    
    # Operation details
    operation_type = Column(String(50), nullable=False)  # 'create', 'approve', 'reject', 'revise'
    phase_name = Column(String(50), nullable=False)
    version_id = Column(UUID, index=True)
    
    # Timing
    initiated_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Results
    success = Column(Boolean)
    error_message = Column(Text)
    operation_metadata = Column(JSONB)
    
    __table_args__ = (
        Index('idx_wf_ver_ops_phase', 'phase_name', 'operation_type'),
    )