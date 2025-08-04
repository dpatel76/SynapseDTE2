"""
Planning phase schemas for workflow management
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator, ConfigDict
from enum import Enum


class MandatoryFlag(str, Enum):
    """Mandatory flag enumeration"""
    MANDATORY = "Mandatory"
    CONDITIONAL = "Conditional"
    OPTIONAL = "Optional"


class DataType(str, Enum):
    """Data type enumeration"""
    STRING = "String"
    INTEGER = "Integer"
    DECIMAL = "Decimal"
    DATE = "Date"
    DATETIME = "DateTime"
    BOOLEAN = "Boolean"
    JSON = "JSON"


class DocumentType(str, Enum):
    """Document type enumeration"""
    REGULATORY_SPECIFICATION = "Regulatory Specification"
    CDE_LIST = "CDE List"
    HISTORICAL_ISSUES_LIST = "Historical Issues List"
    SAMPLE_FILE = "Sample File"
    SOURCE_DOCUMENT = "Source Document"


class InformationSecurityClassification(str, Enum):
    """Information Security Classification enumeration"""
    HRCI = "HRCI"
    CONFIDENTIAL = "Confidential"
    PROPRIETARY = "Proprietary"
    PUBLIC = "Public"


# Document Schemas
class DocumentUpload(BaseModel):
    """Schema for document upload"""
    document_type: DocumentType = Field(..., description="Type of document")
    original_filename: str = Field(..., min_length=1, max_length=255, description="Original filename")


class DocumentResponse(BaseModel):
    """Schema for document response"""
    document_id: int = Field(..., description="Document ID")
    cycle_id: int = Field(..., description="Cycle ID")
    report_id: int = Field(..., description="Report ID")
    document_type: DocumentType = Field(..., description="Document type")
    original_filename: str = Field(..., description="Original filename")
    stored_filename: str = Field(..., description="Stored filename")
    file_size: int = Field(..., description="File size in bytes")
    version_number: int = Field(..., description="Version number")
    uploaded_by: int = Field(..., description="User ID who uploaded")
    is_latest: bool = Field(..., description="Is latest version")
    created_at: datetime = Field(..., description="Upload timestamp")
    
    model_config = ConfigDict(from_attributes=True)


# Report Attribute Schemas
class ReportAttributeBase(BaseModel):
    """Base report attribute schema"""
    attribute_name: str = Field(..., min_length=1, max_length=255, description="Attribute name")
    description: Optional[str] = Field(None, description="Attribute description")
    data_type: Optional[DataType] = Field(None, description="Data type")
    mandatory_flag: MandatoryFlag = Field(default=MandatoryFlag.OPTIONAL, description="Mandatory flag")
    cde_flag: bool = Field(default=False, description="CDE flag")
    historical_issues_flag: bool = Field(default=False, description="Historical issues flag")
    is_primary_key: bool = Field(default=False, description="Primary key flag")
    tester_notes: Optional[str] = Field(None, description="Tester notes")
    information_security_classification: Optional[InformationSecurityClassification] = Field(None, description="Security classification")
    
    # Data dictionary import fields
    line_item_number: Optional[str] = Field(None, max_length=20, description="Regulatory line item number from data dictionary")
    technical_line_item_name: Optional[str] = Field(None, max_length=255, description="Technical line item name from data dictionary")
    mdrm: Optional[str] = Field(None, max_length=50, description="MDRM code from regulatory data dictionary")
    
    # Enhanced LLM-generated fields for better testing guidance
    validation_rules: Optional[str] = Field(None, description="Business rules and validation constraints")
    typical_source_documents: Optional[str] = Field(None, description="Typical source documents where this data is found")
    keywords_to_look_for: Optional[str] = Field(None, description="Keywords to search for in source documents")
    testing_approach: Optional[str] = Field(None, description="Recommended testing approach and methodology")
    
    # Risk assessment fields
    risk_score: Optional[float] = Field(None, ge=0, le=100, description="LLM-provided risk score (0-100)")
    llm_risk_rationale: Optional[str] = Field(None, description="LLM explanation for risk score")


class ReportAttributeCreate(ReportAttributeBase):
    """Schema for creating report attribute"""
    pass


class ReportAttributeUpdate(BaseModel):
    """Schema for updating report attribute"""
    attribute_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Attribute name")
    description: Optional[str] = Field(None, description="Attribute description")
    data_type: Optional[DataType] = Field(None, description="Data type")
    mandatory_flag: Optional[MandatoryFlag] = Field(None, description="Mandatory flag")
    cde_flag: Optional[bool] = Field(None, description="CDE flag")
    historical_issues_flag: Optional[bool] = Field(None, description="Historical issues flag")
    is_primary_key: Optional[bool] = Field(None, description="Primary key flag")
    tester_notes: Optional[str] = Field(None, description="Tester notes")
    
    # Data dictionary import fields
    line_item_number: Optional[str] = Field(None, max_length=20, description="Regulatory line item number from data dictionary")
    technical_line_item_name: Optional[str] = Field(None, max_length=255, description="Technical line item name from data dictionary")
    mdrm: Optional[str] = Field(None, max_length=50, description="MDRM code from regulatory data dictionary")
    
    # Enhanced LLM-generated fields for better testing guidance
    validation_rules: Optional[str] = Field(None, description="Business rules and validation constraints")
    typical_source_documents: Optional[str] = Field(None, description="Typical source documents where this data is found")
    keywords_to_look_for: Optional[str] = Field(None, description="Keywords to search for in source documents")
    testing_approach: Optional[str] = Field(None, description="Recommended testing approach and methodology")
    
    # Risk assessment fields
    risk_score: Optional[float] = Field(None, ge=0, le=100, description="LLM-provided risk score (0-100)")
    llm_risk_rationale: Optional[str] = Field(None, description="LLM explanation for risk score")
    
    # Primary key support fields
    is_primary_key: Optional[bool] = Field(None, description="Whether this attribute is part of the primary key")
    primary_key_order: Optional[int] = Field(None, description="Order of this attribute in composite primary key (1-based)")
    
    # Approval status field
    approval_status: Optional[str] = Field(None, pattern="^(pending|approved|rejected)$", description="Approval status")


class ReportAttributeResponse(ReportAttributeBase):
    """Schema for report attribute response"""
    attribute_id: int = Field(..., description="Attribute ID")
    phase_id: int = Field(..., description="Phase ID")
    is_scoped: bool = Field(..., description="Is scoped for testing")
    
    # Hybrid properties for UI compatibility
    cycle_id: Optional[int] = Field(None, description="Cycle ID (computed from phase)")
    report_id: Optional[int] = Field(None, description="Report ID (computed from phase)")
    llm_generated: bool = Field(..., description="Generated by LLM")
    llm_rationale: Optional[str] = Field(None, description="LLM generation rationale")
    
    # Data dictionary import fields
    line_item_number: Optional[str] = Field(None, description="Regulatory line item number from data dictionary")
    technical_line_item_name: Optional[str] = Field(None, description="Technical line item name from data dictionary")
    mdrm: Optional[str] = Field(None, description="MDRM code from regulatory data dictionary")
    
    risk_score: Optional[float] = Field(None, ge=0, le=100, description="LLM-provided risk score (0-100)")
    
    # Primary key support fields
    is_primary_key: bool = Field(default=False, description="Whether this attribute is part of the primary key")
    primary_key_order: Optional[int] = Field(None, description="Order of this attribute in composite primary key (1-based)")
    
    # Approval status field
    approval_status: str = Field(default="pending", description="Approval status: pending, approved, rejected")
    
    # Versioning fields
    master_attribute_id: Optional[int] = Field(None, description="Master attribute ID linking all versions")
    version_number: int = Field(default=1, description="Version number of this attribute")
    is_latest_version: bool = Field(default=True, description="Whether this is the latest version")
    is_active: bool = Field(default=True, description="Whether this version is active")
    version_notes: Optional[str] = Field(None, description="Notes about what changed in this version")
    change_reason: Optional[str] = Field(None, description="Reason for creating new version")
    replaced_attribute_id: Optional[int] = Field(None, description="ID of the attribute this version replaces")
    
    # Version timestamps and user tracking
    version_created_at: datetime = Field(..., description="Version creation timestamp")
    version_created_by: int = Field(..., description="User who created this version")
    approved_at: Optional[datetime] = Field(None, description="Approval timestamp")
    approved_by: Optional[int] = Field(None, description="User who approved this version")
    archived_at: Optional[datetime] = Field(None, description="Archive timestamp")
    archived_by: Optional[int] = Field(None, description="User who archived this version")
    
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class ReportAttributeListResponse(BaseModel):
    """Schema for report attribute list response"""
    attributes: List[ReportAttributeResponse] = Field(..., description="List of attributes")
    total: int = Field(..., description="Total number of attributes")


# LLM Generation Schemas
class LLMAttributeGenerationRequest(BaseModel):
    """Schema for LLM attribute generation request"""
    include_cde_matching: bool = Field(default=True, description="Include CDE matching")
    include_historical_matching: bool = Field(default=True, description="Include historical issues matching")
    regulatory_context: Optional[str] = Field(None, description="Regulatory context")
    provider: Optional[str] = Field(None, description="LLM provider preference (claude, gemini, hybrid)")
    discovery_provider: Optional[str] = Field(None, description="Provider for discovery phase")
    details_provider: Optional[str] = Field(None, description="Provider for details phase")
    regulatory_report: Optional[str] = Field(None, description="Regulatory report (e.g., FR Y-14M)")
    schedule: Optional[str] = Field(None, description="Report schedule (e.g., Schedule A)")


class LLMAttributeGenerationResponse(BaseModel):
    """Schema for LLM attribute generation response"""
    success: bool = Field(..., description="Generation success")
    attributes: List[ReportAttributeResponse] = Field(..., description="Generated attributes")
    total_generated: int = Field(..., description="Total attributes generated")
    total_saved: int = Field(..., description="Total attributes saved")
    cde_matches: int = Field(..., description="Number of CDE matches")
    historical_matches: int = Field(..., description="Number of historical matches")
    provider_used: str = Field(..., description="LLM provider used")
    method: str = Field(..., description="Generation method used")


# Planning Phase Workflow Schemas
class PlanningPhaseStart(BaseModel):
    """Schema for starting planning phase"""
    planned_start_date: Optional[datetime] = Field(None, description="Planned start date")
    planned_end_date: Optional[datetime] = Field(None, description="Planned end date")
    notes: Optional[str] = Field(None, description="Planning notes")


class PlanningPhaseStatus(BaseModel):
    """Schema for planning phase status"""
    cycle_id: int = Field(..., description="Cycle ID")
    report_id: int = Field(..., description="Report ID")
    phase_id: int = Field(..., description="Phase ID")
    status: str = Field(..., description="Phase status")
    
    # Date fields
    planned_start_date: Optional[datetime] = Field(None, description="Planned start date")
    planned_end_date: Optional[datetime] = Field(None, description="Planned end date")
    actual_start_date: Optional[datetime] = Field(None, description="Actual start date")
    actual_end_date: Optional[datetime] = Field(None, description="Actual end date")
    
    # Alternative names for frontend compatibility
    started_at: Optional[datetime] = Field(None, description="Actual start date (alias)")
    completed_at: Optional[datetime] = Field(None, description="Actual end date (alias)")
    
    # Attribute metrics
    attributes_count: int = Field(..., description="Total number of attributes")
    approved_count: int = Field(..., description="Number of approved attributes")
    pk_count: int = Field(0, description="Number of Primary Key attributes")
    pk_approved_count: int = Field(0, description="Number of approved Primary Key attributes")
    cde_count: int = Field(..., description="Number of CDE attributes")
    historical_issues_count: int = Field(..., description="Number of attributes with historical issues")
    llm_generated_count: int = Field(..., description="Number of LLM generated attributes")
    manual_added_count: int = Field(..., description="Number of manually added attributes")
    can_complete: bool = Field(..., description="Can complete planning phase")
    completion_requirements: List[str] = Field(..., description="Requirements to complete phase")


class PlanningPhaseComplete(BaseModel):
    """Schema for completing planning phase"""
    completion_notes: Optional[str] = Field(None, description="Completion notes")
    attributes_confirmed: bool = Field(..., description="Confirm attributes are reviewed")
    documents_verified: bool = Field(..., description="Confirm documents are verified")


# File Upload Schemas
class FileUploadResponse(BaseModel):
    """Schema for file upload response"""
    success: bool = Field(..., description="Upload success")
    document: DocumentResponse = Field(..., description="Document information")
    message: str = Field(..., description="Upload message")


# VERSIONING SCHEMAS

class AttributeVersionCreateRequest(BaseModel):
    """Schema for creating a new version of an attribute"""
    change_reason: Optional[str] = Field(None, max_length=100, description="Reason for creating new version")
    version_notes: Optional[str] = Field(None, description="Notes about what changed in this version")
    
    # Updated attribute data (inherit from base schema)
    attribute_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Updated attribute name")
    description: Optional[str] = Field(None, description="Updated attribute description")
    data_type: Optional[DataType] = Field(None, description="Updated data type")
    mandatory_flag: Optional[MandatoryFlag] = Field(None, description="Updated mandatory flag")
    cde_flag: Optional[bool] = Field(None, description="Updated CDE flag")
    historical_issues_flag: Optional[bool] = Field(None, description="Updated historical issues flag")
    tester_notes: Optional[str] = Field(None, description="Updated tester notes")
    information_security_classification: Optional[InformationSecurityClassification] = Field(None, description="Updated security classification")
    
    # Data dictionary import fields
    line_item_number: Optional[str] = Field(None, max_length=20, description="Updated line item number")
    technical_line_item_name: Optional[str] = Field(None, max_length=255, description="Updated technical line item name")
    mdrm: Optional[str] = Field(None, max_length=50, description="Updated MDRM code")
    
    validation_rules: Optional[str] = Field(None, description="Updated validation rules")
    typical_source_documents: Optional[str] = Field(None, description="Updated typical source documents")
    keywords_to_look_for: Optional[str] = Field(None, description="Updated keywords to look for")
    testing_approach: Optional[str] = Field(None, description="Updated testing approach")
    risk_score: Optional[float] = Field(None, ge=0, le=100, description="Updated risk score")
    llm_risk_rationale: Optional[str] = Field(None, description="Updated LLM risk rationale")
    is_primary_key: Optional[bool] = Field(None, description="Updated primary key flag")
    primary_key_order: Optional[int] = Field(None, description="Updated primary key order")


class AttributeVersionApprovalRequest(BaseModel):
    """Schema for approving/rejecting a version"""
    action: str = Field(..., pattern="^(approve|reject)$", description="Action to take: approve or reject")
    approval_notes: Optional[str] = Field(None, description="Notes about the approval/rejection")


class AttributeVersionResponse(BaseModel):
    """Schema for version-specific information"""
    attribute_id: int = Field(..., description="Attribute ID")
    master_attribute_id: Optional[int] = Field(None, description="Master attribute ID")
    version_number: int = Field(..., description="Version number")
    is_latest_version: bool = Field(..., description="Whether this is the latest version")
    is_active: bool = Field(..., description="Whether this version is active")
    approval_status: str = Field(..., description="Approval status")
    version_notes: Optional[str] = Field(None, description="Version notes")
    change_reason: Optional[str] = Field(None, description="Reason for change")
    
    # Timestamps and users
    version_created_at: datetime = Field(..., description="Version creation timestamp")
    version_created_by: int = Field(..., description="User who created version")
    approved_at: Optional[datetime] = Field(None, description="Approval timestamp")
    approved_by: Optional[int] = Field(None, description="User who approved")
    archived_at: Optional[datetime] = Field(None, description="Archive timestamp")
    archived_by: Optional[int] = Field(None, description="User who archived")
    
    model_config = ConfigDict(from_attributes=True)


class AttributeVersionHistoryResponse(BaseModel):
    """Schema for attribute version history"""
    master_attribute_id: int = Field(..., description="Master attribute ID")
    attribute_name: str = Field(..., description="Attribute name")
    total_versions: int = Field(..., description="Total number of versions")
    latest_version: int = Field(..., description="Latest version number")
    active_version: int = Field(..., description="Currently active version number")
    
    versions: List[AttributeVersionResponse] = Field(..., description="List of all versions")
    
    model_config = ConfigDict(from_attributes=True)


class AttributeVersionChangeLogResponse(BaseModel):
    """Schema for version change log entries"""
    log_id: int = Field(..., description="Log entry ID")
    attribute_id: int = Field(..., description="Attribute ID")
    change_type: str = Field(..., description="Type of change")
    version_number: int = Field(..., description="Version number")
    change_notes: Optional[str] = Field(None, description="Change notes")
    changed_at: datetime = Field(..., description="Change timestamp")
    changed_by: int = Field(..., description="User who made the change")
    field_changes: Optional[str] = Field(None, description="JSON string of field changes")
    impact_assessment: Optional[str] = Field(None, description="Impact assessment")
    
    model_config = ConfigDict(from_attributes=True)


class AttributeVersionComparisonRequest(BaseModel):
    """Schema for requesting version comparison"""
    version_a_id: int = Field(..., description="First version ID to compare")
    version_b_id: int = Field(..., description="Second version ID to compare")
    comparison_notes: Optional[str] = Field(None, description="Notes about the comparison")


class AttributeVersionComparisonResponse(BaseModel):
    """Schema for version comparison results"""
    comparison_id: int = Field(..., description="Comparison ID")
    version_a_id: int = Field(..., description="First version ID")
    version_b_id: int = Field(..., description="Second version ID")
    differences_found: int = Field(..., description="Number of differences found")
    comparison_summary: Optional[str] = Field(None, description="JSON summary of differences")
    impact_score: Optional[float] = Field(None, description="Impact score (0-10)")
    compared_at: datetime = Field(..., description="Comparison timestamp")
    compared_by: int = Field(..., description="User who performed comparison")
    comparison_notes: Optional[str] = Field(None, description="Comparison notes")
    
    # Detailed change information
    changes: List[Dict[str, Any]] = Field(default=[], description="List of specific changes")
    summary: str = Field(..., description="Human-readable summary")
    
    model_config = ConfigDict(from_attributes=True)


class AttributeBulkVersionRequest(BaseModel):
    """Schema for bulk version operations"""
    attribute_ids: List[int] = Field(..., description="List of attribute IDs")
    action: str = Field(..., pattern="^(approve|reject|archive|restore)$", description="Bulk action")
    notes: Optional[str] = Field(None, description="Notes for the bulk operation")


class AttributeBulkVersionResponse(BaseModel):
    """Schema for bulk version operation results"""
    total_requested: int = Field(..., description="Total attributes requested for operation")
    successful: int = Field(..., description="Number of successful operations")
    failed: int = Field(..., description="Number of failed operations")
    skipped: int = Field(..., description="Number of skipped operations")
    
    results: List[Dict[str, Any]] = Field(..., description="Detailed results for each attribute")
    summary: str = Field(..., description="Operation summary") 