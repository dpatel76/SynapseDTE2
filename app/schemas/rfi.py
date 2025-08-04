"""
Request for Information (RFI) schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class DataSourceType(str, Enum):
    """Supported data source types"""
    POSTGRESQL = "POSTGRESQL"
    MYSQL = "MYSQL"
    ORACLE = "ORACLE"
    SQLSERVER = "SQLSERVER"
    SNOWFLAKE = "SNOWFLAKE"
    BIGQUERY = "BIGQUERY"
    REDSHIFT = "REDSHIFT"
    FILE = "FILE"


class ConnectionConfig(BaseModel):
    """Database connection configuration"""
    host: str
    port: int
    database: str
    schema_name: Optional[str] = Field(default="public", alias="schema")
    table: Optional[str] = None
    
    class Config:
        populate_by_name = True


class AuthConfig(BaseModel):
    """Authentication configuration"""
    username: str
    password: str


class DataSourceCreateRequest(BaseModel):
    """Request to create a data source"""
    name: str = Field(..., description="Data source name")
    description: Optional[str] = Field(None, description="Data source description")
    source_type: DataSourceType
    connection_config: ConnectionConfig
    auth_config: Optional[AuthConfig] = None
    attribute_mapping: Optional[Dict[str, str]] = Field(
        None, 
        description="Mapping of attribute names to column names"
    )


class DataSourceUpdateRequest(BaseModel):
    """Request to update a data source"""
    name: Optional[str] = None
    description: Optional[str] = None
    connection_config: Optional[ConnectionConfig] = None
    auth_config: Optional[AuthConfig] = None
    is_active: Optional[bool] = None


class DataSourceResponse(BaseModel):
    """Data source response"""
    id: int
    name: str
    description: Optional[str]
    source_type: DataSourceType
    connection_config: Dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class QueryValidationRequest(BaseModel):
    """Request to validate a SQL query"""
    query: str = Field(..., description="SQL query to validate")
    required_columns: Optional[List[str]] = Field(
        None, 
        description="List of required column names"
    )
    return_sample: bool = Field(
        default=True, 
        description="Whether to return sample data"
    )


class QueryValidationResponse(BaseModel):
    """Query validation response"""
    is_valid: bool
    error: Optional[str] = None
    columns: List[str] = Field(default_factory=list)
    sample_data: Optional[Dict[str, Any]] = None


class TestCaseQueryItem(BaseModel):
    """Individual test case query update"""
    test_case_id: str
    query_text: str


class TestCaseQueryUpdate(BaseModel):
    """Batch update of test case queries"""
    updates: List[TestCaseQueryItem]


# Additional RFI-related schemas

class TestCaseStatus(str, Enum):
    """Test case status"""
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    FAILED = "Failed"


class TestCasePriority(str, Enum):
    """Test case priority"""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class RFITestCaseResponse(BaseModel):
    """RFI test case response"""
    id: str
    test_case_number: str
    sample_id: str
    sample_identifier: str
    attribute_name: str
    status: TestCaseStatus
    priority: TestCasePriority
    query_text: Optional[str] = None
    expected_value: Optional[Any] = None
    actual_value: Optional[Any] = None
    test_result: Optional[str] = None
    
    class Config:
        from_attributes = True


class RFIPhaseStatus(BaseModel):
    """RFI phase status response"""
    phase_id: int
    status: str
    total_test_cases: int
    completed_test_cases: int
    failed_test_cases: int
    data_sources_configured: int
    assignments_completed: int
    
    class Config:
        from_attributes = True