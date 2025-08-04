"""
Report Attribute model for planning phase
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, Float, select
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.dialects.postgresql import ENUM, UUID 
from datetime import datetime
from app.models.base import CustomPKModel
from app.models.audit_mixin import AuditMixin
from app.core.logging import get_logger

logger = get_logger(__name__)

# Mandatory flag enum
mandatory_flag_enum = ENUM(
    'Mandatory',
    'Conditional', 
    'Optional',
    name='mandatory_flag_enum'
)

# Data type enum
data_type_enum = ENUM(
    'String',
    'Integer',
    'Decimal',
    'Date',
    'DateTime',
    'Boolean',
    'JSON',
    name='data_type_enum'
)

# Information Security Classification enum - using the existing database enum
security_classification_enum = ENUM(
    'Public',
    'Internal',
    'Confidential',
    'Restricted',
    'HRCI',
    name='security_classification_enum'
)

# Version change type enum for audit trail
version_change_type_enum = ENUM(
    'created',
    'updated',
    'approved',
    'rejected',
    'archived',
    'restored',
    name='version_change_type_enum'
)


class ReportAttribute(CustomPKModel, AuditMixin):
    """Report attributes model for planning phase with full versioning support"""
    
    __tablename__ = "cycle_report_planning_attributes"
    
    id = Column(Integer, primary_key=True, index=True)
    phase_id = Column(Integer, ForeignKey('workflow_phases.phase_id'), nullable=False)
    attribute_name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    data_type = Column(data_type_enum, nullable=True)
    mandatory_flag = Column('is_mandatory', mandatory_flag_enum, default='Optional', nullable=False)
    cde_flag = Column('is_cde', Boolean, default=False, nullable=False)
    historical_issues_flag = Column('has_issues', Boolean, default=False, nullable=False)
    is_scoped = Column(Boolean, default=False, nullable=False)
    llm_generated = Column(Boolean, default=False, nullable=False)
    llm_rationale = Column(Text, nullable=True)
    tester_notes = Column(Text, nullable=True)
    
    # Data dictionary import fields
    line_item_number = Column(String(20), nullable=True, comment='Regulatory line item number from data dictionary')
    technical_line_item_name = Column(String(255), nullable=True, comment='Technical line item name from data dictionary')
    mdrm = Column(String(50), nullable=True, comment='MDRM code from regulatory data dictionary')
    
    # Enhanced LLM-generated fields for better testing guidance
    validation_rules = Column(Text, nullable=True)
    typical_source_documents = Column(Text, nullable=True)
    keywords_to_look_for = Column(Text, nullable=True)
    testing_approach = Column(Text, nullable=True)
    
    # Risk assessment fields
    risk_score = Column(Float, nullable=True, comment='LLM-provided risk score (0-10) based on regulatory importance')
    llm_risk_rationale = Column(Text, nullable=True, comment='LLM explanation for the assigned risk score')
    
    # Primary key support fields
    is_primary_key = Column(Boolean, default=False, nullable=False, comment='Whether this attribute is part of the primary key')
    primary_key_order = Column(Integer, nullable=True, comment='Order of this attribute in composite primary key (1-based)')
    
    # Information Security Classification
    information_security_classification = Column(security_classification_enum, nullable=True, comment='Security classification: HRCI, Confidential, Proprietary, Public')
    
    # Approval workflow field
    approval_status = Column('status', String(20), default='pending', nullable=False, comment='Approval status: pending, approved, rejected')
    
    # VERSIONING FIELDS
    # Master attribute reference (links all versions of the same logical attribute)
    master_attribute_id = Column(Integer, ForeignKey("cycle_report_planning_attributes.id"), nullable=True)
    
    # Version information
    version_number = Column('version', Integer, default=1, nullable=False, comment='Version number of this attribute')
    is_latest_version = Column(Boolean, default=True, nullable=False, comment='Whether this is the latest version')
    is_active = Column(Boolean, default=True, nullable=False, comment='Whether this version is active')
    
    # Version metadata
    version_notes = Column(Text, nullable=True, comment='Notes about what changed in this version')
    change_reason = Column(String(100), nullable=True, comment='Reason for creating new version')
    replaced_attribute_id = Column(Integer, ForeignKey("cycle_report_planning_attributes.id"), nullable=True)
    
    # Version timestamps and user tracking
    version_created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    version_created_by = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    approved_at = Column(DateTime, nullable=True)
    approved_by = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    archived_at = Column(DateTime, nullable=True)
    archived_by = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    
    # Relationships
    phase = relationship("app.models.workflow.WorkflowPhase", back_populates="planning_attributes")
    data_owner_assignments = relationship("DataOwnerAssignment", back_populates="attribute")
    
    # Data provider phase relationships - removed (table doesn't exist)
    # lob_assignments removed - AttributeLOBAssignment table doesn't exist
    
    # Attribute mapping relationships
    attribute_mappings = relationship("AttributeMapping")  # back_populates disabled - AttributeMapping doesn't have 'attribute' relationship
    
    # Testing execution relationships
    # test_executions = relationship("app.models.test_execution.TestExecution", back_populates="attribute")  # Removed - relationship established through test case
    # observations = relationship("app.models.observation_enhanced.Observation", back_populates="attribute")  # Removed due to circular dependency
    
    # Versioned model relationships - Temporarily disabled until versioned models are fully configured
    # data_profiling_rules = relationship("DataProfilingRuleVersion", back_populates="attribute")
    # test_execution_versions = relationship("TestExecutionVersion", back_populates="attribute")
    # scoping_decision_versions = relationship("ScopingDecisionVersion", back_populates="attribute")
    # scoping_recommendation_versions = relationship("VersionedAttributeScopingRecommendation", back_populates="attribute")
    
    # VERSIONING RELATIONSHIPS
    # Self-referential relationship for master attribute
    master_attribute = relationship("ReportAttribute", 
                                   primaryjoin="ReportAttribute.master_attribute_id==ReportAttribute.id",
                                   remote_side="ReportAttribute.id",
                                   backref="attribute_versions")
    
    # Self-referential relationship for replaced attribute
    replaced_attribute = relationship("ReportAttribute", 
                                    primaryjoin="ReportAttribute.replaced_attribute_id==ReportAttribute.id",
                                    remote_side="ReportAttribute.id")
    
    # Version tracking relationships
    version_created_by_user = relationship("User", foreign_keys=[version_created_by])
    approved_by_user = relationship("User", foreign_keys=[approved_by])
    archived_by_user = relationship("User", foreign_keys=[archived_by])
    
    # Version change logs
    version_changes = relationship("AttributeVersionChangeLog", back_populates="attribute", cascade="all, delete-orphan")
    
    @property
    def attribute_id(self):
        """Backward compatibility property for attribute_id"""
        return self.id
    
    @attribute_id.setter
    def attribute_id(self, value):
        """Backward compatibility setter for attribute_id"""
        self.id = value
    
    @hybrid_property
    def cycle_id(self):
        """Get cycle_id from phase relationship for UI compatibility"""
        return self.phase.cycle_id if self.phase else None
    
    @cycle_id.expression
    def cycle_id(cls):
        """SQL expression for cycle_id"""
        from app.models.workflow import WorkflowPhase
        return select(WorkflowPhase.cycle_id).where(WorkflowPhase.phase_id == cls.phase_id).scalar_subquery()
    
    @hybrid_property
    def report_id(self):
        """Get report_id from phase relationship for UI compatibility"""
        return self.phase.report_id if self.phase else None
    
    @report_id.expression
    def report_id(cls):
        """SQL expression for report_id"""
        from app.models.workflow import WorkflowPhase
        return select(WorkflowPhase.report_id).where(WorkflowPhase.phase_id == cls.phase_id).scalar_subquery()
    
    @property
    def is_cde(self):
        """Property to access cde_flag with consistent naming"""
        return self.cde_flag
    
    @is_cde.setter
    def is_cde(self, value):
        """Setter for is_cde property"""
        self.cde_flag = value
    
    @property
    def has_issues(self):
        """Property to access historical_issues_flag with consistent naming"""
        return self.historical_issues_flag
    
    @has_issues.setter
    def has_issues(self, value):
        """Setter for has_issues property"""
        self.historical_issues_flag = value
    
    def create_new_version(self, updated_by_user_id: int, change_reason: str = None, version_notes: str = None) -> 'ReportAttribute':
        """Create a new version of this attribute"""
        try:
            # Mark current version as not latest
            self.is_latest_version = False
            
            # Create new attribute version
            new_version = ReportAttribute(
                # Copy all base attribute data
                phase_id=self.phase_id,
                attribute_name=self.attribute_name,
                description=self.description,
                data_type=self.data_type,
                mandatory_flag=self.mandatory_flag,
                cde_flag=self.cde_flag,
                historical_issues_flag=self.historical_issues_flag,
                is_scoped=self.is_scoped,
                llm_generated=self.llm_generated,
                llm_rationale=self.llm_rationale,
                tester_notes=self.tester_notes,
                
                # Data dictionary import fields
                line_item_number=self.line_item_number,
                technical_line_item_name=self.technical_line_item_name,
                mdrm=self.mdrm,
                
                # Enhanced LLM-generated fields for better testing guidance
                validation_rules=self.validation_rules,
                typical_source_documents=self.typical_source_documents,
                keywords_to_look_for=self.keywords_to_look_for,
                testing_approach=self.testing_approach,
                
                # Risk assessment fields
                risk_score=self.risk_score,
                llm_risk_rationale=self.llm_risk_rationale,
                
                # Primary key support fields
                is_primary_key=self.is_primary_key,
                primary_key_order=self.primary_key_order,
                
                # Approval workflow field
                approval_status='pending',  # New version starts as pending
                
                # VERSIONING FIELDS
                # Master attribute reference (links all versions of the same logical attribute)
                master_attribute_id=self.master_attribute_id or self.attribute_id,
                
                # Version information
                version_number=self.version_number + 1,
                is_latest_version=True,
                is_active=True,
                
                # Version metadata
                version_notes=version_notes,
                change_reason=change_reason,
                replaced_attribute_id=self.attribute_id,
                version_created_by=updated_by_user_id
            )
            
            logger.info(f"Created new version {new_version.version_number} for attribute {self.attribute_id}")
            return new_version
            
        except Exception as e:
            logger.error(f"Failed to create new version for attribute {self.attribute_id}: {str(e)}")
            raise
    
    def approve_version(self, approved_by_user_id: int, approval_notes: str = None):
        """Approve this version of the attribute"""
        self.approval_status = 'approved'
        self.approved_at = datetime.utcnow()
        self.approved_by = approved_by_user_id
        
        # Log the approval
        change_log = AttributeVersionChangeLog(
            attribute_id=self.attribute_id,
            change_type='approved',
            changed_by=approved_by_user_id,
            change_notes=approval_notes,
            version_number=self.version_number
        )
        
        logger.info(f"Approved attribute version {self.attribute_id} v{self.version_number} by user {approved_by_user_id}")
        return change_log
    
    def reject_version(self, rejected_by_user_id: int, rejection_reason: str = None):
        """Reject this version of the attribute"""
        self.approval_status = 'rejected'
        self.is_active = False
        
        # Log the rejection
        change_log = AttributeVersionChangeLog(
            attribute_id=self.attribute_id,
            change_type='rejected',
            changed_by=rejected_by_user_id,
            change_notes=rejection_reason,
            version_number=self.version_number
        )
        
        logger.info(f"Rejected attribute version {self.attribute_id} v{self.version_number} by user {rejected_by_user_id}")
        return change_log
    
    def archive_version(self, archived_by_user_id: int, archive_reason: str = None):
        """Archive this version of the attribute"""
        self.is_active = False
        self.archived_at = datetime.utcnow()
        self.archived_by = archived_by_user_id
        
        # Log the archival
        change_log = AttributeVersionChangeLog(
            attribute_id=self.attribute_id,
            change_type='archived',
            changed_by=archived_by_user_id,
            change_notes=archive_reason,
            version_number=self.version_number
        )
        
        logger.info(f"Archived attribute version {self.attribute_id} v{self.version_number} by user {archived_by_user_id}")
        return change_log
    
    def restore_version(self, restored_by_user_id: int, restore_reason: str = None):
        """Restore this version of the attribute as the latest active version"""
        # First, mark all other versions of this attribute as not latest
        # This would typically be done in the service layer with a database session
        
        self.is_latest_version = True
        self.is_active = True
        self.approval_status = 'approved'  # Restored versions are automatically approved
        self.archived_at = None
        self.archived_by = None
        
        # Log the restoration
        change_log = AttributeVersionChangeLog(
            attribute_id=self.attribute_id,
            change_type='restored',
            changed_by=restored_by_user_id,
            change_notes=restore_reason,
            version_number=self.version_number
        )
        
        logger.info(f"Restored attribute version {self.attribute_id} v{self.version_number} by user {restored_by_user_id}")
        return change_log
    
    def get_version_summary(self) -> dict:
        """Get comprehensive version information"""
        return {
            "attribute_id": self.attribute_id,
            "attribute_name": self.attribute_name,
            "master_attribute_id": self.master_attribute_id,
            "version_number": self.version_number,
            "is_latest_version": self.is_latest_version,
            "is_active": self.is_active,
            "approval_status": self.approval_status,
            "version_notes": self.version_notes,
            "change_reason": self.change_reason,
            "version_created_at": self.version_created_at.isoformat() if self.version_created_at else None,
            "version_created_by": self.version_created_by,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "approved_by": self.approved_by,
            "archived_at": self.archived_at.isoformat() if self.archived_at else None,
            "archived_by": self.archived_by
        }
    
    def get_change_summary(self, compared_to_version: 'ReportAttribute' = None) -> dict:
        """Get summary of changes compared to another version"""
        if not compared_to_version:
            return {"changes": [], "summary": "No comparison version provided"}
        
        changes = []
        
        # Compare key fields
        fields_to_compare = [
            'attribute_name', 'description', 'data_type', 'mandatory_flag',
            'cde_flag', 'historical_issues_flag', 'is_scoped', 'tester_notes',
            'line_item_number', 'technical_line_item_name', 'mdrm',
            'validation_rules', 'typical_source_documents', 'keywords_to_look_for',
            'testing_approach', 'risk_score', 'llm_risk_rationale',
            'is_primary_key', 'primary_key_order'
        ]
        
        for field in fields_to_compare:
            old_value = getattr(compared_to_version, field)
            new_value = getattr(self, field)
            
            if old_value != new_value:
                changes.append({
                    "field": field,
                    "old_value": old_value,
                    "new_value": new_value
                })
        
        return {
            "changes": changes,
            "summary": f"{len(changes)} field(s) changed from version {compared_to_version.version_number} to {self.version_number}"
        }
    
    def __repr__(self):
        return f"<ReportAttribute(id={self.attribute_id}, name='{self.attribute_name}', v{self.version_number}, status='{self.approval_status}')>"


class AttributeVersionChangeLog(CustomPKModel, AuditMixin):
    """Log of all changes made to attribute versions"""
    
    __tablename__ = "attribute_version_change_logs"
    
    log_id = Column(Integer, primary_key=True, index=True)
    attribute_id = Column(Integer, ForeignKey("cycle_report_planning_attributes.id"), nullable=False)
    
    # Change information
    change_type = Column(version_change_type_enum, nullable=False)  # created, updated, approved, rejected, archived, restored
    version_number = Column(Integer, nullable=False)
    change_notes = Column(Text, nullable=True)
    
    # Change metadata
    changed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    changed_by = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    
    # Additional context
    field_changes = Column(Text, nullable=True)  # JSON string of specific field changes
    impact_assessment = Column(Text, nullable=True)  # Assessment of change impact
    
    # Relationships
    attribute = relationship("ReportAttribute", back_populates="version_changes")
    changed_by_user = relationship("User", foreign_keys=[changed_by])
    
    def __repr__(self):
        return f"<AttributeVersionChangeLog(id={self.log_id}, attr={self.attribute_id}, type='{self.change_type}', v{self.version_number})>"


class AttributeVersionComparison(CustomPKModel, AuditMixin):
    """Store comparisons between different versions of attributes"""
    
    __tablename__ = "attribute_version_comparisons"
    
    comparison_id = Column(Integer, primary_key=True, index=True)
    
    # Versions being compared
    version_a_id = Column(Integer, ForeignKey("cycle_report_planning_attributes.id"), nullable=False)
    version_b_id = Column(Integer, ForeignKey("cycle_report_planning_attributes.id"), nullable=False)
    
    # Comparison results
    differences_found = Column(Integer, nullable=False, default=0)
    comparison_summary = Column(Text, nullable=True)  # JSON string of differences
    impact_score = Column(Float, nullable=True)  # 0-10 score of impact of changes
    
    # Comparison metadata
    compared_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    compared_by = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    comparison_notes = Column(Text, nullable=True)
    
    # Relationships
    version_a = relationship("ReportAttribute", foreign_keys=[version_a_id])
    version_b = relationship("ReportAttribute", foreign_keys=[version_b_id])
    compared_by_user = relationship("User", foreign_keys=[compared_by])
    
    def __repr__(self):
        return f"<AttributeVersionComparison(id={self.comparison_id}, versions={self.version_a_id}-{self.version_b_id}, diffs={self.differences_found})>" 