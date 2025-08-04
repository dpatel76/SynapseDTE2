"""
Pydantic schemas for PDE Mapping Review and Approval
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class ReviewStatusEnum(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"


class ReviewActionTypeEnum(str, Enum):
    SUBMIT_FOR_REVIEW = "submit_for_review"
    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_REVISION = "request_revision"
    REVISE = "revise"
    AUTO_APPROVE = "auto_approve"


# ===================== Review Schemas =====================

class PDEMappingReviewCreateRequest(BaseModel):
    review_notes: Optional[str] = Field(None, description="Notes for the reviewer")


class PDEMappingReviewUpdateRequest(BaseModel):
    review_status: ReviewStatusEnum = Field(..., description="New review status")
    review_notes: Optional[str] = Field(None, description="Review feedback")
    revision_requested: Optional[str] = Field(None, description="Specific changes requested (if needs revision)")


class PDEMappingReviewResponse(BaseModel):
    id: int
    pde_mapping_id: int
    review_status: ReviewStatusEnum
    
    submitted_by_id: int
    submitted_at: datetime
    reviewed_by_id: Optional[int]
    reviewed_at: Optional[datetime]
    
    review_notes: Optional[str]
    revision_requested: Optional[str]
    
    llm_confidence_threshold: int
    auto_approved: bool
    
    version_number: int
    is_latest: bool
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PDEMappingReviewHistoryResponse(BaseModel):
    id: int
    pde_mapping_id: int
    review_id: int
    
    action_type: ReviewActionTypeEnum
    action_by_id: int
    action_at: datetime
    
    previous_status: Optional[ReviewStatusEnum]
    new_status: Optional[ReviewStatusEnum]
    
    action_notes: Optional[str]
    changes_made: Optional[Dict[str, Any]]
    
    created_at: datetime
    
    class Config:
        from_attributes = True


class BulkReviewRequest(BaseModel):
    mapping_ids: List[int] = Field(..., description="List of PDE mapping IDs to review")
    action: str = Field(..., pattern="^(approve|reject)$", description="Action to take: approve or reject")
    review_status: ReviewStatusEnum = Field(..., description="New review status")
    review_notes: Optional[str] = Field(None, description="Notes for bulk action")


class ReviewSummaryResponse(BaseModel):
    total_mappings: int
    pending: int
    approved: int
    rejected: int
    needs_revision: int
    not_submitted: int
    auto_approved: int


# ===================== Approval Rule Schemas =====================

class ApprovalRuleCreateRequest(BaseModel):
    rule_name: str = Field(..., description="Name of the approval rule")
    rule_description: Optional[str] = Field(None, description="Description of the rule")
    is_active: bool = Field(True, description="Whether the rule is active")
    
    # Conditions
    min_llm_confidence: int = Field(85, ge=0, le=100, description="Minimum LLM confidence score for auto-approval")
    require_data_source: bool = Field(False, description="Require data source to be mapped")
    require_business_metadata: bool = Field(False, description="Require business process/owner")
    
    # Attribute conditions
    auto_approve_cde: bool = Field(False, description="Auto-approve Critical Data Elements")
    auto_approve_primary_key: bool = Field(True, description="Auto-approve primary key attributes")
    auto_approve_public_classification: bool = Field(True, description="Auto-approve public classification attributes")
    
    # Risk conditions
    max_risk_score_for_auto_approval: int = Field(5, ge=0, le=10, description="Maximum risk score for auto-approval")
    
    # Priority
    priority: int = Field(100, ge=1, description="Rule priority (lower = higher priority)")


class ApprovalRuleResponse(BaseModel):
    id: int
    cycle_id: Optional[int]
    report_id: Optional[int]
    
    rule_name: str
    rule_description: Optional[str]
    is_active: bool
    
    min_llm_confidence: int
    require_data_source: bool
    require_business_metadata: bool
    
    auto_approve_cde: bool
    auto_approve_primary_key: bool
    auto_approve_public_classification: bool
    
    max_risk_score_for_auto_approval: int
    
    priority: int
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ===================== Enhanced PDE Mapping Response with Review Status =====================

class PDEMappingWithReviewResponse(BaseModel):
    """PDE Mapping with review status information"""
    id: int
    pde_name: str
    pde_code: str
    attribute_name: str
    
    llm_confidence_score: Optional[int]
    mapping_confirmed_by_user: bool
    
    # Review information
    review_status: Optional[ReviewStatusEnum]
    review_id: Optional[int]
    submitted_at: Optional[datetime]
    reviewed_at: Optional[datetime]
    reviewed_by_name: Optional[str]
    auto_approved: bool
    
    # Attribute details
    is_cde: bool
    is_primary_key: bool
    information_security_classification: Optional[str]
    risk_score: Optional[float]
    
    class Config:
        from_attributes = True