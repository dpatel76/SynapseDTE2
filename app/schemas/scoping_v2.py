"""
Scoping V2 Schemas - Request/Response models for the new scoping system

This module contains Pydantic schemas for the new consolidated scoping system,
providing validation and serialization for API endpoints.
"""

from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, validator, root_validator
from enum import Enum
from uuid import UUID

# Re-export enums for convenience
from app.models.scoping_v2 import (
    VersionStatus, TesterDecision, ReportOwnerDecision, AttributeStatus
)


# Base schemas
class ScopingBaseSchema(BaseModel):
    """Base schema for scoping models"""
    
    class Config:
        from_attributes = True
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
            Decimal: lambda v: float(v) if v else None
        }


# Version schemas
class ScopingVersionCreate(ScopingBaseSchema):
    """Schema for creating a new scoping version"""
    
    phase_id: int = Field(..., description="Workflow phase ID")
    workflow_activity_id: Optional[int] = Field(None, description="Workflow activity ID")
    workflow_execution_id: Optional[str] = Field(None, description="Temporal workflow execution ID")
    workflow_run_id: Optional[str] = Field(None, description="Temporal workflow run ID")
    activity_name: Optional[str] = Field(None, description="Activity name")
    notes: Optional[str] = Field(None, description="Creation notes")
    
    @validator('phase_id')
    def validate_phase_id(cls, v):
        if v <= 0:
            raise ValueError("Phase ID must be positive")
        return v


class ScopingVersionUpdate(ScopingBaseSchema):
    """Schema for updating a scoping version"""
    
    submission_notes: Optional[str] = Field(None, description="Submission notes")
    approval_notes: Optional[str] = Field(None, description="Approval notes")
    rejection_reason: Optional[str] = Field(None, description="Rejection reason")
    requested_changes: Optional[Dict[str, Any]] = Field(None, description="Requested changes")
    resource_impact_assessment: Optional[str] = Field(None, description="Resource impact assessment")
    risk_coverage_assessment: Optional[str] = Field(None, description="Risk coverage assessment")


class ScopingVersionResponse(ScopingBaseSchema):
    """Schema for scoping version responses"""
    
    version_id: UUID
    phase_id: int
    workflow_activity_id: Optional[int]
    version_number: int
    version_status: VersionStatus
    parent_version_id: Optional[UUID]
    
    # Temporal workflow context
    workflow_execution_id: Optional[str]
    workflow_run_id: Optional[str]
    activity_name: Optional[str]
    
    # Summary statistics
    total_attributes: int
    scoped_attributes: int
    declined_attributes: int
    override_count: int
    cde_count: int
    recommendation_accuracy: Optional[float]
    
    # Workflow fields
    submission_notes: Optional[str]
    submitted_by_id: Optional[int]
    submitted_at: Optional[datetime]
    
    approval_notes: Optional[str]
    approved_by_id: Optional[int]
    approved_at: Optional[datetime]
    
    rejection_reason: Optional[str]
    requested_changes: Optional[Dict[str, Any]]
    
    # Risk assessment
    resource_impact_assessment: Optional[str]
    risk_coverage_assessment: Optional[str]
    
    # Audit fields
    created_at: datetime
    created_by_id: int
    updated_at: datetime
    updated_by_id: int
    
    # Computed properties
    is_draft: bool = Field(description="Whether this version is in draft status")
    is_pending_approval: bool = Field(description="Whether this version is pending approval")
    is_approved: bool = Field(description="Whether this version is approved")
    is_rejected: bool = Field(description="Whether this version is rejected")
    is_superseded: bool = Field(description="Whether this version is superseded")
    can_be_edited: bool = Field(description="Whether this version can be edited")
    can_be_submitted: bool = Field(description="Whether this version can be submitted")
    can_be_approved: bool = Field(description="Whether this version can be approved")
    is_current: bool = Field(description="Whether this is the current active version")
    scoping_percentage: float = Field(description="Percentage of attributes scoped in")
    override_percentage: float = Field(description="Percentage of attributes with overrides")


class ScopingVersionSummary(ScopingBaseSchema):
    """Simplified version summary for lists"""
    
    version_id: UUID
    phase_id: int
    version_number: int
    version_status: VersionStatus
    total_attributes: int
    scoped_attributes: int
    declined_attributes: int
    override_count: int
    created_at: datetime
    submitted_at: Optional[datetime]
    approved_at: Optional[datetime]
    can_be_edited: bool
    is_current: bool


# Attribute schemas
class LLMRecommendationCreate(ScopingBaseSchema):
    """Schema for LLM recommendation data"""
    
    recommended_action: str = Field(..., description="Recommended action (test/skip)")
    confidence_score: Optional[float] = Field(None, ge=0, le=1, description="Confidence score")
    rationale: Optional[str] = Field(None, description="Rationale for recommendation")
    provider: Optional[str] = Field(None, description="LLM provider")
    processing_time_ms: Optional[int] = Field(None, ge=0, description="Processing time in ms")
    request_payload: Optional[Dict[str, Any]] = Field(None, description="Request payload")
    response_payload: Optional[Dict[str, Any]] = Field(None, description="Response payload")
    
    # Metadata
    is_cde: bool = Field(False, description="Whether this is a CDE")
    is_primary_key: bool = Field(False, description="Whether this is a primary key")
    has_historical_issues: bool = Field(False, description="Whether this has historical issues")
    data_quality_score: Optional[float] = Field(None, ge=0, le=1, description="Data quality score")
    data_quality_issues: Optional[Dict[str, Any]] = Field(None, description="Data quality issues")
    expected_source_documents: Optional[List[str]] = Field(None, description="Expected source documents")
    search_keywords: Optional[List[str]] = Field(None, description="Search keywords")
    risk_factors: Optional[List[str]] = Field(None, description="Risk factors")
    
    @validator('recommended_action')
    def validate_recommended_action(cls, v):
        if v not in ['test', 'skip']:
            raise ValueError("Recommended action must be 'test' or 'skip'")
        return v


class ScopingAttributeCreate(ScopingBaseSchema):
    """Schema for creating scoping attributes"""
    
    attribute_id: int = Field(..., description="Planning attribute ID")
    llm_recommendation: LLMRecommendationCreate = Field(..., description="LLM recommendation")
    
    @validator('attribute_id')
    def validate_attribute_id(cls, v):
        if v <= 0:
            raise ValueError("Planning attribute ID must be positive")
        return v


class ScopingAttributesBulkCreate(ScopingBaseSchema):
    """Schema for bulk creating scoping attributes"""
    
    attributes: List[ScopingAttributeCreate] = Field(..., description="List of attributes to create")
    
    @validator('attributes')
    def validate_attributes(cls, v):
        if not v:
            raise ValueError("At least one attribute must be provided")
        if len(v) > 1000:
            raise ValueError("Cannot create more than 1000 attributes at once")
        return v


class TesterDecisionCreate(ScopingBaseSchema):
    """Schema for tester decision"""
    
    decision: TesterDecision = Field(..., description="Tester decision")
    final_scoping: bool = Field(..., description="Final scoping decision")
    rationale: Optional[str] = Field(None, description="Decision rationale")
    override_reason: Optional[str] = Field(None, description="Override reason (required for override)")
    
    @root_validator
    def validate_override_reason(cls, values):
        decision = values.get('decision')
        override_reason = values.get('override_reason')
        
        if decision == TesterDecision.OVERRIDE and not override_reason:
            raise ValueError("Override reason is required when decision is override")
        
        return values


class ReportOwnerDecisionCreate(ScopingBaseSchema):
    """Schema for report owner decision"""
    
    decision: ReportOwnerDecision = Field(..., description="Report owner decision")
    notes: Optional[str] = Field(None, description="Decision notes")


class ScopingAttributeUpdate(ScopingBaseSchema):
    """Schema for updating scoping attributes"""
    
    tester_decision: Optional[TesterDecision] = Field(None, description="Tester decision")
    final_scoping: Optional[bool] = Field(None, description="Final scoping decision")
    tester_rationale: Optional[str] = Field(None, description="Tester rationale")
    override_reason: Optional[str] = Field(None, description="Override reason")
    
    report_owner_decision: Optional[ReportOwnerDecision] = Field(None, description="Report owner decision")
    report_owner_notes: Optional[str] = Field(None, description="Report owner notes")
    
    # Metadata updates
    data_quality_score: Optional[float] = Field(None, ge=0, le=1, description="Data quality score")
    data_quality_issues: Optional[Dict[str, Any]] = Field(None, description="Data quality issues")
    expected_source_documents: Optional[List[str]] = Field(None, description="Expected source documents")
    search_keywords: Optional[List[str]] = Field(None, description="Search keywords")
    risk_factors: Optional[List[str]] = Field(None, description="Risk factors")


class ScopingAttributeResponse(ScopingBaseSchema):
    """Schema for scoping attribute responses"""
    
    attribute_id: UUID
    version_id: UUID
    phase_id: int
    attribute_id: int
    
    # LLM recommendation
    llm_recommendation: Dict[str, Any]
    llm_provider: Optional[str]
    llm_confidence_score: Optional[Decimal]
    llm_rationale: Optional[str]
    llm_processing_time_ms: Optional[int]
    
    # Tester decision
    tester_decision: Optional[TesterDecision]
    final_scoping: Optional[bool]
    tester_rationale: Optional[str]
    tester_decided_by_id: Optional[int]
    tester_decided_at: Optional[datetime]
    
    # Report owner decision
    report_owner_decision: Optional[ReportOwnerDecision]
    report_owner_notes: Optional[str]
    report_owner_decided_by_id: Optional[int]
    report_owner_decided_at: Optional[datetime]
    
    # Metadata
    is_override: bool
    override_reason: Optional[str]
    is_cde: bool
    has_historical_issues: bool
    is_primary_key: bool
    
    data_quality_score: Optional[float]
    data_quality_issues: Optional[Dict[str, Any]]
    expected_source_documents: Optional[List[str]]
    search_keywords: Optional[List[str]]
    risk_factors: Optional[List[str]]
    
    status: AttributeStatus
    
    # Audit fields
    created_at: datetime
    created_by_id: int
    updated_at: datetime
    updated_by_id: int
    
    # Computed properties
    has_tester_decision: bool = Field(description="Whether tester has made a decision")
    has_report_owner_decision: bool = Field(description="Whether report owner has made a decision")
    is_scoped_in: bool = Field(description="Whether this attribute is scoped in")
    is_scoped_out: bool = Field(description="Whether this attribute is scoped out")
    is_pending_decision: bool = Field(description="Whether this attribute is pending decision")
    llm_recommended_action: Optional[str] = Field(description="LLM recommended action")
    llm_agreed_with_tester: Optional[bool] = Field(description="Whether LLM agreed with tester")


class ScopingAttributeSummary(ScopingBaseSchema):
    """Simplified attribute summary for lists"""
    
    attribute_id: UUID
    attribute_id: int
    tester_decision: Optional[TesterDecision]
    final_scoping: Optional[bool]
    report_owner_decision: Optional[ReportOwnerDecision]
    is_override: bool
    is_cde: bool
    is_primary_key: bool
    status: AttributeStatus
    created_at: datetime


# Bulk operation schemas
class BulkTesterDecisionCreate(ScopingBaseSchema):
    """Schema for bulk tester decisions"""
    
    decisions: List[Dict[str, Any]] = Field(..., description="List of decisions")
    
    @validator('decisions')
    def validate_decisions(cls, v):
        if not v:
            raise ValueError("At least one decision must be provided")
        if len(v) > 100:
            raise ValueError("Cannot make more than 100 decisions at once")
        
        for decision in v:
            if 'attribute_id' not in decision:
                raise ValueError("Each decision must have an attribute_id")
            if 'decision' not in decision:
                raise ValueError("Each decision must have a decision")
            if 'final_scoping' not in decision:
                raise ValueError("Each decision must have a final_scoping")
        
        return v


class BulkUpdateResponse(ScopingBaseSchema):
    """Schema for bulk update responses"""
    
    total_requested: int = Field(..., description="Total number of updates requested")
    successful_updates: int = Field(..., description="Number of successful updates")
    failed_updates: int = Field(..., description="Number of failed updates")
    errors: List[Dict[str, Any]] = Field(default=[], description="List of errors")
    updated_attributes: List[UUID] = Field(default=[], description="List of updated attribute IDs")


# Statistics and reporting schemas
class VersionStatistics(ScopingBaseSchema):
    """Schema for version statistics"""
    
    version_id: UUID
    version_number: int
    status: VersionStatus
    
    total_attributes: int
    scoped_attributes: int
    declined_attributes: int
    override_count: int
    cde_count: int
    scoping_percentage: float
    override_percentage: float
    
    decision_progress: Dict[str, Any] = Field(description="Decision progress statistics")
    report_owner_progress: Dict[str, Any] = Field(description="Report owner progress statistics")
    
    llm_accuracy: Optional[float] = Field(description="LLM recommendation accuracy")
    
    created_at: datetime
    submitted_at: Optional[datetime]
    approved_at: Optional[datetime]
    
    can_be_edited: bool
    can_be_submitted: bool
    can_be_approved: bool
    is_current: bool


class AttributeDecisionSummary(ScopingBaseSchema):
    """Schema for attribute decision summary"""
    
    attribute_id: UUID
    attribute_id: int
    status: AttributeStatus
    
    llm_recommendation: Dict[str, Any]
    tester_decision: Optional[Dict[str, Any]]
    report_owner_decision: Optional[Dict[str, Any]]
    
    flags: Dict[str, bool] = Field(description="Attribute flags")
    data_quality: Dict[str, Any] = Field(description="Data quality information")
    
    llm_agreed_with_tester: Optional[bool]
    decision_timeline: List[Dict[str, Any]]


# Query parameter schemas
class VersionQueryParams(ScopingBaseSchema):
    """Schema for version query parameters"""
    
    phase_id: Optional[int] = Field(None, description="Filter by phase ID")
    status: Optional[VersionStatus] = Field(None, description="Filter by status")
    version_number: Optional[int] = Field(None, description="Filter by version number")
    created_after: Optional[datetime] = Field(None, description="Filter by creation date")
    created_before: Optional[datetime] = Field(None, description="Filter by creation date")
    limit: int = Field(10, ge=1, le=100, description="Number of results to return")
    offset: int = Field(0, ge=0, description="Number of results to skip")
    include_attributes: bool = Field(False, description="Include attributes in response")


class AttributeQueryParams(ScopingBaseSchema):
    """Schema for attribute query parameters"""
    
    version_id: Optional[UUID] = Field(None, description="Filter by version ID")
    attribute_id: Optional[int] = Field(None, description="Filter by planning attribute ID")
    status: Optional[AttributeStatus] = Field(None, description="Filter by status")
    tester_decision: Optional[TesterDecision] = Field(None, description="Filter by tester decision")
    report_owner_decision: Optional[ReportOwnerDecision] = Field(None, description="Filter by report owner decision")
    final_scoping: Optional[bool] = Field(None, description="Filter by final scoping decision")
    is_override: Optional[bool] = Field(None, description="Filter by override flag")
    is_cde: Optional[bool] = Field(None, description="Filter by CDE flag")
    is_primary_key: Optional[bool] = Field(None, description="Filter by primary key flag")
    limit: int = Field(10, ge=1, le=100, description="Number of results to return")
    offset: int = Field(0, ge=0, description="Number of results to skip")


# Submission and approval schemas
class VersionSubmissionCreate(ScopingBaseSchema):
    """Schema for version submission"""
    
    submission_notes: Optional[str] = Field(None, description="Submission notes")
    resource_impact_assessment: Optional[str] = Field(None, description="Resource impact assessment")
    risk_coverage_assessment: Optional[str] = Field(None, description="Risk coverage assessment")


class VersionApprovalCreate(ScopingBaseSchema):
    """Schema for version approval"""
    
    approval_notes: Optional[str] = Field(None, description="Approval notes")


class VersionRejectionCreate(ScopingBaseSchema):
    """Schema for version rejection"""
    
    rejection_reason: str = Field(..., description="Rejection reason")
    requested_changes: Optional[Dict[str, Any]] = Field(None, description="Requested changes")
    
    @validator('rejection_reason')
    def validate_rejection_reason(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError("Rejection reason must be at least 10 characters")
        return v.strip()


# Copy operation schemas
class VersionCopyCreate(ScopingBaseSchema):
    """Schema for copying versions"""
    
    source_version_id: UUID = Field(..., description="Source version to copy")
    copy_attributes: bool = Field(True, description="Whether to copy attributes")
    copy_decisions: bool = Field(False, description="Whether to copy tester decisions")
    notes: Optional[str] = Field(None, description="Copy notes")


# Error schemas
class ValidationErrorDetail(ScopingBaseSchema):
    """Schema for validation error details"""
    
    field: str = Field(..., description="Field name")
    message: str = Field(..., description="Error message")
    invalid_value: Optional[Any] = Field(None, description="Invalid value")


class APIErrorResponse(ScopingBaseSchema):
    """Schema for API error responses"""
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[List[ValidationErrorDetail]] = Field(None, description="Validation error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")