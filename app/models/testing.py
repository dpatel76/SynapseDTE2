"""
Testing execution models
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ENUM, JSONB, UUID
from app.models.base import CustomPKModel
from app.models.audit_mixin import AuditMixin

# Test result enum
test_result_enum = ENUM(
    'Pass',
    'Fail',
    'Exception',
    name='test_result_enum'
)

# Data source type enum
data_source_type_enum = ENUM(
    'Document',
    'Database',
    name='data_source_type_enum'
)

# Assignment status enum
assignment_status_enum = ENUM(
    'Assigned',
    'In Progress',
    'Completed',
    'Overdue',
    name='assignment_status_enum'
)

# Observation type enum
observation_type_enum = ENUM(
    'Data Quality',
    'Documentation',
    name='observation_type_enum'
)

# Impact level enum
impact_level_enum = ENUM(
    'Low',
    'Medium',
    'High',
    'Critical',
    name='impact_level_enum'
)

# Sample status enum
sample_status_enum = ENUM(
    'Draft',
    'Submitted',
    'Approved',
    'Rejected',
    name='sample_status_enum'
)

# Observation status enum
observation_status_enum = ENUM(
    'Open',
    'In Review',
    'Approved',
    'Rejected',
    'Resolved',
    name='observation_status_enum'
)


# Sample class removed - now using unified sample selection system
# class Sample(CustomPKModel, AuditMixin):
#     """DEPRECATED: Sample data model - Use SampleSelectionSample from sample_selection_v2 instead"""
#     pass


# DEPRECATED: DataOwnerAssignment - using universal assignments instead
# Table doesn't exist in database
class DataOwnerAssignment(CustomPKModel, AuditMixin):
    """Data owner assignments model"""
    
    __tablename__ = "data_owner_assignments"
    
    assignment_id = Column(Integer, primary_key=True, index=True)
    cycle_id = Column(Integer, ForeignKey('test_cycles.cycle_id'), nullable=False)
    report_id = Column(Integer, ForeignKey('reports.id'), nullable=False)
    phase_id = Column(Integer, ForeignKey('workflow_phases.phase_id'), nullable=False)
    attribute_id = Column(UUID(as_uuid=True), ForeignKey("cycle_report_planning_attributes.id"), nullable=False)
    lob_id = Column(Integer, ForeignKey('lobs.lob_id'), nullable=True)
    cdo_id = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    data_owner_id = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    assigned_by = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    assigned_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(assignment_status_enum, default='Assigned', nullable=False)
    
    # Relationships
    cycle = relationship("TestCycle", back_populates="data_owner_assignments")
    attribute = relationship("ReportAttribute", foreign_keys=[attribute_id])
    lob = relationship("LOB")  # back_populates removed - LOB doesn't have this relationship
    cdo = relationship("User", foreign_keys=[cdo_id])
    data_owner = relationship("User", foreign_keys=[data_owner_id])  # back_populates removed - User doesn't have this relationship
    assigned_by_user = relationship("User", foreign_keys=[assigned_by])  # back_populates removed - User doesn't have this relationship
    
    # Data owner phase relationships
    sla_violations = relationship("DataOwnerSLAViolation", back_populates="assignment")
    
    def __repr__(self):
        return f"<DataOwnerAssignment(id={self.assignment_id}, attribute_id={self.attribute_id})>"


# Observation class has been moved to app.models.observation_enhanced
# This avoids duplicate table definitions and SQLAlchemy conflicts 