"""
Authentication-related Pydantic schemas
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator
from app.core.auth import validate_password_strength


class LoginRequest(BaseModel):
    """Login request schema"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=1, description="User password")


class TokenUser(BaseModel):
    """User data in token response"""
    user_id: int = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    first_name: str = Field(..., description="User first name")
    last_name: str = Field(..., description="User last name")
    role: str = Field(..., description="User role")
    lob_id: Optional[int] = Field(None, description="User's LOB ID")


class TokenResponse(BaseModel):
    """Token response schema"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user: TokenUser = Field(..., description="User information")


class PasswordChangeRequest(BaseModel):
    """Password change request schema"""
    current_password: str = Field(..., min_length=1, description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    confirm_password: str = Field(..., min_length=8, description="Confirm new password")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v
    
    @validator('new_password')
    def validate_password(cls, v):
        if not validate_password_strength(v):
            raise ValueError(
                'Password must meet security requirements: '
                'minimum 8 characters, uppercase, lowercase, number, and special character'
            )
        return v


class UserRegistrationRequest(BaseModel):
    """User registration request schema"""
    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Last name")
    email: EmailStr = Field(..., description="Email address")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    password: str = Field(..., min_length=8, description="Password")
    confirm_password: str = Field(..., min_length=8, description="Confirm password")
    role: str = Field(..., description="User role")
    lob_id: Optional[int] = Field(None, description="LOB ID (required for most roles)")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v
    
    @validator('password')
    def validate_password(cls, v):
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


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema"""
    refresh_token: str = Field(..., description="Refresh token")


class LogoutRequest(BaseModel):
    """Logout request schema"""
    token: str = Field(..., description="Access token to invalidate")


class AuthResponse(BaseModel):
    """Generic authentication response"""
    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Response message")
    data: Optional[dict] = Field(None, description="Additional response data") 