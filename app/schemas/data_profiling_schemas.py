"""
Data Profiling Schemas - Request and Response Models

This module contains Pydantic schemas for the unified data profiling API endpoints.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


class VersionStatus(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class RuleType(str, Enum):
    COMPLETENESS = "completeness"
    VALIDITY = "validity"
    ACCURACY = "accuracy"
    CONSISTENCY = "consistency"
    UNIQUENESS = "uniqueness"


class Decision(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUEST_CHANGES = "request_changes"


class RuleStatus(str, Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class DataSourceType(str, Enum):
    FILE_UPLOAD = "file_upload"
    DATABASE_SOURCE = "database_source"


# Request Models
class CreateVersionRequest(BaseModel):
    """Request model for creating a new data profiling version"""
    data_source_config: Optional[Dict[str, Any]] = Field(
        None, 
        description="Data source configuration"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "data_source_config": {
                    "type": "database_source",
                    "table_name": "customer_data",
                    "planning_data_source_id": 123
                }
            }
        }


class TesterDecisionRequest(BaseModel):
    """Request model for tester decision on a rule"""
    decision: Decision = Field(..., description="Tester decision")
    notes: Optional[str] = Field(None, description="Decision notes")
    
    class Config:
        schema_extra = {
            "example": {
                "decision": "approved",
                "notes": "Rule looks good for execution"
            }
        }


class ReportOwnerDecisionRequest(BaseModel):
    """Request model for report owner decision on a rule"""
    decision: Decision = Field(..., description="Report owner decision")
    notes: Optional[str] = Field(None, description="Decision notes")
    
    class Config:
        schema_extra = {
            "example": {
                "decision": "approved",
                "notes": "Approved for execution"
            }
        }


class VersionSubmissionRequest(BaseModel):
    """Request model for submitting a version for approval"""
    submission_notes: Optional[str] = Field(None, description="Submission notes")
    
    class Config:
        schema_extra = {
            "example": {
                "submission_notes": "All rules reviewed and ready for approval"
            }
        }


class VersionApprovalRequest(BaseModel):
    """Request model for approving a version"""
    approval_notes: Optional[str] = Field(None, description="Approval notes")
    
    class Config:
        schema_extra = {
            "example": {
                "approval_notes": "Version approved for execution"
            }
        }


class VersionRejectionRequest(BaseModel):
    """Request model for rejecting a version"""
    reason: str = Field(..., description="Rejection reason")
    
    class Config:
        schema_extra = {
            "example": {
                "reason": "Several rules need refinement before execution"
            }
        }


# Response Models
class DataProfilingVersionResponse(BaseModel):
    """Response model for data profiling version"""
    version_id: str = Field(..., description="Version ID")
    phase_id: int = Field(..., description="Phase ID")
    version_number: int = Field(..., description="Version number")
    version_status: VersionStatus = Field(..., description="Version status")
    total_rules: int = Field(..., description="Total number of rules")
    approved_rules: int = Field(..., description="Number of approved rules")
    rejected_rules: int = Field(..., description="Number of rejected rules")
    data_source_type: Optional[DataSourceType] = Field(None, description="Data source type")
    source_table_name: Optional[str] = Field(None, description="Source table name")
    source_file_path: Optional[str] = Field(None, description="Source file path")
    overall_quality_score: Optional[float] = Field(None, description="Overall quality score")
    execution_job_id: Optional[str] = Field(None, description="Execution job ID")
    submitted_at: Optional[datetime] = Field(None, description="Submission timestamp")
    submitted_by_id: Optional[int] = Field(None, description="Submitted by user ID")
    approved_at: Optional[datetime] = Field(None, description="Approval timestamp")
    approved_by_id: Optional[int] = Field(None, description="Approved by user ID")
    rejection_reason: Optional[str] = Field(None, description="Rejection reason")
    created_at: datetime = Field(..., description="Creation timestamp")
    created_by_id: int = Field(..., description="Created by user ID")
    
    class Config:
        from_attributes = True


class ProfilingRuleResponse(BaseModel):
    """Response model for profiling rule"""
    rule_id: str = Field(..., description="Rule ID")
    version_id: str = Field(..., description="Version ID")
    attribute_id: int = Field(..., description="Attribute ID")
    rule_name: str = Field(..., description="Rule name")
    rule_type: RuleType = Field(..., description="Rule type")
    rule_description: Optional[str] = Field(None, description="Rule description")
    rule_code: Optional[str] = Field(None, description="Rule code")
    rule_parameters: Optional[Dict[str, Any]] = Field(None, description="Rule parameters")
    llm_provider: Optional[str] = Field(None, description="LLM provider")
    llm_rationale: Optional[str] = Field(None, description="LLM rationale")
    llm_confidence_score: Optional[float] = Field(None, description="LLM confidence score")
    regulatory_reference: Optional[str] = Field(None, description="Regulatory reference")
    severity: Optional[Severity] = Field(None, description="Rule severity")
    execution_order: Optional[int] = Field(None, description="Execution order")
    tester_decision: Optional[Decision] = Field(None, description="Tester decision")
    tester_notes: Optional[str] = Field(None, description="Tester notes")
    tester_decided_at: Optional[datetime] = Field(None, description="Tester decision timestamp")
    report_owner_decision: Optional[Decision] = Field(None, description="Report owner decision")
    report_owner_notes: Optional[str] = Field(None, description="Report owner notes")
    report_owner_decided_at: Optional[datetime] = Field(None, description="Report owner decision timestamp")
    status: RuleStatus = Field(..., description="Rule status")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        from_attributes = True


class ExecutionResultsResponse(BaseModel):
    """Response model for execution results"""
    status: str = Field(..., description="Execution status")
    job_id: Optional[str] = Field(None, description="Job ID")
    total_records_processed: int = Field(..., description="Total records processed")
    overall_quality_score: float = Field(..., description="Overall quality score")
    rules_executed: int = Field(..., description="Number of rules executed")
    execution_summary: Dict[str, Any] = Field(..., description="Execution summary")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "completed",
                "job_id": "data_profiling_execution_123",
                "total_records_processed": 10000,
                "overall_quality_score": 95.5,
                "rules_executed": 15,
                "execution_summary": {
                    "completeness_rules": 5,
                    "validity_rules": 3,
                    "accuracy_rules": 4,
                    "consistency_rules": 2,
                    "uniqueness_rules": 1
                }
            }
        }