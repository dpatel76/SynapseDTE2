"""
Schemas for Regulatory Data Dictionary
"""

from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class RegulatoryDataDictionaryBase(BaseModel):
    """Base schema for regulatory data dictionary"""
    report_name: str = Field(..., description="Report name")
    schedule_name: str = Field(..., description="Schedule name")
    line_item_number: Optional[str] = Field(None, description="Line item number")
    line_item_name: str = Field(..., description="Line item name")
    technical_line_item_name: Optional[str] = Field(None, description="Technical line item name")
    mdrm: Optional[str] = Field(None, description="Master Data Reference Model")
    description: Optional[str] = Field(None, description="Description")
    static_or_dynamic: Optional[str] = Field(None, description="Static or Dynamic")
    mandatory_or_optional: Optional[str] = Field(None, description="Mandatory or Optional")
    format_specification: Optional[str] = Field(None, description="Format specification")
    num_reports_schedules_used: Optional[str] = Field(None, description="Number of reports/schedules used")
    other_schedule_reference: Optional[str] = Field(None, description="Other schedule reference")
    is_active: bool = Field(default=True, description="Is active")


class RegulatoryDataDictionaryCreate(RegulatoryDataDictionaryBase):
    """Schema for creating regulatory data dictionary entry"""
    pass


class RegulatoryDataDictionaryUpdate(BaseModel):
    """Schema for updating regulatory data dictionary entry"""
    report_name: Optional[str] = Field(None, description="Report name")
    schedule_name: Optional[str] = Field(None, description="Schedule name")
    line_item_number: Optional[str] = Field(None, description="Line item number")
    line_item_name: Optional[str] = Field(None, description="Line item name")
    technical_line_item_name: Optional[str] = Field(None, description="Technical line item name")
    mdrm: Optional[str] = Field(None, description="Master Data Reference Model")
    description: Optional[str] = Field(None, description="Description")
    static_or_dynamic: Optional[str] = Field(None, description="Static or Dynamic")
    mandatory_or_optional: Optional[str] = Field(None, description="Mandatory or Optional")
    format_specification: Optional[str] = Field(None, description="Format specification")
    num_reports_schedules_used: Optional[str] = Field(None, description="Number of reports/schedules used")
    other_schedule_reference: Optional[str] = Field(None, description="Other schedule reference")
    is_active: Optional[bool] = Field(None, description="Is active")


class RegulatoryDataDictionaryResponse(RegulatoryDataDictionaryBase):
    """Schema for regulatory data dictionary response"""
    dict_id: int = Field(..., description="Dictionary ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class RegulatoryDataDictionaryListResponse(BaseModel):
    """Schema for regulatory data dictionary list response"""
    items: List[RegulatoryDataDictionaryResponse] = Field(..., description="List of dictionary entries")
    total: int = Field(..., description="Total number of entries")
    page: int = Field(..., description="Current page")
    per_page: int = Field(..., description="Items per page")


class DataDictionaryFilter(BaseModel):
    """Schema for filtering data dictionary"""
    report_name: Optional[str] = Field(None, description="Filter by report name")
    schedule_name: Optional[str] = Field(None, description="Filter by schedule name")
    line_item_name: Optional[str] = Field(None, description="Filter by line item name (contains)")
    mandatory_or_optional: Optional[str] = Field(None, description="Filter by mandatory/optional")
    static_or_dynamic: Optional[str] = Field(None, description="Filter by static/dynamic")
    search: Optional[str] = Field(None, description="General search term")
    is_active: Optional[bool] = Field(None, description="Filter by active status")


class DataDictionaryImportRequest(BaseModel):
    """Schema for importing data dictionary entries to report attributes"""
    selected_dict_ids: List[int] = Field(..., description="List of dictionary IDs to import")
    cycle_id: int = Field(..., description="Target cycle ID")
    report_id: int = Field(..., description="Target report ID")
    import_options: Optional[dict] = Field(None, description="Import options (e.g., override existing)")


class DataDictionaryImportResponse(BaseModel):
    """Schema for data dictionary import response"""
    success: bool = Field(..., description="Import success status")
    imported_count: int = Field(..., description="Number of entries imported")
    skipped_count: int = Field(..., description="Number of entries skipped")
    error_count: int = Field(..., description="Number of entries with errors")
    messages: List[str] = Field(default=[], description="Import messages")
    created_attributes: List[int] = Field(default=[], description="IDs of created attributes") 