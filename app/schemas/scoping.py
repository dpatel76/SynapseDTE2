"""
Scoping Schemas - Consolidated Version Management System

This module provides comprehensive Pydantic schemas for the consolidated scoping system,
supporting version management, attribute decisions, and workflow integration.
"""

from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator, root_validator
from enum import Enum
from uuid import UUID
from decimal import Decimal


# Enums for scoping system
class VersionStatus(str, Enum):
    """Version status enumeration"""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class TesterDecision(str, Enum):
    """Tester decision enumeration"""
    ACCEPT = "accept"
    DECLINE = "decline"
    OVERRIDE = "override"


class ReportOwnerDecision(str, Enum):
    """Report owner decision enumeration"""
    APPROVED = "approved"
    REJECTED = "rejected"
    PENDING = "pending"
    NEEDS_REVISION = "needs_revision"


class AttributeStatus(str, Enum):
    """Attribute status enumeration"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"


# LLM Recommendation Schemas
class LLMRecommendationCreate(BaseModel):
    """Schema for creating LLM recommendations"""
    recommended_action: str = Field(..., description="Test or Skip recommendation")
    confidence_score: Optional[Decimal] = Field(None, ge=0, le=100, description="Confidence score (0-100)")
    rationale: str = Field(..., description="Detailed rationale for recommendation")
    expected_source_documents: Optional[List[str]] = Field(None, description="Expected source document types")
    search_keywords: Optional[List[str]] = Field(None, description="Keywords to search in source documents")
    risk_factors: Optional[List[str]] = Field(None, description="Risk factors identified")
    priority_level: Optional[str] = Field(None, description="Priority level (High/Medium/Low)")
    provider: Optional[str] = Field(None, description="LLM provider used")
    processing_time_ms: Optional[int] = Field(None, description="Processing time in milliseconds")
    request_payload: Optional[Dict[str, Any]] = Field(None, description="Request payload for audit")
    response_payload: Optional[Dict[str, Any]] = Field(None, description="Response payload for audit")
    is_cde: Optional[bool] = Field(False, description="Is CDE attribute")
    is_primary_key: Optional[bool] = Field(False, description="Is primary key")
    has_historical_issues: Optional[bool] = Field(False, description="Has historical issues")
    data_quality_score: Optional[float] = Field(None, description="Data quality score")
    data_quality_issues: Optional[Dict[str, Any]] = Field(None, description="Data quality issues")


class LLMRecommendationResponse(BaseModel):
    """Schema for LLM recommendation response"""
    recommended_action: str
    confidence_score: Optional[Decimal]
    rationale: str
    expected_source_documents: Optional[List[str]]
    search_keywords: Optional[List[str]]
    risk_factors: Optional[List[str]]
    priority_level: Optional[str]
    provider: Optional[str]
    processing_time_ms: Optional[int]
    is_cde: Optional[bool]
    is_primary_key: Optional[bool]
    has_historical_issues: Optional[bool]
    data_quality_score: Optional[float]
    data_quality_issues: Optional[Dict[str, Any]]


# Version Management Schemas
class ScopingVersionCreate(BaseModel):
    """Schema for creating a new scoping version"""
    phase_id: int = Field(..., description="Phase ID")
    workflow_activity_id: Optional[int] = Field(None, description="Workflow activity ID")
    workflow_execution_id: Optional[str] = Field(None, description="Temporal workflow execution ID")
    workflow_run_id: Optional[str] = Field(None, description="Temporal workflow run ID")
    activity_name: Optional[str] = Field(None, description="Activity name")
    notes: Optional[str] = Field(None, description="Creation notes")


class ScopingVersionUpdate(BaseModel):
    """Schema for updating a scoping version"""
    notes: Optional[str] = Field(None, description="Update notes")
    resource_impact_assessment: Optional[str] = Field(None, description="Resource impact assessment")
    risk_coverage_assessment: Optional[str] = Field(None, description="Risk coverage assessment")


class ScopingVersionResponse(BaseModel):
    """Schema for scoping version response"""
    version_id: UUID
    phase_id: int
    workflow_activity_id: Optional[int]
    version_number: int
    version_status: VersionStatus
    parent_version_id: Optional[UUID]
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
    
    # Submission and approval
    submission_notes: Optional[str]
    submitted_by_id: Optional[int]
    submitted_at: Optional[datetime]
    approval_notes: Optional[str]
    approved_by_id: Optional[int]
    approved_at: Optional[datetime]
    rejection_reason: Optional[str]
    requested_changes: Optional[Dict[str, Any]]
    
    # Risk assessments
    resource_impact_assessment: Optional[str]
    risk_coverage_assessment: Optional[str]
    
    # Audit fields
    created_at: datetime
    created_by_id: int
    updated_at: datetime
    updated_by_id: int
    
    # Computed properties
    can_be_edited: bool = Field(False, description="Can be edited")
    can_be_submitted: bool = Field(False, description="Can be submitted")
    can_be_approved: bool = Field(False, description="Can be approved")
    is_current: bool = Field(False, description="Is current approved version")
    
    class Config:
        from_attributes = True


class ScopingVersionSummary(BaseModel):
    """Schema for scoping version summary"""
    version_id: UUID
    version_number: int
    version_status: VersionStatus
    total_attributes: int
    scoped_attributes: int
    declined_attributes: int
    override_count: int
    scoping_percentage: float
    created_at: datetime
    submitted_at: Optional[datetime]
    approved_at: Optional[datetime]


class VersionStatistics(BaseModel):
    """Schema for version statistics"""
    version_id: UUID
    version_number: int
    status: str
    total_attributes: int
    scoped_attributes: int
    declined_attributes: int
    override_count: int
    cde_count: int
    scoping_percentage: float
    override_percentage: float
    decision_progress: Dict[str, Any]
    report_owner_progress: Dict[str, Any]
    llm_accuracy: Optional[float]
    created_at: str
    submitted_at: Optional[str]
    approved_at: Optional[str]
    can_be_edited: bool
    can_be_submitted: bool
    can_be_approved: bool
    is_current: bool


class VersionQueryParams(BaseModel):
    """Schema for version query parameters"""
    phase_id: Optional[int] = Field(None, description="Filter by phase ID")
    status: Optional[VersionStatus] = Field(None, description="Filter by status")
    limit: Optional[int] = Field(10, ge=1, le=100, description="Number of versions to return")
    offset: Optional[int] = Field(0, ge=0, description="Offset for pagination")
    include_attributes: Optional[bool] = Field(False, description="Include attributes in response")


class VersionSubmissionCreate(BaseModel):
    """Schema for submitting a version for approval"""
    submission_notes: Optional[str] = Field(None, description="Submission notes")
    resource_impact_assessment: Optional[str] = Field(None, description="Resource impact assessment")
    risk_coverage_assessment: Optional[str] = Field(None, description="Risk coverage assessment")


class VersionApprovalCreate(BaseModel):
    """Schema for approving a version"""
    approval_notes: Optional[str] = Field(None, description="Approval notes")


class VersionRejectionCreate(BaseModel):
    """Schema for rejecting a version"""
    rejection_reason: str = Field(..., description="Reason for rejection")
    requested_changes: Optional[Dict[str, Any]] = Field(None, description="Structured requested changes")


class VersionCopyCreate(BaseModel):
    """Schema for copying a version"""
    copy_attributes: bool = Field(True, description="Copy attributes from source version")
    copy_decisions: bool = Field(False, description="Copy tester decisions")
    notes: Optional[str] = Field(None, description="Copy notes")


# Attribute Management Schemas
class ScopingAttributeCreate(BaseModel):
    """Schema for creating a scoping attribute"""
    planning_attribute_id: int = Field(..., description="Planning attribute ID")
    llm_recommendation: LLMRecommendationCreate = Field(..., description="LLM recommendation")


class ScopingAttributesBulkCreate(BaseModel):
    """Schema for bulk creating scoping attributes"""
    attributes: List[ScopingAttributeCreate] = Field(..., description="List of attributes to create")


class ScopingAttributeUpdate(BaseModel):
    """Schema for updating a scoping attribute"""
    llm_recommendation: Optional[LLMRecommendationCreate] = Field(None, description="Updated LLM recommendation")
    expected_source_documents: Optional[List[str]] = Field(None, description="Expected source documents")
    search_keywords: Optional[List[str]] = Field(None, description="Search keywords")
    risk_factors: Optional[List[str]] = Field(None, description="Risk factors")


class ScopingAttributeResponse(BaseModel):
    """Schema for scoping attribute response"""
    attribute_id: UUID
    version_id: UUID
    phase_id: int
    planning_attribute_id: int
    
    # Planning attribute details
    attribute_name: Optional[str] = None
    line_item_number: Optional[str] = None
    
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
    
    # Special cases
    is_override: bool
    override_reason: Optional[str]
    is_cde: bool
    has_historical_issues: bool
    is_primary_key: bool
    
    # Data quality
    data_quality_score: Optional[float]
    data_quality_issues: Optional[Dict[str, Any]]
    
    # Expected source documents
    expected_source_documents: Optional[List[str]]
    search_keywords: Optional[List[str]]
    risk_factors: Optional[List[str]]
    
    # Status
    status: AttributeStatus
    
    # Audit fields
    created_at: datetime
    created_by_id: int
    updated_at: datetime
    updated_by_id: int
    
    # Computed properties
    has_tester_decision: bool = Field(False, description="Has tester decision")
    has_report_owner_decision: bool = Field(False, description="Has report owner decision")
    is_scoped_in: bool = Field(False, description="Is scoped in for testing")
    is_scoped_out: bool = Field(False, description="Is scoped out")
    is_pending_decision: bool = Field(False, description="Is pending decision")
    llm_agreed_with_tester: Optional[bool] = Field(None, description="LLM agreed with tester")
    
    class Config:
        from_attributes = True


class ScopingAttributeSummary(BaseModel):
    """Schema for scoping attribute summary"""
    attribute_id: UUID
    planning_attribute_id: int
    llm_recommendation: str
    llm_confidence_score: Optional[Decimal]
    tester_decision: Optional[TesterDecision]
    final_scoping: Optional[bool]
    report_owner_decision: Optional[ReportOwnerDecision]
    is_override: bool
    is_cde: bool
    status: AttributeStatus


class AttributeDecisionSummary(BaseModel):
    """Schema for attribute decision summary"""
    total_attributes: int
    pending_decisions: int
    completed_decisions: int
    scoped_in: int
    scoped_out: int
    overrides: int
    cde_attributes: int
    decision_progress_percentage: float
    scoping_percentage: float


class AttributeQueryParams(BaseModel):
    """Schema for attribute query parameters"""
    version_id: Optional[UUID] = Field(None, description="Filter by version ID")
    phase_id: Optional[int] = Field(None, description="Filter by phase ID")
    planning_attribute_id: Optional[int] = Field(None, description="Filter by planning attribute ID")
    status: Optional[AttributeStatus] = Field(None, description="Filter by status")
    tester_decision: Optional[TesterDecision] = Field(None, description="Filter by tester decision")
    report_owner_decision: Optional[ReportOwnerDecision] = Field(None, description="Filter by report owner decision")
    final_scoping: Optional[bool] = Field(None, description="Filter by final scoping")
    is_override: Optional[bool] = Field(None, description="Filter by override flag")
    is_cde: Optional[bool] = Field(None, description="Filter by CDE flag")
    limit: Optional[int] = Field(10, ge=1, le=100, description="Number of attributes to return")
    offset: Optional[int] = Field(0, ge=0, description="Offset for pagination")


# Decision Making Schemas
class TesterDecisionCreate(BaseModel):
    """Schema for creating a tester decision"""
    decision: TesterDecision = Field(..., description="Tester decision")
    final_scoping: bool = Field(..., description="Final scoping decision")
    rationale: Optional[str] = Field(None, description="Rationale for decision")
    override_reason: Optional[str] = Field(None, description="Reason for override (required if decision is override)")
    
    @validator('override_reason')
    def validate_override_reason(cls, v, values):
        if values.get('decision') == TesterDecision.OVERRIDE and not v:
            raise ValueError('Override reason is required when decision is override')
        return v


class ReportOwnerDecisionCreate(BaseModel):
    """Schema for creating a report owner decision"""
    decision: ReportOwnerDecision = Field(..., description="Report owner decision")
    notes: Optional[str] = Field(None, description="Decision notes")


class BulkTesterDecisionCreate(BaseModel):
    """Schema for bulk tester decisions"""
    decisions: List[Dict[str, Any]] = Field(..., description="List of decisions with attribute_id and decision data")


class BulkUpdateResponse(BaseModel):
    """Schema for bulk update response"""
    updated_count: int = Field(..., description="Number of attributes updated")
    errors: List[str] = Field(default=[], description="List of errors encountered")
    updated_attributes: List[UUID] = Field(default=[], description="List of updated attribute IDs")


# Workflow Integration Schemas
class WorkflowContextCreate(BaseModel):
    """Schema for workflow context"""
    workflow_execution_id: str = Field(..., description="Temporal workflow execution ID")
    workflow_run_id: str = Field(..., description="Temporal workflow run ID")
    activity_name: str = Field(..., description="Activity name")
    activity_metadata: Optional[Dict[str, Any]] = Field(None, description="Activity metadata")


class WorkflowContextResponse(BaseModel):
    """Schema for workflow context response"""
    workflow_execution_id: str
    workflow_run_id: str
    activity_name: str
    activity_metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime


# Utility Schemas
class APIErrorResponse(BaseModel):
    """Schema for API error responses"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")


class PaginatedResponse(BaseModel):
    """Schema for paginated responses"""
    items: List[Any] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page")
    per_page: int = Field(..., description="Items per page")
    has_next: bool = Field(..., description="Has next page")
    has_prev: bool = Field(..., description="Has previous page")


class HealthCheckResponse(BaseModel):
    """Schema for health check response"""
    status: str = Field(..., description="Health status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(..., description="Health check timestamp")


# Legacy Compatibility Schemas (for backward compatibility)
class ScopingRecommendation(str, Enum):
    """Legacy scoping recommendation enumeration"""
    TEST = "Test"
    SKIP = "Skip"


class ScopingDecision(str, Enum):
    """Legacy scoping decision enumeration"""
    ACCEPT = "Accept"
    DECLINE = "Decline"
    OVERRIDE = "Override"


class ApprovalStatus(str, Enum):
    """Legacy approval status enumeration"""
    PENDING = "Pending"
    APPROVED = "Approved"
    DECLINED = "Declined"
    NEEDS_REVISION = "Needs Revision"


class LegacyScopingPhaseStatus(BaseModel):
    """Legacy schema for scoping phase status"""
    cycle_id: int = Field(..., description="Cycle ID")
    report_id: int = Field(..., description="Report ID")
    phase_status: str = Field(..., description="Phase status")
    total_attributes: int = Field(..., description="Total attributes")
    attributes_with_recommendations: int = Field(..., description="Attributes with LLM recommendations")
    attributes_with_decisions: int = Field(..., description="Attributes with tester decisions")
    attributes_scoped_for_testing: int = Field(..., description="Attributes scoped for testing")
    submission_status: str = Field(..., description="Submission status")
    approval_status: Optional[ApprovalStatus] = Field(None, description="Report Owner approval status")
    can_generate_recommendations: bool = Field(..., description="Can generate LLM recommendations")
    can_submit_for_approval: bool = Field(..., description="Can submit for approval")
    can_complete_phase: bool = Field(..., description="Can complete scoping phase")
    completion_requirements: List[str] = Field(..., description="Requirements to complete phase")
    can_resubmit: bool = Field(False, description="Can resubmit after receiving feedback")
    latest_submission_version: Optional[int] = Field(None, description="Latest submission version number")
    has_submission: bool = Field(False, description="Whether a submission has been made")
    # Additional metrics
    cdes_count: int = Field(0, description="Total number of CDEs")
    historical_issues_count: int = Field(0, description="Number of attributes with historical issues")
    attributes_with_anomalies: int = Field(0, description="Number of attributes with anomalies from profiling")
    days_elapsed: int = Field(0, description="Days elapsed since phase started")