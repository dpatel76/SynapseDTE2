"""
Unified Test Execution Models
Simplified architecture based on corrected implementation plan
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, UniqueConstraint, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import BaseModel, Base
from app.models.user import User
from app.models.workflow import WorkflowPhase
from app.models.test_cycle import TestCycle
from app.models.report import Report


class TestExecution(BaseModel):
    """
    Unified test execution results table with evidence integration
    Stores all test execution data, LLM analysis, and database results
    """
    __tablename__ = 'cycle_report_test_execution_results'
    
    id = Column(Integer, primary_key=True)
    phase_id = Column(Integer, ForeignKey('workflow_phases.phase_id'), nullable=False)
    # Note: cycle_id and report_id were removed in phase_id_refactoring migration
    # They are accessed through the phase relationship
    test_case_id = Column(String(255), nullable=False)  # Stores string representation of test case ID
    
    # Link to approved evidence from Request for Information
    evidence_id = Column(Integer, nullable=False)  # References evidence from test cases
    
    # Execution versioning (multiple executions per test case)
    execution_number = Column(Integer, nullable=False)
    is_latest_execution = Column(Boolean, default=False)
    execution_reason = Column(String(100))  # 'initial', 'retry', 'evidence_updated', 'manual_rerun'
    
    # Test execution configuration
    test_type = Column(String(50), nullable=False)  # 'document_analysis', 'database_test', 'manual_test', 'hybrid'
    analysis_method = Column(String(50), nullable=False)  # 'llm_analysis', 'database_query', 'manual_review'
    
    # Core test data (as per current implementation)
    sample_value = Column(Text)  # Expected value from sample data
    extracted_value = Column(Text)  # Actual value extracted from evidence
    expected_value = Column(Text)  # Business rule expected value (may differ from sample)
    
    # Test results
    test_result = Column(String(50))  # 'pass', 'fail', 'inconclusive', 'pending_review'
    comparison_result = Column(Boolean)  # Direct comparison: extracted_value == expected_value
    variance_details = Column(JSONB)  # Details of any variance found
    
    # LLM Analysis Results (matching current DocumentAnalysis model)
    llm_confidence_score = Column(Float)  # 0.0 to 1.0
    llm_analysis_rationale = Column(Text)  # LLM explanation
    llm_model_used = Column(String(100))  # e.g., 'gpt-4', 'claude-3'
    llm_tokens_used = Column(Integer)
    llm_response_raw = Column(JSONB)  # Raw LLM response
    llm_processing_time_ms = Column(Integer)
    
    # Database Test Results (for database evidence)
    database_query_executed = Column(Text)
    database_result_count = Column(Integer)
    database_execution_time_ms = Column(Integer)
    database_result_sample = Column(JSONB)  # Sample of query results
    
    # Execution status and timing
    execution_status = Column(String(50), default='pending')  # 'pending', 'running', 'completed', 'failed', 'cancelled'
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    processing_time_ms = Column(Integer)
    
    # Error handling
    error_message = Column(Text)
    error_details = Column(JSONB)
    retry_count = Column(Integer, default=0)
    
    # Comprehensive analysis results (unified storage)
    analysis_results = Column(JSONB, nullable=False)
    
    # Evidence context (from Request for Information phase)
    evidence_validation_status = Column(String(50))  # Status of evidence when test was executed
    evidence_version_number = Column(Integer)  # Version of evidence used
    
    # Test execution summary
    execution_summary = Column(Text)  # Human-readable summary
    processing_notes = Column(Text)  # Additional processing notes
    
    # Execution metadata
    executed_by = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    execution_method = Column(String(50), nullable=False)  # 'automatic', 'manual', 'scheduled'
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    updated_by = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    
    # Relationships
    phase = relationship("WorkflowPhase", foreign_keys=[phase_id])
    executor = relationship("User", foreign_keys=[executed_by])
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    
    # Related records
    reviews = relationship("TestExecutionReview", back_populates="execution", cascade="all, delete-orphan")
    audit_logs = relationship("TestExecutionAudit", back_populates="execution", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('test_case_id', 'execution_number', name='uq_test_execution_results_test_case_execution'),
        CheckConstraint("evidence_validation_status IN ('valid', 'approved')", name='ck_test_execution_evidence_approved'),
        Index('idx_test_execution_results_phase_id', 'phase_id'),
        Index('idx_test_execution_results_test_case_id', 'test_case_id'),
        Index('idx_test_execution_results_evidence_id', 'evidence_id'),
        Index('idx_test_execution_results_execution_status', 'execution_status'),
        Index('idx_test_execution_results_executed_by', 'executed_by'),
        Index('idx_test_execution_results_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<TestExecutionResult(id={self.id}, test_case_id={self.test_case_id}, execution_number={self.execution_number}, status={self.execution_status})>"
    
    # Properties to access cycle_id and report_id through phase
    @property
    def cycle_id(self):
        return self.phase.cycle_id if self.phase else None
    
    @property
    def report_id(self):
        return self.phase.report_id if self.phase else None


class TestExecutionReview(BaseModel):
    """
    Tester approval and review table for test execution results
    """
    __tablename__ = 'cycle_report_test_execution_reviews'
    
    id = Column(Integer, primary_key=True)
    execution_id = Column(Integer, ForeignKey('cycle_report_test_execution_results.id'), nullable=False)
    phase_id = Column(Integer, ForeignKey('workflow_phases.phase_id'), nullable=False)
    
    # Review details
    review_status = Column(String(50), nullable=False)  # 'approved', 'rejected', 'requires_revision'
    review_notes = Column(Text)
    reviewer_comments = Column(Text)
    recommended_action = Column(String(100))  # 'approve', 'retest', 'escalate', 'manual_review'
    
    # Quality assessment (matching current implementation)
    accuracy_score = Column(Float)  # 0.0 to 1.0
    completeness_score = Column(Float)  # 0.0 to 1.0
    consistency_score = Column(Float)  # 0.0 to 1.0
    overall_score = Column(Float)  # Calculated overall score
    
    # Review criteria
    review_criteria_used = Column(JSONB)
    
    # Follow-up actions
    requires_retest = Column(Boolean, default=False)
    retest_reason = Column(Text)
    escalation_required = Column(Boolean, default=False)
    escalation_reason = Column(Text)
    
    # Approval workflow
    reviewed_by = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    reviewed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    updated_by = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    
    # Relationships
    execution = relationship("TestExecution", back_populates="reviews")
    phase = relationship("WorkflowPhase")
    reviewer = relationship("User", foreign_keys=[reviewed_by], back_populates="test_execution_reviews")
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('execution_id', 'reviewed_by', name='uq_test_execution_reviews_execution_reviewer'),
        Index('idx_test_execution_reviews_execution_id', 'execution_id'),
        Index('idx_test_execution_reviews_phase_id', 'phase_id'),
        Index('idx_test_execution_reviews_status', 'review_status'),
        Index('idx_test_execution_reviews_reviewed_by', 'reviewed_by'),
    )
    
    def __repr__(self):
        return f"<TestExecutionReview(id={self.id}, execution_id={self.execution_id}, status={self.review_status})>"


class TestExecutionAudit(Base):
    """
    Audit trail table for test execution changes
    """
    __tablename__ = 'cycle_report_test_execution_audit'
    
    id = Column(Integer, primary_key=True)
    execution_id = Column(Integer, ForeignKey('cycle_report_test_execution_results.id'), nullable=False)
    action = Column(String(100), nullable=False)  # 'started', 'completed', 'failed', 'reviewed', 'approved', 'rejected'
    action_details = Column(JSONB)
    performed_by = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    performed_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Context information
    previous_status = Column(String(50))
    new_status = Column(String(50))
    change_reason = Column(Text)
    system_info = Column(JSONB)  # IP, user agent, etc.
    
    # Relationships
    execution = relationship("TestExecution", back_populates="audit_logs")
    performer = relationship("User", foreign_keys=[performed_by], back_populates="test_execution_audit_logs")
    
    # Constraints
    __table_args__ = (
        Index('idx_test_execution_audit_execution_id', 'execution_id'),
        Index('idx_test_execution_audit_performed_by', 'performed_by'),
        Index('idx_test_execution_audit_performed_at', 'performed_at'),
    )
    
    def __repr__(self):
        return f"<TestExecutionAudit(id={self.id}, execution_id={self.execution_id}, action={self.action})>"


# Update User model to include test execution relationships
def update_user_relationships():
    """Add test execution relationships to User model"""
    if not hasattr(User, 'executed_tests'):
        User.executed_tests = relationship("TestExecution", foreign_keys="TestExecution.executed_by", back_populates="executor")
    if not hasattr(User, 'test_execution_reviews'):
        User.test_execution_reviews = relationship("TestExecutionReview", foreign_keys="TestExecutionReview.reviewed_by", back_populates="reviewer")
    if not hasattr(User, 'test_execution_audit_logs'):
        User.test_execution_audit_logs = relationship("TestExecutionAudit", foreign_keys="TestExecutionAudit.performed_by", back_populates="performer")


# Update other model relationships
def update_model_relationships():
    """Add test execution relationships to other models"""
    if not hasattr(WorkflowPhase, 'test_execution_results'):
        WorkflowPhase.test_execution_results = relationship("TestExecution", back_populates="phase", overlaps="test_executions")
    # if not hasattr(TestCycle, 'test_execution_results'):
    #     TestCycle.test_execution_results = relationship("TestExecution", back_populates="cycle", overlaps="test_executions")  # Removed - no direct cycle_id in TestExecution
    # if not hasattr(Report, 'test_execution_results'):
    #     Report.test_execution_results = relationship("TestExecution", back_populates="report", overlaps="test_executions")  # Removed - no direct report_id in TestExecution


# Call the functions to update relationships
update_user_relationships()
update_model_relationships()