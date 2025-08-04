"""
Test Cycle management model
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, Date
from sqlalchemy.orm import relationship
from app.models.base import CustomPKModel
from app.models.audit_mixin import AuditMixin


class TestCycle(CustomPKModel, AuditMixin):
    """Test cycle model for managing testing workflows"""
    
    __tablename__ = "test_cycles"
    
    cycle_id = Column(Integer, primary_key=True, index=True)
    cycle_name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    test_executive_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)  # Made nullable to match our API
    status = Column(String(50), nullable=False, default="Active")
    
    # Temporal workflow integration
    workflow_id = Column(String(255), nullable=True, index=True)
    
    # Relationships
    test_executive = relationship("User", foreign_keys=[test_executive_id], back_populates="managed_cycles")
    cycle_reports = relationship("CycleReport", back_populates="cycle", cascade="all, delete-orphan")
    workflow_phases = relationship("WorkflowPhase", back_populates="cycle", cascade="all, delete-orphan")
    # Documents are accessed via: cycle.workflow_phases[x].documents (phase-based architecture)
    # documents = relationship("CycleReportDocument", back_populates="test_cycle")  # Removed - no direct FK, CycleReportDocument only has phase_id
    # Planning attributes relationship updated to use new unified planning models
    # Use through WorkflowPhase -> PlanningVersion -> PlanningAttribute instead of direct relationship
    # data_provider_assignments = relationship("DataProviderAssignment", back_populates="cycle")  # Model doesn't exist
    
    # Scoping phase relationships - temporarily disabled during transition to unified scoping
    # scoping_recommendations = relationship("AttributeScopingRecommendation", back_populates="cycle")
    # scoping_decisions = relationship("ScopingDecision", back_populates="cycle")
    # scoping_submissions = relationship("ScopingSubmission", back_populates="cycle")
    # scoping_reviews = relationship("ReportOwnerScopingReview", back_populates="cycle")
    # scoping_audit_logs = relationship("ScopingAuditLog", back_populates="cycle")
    
    # Data provider phase relationships
    # attribute_lob_assignments removed - table doesn't exist
    # data_owner_assignments removed - using universal assignments instead
    # data_executive_notifications = relationship("DataExecutiveNotification", back_populates="cycle")  # Deprecated - using universal assignments
    # historical_assignments removed - table doesn't exist
    # sla_violations removed - data_owner_sla_violations table doesn't exist
    # data_owner_audit_logs = relationship("DataOwnerPhaseAuditLog", back_populates="cycle")  # Now phase-based
    
    # Sample selection phase relationships
    # Sample selection data accessed through workflow_phases -> SampleSelectionVersion (new unified architecture)
    # sample_selection_phases = relationship("SampleSelectionPhase", back_populates="cycle")  # DEPRECATED: Use workflow_activities
    # Sample selection audit logs moved to unified audit system
    
    # Individual samples relationships
    # Sample relationships (removed sample_individual references)
    
    # Data Profiling phase relationships
    # data_profiling_phases = relationship("DataProfilingPhase", back_populates="cycle")  # DEPRECATED: Use workflow_activities
    
    # Request for Information phase relationships
    # request_info_phases = relationship("RequestInfoPhase", back_populates="cycle")  # DEPRECATED: Use workflow_activities
    
    # Testing execution relationships
    # samples = relationship("Sample", back_populates="cycle")  # DEPRECATED: Use unified sample selection system
    # test_executions = relationship("app.models.test_execution.TestExecution", back_populates="cycle")  # Removed - no direct cycle_id in TestExecution
    # observations = relationship("app.models.observation_enhanced.Observation", back_populates="cycle")  # Removed due to circular dependency
    
    # Observation management relationships
    # observation_management_phases = relationship("ObservationManagementPhase", back_populates="cycle")  # DEPRECATED: Use workflow_activities
    
    # Metrics relationships
    phase_metrics = relationship("PhaseMetrics", back_populates="cycle")
    execution_metrics = relationship("ExecutionMetrics", back_populates="cycle")
    
    # Audit relationships
    llm_audit_logs = relationship("LLMAuditLog", back_populates="cycle")
    
    # Versioned model relationships - Temporarily disabled until versioned models are fully configured
    # data_profiling_rules = relationship("DataProfilingRuleVersion", back_populates="cycle")
    # test_execution_versions = relationship("TestExecutionVersion", back_populates="cycle")
    # observation_versions = relationship("ObservationVersion", back_populates="cycle")
    # scoping_decision_versions = relationship("ScopingDecisionVersion", back_populates="cycle")
    # scoping_recommendation_versions = relationship("VersionedAttributeScopingRecommendation", back_populates="cycle")
    
    # Report Owner Assignment relationships - Deprecated (using universal assignments)
    # report_owner_assignments = relationship("ReportOwnerAssignment", back_populates="cycle")
    
    # Data Source Configuration relationships updated to use new unified planning models
    # Use through WorkflowPhase -> PlanningVersion -> PlanningDataSource instead of direct relationship
    
    def __repr__(self):
        return f"<TestCycle(id={self.cycle_id}, name='{self.cycle_name}', executive_id={self.test_executive_id})>" 