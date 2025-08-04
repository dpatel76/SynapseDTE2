"""
Data Source Configuration models
"""

from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, DateTime, JSON, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.models.base import Base, CustomPKModel
from app.models.audit_mixin import AuditMixin


class DataSourceType(str, enum.Enum):
    """Types of data sources supported"""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    ORACLE = "oracle"
    SQLSERVER = "sqlserver"
    MONGODB = "mongodb"
    CSV = "csv"
    EXCEL = "excel"
    API = "api"
    SFTP = "sftp"
    S3 = "s3"


# DISABLED: DataSourceConfig conflicts with CycleReportDataSource table - using CycleReportDataSource instead  
# class DataSourceConfig(Base, AuditMixin):
#     """Data source configuration for reports"""
#     __tablename__ = "cycle_report_planning_data_sources"
# 
#     id = Column(Integer, primary_key=True)
#     cycle_id = Column(Integer, ForeignKey("test_cycles.cycle_id"), nullable=False)
#     report_id = Column(Integer, ForeignKey("reports.id"), nullable=False)
#     
#     # Basic configuration
#     name = Column(String(255), nullable=False)
#     description = Column(Text)
#     source_type = Column(Enum(DataSourceType), nullable=False)
#     is_active = Column(Boolean, default=True)
#     
#     # Connection details (encrypted in production)
#     connection_config = Column(JSON)  # Store connection details as JSON
#     
#     # Authentication
#     auth_type = Column(String(50))  # basic, oauth, api_key, certificate
#     auth_config = Column(JSON)  # Store auth details (encrypted)
#     
#     # Additional settings
#     refresh_schedule = Column(String(100))  # Cron expression for data refresh
#     last_sync_at = Column(DateTime)
#     last_sync_status = Column(String(50))
#     last_sync_message = Column(Text)
#     
#     # Validation rules
#     validation_rules = Column(JSON)  # Custom validation rules for this data source
#     
#     # Relationships
#     cycle = relationship("TestCycle", back_populates="data_source_configs")
#     report = relationship("Report", back_populates="data_source_configs")
#     pde_mappings = relationship("PDEMapping", back_populates="data_source", cascade="all, delete-orphan")


# DISABLED: PDEMapping conflicts with PlanningPDEMapping table - using PlanningPDEMapping instead
# class PDEMapping(Base, AuditMixin):
#     """Physical Data Element mapping to report attributes"""
#     __tablename__ = "cycle_report_planning_pde_mappings"
# 
#     id = Column(Integer, primary_key=True)
#     cycle_id = Column(Integer, ForeignKey("test_cycles.cycle_id"), nullable=False)
#     report_id = Column(Integer, ForeignKey("reports.id"), nullable=False)
#     attribute_id = Column(UUID(as_uuid=True), ForeignKey("cycle_report_planning_attributes.id"), nullable=False)
#     data_source_id = Column(UUID(as_uuid=True), ForeignKey("cycle_report_planning_data_sources.data_source_id"))
#     
#     # PDE information
#     pde_name = Column(String(255), nullable=False)
#     pde_code = Column(String(100), unique=True, nullable=False)
#     pde_description = Column(Text)
#     
#     # Mapping details
#     source_field = Column(String(255))  # Field in the data source
#     transformation_rule = Column(JSON)  # How to transform source to target
#     mapping_type = Column(String(50))  # direct, calculated, lookup, conditional
#     
#     # LLM-assisted mapping
#     llm_suggested_mapping = Column(JSON)  # LLM's suggested mapping configuration
#     llm_confidence_score = Column(Integer)  # 0-100 confidence in the mapping
#     llm_mapping_rationale = Column(Text)  # Why LLM suggested this mapping
#     llm_alternative_mappings = Column(JSON)  # Other possible mappings suggested
#     mapping_confirmed_by_user = Column(Boolean, default=False)
#     
#     # Business metadata
#     business_process = Column(String(255))
#     business_owner = Column(String(255))
#     data_steward = Column(String(255))
#     
#     # Classification (will be set in classify_pdes activity)
#     criticality = Column(String(50))  # high, medium, low
#     risk_level = Column(String(50))  # high, medium, low
#     regulatory_flag = Column(Boolean, default=False)
#     pii_flag = Column(Boolean, default=False)
#     
#     # LLM-assisted classification
#     llm_suggested_criticality = Column(String(50))
#     llm_suggested_risk_level = Column(String(50))
#     llm_classification_rationale = Column(Text)
#     llm_regulatory_references = Column(JSON)  # Specific regulations that apply
#     
#     # Information Security Classification
#     information_security_classification = Column(String(50))  # HRCI, Confidential, Proprietary, Public
#     
#     # Validation
#     is_validated = Column(Boolean, default=False)
#     validation_message = Column(Text)
#     
#     # Data profiling criteria (for reproducibility)
#     profiling_criteria = Column(JSON)  # timeframe, filters, etc.
#     
#     # Relationships
#     attribute = relationship("ReportAttribute")
#     data_source = relationship("DataSourceConfig", back_populates="pde_mappings")
#     classifications = relationship("PDEClassification", back_populates="pde_mapping", cascade="all, delete-orphan")


class PDEClassification(CustomPKModel, AuditMixin):
    """Detailed classification of PDEs"""
    __tablename__ = "cycle_report_planning_pde_classifications"

    id = Column(Integer, primary_key=True)
    pde_mapping_id = Column(Integer, ForeignKey("cycle_report_planning_pde_mappings.pde_mapping_id"), nullable=False)
    
    # Classification details
    classification_type = Column(String(100), nullable=False)  # criticality, risk, regulatory, data_sensitivity
    classification_value = Column(String(100), nullable=False)  # high, medium, low, etc.
    classification_reason = Column(Text)
    
    # Supporting evidence
    evidence_type = Column(String(100))  # regulation, policy, historical_issue, business_rule
    evidence_reference = Column(String(500))
    evidence_details = Column(JSON)
    
    # Review and approval
    classified_by = Column(Integer, ForeignKey("users.user_id"))
    reviewed_by = Column(Integer, ForeignKey("users.user_id"))
    approved_by = Column(Integer, ForeignKey("users.user_id"))
    review_status = Column(String(50))  # pending, reviewed, approved, rejected
    review_notes = Column(Text)
    
    # Relationships
    # pde_mapping = relationship("PDEMapping", back_populates="classifications")  # Disabled - PDEMapping is disabled
    classifier = relationship("User", foreign_keys=[classified_by])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    approver = relationship("User", foreign_keys=[approved_by])