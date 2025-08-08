"""
Observation Management Phase database models
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, JSON, ForeignKey, Enum as SQLEnum, func, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import enum
import uuid

from app.models.base import BaseModel, CustomPKModel
from app.models.audit_mixin import AuditMixin


class ObservationTypeEnum(enum.Enum):
    """Observation type enumeration"""
    DATA_QUALITY = "Data Quality"
    PROCESS_CONTROL = "Process Control"
    REGULATORY_COMPLIANCE = "Regulatory Compliance"
    SYSTEM_CONTROL = "System Control"
    DOCUMENTATION = "Documentation"
    CALCULATION_ERROR = "Calculation Error"
    TIMING_ISSUE = "Timing Issue"
    ACCESS_CONTROL = "Access Control"


class ObservationSeverityEnum(enum.Enum):
    """Observation severity enumeration"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFORMATIONAL = "INFORMATIONAL"


class ObservationStatusEnum(enum.Enum):
    """Observation status enumeration"""
    DETECTED = "Detected"
    SUBMITTED = "Submitted"
    UNDER_REVIEW = "Under Review"
    CONFIRMED = "Confirmed"
    DISPUTED = "Disputed"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    IN_REMEDIATION = "In Remediation"
    RESOLVED = "Resolved"
    CLOSED = "Closed"


class VersionStatusEnum(enum.Enum):
    """Version status enumeration"""
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SUPERSEDED = "SUPERSEDED"


class ImpactCategoryEnum(enum.Enum):
    """Impact category enumeration"""
    FINANCIAL = "Financial"
    REGULATORY = "Regulatory"
    OPERATIONAL = "Operational"
    REPUTATIONAL = "Reputational"
    STRATEGIC = "Strategic"
    CUSTOMER = "Customer"


class ResolutionStatusEnum(enum.Enum):
    """Resolution status enumeration"""
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    PENDING_VALIDATION = "Pending Validation"
    COMPLETED = "Completed"
    FAILED = "Failed"
    CANCELLED = "Cancelled"


# DEPRECATED: Using unified WorkflowPhase instead
# class ObservationManagementPhase(CustomPKModel, AuditMixin):
#     """Observation Management phase tracking"""
#     __tablename__ = "observation_management_phases"
#     
#     phase_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
#     cycle_id = Column(Integer, ForeignKey('test_cycles.cycle_id'), nullable=False)
#     report_id = Column(Integer, ForeignKey('reports.id'), nullable=False)
#     phase_id = Column(Integer, ForeignKey('workflow_phases.phase_id'), nullable=False)
#     phase_status = Column(String, nullable=False, default="In Progress")
#     
#     # Phase timing
#     planned_start_date = Column(DateTime)
#     planned_end_date = Column(DateTime)
#     observation_deadline = Column(DateTime, nullable=False)
#     started_at = Column(DateTime, default=datetime.utcnow)
#     completed_at = Column(DateTime)
#     
#     # Configuration
#     observation_strategy = Column(Text)
#     detection_criteria = Column(JSON)  # Criteria for automatic detection
#     approval_threshold = Column(Float, default=0.7)  # Threshold for automatic approval
#     instructions = Column(Text)
#     notes = Column(Text)
#     
#     # User assignments
#     started_by = Column(Integer, ForeignKey('users.user_id'))
#     completed_by = Column(Integer, ForeignKey('users.user_id'))
#     assigned_testers = Column(JSON)  # List of tester IDs
#     
#     # Statistics
#     total_observations = Column(Integer, default=0)
#     auto_detected_observations = Column(Integer, default=0)
#     manual_observations = Column(Integer, default=0)
#     approved_observations = Column(Integer, default=0)
#     rejected_observations = Column(Integer, default=0)
#     
#     # Relationships
#     phase = relationship("app.models.workflow.WorkflowPhase", back_populates="observations")
#     cycle = relationship("TestCycle", back_populates="observation_management_phases")
#     report = relationship("Report", back_populates="observation_management_phases")
#     starter = relationship("User", foreign_keys=[started_by])
#     completer = relationship("User", foreign_keys=[completed_by])
#     observations = relationship("ObservationRecord", back_populates="phase")


class ObservationRecord(CustomPKModel, AuditMixin):
    """Individual observation record"""
    __tablename__ = "cycle_report_observation_mgmt_observation_records"
    
    observation_id = Column(Integer, primary_key=True)
    phase_id = Column(Integer, ForeignKey('workflow_phases.phase_id'), nullable=False)
    
    # Observation identification
    observation_title = Column(String, nullable=False)
    observation_description = Column(Text, nullable=False)
    observation_type = Column(SQLEnum(ObservationTypeEnum), nullable=False)
    severity = Column(SQLEnum(ObservationSeverityEnum), nullable=False)
    status = Column(SQLEnum(ObservationStatusEnum), default=ObservationStatusEnum.DETECTED)
    
    # Source information
    source_test_execution_id = Column(Integer, ForeignKey('cycle_report_test_execution_results.id'), nullable=True)  # DEPRECATED: Use test_execution_links
    # source_sample_record_id removed - derive from test cases instead
    source_attribute_id = Column(Integer, ForeignKey("cycle_report_planning_attributes.id"), nullable=False)
    detection_method = Column(String)  # Auto-detected, Manual, Review-based
    detection_confidence = Column(Float)  # Confidence score for auto-detected
    
    # Impact assessment
    impact_description = Column(Text)
    impact_categories = Column(JSON)  # List of impact categories
    financial_impact_estimate = Column(Float)
    regulatory_risk_level = Column(String)
    affected_processes = Column(JSON)  # List of affected processes
    affected_systems = Column(JSON)  # List of affected systems
    
    # Evidence and documentation
    evidence_documents = Column(JSON)  # List of document references
    supporting_data = Column(JSON)  # Supporting data and analysis
    screenshots = Column(JSON)  # Screenshot references
    related_observations = Column(JSON)  # Related observation IDs
    
    # Assignment and tracking
    detected_by = Column(Integer, ForeignKey('users.user_id'))
    assigned_to = Column(Integer, ForeignKey('users.user_id'))
    detected_at = Column(DateTime, default=datetime.utcnow)
    assigned_at = Column(DateTime)
    
    # Auto-detection metadata
    auto_detection_rules = Column(JSON)  # Rules that triggered detection
    auto_detection_score = Column(Float)
    manual_validation_required = Column(Boolean, default=False)
    
    # Approval fields (similar to scoping)
    tester_decision = Column(String, nullable=True)  # Approved, Rejected, null
    tester_comments = Column(Text, nullable=True)
    tester_decision_by_id = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    tester_decision_at = Column(DateTime, nullable=True)
    
    report_owner_decision = Column(String, nullable=True)  # Approved, Rejected, null
    report_owner_comments = Column(Text, nullable=True)
    report_owner_decision_by_id = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    report_owner_decision_at = Column(DateTime, nullable=True)
    
    # Overall approval status
    approval_status = Column(String, nullable=True, default="Pending Review")
    
    # Relationships
    phase = relationship("app.models.workflow.WorkflowPhase", back_populates="observations")
    source_test_execution = relationship("app.models.test_execution.TestExecution", foreign_keys=[source_test_execution_id])  # DEPRECATED
    source_attribute = relationship("ReportAttribute", foreign_keys=[source_attribute_id])
    detector = relationship("User", foreign_keys=[detected_by])
    assignee = relationship("User", foreign_keys=[assigned_to])
    tester_decision_by = relationship("User", foreign_keys=[tester_decision_by_id])
    report_owner_decision_by = relationship("User", foreign_keys=[report_owner_decision_by_id])
    impact_assessments = relationship("ObservationImpactAssessment", back_populates="observation")
    # approvals = relationship("ObservationApproval", back_populates="observation")  # Removed - approvals now in ObservationRecord
    resolutions = relationship("ObservationResolution", back_populates="observation")
    
    # New relationship to test executions through junction table
    test_execution_links = relationship("ObservationTestExecutionLink", back_populates="observation", cascade="all, delete-orphan")
    
    # Properties to access cycle_id and report_id through phase
    @property
    def cycle_id(self):
        return self.phase.cycle_id if self.phase else None
    
    @property
    def report_id(self):
        return self.phase.report_id if self.phase else None


class ObservationVersionRecord(CustomPKModel, AuditMixin):
    """
    Observation version model following the scoping versioning pattern.
    Note: Renamed from ObservationVersion to ObservationVersionRecord to avoid duplicate mapper conflicts.
    
    This model manages observation versions providing:
    - Version management with draft → pending → approved/rejected → superseded lifecycle
    - Temporal workflow integration
    - Summary statistics and progress tracking
    - Submission and approval workflow
    """
    
    __tablename__ = "cycle_report_observation_versions"
    
    # Primary key
    version_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Phase context
    phase_id = Column(Integer, ForeignKey('workflow_phases.phase_id'), nullable=False)
    workflow_activity_id = Column(Integer, ForeignKey('workflow_activities.activity_id'), nullable=True)
    
    # Version Management
    version_number = Column(Integer, nullable=False)
    version_status = Column(SQLEnum(VersionStatusEnum), nullable=False)
    parent_version_id = Column(UUID(as_uuid=True), ForeignKey('cycle_report_observation_versions.version_id'), nullable=True)
    
    # Temporal Workflow Context
    workflow_execution_id = Column(String(255), nullable=True)
    workflow_run_id = Column(String(255), nullable=True)
    activity_name = Column(String(100), nullable=True)
    
    # Observation Summary Statistics
    total_observations = Column(Integer, nullable=False, default=0)
    high_severity_count = Column(Integer, nullable=False, default=0)
    medium_severity_count = Column(Integer, nullable=False, default=0)
    low_severity_count = Column(Integer, nullable=False, default=0)
    approved_count = Column(Integer, nullable=False, default=0)
    rejected_count = Column(Integer, nullable=False, default=0)
    pending_count = Column(Integer, nullable=False, default=0)
    
    # Submission and Approval Workflow
    submission_notes = Column(Text, nullable=True)
    submitted_by_id = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    
    approval_notes = Column(Text, nullable=True)
    approved_by_id = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    
    rejection_reason = Column(Text, nullable=True)
    requested_changes = Column(JSONB, nullable=True)
    
    # Report Owner Feedback (similar to scoping)
    report_owner_feedback = Column(Text, nullable=True)
    report_owner_decision = Column(String, nullable=True)  # Approved, Rejected
    report_owner_decision_by_id = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    report_owner_decision_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    phase = relationship("app.models.workflow.WorkflowPhase", back_populates="observation_versions")
    workflow_activity = relationship("app.models.workflow_activity.WorkflowActivity")
    parent_version = relationship("ObservationVersionRecord", remote_side=[version_id])
    child_versions = relationship("ObservationVersionRecord", back_populates="parent_version")
    submitter = relationship("app.models.user.User", foreign_keys=[submitted_by_id])
    approver = relationship("app.models.user.User", foreign_keys=[approved_by_id])
    report_owner_decision_by = relationship("app.models.user.User", foreign_keys=[report_owner_decision_by_id])
    
    # Observation version items
    version_items = relationship("ObservationVersionItem", back_populates="version", cascade="all, delete-orphan")


class ObservationVersionItem(CustomPKModel, AuditMixin):
    """
    Individual observation items within a version.
    Links observations to specific versions.
    """
    
    __tablename__ = "cycle_report_observation_version_items"
    
    # Primary key
    item_id = Column(Integer, primary_key=True)
    
    # Foreign keys
    version_id = Column(UUID(as_uuid=True), ForeignKey('cycle_report_observation_versions.version_id'), nullable=False)
    observation_id = Column(Integer, ForeignKey('cycle_report_observation_mgmt_observation_records.observation_id'), nullable=False)
    
    # Item-specific versioning data
    included_in_version = Column(Boolean, default=True, nullable=False)
    version_notes = Column(Text, nullable=True)
    
    # Relationships
    version = relationship("ObservationVersionRecord", back_populates="version_items")
    observation = relationship("ObservationRecord")


class ObservationImpactAssessment(CustomPKModel, AuditMixin):
    """Detailed impact assessment for observations"""
    __tablename__ = "cycle_report_observation_mgmt_impact_assessments"
    
    assessment_id = Column(Integer, primary_key=True)
    observation_id = Column(Integer, ForeignKey("cycle_report_observation_mgmt_observation_records.observation_id"), nullable=False)
    
    # Assessment details
    impact_category = Column(SQLEnum(ImpactCategoryEnum), nullable=False)
    impact_severity = Column(String, nullable=False)
    impact_likelihood = Column(String, nullable=False)
    impact_score = Column(Float, nullable=False)  # Calculated risk score
    
    # Financial impact
    financial_impact_min = Column(Float)
    financial_impact_max = Column(Float)
    financial_impact_currency = Column(String, default="USD")
    
    # Regulatory impact
    regulatory_requirements_affected = Column(JSON)
    regulatory_deadlines = Column(JSON)
    potential_penalties = Column(Float)
    
    # Operational impact
    process_disruption_level = Column(String)
    system_availability_impact = Column(String)
    resource_requirements = Column(JSON)
    
    # Timeline impact
    resolution_time_estimate = Column(Integer)  # Days
    business_disruption_duration = Column(Integer)  # Hours
    
    # Assessment metadata
    assessment_method = Column(String)
    assessment_confidence = Column(Float)
    assessment_rationale = Column(Text)
    assessment_assumptions = Column(JSON)
    
    # User tracking
    assessed_by = Column(Integer, ForeignKey('users.user_id'))
    assessed_at = Column(DateTime, default=datetime.utcnow)
    reviewed_by = Column(Integer, ForeignKey('users.user_id'))
    reviewed_at = Column(DateTime)
    
    # Relationships
    observation = relationship("ObservationRecord", back_populates="impact_assessments")
    assessor = relationship("User", foreign_keys=[assessed_by])
    reviewer = relationship("User", foreign_keys=[reviewed_by])


# ObservationApproval class removed - approvals are now handled directly in ObservationRecord
# with tester_decision, report_owner_decision fields similar to scoping phase


class ObservationResolution(CustomPKModel, AuditMixin):
    """Observation resolution tracking"""
    __tablename__ = "cycle_report_observation_mgmt_resolutions"
    
    resolution_id = Column(Integer, primary_key=True)
    observation_id = Column(Integer, ForeignKey("cycle_report_observation_mgmt_observation_records.observation_id"), nullable=False)
    
    # Resolution plan
    resolution_strategy = Column(String, nullable=False)
    resolution_description = Column(Text)
    resolution_steps = Column(JSON)  # List of resolution steps
    success_criteria = Column(JSON)
    validation_requirements = Column(JSON)
    
    # Resolution status
    resolution_status = Column(SQLEnum(ResolutionStatusEnum), default=ResolutionStatusEnum.NOT_STARTED)
    progress_percentage = Column(Float, default=0.0)
    current_step = Column(String)
    
    # Timeline
    planned_start_date = Column(DateTime)
    planned_completion_date = Column(DateTime)
    actual_start_date = Column(DateTime)
    actual_completion_date = Column(DateTime)
    
    # Resource allocation
    assigned_resources = Column(JSON)  # List of assigned users/teams
    estimated_effort_hours = Column(Integer)
    actual_effort_hours = Column(Integer)
    budget_allocated = Column(Float)
    budget_spent = Column(Float)
    
    # Implementation details
    implemented_controls = Column(JSON)
    process_changes = Column(JSON)
    system_changes = Column(JSON)
    documentation_updates = Column(JSON)
    training_requirements = Column(JSON)
    
    # Validation and testing
    validation_tests_planned = Column(JSON)
    validation_tests_completed = Column(JSON)
    validation_results = Column(JSON)
    effectiveness_metrics = Column(JSON)
    
    # User tracking
    resolution_owner = Column(Integer, ForeignKey('users.user_id'))
    created_by = Column(Integer, ForeignKey('users.user_id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    validated_by = Column(Integer, ForeignKey('users.user_id'))
    validated_at = Column(DateTime)
    
    # Relationships
    observation = relationship("ObservationRecord", back_populates="resolutions")
    owner = relationship("User", foreign_keys=[resolution_owner])
    creator = relationship("User", foreign_keys=[created_by])
    validator = relationship("User", foreign_keys=[validated_by])


class ObservationManagementAuditLog(CustomPKModel, AuditMixin):
    """Audit log for observation management activities"""
    __tablename__ = "observation_management_audit_logs"
    
    log_id = Column(Integer, primary_key=True)
    cycle_id = Column(Integer, ForeignKey('test_cycles.cycle_id'), nullable=False)
    report_id = Column(Integer, ForeignKey('reports.id'), nullable=False)
    phase_id = Column(Integer, ForeignKey('workflow_phases.phase_id'), nullable=False)
    observation_id = Column(Integer, ForeignKey("cycle_report_observation_mgmt_observation_records.observation_id"))
    
    # Action details
    action = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    entity_id = Column(String)
    
    # Change tracking
    old_values = Column(JSON)
    new_values = Column(JSON)
    changes_summary = Column(Text)
    
    # User context
    performed_by = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    performed_at = Column(DateTime, default=datetime.utcnow)
    user_role = Column(String)
    
    # Request context
    ip_address = Column(String)
    user_agent = Column(String)
    session_id = Column(String)
    
    # Additional metadata
    notes = Column(Text)
    execution_time_ms = Column(Integer)
    business_justification = Column(Text)
    source_test_execution_id = Column(Integer, ForeignKey('cycle_report_test_execution_results.id'), nullable=True)
    
    # Relationships
    cycle = relationship("TestCycle")
    report = relationship("Report")
    phase = relationship("app.models.workflow.WorkflowPhase")
    observation = relationship("ObservationRecord")
    user = relationship("User", foreign_keys=[performed_by])
    source_test_execution = relationship("app.models.test_execution.TestExecution", foreign_keys=[source_test_execution_id])


class ObservationTestExecutionLink(BaseModel):
    """Junction table for observation to test execution many-to-many relationship"""
    __tablename__ = "cycle_report_observation_mgmt_test_executions"
    
    id = Column(Integer, primary_key=True)
    observation_id = Column(Integer, ForeignKey("cycle_report_observation_mgmt_observation_records.observation_id", ondelete="CASCADE"), nullable=False)
    test_execution_id = Column(Integer, ForeignKey("cycle_report_test_execution_results.id", ondelete="CASCADE"), nullable=False)
    is_primary = Column(Boolean, default=False, nullable=False)
    linked_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    linked_by_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    
    # Relationships
    observation = relationship("ObservationRecord", back_populates="test_execution_links")
    test_execution = relationship("app.models.test_execution.TestExecution")
    linked_by = relationship("User", foreign_keys=[linked_by_id])
    
    __table_args__ = (
        UniqueConstraint('observation_id', 'test_execution_id', name='uq_obs_test_exec'),
        Index('idx_obs_test_exec_observation', 'observation_id'),
        Index('idx_obs_test_exec_test_execution', 'test_execution_id'),
    ) 