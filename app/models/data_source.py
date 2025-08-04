"""
Data Source models for connecting to external databases
Supports secure credential storage and connection management
"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey, Enum as SQLEnum, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB 
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
import uuid
from cryptography.fernet import Fernet
import os

from app.models.base import CustomPKModel
from app.models.audit_mixin import AuditMixin


class DataSourceType(str, Enum):
    """Supported data source types"""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    ORACLE = "oracle"
    SQLSERVER = "sqlserver"
    SNOWFLAKE = "snowflake"
    BIGQUERY = "bigquery"
    REDSHIFT = "redshift"
    FILE = "file"  # For backward compatibility


class SecurityClassification(str, Enum):
    """Information security classification levels"""
    HRCI = "HRCI"  # Highly Restricted Confidential Information
    CONFIDENTIAL = "Confidential"
    PROPRIETARY = "Proprietary"
    PUBLIC = "Public"


class DataSource(CustomPKModel, AuditMixin):
    """Data source configuration for reports"""
    __tablename__ = 'data_sources_v2'
    
    data_source_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    report_id = Column(Integer, ForeignKey('reports.id'), nullable=False)
    
    # Source identification
    source_name = Column(String(255), nullable=False)
    source_type = Column(SQLEnum(DataSourceType), nullable=False)
    description = Column(Text)
    
    # Connection details (encrypted)
    connection_config = Column(Text, nullable=False)  # Encrypted JSON
    _encryption_key = None
    
    # Metadata
    is_active = Column(Boolean, default=True)
    is_validated = Column(Boolean, default=False)
    last_validated_at = Column(DateTime)
    validation_error = Column(Text)
    
    # Default query patterns
    default_date_column = Column(String(255))  # For timeframe filtering
    default_schema = Column(String(255))
    
    # Relationships
    # report = relationship("Report", back_populates="data_sources")  # REMOVED: Data sources are managed at cycle level
    attribute_mappings = relationship("AttributeMapping", back_populates="data_source")
    profiling_executions = relationship("ProfilingExecution", back_populates="data_source")
    data_queries = relationship("DataQuery", back_populates="data_source")
    
    __table_args__ = (
        Index('idx_datasource_report', 'report_id', 'is_active'),
    )
    
    @classmethod
    def _get_encryption_key(cls):
        """Get or generate encryption key"""
        if not cls._encryption_key:
            key = os.environ.get('DATA_SOURCE_ENCRYPTION_KEY')
            if not key:
                # In production, this should come from a secure key management service
                key = Fernet.generate_key()
            cls._encryption_key = key
        return cls._encryption_key
    
    def encrypt_config(self, config_dict: dict) -> str:
        """Encrypt connection configuration"""
        import json
        fernet = Fernet(self._get_encryption_key())
        json_str = json.dumps(config_dict)
        return fernet.encrypt(json_str.encode()).decode()
    
    def decrypt_config(self) -> dict:
        """Decrypt connection configuration"""
        import json
        fernet = Fernet(self._get_encryption_key())
        decrypted = fernet.decrypt(self.connection_config.encode())
        return json.loads(decrypted.decode())


class AttributeMapping(CustomPKModel, AuditMixin):
    """Maps report attributes to physical data elements"""
    __tablename__ = 'attribute_mappings'
    
    mapping_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    attribute_id = Column(UUID(as_uuid=True), ForeignKey("cycle_report_planning_attributes.id"), nullable=False)
    data_source_id = Column(UUID, ForeignKey('data_sources_v2.data_source_id'), nullable=False)
    
    # Physical mapping
    table_name = Column(String(255), nullable=False)
    column_name = Column(String(255), nullable=False)
    data_type = Column(String(100))
    
    # Security classification
    security_classification = Column(
        SQLEnum(SecurityClassification), 
        nullable=False, 
        default=SecurityClassification.PUBLIC
    )
    
    # Mapping metadata
    is_primary_key = Column(Boolean, default=False)
    is_nullable = Column(Boolean, default=True)
    column_description = Column(Text)
    
    # LLM-assisted mapping
    mapping_confidence = Column(Integer)  # 0-100
    llm_suggested = Column(Boolean, default=False)
    manual_override = Column(Boolean, default=False)
    
    # Validation
    is_validated = Column(Boolean, default=False)
    validation_error = Column(Text)
    
    # Relationships
    # attribute = relationship("app.models.planning.PlanningAttribute", back_populates="attribute_mappings")  # TODO: Check if this is still needed
    data_source = relationship("DataSource", back_populates="attribute_mappings")
    
    __table_args__ = (
        Index('idx_mapping_attribute', 'attribute_id'),
        Index('idx_mapping_source', 'data_source_id'),
        Index('idx_mapping_security', 'security_classification'),
    )


class DataQuery(CustomPKModel, AuditMixin):
    """Stores queries for retrieving data from sources"""
    __tablename__ = 'data_queries'
    
    query_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    data_source_id = Column(UUID, ForeignKey('data_sources_v2.data_source_id'), nullable=False)
    
    # Query details
    query_name = Column(String(255), nullable=False)
    query_type = Column(String(50), nullable=False)  # profiling, sampling, testing, retrieval
    query_template = Column(Text, nullable=False)
    
    # Parameters
    parameters = Column(JSONB)  # Dynamic parameters for the query
    
    # Performance hints
    estimated_rows = Column(Integer)
    execution_timeout_seconds = Column(Integer, default=300)
    
    # Relationships
    data_source = relationship("DataSource", back_populates="data_queries")
    
    __table_args__ = (
        Index('idx_query_source_type', 'data_source_id', 'query_type'),
    )


class ProfilingExecution(CustomPKModel, AuditMixin):
    """Tracks data profiling executions on data sources"""
    __tablename__ = 'cycle_report_data_profiling_highvolume_executions'
    
    execution_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    cycle_id = Column(Integer, ForeignKey('test_cycles.cycle_id'), nullable=False)
    report_id = Column(Integer, ForeignKey('reports.id'), nullable=False)
    data_source_id = Column(UUID, ForeignKey('data_sources_v2.data_source_id'))
    
    # Execution details
    execution_type = Column(String(50), nullable=False)  # file, database
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    status = Column(String(50), nullable=False)  # running, completed, failed
    
    # Profiling criteria
    profiling_criteria = Column(JSONB, nullable=False)  # timeframe, filters, etc.
    total_records_profiled = Column(Integer)
    total_rules_executed = Column(Integer)
    
    # Performance metrics
    execution_time_seconds = Column(Integer)
    records_per_second = Column(Integer)
    peak_memory_mb = Column(Integer)
    
    # Results summary
    rules_passed = Column(Integer)
    rules_failed = Column(Integer)
    anomalies_detected = Column(Integer)
    
    # Error handling
    error_message = Column(Text)
    error_details = Column(JSONB)
    
    # Relationships
    cycle = relationship("TestCycle")
    report = relationship("Report")
    data_source = relationship("DataSource", back_populates="profiling_executions")
    # profiling_results = relationship("ProfilingResult", back_populates="execution")  # No direct relationship - results belong to phase
    
    __table_args__ = (
        Index('idx_profiling_exec_cycle', 'cycle_id', 'report_id'),
        Index('idx_profiling_exec_status', 'status', 'start_time'),
    )


class SecureDataAccess(CustomPKModel, AuditMixin):
    """Audit log for sensitive data access"""
    __tablename__ = 'secure_data_access_logs'
    
    access_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    
    # What was accessed
    table_name = Column(String(255), nullable=False)
    column_name = Column(String(255), nullable=False)
    record_identifier = Column(String(255))  # Primary key or identifier
    security_classification = Column(SQLEnum(SecurityClassification), nullable=False)
    
    # Access context
    access_type = Column(String(50), nullable=False)  # view, export, test
    access_reason = Column(Text)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    
    # Access timestamp
    accessed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    
    __table_args__ = (
        Index('idx_secure_access_user', 'user_id', 'accessed_at'),
        Index('idx_secure_access_classification', 'security_classification', 'accessed_at'),
    )