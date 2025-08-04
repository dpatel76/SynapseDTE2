"""
PDE Mapping Review and Approval workflow models
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, JSON, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.models.base import Base
from app.models.audit_mixin import AuditMixin
from app.models.planning import PlanningPDEMapping
from app.models.user import User


class ReviewStatus(str, enum.Enum):
    """Review status for PDE mappings"""
    PENDING = "pending"
    APPROVED = "approved" 
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"


class ReviewActionType(str, enum.Enum):
    """Types of review actions"""
    SUBMIT_FOR_REVIEW = "submit_for_review"
    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_REVISION = "request_revision"
    REVISE = "revise"
    AUTO_APPROVE = "auto_approve"


class PDEMappingReview(Base, AuditMixin):
    """Review and approval tracking for PDE mappings"""
    __tablename__ = "cycle_report_planning_pde_mapping_reviews"
    
    id = Column(Integer, primary_key=True)
    pde_mapping_id = Column(Integer, ForeignKey("cycle_report_planning_pde_mappings.id"), nullable=False)
    phase_id = Column(Integer, ForeignKey('workflow_phases.phase_id'), nullable=False)
    
    # Review status
    review_status = Column(Enum(ReviewStatus), default=ReviewStatus.PENDING, nullable=False)
    
    # Reviewer information
    submitted_by_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    reviewed_by_id = Column(Integer, ForeignKey("users.user_id"))
    reviewed_at = Column(DateTime)
    
    # Review details
    review_notes = Column(Text)
    revision_requested = Column(Text)  # Specific changes requested
    
    # LLM confidence thresholds for auto-approval
    llm_confidence_threshold = Column(Integer, default=85)  # Auto-approve if confidence >= threshold
    auto_approved = Column(Boolean, default=False)
    
    # Version tracking for iterations
    version_number = Column(Integer, default=1)
    is_latest = Column(Boolean, default=True)
    
    # Relationships
    phase = relationship("app.models.workflow.WorkflowPhase", back_populates="pde_mapping_reviews")
    pde_mapping = relationship("PlanningPDEMapping", backref="reviews")
    submitter = relationship("User", foreign_keys=[submitted_by_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by_id])
    
    
class PDEMappingReviewHistory(Base, AuditMixin):
    """Audit trail for all review actions"""
    __tablename__ = "cycle_report_planning_pde_mapping_review_history"
    
    id = Column(Integer, primary_key=True)
    pde_mapping_id = Column(Integer, ForeignKey("cycle_report_planning_pde_mappings.id"), nullable=False)
    review_id = Column(Integer, ForeignKey("cycle_report_planning_pde_mapping_reviews.id"), nullable=False)
    phase_id = Column(Integer, ForeignKey('workflow_phases.phase_id'), nullable=False)
    
    # Action details
    action_type = Column(Enum(ReviewActionType), nullable=False)
    action_by_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    action_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # State before and after
    previous_status = Column(Enum(ReviewStatus))
    new_status = Column(Enum(ReviewStatus))
    
    # Action metadata
    action_notes = Column(Text)
    changes_made = Column(JSON)  # Track what fields were changed
    
    # Relationships
    phase = relationship("app.models.workflow.WorkflowPhase")
    pde_mapping = relationship("PlanningPDEMapping")
    review = relationship("PDEMappingReview")
    action_by = relationship("User", foreign_keys=[action_by_id])


class PDEMappingApprovalRule(Base, AuditMixin):
    """Configurable rules for auto-approval of PDE mappings"""
    __tablename__ = "cycle_report_planning_pde_mapping_approval_rules"
    
    id = Column(Integer, primary_key=True)
    cycle_id = Column(Integer, ForeignKey("test_cycles.cycle_id"))
    report_id = Column(Integer, ForeignKey("reports.id"))
    
    # Rule configuration
    rule_name = Column(String(255), nullable=False)
    rule_description = Column(Text)
    is_active = Column(Boolean, default=True)
    
    # Conditions for auto-approval
    min_llm_confidence = Column(Integer, default=85)  # Minimum LLM confidence score
    require_data_source = Column(Boolean, default=False)  # Must have data source mapped
    require_business_metadata = Column(Boolean, default=False)  # Must have business process/owner
    
    # Attribute-based conditions
    auto_approve_cde = Column(Boolean, default=False)  # Auto-approve CDEs
    auto_approve_primary_key = Column(Boolean, default=True)  # Auto-approve primary keys
    auto_approve_public_classification = Column(Boolean, default=True)  # Auto-approve public data
    
    # Risk-based conditions
    max_risk_score_for_auto_approval = Column(Integer, default=5)  # Max risk score (0-10) for auto-approval
    
    # Priority and ordering
    priority = Column(Integer, default=100)  # Lower number = higher priority
    
    # Relationships
    cycle = relationship("TestCycle")
    report = relationship("Report")