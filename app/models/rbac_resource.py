"""
RBAC Resource model - defines what can be protected
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import CustomPKModel
from app.models.audit_mixin import AuditMixin


class Resource(CustomPKModel, AuditMixin):
    """Resource model - defines what can be protected by permissions"""
    
    __tablename__ = "rbac_resources"
    
    resource_id = Column(Integer, primary_key=True, index=True)
    resource_name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    resource_type = Column(String(50), nullable=False, index=True)  # 'module', 'entity', 'workflow', 'system'
    parent_resource_id = Column(Integer, ForeignKey('rbac_resources.resource_id'), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    parent = relationship("Resource", remote_side=[resource_id], backref="children")
    
    def __repr__(self):
        return f"<Resource(id={self.resource_id}, name='{self.resource_name}', type='{self.resource_type}')>"
    
    @property
    def full_path(self):
        """Get full resource path including parents"""
        if self.parent:
            return f"{self.parent.full_path}.{self.resource_name}"
        return self.resource_name