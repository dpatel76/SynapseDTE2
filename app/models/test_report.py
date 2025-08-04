"""
Test Report Phase unified models
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from datetime import datetime

from app.models.base import BaseModel
from app.models.audit_mixin import AuditMixin


class TestReportSection(BaseModel, AuditMixin):
    """Test report sections with built-in approval workflow"""
    __tablename__ = "cycle_report_test_report_sections"
    
    phase_id = Column(Integer, ForeignKey('workflow_phases.phase_id'), nullable=False)
    cycle_id = Column(Integer, ForeignKey('test_cycles.cycle_id'), nullable=False)
    report_id = Column(Integer, ForeignKey('reports.id'), nullable=False)
    
    # Section identification
    section_name = Column(String(100), nullable=False)  # 'executive_summary', 'strategic_approach', etc.
    section_title = Column(String(255), nullable=False)
    section_order = Column(Integer, nullable=False)
    section_type = Column(String(50), nullable=False, default='standard')  # Added to match database schema
    
    # Section content (unified storage)
    section_content = Column(JSONB, nullable=False)
    """
    Unified structure:
    {
        "summary": "Executive summary text",
        "content": "Main section content",
        "metrics": {
            "key_metric_1": 123,
            "key_metric_2": 456
        },
        "charts": [
            {
                "type": "bar_chart",
                "title": "Test Results by Phase",
                "data": {...}
            }
        ],
        "tables": [
            {
                "title": "Phase Summary",
                "headers": ["Phase", "Status", "Completion"],
                "rows": [...]
            }
        ],
        "artifacts": [
            {
                "type": "document",
                "name": "Planning Phase Report",
                "path": "/path/to/file.pdf"
            }
        ]
    }
    """
    
    # Section metadata
    data_sources = Column(JSONB, nullable=True)  # Which phases/tables this section gets data from
    last_generated_at = Column(DateTime(timezone=True), nullable=True)
    requires_refresh = Column(Boolean, default=False, nullable=False)
    
    # Section status
    status = Column(String(50), default='draft', nullable=False)  # 'draft', 'generated', 'approved', 'final'
    
    # Approval workflow (built-in)
    tester_approved = Column(Boolean, default=False, nullable=False)
    tester_approved_by = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    tester_approved_at = Column(DateTime(timezone=True), nullable=True)
    tester_notes = Column(Text, nullable=True)
    
    report_owner_approved = Column(Boolean, default=False, nullable=False)
    report_owner_approved_by = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    report_owner_approved_at = Column(DateTime(timezone=True), nullable=True)
    report_owner_notes = Column(Text, nullable=True)
    
    executive_approved = Column(Boolean, default=False, nullable=False)
    executive_approved_by = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    executive_approved_at = Column(DateTime(timezone=True), nullable=True)
    executive_notes = Column(Text, nullable=True)
    
    # Final output formats
    markdown_content = Column(Text, nullable=True)
    html_content = Column(Text, nullable=True)
    pdf_path = Column(String(500), nullable=True)
    
    # Relationships
    phase = relationship("app.models.workflow.WorkflowPhase", back_populates="test_report_sections")
    cycle = relationship("app.models.test_cycle.TestCycle")
    report = relationship("app.models.report.Report")
    
    # Approver relationships
    tester_approver = relationship("app.models.user.User", foreign_keys=[tester_approved_by])
    report_owner_approver = relationship("app.models.user.User", foreign_keys=[report_owner_approved_by])
    executive_approver = relationship("app.models.user.User", foreign_keys=[executive_approved_by])
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('phase_id', 'section_name', name='uq_test_report_section_phase'),
        UniqueConstraint('cycle_id', 'report_id', 'section_name', name='uq_test_report_section_report'),
        Index('idx_test_report_sections_phase', 'phase_id'),
        Index('idx_test_report_sections_cycle_report', 'cycle_id', 'report_id'),
        Index('idx_test_report_sections_status', 'status'),
        Index('idx_test_report_sections_approvals', 'tester_approved', 'report_owner_approved', 'executive_approved'),
    )
    
    def is_fully_approved(self) -> bool:
        """Check if all required approvals are received"""
        return (
            self.tester_approved and
            self.report_owner_approved and
            self.executive_approved
        )
    
    def get_approval_status(self) -> str:
        """Get current approval status"""
        if not self.tester_approved:
            return 'pending_tester'
        elif not self.report_owner_approved:
            return 'pending_report_owner'
        elif not self.executive_approved:
            return 'pending_executive'
        else:
            return 'fully_approved'
    
    def get_next_approver_level(self) -> str:
        """Get the next level of approval needed"""
        if not self.tester_approved:
            return 'tester'
        elif not self.report_owner_approved:
            return 'report_owner'
        elif not self.executive_approved:
            return 'executive'
        else:
            return None
    
    def approve_section(self, approver_id: int, approval_level: str, notes: str = None) -> bool:
        """Approve section at specific level"""
        if approval_level == 'tester':
            self.tester_approved = True
            self.tester_approved_by = approver_id
            self.tester_approved_at = datetime.utcnow()
            self.tester_notes = notes
        elif approval_level == 'report_owner':
            self.report_owner_approved = True
            self.report_owner_approved_by = approver_id
            self.report_owner_approved_at = datetime.utcnow()
            self.report_owner_notes = notes
        elif approval_level == 'executive':
            self.executive_approved = True
            self.executive_approved_by = approver_id
            self.executive_approved_at = datetime.utcnow()
            self.executive_notes = notes
        else:
            return False
        
        # Update section status if all approvals received
        if self.is_fully_approved():
            self.status = 'final'
        
        return True


class TestReportGeneration(BaseModel, AuditMixin):
    """Test report generation metadata and tracking"""
    __tablename__ = "cycle_report_test_report_generation"
    phase_id = Column(Integer, ForeignKey('workflow_phases.phase_id'), nullable=False)
    cycle_id = Column(Integer, ForeignKey('test_cycles.cycle_id'), nullable=False)
    report_id = Column(Integer, ForeignKey('reports.id'), nullable=False)
    
    # Generation metadata
    generation_started_at = Column(DateTime(timezone=True), nullable=True)
    generation_completed_at = Column(DateTime(timezone=True), nullable=True)
    generation_duration_ms = Column(Integer, nullable=True)
    
    # Data collection summary
    phase_data_collected = Column(JSONB, nullable=True)
    """
    Structure:
    {
        "planning": {
            "total_attributes": 150,
            "cde_count": 45,
            "primary_keys": 8,
            "data_collected_at": "2024-01-15T10:00:00Z"
        },
        "scoping": {
            "attributes_selected": 120,
            "approval_rate": 0.85,
            "data_collected_at": "2024-01-15T10:01:00Z"
        },
        "test_execution": {
            "tests_executed": 500,
            "pass_rate": 0.92,
            "data_collected_at": "2024-01-15T10:02:00Z"
        },
        "observations": {
            "total_observations": 15,
            "high_severity": 3,
            "resolved": 10,
            "data_collected_at": "2024-01-15T10:03:00Z"
        }
    }
    """
    
    # Generation status
    status = Column(String(50), default='pending', nullable=False)  # 'pending', 'in_progress', 'completed', 'failed'
    error_message = Column(Text, nullable=True)
    
    # Output summary
    total_sections = Column(Integer, nullable=True)
    sections_completed = Column(Integer, nullable=True)
    output_formats_generated = Column(ARRAY(Text), nullable=True)  # ['markdown', 'html', 'pdf']
    
    # Phase completion tracking
    all_approvals_received = Column(Boolean, default=False, nullable=False)
    phase_completion_ready = Column(Boolean, default=False, nullable=False)
    phase_completed_at = Column(DateTime(timezone=True), nullable=True)
    phase_completed_by = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    
    # User tracking
    generated_by = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    
    # Relationships
    phase = relationship("app.models.workflow.WorkflowPhase", back_populates="test_report_generation")
    cycle = relationship("app.models.test_cycle.TestCycle")
    report = relationship("app.models.report.Report")
    generator = relationship("app.models.user.User", foreign_keys=[generated_by])
    completer = relationship("app.models.user.User", foreign_keys=[phase_completed_by])
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('phase_id', name='uq_test_report_generation_phase'),
        Index('idx_test_report_generation_phase', 'phase_id'),
        Index('idx_test_report_generation_cycle_report', 'cycle_id', 'report_id'),
        Index('idx_test_report_generation_status', 'status'),
    )
    
    def start_generation(self, user_id: int) -> None:
        """Start report generation"""
        self.status = 'in_progress'
        self.generation_started_at = datetime.utcnow()
        self.generated_by = user_id
        self.error_message = None
    
    def complete_generation(self, total_sections: int, sections_completed: int) -> None:
        """Complete report generation"""
        self.status = 'completed'
        self.generation_completed_at = datetime.utcnow()
        self.total_sections = total_sections
        self.sections_completed = sections_completed
        
        if self.generation_started_at:
            duration = (self.generation_completed_at - self.generation_started_at).total_seconds() * 1000
            self.generation_duration_ms = int(duration)
    
    def fail_generation(self, error_message: str) -> None:
        """Mark generation as failed"""
        self.status = 'failed'
        self.error_message = error_message
        self.generation_completed_at = datetime.utcnow()
        
        if self.generation_started_at:
            duration = (self.generation_completed_at - self.generation_started_at).total_seconds() * 1000
            self.generation_duration_ms = int(duration)
    
    def update_phase_data(self, phase_name: str, data: dict) -> None:
        """Update phase data collection summary"""
        if self.phase_data_collected is None:
            self.phase_data_collected = {}
        
        self.phase_data_collected[phase_name] = {
            **data,
            "data_collected_at": datetime.utcnow().isoformat()
        }
    
    def get_completion_percentage(self) -> float:
        """Get generation completion percentage"""
        if not self.total_sections or self.total_sections == 0:
            return 0.0
        
        return (self.sections_completed / self.total_sections) * 100.0


# Standard report sections configuration
STANDARD_REPORT_SECTIONS = [
    {
        'name': 'executive_summary',
        'title': 'Executive Summary',
        'order': 1,
        'data_sources': ['planning', 'test_execution', 'observations'],
        'required_approvals': ['tester', 'report_owner', 'executive']
    },
    {
        'name': 'strategic_approach',
        'title': 'Strategic Approach',
        'order': 2,
        'data_sources': ['planning', 'scoping'],
        'required_approvals': ['tester', 'report_owner']
    },
    {
        'name': 'testing_coverage',
        'title': 'Testing Coverage',
        'order': 3,
        'data_sources': ['scoping', 'sample_selection', 'test_execution'],
        'required_approvals': ['tester', 'report_owner']
    },
    {
        'name': 'phase_analysis',
        'title': 'Phase Analysis',
        'order': 4,
        'data_sources': ['planning', 'scoping', 'sample_selection', 'test_execution'],
        'required_approvals': ['tester', 'report_owner']
    },
    {
        'name': 'testing_results',
        'title': 'Testing Results',
        'order': 5,
        'data_sources': ['test_execution', 'observations'],
        'required_approvals': ['tester', 'report_owner']
    },
    {
        'name': 'value_delivery',
        'title': 'Value Delivery',
        'order': 6,
        'data_sources': ['test_execution', 'observations'],
        'required_approvals': ['tester', 'report_owner']
    },
    {
        'name': 'recommendations',
        'title': 'Recommendations',
        'order': 7,
        'data_sources': ['observations'],
        'required_approvals': ['tester', 'report_owner']
    },
    {
        'name': 'executive_attestation',
        'title': 'Executive Attestation',
        'order': 8,
        'data_sources': ['all'],
        'required_approvals': ['tester', 'report_owner', 'executive']
    }
]