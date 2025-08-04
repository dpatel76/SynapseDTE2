"""Report Inventory model - master list of all reports"""

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import CustomPKModel
from app.models.audit_mixin import AuditMixin
import enum


class ReportStatusEnum(str, enum.Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    UNDER_REVIEW = "Under Review"
    ARCHIVED = "Archived"


class ReportInventory(CustomPKModel, AuditMixin):
    """Master list of all reports in the organization"""
    
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    report_number = Column(String(50), unique=True, nullable=False, index=True)
    report_name = Column(String(255), nullable=False)
    description = Column(Text)
    frequency = Column(String(50))  # Monthly, Quarterly, Annual
    business_unit = Column(String(100))
    regulatory_requirement = Column(Boolean, default=False)
    status = Column(
        SQLEnum(ReportStatusEnum, values_callable=lambda x: [e.value for e in x]),
        default=ReportStatusEnum.ACTIVE,
        nullable=False
    )
    
    # Relationships are already defined in AuditMixin
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "report_number": self.report_number,
            "report_name": self.report_name,
            "description": self.description,
            "frequency": self.frequency,
            "business_unit": self.business_unit,
            "regulatory_requirement": self.regulatory_requirement,
            "status": self.status.value if self.status else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by_id,
            "updated_by": self.updated_by_id
        }
    
    def __repr__(self):
        return f"<ReportInventory {self.report_number}: {self.report_name}>"