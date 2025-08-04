"""
Authentication DTOs
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserLoginDTO(BaseModel):
    """DTO for user login"""
    email: EmailStr
    password: str


class UserRegistrationDTO(BaseModel):
    """DTO for user registration"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str
    last_name: str
    role: Optional[str] = "Tester"


class UserResponseDTO(BaseModel):
    """DTO for user response"""
    user_id: int
    email: str
    first_name: str
    last_name: str
    role: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class TokenResponseDTO(BaseModel):
    """DTO for token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: Optional[UserResponseDTO] = None


class PasswordChangeDTO(BaseModel):
    """DTO for password change"""
    old_password: str
    new_password: str = Field(..., min_length=8)