"""
Report and Data Source models
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import CustomPKModel
from app.models.audit_mixin import AuditMixin
from app.core.security import encrypt_data, decrypt_data, SecurityAudit
# from app.models.user import report_owner_executives  # Temporarily disabled
import logging

logger = logging.getLogger(__name__)


class Report(CustomPKModel, AuditMixin):
    """Report inventory model"""
    
    __tablename__ = "reports"
    
    report_id = Column("id", Integer, primary_key=True, index=True)
    report_name = Column(String(255), nullable=False, index=True)
    report_number = Column(String(50), unique=True, nullable=False, index=True)
    regulation = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    frequency = Column(String(100), nullable=True)
    business_unit = Column(String(100), nullable=True)
    regulatory_requirement = Column(Boolean, default=False)
    status = Column(String(20), default='Active')
    report_owner_id = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    lob_id = Column(Integer, ForeignKey('lobs.lob_id'), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    lob = relationship("LOB", back_populates="reports")
    owner = relationship("User", foreign_keys=[report_owner_id], back_populates="owned_reports")
    cycle_reports = relationship("CycleReport", back_populates="report", cascade="all, delete-orphan")
    # documents = relationship("Document", back_populates="report")
    # report_attributes = relationship("ReportAttribute", back_populates="report")
    
    # Data provider phase relationships - All now connected through WorkflowPhase instead of direct Report relationships
    # This follows the architectural principle: data sources and assignments managed at cycle level through WorkflowPhase
    # attribute_lob_assignments = relationship("AttributeLOBAssignment", back_populates="report")  # Now phase-based
    # data_executive_notifications = relationship("CDONotification", back_populates="report")  # Deprecated
    # sla_violations = relationship("DataOwnerSLAViolation", back_populates="report")  # Now phase-based
    # escalation_emails = relationship("DataOwnerEscalationLog", back_populates="report")  # Now phase-based
    # data_owner_audit_logs = relationship("DataOwnerPhaseAuditLog", back_populates="report")  # Now phase-based
    
    # Sample selection phase relationships
    # sample_sets = relationship("SampleSet", back_populates="report")
    # sample_selection_phases = relationship("SampleSelectionPhase", back_populates="report")  # DEPRECATED: Use workflow_phases
    # sample_selection_audit_logs = relationship("SampleSelectionAuditLog", back_populates="report")
    
    # Individual samples relationships (forward declared to avoid circular imports)
    
    # Data Profiling phase relationships
    # data_profiling_phases = relationship("DataProfilingPhase", back_populates="report")  # DEPRECATED: Use workflow_phases
    
    # Request for Information phase relationships
    # request_info_phases = relationship("RequestInfoPhase", back_populates="report")  # DEPRECATED: Use workflow_phases
    
    # Testing execution relationships
    # samples = relationship("Sample", back_populates="report")  # DEPRECATED: Use unified sample selection system
    # test_executions = relationship("app.models.test_execution.TestExecution", back_populates="report")  # Removed - no direct relationship
    # observations = relationship("app.models.observation_enhanced.Observation", back_populates="report")  # Removed due to circular dependency
    # test_execution_phases = relationship("TestExecutionPhase", back_populates="report")  # DEPRECATED: Use workflow_phases
    
    # Observation management relationships
    # observation_management_phases = relationship("ObservationManagementPhase", back_populates="report")  # DEPRECATED: Use workflow_phases
    
    # Metrics relationships
    phase_metrics = relationship("PhaseMetrics", back_populates="report")
    execution_metrics = relationship("ExecutionMetrics", back_populates="report")
    
    # Versioned model relationships - Temporarily disabled until versioned models are fully configured
    # data_profiling_rules = relationship("DataProfilingRuleVersion", back_populates="report")
    # test_execution_versions = relationship("TestExecutionVersion", back_populates="report")
    # observation_versions = relationship("ObservationVersion", back_populates="report")
    # scoping_decision_versions = relationship("ScopingDecisionVersion", back_populates="report")
    # scoping_recommendation_versions = relationship("VersionedAttributeScopingRecommendation", back_populates="report")
    
    # Report Owner Assignment relationships - Deprecated (using universal assignments)
    # report_owner_assignments = relationship("ReportOwnerAssignment", back_populates="report")
    
    # Data source relationships - REMOVED: Reports don't have direct data source relationships
    # All data sources are managed at the cycle level through CycleReport
    # data_source_configs = relationship("DataSourceConfig", back_populates="report")  # Removed - using cycle-specific data sources
    
    # executives = relationship(
    #     "User",
    #     secondary=report_owner_executives,
    #     primaryjoin="Report.report_owner_id==report_owner_executives.c.report_owner_id",
    #     secondaryjoin="User.user_id==report_owner_executives.c.executive_id",
    #     overlaps="executives,report_owners"
    # )  # Temporarily disabled
    
    def __repr__(self):
        return f"<Report(id={self.report_id}, name='{self.report_name}', regulation='{self.regulation}')>"


# NOTE: DataSource model has been moved to app/models/data_source.py with enhanced features
# The old model is kept here commented out for reference
# class DataSource(CustomPKModel, AuditMixin):
#     """Data sources configuration model with AES-256 encryption"""
#     
#     __tablename__ = "data_sources"
#     
#     data_source_id = Column(Integer, primary_key=True, index=True)
#     data_source_name = Column(String(255), nullable=False, index=True)
#     database_type = Column(String(50), nullable=False)  # PostgreSQL, MySQL, Oracle, SQL Server
#     database_url = Column(Text, nullable=False)
#     database_user = Column(String(255), nullable=False)
#     database_password_encrypted = Column(Text, nullable=False)  # AES-256 encrypted password
#     description = Column(Text, nullable=True)  # Optional description field
#     is_active = Column(Boolean, default=True, nullable=False)
#     
#     # Relationships
#     test_executions = relationship("app.models.test_execution.TestExecution", back_populates="data_source")
#     
#     def set_password(self, password: str) -> None:
#         """Encrypt and store database password using AES-256"""
#         try:
#             self.database_password_encrypted = encrypt_data(password)
#             SecurityAudit.log_encryption_operation(
#                 "encrypt_password", 
#                 f"datasource_{self.data_source_id}", 
#                 True
#             )
#             logger.info(f"Password encrypted for data source: {self.data_source_id}")
#         except Exception as e:
#             SecurityAudit.log_encryption_operation(
#                 "encrypt_password", 
#                 f"datasource_{self.data_source_id}", 
#                 False
#             )
#             logger.error(f"Failed to encrypt password for data source {self.data_source_id}: {str(e)}")
#             raise
#     
#     def get_password(self) -> str:
#         """Decrypt and return database password"""
#         try:
#             if not self.database_password_encrypted:
#                 return ""
#             
#             password = decrypt_data(self.database_password_encrypted)
#             SecurityAudit.log_encryption_operation(
#                 "decrypt_password", 
#                 f"datasource_{self.data_source_id}", 
#                 True
#             )
#             logger.debug(f"Password decrypted for data source: {self.data_source_id}")
#             return password
#         except Exception as e:
#             SecurityAudit.log_encryption_operation(
#                 "decrypt_password", 
#                 f"datasource_{self.data_source_id}", 
#                 False
#             )
#             logger.error(f"Failed to decrypt password for data source {self.data_source_id}: {str(e)}")
#             raise
#     
#     def get_connection_info(self) -> dict:
#         """Get complete connection information with decrypted password"""
#         try:
#             return {
#                 "database_type": self.database_type,
#                 "database_url": self.database_url,
#                 "database_user": self.database_user,
#                 "database_password": self.get_password()
#             }
#         except Exception as e:
#             logger.error(f"Failed to get connection info for data source {self.data_source_id}: {str(e)}")
#             raise
#     
#     def test_connection(self) -> bool:
#         """Test database connection with encrypted credentials"""
#         # Implementation would depend on database type
#         # This is a placeholder for connection testing logic
#         try:
#             connection_info = self.get_connection_info()
#             # Database-specific connection testing would go here
#             logger.info(f"Connection test successful for data source: {self.data_source_id}")
#             return True
#         except Exception as e:
#             logger.error(f"Connection test failed for data source {self.data_source_id}: {str(e)}")
#             return False
#     
#     def __repr__(self):
#         return f"<DataSource(id={self.data_source_id}, name='{self.data_source_name}', type='{self.database_type}')>" 