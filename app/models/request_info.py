"""
Request for Information phase models
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, Float, JSON, CheckConstraint, UniqueConstraint, Index, text, cast
from sqlalchemy.orm import relationship, foreign
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.dialects.postgresql import ENUM, JSONB, UUID 
from datetime import datetime
from app.models.base import CustomPKModel
from app.models.audit_mixin import AuditMixin
import uuid

# ENUM types for request info phase
submission_type_enum = ENUM(
    'Document',
    'Database', 
    'Mixed',
    name='submission_type_enum'
)

submission_status_enum = ENUM(
    'Pending',
    'In Progress',
    'Submitted',
    'Validated',
    'Requires Revision',
    'Overdue',
    name='submission_status_enum'
)

document_type_enum = ENUM(
    'Source Document',
    'Supporting Evidence',
    'Data Extract',
    'Query Result',
    'Other',
    name='document_type_enum'
)

validation_status_enum = ENUM(
    'Pending',
    'Passed',
    'Failed',
    'Warning',
    name='validation_status_enum'
)

# Evidence management enums
evidence_type_enum = ENUM(
    'document',
    'data_source',
    name='evidence_type_enum'
)

evidence_validation_status_enum = ENUM(
    'pending',
    'valid',
    'invalid',
    'requires_review',
    name='evidence_validation_status_enum'
)

validation_result_enum = ENUM(
    'passed',
    'failed',
    'warning',
    name='validation_result_enum'
)

tester_decision_enum = ENUM(
    'approved',
    'rejected',
    'requires_revision',
    name='tester_decision_enum'
)

# Request Info phase status enum
request_info_phase_status_enum = ENUM(
    'Not Started',
    'In Progress',
    'Complete',
    name='request_info_phase_status_enum'
)

# Test case status enum
test_case_status_enum = ENUM(
    'Pending',
    'Submitted',
    'Overdue',
    name='test_case_status_enum'
)

# Evidence type enum
evidence_type_enum = ENUM(
    'document',
    'data_source',
    name='evidence_type_enum'
)

# Evidence validation status enum
evidence_validation_status_enum = ENUM(
    'pending',
    'valid',
    'invalid',
    'requires_review',
    name='evidence_validation_status_enum'
)

# Validation result enum
validation_result_enum = ENUM(
    'passed',
    'failed',
    'warning',
    name='validation_result_enum'
)

# Tester decision enum
tester_decision_enum = ENUM(
    'approved',
    'rejected',
    'requires_revision',
    name='tester_decision_enum'
)


# DEPRECATED: Using unified WorkflowPhase instead
# class RequestInfoPhase(CustomPKModel, AuditMixin):
#     """Request for Information phase management"""
#     
#     __tablename__ = "cycle_report_request_info_phases"
#     
#     phase_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
#     cycle_id = Column(Integer, ForeignKey('test_cycles.cycle_id'), nullable=False)
#     report_id = Column(Integer, ForeignKey('reports.id'), nullable=False)
#     
#     # Phase details - match actual database schema
#     phase_status = Column(String(50), default='Not Started', nullable=False)
#     
#     # Timing
#     started_by = Column(Integer, ForeignKey('users.user_id'), nullable=True)
#     started_at = Column(DateTime(timezone=True), nullable=True)
#     completed_by = Column(Integer, ForeignKey('users.user_id'), nullable=True)
#     completed_at = Column(DateTime(timezone=True), nullable=True)
#     submission_deadline = Column(DateTime(timezone=True), nullable=True)
#     
#     # Configuration - match actual database schema
#     instructions = Column(Text, nullable=True)
#     reminder_schedule = Column(JSONB, nullable=True)
#     planned_start_date = Column(DateTime(timezone=True), nullable=True)
#     planned_end_date = Column(DateTime(timezone=True), nullable=True)
#     
#     # Metadata
#     created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
#     updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
#     
#     # Relationships
#     cycle = relationship("TestCycle", back_populates="request_info_phases")
#     report = relationship("Report", back_populates="request_info_phases")
#     started_by_user = relationship("User", foreign_keys=[started_by])
#     completed_by_user = relationship("User", foreign_keys=[completed_by])
#     test_cases = relationship("TestCase", back_populates="phase", cascade="all, delete-orphan")
#     notifications = relationship("DataProviderNotification", back_populates="phase", cascade="all, delete-orphan")
#     
#     def __repr__(self):
#         return f"<RequestInfoPhase(id='{self.phase_id}', status='{self.phase_status}')>"


class CycleReportTestCase(CustomPKModel):
    """Test cases for cycle reports - matches actual cycle_report_test_cases table"""
    
    __tablename__ = "cycle_report_test_cases"
    
    id = Column(Integer, primary_key=True)
    test_case_number = Column(String(50), nullable=False)
    test_case_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    expected_outcome = Column(Text, nullable=True)
    test_type = Column(String(50), nullable=True)
    query_text = Column(Text, nullable=True)
    version = Column(Integer, default=1, nullable=True)
    status = Column(ENUM('Not Started', 'In Progress', 'Submitted', 'Pending Approval', 'Complete', name='phase_status_enum'), default='Not Started', nullable=False)
    phase_id = Column(Integer, ForeignKey('workflow_phases.phase_id'), nullable=True)
    
    # Sample and attribute references
    sample_id = Column(String(255), nullable=False)
    attribute_id = Column(Integer, ForeignKey('cycle_report_planning_attributes.id'), nullable=False)
    attribute_name = Column(String(255), nullable=False)
    lob_id = Column(Integer, ForeignKey('lobs.lob_id'), nullable=False)
    
    # Data owner assignment
    data_owner_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    assigned_by = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    assigned_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    # Submission tracking
    submission_deadline = Column(DateTime(timezone=True), nullable=True)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    special_instructions = Column(Text, nullable=True)
    
    # Audit fields
    created_by = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    updated_by = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    phase = relationship("app.models.workflow.WorkflowPhase")
    attribute = relationship("app.models.report_attribute.ReportAttribute", foreign_keys=[attribute_id])
    lob = relationship("app.models.lob.LOB", foreign_keys=[lob_id])
    data_owner = relationship("User", foreign_keys=[data_owner_id])
    assigned_by_user = relationship("User", foreign_keys=[assigned_by])
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    evidence_submissions = relationship("TestCaseEvidence", back_populates="test_case", foreign_keys="TestCaseEvidence.test_case_id")
    
    # Sample relationship - the sample_id is stored as string in test case but UUID in samples table
    # Using a custom join condition to handle the type mismatch
    sample = relationship(
        "app.models.sample_selection.SampleSelectionSample",
        primaryjoin="CycleReportTestCase.sample_id == cast(app.models.sample_selection.SampleSelectionSample.sample_id, String)",
        foreign_keys=[sample_id],
        uselist=False,
        viewonly=True
    )
    
    # Properties for compatibility
    @property
    def test_case_id(self):
        return str(self.id)
    
    @property
    def cycle_id(self):
        return self.phase.cycle_id if self.phase else None
    
    @property 
    def report_id(self):
        return self.phase.report_id if self.phase else None
    
    @property
    def primary_key_attributes(self):
        """Get primary key attributes as a dict - populated from sample data"""
        # This is now populated in the API endpoint when fetching test cases
        return getattr(self, '_primary_key_attributes', {})
    
    @property
    def sample_identifier(self):
        """Get sample identifier - combination of primary key values"""
        return self.sample_id
    
    @property
    def expected_evidence_type(self):
        """Expected evidence type based on attribute configuration"""
        return "document"  # Default, could be enhanced based on attribute type
    
    def __repr__(self):
        return f"<CycleReportTestCase(id={self.id}, name='{self.test_case_name}', status='{self.status}')>"


class DataProviderNotification(CustomPKModel, AuditMixin):
    """Data provider notifications for information requests"""
    
    __tablename__ = "data_owner_notifications"
    
    notification_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    phase_id = Column(Integer, ForeignKey('workflow_phases.phase_id'), nullable=False)
    cycle_id = Column(Integer, ForeignKey('test_cycles.cycle_id'), nullable=False)
    report_id = Column(Integer, ForeignKey('reports.id'), nullable=False)
    data_owner_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    
    # Notification details
    assigned_attributes = Column(JSONB, nullable=False)  # List of attribute names
    sample_count = Column(Integer, nullable=False)
    submission_deadline = Column(DateTime(timezone=True), nullable=False)
    portal_access_url = Column(String(500), nullable=False)
    custom_instructions = Column(Text, nullable=True)
    
    # Tracking
    notification_sent_at = Column(DateTime(timezone=True), nullable=True)
    first_access_at = Column(DateTime(timezone=True), nullable=True)
    last_access_at = Column(DateTime(timezone=True), nullable=True)
    access_count = Column(Integer, default=0, nullable=False)
    is_acknowledged = Column(Boolean, default=False, nullable=False)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    
    # Status tracking
    status = Column(submission_status_enum, default='Pending', nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    phase = relationship("app.models.workflow.WorkflowPhase")
    data_owner = relationship("User", foreign_keys=[data_owner_id])
    
    def __repr__(self):
        return f"<DataProviderNotification(id='{self.notification_id}', data_owner_id={self.data_owner_id})>"


# TestCaseDocumentSubmission has been removed - use TestCaseEvidence instead


class RequestInfoAuditLog(CustomPKModel, AuditMixin):
    """Audit log for Request for Information phase"""
    
    __tablename__ = "cycle_report_request_info_audit_logs"
    
    audit_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    cycle_id = Column(Integer, ForeignKey('test_cycles.cycle_id'), nullable=False)
    report_id = Column(Integer, ForeignKey('reports.id'), nullable=False)
    phase_id = Column(Integer, ForeignKey('workflow_phases.phase_id'), nullable=True)
    
    # Audit details
    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)  # Phase, TestCase, DocumentSubmission, etc.
    entity_id = Column(String(36), nullable=True)
    performed_by = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    performed_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    # Change tracking
    old_values = Column(JSONB, nullable=True)
    new_values = Column(JSONB, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Request metadata
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    session_id = Column(String(100), nullable=True)
    
    # Relationships
    cycle = relationship("TestCycle")
    report = relationship("Report")
    phase = relationship("app.models.workflow.WorkflowPhase")
    user = relationship("User", foreign_keys=[performed_by])
    
    def __repr__(self):
        return f"<RequestInfoAuditLog(id='{self.audit_id}', action='{self.action}')>"


# Add relationships to existing models
def setup_request_info_relationships():
    """Setup relationships for request info models"""
    from app.models.test_cycle import TestCycle
    from app.models.report import Report
    from app.models.report_attribute import ReportAttribute
    
    # Add relationship to TestCycle
    if not hasattr(TestCycle, 'request_info_phases'):
        TestCycle.request_info_phases = relationship("RequestInfoPhase", back_populates="cycle")
    
    # Add relationship to Report
    if not hasattr(Report, 'request_info_phases'):
        Report.request_info_phases = relationship("RequestInfoPhase", back_populates="report")
    
    # Add relationship to ReportAttribute  
    if not hasattr(ReportAttribute, 'database_submissions'):
        ReportAttribute.database_submissions = relationship("DatabaseSubmission", back_populates="attribute")
    
    if not hasattr(ReportAttribute, 'submissions'):
        ReportAttribute.submissions = relationship("DataProviderSubmission", back_populates="attribute")


# New Evidence Management Models

class TestCaseSourceEvidence(CustomPKModel):
    """Source evidence for test cases - supports both document and data source evidence"""
    
    __tablename__ = "cycle_report_request_info_testcase_source_evidence"
    
    id = Column(Integer, primary_key=True)
    phase_id = Column(Integer, ForeignKey('workflow_phases.phase_id'), nullable=False)
    # cycle_id = Column(Integer, ForeignKey('test_cycles.cycle_id'), nullable=False)  # Not in database
    # report_id = Column(Integer, ForeignKey('reports.id'), nullable=False)  # Not in database
    test_case_id = Column(Integer, ForeignKey('cycle_report_test_cases.id'), nullable=False)
    sample_id = Column(String(255), nullable=False)
    # Attribute reference - storing attribute_id for easier retrieval
    attribute_id = Column(Integer, nullable=True)  # References cycle_report_planning_attributes.id
    
    # Evidence type and source
    evidence_type = Column(evidence_type_enum, nullable=False)
    
    # Document evidence fields
    document_name = Column(String(255), nullable=True)
    document_path = Column(String(500), nullable=True)
    document_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    document_hash = Column(String(128), nullable=True)
    
    # Data source evidence fields  
    data_source_id = Column(Integer, ForeignKey('cycle_report_planning_data_sources.id'), nullable=True)
    rfi_data_source_id = Column(UUID(as_uuid=True), ForeignKey('cycle_report_rfi_data_sources.data_source_id'), nullable=True)
    query_text = Column(Text, nullable=True)
    query_parameters = Column(JSONB, nullable=True)
    query_result_sample = Column(JSONB, nullable=True)  # Sample of query results for verification
    query_validation_id = Column(UUID(as_uuid=True), ForeignKey('cycle_report_rfi_query_validations.validation_id'), nullable=True)
    
    # Submission metadata
    submitted_by = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    submitted_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    submission_notes = Column(Text, nullable=True)
    
    # Validation and review
    validation_status = Column(evidence_validation_status_enum, default='pending', nullable=False)
    validation_notes = Column(Text, nullable=True)
    validated_by = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    validated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Version tracking (for resubmissions)
    version_number = Column(Integer, default=1, nullable=False)
    is_current = Column(Boolean, default=True, nullable=False)
    replaced_by = Column(Integer, ForeignKey('cycle_report_request_info_testcase_source_evidence.id'), nullable=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    updated_by = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    
    # Relationships
    phase = relationship("app.models.workflow.WorkflowPhase")
    # cycle = relationship("TestCycle")  # cycle_id column not in database
    # report = relationship("Report")  # report_id column not in database
    test_case = relationship("CycleReportTestCase")
    # Attribute relationship updated - attributes now accessed through WorkflowPhase -> PlanningVersion -> PlanningAttribute
    # data_source = relationship("app.models.planning.PlanningDataSource", foreign_keys=[data_source_id])  # Disabled - using CycleReportDataSource instead
    submitted_by_user = relationship("User", foreign_keys=[submitted_by])
    validated_by_user = relationship("User", foreign_keys=[validated_by])
    created_by_user = relationship("User", foreign_keys=[created_by])
    updated_by_user = relationship("User", foreign_keys=[updated_by])
    replaced_by_evidence = relationship("TestCaseSourceEvidence", remote_side=[id])
    
    # Related records
    validation_results = relationship("EvidenceValidationResult", back_populates="evidence", cascade="all, delete-orphan")
    tester_decisions = relationship("TesterDecision", back_populates="evidence", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('test_case_id', 'version_number', name='uq_evidence_test_case_version'),
        CheckConstraint(
            "(evidence_type = 'document' AND document_name IS NOT NULL) OR "
            "(evidence_type = 'data_source' AND data_source_id IS NOT NULL AND query_text IS NOT NULL)",
            name='check_evidence_type_constraints'
        ),
    )
    
    def __repr__(self):
        return f"<TestCaseSourceEvidence(id={self.id}, test_case_id={self.test_case_id}, evidence_type='{self.evidence_type}', version={self.version_number})>"


class EvidenceValidationResult(CustomPKModel):
    """Validation results for evidence submissions"""
    
    __tablename__ = "cycle_report_request_info_evidence_validation"
    
    id = Column(Integer, primary_key=True)
    evidence_id = Column(Integer, ForeignKey('cycle_report_request_info_testcase_source_evidence.id'), nullable=False)
    validation_rule = Column(String(255), nullable=False)
    validation_result = Column(validation_result_enum, nullable=False)
    validation_message = Column(Text, nullable=True)
    validated_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    validated_by = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    
    # Relationships
    evidence = relationship("TestCaseSourceEvidence", back_populates="validation_results")
    validated_by_user = relationship("User", foreign_keys=[validated_by])
    
    def __repr__(self):
        return f"<EvidenceValidationResult(id={self.id}, evidence_id={self.evidence_id}, result='{self.validation_result}')>"


class TesterDecision(CustomPKModel):
    """Tester decisions on evidence submissions"""
    
    __tablename__ = "cycle_report_request_info_tester_decisions"
    
    id = Column(Integer, primary_key=True)
    phase_id = Column(Integer, ForeignKey('workflow_phases.phase_id'), nullable=False)
    evidence_id = Column(Integer, ForeignKey('cycle_report_request_info_testcase_source_evidence.id'), nullable=False)
    test_case_id = Column(Integer, ForeignKey('cycle_report_test_cases.id'), nullable=False)
    
    # Decision details
    decision = Column(tester_decision_enum, nullable=False)
    decision_notes = Column(Text, nullable=True)
    decision_date = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    decided_by = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    
    # Follow-up actions
    requires_resubmission = Column(Boolean, default=False, nullable=False)
    resubmission_deadline = Column(DateTime(timezone=True), nullable=True)
    follow_up_instructions = Column(Text, nullable=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    phase = relationship("app.models.workflow.WorkflowPhase")
    evidence = relationship("TestCaseSourceEvidence", back_populates="tester_decisions")
    test_case = relationship("CycleReportTestCase")
    decided_by_user = relationship("User", foreign_keys=[decided_by])
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('evidence_id', 'decided_by', name='uq_tester_decision_evidence_tester'),
    )
    
    def __repr__(self):
        return f"<TesterDecision(id={self.id}, evidence_id={self.evidence_id}, decision='{self.decision}')>"


# Python enum classes for import
from enum import Enum


class EvidenceType(str, Enum):
    """Evidence type enum for Python usage"""
    DOCUMENT = "document"
    DATA_SOURCE = "data_source"


class EvidenceValidationStatus(str, Enum):
    """Evidence validation status enum for Python usage"""
    PENDING = "pending"
    VALID = "valid"
    INVALID = "invalid"
    REQUIRES_REVIEW = "requires_review"


class ValidationResult(str, Enum):
    """Validation result enum for Python usage"""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"


class TesterDecisionEnum(str, Enum):
    """Tester decision enum for Python usage"""
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUIRES_REVISION = "requires_revision"


# New RFI Query Validation Models

class RFIDataSource(CustomPKModel):
    """Reusable data source configurations for query-based evidence"""
    
    __tablename__ = "cycle_report_rfi_data_sources"
    
    data_source_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    phase_id = Column(Integer, ForeignKey('workflow_phases.phase_id'), nullable=True)
    data_owner_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    source_name = Column(String(255), nullable=False)
    connection_type = Column(String(50), nullable=False)  # postgresql, mysql, oracle, csv, api
    connection_details = Column(JSONB, nullable=False)  # Encrypted connection info
    is_active = Column(Boolean, default=True, nullable=False)
    test_query = Column(Text, nullable=True)
    
    # Validation tracking
    last_validated_at = Column(DateTime(timezone=True), nullable=True)
    validation_status = Column(String(50), nullable=True)  # valid, invalid, pending
    validation_error = Column(Text, nullable=True)
    usage_count = Column(Integer, default=0, nullable=False)
    
    # Audit fields
    created_by = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_by = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    phase = relationship("app.models.workflow.WorkflowPhase")
    data_owner = relationship("User", foreign_keys=[data_owner_id])
    created_by_user = relationship("User", foreign_keys=[created_by])
    updated_by_user = relationship("User", foreign_keys=[updated_by])
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('data_owner_id', 'source_name', name='uq_data_source_name_owner'),
    )
    
    def __repr__(self):
        return f"<RFIDataSource(id='{self.data_source_id}', name='{self.source_name}', type='{self.connection_type}')>"


class RFIQueryValidation(CustomPKModel):
    """Query validation results before evidence submission"""
    
    __tablename__ = "cycle_report_rfi_query_validations"
    
    validation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    test_case_id = Column(Integer, ForeignKey('cycle_report_test_cases.id'), nullable=False)
    data_source_id = Column(UUID(as_uuid=True), ForeignKey('cycle_report_rfi_data_sources.data_source_id'), nullable=False)
    
    # Query details
    query_text = Column(Text, nullable=False)
    query_parameters = Column(JSONB, nullable=True)
    
    # Validation results
    validation_status = Column(String(50), nullable=False)  # success, failed, timeout
    validation_timestamp = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    execution_time_ms = Column(Integer, nullable=True)
    
    # Results
    row_count = Column(Integer, nullable=True)
    column_names = Column(JSONB, nullable=True)  # Array of column names
    sample_rows = Column(JSONB, nullable=True)  # First N rows as preview
    error_message = Column(Text, nullable=True)
    
    # Column validation
    has_primary_keys = Column(Boolean, nullable=True)
    has_target_attribute = Column(Boolean, nullable=True)
    missing_columns = Column(JSONB, nullable=True)  # Array of missing column names
    validation_warnings = Column(JSONB, nullable=True)  # Array of validation warnings
    
    # User tracking
    validated_by = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    
    # Relationships
    test_case = relationship("CycleReportTestCase")
    data_source = relationship("RFIDataSource")
    validated_by_user = relationship("User", foreign_keys=[validated_by])
    
    def __repr__(self):
        return f"<RFIQueryValidation(id='{self.validation_id}', test_case={self.test_case_id}, status='{self.validation_status}')>"


class TestCaseEvidence(CustomPKModel, AuditMixin):
    """Unified evidence table for test cases - combines documents and data sources"""
    
    __tablename__ = "cycle_report_test_cases_evidence"
    
    id = Column(Integer, primary_key=True)
    test_case_id = Column(Integer, ForeignKey('cycle_report_test_cases.id'), nullable=False)
    phase_id = Column(Integer, ForeignKey('workflow_phases.phase_id'), nullable=False)
    cycle_id = Column(Integer, ForeignKey('test_cycles.cycle_id'), nullable=False)
    report_id = Column(Integer, ForeignKey('reports.id'), nullable=False)
    sample_id = Column(String(255), nullable=False)
    
    # Evidence type and version
    evidence_type = Column(String(20), nullable=False)  # 'document' or 'data_source'
    version_number = Column(Integer, default=1, nullable=False)
    is_current = Column(Boolean, default=True, nullable=False)
    parent_evidence_id = Column(Integer, ForeignKey('cycle_report_test_cases_evidence.id'), nullable=True)
    
    # Common submission fields
    data_owner_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    submitted_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    submission_notes = Column(Text, nullable=True)
    
    # Submission tracking (from document submissions)
    submission_number = Column(Integer, default=1, nullable=False)
    is_revision = Column(Boolean, default=False, nullable=False)
    revision_requested_by = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    revision_requested_at = Column(DateTime(timezone=True), nullable=True)
    revision_reason = Column(Text, nullable=True)
    revision_deadline = Column(DateTime(timezone=True), nullable=True)
    
    # Validation and review
    validation_status = Column(String(50), default='pending', nullable=False)
    validation_notes = Column(Text, nullable=True)
    validated_by = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    validated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Tester decision fields
    tester_decision = Column(String(50), nullable=True)  # 'approved', 'rejected', 'requires_revision'
    tester_notes = Column(Text, nullable=True)
    decided_by = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    decided_at = Column(DateTime(timezone=True), nullable=True)
    requires_resubmission = Column(Boolean, default=False, nullable=False)
    resubmission_deadline = Column(DateTime(timezone=True), nullable=True)
    
    # Document specific fields (nullable)
    original_filename = Column(String(255), nullable=True)
    stored_filename = Column(String(255), nullable=True)
    file_path = Column(String(500), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    file_hash = Column(String(64), nullable=True)
    mime_type = Column(String(100), nullable=True)
    document_type = Column(document_type_enum, nullable=True)  # For document classification
    
    # Data source specific fields (nullable)
    rfi_data_source_id = Column(UUID(as_uuid=True), ForeignKey('cycle_report_rfi_data_sources.data_source_id'), nullable=True)
    planning_data_source_id = Column(Integer, ForeignKey('cycle_report_planning_data_sources.id'), nullable=True)
    query_text = Column(Text, nullable=True)
    query_parameters = Column(JSONB, nullable=True)
    query_validation_id = Column(UUID(as_uuid=True), ForeignKey('cycle_report_rfi_query_validations.validation_id'), nullable=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    updated_by = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    
    # Relationships
    test_case = relationship("CycleReportTestCase")
    phase = relationship("app.models.workflow.WorkflowPhase")
    cycle = relationship("TestCycle")
    report = relationship("Report")
    data_owner = relationship("User", foreign_keys=[data_owner_id])
    # submitted_by_user = relationship("User", foreign_keys=[data_owner_id])  # Using data_owner relationship instead
    validated_by_user = relationship("User", foreign_keys=[validated_by])
    decided_by_user = relationship("User", foreign_keys=[decided_by])
    revision_requester = relationship("User", foreign_keys=[revision_requested_by])
    created_by_user = relationship("User", foreign_keys=[created_by])
    updated_by_user = relationship("User", foreign_keys=[updated_by])
    parent_evidence = relationship("TestCaseEvidence", remote_side=[id], foreign_keys=[parent_evidence_id])
    rfi_data_source = relationship("RFIDataSource", foreign_keys=[rfi_data_source_id])
    query_validation = relationship("RFIQueryValidation", foreign_keys=[query_validation_id])
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('test_case_id', 'version_number', name='uq_test_case_version'),
        CheckConstraint(
            "(evidence_type = 'document' AND original_filename IS NOT NULL AND file_path IS NOT NULL) OR "
            "(evidence_type = 'data_source' AND query_text IS NOT NULL)",
            name='check_evidence_type_fields'
        ),
    )
    
    def __repr__(self):
        return f"<TestCaseEvidence(id={self.id}, test_case_id={self.test_case_id}, evidence_type='{self.evidence_type}', version={self.version_number})>" 


# Backward compatibility alias
RFIEvidenceLegacy = TestCaseEvidence