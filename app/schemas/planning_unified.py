"""
Unified Planning Phase Schemas
This module contains the schemas for the new unified planning phase architecture.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, validator
from enum import Enum
import uuid


# Enums matching the database models
class VersionStatusEnum(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class DataSourceTypeEnum(str, Enum):
    DATABASE = "database"
    FILE = "file"
    API = "api"
    SFTP = "sftp"
    S3 = "s3"
    OTHER = "other"


class AttributeDataTypeEnum(str, Enum):
    STRING = "string"
    INTEGER = "integer"
    DECIMAL = "decimal"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    TEXT = "text"


class InformationSecurityClassificationEnum(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class MappingTypeEnum(str, Enum):
    DIRECT = "direct"
    CALCULATED = "calculated"
    LOOKUP = "lookup"
    CONDITIONAL = "conditional"


class DecisionEnum(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_CHANGES = "request_changes"


class StatusEnum(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


# Base Schemas
class BaseSchema(BaseModel):
    """Base schema with common configuration"""
    model_config = ConfigDict(from_attributes=True)


# Planning Version Schemas
class PlanningVersionBase(BaseSchema):
    """Base planning version schema"""
    phase_id: int = Field(..., description="Phase ID")
    workflow_activity_id: Optional[int] = Field(None, description="Workflow activity ID")
    version_number: int = Field(..., description="Version number")
    version_status: VersionStatusEnum = Field(default=VersionStatusEnum.DRAFT, description="Version status")
    parent_version_id: Optional[uuid.UUID] = Field(None, description="Parent version ID")
    workflow_execution_id: Optional[str] = Field(None, description="Temporal workflow execution ID")
    workflow_run_id: Optional[str] = Field(None, description="Temporal workflow run ID")
    llm_generation_summary: Optional[Dict[str, Any]] = Field(None, description="LLM generation summary")
    rejection_reason: Optional[str] = Field(None, description="Rejection reason")


class PlanningVersionCreate(PlanningVersionBase):
    """Schema for creating a planning version"""
    pass


class PlanningVersionUpdate(BaseSchema):
    """Schema for updating a planning version"""
    version_status: Optional[VersionStatusEnum] = Field(None, description="Version status")
    llm_generation_summary: Optional[Dict[str, Any]] = Field(None, description="LLM generation summary")
    rejection_reason: Optional[str] = Field(None, description="Rejection reason")


class PlanningVersionResponse(PlanningVersionBase):
    """Schema for planning version response"""
    version_id: uuid.UUID = Field(..., description="Version ID")
    total_attributes: int = Field(default=0, description="Total attributes")
    approved_attributes: int = Field(default=0, description="Approved attributes")
    pk_attributes: int = Field(default=0, description="Primary key attributes")
    cde_attributes: int = Field(default=0, description="CDE attributes")
    mandatory_attributes: int = Field(default=0, description="Mandatory attributes")
    total_data_sources: int = Field(default=0, description="Total data sources")
    approved_data_sources: int = Field(default=0, description="Approved data sources")
    total_pde_mappings: int = Field(default=0, description="Total PDE mappings")
    approved_pde_mappings: int = Field(default=0, description="Approved PDE mappings")
    
    submitted_by_id: Optional[int] = Field(None, description="Submitted by user ID")
    submitted_at: Optional[datetime] = Field(None, description="Submission timestamp")
    approved_by_id: Optional[int] = Field(None, description="Approved by user ID")
    approved_at: Optional[datetime] = Field(None, description="Approval timestamp")
    
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    created_by_id: int = Field(..., description="Created by user ID")
    updated_by_id: int = Field(..., description="Updated by user ID")


# Planning Data Source Schemas
class PlanningDataSourceBase(BaseSchema):
    """Base planning data source schema"""
    source_name: str = Field(..., min_length=1, max_length=255, description="Data source name")
    source_type: DataSourceTypeEnum = Field(..., description="Data source type")
    description: Optional[str] = Field(None, description="Data source description")
    connection_config: Dict[str, Any] = Field(..., description="Connection configuration")
    auth_config: Optional[Dict[str, Any]] = Field(None, description="Authentication configuration")
    refresh_schedule: Optional[str] = Field(None, max_length=100, description="Refresh schedule")
    validation_rules: Optional[Dict[str, Any]] = Field(None, description="Validation rules")
    estimated_record_count: Optional[int] = Field(None, description="Estimated record count")
    data_freshness_hours: Optional[int] = Field(None, description="Data freshness in hours")


class PlanningDataSourceCreate(PlanningDataSourceBase):
    """Schema for creating a planning data source"""
    version_id: uuid.UUID = Field(..., description="Version ID")
    phase_id: int = Field(..., description="Phase ID")


class PlanningDataSourceUpdate(BaseSchema):
    """Schema for updating a planning data source"""
    source_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Data source name")
    source_type: Optional[DataSourceTypeEnum] = Field(None, description="Data source type")
    description: Optional[str] = Field(None, description="Data source description")
    connection_config: Optional[Dict[str, Any]] = Field(None, description="Connection configuration")
    auth_config: Optional[Dict[str, Any]] = Field(None, description="Authentication configuration")
    refresh_schedule: Optional[str] = Field(None, max_length=100, description="Refresh schedule")
    validation_rules: Optional[Dict[str, Any]] = Field(None, description="Validation rules")
    estimated_record_count: Optional[int] = Field(None, description="Estimated record count")
    data_freshness_hours: Optional[int] = Field(None, description="Data freshness in hours")


class PlanningDataSourceResponse(PlanningDataSourceBase):
    """Schema for planning data source response"""
    data_source_id: uuid.UUID = Field(..., description="Data source ID")
    version_id: uuid.UUID = Field(..., description="Version ID")
    phase_id: int = Field(..., description="Phase ID")
    
    tester_decision: Optional[DecisionEnum] = Field(None, description="Tester decision")
    tester_decided_by: Optional[int] = Field(None, description="Tester decided by user ID")
    tester_decided_at: Optional[datetime] = Field(None, description="Tester decision timestamp")
    tester_notes: Optional[str] = Field(None, description="Tester notes")
    
    status: StatusEnum = Field(default=StatusEnum.PENDING, description="Status")
    
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    created_by_id: int = Field(..., description="Created by user ID")
    updated_by_id: int = Field(..., description="Updated by user ID")


# Planning Attribute Schemas
class PlanningAttributeBase(BaseSchema):
    """Base planning attribute schema"""
    attribute_name: str = Field(..., min_length=1, max_length=255, description="Attribute name")
    data_type: AttributeDataTypeEnum = Field(..., description="Data type")
    description: Optional[str] = Field(None, description="Attribute description")
    business_definition: Optional[str] = Field(None, description="Business definition")
    is_mandatory: bool = Field(default=False, description="Is mandatory")
    is_cde: bool = Field(default=False, description="Is CDE")
    is_primary_key: bool = Field(default=False, description="Is primary key")
    max_length: Optional[int] = Field(None, description="Maximum length")
    information_security_classification: InformationSecurityClassificationEnum = Field(
        default=InformationSecurityClassificationEnum.INTERNAL, 
        description="Information security classification"
    )
    llm_metadata: Optional[Dict[str, Any]] = Field(None, description="LLM metadata")


class PlanningAttributeCreate(PlanningAttributeBase):
    """Schema for creating a planning attribute"""
    version_id: uuid.UUID = Field(..., description="Version ID")
    phase_id: int = Field(..., description="Phase ID")


class PlanningAttributeUpdate(BaseSchema):
    """Schema for updating a planning attribute"""
    attribute_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Attribute name")
    data_type: Optional[AttributeDataTypeEnum] = Field(None, description="Data type")
    description: Optional[str] = Field(None, description="Attribute description")
    business_definition: Optional[str] = Field(None, description="Business definition")
    is_mandatory: Optional[bool] = Field(None, description="Is mandatory")
    is_cde: Optional[bool] = Field(None, description="Is CDE")
    is_primary_key: Optional[bool] = Field(None, description="Is primary key")
    max_length: Optional[int] = Field(None, description="Maximum length")
    information_security_classification: Optional[InformationSecurityClassificationEnum] = Field(
        None, description="Information security classification"
    )
    llm_metadata: Optional[Dict[str, Any]] = Field(None, description="LLM metadata")


class PlanningAttributeResponse(PlanningAttributeBase):
    """Schema for planning attribute response"""
    attribute_id: uuid.UUID = Field(..., description="Attribute ID")
    version_id: uuid.UUID = Field(..., description="Version ID")
    phase_id: int = Field(..., description="Phase ID")
    
    tester_decision: Optional[DecisionEnum] = Field(None, description="Tester decision")
    tester_decided_by: Optional[int] = Field(None, description="Tester decided by user ID")
    tester_decided_at: Optional[datetime] = Field(None, description="Tester decision timestamp")
    tester_notes: Optional[str] = Field(None, description="Tester notes")
    
    status: StatusEnum = Field(default=StatusEnum.PENDING, description="Status")
    
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    created_by_id: int = Field(..., description="Created by user ID")
    updated_by_id: int = Field(..., description="Updated by user ID")


# Planning PDE Mapping Schemas
class PlanningPDEMappingBase(BaseSchema):
    """Base planning PDE mapping schema"""
    pde_name: str = Field(..., min_length=1, max_length=255, description="PDE name")
    pde_code: str = Field(..., min_length=1, max_length=100, description="PDE code")
    mapping_type: MappingTypeEnum = Field(default=MappingTypeEnum.DIRECT, description="Mapping type")
    source_table: str = Field(..., min_length=1, max_length=255, description="Source table")
    source_column: str = Field(..., min_length=1, max_length=255, description="Source column")
    source_field: str = Field(..., min_length=1, max_length=500, description="Source field path")
    column_data_type: Optional[str] = Field(None, max_length=100, description="Column data type")
    transformation_rule: Optional[str] = Field(None, description="Transformation rule")
    condition_rule: Optional[str] = Field(None, description="Condition rule")
    is_primary: bool = Field(default=False, description="Is primary mapping")
    classification: Optional[Dict[str, Any]] = Field(None, description="PDE classification")
    llm_metadata: Optional[Dict[str, Any]] = Field(None, description="LLM metadata")


class PlanningPDEMappingCreate(PlanningPDEMappingBase):
    """Schema for creating a planning PDE mapping"""
    version_id: uuid.UUID = Field(..., description="Version ID")
    attribute_id: uuid.UUID = Field(..., description="Attribute ID")
    data_source_id: uuid.UUID = Field(..., description="Data source ID")
    phase_id: int = Field(..., description="Phase ID")


class PlanningPDEMappingUpdate(BaseSchema):
    """Schema for updating a planning PDE mapping"""
    pde_name: Optional[str] = Field(None, min_length=1, max_length=255, description="PDE name")
    pde_code: Optional[str] = Field(None, min_length=1, max_length=100, description="PDE code")
    mapping_type: Optional[MappingTypeEnum] = Field(None, description="Mapping type")
    source_table: Optional[str] = Field(None, min_length=1, max_length=255, description="Source table")
    source_column: Optional[str] = Field(None, min_length=1, max_length=255, description="Source column")
    source_field: Optional[str] = Field(None, min_length=1, max_length=500, description="Source field path")
    column_data_type: Optional[str] = Field(None, max_length=100, description="Column data type")
    transformation_rule: Optional[str] = Field(None, description="Transformation rule")
    condition_rule: Optional[str] = Field(None, description="Condition rule")
    is_primary: Optional[bool] = Field(None, description="Is primary mapping")
    classification: Optional[Dict[str, Any]] = Field(None, description="PDE classification")
    llm_metadata: Optional[Dict[str, Any]] = Field(None, description="LLM metadata")


class PlanningPDEMappingResponse(PlanningPDEMappingBase):
    """Schema for planning PDE mapping response"""
    pde_mapping_id: uuid.UUID = Field(..., description="PDE mapping ID")
    version_id: uuid.UUID = Field(..., description="Version ID")
    attribute_id: uuid.UUID = Field(..., description="Attribute ID")
    data_source_id: uuid.UUID = Field(..., description="Data source ID")
    phase_id: int = Field(..., description="Phase ID")
    
    tester_decision: Optional[DecisionEnum] = Field(None, description="Tester decision")
    tester_decided_by: Optional[int] = Field(None, description="Tester decided by user ID")
    tester_decided_at: Optional[datetime] = Field(None, description="Tester decision timestamp")
    tester_notes: Optional[str] = Field(None, description="Tester notes")
    auto_approved: bool = Field(default=False, description="Auto approved")
    
    status: StatusEnum = Field(default=StatusEnum.PENDING, description="Status")
    
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    created_by_id: int = Field(..., description="Created by user ID")
    updated_by_id: int = Field(..., description="Updated by user ID")


# Tester Decision Schemas
class TesterDecisionRequest(BaseSchema):
    """Schema for tester decision request"""
    decision: DecisionEnum = Field(..., description="Tester decision")
    notes: Optional[str] = Field(None, description="Decision notes")


class TesterDecisionResponse(BaseSchema):
    """Schema for tester decision response"""
    success: bool = Field(..., description="Decision success")
    message: str = Field(..., description="Decision message")
    decision: DecisionEnum = Field(..., description="Decision made")
    decided_at: datetime = Field(..., description="Decision timestamp")
    decided_by: int = Field(..., description="Decision made by user ID")


# Workflow Schemas
class PlanningVersionSubmissionRequest(BaseSchema):
    """Schema for submitting a planning version for approval"""
    submission_notes: Optional[str] = Field(None, description="Submission notes")


class PlanningVersionApprovalRequest(BaseSchema):
    """Schema for approving/rejecting a planning version"""
    action: str = Field(..., pattern="^(approve|reject)$", description="Approval action")
    notes: Optional[str] = Field(None, description="Approval notes")


# List Response Schemas
class PlanningVersionListResponse(BaseSchema):
    """Schema for planning version list response"""
    versions: List[PlanningVersionResponse] = Field(..., description="List of planning versions")
    total: int = Field(..., description="Total number of versions")
    current_page: int = Field(..., description="Current page number")
    total_pages: int = Field(..., description="Total number of pages")


class PlanningDataSourceListResponse(BaseSchema):
    """Schema for planning data source list response"""
    data_sources: List[PlanningDataSourceResponse] = Field(..., description="List of data sources")
    total: int = Field(..., description="Total number of data sources")


class PlanningAttributeListResponse(BaseSchema):
    """Schema for planning attribute list response"""
    attributes: List[PlanningAttributeResponse] = Field(..., description="List of attributes")
    total: int = Field(..., description="Total number of attributes")


class PlanningPDEMappingListResponse(BaseSchema):
    """Schema for planning PDE mapping list response"""
    pde_mappings: List[PlanningPDEMappingResponse] = Field(..., description="List of PDE mappings")
    total: int = Field(..., description="Total number of PDE mappings")


# Planning Dashboard Schema
class PlanningDashboardResponse(BaseSchema):
    """Schema for planning dashboard response"""
    version: PlanningVersionResponse = Field(..., description="Current planning version")
    data_sources: PlanningDataSourceListResponse = Field(..., description="Data sources")
    attributes: PlanningAttributeListResponse = Field(..., description="Attributes")
    pde_mappings: PlanningPDEMappingListResponse = Field(..., description="PDE mappings")
    
    # Summary statistics
    completion_percentage: float = Field(..., ge=0, le=100, description="Completion percentage")
    pending_decisions: int = Field(..., description="Number of pending decisions")
    can_submit: bool = Field(..., description="Can submit for approval")
    submission_requirements: List[str] = Field(..., description="Requirements for submission")


# LLM Generation Schemas
class LLMPlanningGenerationRequest(BaseSchema):
    """Schema for LLM planning generation request"""
    version_id: uuid.UUID = Field(..., description="Version ID")
    include_attributes: bool = Field(default=True, description="Include attribute generation")
    include_pde_mappings: bool = Field(default=True, description="Include PDE mapping generation")
    regulatory_context: Optional[str] = Field(None, description="Regulatory context")
    provider: Optional[str] = Field(None, description="LLM provider preference")


class LLMPlanningGenerationResponse(BaseSchema):
    """Schema for LLM planning generation response"""
    success: bool = Field(..., description="Generation success")
    attributes_generated: int = Field(..., description="Number of attributes generated")
    pde_mappings_generated: int = Field(..., description="Number of PDE mappings generated")
    auto_approved_count: int = Field(..., description="Number of auto-approved items")
    provider_used: str = Field(..., description="LLM provider used")
    generation_summary: Dict[str, Any] = Field(..., description="Generation summary")


# Bulk Operations Schemas
class BulkTesterDecisionRequest(BaseSchema):
    """Schema for bulk tester decision request"""
    item_ids: List[uuid.UUID] = Field(..., description="List of item IDs")
    item_type: str = Field(..., pattern="^(data_source|attribute|pde_mapping)$", description="Item type")
    decision: DecisionEnum = Field(..., description="Bulk decision")
    notes: Optional[str] = Field(None, description="Bulk decision notes")


class BulkTesterDecisionResponse(BaseSchema):
    """Schema for bulk tester decision response"""
    success: bool = Field(..., description="Bulk operation success")
    total_requested: int = Field(..., description="Total items requested")
    successful: int = Field(..., description="Successfully processed items")
    failed: int = Field(..., description="Failed items")
    results: List[Dict[str, Any]] = Field(..., description="Detailed results")


# Error Schemas
class PlanningErrorResponse(BaseSchema):
    """Schema for planning error response"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Error details")
    timestamp: datetime = Field(..., description="Error timestamp")