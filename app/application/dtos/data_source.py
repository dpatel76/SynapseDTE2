from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class DataSourceCreateDTO(BaseModel):
    """DTO for creating a new data source"""
    data_source_name: str = Field(..., min_length=1, max_length=255, description="Name of the data source")
    database_type: str = Field(..., description="Type of database (PostgreSQL, MySQL, Oracle, SQL Server)")
    database_url: str = Field(..., description="Database connection URL")
    database_user: str = Field(..., min_length=1, max_length=255, description="Database username")
    database_password: str = Field(..., min_length=1, description="Database password (will be encrypted)")
    description: Optional[str] = Field(None, max_length=500, description="Optional description")
    is_active: bool = Field(True, description="Whether the data source is active")

    @field_validator('database_type')
    def validate_database_type(cls, v):
        allowed_types = ['PostgreSQL', 'MySQL', 'Oracle', 'SQL Server', 'SQLite']
        if v not in allowed_types:
            raise ValueError(f"Database type must be one of: {', '.join(allowed_types)}")
        return v


class DataSourceUpdateDTO(BaseModel):
    """DTO for updating a data source"""
    data_source_name: Optional[str] = Field(None, min_length=1, max_length=255)
    database_type: Optional[str] = Field(None)
    database_url: Optional[str] = Field(None)
    database_user: Optional[str] = Field(None, min_length=1, max_length=255)
    database_password: Optional[str] = Field(None, min_length=1, description="New password (will be encrypted)")
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = Field(None)

    @field_validator('database_type')
    def validate_database_type(cls, v):
        if v is not None:
            allowed_types = ['PostgreSQL', 'MySQL', 'Oracle', 'SQL Server', 'SQLite']
            if v not in allowed_types:
                raise ValueError(f"Database type must be one of: {', '.join(allowed_types)}")
        return v


class DataSourceDTO(BaseModel):
    """DTO for data source response"""
    data_source_id: int
    data_source_name: str
    database_type: str
    database_url: str
    database_user: str
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DataSourceFilterDTO(BaseModel):
    """DTO for filtering data sources"""
    skip: int = 0
    limit: int = 100
    search: Optional[str] = None
    database_type: Optional[str] = None
    is_active: Optional[bool] = None


class DataSourceListDTO(BaseModel):
    """DTO for data source list response"""
    data_sources: List[DataSourceDTO]
    total: int
    skip: int
    limit: int


class DataSourceTestResultDTO(BaseModel):
    """DTO for data source connection test result"""
    success: bool
    message: str
    connection_time_ms: Optional[int] = None
    error_details: Optional[str] = None


class DataSourceStatsDTO(BaseModel):
    """DTO for data source statistics"""
    total_data_sources: int
    active_data_sources: int
    inactive_data_sources: int
    sources_by_type: Dict[str, int]
    recent_connection_tests: List[Dict[str, Any]]