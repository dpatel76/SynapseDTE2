"""
Workflow models for phases
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, Date, DateTime
from sqlalchemy.orm import relationship, synonym
from sqlalchemy.dialects.postgresql import ENUM, JSONB
from app.models.base import CustomPKModel
from app.models.audit_mixin import AuditMixin

# Workflow phase enum
workflow_phase_enum = ENUM(
    'Planning',
    'Data Profiling',
    'Scoping',
    'Data Provider ID',
    'Data Owner Identification',
    'Sampling',
    'Request Info',
    'Testing',
    'Observations',
    'Sample Selection',
    'Data Owner ID',
    'Test Execution',
    'Preparing Test Report',
    'Finalize Test Report',
    name='workflow_phase_enum'
)

# Workflow phase state enum (progress tracking)
workflow_phase_state_enum = ENUM(
    'Not Started',
    'In Progress', 
    'Complete',
    name='workflow_phase_state_enum'
)

# Workflow phase status enum (schedule adherence)
workflow_phase_status_enum = ENUM(
    'On Track',
    'At Risk',
    'Past Due',
    name='workflow_phase_status_enum'
)

# Legacy status enum for backward compatibility
phase_status_enum = ENUM(
    'Not Started',
    'In Progress',
    'Complete',
    'Pending Approval',
    name='phase_status_enum'
)

# Cycle report status enum
cycle_report_status_enum = ENUM(
    'Not Started',
    'In Progress',
    'Complete',
    name='cycle_report_status_enum'
)

# Mandatory flag enum
mandatory_flag_enum = ENUM(
    'Mandatory',
    'Conditional',
    'Optional',
    name='mandatory_flag_enum'
)


class WorkflowPhase(CustomPKModel, AuditMixin):
    """Unified workflow phase tracking - replaces all individual phase tables"""
    
    __tablename__ = "workflow_phases"
    
    phase_id = Column(Integer, primary_key=True, index=True)
    cycle_id = Column(Integer, ForeignKey('test_cycles.cycle_id'), nullable=False)
    report_id = Column(Integer, ForeignKey('reports.id'), nullable=False)
    phase_name = Column(workflow_phase_enum, nullable=False)
    phase_order = Column(Integer, nullable=False)  # 1-9 for the 9 phases
    
    # Legacy status field (for backward compatibility)
    status = Column(phase_status_enum, default='Not Started', nullable=False)
    
    # New enhanced state and status tracking
    state = Column(workflow_phase_state_enum, default='Not Started', nullable=False)
    schedule_status = Column(workflow_phase_status_enum, default='On Track', nullable=False)
    
    # Phase-specific tracking (consolidated from old phase tables)
    data_requested_at = Column(DateTime(timezone=True), nullable=True)  # For data_request phase
    data_requested_by = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    data_received_at = Column(DateTime(timezone=True), nullable=True)
    rules_generated_at = Column(DateTime(timezone=True), nullable=True)  # For data_profiling phase
    profiling_executed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Risk and metadata
    risk_level = Column(String(20), nullable=True)  # 'low', 'medium', 'high'
    phase_metadata = Column("metadata", JSONB, nullable=True)  # Maps to 'metadata' column in database
    
    # Progress tracking
    progress_percentage = Column(Integer, default=0)
    estimated_completion_date = Column(Date, nullable=True)
    
    # SLA tracking
    sla_deadline = Column(DateTime(timezone=True), nullable=True)
    is_sla_breached = Column(Boolean, default=False)
    
    # Override capabilities
    state_override = Column(workflow_phase_state_enum, nullable=True)  # Tester can override state
    status_override = Column(workflow_phase_status_enum, nullable=True)  # Tester can override status
    override_reason = Column(Text, nullable=True)  # Reason for override
    override_by = Column(Integer, ForeignKey('users.user_id'), nullable=True)  # Who made the override
    override_at = Column(DateTime(timezone=True), nullable=True)  # When override was made
    
    # Date tracking (planned vs actual)
    planned_start_date = Column(Date, nullable=True)
    planned_end_date = Column(Date, nullable=True)
    actual_start_date = Column(DateTime(timezone=True), nullable=True)
    actual_end_date = Column(DateTime(timezone=True), nullable=True)
    
    # User tracking
    started_by = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    completed_by = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    
    # Additional notes
    notes = Column(Text, nullable=True)
    
    # Phase-specific data storage (e.g., samples for Sample Selection phase)
    phase_data = Column(JSONB, nullable=True)
    
    # Relationships
    cycle = relationship("app.models.test_cycle.TestCycle", back_populates="workflow_phases", overlaps="workflow_phases")
    report = relationship("app.models.report.Report", backref="workflow_phases", overlaps="workflow_phases")
    activities = relationship("app.models.workflow_activity.WorkflowActivity", back_populates="phase", cascade="all, delete-orphan")
    
    # User relationships
    started_by_user = relationship("app.models.user.User", foreign_keys=[started_by])
    completed_by_user = relationship("app.models.user.User", foreign_keys=[completed_by])
    override_by_user = relationship("app.models.user.User", foreign_keys=[override_by])
    data_requester = relationship("app.models.user.User", foreign_keys=[data_requested_by])
    
    # Data relationships - all cycle_report_* tables reference this via phase_id
    # Planning phase
    planning_attributes = relationship("app.models.report_attribute.ReportAttribute", back_populates="phase")
    pde_mapping_reviews = relationship("app.models.pde_mapping_review.PDEMappingReview", back_populates="phase")
    
    # New unified planning phase - temporarily disabled due to table conflicts
    # planning_versions = relationship("app.models.planning.PlanningVersion", back_populates="phase")
    # planning_data_sources = relationship("app.models.planning.PlanningDataSource", back_populates="phase")
    # planning_pde_mappings = relationship("app.models.planning.PlanningPDEMapping", back_populates="phase")
    
    # Scoping phase
    scoping_recommendations = relationship("app.models.scoping.AttributeScopingRecommendation", back_populates="phase")
    scoping_decisions = relationship("app.models.scoping.ScopingDecision", back_populates="phase")
    scoping_submissions = relationship("app.models.scoping.ScopingSubmission", back_populates="phase")
    scoping_reviews = relationship("app.models.scoping.ReportOwnerScopingReview", back_populates="phase")
    
    # New consolidated scoping phase
    scoping_versions = relationship("app.models.scoping.ScopingVersion", back_populates="phase", overlaps="scoping_reviews,scoping_submissions")
    
    # Data profiling phase
    profiling_files = relationship("app.models.data_profiling.DataProfilingFile", back_populates="phase")
    profiling_rules = relationship("app.models.data_profiling.ProfilingRule", back_populates="phase")
    profiling_results = relationship("app.models.data_profiling.ProfilingResult", back_populates="phase")
    # profiling_scores = relationship("app.models.data_profiling.AttributeProfilingScore", back_populates="phase")  # DEPRECATED - table removed
    
    # Sample selection phase
    # samples = relationship("app.models.testing.Sample", back_populates="phase")  # DEPRECATED: Use unified sample selection system
    sample_selection_versions = relationship("app.models.sample_selection.SampleSelectionVersion", back_populates="phase")
    
    # Test execution phase
    test_executions = relationship("app.models.test_execution.TestExecution", back_populates="phase")
    # document_analyses = relationship("app.models.test_execution.DocumentAnalysis", back_populates="phase")  # DocumentAnalysis doesn't have phase_id
    # database_tests = relationship("app.models.test_execution.DatabaseTest", back_populates="phase")  # DatabaseTest doesn't have phase_id
    
    # Observation management phase
    observations = relationship("app.models.observation_management.ObservationRecord", back_populates="phase")
    observation_versions = relationship("app.models.observation_management.ObservationVersionRecord", back_populates="phase")
    # impact_assessments = relationship("app.models.observation_management.ObservationImpactAssessment", back_populates="phase")  # ObservationImpactAssessment doesn't have phase_id
    # observation_approvals = relationship("app.models.observation_management.ObservationApproval", back_populates="phase")  # ObservationApproval doesn't have phase_id
    # observation_resolutions = relationship("app.models.observation_management.ObservationResolution", back_populates="phase")  # ObservationResolution doesn't have phase_id
    
    # Test report phase
    # report_sections = relationship("app.models.observation_enhanced.TestReportSection", back_populates="phase")  # Disabled - TestReportSection moved to test_report.py
    test_report_sections = relationship("app.models.test_report.TestReportSection", back_populates="phase")
    test_report_generation = relationship("app.models.test_report.TestReportGeneration", back_populates="phase")
    
    # Standard phase names and their order
    PHASE_DEFINITIONS = {
        "Planning": {"order": 1, "display_name": "Planning & Attribute Definition"},
        "Data Profiling": {"order": 2, "display_name": "Data Profiling & Quality Assessment"},
        "Scoping": {"order": 3, "display_name": "Scoping & Risk Assessment"},
        "Sample Selection": {"order": 4, "display_name": "Sample Selection"},
        "Data Provider ID": {"order": 5, "display_name": "Data Request to CDOs"},
        "Request Info": {"order": 6, "display_name": "Request for Information"},
        "Test Execution": {"order": 7, "display_name": "Test Execution"},
        "Observations": {"order": 8, "display_name": "Observation Management"},
        "Finalize Test Report": {"order": 9, "display_name": "Test Report Generation"}
    }
    
    @classmethod
    def create_phases_for_report(cls, cycle_id: int, report_id: int, created_by: int):
        """Create all 9 phases for a new report in a test cycle"""
        phases = []
        for phase_name, phase_info in cls.PHASE_DEFINITIONS.items():
            phase = cls(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_name=phase_name,
                phase_order=phase_info["order"],
                status="Not Started",
                state="Not Started",
                schedule_status="On Track",
                created_by=created_by,
                phase_metadata={
                    "display_name": phase_info["display_name"],
                    "activities_count": 0,
                    "activities_completed": 0
                }
            )
            phases.append(phase)
        return phases
    
    def can_start(self) -> bool:
        """Check if this phase can be started based on previous phase completion"""
        if self.phase_order == 1:
            return True
        
        # Check if previous phase is completed
        # This would be implemented based on business rules
        return True
    
    def update_progress(self):
        """Update progress percentage based on completed activities"""
        if not self.activities:
            self.progress_percentage = 0
            return
        
        total_activities = len(self.activities)
        completed_activities = len([a for a in self.activities if a.status == "COMPLETED"])
        
        self.progress_percentage = int((completed_activities / total_activities) * 100)
        
        # Update metadata
        if self.phase_metadata is None:
            self.phase_metadata = {}
        self.phase_metadata["activities_count"] = total_activities
        self.phase_metadata["activities_completed"] = completed_activities
    
    def __repr__(self):
        return f"<WorkflowPhase(phase_id={self.phase_id}, phase_name='{self.phase_name}', state='{self.state}', status='{self.schedule_status}')>" 