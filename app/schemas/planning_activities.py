"""
Pydantic schemas for Planning phase optional activities
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class DataSourceTypeEnum(str, Enum):
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    ORACLE = "oracle"
    SQLSERVER = "sqlserver"
    MONGODB = "mongodb"
    CSV = "csv"
    EXCEL = "excel"
    API = "api"
    SFTP = "sftp"
    S3 = "s3"


class InformationSecurityClassification(str, Enum):
    HRCI = "HRCI"
    CONFIDENTIAL = "Confidential"
    PROPRIETARY = "Proprietary"
    PUBLIC = "Public"


# ===================== Data Source Schemas =====================

class DataSourceTestConnectionRequest(BaseModel):
    source_type: DataSourceTypeEnum
    connection_config: Dict[str, Any] = Field(..., description="Connection configuration")
    auth_type: Optional[str] = Field(None, description="Authentication type: basic, oauth, api_key, certificate")
    auth_config: Optional[Dict[str, Any]] = Field(None, description="Authentication configuration")


class DataSourceCreateRequest(BaseModel):
    name: str = Field(..., description="Name of the data source")
    description: Optional[str] = Field(None, description="Description of the data source")
    source_type: DataSourceTypeEnum
    connection_config: Dict[str, Any] = Field(..., description="Connection configuration (encrypted)")
    auth_type: Optional[str] = Field(None, description="Authentication type: basic, oauth, api_key, certificate")
    auth_config: Optional[Dict[str, Any]] = Field(None, description="Authentication configuration (encrypted)")
    refresh_schedule: Optional[str] = Field(None, description="Cron expression for data refresh")
    validation_rules: Optional[Dict[str, Any]] = Field(None, description="Custom validation rules")


class DataSourceResponse(BaseModel):
    id: int
    cycle_id: int
    report_id: int
    name: str
    description: Optional[str]
    source_type: DataSourceTypeEnum
    is_active: bool
    connection_config: Dict[str, Any]
    auth_type: Optional[str]
    auth_config: Optional[Dict[str, Any]]
    refresh_schedule: Optional[str]
    last_sync_at: Optional[datetime]
    last_sync_status: Optional[str]
    last_sync_message: Optional[str]
    validation_rules: Optional[Dict[str, Any]]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ===================== PDE Mapping Schemas =====================

class PDEMappingCreateRequest(BaseModel):
    attribute_id: int = Field(..., description="ID of the report attribute")
    data_source_id: Optional[int] = Field(None, description="ID of the data source")
    pde_name: str = Field(..., description="Name of the Physical Data Element")
    pde_code: str = Field(..., description="Unique code for the PDE")
    pde_description: Optional[str] = Field(None, description="Description of the PDE")
    source_field: Optional[str] = Field(None, description="Field in the data source")
    transformation_rule: Optional[Dict[str, Any]] = Field(None, description="Transformation rules")
    mapping_type: Optional[str] = Field(None, description="Type: direct, calculated, lookup, conditional")
    
    # LLM-assisted fields
    llm_suggested_mapping: Optional[Dict[str, Any]] = None
    llm_confidence_score: Optional[int] = None
    llm_mapping_rationale: Optional[str] = None
    llm_alternative_mappings: Optional[List[Dict[str, Any]]] = None
    mapping_confirmed_by_user: bool = False
    
    # Business metadata
    business_process: Optional[str] = None
    business_owner: Optional[str] = None
    data_steward: Optional[str] = None
    
    # Security classification
    information_security_classification: Optional[InformationSecurityClassification] = None
    
    # Profiling criteria
    profiling_criteria: Optional[Dict[str, Any]] = Field(None, description="Timeframe and filters for data profiling")


class PDEMappingResponse(BaseModel):
    id: int
    cycle_id: int
    report_id: int
    attribute_id: int
    attribute_name: Optional[str] = None
    data_source_id: Optional[int]
    data_source_name: Optional[str] = None
    
    pde_name: str
    pde_code: str
    pde_description: Optional[str]
    source_field: Optional[str]
    source_table: Optional[str] = None  # Extracted table name
    source_column: Optional[str] = None  # Extracted column name
    column_data_type: Optional[str] = None  # Column data type from schema
    transformation_rule: Optional[Dict[str, Any]]
    mapping_type: Optional[str]
    
    llm_suggested_mapping: Optional[Dict[str, Any]]
    llm_confidence_score: Optional[int]
    llm_mapping_rationale: Optional[str]
    llm_alternative_mappings: Optional[List[Dict[str, Any]]]
    mapping_confirmed_by_user: bool
    
    business_process: Optional[str]
    business_owner: Optional[str]
    data_steward: Optional[str]
    
    criticality: Optional[str]
    risk_level: Optional[str]
    regulatory_flag: bool
    pii_flag: bool
    
    information_security_classification: Optional[str]
    profiling_criteria: Optional[Dict[str, Any]]
    
    is_validated: bool
    validation_message: Optional[str]
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        populate_by_name = True
    
    @classmethod
    def from_orm_with_relationships(cls, pde_mapping):
        """Create response with relationships properly loaded"""
        # Extract table and column from source_field
        source_field_parts = pde_mapping.source_field.split('.') if pde_mapping.source_field else []
        
        # Handle different formats: [database.]schema.table.column, table.column, or just column
        if len(source_field_parts) >= 3:
            # Format: schema.table.column or database.schema.table.column
            # Always take the last two parts as table.column
            source_table = source_field_parts[-2]  # Second to last part (table)
            source_column = source_field_parts[-1]  # Last part (column)
        elif len(source_field_parts) == 2:
            # Format: table.column
            source_table = source_field_parts[0]
            source_column = source_field_parts[1]
        elif len(source_field_parts) == 1:
            # Format: just column name
            source_table = None
            source_column = source_field_parts[0]
        else:
            source_table = None
            source_column = None
        
        # If we don't have a table but have llm_suggested_mapping, try to extract from there
        if not source_table and hasattr(pde_mapping, 'llm_suggested_mapping') and pde_mapping.llm_suggested_mapping:
            llm_mapping = pde_mapping.llm_suggested_mapping
            if isinstance(llm_mapping, dict):
                source_table = llm_mapping.get('table_name') or llm_mapping.get('table')
        
        data = {
            "id": pde_mapping.id,
            "cycle_id": pde_mapping.cycle_id,
            "report_id": pde_mapping.report_id,
            "attribute_id": pde_mapping.attribute_id,
            "attribute_name": pde_mapping.attribute.attribute_name if pde_mapping.attribute else None,
            "data_source_id": pde_mapping.data_source_id,
            "data_source_name": pde_mapping.data_source.name if pde_mapping.data_source else None,
            "pde_name": pde_mapping.pde_name,
            "pde_code": pde_mapping.pde_code,
            "pde_description": pde_mapping.pde_description,
            "source_field": pde_mapping.source_field,
            "source_table": source_table,
            "source_column": source_column,
            "column_data_type": getattr(pde_mapping, 'column_data_type', None),  # Will be populated by API
            "transformation_rule": pde_mapping.transformation_rule,
            "mapping_type": pde_mapping.mapping_type,
            "llm_suggested_mapping": pde_mapping.llm_suggested_mapping,
            "llm_confidence_score": pde_mapping.llm_confidence_score,
            "llm_mapping_rationale": pde_mapping.llm_mapping_rationale,
            "llm_alternative_mappings": pde_mapping.llm_alternative_mappings,
            "mapping_confirmed_by_user": pde_mapping.mapping_confirmed_by_user,
            "business_process": pde_mapping.business_process,
            "business_owner": pde_mapping.business_owner,
            "data_steward": pde_mapping.data_steward,
            "criticality": pde_mapping.criticality,
            "risk_level": pde_mapping.risk_level,
            "regulatory_flag": pde_mapping.regulatory_flag if pde_mapping.regulatory_flag is not None else False,
            "pii_flag": pde_mapping.pii_flag if pde_mapping.pii_flag is not None else False,
            "information_security_classification": pde_mapping.information_security_classification,
            "profiling_criteria": pde_mapping.profiling_criteria,
            "is_validated": pde_mapping.is_validated if pde_mapping.is_validated is not None else False,
            "validation_message": pde_mapping.validation_message,
            "created_at": getattr(pde_mapping, 'created_at', None) or datetime.utcnow(),
            "updated_at": getattr(pde_mapping, 'updated_at', None) or datetime.utcnow()
        }
        return cls(**data)


class LLMMappingSuggestionResponse(BaseModel):
    attribute_id: int
    attribute_name: str
    llm_suggested_mapping: Dict[str, Any]
    confidence_score: int
    rationale: str
    alternative_mappings: List[Dict[str, Any]]


# ===================== PDE Classification Schemas =====================

class PDEClassificationRequest(BaseModel):
    pde_mapping_id: int
    classification_type: str = Field(..., description="Type: criticality, risk, regulatory, data_sensitivity, information_security")
    classification_value: str = Field(..., description="Value: high, medium, low, HRCI, Confidential, Proprietary, Public, etc.")
    classification_reason: Optional[str] = None
    
    # For updating the PDE mapping
    criticality: Optional[str] = None
    risk_level: Optional[str] = None
    regulatory_flag: bool = False
    pii_flag: bool = False
    information_security_classification: Optional[str] = None
    
    # LLM suggestions
    llm_suggested_criticality: Optional[str] = None
    llm_suggested_risk_level: Optional[str] = None
    llm_classification_rationale: Optional[str] = None
    llm_regulatory_references: Optional[List[str]] = None
    
    # Evidence
    evidence_type: Optional[str] = None
    evidence_reference: Optional[str] = None
    evidence_details: Optional[Dict[str, Any]] = None


class PDEClassificationResponse(BaseModel):
    id: int
    pde_mapping_id: int
    classification_type: str
    classification_value: str
    classification_reason: Optional[str]
    
    evidence_type: Optional[str]
    evidence_reference: Optional[str]
    evidence_details: Optional[Dict[str, Any]]
    
    classified_by: Optional[int]
    reviewed_by: Optional[int]
    approved_by: Optional[int]
    review_status: Optional[str]
    review_notes: Optional[str]
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class LLMClassificationSuggestionResponse(BaseModel):
    pde_mapping_id: int
    pde_name: str
    llm_suggested_criticality: str
    llm_suggested_risk_level: str
    llm_suggested_information_security_classification: str
    llm_regulatory_references: List[str]
    llm_classification_rationale: str
    regulatory_flag: bool
    pii_flag: bool
    evidence: Dict[str, Any]
    security_controls: Optional[Dict[str, Any]] = None