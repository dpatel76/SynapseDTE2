"""
Scoping Version 2 Models - New consolidated scoping system

This module contains the new scoping models that replace the legacy scoping system,
implementing the versioning framework pattern used across the application.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, Boolean, ForeignKey, DateTime, Float, DECIMAL
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM as PgEnum
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
from sqlalchemy.ext.hybrid import hybrid_property
from enum import Enum

from app.models.base import CustomPKModel
from app.models.audit_mixin import AuditMixin


# Enums for scoping system
class VersionStatus(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class TesterDecision(str, Enum):
    ACCEPT = "accept"
    DECLINE = "decline"
    OVERRIDE = "override"


class ReportOwnerDecision(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    PENDING = "pending"
    NEEDS_REVISION = "needs_revision"


class AttributeStatus(str, Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"


# PostgreSQL enum types (match the migration)
version_status_enum = PgEnum(
    'draft', 'pending_approval', 'approved', 'rejected', 'superseded',
    name='scoping_version_status_enum'
)

tester_decision_enum = PgEnum(
    'accept', 'decline', 'override',
    name='scoping_tester_decision_enum'
)

report_owner_decision_enum = PgEnum(
    'approved', 'rejected', 'pending', 'needs_revision',
    name='scoping_report_owner_decision_enum'
)

attribute_status_enum = PgEnum(
    'pending', 'submitted', 'approved', 'rejected', 'needs_revision',
    name='scoping_attribute_status_enum'
)


class ScopingVersion(CustomPKModel, AuditMixin):
    """
    Consolidated scoping version model following the versioning framework pattern.
    
    This model manages scoping decisions at the version level, providing:
    - Version management with draft → pending → approved/rejected → superseded lifecycle
    - Temporal workflow integration
    - Summary statistics and progress tracking
    - Submission and approval workflow
    - Risk and impact assessment
    """
    
    __tablename__ = "cycle_report_scoping_versions"
    
    # Primary key
    version_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Phase context (replaces cycle_id/report_id pattern)
    phase_id = Column(Integer, ForeignKey('workflow_phases.phase_id'), nullable=False)
    workflow_activity_id = Column(Integer, ForeignKey('workflow_activities.activity_id'), nullable=True)
    
    # Version Management
    version_number = Column(Integer, nullable=False)
    version_status = Column(version_status_enum, nullable=False)
    parent_version_id = Column(UUID(as_uuid=True), ForeignKey('cycle_report_scoping_versions.version_id'), nullable=True)
    
    # Temporal Workflow Context
    workflow_execution_id = Column(String(255), nullable=True)
    workflow_run_id = Column(String(255), nullable=True)
    activity_name = Column(String(100), nullable=True)
    
    # Scoping Summary Statistics
    total_attributes = Column(Integer, nullable=False, default=0)
    scoped_attributes = Column(Integer, nullable=False, default=0)
    declined_attributes = Column(Integer, nullable=False, default=0)
    override_count = Column(Integer, nullable=False, default=0)
    cde_count = Column(Integer, nullable=False, default=0)
    recommendation_accuracy = Column(Float, nullable=True)
    
    # Submission and Approval Workflow
    submission_notes = Column(Text, nullable=True)
    submitted_by_id = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    
    approval_notes = Column(Text, nullable=True)
    approved_by_id = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    
    rejection_reason = Column(Text, nullable=True)
    requested_changes = Column(JSONB, nullable=True)
    
    # Risk and Impact Assessment
    resource_impact_assessment = Column(Text, nullable=True)
    risk_coverage_assessment = Column(Text, nullable=True)
    
    # Relationships
    phase = relationship("app.models.workflow.WorkflowPhase", back_populates="scoping_versions")
    workflow_activity = relationship("app.models.workflow_activity.WorkflowActivity")
    parent_version = relationship("ScopingVersion", remote_side=[version_id])
    child_versions = relationship("ScopingVersion", back_populates="parent_version")
    
    # Scoping attributes in this version
    attributes = relationship("ScopingAttribute", back_populates="version", cascade="all, delete-orphan")
    
    # User relationships
    submitted_by = relationship("app.models.user.User", foreign_keys=[submitted_by_id])
    approved_by = relationship("app.models.user.User", foreign_keys=[approved_by_id])
    
    # Validation
    @validates('version_number')
    def validate_version_number(self, key, value):
        if value <= 0:
            raise ValueError("Version number must be positive")
        return value
    
    @validates('total_attributes', 'scoped_attributes', 'declined_attributes', 'override_count', 'cde_count')
    def validate_counts(self, key, value):
        if value < 0:
            raise ValueError(f"{key} cannot be negative")
        return value
    
    @validates('recommendation_accuracy')
    def validate_accuracy(self, key, value):
        if value is not None and (value < 0 or value > 1):
            raise ValueError("Recommendation accuracy must be between 0 and 1")
        return value
    
    # Properties for version lifecycle management
    @hybrid_property
    def is_draft(self) -> bool:
        """Check if this version is in draft status"""
        return self.version_status == VersionStatus.DRAFT
    
    @hybrid_property
    def is_pending_approval(self) -> bool:
        """Check if this version is pending approval"""
        return self.version_status == VersionStatus.PENDING_APPROVAL
    
    @hybrid_property
    def is_approved(self) -> bool:
        """Check if this version is approved"""
        return self.version_status == VersionStatus.APPROVED
    
    @hybrid_property
    def is_rejected(self) -> bool:
        """Check if this version is rejected"""
        return self.version_status == VersionStatus.REJECTED
    
    @hybrid_property
    def is_superseded(self) -> bool:
        """Check if this version is superseded"""
        return self.version_status == VersionStatus.SUPERSEDED
    
    @hybrid_property
    def can_be_edited(self) -> bool:
        """Check if this version can be edited"""
        return self.version_status in [VersionStatus.DRAFT, VersionStatus.REJECTED]
    
    @hybrid_property
    def can_be_submitted(self) -> bool:
        """Check if this version can be submitted for approval"""
        return self.version_status == VersionStatus.DRAFT and self.total_attributes > 0
    
    @hybrid_property
    def can_be_approved(self) -> bool:
        """Check if this version can be approved"""
        return self.version_status == VersionStatus.PENDING_APPROVAL
    
    @hybrid_property
    def is_current(self) -> bool:
        """Check if this is the current active version"""
        return self.version_status == VersionStatus.APPROVED
    
    @hybrid_property
    def scoping_percentage(self) -> float:
        """Calculate the percentage of attributes scoped in"""
        if self.total_attributes == 0:
            return 0.0
        return (self.scoped_attributes / self.total_attributes) * 100
    
    @hybrid_property
    def override_percentage(self) -> float:
        """Calculate the percentage of attributes with overrides"""
        if self.total_attributes == 0:
            return 0.0
        return (self.override_count / self.total_attributes) * 100
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get comprehensive summary statistics for this version"""
        return {
            "version_id": str(self.version_id),
            "version_number": self.version_number,
            "status": self.version_status.value,
            "total_attributes": self.total_attributes,
            "scoped_attributes": self.scoped_attributes,
            "declined_attributes": self.declined_attributes,
            "override_count": self.override_count,
            "cde_count": self.cde_count,
            "scoping_percentage": self.scoping_percentage,
            "override_percentage": self.override_percentage,
            "recommendation_accuracy": self.recommendation_accuracy,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "can_be_edited": self.can_be_edited,
            "can_be_submitted": self.can_be_submitted,
            "can_be_approved": self.can_be_approved,
            "is_current": self.is_current
        }
    
    def __repr__(self):
        return f"<ScopingVersion(version_id={self.version_id}, phase_id={self.phase_id}, version_number={self.version_number}, status={self.version_status})>"


class ScopingAttribute(CustomPKModel, AuditMixin):
    """
    Individual scoping attribute decision model.
    
    This model stores the scoping decision for each attribute within a version,
    including LLM recommendations, tester decisions, and report owner decisions.
    """
    
    __tablename__ = "cycle_report_scoping_attributes"
    
    # Primary key
    attribute_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Context
    version_id = Column(UUID(as_uuid=True), ForeignKey('cycle_report_scoping_versions.version_id'), nullable=False)
    phase_id = Column(Integer, ForeignKey('workflow_phases.phase_id'), nullable=False)
    planning_attribute_id = Column(UUID(as_uuid=True), ForeignKey("cycle_report_planning_attributes.id"), nullable=False)
    
    # LLM Recommendation (embedded JSON)
    llm_recommendation = Column(JSONB, nullable=False)
    llm_provider = Column(String(50), nullable=True)
    llm_confidence_score = Column(DECIMAL(5,2), nullable=True)
    llm_rationale = Column(Text, nullable=True)
    llm_processing_time_ms = Column(Integer, nullable=True)
    llm_request_payload = Column(JSONB, nullable=True)
    llm_response_payload = Column(JSONB, nullable=True)
    
    # Tester Decision
    tester_decision = Column(tester_decision_enum, nullable=True)
    final_scoping = Column(Boolean, nullable=True)
    tester_rationale = Column(Text, nullable=True)
    tester_decided_by_id = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    tester_decided_at = Column(DateTime(timezone=True), nullable=True)
    
    # Report Owner Decision
    report_owner_decision = Column(report_owner_decision_enum, nullable=True)
    report_owner_notes = Column(Text, nullable=True)
    report_owner_decided_by_id = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    report_owner_decided_at = Column(DateTime(timezone=True), nullable=True)
    
    # Special Cases and Metadata
    is_override = Column(Boolean, nullable=False, default=False)
    override_reason = Column(Text, nullable=True)
    is_cde = Column(Boolean, nullable=False, default=False)
    has_historical_issues = Column(Boolean, nullable=False, default=False)
    is_primary_key = Column(Boolean, nullable=False, default=False)
    
    # Data Quality Integration
    data_quality_score = Column(Float, nullable=True)
    data_quality_issues = Column(JSONB, nullable=True)
    
    # Expected Source Documents
    expected_source_documents = Column(JSONB, nullable=True)
    search_keywords = Column(JSONB, nullable=True)
    risk_factors = Column(JSONB, nullable=True)
    
    # Status
    status = Column(attribute_status_enum, nullable=False)
    
    # Relationships
    version = relationship("ScopingVersion", back_populates="attributes")
    phase = relationship("app.models.workflow.WorkflowPhase")
    planning_attribute = relationship("app.models.report_attribute.ReportAttribute")
    
    # User relationships
    tester_decided_by = relationship("app.models.user.User", foreign_keys=[tester_decided_by_id])
    report_owner_decided_by = relationship("app.models.user.User", foreign_keys=[report_owner_decided_by_id])
    
    # Validation
    @validates('llm_confidence_score')
    def validate_confidence_score(self, key, value):
        if value is not None and (value < 0 or value > 1):
            raise ValueError("LLM confidence score must be between 0 and 1")
        return value
    
    @validates('data_quality_score')
    def validate_data_quality_score(self, key, value):
        if value is not None and (value < 0 or value > 1):
            raise ValueError("Data quality score must be between 0 and 1")
        return value
    
    @validates('llm_processing_time_ms')
    def validate_processing_time(self, key, value):
        if value is not None and value < 0:
            raise ValueError("Processing time cannot be negative")
        return value
    
    # Properties
    @hybrid_property
    def has_tester_decision(self) -> bool:
        """Check if tester has made a decision"""
        return self.tester_decision is not None
    
    @hybrid_property
    def has_report_owner_decision(self) -> bool:
        """Check if report owner has made a decision"""
        return self.report_owner_decision is not None
    
    @hybrid_property
    def is_scoped_in(self) -> bool:
        """Check if this attribute is scoped in for testing"""
        return self.final_scoping is True
    
    @hybrid_property
    def is_scoped_out(self) -> bool:
        """Check if this attribute is scoped out"""
        return self.final_scoping is False
    
    @hybrid_property
    def is_pending_decision(self) -> bool:
        """Check if this attribute is pending tester decision"""
        return self.tester_decision is None
    
    @hybrid_property
    def llm_recommended_action(self) -> Optional[str]:
        """Get the LLM recommended action from the recommendation JSON"""
        if not self.llm_recommendation:
            return None
        return self.llm_recommendation.get('recommended_action')
    
    @hybrid_property
    def llm_agreed_with_tester(self) -> Optional[bool]:
        """Check if LLM recommendation agrees with tester decision"""
        if not self.has_tester_decision or not self.llm_recommendation:
            return None
        
        llm_action = self.llm_recommended_action
        if llm_action == 'test' and self.final_scoping is True:
            return True
        elif llm_action == 'skip' and self.final_scoping is False:
            return True
        return False
    
    @hybrid_property
    def decision_timeline(self) -> List[Dict[str, Any]]:
        """Get the decision timeline for this attribute"""
        timeline = []
        
        if self.created_at:
            timeline.append({
                "event": "attribute_created",
                "timestamp": self.created_at,
                "user_id": self.created_by_id,
                "details": "Attribute added to scoping version"
            })
        
        if self.tester_decided_at:
            timeline.append({
                "event": "tester_decision",
                "timestamp": self.tester_decided_at,
                "user_id": self.tester_decided_by_id,
                "details": f"Tester decision: {self.tester_decision}",
                "decision": self.tester_decision,
                "scoping": self.final_scoping
            })
        
        if self.report_owner_decided_at:
            timeline.append({
                "event": "report_owner_decision",
                "timestamp": self.report_owner_decided_at,
                "user_id": self.report_owner_decided_by_id,
                "details": f"Report owner decision: {self.report_owner_decision}",
                "decision": self.report_owner_decision
            })
        
        return sorted(timeline, key=lambda x: x["timestamp"])
    
    def get_decision_summary(self) -> Dict[str, Any]:
        """Get a comprehensive summary of all decisions for this attribute"""
        return {
            "attribute_id": str(self.attribute_id),
            "planning_attribute_id": self.planning_attribute_id,
            "status": self.status.value,
            "llm_recommendation": {
                "recommended_action": self.llm_recommended_action,
                "confidence_score": float(self.llm_confidence_score) if self.llm_confidence_score else None,
                "rationale": self.llm_rationale,
                "provider": self.llm_provider,
                "processing_time_ms": self.llm_processing_time_ms
            },
            "tester_decision": {
                "decision": self.tester_decision.value if self.tester_decision else None,
                "final_scoping": self.final_scoping,
                "rationale": self.tester_rationale,
                "decided_by_id": self.tester_decided_by_id,
                "decided_at": self.tester_decided_at.isoformat() if self.tester_decided_at else None,
                "is_override": self.is_override,
                "override_reason": self.override_reason
            },
            "report_owner_decision": {
                "decision": self.report_owner_decision.value if self.report_owner_decision else None,
                "notes": self.report_owner_notes,
                "decided_by_id": self.report_owner_decided_by_id,
                "decided_at": self.report_owner_decided_at.isoformat() if self.report_owner_decided_at else None
            },
            "flags": {
                "is_cde": self.is_cde,
                "is_primary_key": self.is_primary_key,
                "has_historical_issues": self.has_historical_issues
            },
            "data_quality": {
                "score": self.data_quality_score,
                "issues": self.data_quality_issues
            },
            "llm_agreed_with_tester": self.llm_agreed_with_tester,
            "decision_timeline": self.decision_timeline
        }
    
    def __repr__(self):
        return f"<ScopingAttribute(attribute_id={self.attribute_id}, planning_attribute_id={self.planning_attribute_id}, tester_decision={self.tester_decision}, final_scoping={self.final_scoping})>"