"""
Pydantic schemas for Sample Selection V2 API
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum
import uuid

from app.models.sample_selection import VersionStatus, SampleCategory, SampleDecision, SampleSource


# Enum schemas for API
class VersionStatusEnum(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class SampleCategoryEnum(str, Enum):
    CLEAN = "clean"
    ANOMALY = "anomaly"
    BOUNDARY = "boundary"


class SampleDecisionEnum(str, Enum):
    INCLUDE = "include"
    EXCLUDE = "exclude"
    PENDING = "pending"


class SampleSourceEnum(str, Enum):
    TESTER = "tester"
    LLM = "llm"
    MANUAL = "manual"
    CARRIED_FORWARD = "carried_forward"


# Base schemas
class SampleSelectionVersionBase(BaseModel):
    """Base schema for sample selection version"""
    selection_criteria: Dict[str, Any] = Field(..., description="Selection criteria for samples")
    target_sample_size: int = Field(..., ge=1, description="Target number of samples")
    intelligent_sampling_config: Optional[Dict[str, Any]] = Field(None, description="Intelligent sampling configuration")
    data_source_config: Optional[Dict[str, Any]] = Field(None, description="Data source configuration")
    submission_notes: Optional[str] = Field(None, description="Notes for submission")
    approval_notes: Optional[str] = Field(None, description="Notes for approval")


class SampleSelectionSampleBase(BaseModel):
    """Base schema for sample selection sample"""
    lob_id: int = Field(..., description="LOB ID for the sample")
    sample_identifier: str = Field(..., description="Unique identifier for the sample")
    sample_data: Dict[str, Any] = Field(..., description="Sample data content")
    sample_category: SampleCategoryEnum = Field(..., description="Sample category")
    sample_source: SampleSourceEnum = Field(SampleSourceEnum.MANUAL, description="Source of the sample")
    risk_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Risk score (0-1)")
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence score (0-1)")
    generation_metadata: Optional[Dict[str, Any]] = Field(None, description="Generation metadata")
    validation_results: Optional[Dict[str, Any]] = Field(None, description="Validation results")
    carry_forward_reason: Optional[str] = Field(None, description="Reason for carry forward")


# Request schemas
class CreateSampleSelectionVersionRequest(SampleSelectionVersionBase):
    """Request schema for creating a new sample selection version"""
    phase_id: int = Field(..., description="Phase ID")
    workflow_execution_id: str = Field(..., description="Temporal workflow execution ID")
    workflow_run_id: str = Field(..., description="Temporal workflow run ID")
    activity_name: str = Field(..., description="Activity name")
    
    @validator('workflow_execution_id')
    def validate_workflow_execution_id(cls, v):
        if not v or not v.strip():
            raise ValueError('workflow_execution_id cannot be empty')
        return v.strip()


class AddSamplesRequest(BaseModel):
    """Request schema for adding samples to a version"""
    samples: List[SampleSelectionSampleBase] = Field(..., description="List of samples to add")
    
    @validator('samples')
    def validate_samples(cls, v):
        if not v:
            raise ValueError('At least one sample must be provided')
        return v


class GenerateIntelligentSamplesRequest(BaseModel):
    """Request schema for generating intelligent samples"""
    custom_distribution: Optional[Dict[str, float]] = Field(None, description="Custom distribution ratios")
    profiling_rules: Optional[List[Dict[str, Any]]] = Field(None, description="Profiling rules for anomaly detection")
    data_source_config: Optional[Dict[str, Any]] = Field(None, description="Data source configuration")
    
    @validator('custom_distribution')
    def validate_distribution(cls, v):
        if v is not None:
            if not isinstance(v, dict):
                raise ValueError('Distribution must be a dictionary')
            
            required_keys = {'clean', 'anomaly', 'boundary'}
            if not all(key in v for key in required_keys):
                raise ValueError(f'Distribution must include all keys: {required_keys}')
            
            if abs(sum(v.values()) - 1.0) > 0.01:
                raise ValueError('Distribution ratios must sum to 1.0')
            
            for key, value in v.items():
                if not isinstance(value, (int, float)) or value < 0:
                    raise ValueError(f'Distribution value for {key} must be non-negative number')
        
        return v


class CarryForwardSamplesRequest(BaseModel):
    """Request schema for carrying forward samples"""
    source_version_id: uuid.UUID = Field(..., description="Source version ID")
    sample_filters: Optional[Dict[str, Any]] = Field(None, description="Filters for samples to carry forward")


class SubmitVersionRequest(BaseModel):
    """Request schema for submitting version for approval"""
    submission_notes: Optional[str] = Field(None, description="Notes for submission")


class ApproveVersionRequest(BaseModel):
    """Request schema for approving a version"""
    approval_notes: Optional[str] = Field(None, description="Notes for approval")


class RejectVersionRequest(BaseModel):
    """Request schema for rejecting a version"""
    rejection_notes: str = Field(..., description="Notes for rejection")


class UpdateSampleDecisionRequest(BaseModel):
    """Request schema for updating sample decision"""
    decision_type: str = Field(..., description="Type of decision (tester or report_owner)")
    decision: SampleDecisionEnum = Field(..., description="Decision")
    decision_notes: Optional[str] = Field(None, description="Decision notes")
    
    @validator('decision_type')
    def validate_decision_type(cls, v):
        if v not in ['tester', 'report_owner']:
            raise ValueError('decision_type must be either "tester" or "report_owner"')
        return v


# Response schemas
class SampleSelectionSampleResponse(SampleSelectionSampleBase):
    """Response schema for sample selection sample"""
    sample_id: uuid.UUID = Field(..., description="Sample ID")
    version_id: uuid.UUID = Field(..., description="Version ID")
    phase_id: int = Field(..., description="Phase ID")
    
    # Decision tracking
    tester_decision: SampleDecisionEnum = Field(..., description="Tester decision")
    tester_decision_notes: Optional[str] = Field(None, description="Tester decision notes")
    tester_decision_at: Optional[datetime] = Field(None, description="Tester decision timestamp")
    tester_decision_by_id: Optional[int] = Field(None, description="Tester decision by user ID")
    
    report_owner_decision: SampleDecisionEnum = Field(..., description="Report owner decision")
    report_owner_decision_notes: Optional[str] = Field(None, description="Report owner decision notes")
    report_owner_decision_at: Optional[datetime] = Field(None, description="Report owner decision timestamp")
    report_owner_decision_by_id: Optional[int] = Field(None, description="Report owner decision by user ID")
    
    # Carry-forward tracking
    carried_from_version_id: Optional[uuid.UUID] = Field(None, description="Carried from version ID")
    carried_from_sample_id: Optional[uuid.UUID] = Field(None, description="Carried from sample ID")
    
    # Status properties
    is_approved: bool = Field(..., description="Whether sample is approved")
    is_rejected: bool = Field(..., description="Whether sample is rejected")
    needs_review: bool = Field(..., description="Whether sample needs review")
    is_carried_forward: bool = Field(..., description="Whether sample was carried forward")
    
    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    # LOB information
    lob_name: Optional[str] = Field(None, description="LOB name")
    
    class Config:
        from_attributes = True


class SampleSelectionVersionResponse(SampleSelectionVersionBase):
    """Response schema for sample selection version"""
    version_id: uuid.UUID = Field(..., description="Version ID")
    phase_id: int = Field(..., description="Phase ID")
    version_number: int = Field(..., description="Version number")
    version_status: VersionStatusEnum = Field(..., description="Version status")
    parent_version_id: Optional[uuid.UUID] = Field(None, description="Parent version ID")
    
    # Temporal workflow context
    workflow_execution_id: str = Field(..., description="Temporal workflow execution ID")
    workflow_run_id: str = Field(..., description="Temporal workflow run ID")
    activity_name: str = Field(..., description="Activity name")
    
    # Sample metrics
    actual_sample_size: int = Field(..., description="Actual number of samples")
    distribution_metrics: Optional[Dict[str, Any]] = Field(None, description="Distribution metrics")
    
    # Timestamps and tracking
    created_at: datetime = Field(..., description="Creation timestamp")
    created_by_id: int = Field(..., description="Created by user ID")
    
    submitted_at: Optional[datetime] = Field(None, description="Submission timestamp")
    submitted_by_id: Optional[int] = Field(None, description="Submitted by user ID")
    
    approved_at: Optional[datetime] = Field(None, description="Approval timestamp")
    approved_by_id: Optional[int] = Field(None, description="Approved by user ID")
    
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    # Status properties
    is_current_version: bool = Field(..., description="Whether this is the current version")
    can_be_edited: bool = Field(..., description="Whether version can be edited")
    
    # User information
    created_by_name: Optional[str] = Field(None, description="Created by user name")
    submitted_by_name: Optional[str] = Field(None, description="Submitted by user name")
    approved_by_name: Optional[str] = Field(None, description="Approved by user name")
    
    # Samples (optional, loaded on demand)
    samples: Optional[List[SampleSelectionSampleResponse]] = Field(None, description="Samples in this version")
    
    class Config:
        from_attributes = True


class SampleSelectionVersionWithSamplesResponse(SampleSelectionVersionResponse):
    """Response schema for version with samples included"""
    samples: List[SampleSelectionSampleResponse] = Field(..., description="Samples in this version")


class SampleSelectionVersionListResponse(BaseModel):
    """Response schema for list of versions"""
    versions: List[SampleSelectionVersionResponse] = Field(..., description="List of versions")
    total_count: int = Field(..., description="Total number of versions")
    phase_id: int = Field(..., description="Phase ID")


class SampleSelectionVersionStatisticsResponse(BaseModel):
    """Response schema for version statistics"""
    version_info: Dict[str, Any] = Field(..., description="Version information")
    sample_counts: Dict[str, Any] = Field(..., description="Sample count statistics")
    category_distribution: Dict[str, int] = Field(..., description="Distribution by category")
    source_distribution: Dict[str, int] = Field(..., description="Distribution by source")
    lob_distribution: Dict[str, int] = Field(..., description="Distribution by LOB")
    decision_statistics: Dict[str, Any] = Field(..., description="Decision statistics")
    risk_statistics: Dict[str, Any] = Field(..., description="Risk score statistics")


class IntelligentSamplingResultResponse(BaseModel):
    """Response schema for intelligent sampling results"""
    generation_summary: Dict[str, Any] = Field(..., description="Generation summary")
    samples_created: List[SampleSelectionSampleResponse] = Field(..., description="Created samples")
    total_generated: int = Field(..., description="Total samples generated")
    distribution_achieved: Dict[str, Any] = Field(..., description="Achieved distribution")
    generation_quality: float = Field(..., description="Generation quality score")


class CarryForwardResultResponse(BaseModel):
    """Response schema for carry forward results"""
    carried_samples: List[SampleSelectionSampleResponse] = Field(..., description="Carried forward samples")
    total_carried: int = Field(..., description="Total samples carried forward")
    source_version_id: uuid.UUID = Field(..., description="Source version ID")
    target_version_id: uuid.UUID = Field(..., description="Target version ID")
    filters_applied: Optional[Dict[str, Any]] = Field(None, description="Filters applied")


# Bulk operation schemas
class BulkUpdateSampleDecisionsRequest(BaseModel):
    """Request schema for bulk updating sample decisions"""
    sample_ids: List[uuid.UUID] = Field(..., description="List of sample IDs")
    decision_type: str = Field(..., description="Type of decision (tester or report_owner)")
    decision: SampleDecisionEnum = Field(..., description="Decision")
    decision_notes: Optional[str] = Field(None, description="Decision notes")
    
    @validator('sample_ids')
    def validate_sample_ids(cls, v):
        if not v:
            raise ValueError('At least one sample ID must be provided')
        return v
    
    @validator('decision_type')
    def validate_decision_type(cls, v):
        if v not in ['tester', 'report_owner']:
            raise ValueError('decision_type must be either "tester" or "report_owner"')
        return v


class BulkUpdateSampleDecisionsResponse(BaseModel):
    """Response schema for bulk update results"""
    updated_samples: List[SampleSelectionSampleResponse] = Field(..., description="Updated samples")
    total_updated: int = Field(..., description="Total samples updated")
    failed_updates: List[Dict[str, Any]] = Field(..., description="Failed updates with reasons")


# Error schemas
class SampleSelectionErrorResponse(BaseModel):
    """Error response schema"""
    error: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")


# Query parameter schemas
class SampleSelectionVersionQueryParams(BaseModel):
    """Query parameters for version endpoints"""
    include_samples: bool = Field(False, description="Include samples in response")
    status: Optional[VersionStatusEnum] = Field(None, description="Filter by status")
    limit: Optional[int] = Field(None, ge=1, le=100, description="Limit results")
    offset: Optional[int] = Field(None, ge=0, description="Offset results")


class SampleSelectionSampleQueryParams(BaseModel):
    """Query parameters for sample endpoints"""
    category: Optional[SampleCategoryEnum] = Field(None, description="Filter by category")
    source: Optional[SampleSourceEnum] = Field(None, description="Filter by source")
    decision_status: Optional[str] = Field(None, description="Filter by decision status")
    lob_id: Optional[int] = Field(None, description="Filter by LOB ID")
    min_risk_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum risk score")
    max_risk_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Maximum risk score")
    limit: Optional[int] = Field(None, ge=1, le=100, description="Limit results")
    offset: Optional[int] = Field(None, ge=0, description="Offset results")
    
    @validator('decision_status')
    def validate_decision_status(cls, v):
        if v is not None and v not in ['approved', 'rejected', 'pending', 'needs_review']:
            raise ValueError('decision_status must be one of: approved, rejected, pending, needs_review')
        return v