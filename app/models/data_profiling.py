"""
Data Profiling Models - Unified Architecture

This module contains the new unified data profiling models that replace the 23+ legacy tables,
implementing the same versioning pattern as sample selection and scoping.

Key Features:
- Unified 2-table architecture (versions + rules)
- Dual decision model (tester + report owner)
- Background job execution tracking
- LLM-driven rule generation
- Version lifecycle management
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy import Column, String, Integer, BigInteger, Text, Boolean, ForeignKey, DateTime, Float, DECIMAL, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM as PgEnum
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
from sqlalchemy.ext.hybrid import hybrid_property
from enum import Enum
import uuid

from app.models.base import CustomPKModel
from app.models.audit_mixin import AuditMixin

# Import existing relationships to avoid conflicts
try:
    from app.models.report_attribute import ReportAttribute
except ImportError:
    # Define placeholder if not available
    class PlanningAttribute:
        pass


# Enums for data profiling system
class VersionStatus(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class ProfilingRuleType(str, Enum):
    COMPLETENESS = "completeness"
    VALIDITY = "validity"
    ACCURACY = "accuracy"
    CONSISTENCY = "consistency"
    UNIQUENESS = "uniqueness"
    FORMAT = "format"


class ProfilingRuleStatus(str, Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Decision(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUEST_CHANGES = "request_changes"


class DataSourceType(str, Enum):
    FILE_UPLOAD = "file_upload"
    DATABASE_SOURCE = "database_source"
    DATABASE_DIRECT = "database_direct"
    API = "api"
    STREAMING = "streaming"


class ProfilingMode(str, Enum):
    """Profiling execution mode"""
    FULL_SCAN = "full_scan"
    SAMPLE_BASED = "sample_based"
    INCREMENTAL = "incremental"
    STREAMING = "streaming"


class ProfilingStatus(str, Enum):
    """Status of profiling job execution"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# PostgreSQL enum types (match the migration)
version_status_enum = PgEnum(
    'draft', 'pending_approval', 'approved', 'rejected', 'superseded',
    name='version_status_enum'
)

rule_type_enum = PgEnum(
    'completeness', 'validity', 'accuracy', 'consistency', 'uniqueness', 'format',
    name='rule_type_enum'
)

severity_enum = PgEnum(
    'low', 'medium', 'high', 'critical',
    name='severity_enum'
)

decision_enum = PgEnum(
    'approved', 'rejected', 'request_changes',
    name='decision_enum'
)

rule_status_enum = PgEnum(
    'pending', 'submitted', 'approved', 'rejected',
    name='rule_status_enum'
)

data_source_type_enum = PgEnum(
    'file_upload', 'database_source',
    name='data_source_type_enum'
)


class DataProfilingRuleVersion(CustomPKModel, AuditMixin):
    """
    Data Profiling Rule Version model following the exact same pattern as sample selection/scoping.
    
    This model manages data profiling rules at the version level, providing:
    - Version management with draft → pending → approved/rejected → superseded lifecycle
    - Temporal workflow integration
    - Summary statistics and progress tracking
    - Submission and approval workflow
    - Data source reference from planning phase
    """
    
    __tablename__ = "cycle_report_data_profiling_rule_versions"
    
    # Primary key
    version_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Phase Integration (only phase_id needed - follows new pattern)
    phase_id = Column(Integer, ForeignKey('workflow_phases.phase_id'), nullable=False)
    workflow_activity_id = Column(Integer, ForeignKey('workflow_activities.activity_id'), nullable=True)
    
    # Version Management (exact same as sample selection/scoping)
    version_number = Column(Integer, nullable=False)
    version_status = Column(version_status_enum, nullable=False, server_default='draft')
    parent_version_id = Column(UUID(as_uuid=True), ForeignKey('cycle_report_data_profiling_rule_versions.version_id'), nullable=True)
    
    # Temporal Workflow Context
    workflow_execution_id = Column(String(255), nullable=True)
    workflow_run_id = Column(String(255), nullable=True)
    
    # Rule Set Summary
    total_rules = Column(Integer, nullable=False, server_default='0')
    approved_rules = Column(Integer, nullable=False, server_default='0')
    rejected_rules = Column(Integer, nullable=False, server_default='0')
    
    # Data Source Reference (from planning phase)
    data_source_type = Column(data_source_type_enum, nullable=True)
    planning_data_source_id = Column(Integer, nullable=True)  # References planning phase data source
    source_table_name = Column(String(255), nullable=True)
    source_file_path = Column(String(500), nullable=True)
    
    # Execution Summary
    total_records_processed = Column(Integer, nullable=True)
    overall_quality_score = Column(DECIMAL(5, 2), nullable=True)
    execution_job_id = Column(String(255), nullable=True)  # Background job ID
    
    # Generation tracking fields (missing from model but exist in DB)
    generation_job_id = Column(String(255), nullable=True)  # Background job ID for rule generation
    generation_status = Column(String(50), nullable=True)  # Status of rule generation: queued, running, completed, failed
    
    # Approval Workflow
    submitted_by_id = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    approved_by_id = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # Relationships - using string references to avoid circular imports
    rules = relationship("ProfilingRule", back_populates="version", cascade="all, delete-orphan")
    phase = relationship("WorkflowPhase", foreign_keys=[phase_id])
    parent_version = relationship("DataProfilingRuleVersion", remote_side=[version_id])
    child_versions = relationship("DataProfilingRuleVersion", back_populates="parent_version")
    
    # User relationships (created_by and updated_by provided by AuditMixin)
    submitted_by = relationship("User", foreign_keys=[submitted_by_id])
    approved_by = relationship("User", foreign_keys=[approved_by_id])
    
    @hybrid_property
    def is_latest(self) -> bool:
        """Check if this is the latest version for the phase"""
        return self.version_status in [VersionStatus.APPROVED, VersionStatus.PENDING_APPROVAL]
    
    @hybrid_property
    def completion_percentage(self) -> float:
        """Calculate rule completion percentage"""
        if self.total_rules == 0:
            return 0.0
        return (self.approved_rules + self.rejected_rules) / self.total_rules * 100
    
    @hybrid_property
    def approval_percentage(self) -> float:
        """Calculate rule approval percentage"""
        if self.total_rules == 0:
            return 0.0
        return self.approved_rules / self.total_rules * 100
    
    @hybrid_property
    def can_be_edited(self) -> bool:
        """Check if version can be edited (only draft versions are editable)"""
        return self.version_status == VersionStatus.DRAFT or self.version_status == 'draft'
    
    def __repr__(self) -> str:
        return f"<DataProfilingRuleVersion(version_id={self.version_id}, phase_id={self.phase_id}, version_number={self.version_number}, status={self.version_status})>"


class ProfilingRule(CustomPKModel, AuditMixin):
    """
    Individual Data Profiling Rule model (NO execution results stored here).
    
    This model stores rule definitions and decisions, following the dual decision model
    used in scoping (tester + report owner decisions).
    
    Execution results are tracked via the universal background job system.
    """
    
    __tablename__ = "cycle_report_data_profiling_rules"
    
    # Primary key
    rule_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Version Reference
    version_id = Column(UUID(as_uuid=True), ForeignKey('cycle_report_data_profiling_rule_versions.version_id', ondelete='CASCADE'), nullable=False)
    
    # Phase Integration
    phase_id = Column(Integer, ForeignKey('workflow_phases.phase_id'), nullable=False)
    
    # Attribute Reference
    attribute_id = Column(Integer, ForeignKey("cycle_report_planning_attributes.id"), nullable=False)
    attribute_name = Column(String(255), nullable=False)
    
    # Rule Definition (NO execution results here)
    rule_name = Column(String(255), nullable=False)
    rule_type = Column(rule_type_enum, nullable=False)
    rule_description = Column(Text, nullable=True)
    rule_code = Column(Text, nullable=False)
    rule_parameters = Column(JSONB, nullable=True)
    
    # LLM Metadata
    llm_provider = Column(String(50), nullable=True)
    llm_rationale = Column(Text, nullable=True)
    llm_confidence_score = Column(DECIMAL(5, 2), nullable=True)
    regulatory_reference = Column(Text, nullable=True)
    
    # Rule Configuration
    is_executable = Column(Boolean, nullable=False, server_default='true')
    execution_order = Column(Integer, nullable=False, server_default='0')
    severity = Column(severity_enum, nullable=False, server_default='medium')
    
    # Dual Decision Model (same as scoping)
    tester_decision = Column(decision_enum, nullable=True)
    tester_decided_by = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    tester_decided_at = Column(DateTime(timezone=True), nullable=True)
    tester_notes = Column(Text, nullable=True)
    
    report_owner_decision = Column(decision_enum, nullable=True)
    report_owner_decided_by = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    report_owner_decided_at = Column(DateTime(timezone=True), nullable=True)
    report_owner_notes = Column(Text, nullable=True)
    
    # Status
    status = Column(rule_status_enum, nullable=False, server_default='pending')
    
    # Calculated status column (automatically updated by database trigger)
    calculated_status = Column(String(20), nullable=False, default='pending')
    
    # Relationships - using string references to avoid circular imports
    version = relationship("DataProfilingRuleVersion", back_populates="rules")
    phase = relationship("WorkflowPhase", foreign_keys=[phase_id])
    
    # User relationships (created_by and updated_by provided by AuditMixin)
    tester_decided_by_user = relationship("User", foreign_keys=[tester_decided_by])
    report_owner_decided_by_user = relationship("User", foreign_keys=[report_owner_decided_by])
    
    @hybrid_property
    def is_approved(self) -> bool:
        """Check if rule is approved by both tester and report owner"""
        return (self.tester_decision == Decision.APPROVED and 
                self.report_owner_decision == Decision.APPROVED)
    
    @hybrid_property
    def is_rejected(self) -> bool:
        """Check if rule is rejected by either tester or report owner"""
        return (self.tester_decision == Decision.REJECTED or 
                self.report_owner_decision == Decision.REJECTED)
    
    @hybrid_property
    def final_decision(self) -> Optional[str]:
        """Get the final decision based on both tester and report owner decisions"""
        if self.is_approved:
            return "approved"
        elif self.is_rejected:
            return "rejected"
        elif (self.tester_decision == Decision.REQUEST_CHANGES or 
              self.report_owner_decision == Decision.REQUEST_CHANGES):
            return "request_changes"
        else:
            return "pending"
    
    
    @validates('rule_type')
    def validate_rule_type(self, key, rule_type):
        """Validate that rule_type is one of the supported types"""
        if rule_type not in [rt.value for rt in ProfilingRuleType]:
            raise ValueError(f"Invalid rule_type: {rule_type}")
        return rule_type
    
    @validates('severity')
    def validate_severity(self, key, severity):
        """Validate that severity is one of the supported levels"""
        if severity not in [s.value for s in Severity]:
            raise ValueError(f"Invalid severity: {severity}")
        return severity
    
    def __repr__(self) -> str:
        return f"<ProfilingRule(rule_id={self.rule_id}, version_id={self.version_id}, attribute_id={self.attribute_id}, rule_name={self.rule_name})>"


# Upload tracking model for data profiling files
class DataProfilingUpload(CustomPKModel, AuditMixin):
    """Tracks data profiling file uploads"""
    
    __tablename__ = "cycle_report_data_profiling_uploads"
    
    id = Column(Integer, primary_key=True, index=True)
    phase_id = Column(Integer, ForeignKey('workflow_phases.phase_id'), nullable=False)
    
    # File details
    file_name = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)
    file_size = Column(Integer, nullable=True)
    upload_status = Column(String(50), nullable=True, server_default='pending')
    
    # Relationships
    workflow_phase = relationship("WorkflowPhase", foreign_keys=[phase_id])
    
    # Hybrid properties to access cycle_id and report_id through phase relationship
    @hybrid_property
    def cycle_id(self):
        """Get cycle_id from phase relationship for UI compatibility"""
        return self.workflow_phase.cycle_id if self.workflow_phase else None
    
    @hybrid_property
    def report_id(self):
        """Get report_id from phase relationship for UI compatibility"""
        return self.workflow_phase.report_id if self.workflow_phase else None
    
    @hybrid_property
    def cycle(self):
        """Get test cycle through phase relationship"""
        return self.workflow_phase.cycle if self.workflow_phase else None
    
    @hybrid_property
    def report(self):
        """Get report through phase relationship"""
        return self.workflow_phase.report if self.workflow_phase else None
    
    def __repr__(self):
        return f"<DataProfilingUpload(id={self.id}, phase_id={self.phase_id}, file_name={self.file_name})>"


# Advanced Profiling Configuration Models
class DataProfilingConfiguration(CustomPKModel, AuditMixin):
    """Configuration for advanced data profiling execution"""
    __tablename__ = "cycle_report_data_profiling_configurations"
    
    id = Column(Integer, primary_key=True)
    cycle_id = Column(Integer, ForeignKey("test_cycles.cycle_id"), nullable=False)
    report_id = Column(Integer, ForeignKey("reports.id"), nullable=False)
    phase_id = Column(Integer, ForeignKey('workflow_phases.phase_id'), nullable=False)
    
    # Configuration details
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    source_type = Column(String(50), nullable=False, default="file_upload")  # file_upload, database_direct, api, streaming
    profiling_mode = Column(String(50), nullable=False, default="full_scan")  # full_scan, sample_based, incremental, streaming
    
    # Data source configuration
    data_source_id = Column(Integer, ForeignKey("cycle_report_planning_data_sources.id"), nullable=True)
    file_upload_id = Column(Integer, ForeignKey("cycle_report_data_profiling_uploads.id"), nullable=True)
    
    # Sampling configuration
    use_timeframe = Column(Boolean, default=False)
    timeframe_start = Column(DateTime, nullable=True)
    timeframe_end = Column(DateTime, nullable=True)
    timeframe_column = Column(String(255), nullable=True)
    sample_size = Column(Integer, nullable=True)
    sample_percentage = Column(Float, nullable=True)
    sample_method = Column(String(50), default="random")
    
    # Performance configuration
    partition_column = Column(String(255), nullable=True)
    partition_count = Column(Integer, nullable=True)
    max_memory_mb = Column(Integer, nullable=True)
    
    # Query configuration
    custom_query = Column(Text, nullable=True)
    table_name = Column(String(255), nullable=True)
    schema_name = Column(String(255), nullable=True)
    where_clause = Column(Text, nullable=True)
    exclude_columns = Column(JSONB, nullable=True)  # Array of column names
    include_columns = Column(JSONB, nullable=True)  # Array of column names
    
    # Profiling options
    profile_relationships = Column(Boolean, default=False)
    profile_distributions = Column(Boolean, default=True)
    profile_patterns = Column(Boolean, default=True)
    detect_anomalies = Column(Boolean, default=True)
    
    # Scheduling
    is_scheduled = Column(Boolean, default=False)
    schedule_cron = Column(String(100), nullable=True)
    
    # Relationships
    workflow_phase = relationship("WorkflowPhase", foreign_keys=[phase_id])
    data_source = relationship("CycleReportDataSource", foreign_keys=[data_source_id])
    file_upload = relationship("DataProfilingUpload", foreign_keys=[file_upload_id])
    
    def __repr__(self):
        return f"<DataProfilingConfiguration(id={self.id}, name={self.name}, source_type={self.source_type})>"


class DataProfilingJob(CustomPKModel, AuditMixin):
    """Execution job for data profiling"""
    __tablename__ = "cycle_report_data_profiling_jobs"
    
    id = Column(Integer, primary_key=True)
    configuration_id = Column(Integer, ForeignKey("cycle_report_data_profiling_configurations.id"), nullable=False)
    job_id = Column(String(255), nullable=False, unique=True)  # Background job ID
    
    # Job status
    status = Column(String(50), nullable=False, default="pending")  # pending, queued, running, completed, failed, cancelled
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    # Progress tracking
    total_records = Column(BigInteger, nullable=True)
    records_processed = Column(BigInteger, nullable=True)
    records_failed = Column(BigInteger, nullable=True)
    processing_rate = Column(Float, nullable=True)  # records per second
    
    # Performance metrics
    memory_peak_mb = Column(Integer, nullable=True)
    cpu_peak_percent = Column(Float, nullable=True)
    
    # Results summary
    anomalies_detected = Column(Integer, default=0)
    data_quality_score = Column(Float, nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Relationships
    configuration = relationship("DataProfilingConfiguration", foreign_keys=[configuration_id])
    
    def __repr__(self):
        return f"<DataProfilingJob(id={self.id}, job_id={self.job_id}, status={self.status})>"


class AttributeProfileResult(CustomPKModel, AuditMixin):
    """Detailed profiling results for individual attributes"""
    __tablename__ = "cycle_report_data_profiling_attribute_results"
    
    id = Column(Integer, primary_key=True)
    profiling_job_id = Column(Integer, ForeignKey("cycle_report_data_profiling_jobs.id"), nullable=False)
    attribute_id = Column(UUID(as_uuid=True), ForeignKey("cycle_report_planning_attributes.id"), nullable=False)
    attribute_name = Column(String(255), nullable=False)
    
    # Basic statistics
    total_values = Column(BigInteger, nullable=False)
    null_count = Column(BigInteger, default=0)
    null_percentage = Column(Float, default=0.0)
    distinct_count = Column(BigInteger, default=0)
    distinct_percentage = Column(Float, default=0.0)
    
    # Data type analysis
    detected_data_type = Column(String(100), nullable=True)
    type_consistency = Column(Float, nullable=True)  # 0.0 to 1.0
    
    # Numeric statistics (if applicable)
    min_value = Column(Float, nullable=True)
    max_value = Column(Float, nullable=True)
    mean_value = Column(Float, nullable=True)
    median_value = Column(Float, nullable=True)
    std_deviation = Column(Float, nullable=True)
    percentile_25 = Column(Float, nullable=True)
    percentile_75 = Column(Float, nullable=True)
    
    # String statistics (if applicable)
    min_length = Column(Integer, nullable=True)
    max_length = Column(Integer, nullable=True)
    avg_length = Column(Float, nullable=True)
    
    # Pattern analysis
    common_patterns = Column(JSONB, nullable=True)  # Top patterns found
    pattern_coverage = Column(Float, nullable=True)  # Percentage of data matching patterns
    
    # Value distribution
    top_values = Column(JSONB, nullable=True)  # Most frequent values
    value_distribution = Column(JSONB, nullable=True)  # Statistical distribution
    
    # Quality scores
    completeness_score = Column(Float, nullable=False, default=0.0)
    validity_score = Column(Float, nullable=False, default=0.0)
    consistency_score = Column(Float, nullable=False, default=0.0)
    uniqueness_score = Column(Float, nullable=False, default=0.0)
    overall_quality_score = Column(Float, nullable=False, default=0.0)
    
    # Anomaly detection
    anomaly_count = Column(Integer, default=0)
    anomaly_examples = Column(JSONB, nullable=True)
    anomaly_rules_triggered = Column(JSONB, nullable=True)  # Rule names that detected anomalies
    outliers_detected = Column(Integer, default=0)
    outlier_examples = Column(JSONB, nullable=True)
    
    # Performance metrics
    profiling_duration_ms = Column(Integer, nullable=True)
    sampling_applied = Column(Boolean, default=False)
    sample_size_used = Column(Integer, nullable=True)
    
    # Relationships
    profiling_job = relationship("DataProfilingJob", foreign_keys=[profiling_job_id])
    attribute = relationship("ReportAttribute", foreign_keys=[attribute_id])
    
    def __repr__(self):
        return f"<AttributeProfileResult(id={self.id}, attribute_name={self.attribute_name}, quality_score={self.overall_quality_score})>"


# Legacy models - DEPRECATED, will be removed after migration
class DataProfilingFile(CustomPKModel, AuditMixin):
    """DEPRECATED: Files referenced from planning phase instead"""
    
    __tablename__ = "cycle_report_data_profiling_files"
    
    file_id = Column(Integer, primary_key=True, index=True)
    phase_id = Column(Integer, ForeignKey('workflow_phases.phase_id'), nullable=False)
    # ... other fields kept for migration compatibility
    
    # Relationships
    phase = relationship("WorkflowPhase", foreign_keys=[phase_id])
    
    def __repr__(self):
        return f"<DataProfilingFile(file_id={self.file_id}, phase_id={self.phase_id}) [DEPRECATED]>"


class ProfilingResult(CustomPKModel, AuditMixin):
    """Stores execution results for data profiling rules"""
    
    __tablename__ = "cycle_report_data_profiling_results"
    
    result_id = Column(Integer, primary_key=True, index=True)
    phase_id = Column(Integer, ForeignKey('workflow_phases.phase_id'), nullable=False)
    rule_id = Column(UUID(as_uuid=True), ForeignKey('cycle_report_data_profiling_rules.rule_id'), nullable=False)
    attribute_id = Column(Integer, nullable=True)  # Made nullable since attribute table doesn't exist
    execution_status = Column(String(50), nullable=False)
    execution_time_ms = Column(Integer)
    executed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    passed_count = Column(Integer)
    failed_count = Column(Integer)
    total_count = Column(Integer)
    pass_rate = Column(Float)
    result_summary = Column(JSON)
    failed_records = Column(JSON)
    result_details = Column(Text)
    quality_impact = Column(Float)
    severity = Column(String(50))
    has_anomaly = Column(Boolean, default=False)
    anomaly_description = Column(Text)
    anomaly_marked_by = Column(Integer, ForeignKey('users.user_id'))
    anomaly_marked_at = Column(DateTime)
    
    # Relationships
    phase = relationship("WorkflowPhase", foreign_keys=[phase_id])
    rule = relationship("ProfilingRule", foreign_keys=[rule_id])
    # Removed attribute relationship since ReportAttribute table doesn't exist
    anomaly_marked_by_user = relationship("User", foreign_keys=[anomaly_marked_by])
    
    def __repr__(self):
        return f"<ProfilingResult(result_id={self.result_id}, rule_id={self.rule_id}, status={self.execution_status})>"


# For backward compatibility - aliases
DataProfilingVersion = DataProfilingRuleVersion
DataProfilingRule = ProfilingRule