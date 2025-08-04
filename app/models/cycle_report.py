"""
Cycle Report model (many-to-many relationship between cycles and reports)
"""

from sqlalchemy import Column, Integer, ForeignKey, DateTime, String
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ENUM
from app.models.base import CustomPKModel
from app.models.audit_mixin import AuditMixin

# Cycle report status enum
cycle_report_status_enum = ENUM(
    'Not Started',
    'In Progress',
    'Complete',
    name='cycle_report_status_enum'
)


class CycleReport(CustomPKModel, AuditMixin):
    """Cycle reports (many-to-many between cycles and reports)"""
    
    __tablename__ = "cycle_reports"
    
    cycle_id = Column(Integer, ForeignKey('test_cycles.cycle_id'), primary_key=True)
    report_id = Column(Integer, ForeignKey('reports.id'), primary_key=True)
    tester_id = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    status = Column(cycle_report_status_enum, default='Not Started', nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    workflow_id = Column(String(255), nullable=True, index=True)
    
    # Relationships
    cycle = relationship("app.models.test_cycle.TestCycle", back_populates="cycle_reports")
    report = relationship("app.models.report.Report", back_populates="cycle_reports")
    tester = relationship("app.models.user.User", foreign_keys=[tester_id], back_populates="assigned_reports")
    workflow_phases = relationship("app.models.workflow.WorkflowPhase", 
                                 foreign_keys="[app.models.workflow.WorkflowPhase.cycle_id, app.models.workflow.WorkflowPhase.report_id]",
                                 primaryjoin="and_(CycleReport.cycle_id==app.models.workflow.WorkflowPhase.cycle_id, "
                                           "CycleReport.report_id==app.models.workflow.WorkflowPhase.report_id)",
                                 overlaps="workflow_phases")
    # test_executions = relationship("app.models.test_execution.TestExecution",
    #                              foreign_keys="[app.models.test_execution.TestExecution.cycle_id, app.models.test_execution.TestExecution.report_id]",
    #                              primaryjoin="and_(CycleReport.cycle_id==app.models.test_execution.TestExecution.cycle_id, "
    #                                        "CycleReport.report_id==app.models.test_execution.TestExecution.report_id)",
    #                              overlaps="test_executions")  # DEPRECATED: Access through workflow_phases
    # observations = relationship("app.models.observation_enhanced.Observation",
    #                          foreign_keys="[app.models.observation_enhanced.Observation.cycle_id, app.models.observation_enhanced.Observation.report_id]",
    #                          primaryjoin="and_(CycleReport.cycle_id==app.models.observation_enhanced.Observation.cycle_id, "
    #                                    "CycleReport.report_id==app.models.observation_enhanced.Observation.report_id)")
    # Disabled: Observations now reference cycle/report through phase_id relationship, not direct foreign keys
    
    def __repr__(self):
        return f"<CycleReport(cycle_id={self.cycle_id}, report_id={self.report_id})>" 