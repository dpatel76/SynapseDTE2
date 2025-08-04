"""
Enhanced Data Profiling Rules Schemas
Supports individual rule approval/decline with versioning
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from app.models.data_profiling import ProfilingRuleStatus, ProfilingRuleType

class RuleApprovalRequest(BaseModel):
    """Request schema for approving a rule"""
    notes: Optional[str] = Field(None, description="Approval notes or comments")

class RuleRejectionRequest(BaseModel):
    """Request schema for rejecting a rule"""
    reason: str = Field(..., description="Reason for rejection")
    notes: Optional[str] = Field(None, description="Additional rejection notes")
    allow_revision: bool = Field(True, description="Allow tester to revise and resubmit")

class ProfilingRuleUpdate(BaseModel):
    """Schema for updating/revising a profiling rule"""
    rule_name: Optional[str] = None
    rule_code: Optional[str] = None  # Changed from rule_logic to rule_code
    expected_result: Optional[str] = None
    severity: Optional[str] = None
    rule_type: Optional[ProfilingRuleType] = None
    llm_rationale: Optional[str] = None
    revision_notes: Optional[str] = Field(None, description="Notes explaining the revision")

class AttributeRulesSummary(BaseModel):
    """Summary of rules for an attribute"""
    attribute_id: int
    attribute_name: str
    attribute_type: str
    mandatory: bool
    total_rules: int
    approved_count: int
    rejected_count: int
    pending_count: int
    needs_revision_count: int
    last_updated: Optional[datetime]
    can_approve: bool = Field(description="Current user can approve rules")
    can_edit: bool = Field(description="Current user can edit rules")
    line_item_number: Optional[str] = None
    is_cde: bool = False
    is_primary_key: bool = False
    has_issues: bool = False
    
    class Config:
        from_attributes = True

class ProfilingRuleResponse(BaseModel):
    """Enhanced response schema for profiling rules"""
    rule_id: int
    cycle_id: Optional[int] = None
    report_id: Optional[int] = None
    attribute_id: int
    attribute_name: Optional[str] = None
    rule_name: str
    rule_type: ProfilingRuleType
    rule_code: Optional[str] = None  # Changed from rule_logic to rule_code
    rule_description: Optional[str] = None
    expected_result: Optional[str] = None
    severity: Optional[str] = None  # Made optional
    status: ProfilingRuleStatus
    
    # Versioning fields
    version_number: int = 1
    is_current_version: bool = True
    business_key: str
    
    # Approval workflow fields
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    approval_notes: Optional[str] = None
    rejected_by: Optional[int] = None
    rejected_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    rejection_notes: Optional[str] = None
    revision_notes: Optional[str] = None
    
    # Audit fields
    created_by: Optional[int] = None  # Made optional
    created_at: Optional[datetime] = None  # Made optional
    updated_by: Optional[int] = None
    updated_at: Optional[datetime] = None
    
    # LLM fields
    llm_provider: Optional[str] = None
    llm_rationale: Optional[str] = None
    regulatory_reference: Optional[str] = None
    
    # Execution fields
    is_executable: bool = True
    execution_order: int = 1
    
    # Action permissions (computed fields)
    can_approve: bool = False
    can_reject: bool = False
    can_revise: bool = False
    
    class Config:
        from_attributes = True

class RuleBulkAction(BaseModel):
    """Schema for bulk actions on rules"""
    rule_ids: List[int]
    action: str = Field(..., pattern="^(approve|reject)$")
    notes: Optional[str] = None
    reason: Optional[str] = None  # Required for reject action

class AttributeRulesExpandedView(BaseModel):
    """Expanded view showing attribute with all its rules"""
    attribute_id: int
    attribute_name: str
    attribute_type: str
    mandatory: bool
    description: Optional[str] = None
    
    # Rule summary
    total_rules: int
    approved_count: int
    rejected_count: int
    pending_count: int
    needs_revision_count: int
    
    # All rules for this attribute
    rules: List[ProfilingRuleResponse]
    
    # Permissions
    can_approve_all: bool
    can_reject_all: bool
    can_add_rule: bool
    
    class Config:
        from_attributes = True

class RuleVersionComparison(BaseModel):
    """Schema for comparing rule versions"""
    rule_id: int
    attribute_name: str
    
    # Current version
    current_version: ProfilingRuleResponse
    
    # Previous version (if exists)
    previous_version: Optional[ProfilingRuleResponse] = None
    
    # Changes summary
    changes: Dict[str, Any] = Field(description="Summary of changes between versions")
    
    class Config:
        from_attributes = True

class DataProfilingWorkflowStatus(BaseModel):
    """Overall status of data profiling workflow"""
    cycle_id: int
    report_id: int
    total_attributes: int
    total_rules: int
    
    # Approval status counts
    fully_approved_attributes: int
    partially_approved_attributes: int
    pending_attributes: int
    rejected_attributes: int
    
    # Rule status breakdown
    approved_rules: int
    rejected_rules: int
    pending_rules: int
    needs_revision_rules: int
    
    # Workflow status
    can_proceed_to_execution: bool
    completion_percentage: float
    
    # Next actions
    next_action_required: str
    next_action_user_roles: List[str]
    
    class Config:
        from_attributes = True