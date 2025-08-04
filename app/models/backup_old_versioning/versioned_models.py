"""
Phase-specific versioned models for SynapseDTE
Models that need versioning capability across different phases
"""

from typing import Optional, Dict, Any, List
from sqlalchemy import Column, String, Integer, Text, Boolean, ForeignKey, DateTime, Float
from sqlalchemy.dialects.postgresql import UUID, JSONBUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import CustomPKModel
from app.models.audit_mixin import AuditMixin
from app.models.versioning import VersionedMixin


class DataProfilingRuleVersion(CustomPKModel, AuditMixin, VersionedMixin):
    """Versioned data profiling rules"""
    
    __tablename__ = "cycle_report_data_profiling_rule_versions"
    __versioned__ = True
    
    rule_version_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Link to original rule
    rule_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Phase context
    cycle_id = Column(Integer, ForeignKey("test_cycles.cycle_id"), nullable=False)
    report_id = Column(Integer, ForeignKey("reports.report_id"), nullable=False)
    attribute_id = Column(Integer, ForeignKey("report_attributes.attribute_id"), nullable=False)
    
    # Rule definition
    rule_type = Column(String(50), nullable=False)  # completeness, uniqueness, format, range, etc.
    rule_definition = Column(JSONB, nullable=False)
    rule_description = Column(Text)
    
    # Validation parameters
    threshold_value = Column(Float)
    threshold_type = Column(String(20))  # percentage, count, etc.
    
    # Execution results
    execution_status = Column(String(50))  # pending, running, completed, failed
    execution_results = Column(JSONB)
    issues_found = Column(Integer, default=0)
    
    # Relationships
    cycle = relationship("TestCycle", back_populates="data_profiling_rules")
    report = relationship("Report", back_populates="data_profiling_rules")
    attribute = relationship("ReportAttribute", back_populates="data_profiling_rules")


class TestExecutionVersion(CustomPKModel, AuditMixin, VersionedMixin):
    """Versioned test execution results"""
    
    __tablename__ = "test_execution_versions"
    __versioned__ = True
    
    execution_version_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Link to original execution
    execution_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Context
    cycle_id = Column(Integer, ForeignKey("test_cycles.cycle_id"), nullable=False)
    report_id = Column(Integer, ForeignKey("reports.report_id"), nullable=False)
    # test_plan_id = Column(UUID(as_uuid=True), nullable=False)  # No test_plans table yet
    
    # Test details
    attribute_id = Column(Integer, ForeignKey("report_attributes.attribute_id"), nullable=False)
    sample_id = Column(Integer, ForeignKey("cycle_report_sample_selection_samples.sample_id"), nullable=False)
    
    # Results
    test_results = Column(JSONB, nullable=False)
    document_results = Column(JSONB)
    database_results = Column(JSONB)
    
    # Overall outcome
    overall_result = Column(String(20))  # pass, fail, inconclusive
    confidence_score = Column(Float)
    
    # Issues and findings
    issues_identified = Column(JSONB)
    requires_resubmission = Column(Boolean, default=False)
    resubmission_reason = Column(Text)
    
    # Evidence
    evidence_files = Column(JSONB)  # List of file references
    screenshots = Column(JSONB)
    
    # Relationships
    cycle = relationship("TestCycle", back_populates="test_execution_versions")
    report = relationship("Report", back_populates="test_execution_versions")
    # test_plan = relationship("TestPlan", back_populates="execution_versions")  # No TestPlan model yet
    attribute = relationship("ReportAttribute", back_populates="test_execution_versions")
    sample = relationship("Sample", back_populates="test_execution_versions")


class ObservationVersion(CustomPKModel, AuditMixin, VersionedMixin):
    """Versioned observations"""
    
    __tablename__ = "observation_versions"
    __versioned__ = True
    
    observation_version_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Link to original observation
    observation_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Context
    cycle_id = Column(Integer, ForeignKey("test_cycles.cycle_id"), nullable=False)
    report_id = Column(Integer, ForeignKey("reports.report_id"), nullable=False)
    # test_plan_id = Column(UUID(as_uuid=True))  # No test_plans table yet
    
    # Observation details
    observation_type = Column(String(50), nullable=False)  # data_quality, process, compliance, etc.
    severity = Column(String(20), nullable=False)  # critical, high, medium, low
    
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    
    # Impact assessment
    impact_description = Column(Text)
    affected_attributes = Column(JSONB)  # List of attribute IDs
    affected_samples = Column(JSONB)  # List of sample IDs
    affected_lobs = Column(JSONB)  # List of LOB names
    
    # Resolution
    resolution_status = Column(String(50))  # open, in_progress, resolved, accepted
    resolution_description = Column(Text)
    resolution_date = Column(DateTime(timezone=True))
    resolved_by = Column(String(255))
    
    # Grouping
    group_id = Column(UUID(as_uuid=True))
    is_group_parent = Column(Boolean, default=False)
    
    # Evidence and documentation
    evidence_links = Column(JSONB)
    supporting_documents = Column(JSONB)
    
    # Metadata for tracking
    tracking_metadata = Column(JSONB)
    
    # Relationships
    cycle = relationship("TestCycle", back_populates="observation_versions")
    report = relationship("Report", back_populates="observation_versions")
    # test_plan = relationship("TestPlan", back_populates="observation_versions")  # No TestPlan model yet


class ScopingDecisionVersion(CustomPKModel, AuditMixin, VersionedMixin):
    """Versioned scoping decisions"""
    
    __tablename__ = "cycle_report_scoping_decision_versions"
    __versioned__ = True
    
    decision_version_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Link to original decision
    decision_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Context
    cycle_id = Column(Integer, ForeignKey("test_cycles.cycle_id"), nullable=False)
    report_id = Column(Integer, ForeignKey("reports.report_id"), nullable=False)
    attribute_id = Column(Integer, ForeignKey("report_attributes.attribute_id"), nullable=False)
    
    # Scoping decision
    is_in_scope = Column(Boolean, nullable=False)
    scope_reason = Column(Text)
    
    # Testing parameters
    testing_approach = Column(String(100))  # automated, manual, hybrid
    sample_size_override = Column(Integer)
    special_instructions = Column(Text)
    
    # Risk assessment
    risk_level = Column(String(20))  # high, medium, low
    risk_factors = Column(JSONB)
    
    # LOB assignment
    assigned_lobs = Column(JSONB)  # List of LOB names
    
    # Dependencies
    depends_on_attributes = Column(JSONB)  # List of attribute IDs
    
    # Relationships
    cycle = relationship("TestCycle", back_populates="cycle_report_scoping_decision_versions")
    report = relationship("Report", back_populates="cycle_report_scoping_decision_versions")
    attribute = relationship("ReportAttribute", back_populates="cycle_report_scoping_decision_versions")


# Update existing models to inherit from VersionedMixin
# This would be done in the actual model files

"""
Example of updating existing model:

class ReportAttribute(CustomPKModel, AuditMixin, VersionedMixin):
    __tablename__ = "report_attributes"
    __versioned__ = True
    
    # Existing columns...
    attribute_id = Column(UUID(as_uuid=True), primary_key=True)
    # ... rest of the model
"""


class VersionedAttributeScopingRecommendation(CustomPKModel, AuditMixin, VersionedMixin):
    """Versioned attribute scoping recommendations"""
    
    __tablename__ = "cycle_report_scoping_attribute_recommendation_versions"
    __versioned__ = True
    
    recommendation_version_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Link to original
    recommendation_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Context
    cycle_id = Column(Integer, ForeignKey("test_cycles.cycle_id"), nullable=False)
    report_id = Column(Integer, ForeignKey("reports.report_id"), nullable=False)
    attribute_id = Column(Integer, ForeignKey("report_attributes.attribute_id"), nullable=False)
    
    # LLM recommendation
    llm_recommendation = Column(Boolean, nullable=False)
    llm_confidence_score = Column(Float)
    llm_reasoning = Column(Text)
    llm_provider = Column(String(50))
    
    # Tester decision
    tester_decision = Column(Boolean)
    tester_reasoning = Column(Text)
    decision_timestamp = Column(DateTime(timezone=True))
    
    # Override information
    is_override = Column(Boolean, default=False)
    override_justification = Column(Text)
    
    # Additional metadata
    risk_indicators = Column(JSONB)
    testing_complexity = Column(String(20))  # high, medium, low
    estimated_effort_hours = Column(Float)
    
    # Relationships
    cycle = relationship("TestCycle", back_populates="scoping_recommendation_versions")
    report = relationship("Report", back_populates="scoping_recommendation_versions")
    attribute = relationship("ReportAttribute", back_populates="scoping_recommendation_versions")


# Service for managing versioned entities
class VersioningService:
    """Service for managing versioned entities"""
    
    @staticmethod
    async def create_version(
        db_session,
        entity: VersionedMixin,
        reason: str,
        user_id: str,
        notes: Optional[str] = None,
        auto_approve: bool = False
    ):
        """Create a new version of an entity"""
        # Create new version
        new_version = entity.create_new_version(
            reason=reason,
            user_id=user_id,
            notes=notes,
            auto_approve=auto_approve
        )
        
        # Add to session
        db_session.add(new_version)
        
        # Create history record
        from app.models.versioning import VersionHistory
        
        history = VersionHistory.record_change(
            entity_type=entity.__class__.__name__,
            entity_id=str(entity.id),
            entity_name=getattr(entity, 'name', str(entity.id)),
            version_number=new_version.version_number,
            change_type="created",
            changed_by=user_id,
            change_reason=reason,
            cycle_id=getattr(entity, 'cycle_id', None),
            report_id=getattr(entity, 'report_id', None)
        )
        
        db_session.add(history)
        
        # Commit changes
        await db_session.commit()
        
        return new_version
    
    @staticmethod
    async def get_version_history(
        db_session,
        entity_type: str,
        entity_id: str,
        limit: int = 10
    ):
        """Get version history for an entity"""
        from sqlalchemy import select
        from app.models.versioning import VersionHistory
        
        query = select(VersionHistory).where(
            (VersionHistory.entity_type == entity_type) &
            (VersionHistory.entity_id == entity_id)
        ).order_by(VersionHistory.changed_at.desc()).limit(limit)
        
        result = await db_session.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def compare_versions(
        db_session,
        entity_class,
        version1_id: str,
        version2_id: str
    ):
        """Compare two versions of an entity"""
        from app.models.versioning import VersionComparison
        
        # Get both versions
        version1 = await db_session.get(entity_class, version1_id)
        version2 = await db_session.get(entity_class, version2_id)
        
        if not version1 or not version2:
            raise ValueError("One or both versions not found")
        
        # Compare
        return VersionComparison.compare_versions(version1, version2)
    
    @staticmethod
    async def revert_to_version(
        db_session,
        entity_class,
        entity_id: str,
        target_version_number: int,
        user_id: str,
        reason: str
    ):
        """Revert to a previous version"""
        from sqlalchemy import select
        
        # Find the target version
        query = select(entity_class).where(
            (entity_class.id == entity_id) &
            (entity_class.version_number == target_version_number)
        )
        
        result = await db_session.execute(query)
        target_version = result.scalar_one_or_none()
        
        if not target_version:
            raise ValueError(f"Version {target_version_number} not found")
        
        # Create new version based on target
        new_version = await VersioningService.create_version(
            db_session=db_session,
            entity=target_version,
            reason=f"Reverted to version {target_version_number}: {reason}",
            user_id=user_id,
            notes=f"Reverted from version {entity_class.version_number}",
            auto_approve=False
        )
        
        return new_version