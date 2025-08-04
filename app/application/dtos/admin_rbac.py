"""DTOs for RBAC Administration."""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator


# Permission DTOs
class PermissionDTO(BaseModel):
    """DTO for permission information."""
    permission_id: int
    resource: str
    action: str
    description: Optional[str]
    permission_string: str
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        orm_mode = True


class CreatePermissionDTO(BaseModel):
    """DTO for creating a new permission."""
    resource: str = Field(..., description="Resource name (e.g., 'reports', 'users')")
    action: str = Field(..., description="Action name (e.g., 'read', 'write', 'delete')")
    description: Optional[str] = Field(None, description="Permission description")
    
    @validator('resource', 'action')
    def validate_names(cls, v):
        if not v or not v.strip():
            raise ValueError("Resource and action must not be empty")
        return v.strip().lower()


# Role DTOs
class RoleDTO(BaseModel):
    """DTO for role information."""
    role_id: int
    role_name: str
    description: Optional[str]
    is_system: bool
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    permissions: Optional[List[PermissionDTO]] = None
    user_count: Optional[int] = None
    
    class Config:
        orm_mode = True


class CreateRoleDTO(BaseModel):
    """DTO for creating a new role."""
    role_name: str = Field(..., description="Unique role name")
    description: Optional[str] = Field(None, description="Role description")
    is_system: bool = Field(default=False, description="Whether this is a system role")
    is_active: bool = Field(default=True, description="Whether the role is active")
    
    @validator('role_name')
    def validate_role_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Role name must not be empty")
        return v.strip()


class UpdateRoleDTO(BaseModel):
    """DTO for updating a role."""
    role_name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


# Role Permission Management DTOs
class RolePermissionRestrictionsDTO(BaseModel):
    """DTO for role permission restrictions."""
    role_name: str
    role_description: str
    total_permissions: int
    allowed_count: int
    forbidden_count: int
    allowed_permissions: List[str]
    forbidden_permissions: List[str]


class UpdateRolePermissionsDTO(BaseModel):
    """DTO for updating all permissions for a role."""
    permission_ids: List[int] = Field(..., description="List of permission IDs to assign to the role")


# User Permission Management DTOs
class UserRoleAssignmentDTO(BaseModel):
    """DTO for assigning a role to a user."""
    role_id: int = Field(..., description="Role ID to assign")
    expires_at: Optional[datetime] = Field(None, description="Optional expiration date for the role assignment")


class UserPermissionGrantDTO(BaseModel):
    """DTO for granting a permission directly to a user."""
    permission_id: int = Field(..., description="Permission ID to grant")
    expires_at: Optional[datetime] = Field(None, description="Optional expiration date for the permission")


class UserPermissionsResponseDTO(BaseModel):
    """DTO for user permissions response."""
    user_id: int
    all_permissions: List[str]
    direct_permissions: List[str]
    roles: List[Dict[str, Any]]


# Resource Permission DTOs
class ResourcePermissionGrantDTO(BaseModel):
    """DTO for granting permission for a specific resource."""
    user_id: int = Field(..., description="User ID to grant permission to")
    resource_type: str = Field(..., description="Type of resource (e.g., 'report', 'cycle')")
    resource_id: int = Field(..., description="ID of the specific resource")
    permission_id: int = Field(..., description="Permission ID to grant")
    expires_at: Optional[datetime] = Field(None, description="Optional expiration date")
    
    @validator('resource_type')
    def validate_resource_type(cls, v):
        allowed_types = ['report', 'cycle', 'lob', 'test_case', 'observation']
        if v not in allowed_types:
            raise ValueError(f"Resource type must be one of: {', '.join(allowed_types)}")
        return v


# Audit Log DTOs
class PermissionAuditLogDTO(BaseModel):
    """DTO for permission audit log entries."""
    audit_id: int
    action_type: str
    target_type: str
    target_id: int
    permission_id: Optional[int]
    role_id: Optional[int]
    performed_by: int
    performed_at: datetime
    metadata: Optional[Dict[str, Any]]
    
    # Related entities (loaded via selectinload)
    permission: Optional[PermissionDTO]
    role: Optional[RoleDTO]
    performer: Optional[Dict[str, Any]]  # Basic user info
    
    class Config:
        orm_mode = True


# Query/Filter DTOs
class PermissionFilterDTO(BaseModel):
    """DTO for filtering permissions."""
    resource: Optional[str] = None
    action: Optional[str] = None
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=100, ge=1, le=1000)


class RoleFilterDTO(BaseModel):
    """DTO for filtering roles."""
    include_permissions: bool = Field(default=False, description="Include permissions for each role")
    include_user_count: bool = Field(default=False, description="Include user count for each role")
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=100, ge=1, le=1000)


class AuditLogFilterDTO(BaseModel):
    """DTO for filtering audit logs."""
    target_type: Optional[str] = None
    target_id: Optional[int] = None
    performed_by: Optional[int] = None
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=100, ge=1, le=1000)


# Response DTOs
class MessageResponseDTO(BaseModel):
    """Generic message response."""
    message: str


class ValidationErrorDTO(BaseModel):
    """DTO for validation errors."""
    field: str
    message: str
    code: str


# Aliases for compatibility with existing code
CreatePermissionRequestDTO = CreatePermissionDTO
CreateRoleRequestDTO = CreateRoleDTO
UpdateRoleRequestDTO = UpdateRoleDTO
UpdateRolePermissionsRequestDTO = UpdateRolePermissionsDTO
AssignRoleToUserRequestDTO = UserRoleAssignmentDTO
GrantPermissionToUserRequestDTO = UserPermissionGrantDTO
GrantResourcePermissionRequestDTO = ResourcePermissionGrantDTO

# List Response DTOs
class PermissionListResponseDTO(BaseModel):
    """Response for permission list."""
    permissions: List[PermissionDTO]
    total_count: int
    filtered_count: int
    skip: int
    limit: int


class RoleListResponseDTO(BaseModel):
    """Response for role list."""
    roles: List[RoleDTO]
    total_count: int
    skip: int
    limit: int


class PermissionAuditLogListResponseDTO(BaseModel):
    """Response for audit log list."""
    logs: List[PermissionAuditLogDTO]
    total_count: int
    skip: int
    limit: int


# Action Response DTOs
class DeletePermissionResponseDTO(MessageResponseDTO):
    """Response for permission deletion."""
    permission_id: int


class DeleteRoleResponseDTO(MessageResponseDTO):
    """Response for role deletion."""
    role_id: int


class GrantRolePermissionResponseDTO(MessageResponseDTO):
    """Response for granting role permission."""
    role_id: int
    permission_id: int


class RevokeRolePermissionResponseDTO(MessageResponseDTO):
    """Response for revoking role permission."""
    role_id: int
    permission_id: int


class AssignRoleToUserResponseDTO(MessageResponseDTO):
    """Response for assigning role to user."""
    user_id: int
    role_id: int


class RemoveRoleFromUserResponseDTO(MessageResponseDTO):
    """Response for removing role from user."""
    user_id: int
    role_id: int


class GrantPermissionToUserResponseDTO(MessageResponseDTO):
    """Response for granting permission to user."""
    user_id: int
    permission_id: int


class GrantResourcePermissionResponseDTO(MessageResponseDTO):
    """Response for granting resource permission."""
    user_id: int
    resource_type: str
    resource_id: int
    permission_id: int


# Aliases for backward compatibility
UserPermissionsDTO = UserPermissionsResponseDTO