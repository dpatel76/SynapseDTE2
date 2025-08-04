"""
RBAC (Role-Based Access Control) models
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import CustomPKModel
from app.models.audit_mixin import AuditMixin


class Permission(CustomPKModel, AuditMixin):
    """Permission model - defines what actions can be performed on resources"""
    
    __tablename__ = "rbac_permissions"
    
    permission_id = Column(Integer, primary_key=True, index=True)
    resource = Column(String(100), nullable=False, index=True)
    action = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Relationships
    role_permissions = relationship("RolePermission", back_populates="permission")
    user_permissions = relationship("UserPermission", back_populates="permission")
    resource_permissions = relationship("ResourcePermission", back_populates="permission")
    
    __table_args__ = (
        UniqueConstraint('resource', 'action', name='uq_resource_action'),
    )
    
    def __repr__(self):
        return f"<Permission(id={self.permission_id}, permission='{self.resource}:{self.action}')>"
    
    @property
    def permission_string(self):
        return f"{self.resource}:{self.action}"


class Role(CustomPKModel, AuditMixin):
    """Role model - groups of permissions"""
    
    __tablename__ = "rbac_roles"
    
    role_id = Column(Integer, primary_key=True, index=True)
    role_name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_system = Column(Boolean, default=False, nullable=False)  # System roles cannot be deleted
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    role_permissions = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")
    user_roles = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")
    parent_roles = relationship(
        "RoleHierarchy",
        foreign_keys="RoleHierarchy.child_role_id",
        back_populates="child_role"
    )
    child_roles = relationship(
        "RoleHierarchy",
        foreign_keys="RoleHierarchy.parent_role_id",
        back_populates="parent_role"
    )
    
    @property
    def permissions(self):
        """Get list of permissions for this role (for schema compatibility)"""
        if hasattr(self, 'role_permissions') and self.role_permissions:
            return [rp.permission for rp in self.role_permissions]
        return []
    
    def __repr__(self):
        return f"<Role(id={self.role_id}, name='{self.role_name}')>"


class RolePermission(CustomPKModel, AuditMixin):
    """Many-to-many relationship between roles and permissions"""
    
    __tablename__ = "rbac_role_permissions"
    
    role_id = Column(Integer, ForeignKey('rbac_roles.role_id', ondelete='CASCADE'), primary_key=True)
    permission_id = Column(Integer, ForeignKey('rbac_permissions.permission_id', ondelete='CASCADE'), primary_key=True)
    granted_by = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    granted_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Relationships
    role = relationship("Role", back_populates="role_permissions")
    permission = relationship("Permission", back_populates="role_permissions")
    granter = relationship("User", foreign_keys=[granted_by])
    
    def __repr__(self):
        return f"<RolePermission(role_id={self.role_id}, permission_id={self.permission_id})>"


class UserRole(CustomPKModel, AuditMixin):
    """Many-to-many relationship between users and roles"""
    
    __tablename__ = "rbac_user_roles"
    
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey('rbac_roles.role_id', ondelete='CASCADE'), primary_key=True)
    assigned_by = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    assigned_at = Column(DateTime, server_default=func.now(), nullable=False)
    expires_at = Column(DateTime, nullable=True, index=True)  # For temporary role assignments
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles")
    assigner = relationship("User", foreign_keys=[assigned_by])
    
    def __repr__(self):
        return f"<UserRole(user_id={self.user_id}, role_id={self.role_id})>"


class UserPermission(CustomPKModel, AuditMixin):
    """Direct permissions for users (overrides role permissions)"""
    
    __tablename__ = "rbac_user_permissions"
    
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), primary_key=True, index=True)
    permission_id = Column(Integer, ForeignKey('rbac_permissions.permission_id', ondelete='CASCADE'), primary_key=True)
    granted = Column(Boolean, default=True, nullable=False)  # Can be used to explicitly deny
    granted_by = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    granted_at = Column(DateTime, server_default=func.now(), nullable=False)
    expires_at = Column(DateTime, nullable=True, index=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="user_permissions")
    permission = relationship("Permission", back_populates="user_permissions")
    granter = relationship("User", foreign_keys=[granted_by])
    
    def __repr__(self):
        return f"<UserPermission(user_id={self.user_id}, permission_id={self.permission_id}, granted={self.granted})>"


class ResourcePermission(CustomPKModel, AuditMixin):
    """Resource-level permissions (e.g., access to specific reports)"""
    
    __tablename__ = "rbac_resource_permissions"
    
    resource_permission_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False, index=True)  # e.g., 'report', 'cycle', 'lob'
    resource_id = Column(Integer, nullable=False, index=True)
    permission_id = Column(Integer, ForeignKey('rbac_permissions.permission_id', ondelete='CASCADE'), nullable=False)
    granted = Column(Boolean, default=True, nullable=False)
    granted_by = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    granted_at = Column(DateTime, server_default=func.now(), nullable=False)
    expires_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="resource_permissions")
    permission = relationship("Permission", back_populates="resource_permissions")
    granter = relationship("User", foreign_keys=[granted_by])
    
    __table_args__ = (
        UniqueConstraint('user_id', 'resource_type', 'resource_id', 'permission_id', 
                        name='uq_user_resource_permission'),
    )
    
    def __repr__(self):
        return f"<ResourcePermission(user_id={self.user_id}, {self.resource_type}:{self.resource_id}, permission_id={self.permission_id})>"


class RoleHierarchy(CustomPKModel, AuditMixin):
    """Role inheritance hierarchy"""
    
    __tablename__ = "rbac_role_hierarchy"
    
    parent_role_id = Column(Integer, ForeignKey('rbac_roles.role_id', ondelete='CASCADE'), primary_key=True)
    child_role_id = Column(Integer, ForeignKey('rbac_roles.role_id', ondelete='CASCADE'), primary_key=True)
    
    # Relationships
    parent_role = relationship("Role", foreign_keys=[parent_role_id], back_populates="child_roles")
    child_role = relationship("Role", foreign_keys=[child_role_id], back_populates="parent_roles")
    
    def __repr__(self):
        return f"<RoleHierarchy(parent={self.parent_role_id}, child={self.child_role_id})>"


class PermissionAuditLog(CustomPKModel, AuditMixin):
    """Audit log for permission changes"""
    
    __tablename__ = "rbac_permission_audit_logs"
    
    audit_id = Column(Integer, primary_key=True, index=True)
    action_type = Column(String(50), nullable=False)  # 'grant', 'revoke', 'expire'
    target_type = Column(String(50), nullable=False, index=True)  # 'user', 'role'
    target_id = Column(Integer, nullable=False, index=True)
    permission_id = Column(Integer, ForeignKey('rbac_permissions.permission_id'), nullable=True)
    role_id = Column(Integer, ForeignKey('rbac_roles.role_id'), nullable=True)
    performed_by = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    performed_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    reason = Column(Text, nullable=True)
    
    # Relationships
    permission = relationship("Permission")
    role = relationship("Role")
    performer = relationship("User", foreign_keys=[performed_by])
    
    def __repr__(self):
        return f"<PermissionAuditLog(id={self.audit_id}, action='{self.action_type}', target='{self.target_type}:{self.target_id}')>"