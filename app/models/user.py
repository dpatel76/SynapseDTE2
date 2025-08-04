"""
User models
"""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ENUM
from app.models.base import CustomPKModel

# User roles enum
user_role_enum = ENUM(
    'Tester',
    'Test Executive', 
    'Report Owner',
    'Report Executive',
    'Data Owner',
    'Data Executive',
    'Admin',
    name='user_role_enum'
)

# Association table for Report Owner to Executive mapping - REMOVED
# Now handled through role-based system with "Report Executive" role
# report_owner_executives = Table(
#     'report_owner_executives',
#     CustomPKModel.metadata,
#     Column('executive_id', Integer, ForeignKey('users.user_id'), primary_key=True),
#     Column('report_owner_id', Integer, ForeignKey('users.user_id'), primary_key=True)
# )


class User(CustomPKModel):
    """User model with role-based access"""
    
    __tablename__ = "users"
    
    user_id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    phone = Column(String(20), nullable=True)
    role = Column(user_role_enum, nullable=False, index=True)
    lob_id = Column(Integer, ForeignKey('lobs.lob_id'), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Password fields (will be added in auth module)
    hashed_password = Column(String(255), nullable=False)
    
    # RBAC relationships
    user_roles = relationship("UserRole", foreign_keys="UserRole.user_id", back_populates="user", cascade="all, delete-orphan")
    user_permissions = relationship("UserPermission", foreign_keys="UserPermission.user_id", back_populates="user", cascade="all, delete-orphan")
    resource_permissions = relationship("ResourcePermission", foreign_keys="ResourcePermission.user_id", back_populates="user", cascade="all, delete-orphan")
    
    # Relationships
    lob = relationship("LOB", primaryjoin="User.lob_id == LOB.lob_id", back_populates="users")
    
    # Report Owner relationships
    owned_reports = relationship("Report", primaryjoin="User.user_id == Report.report_owner_id", back_populates="owner")
    
    # Executive relationships - REMOVED (now handled through role-based system)
    # Users with "Report Executive" role can access reports from "Report Owner" role users
    # report_owners = relationship(
    #     "User",
    #     secondary=report_owner_executives,
    #     primaryjoin=user_id == report_owner_executives.c.executive_id,
    #     secondaryjoin=user_id == report_owner_executives.c.report_owner_id,
    #     back_populates="executives"
    # )
    # executives = relationship(
    #     "User",
    #     secondary=report_owner_executives,
    #     primaryjoin=user_id == report_owner_executives.c.report_owner_id,
    #     secondaryjoin=user_id == report_owner_executives.c.executive_id,
    #     back_populates="report_owners"
    # )
    
    # Test cycle relationships
    managed_cycles = relationship("TestCycle", primaryjoin="User.user_id == TestCycle.test_executive_id", back_populates="test_executive")
    assigned_reports = relationship("CycleReport", primaryjoin="User.user_id == CycleReport.tester_id", back_populates="tester")
    test_executions = relationship("TestExecution", foreign_keys="TestExecution.executed_by", viewonly=True)
    
    # Data owner assignments - Deprecated (using universal assignments)
    # data_owner_assignments = relationship(
    #     "DataOwnerAssignment", 
    #     primaryjoin="User.user_id == DataOwnerAssignment.data_owner_id",
    #     back_populates="data_owner"
    # )
    # assigned_by_assignments = relationship(
    #     "DataOwnerAssignment", 
    #     primaryjoin="User.user_id == DataOwnerAssignment.assigned_by",
    #     back_populates="assigned_by_user"
    # )
    
    # Data owner phase relationships
    # lob_assignments removed - AttributeLOBAssignment table doesn't exist
    # data_executive_notifications = relationship("CDONotification", back_populates="data_executive")  # Deprecated - using universal assignments
    # historical_assignments removed - HistoricalDataOwnerAssignment table doesn't exist
    # historical_assignments_made removed - HistoricalDataOwnerAssignment table doesn't exist
    data_owner_audit_logs = relationship("DataOwnerPhaseAuditLog", primaryjoin="User.user_id == DataOwnerPhaseAuditLog.performed_by", back_populates="user")
    
    # Sample selection phase relationships
    # created_sample_sets = relationship(
    #     "SampleSet",
    #     primaryjoin="User.user_id == SampleSet.created_by",
    #     back_populates="created_by_user"
    # )
    # approved_sample_sets = relationship(
    #     "SampleSet",
    #     primaryjoin="User.user_id == SampleSet.approved_by",
    #     back_populates="approved_by_user"
    # )
    
    # Sample set versioning relationships
    # version_created_sample_sets = relationship(
    #     "SampleSet",
    #     primaryjoin="User.user_id == SampleSet.version_created_by",
    #     back_populates="version_created_by_user"
    # )
    # archived_sample_sets = relationship(
    #     "SampleSet",
    #     primaryjoin="User.user_id == SampleSet.archived_by",
    #     back_populates="archived_by_user"
    # )
    
    # Individual sample approval relationships
    # approved_sample_records = relationship(
    #     "SampleRecord",
    #     primaryjoin="User.user_id == SampleRecord.approved_by",
    #     back_populates="approved_by_user"
    # )
    
    # sample_validations = relationship("SampleValidationResult", primaryjoin="User.user_id == SampleValidationResult.validated_by", back_populates="validated_by_user")
    # resolved_validation_issues = relationship("SampleValidationIssue", primaryjoin="User.user_id == SampleValidationIssue.resolved_by", back_populates="resolved_by_user")
    # sample_approvals = relationship("SampleApprovalHistory", primaryjoin="User.user_id == SampleApprovalHistory.approved_by", back_populates="approved_by_user")
    # llm_sample_generations = relationship("LLMSampleGeneration", primaryjoin="User.user_id == LLMSampleGeneration.generated_by", back_populates="generated_by_user")
    # sample_uploads = relationship("SampleUploadHistory", primaryjoin="User.user_id == SampleUploadHistory.uploaded_by", back_populates="uploaded_by_user")
    # sample_selection_audit_logs = relationship("SampleSelectionAuditLog", primaryjoin="User.user_id == SampleSelectionAuditLog.performed_by", back_populates="user")
    
    # Individual samples relationships
    # Sample relationships (removed sample_individual references)
    
    # Audit logs
    audit_logs = relationship("AuditLog", primaryjoin="User.user_id == AuditLog.user_id", back_populates="user")
    llm_audit_logs = relationship("LLMAuditLog", primaryjoin="User.user_id == LLMAuditLog.executed_by", back_populates="executed_by_user")
    
    # Report Owner Assignment relationships
    # Report owner assignments - Deprecated (using universal assignments)
    # assigned_report_owner_tasks = relationship("ReportOwnerAssignment", primaryjoin="User.user_id == ReportOwnerAssignment.assigned_to", back_populates="assigned_to_user")
    # created_report_owner_assignments = relationship("ReportOwnerAssignment", primaryjoin="User.user_id == ReportOwnerAssignment.assigned_by", back_populates="assigned_by_user")
    # completed_report_owner_assignments = relationship("ReportOwnerAssignment", primaryjoin="User.user_id == ReportOwnerAssignment.completed_by", back_populates="completed_by_user")
    # report_owner_assignment_changes = relationship("ReportOwnerAssignmentHistory", primaryjoin="User.user_id == ReportOwnerAssignmentHistory.changed_by", back_populates="changed_by_user")
    
    # New unified planning phase relationships - Temporarily disabled to resolve SQLAlchemy conflicts
    # planning_versions_submitted = relationship("app.models.planning.PlanningVersion", 
    #                                          primaryjoin="User.user_id == foreign(remote(app.models.planning.PlanningVersion.submitted_by_id))",
    #                                          back_populates="submitted_by")
    # planning_versions_approved = relationship("app.models.planning.PlanningVersion", 
    #                                         primaryjoin="User.user_id == foreign(remote(app.models.planning.PlanningVersion.approved_by_id))",
    #                                         back_populates="approved_by")
    # planning_data_source_decisions = relationship("app.models.planning.PlanningDataSource", 
    #                                             primaryjoin="User.user_id == foreign(remote(app.models.planning.PlanningDataSource.tester_decided_by))",
    #                                             back_populates="tester_decided_by_user")
    # PlanningAttribute relationship disabled due to table conflict with ReportAttribute
    # planning_attribute_decisions = relationship("app.models.planning.PlanningAttribute", 
    #                                           primaryjoin="User.user_id == foreign(remote(app.models.planning.PlanningAttribute.tester_decided_by))",
    #                                           back_populates="tester_decided_by_user")
    # planning_pde_mapping_decisions = relationship("app.models.planning.PlanningPDEMapping", 
    #                                             primaryjoin="User.user_id == foreign(remote(app.models.planning.PlanningPDEMapping.tester_decided_by))",
    #                                             back_populates="tester_decided_by_user")
    
    # Universal Assignment relationships - properly handling circular imports
    
    @property
    def full_name(self) -> str:
        """Get user's full name"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_tester(self) -> bool:
        """Check if user is a tester"""
        return self.role == 'Tester'
    
    @property
    def is_test_executive(self) -> bool:
        """Check if user is a test manager"""
        return self.role == 'Test Executive'
    
    @property
    def is_report_owner(self) -> bool:
        """Check if user is a report owner"""
        return self.role == 'Report Owner'
    
    @property
    def is_report_owner_executive(self) -> bool:
        """Check if user is a report owner executive"""
        return self.role == 'Report Executive'
    
    @property
    def is_report_executive(self) -> bool:
        """Check if user is a report executive (alias for report owner executive)"""
        return self.role == 'Report Executive'
    
    @property
    def is_data_owner(self) -> bool:
        """Check if user is a data provider"""
        return self.role == 'Data Owner'
    
    @property
    def is_data_executive(self) -> bool:
        """Check if user is a Data Executive"""
        return self.role == 'Data Executive'
    
    @property
    def is_cdo(self) -> bool:
        """Deprecated: Use is_data_executive instead"""
        return self.is_data_executive
    
    @property
    def is_admin(self) -> bool:
        """Check if user is an admin"""
        return self.role == 'Admin'
    
    def __repr__(self):
        return f"<User(id={self.user_id}, email='{self.email}', role='{self.role}')>"


# Configure Universal Assignment relationships after class definition to avoid circular imports
def configure_universal_assignment_relationships():
    """Configure Universal Assignment relationships after both User and UniversalAssignment classes are defined"""
    try:
        from app.models.universal_assignment import UniversalAssignment, UniversalAssignmentHistory
        
        # Add the relationships to the User class
        User.created_assignments = relationship("UniversalAssignment", 
                                              primaryjoin="User.user_id == UniversalAssignment.from_user_id", 
                                              back_populates="from_user")
        
        User.received_assignments = relationship("UniversalAssignment", 
                                               primaryjoin="User.user_id == UniversalAssignment.to_user_id", 
                                               back_populates="to_user")
        
        User.completed_assignments = relationship("UniversalAssignment", 
                                                primaryjoin="User.user_id == UniversalAssignment.completed_by_user_id", 
                                                back_populates="completed_by_user")
        
        User.approved_assignments = relationship("UniversalAssignment", 
                                               primaryjoin="User.user_id == UniversalAssignment.approved_by_user_id", 
                                               back_populates="approved_by_user")
        
        User.escalated_assignments = relationship("UniversalAssignment", 
                                                primaryjoin="User.user_id == UniversalAssignment.escalated_to_user_id", 
                                                back_populates="escalated_to_user")
        
        User.delegated_assignments = relationship("UniversalAssignment", 
                                                primaryjoin="User.user_id == UniversalAssignment.delegated_to_user_id", 
                                                back_populates="delegated_to_user")
        
        User.assignment_changes = relationship("UniversalAssignmentHistory", 
                                             primaryjoin="User.user_id == UniversalAssignmentHistory.changed_by_user_id",
                                             back_populates="changed_by_user")
    except ImportError:
        # If UniversalAssignment models don't exist, skip this configuration
        pass

# Call the configuration function
configure_universal_assignment_relationships() 