"""
Data Source management schemas
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator, ConfigDict


class DataSourceBase(BaseModel):
    """Base data source schema"""
    data_source_name: str = Field(..., min_length=1, max_length=255, description="Name of the data source")
    database_type: str = Field(..., description="Type of database (PostgreSQL, MySQL, Oracle, SQL Server)")
    database_url: str = Field(..., description="Database connection URL")
    database_user: str = Field(..., min_length=1, max_length=255, description="Database username")
    description: Optional[str] = Field(None, max_length=500, description="Optional description")
    is_active: bool = Field(True, description="Whether the data source is active")

    @validator('database_type')
    def validate_database_type(cls, v):
        allowed_types = ['PostgreSQL', 'MySQL', 'Oracle', 'SQL Server', 'SQLite']
        if v not in allowed_types:
            raise ValueError(f"Database type must be one of: {', '.join(allowed_types)}")
        return v


class DataSourceCreate(DataSourceBase):
    """Schema for creating a new data source"""
    database_password: str = Field(..., min_length=1, description="Database password (will be encrypted)")


class DataSourceUpdate(BaseModel):
    """Schema for updating a data source"""
    data_source_name: Optional[str] = Field(None, min_length=1, max_length=255)
    database_type: Optional[str] = Field(None)
    database_url: Optional[str] = Field(None)
    database_user: Optional[str] = Field(None, min_length=1, max_length=255)
    database_password: Optional[str] = Field(None, min_length=1, description="New password (will be encrypted)")
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = Field(None)

    @validator('database_type')
    def validate_database_type(cls, v):
        if v is not None:
            allowed_types = ['PostgreSQL', 'MySQL', 'Oracle', 'SQL Server', 'SQLite']
            if v not in allowed_types:
                raise ValueError(f"Database type must be one of: {', '.join(allowed_types)}")
        return v


class DataSourceResponse(BaseModel):
    """Schema for data source response"""
    data_source_id: int
    data_source_name: str
    database_type: str
    database_url: str
    database_user: str
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DataSourceListResponse(BaseModel):
    """Schema for data source list response"""
    data_sources: List[DataSourceResponse]
    total: int
    skip: int
    limit: int


class DataSourceTestResponse(BaseModel):
    """Schema for data source connection test response"""
    success: bool
    message: str
    connection_time_ms: Optional[int] = None
    error_details: Optional[str] = None


class DataSourceStatsResponse(BaseModel):
    """Schema for data source statistics"""
    total_data_sources: int
    active_data_sources: int
    inactive_data_sources: int
    sources_by_type: dict
    recent_connection_tests: List[dict] 