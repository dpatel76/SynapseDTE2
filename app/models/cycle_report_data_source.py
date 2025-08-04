"""
Cycle Report Data Source models
"""

from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, DateTime, JSON, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.models.base import Base, TimestampMixin
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


class CycleReportDataSource(Base, TimestampMixin, AuditMixin):
    """Data source configuration for cycle reports"""
    __tablename__ = "cycle_report_planning_data_sources"

    id = Column(Integer, primary_key=True)
    phase_id = Column(Integer, ForeignKey("workflow_phases.phase_id"), nullable=True)
    
    # Basic configuration
    name = Column(String(255), nullable=False)
    description = Column(Text)
    source_type = Column(Enum(DataSourceType), nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Connection details (encrypted in production)
    connection_config = Column(JSON)  # Store connection details as JSON
    
    # Authentication
    auth_type = Column(String(50))  # basic, oauth, api_key, certificate
    auth_config = Column(JSON)  # Store auth details (encrypted)
    
    # Additional settings
    refresh_schedule = Column(String(100))  # Cron expression for data refresh
    last_sync_at = Column(DateTime)
    last_sync_status = Column(String(50))
    last_sync_message = Column(Text)
    
    # Validation rules
    validation_rules = Column(JSON)  # Custom validation rules for this data source
    
    # Schema information (for LLM mapping)
    schema_summary = Column(Text)  # Table and column information for mapping
    
    # Relationships
    phase = relationship("WorkflowPhase")

    def __repr__(self):
        return f"<CycleReportDataSource(id={self.id}, name={self.name}, source_type={self.source_type})>"