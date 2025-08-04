"""Cycle Report Planning Phase models"""

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, Enum as SQLEnum, UniqueConstraint, DateTime, ForeignKeyConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import BaseModel
from app.models.audit_mixin import AuditMixin
import enum


class SecurityClassificationEnum(str, enum.Enum):
    PUBLIC = "Public"
    INTERNAL = "Internal"
    CONFIDENTIAL = "Confidential"
    RESTRICTED = "Restricted"
    HRCI = "HRCI"


# NOTE: This model is now replaced by ReportAttribute in report_attribute.py
# which uses the same table name "cycle_report_planning_attributes"
# Commenting out to avoid duplicate table definition
"""
class CycleReportAttributesPlanning(BaseModel, AuditMixin):
    Planning phase attributes for cycle reports
    
    __tablename__ = "cycle_report_planning_attributes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign keys to cycle_reports composite key
    cycle_id = Column(Integer, nullable=False)
    report_id = Column(Integer, nullable=False)
    
    # Attribute details
    attribute_name = Column(String(255), nullable=False)
    description = Column(Text)
    data_type = Column(String(50), nullable=False)  # Using existing data_type_enum
    is_mandatory = Column(Boolean, default=False)
    is_cde = Column(Boolean, default=False)
    has_issues = Column(Boolean, default=False)
    is_primary_key = Column(Boolean, default=False)
    information_security_classification = Column(
        SQLEnum(SecurityClassificationEnum, values_callable=lambda x: [e.value for e in x]),
        default=SecurityClassificationEnum.INTERNAL
    )
    
    # Data source mapping - stored directly in this table
    data_source_name = Column(String(255))
    data_source_type = Column(String(50))  # e.g., 'database', 'file', 'api'
    source_table = Column(String(255))
    source_column = Column(String(255))
    source_connection_details = Column(Text)  # JSON or connection string
    
    # Versioning
    version = Column(Integer, default=1)
    status = Column(String(50), default="Not Started")  # Using existing phase_status_enum
    
    # Approval tracking
    approved_by = Column(Integer, ForeignKey("users.user_id"))
    approved_at = Column(DateTime(timezone=True))
    
    # Constraints
    __table_args__ = (
        ForeignKeyConstraint(
            ["cycle_id", "report_id"],
            ["cycle_reports.cycle_id", "cycle_reports.report_id"]
        ),
        UniqueConstraint("cycle_id", "report_id", "attribute_name", "version"),
    )
    
    # Relationships
    # Temporarily disabled - data_sources_v2 table is not being used
    # data_source = relationship("DataSource", backref="planning_attributes")
    approved_by_user = relationship(
        "User",
        foreign_keys=[approved_by],
        backref="approved_planning_attributes"
    )
    # created_by and updated_by relationships are already defined in AuditMixin
    
    def to_dict(self):
        Convert to dictionary for API responses
        return {
            "id": self.id,
            "cycle_id": self.cycle_id,
            "report_id": self.report_id,
            "attribute_name": self.attribute_name,
            "description": self.description,
            "data_type": self.data_type,
            "is_mandatory": self.is_mandatory,
            "is_cde": self.is_cde,
            "has_issues": self.has_issues,
            "is_primary_key": self.is_primary_key,
            "information_security_classification": self.information_security_classification.value if self.information_security_classification else None,
            "data_source_name": self.data_source_name,
            "data_source_type": self.data_source_type,
            "source_table": self.source_table,
            "source_column": self.source_column,
            "source_connection_details": self.source_connection_details,
            "version": self.version,
            "status": self.status,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f"<CycleReportAttributesPlanning {self.attribute_name} v{self.version}>"
"""


class CycleReportPlanningAttributeVersionHistory(BaseModel):
    """Version history for planning attributes"""
    
    __tablename__ = "cycle_report_planning_attribute_version_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    planning_attribute_id = Column(Integer, nullable=False)
    cycle_id = Column(Integer, nullable=False)
    report_id = Column(Integer, nullable=False)
    attribute_name = Column(String(255), nullable=False)
    description = Column(Text)
    data_type = Column(String(50), nullable=False)
    is_mandatory = Column(Boolean)
    is_cde = Column(Boolean)
    has_issues = Column(Boolean)
    is_primary_key = Column(Boolean)
    information_security_classification = Column(
        SQLEnum(SecurityClassificationEnum, values_callable=lambda x: [e.value for e in x])
    )
    data_source_id = Column(Integer)
    source_table = Column(String(255))
    source_column = Column(String(255))
    version = Column(Integer, nullable=False)
    change_reason = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.user_id"))
    
    # Relationships
    created_by_user = relationship(
        "User",
        foreign_keys=[created_by],
        backref="created_planning_version_history"
    )
    
    def __repr__(self):
        return f"<PlanningVersionHistory {self.attribute_name} v{self.version}>"