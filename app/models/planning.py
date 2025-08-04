"""
Unified Planning Phase Models
This module contains the new unified planning phase architecture with 4 core tables:
1. PlanningVersion - Version management and planning metadata
2. PlanningDataSource - Phase-level data source definitions
3. PlanningAttribute - Individual planning attributes
4. PlanningPDEMapping - PDE mappings for attributes
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, UniqueConstraint, ForeignKeyConstraint, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM 
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import AuditableCustomPKModel
from app.models.audit_mixin import AuditMixin
import enum
import uuid


# Enums for the planning phase
class VersionStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class DataSourceType(str, enum.Enum):
    DATABASE = "database"
    FILE = "file"
    API = "api"
    SFTP = "sftp"
    S3 = "s3"
    OTHER = "other"


class AttributeDataType(str, enum.Enum):
    STRING = "string"
    INTEGER = "integer"
    DECIMAL = "decimal"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    TEXT = "text"


class InformationSecurityClassification(str, enum.Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class MappingType(str, enum.Enum):
    DIRECT = "direct"
    CALCULATED = "calculated"
    LOOKUP = "lookup"
    CONDITIONAL = "conditional"


class Decision(str, enum.Enum):
    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_CHANGES = "request_changes"


class Status(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ReviewStatus(str, enum.Enum):
    """Review status for PDE mappings - duplicated here to avoid circular import"""
    PENDING = "pending"
    APPROVED = "approved" 
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"


class PlanningVersion(AuditableCustomPKModel):
    """Planning Version Management
    
    Manages planning phase versions and metadata including:
    - Version lifecycle management
    - Temporal workflow integration
    - Planning summary statistics
    - Tester-only approval workflow
    """
    
    __tablename__ = "cycle_report_planning_versions"
    
    # Primary Key
    version_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Phase Integration
    phase_id = Column(Integer, ForeignKey("workflow_phases.phase_id"), nullable=False)
    workflow_activity_id = Column(Integer, ForeignKey("workflow_activities.activity_id"), nullable=True)
    
    # Version Management
    version_number = Column(Integer, nullable=False)
    version_status = Column(ENUM(VersionStatus), nullable=False, default=VersionStatus.DRAFT)
    parent_version_id = Column(UUID(as_uuid=True), ForeignKey("cycle_report_planning_versions.version_id"), nullable=True)
    
    # Temporal Workflow Context
    workflow_execution_id = Column(String(255), nullable=True)
    workflow_run_id = Column(String(255), nullable=True)
    
    # Planning Summary Statistics
    total_attributes = Column(Integer, nullable=False, default=0)
    approved_attributes = Column(Integer, nullable=False, default=0)
    pk_attributes = Column(Integer, nullable=False, default=0)
    cde_attributes = Column(Integer, nullable=False, default=0)
    mandatory_attributes = Column(Integer, nullable=False, default=0)
    total_data_sources = Column(Integer, nullable=False, default=0)
    approved_data_sources = Column(Integer, nullable=False, default=0)
    total_pde_mappings = Column(Integer, nullable=False, default=0)
    approved_pde_mappings = Column(Integer, nullable=False, default=0)
    
    # LLM Generation Summary
    llm_generation_summary = Column(JSONB, nullable=True)
    
    # Tester-Only Approval Workflow
    submitted_by_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    approved_by_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("phase_id", "version_number", name="uq_planning_version_phase_number"),
    )
    
    # Relationships
    phase = relationship("WorkflowPhase")  # back_populates disabled - planning_versions commented out in WorkflowPhase
    workflow_activity = relationship("WorkflowActivity")  # back_populates disabled - planning_versions commented out in WorkflowActivity
    parent_version = relationship("PlanningVersion", remote_side=[version_id])
    child_versions = relationship("PlanningVersion", back_populates="parent_version")
    
    submitted_by = relationship("User", foreign_keys=[submitted_by_id])
    approved_by = relationship("User", foreign_keys=[approved_by_id])
    
    # data_sources = relationship("PlanningDataSource", back_populates="version", cascade="all, delete-orphan")  # Disabled - using CycleReportDataSource instead
    # attributes = relationship("PlanningAttribute", back_populates="version", cascade="all, delete-orphan")  # Disabled - using ReportAttribute instead
    # pde_mappings = relationship("PlanningPDEMapping", back_populates="version", cascade="all, delete-orphan")  # Disabled - version_id doesn't exist in PDE mappings table
    
    def __repr__(self):
        return f"<PlanningVersion(version_id={self.version_id}, phase_id={self.phase_id}, version_number={self.version_number})>"


# DISABLED: PlanningDataSource conflicts with CycleReportDataSource table - using CycleReportDataSource instead


# DISABLED: PlanningAttribute conflicts with ReportAttribute table - using ReportAttribute instead
# class PlanningAttribute(AuditableCustomPKModel):
#     """Individual Planning Attributes
#     
#     Manages individual planning attributes including:
#     - Attribute definitions and characteristics
#     - Information security classification
#     - LLM assistance metadata
#     - Tester decision workflow
#     """
#     
#     __tablename__ = "cycle_report_planning_attributes"
#     
#     # Primary Key
#     attribute_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     
#     # Version Reference
#     version_id = Column(UUID(as_uuid=True), ForeignKey("cycle_report_planning_versions.version_id", ondelete="CASCADE"), nullable=False)
#     
#     # Phase Integration
#     phase_id = Column(Integer, ForeignKey("workflow_phases.phase_id"), nullable=False)
#     
#     # Attribute Definition
#     attribute_name = Column(String(255), nullable=False)
#     data_type = Column(ENUM(AttributeDataType), nullable=False)
#     description = Column(Text, nullable=True)
#     business_definition = Column(Text, nullable=True)
#     
#     # Attribute Characteristics
#     is_mandatory = Column(Boolean, nullable=False, default=False)
#     is_cde = Column(Boolean, nullable=False, default=False)
#     is_primary_key = Column(Boolean, nullable=False, default=False)
#     max_length = Column(Integer, nullable=True)
#     
#     # Information Security Classification
#     information_security_classification = Column(ENUM(InformationSecurityClassification), nullable=False, default=InformationSecurityClassification.INTERNAL)
#     
#     # LLM Assistance Metadata
#     llm_metadata = Column(JSONB, nullable=True)
#     
#     # Tester Decision
#     tester_decision = Column(ENUM(Decision), nullable=True)
#     tester_decided_by = Column(Integer, ForeignKey("users.user_id"), nullable=True)
#     tester_decided_at = Column(DateTime(timezone=True), nullable=True)
#     tester_notes = Column(Text, nullable=True)
#     
#     # Status
#     status = Column(ENUM(Status), nullable=False, default=Status.PENDING)
#     
#     # Constraints
#     __table_args__ = (
#         UniqueConstraint("version_id", "attribute_name", name="uq_planning_attribute_version_name"),
#     )
#     
#     # Relationships
#     version = relationship("PlanningVersion", back_populates="attributes")
#     phase = relationship("WorkflowPhase", back_populates="planning_attributes_new")
#     tester_decided_by_user = relationship("User", foreign_keys=[tester_decided_by])
#     
#     pde_mappings = relationship("PlanningPDEMapping", back_populates="attribute", cascade="all, delete-orphan")
#     
#     def __repr__(self):
#         return f"<PlanningAttribute(attribute_id={self.attribute_id}, attribute_name={self.attribute_name})>"


class PlanningPDEMapping(AuditableCustomPKModel):
    """PDE Mappings for Attributes
    
    Manages PDE mappings for attributes including:
    - Multiple PDE mappings per attribute
    - Data source mapping details
    - PDE classification metadata
    - Tester decision workflow with auto-approval
    """
    
    __tablename__ = "cycle_report_planning_pde_mappings"
    
    # Primary Key - matches database table which uses 'id' integer column
    id = Column(Integer, primary_key=True)
    
    # Attribute and Data Source References - integers in DB
    attribute_id = Column(Integer, ForeignKey("cycle_report_planning_attributes.id", ondelete="CASCADE"), nullable=False)
    data_source_id = Column(Integer, nullable=True)
    
    # Phase Integration
    phase_id = Column(Integer, ForeignKey("workflow_phases.phase_id"), nullable=False)
    
    # PDE Definition
    pde_name = Column(String(255), nullable=False)
    pde_code = Column(String(100), nullable=False)
    pde_description = Column(Text, nullable=True)
    mapping_type = Column(String(50), nullable=True)
    
    # Data Source Mapping  
    source_field = Column(String(255), nullable=True)  # Full field path: schema.table.column
    transformation_rule = Column(JSON, nullable=True)
    
    # Business Metadata
    business_process = Column(String(255), nullable=True)
    business_owner = Column(String(255), nullable=True)
    data_steward = Column(String(255), nullable=True)
    
    # LLM Mapping Assistance
    llm_suggested_mapping = Column(JSON, nullable=True)
    llm_confidence_score = Column(Integer, nullable=True)
    llm_mapping_rationale = Column(Text, nullable=True)
    llm_alternative_mappings = Column(JSON, nullable=True)
    mapping_confirmed_by_user = Column(Boolean, default=False)
    
    # Classification
    criticality = Column(String(50), nullable=True)
    risk_level = Column(String(50), nullable=True)
    regulatory_flag = Column(Boolean, default=False)
    pii_flag = Column(Boolean, default=False)
    
    # LLM Classification Assistance
    llm_suggested_criticality = Column(String(50), nullable=True)
    llm_suggested_risk_level = Column(String(50), nullable=True)
    llm_classification_rationale = Column(Text, nullable=True)
    llm_regulatory_references = Column(JSON, nullable=True)
    
    # Information Security
    information_security_classification = Column(String(50), nullable=True)
    
    # Validation
    is_validated = Column(Boolean, default=False)
    validation_message = Column(Text, nullable=True)
    
    # Data profiling criteria
    profiling_criteria = Column(JSON, nullable=True)
    
    # Review Status
    latest_review_status = Column(ENUM(ReviewStatus), nullable=True)
    latest_review_id = Column(Integer, nullable=True)
    
    # Relationships
    phase = relationship("WorkflowPhase")  # back_populates disabled - planning_pde_mappings commented out in WorkflowPhase
    
    def __repr__(self):
        return f"<PlanningPDEMapping(id={self.id}, pde_code={self.pde_code})>"