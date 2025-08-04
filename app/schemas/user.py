"""
User-related Pydantic schemas
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, validator, field_validator, ConfigDict


class UserBase(BaseModel):
    """Base user schema with common fields"""
    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Last name")
    email: EmailStr = Field(..., description="Email address")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    role: str = Field(..., description="User role")
    lob_id: Optional[int] = Field(None, description="LOB ID")
    is_active: bool = Field(default=True, description="User active status")


class UserCreate(UserBase):
    """Schema for creating a new user"""
    password: str = Field(..., min_length=8, description="Password")
    
    @validator('password')
    def validate_password(cls, v):
        from app.core.auth import validate_password_strength
        if not validate_password_strength(v):
            raise ValueError(
                'Password must meet security requirements: '
                'minimum 8 characters, uppercase, lowercase, number, and special character'
            )
        return v
    
    @validator('role')
    def validate_role(cls, v):
        from app.core.auth import UserRoles
        if v not in UserRoles.all_roles():
            raise ValueError(f'Invalid role. Must be one of: {UserRoles.all_roles()}')
        return v


class UserUpdate(BaseModel):
    """Schema for updating user information"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100, description="First name")
    last_name: Optional[str] = Field(None, min_length=1, max_length=100, description="Last name")
    email: Optional[EmailStr] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    role: Optional[str] = Field(None, description="User role")
    lob_id: Optional[int] = Field(None, description="LOB ID")
    is_active: Optional[bool] = Field(None, description="User active status")
    
    @validator('role')
    def validate_role(cls, v):
        if v is not None:
            from app.core.auth import UserRoles
            if v not in UserRoles.all_roles():
                raise ValueError(f'Invalid role. Must be one of: {UserRoles.all_roles()}')
        return v


class UserRoleUpdate(BaseModel):
    """Schema for updating user role"""
    role: str = Field(..., description="New user role")
    lob_id: Optional[int] = Field(None, description="New LOB ID")
    
    @validator('role')
    def validate_role(cls, v):
        from app.core.auth import UserRoles
        if v not in UserRoles.all_roles():
            raise ValueError(f'Invalid role. Must be one of: {UserRoles.all_roles()}')
        return v


class UserResponse(UserBase):
    """Schema for user response (excludes sensitive data)"""
    user_id: int = Field(..., description="User ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    """Schema for user list response with pagination"""
    users: List[UserResponse] = Field(..., description="List of users")
    total: int = Field(..., description="Total number of users")
    skip: int = Field(..., description="Number of records skipped")
    limit: int = Field(..., description="Number of records returned")


class UserSearchFilters(BaseModel):
    """Schema for user search filters"""
    role: Optional[str] = Field(None, description="Filter by role")
    lob_id: Optional[int] = Field(None, description="Filter by LOB ID")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    search: Optional[str] = Field(None, description="Search in name or email")


class UserProfileResponse(UserResponse):
    """Extended user profile response"""
    lob_name: Optional[str] = Field(None, description="LOB name")
    reports_owned: Optional[int] = Field(None, description="Number of reports owned")
    active_assignments: Optional[int] = Field(None, description="Number of active assignments")


class UserStatsResponse(BaseModel):
    """User statistics response"""
    total_users: int = Field(..., description="Total number of users")
    active_users: int = Field(..., description="Number of active users")
    users_by_role: dict = Field(..., description="User count by role")
    users_by_lob: dict = Field(..., description="User count by LOB")


class UserSearchRequest(BaseModel):
    """User search request schema"""
    query: Optional[str] = Field(None, description="Search query (name or email)")
    role: Optional[str] = Field(None, description="Filter by role")
    lob_id: Optional[int] = Field(None, description="Filter by LOB ID")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    page: int = Field(default=1, ge=1, description="Page number")
    per_page: int = Field(default=20, ge=1, le=100, description="Items per page")
    sort_by: str = Field(default="created_at", description="Sort field")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$", description="Sort order")


class UserActivationRequest(BaseModel):
    """User activation/deactivation request"""
    is_active: bool = Field(..., description="New active status")
    reason: Optional[str] = Field(None, description="Reason for status change")


class UserRoleChangeRequest(BaseModel):
    """User role change request"""
    new_role: str = Field(..., description="New user role")
    new_lob_id: Optional[int] = Field(None, description="New LOB ID (if applicable)")
    reason: str = Field(..., description="Reason for role change")
    
    @validator('new_role')
    def validate_role(cls, v):
        from app.core.auth import UserRoles
        if v not in UserRoles.all_roles():
            raise ValueError(f'Invalid role. Must be one of: {UserRoles.all_roles()}')
        return v 