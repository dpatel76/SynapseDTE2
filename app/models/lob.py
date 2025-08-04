"""
Lines of Business (LOB) model
"""

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import AuditableCustomPKModel


class LOB(AuditableCustomPKModel):
    """Lines of Business model"""
    
    __tablename__ = "lobs"
    
    lob_id = Column(Integer, primary_key=True, index=True)
    lob_name = Column(String(255), nullable=False, unique=True, index=True)
    
    # Relationships
    users = relationship(
        "User", 
        primaryjoin="LOB.lob_id == User.lob_id",
        back_populates="lob",
        viewonly=False
    )
    reports = relationship("Report", back_populates="lob")
    # data_owner_assignments = relationship("DataOwnerAssignment", back_populates="lob")  # Deprecated - using universal assignments
    
    # Data provider phase relationships - removed (table doesn't exist)
    # attribute_assignments removed - table doesn't exist
    # data_executive_notifications = relationship("CDONotification", back_populates="lob")  # Deprecated
    
    def __repr__(self):
        return f"<LOB(id={self.lob_id}, name='{self.lob_name}')>" 