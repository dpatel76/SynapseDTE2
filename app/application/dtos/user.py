"""
User DTOs
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserDTO(BaseModel):
    """DTO for user data"""
    user_id: int
    email: str
    first_name: str
    last_name: str
    role: str
    lob_id: Optional[int] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserCreateDTO(BaseModel):
    """DTO for creating a user"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str
    last_name: str
    role: str
    lob_id: Optional[int] = None


class UserUpdateDTO(BaseModel):
    """DTO for updating a user"""
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[str] = None
    lob_id: Optional[int] = None
    is_active: Optional[bool] = None


class UserListResponseDTO(BaseModel):
    """DTO for user list response"""
    users: list[UserDTO]
    total: int
    skip: int = 0
    limit: int = 100