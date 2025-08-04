"""
Regulatory Data Dictionary model for storing standard regulatory reporting attributes
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, Index
from app.models.base import CustomPKModel
from app.models.audit_mixin import AuditMixin
from app.core.logging import get_logger

logger = get_logger(__name__)


class RegulatoryDataDictionary(CustomPKModel, AuditMixin):
    """Model for storing regulatory data dictionary entries"""
    
    __tablename__ = "regulatory_data_dictionaries"
    
    dict_id = Column(Integer, primary_key=True, index=True)
    
    # Core dictionary fields from FR Y-14M
    report_name = Column(String(255), nullable=False, index=True)
    schedule_name = Column(String(255), nullable=False, index=True)
    line_item_number = Column(String(50), nullable=True)
    line_item_name = Column(String(500), nullable=False, index=True)
    technical_line_item_name = Column(String(500), nullable=True)
    mdrm = Column(String(50), nullable=True)  # Master Data Reference Model
    description = Column(Text, nullable=True)
    static_or_dynamic = Column(String(20), nullable=True)
    mandatory_or_optional = Column(String(20), nullable=True, index=True)
    format_specification = Column(String(200), nullable=True)
    num_reports_schedules_used = Column(String(50), nullable=True)
    other_schedule_reference = Column(Text, nullable=True)
    
    # Additional fields for enhanced search and filtering
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Composite indexes for common search patterns
    __table_args__ = (
        Index('ix_rdd_report_schedule', 'report_name', 'schedule_name'),
        Index('ix_rdd_item_name_search', 'line_item_name'),
        Index('ix_rdd_mandatory_search', 'mandatory_or_optional'),
    )
    
    def __repr__(self):
        return f"<RegulatoryDataDictionary(id={self.dict_id}, report={self.report_name}, item={self.line_item_name})>"
    
    def to_dict(self):
        """Convert to dictionary for easy serialization"""
        return {
            'dict_id': self.dict_id,
            'report_name': self.report_name,
            'schedule_name': self.schedule_name,
            'line_item_number': self.line_item_number,
            'line_item_name': self.line_item_name,
            'technical_line_item_name': self.technical_line_item_name,
            'mdrm': self.mdrm,
            'description': self.description,
            'static_or_dynamic': self.static_or_dynamic,
            'mandatory_or_optional': self.mandatory_or_optional,
            'format_specification': self.format_specification,
            'num_reports_schedules_used': self.num_reports_schedules_used,
            'other_schedule_reference': self.other_schedule_reference,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 