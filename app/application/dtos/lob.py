"""
Line of Business DTOs
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class LOBDTO(BaseModel):
    """DTO for line of business data"""
    lob_id: int
    lob_name: str
    lob_code: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class LOBCreateDTO(BaseModel):
    """DTO for creating a line of business"""
    lob_name: str = Field(..., min_length=1, max_length=100)
    lob_code: str = Field(..., min_length=1, max_length=20)
    description: Optional[str] = None


class LOBUpdateDTO(BaseModel):
    """DTO for updating a line of business"""
    lob_name: Optional[str] = Field(None, min_length=1, max_length=100)
    lob_code: Optional[str] = Field(None, min_length=1, max_length=20)
    description: Optional[str] = None
    is_active: Optional[bool] = None