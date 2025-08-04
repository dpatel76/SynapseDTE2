"""
Schemas for RBAC (Role-Based Access Control)
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# Permission Schemas

class PermissionBase(BaseModel):
    """Base permission schema"""
    resource: str = Field(..., max_length=100, description="Resource name")
    action: str = Field(..., max_length=50, description="Action name")
    description: Optional[str] = Field(None, description="Permission description")


class PermissionCreate(PermissionBase):
    """Schema for creating permission"""
    pass


class PermissionSchema(PermissionBase):
    """Schema for permission response"""
    permission_id: int = Field(..., description="Permission ID")
    permission_string: str = Field(..., description="Permission string (resource:action)")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


# Role Schemas

class RoleBase(BaseModel):
    """Base role schema"""
    role_name: str = Field(..., max_length=100, description="Role name")
    description: Optional[str] = Field(None, description="Role description")


class RoleCreate(RoleBase):
    """Schema for creating role"""
    is_system: bool = Field(default=False, description="Is system role")


class RoleUpdate(BaseModel):
    """Schema for updating role"""
    role_name: Optional[str] = Field(None, max_length=100, description="Role name")
    description: Optional[str] = Field(None, description="Role description")
    is_active: Optional[bool] = Field(None, description="Is active")


class RoleSchema(RoleBase):
    """Schema for role response"""
    role_id: int = Field(..., description="Role ID")
    is_system: bool = Field(..., description="Is system role")
    is_active: bool = Field(..., description="Is active")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    permissions: Optional[List[PermissionSchema]] = Field(None, description="Role permissions")
    user_count: Optional[int] = Field(None, description="Number of users with this role")
    
    model_config = ConfigDict(from_attributes=True)


# User Role/Permission Schemas

class UserRoleAssignment(BaseModel):
    """Schema for assigning role to user"""
    role_id: int = Field(..., description="Role ID")
    expires_at: Optional[datetime] = Field(None, description="Expiration date")


class UserPermissionGrant(BaseModel):
    """Schema for granting permission to user"""
    permission_id: int = Field(..., description="Permission ID")
    expires_at: Optional[datetime] = Field(None, description="Expiration date")


class ResourcePermissionGrant(BaseModel):
    """Schema for granting resource-level permission"""
    user_id: int = Field(..., description="User ID")
    resource_type: str = Field(..., max_length=50, description="Resource type (e.g., 'report', 'cycle')")
    resource_id: int = Field(..., description="Resource ID")
    permission_id: int = Field(..., description="Permission ID")
    expires_at: Optional[datetime] = Field(None, description="Expiration date")


class RolePermissionsUpdate(BaseModel):
    """Schema for updating all permissions for a role"""
    permission_ids: List[int] = Field(..., description="List of permission IDs")


# Response Schemas

class UserRoleSchema(BaseModel):
    """Schema for user role assignment"""
    role: RoleSchema = Field(..., description="Role details")
    assigned_at: datetime = Field(..., description="Assignment date")
    assigned_by: Optional[int] = Field(None, description="Assigned by user ID")
    expires_at: Optional[datetime] = Field(None, description="Expiration date")
    
    model_config = ConfigDict(from_attributes=True)


class UserPermissionSchema(BaseModel):
    """Schema for user permission"""
    permission: PermissionSchema = Field(..., description="Permission details")
    granted: bool = Field(..., description="Is granted")
    granted_at: datetime = Field(..., description="Grant date")
    granted_by: Optional[int] = Field(None, description="Granted by user ID")
    expires_at: Optional[datetime] = Field(None, description="Expiration date")
    
    model_config = ConfigDict(from_attributes=True)


class UserPermissionsResponse(BaseModel):
    """Schema for user permissions response"""
    user_id: int = Field(..., description="User ID")
    all_permissions: List[str] = Field(..., description="All effective permissions")
    direct_permissions: List[str] = Field(..., description="Direct user permissions")
    roles: List[RoleSchema] = Field(..., description="User roles")


# Audit Log Schema

class PermissionAuditSchema(BaseModel):
    """Schema for permission audit log"""
    audit_id: int = Field(..., description="Audit ID")
    action_type: str = Field(..., description="Action type (grant/revoke/expire)")
    target_type: str = Field(..., description="Target type (user/role)")
    target_id: int = Field(..., description="Target ID")
    permission: Optional[PermissionSchema] = Field(None, description="Permission details")
    role: Optional[RoleSchema] = Field(None, description="Role details")
    performed_by: Optional[int] = Field(None, description="Performed by user ID")
    performed_at: datetime = Field(..., description="Action timestamp")
    reason: Optional[str] = Field(None, description="Reason for action")
    
    model_config = ConfigDict(from_attributes=True)


# Bulk Operations

class BulkRoleAssignment(BaseModel):
    """Schema for bulk role assignment"""
    user_ids: List[int] = Field(..., description="List of user IDs")
    role_id: int = Field(..., description="Role ID to assign")
    expires_at: Optional[datetime] = Field(None, description="Expiration date")


class BulkPermissionGrant(BaseModel):
    """Schema for bulk permission grant"""
    user_ids: List[int] = Field(..., description="List of user IDs")
    permission_ids: List[int] = Field(..., description="List of permission IDs")
    expires_at: Optional[datetime] = Field(None, description="Expiration date")