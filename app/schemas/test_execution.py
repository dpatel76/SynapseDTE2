"""
Test Execution Engine schemas
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


class TestType(str, Enum):
    """Test type enumeration"""
    DOCUMENT_BASED = "Document Based"
    DATABASE_BASED = "Database Based"
    HYBRID = "Hybrid"


class TestStatus(str, Enum):
    """Test execution status enumeration"""
    PENDING = "Pending"
    RUNNING = "Running"
    COMPLETED = "Completed"
    FAILED = "Failed"
    CANCELLED = "Cancelled"
    REQUIRES_REVIEW = "Requires Review"


class TestResult(str, Enum):
    """Test result enumeration"""
    PASS = "Pass"
    FAIL = "Fail"
    INCONCLUSIVE = "Inconclusive"
    PENDING_REVIEW = "Pending Review"


class AnalysisMethod(str, Enum):
    """Analysis method enumeration"""
    LLM_ANALYSIS = "LLM Analysis"
    DATABASE_QUERY = "Database Query"
    MANUAL_REVIEW = "Manual Review"
    AUTOMATED_COMPARISON = "Automated Comparison"


class ReviewStatus(str, Enum):
    """Review status enumeration"""
    PENDING = "Pending"
    IN_REVIEW = "In Review"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    REQUIRES_REVISION = "Requires Revision"


# Test Execution Phase Start
class TestExecutionPhaseStart(BaseModel):
    """Schema for starting testing execution phase"""
    planned_start_date: Optional[datetime] = Field(None, description="Planned start date")
    planned_end_date: Optional[datetime] = Field(None, description="Planned end date")
    testing_deadline: datetime = Field(..., description="Testing completion deadline")
    test_strategy: Optional[str] = Field(None, description="Testing strategy and approach")
    instructions: Optional[str] = Field(None, description="Special instructions for testers")
    notes: Optional[str] = Field(None, description="Testing phase notes")


# Document Analysis Schemas
class DocumentAnalysisRequest(BaseModel):
    """Schema for document analysis request"""
    submission_document_id: int = Field(..., description="Submission document ID")
    sample_record_id: str = Field(..., description="Sample record ID")
    attribute_id: int = Field(..., description="Attribute ID")
    analysis_prompt: Optional[str] = Field(None, description="Custom analysis prompt")
    expected_value: Optional[str] = Field(None, description="Expected value for comparison")
    confidence_threshold: float = Field(0.8, description="Confidence threshold for analysis")
    
    @validator('confidence_threshold')
    def validate_confidence(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("Confidence threshold must be between 0.0 and 1.0")
        return v


class DocumentAnalysisResponse(BaseModel):
    """Schema for document analysis response"""
    analysis_id: int = Field(..., description="Analysis ID")
    submission_document_id: int = Field(..., description="Submission document ID")
    sample_record_id: str = Field(..., description="Sample record ID")
    attribute_id: int = Field(..., description="Attribute ID")
    extracted_value: Optional[str] = Field(None, description="Extracted value from document")
    confidence_score: float = Field(..., description="Confidence score (0.0-1.0)")
    analysis_rationale: str = Field(..., description="LLM analysis explanation")
    matches_expected: Optional[bool] = Field(None, description="Whether extracted value matches expected")
    validation_notes: List[str] = Field(..., description="Validation messages")
    analyzed_at: datetime = Field(..., description="Analysis timestamp")
    analysis_duration_ms: int = Field(..., description="Analysis processing time")


# Database Testing Schemas
class DatabaseTestRequest(BaseModel):
    """Schema for database test request"""
    database_submission_id: str = Field(..., description="Database submission ID")
    sample_record_id: str = Field(..., description="Sample record ID")
    attribute_id: int = Field(..., description="Attribute ID")
    test_query: Optional[str] = Field(None, description="Custom test query")
    connection_timeout: int = Field(30, description="Connection timeout in seconds")
    query_timeout: int = Field(60, description="Query timeout in seconds")
    
    @validator('connection_timeout', 'query_timeout')
    def validate_timeouts(cls, v):
        if v <= 0 or v > 300:
            raise ValueError("Timeout must be between 1 and 300 seconds")
        return v


class DatabaseTestResponse(BaseModel):
    """Schema for database test response"""
    test_id: int = Field(..., description="Database test ID")
    database_submission_id: str = Field(..., description="Database submission ID")
    sample_record_id: str = Field(..., description="Sample record ID")
    attribute_id: int = Field(..., description="Attribute ID")
    connection_successful: bool = Field(..., description="Database connection success")
    query_successful: bool = Field(..., description="Query execution success")
    retrieved_value: Optional[str] = Field(None, description="Retrieved value from database")
    record_count: Optional[int] = Field(None, description="Number of records returned")
    execution_time_ms: int = Field(..., description="Query execution time")
    error_message: Optional[str] = Field(None, description="Error message if any")
    tested_at: datetime = Field(..., description="Test execution timestamp")


# Test Execution Schemas
class TestExecutionRequest(BaseModel):
    """Schema for test execution request"""
    sample_record_id: str = Field(..., description="Sample record ID")
    attribute_id: int = Field(..., description="Attribute ID")
    test_type: TestType = Field(..., description="Type of test to execute")
    analysis_method: AnalysisMethod = Field(..., description="Analysis method to use")
    priority: str = Field("Normal", description="Test priority (High/Normal/Low)")
    custom_instructions: Optional[str] = Field(None, description="Custom test instructions")
    document_analysis_id: Optional[int] = Field(None, description="Document analysis ID for document-based tests")
    database_test_id: Optional[str] = Field(None, description="Database test ID for database-based tests")
    
    @validator('priority')
    def validate_priority(cls, v):
        if v not in ['High', 'Normal', 'Low']:
            raise ValueError("Priority must be High, Normal, or Low")
        return v


class TestExecutionResponse(BaseModel):
    """Schema for test execution response"""
    execution_id: int = Field(..., description="Test execution ID")
    phase_id: str = Field(..., description="Testing execution phase ID")
    sample_record_id: str = Field(..., description="Sample record ID")
    attribute_id: int = Field(..., description="Attribute ID")
    test_type: TestType = Field(..., description="Test type")
    status: TestStatus = Field(..., description="Execution status")
    result: Optional[TestResult] = Field(None, description="Test result")
    confidence_score: Optional[float] = Field(None, description="Result confidence score")
    execution_summary: Optional[str] = Field(None, description="Execution summary")
    error_message: Optional[str] = Field(None, description="Error message if any")
    started_at: datetime = Field(..., description="Execution start time")
    completed_at: Optional[datetime] = Field(None, description="Execution completion time")
    processing_time_ms: Optional[int] = Field(None, description="Total processing time")


# Bulk Test Execution
class BulkTestExecutionRequest(BaseModel):
    """Schema for bulk test execution request"""
    test_requests: List[TestExecutionRequest] = Field(..., description="List of test requests")
    execution_mode: str = Field("Parallel", description="Execution mode (Parallel/Sequential)")
    max_concurrent_tests: int = Field(5, description="Maximum concurrent tests")
    
    @validator('test_requests')
    def validate_test_requests(cls, v):
        if not v:
            raise ValueError("At least one test request is required")
        if len(v) > 100:
            raise ValueError("Maximum 100 tests per bulk request")
        return v
    
    @validator('execution_mode')
    def validate_execution_mode(cls, v):
        if v not in ['Parallel', 'Sequential']:
            raise ValueError("Execution mode must be Parallel or Sequential")
        return v


class BulkTestExecutionResponse(BaseModel):
    """Schema for bulk test execution response"""
    bulk_execution_id: int = Field(..., description="Bulk execution ID")
    phase_id: str = Field(..., description="Testing execution phase ID")
    total_tests: int = Field(..., description="Total tests submitted")
    tests_started: int = Field(..., description="Tests started")
    tests_completed: int = Field(..., description="Tests completed")
    tests_failed: int = Field(..., description="Tests failed")
    execution_ids: List[int] = Field(..., description="Individual execution IDs")
    status: str = Field(..., description="Bulk execution status")
    started_at: datetime = Field(..., description="Bulk execution start time")
    completed_at: Optional[datetime] = Field(None, description="Bulk execution completion time")
    processing_time_ms: int = Field(..., description="Total processing time")


# Test Result Review
class TestResultReviewRequest(BaseModel):
    """Schema for test result review request"""
    execution_id: int = Field(..., description="Test execution ID")
    review_result: ReviewStatus = Field(..., description="Review result")
    reviewer_comments: str = Field(..., description="Reviewer comments")
    recommended_action: Optional[str] = Field(None, description="Recommended action")
    requires_retest: bool = Field(False, description="Whether retest is required")
    
    @validator('reviewer_comments')
    def validate_comments(cls, v):
        if not v.strip():
            raise ValueError("Reviewer comments are required")
        return v.strip()


class TestResultReviewResponse(BaseModel):
    """Schema for test result review response"""
    review_id: int = Field(..., description="Review ID")
    execution_id: int = Field(..., description="Test execution ID")
    reviewer_id: int = Field(..., description="Reviewer user ID")
    review_result: ReviewStatus = Field(..., description="Review result")
    reviewer_comments: str = Field(..., description="Reviewer comments")
    recommended_action: Optional[str] = Field(None, description="Recommended action")
    requires_retest: bool = Field(..., description="Whether retest is required")
    overall_score: Optional[float] = Field(None, description="Overall review score")
    reviewed_at: datetime = Field(..., description="Review timestamp")
    review_duration_ms: Optional[int] = Field(None, description="Review duration in milliseconds")


# Test Comparison
class TestComparisonRequest(BaseModel):
    """Schema for test comparison request"""
    execution_ids: List[int] = Field(..., description="Execution IDs to compare")
    comparison_criteria: List[str] = Field(..., description="Criteria for comparison")
    include_analysis_details: bool = Field(True, description="Include detailed analysis")
    
    @validator('execution_ids')
    def validate_execution_ids(cls, v):
        if len(v) < 2:
            raise ValueError("At least 2 executions required for comparison")
        if len(v) > 10:
            raise ValueError("Maximum 10 executions per comparison")
        return v


class TestComparisonResponse(BaseModel):
    """Schema for test comparison response"""
    comparison_id: int = Field(..., description="Comparison ID")
    execution_ids: List[int] = Field(..., description="Compared execution IDs")
    consistency_score: float = Field(..., description="Consistency score across executions")
    comparison_results: Dict[str, Any] = Field(..., description="Comparison results")
    differences_found: List[str] = Field(..., description="Differences identified")
    recommendations: List[str] = Field(..., description="Recommendations based on comparison")
    compared_at: datetime = Field(..., description="Comparison timestamp")
    comparison_duration_ms: int = Field(..., description="Comparison processing time in milliseconds")


# Phase Status and Progress
class TestExecutionPhaseStatus(BaseModel):
    """Schema for testing execution phase status"""
    cycle_id: int = Field(..., description="Cycle ID")
    report_id: int = Field(..., description="Report ID")
    phase_status: str = Field(..., description="Phase status")
    testing_deadline: datetime = Field(..., description="Testing deadline")
    days_until_deadline: int = Field(..., description="Days until deadline")
    total_samples: int = Field(..., description="Total sample records")
    total_tests: int = Field(..., description="Total tests to execute")
    tests_completed: int = Field(..., description="Tests completed")
    tests_pending: int = Field(..., description="Tests pending")
    tests_failed: int = Field(..., description="Tests failed")
    tests_under_review: int = Field(..., description="Tests under review")
    completion_percentage: float = Field(..., description="Overall completion percentage")
    average_confidence_score: float = Field(..., description="Average confidence score")
    test_results_summary: Dict[str, int] = Field(..., description="Test results breakdown")
    can_complete_phase: bool = Field(..., description="Can complete testing phase")
    completion_requirements: List[str] = Field(..., description="Requirements to complete phase")


# Analytics and Insights
class TestingAnalytics(BaseModel):
    """Schema for testing analytics"""
    cycle_id: int = Field(..., description="Cycle ID")
    report_id: int = Field(..., description="Report ID")
    phase_id: str = Field(..., description="Testing execution phase ID")
    total_tests: int = Field(..., description="Total tests executed")
    document_based_tests: int = Field(..., description="Document-based tests")
    database_based_tests: int = Field(..., description="Database-based tests")
    completed_tests: int = Field(..., description="Completed tests")
    failed_tests: int = Field(..., description="Failed tests")
    success_rate: float = Field(..., description="Success rate percentage")
    average_confidence_score: float = Field(..., description="Average confidence score")
    average_processing_time_ms: float = Field(..., description="Average processing time")
    test_results_distribution: Dict[str, int] = Field(..., description="Test result distribution")
    test_type_performance: Dict[str, Dict[str, float]] = Field(..., description="Performance by test type")
    daily_execution_trends: List[Dict[str, Any]] = Field(..., description="Daily execution trends")
    phase_duration_days: int = Field(..., description="Phase duration in days")


# Phase Completion
class TestExecutionPhaseComplete(BaseModel):
    """Schema for completing testing execution phase"""
    completion_notes: Optional[str] = Field(None, description="Completion notes")
    confirm_completion: bool = Field(..., description="Confirm completion")
    override_validation: bool = Field(False, description="Override validation requirements")
    override_reason: Optional[str] = Field(None, description="Reason for override")
    final_summary: Optional[str] = Field(None, description="Final testing summary")
    
    @validator('override_reason')
    def validate_override_reason(cls, v, values):
        if values.get('override_validation') and not v:
            raise ValueError("Override reason required when overriding validation")
        return v


# Audit Log Schema
class TestExecutionAuditLog(BaseModel):
    """Schema for testing execution audit log"""
    log_id: int = Field(..., description="Log ID")
    cycle_id: int = Field(..., description="Cycle ID")
    report_id: int = Field(..., description="Report ID")
    phase_id: Optional[str] = Field(None, description="Testing execution phase ID")
    action: str = Field(..., description="Action performed")
    entity_type: str = Field(..., description="Entity type affected")
    entity_id: Optional[str] = Field(None, description="Entity ID")
    performed_by: int = Field(..., description="User who performed action")
    performed_at: datetime = Field(..., description="When action was performed")
    old_values: Optional[Dict[str, Any]] = Field(None, description="Previous values")
    new_values: Optional[Dict[str, Any]] = Field(None, description="New values")
    notes: Optional[str] = Field(None, description="Additional notes")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent")
    execution_time_ms: Optional[int] = Field(None, description="Execution time in milliseconds") 