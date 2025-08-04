"""
Unified Test Execution Schemas
Pydantic models for test execution API requests and responses
"""

from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field, validator
from enum import Enum


class TestType(str, Enum):
    """Test execution type"""
    DOCUMENT_ANALYSIS = "document_analysis"
    DATABASE_TEST = "database_test"
    MANUAL_TEST = "manual_test"
    HYBRID = "hybrid"


class AnalysisMethod(str, Enum):
    """Analysis method for test execution"""
    LLM_ANALYSIS = "llm_analysis"
    DATABASE_QUERY = "database_query"
    MANUAL_REVIEW = "manual_review"


class ExecutionStatus(str, Enum):
    """Test execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TestResult(str, Enum):
    """Test result status"""
    PASS = "pass"
    FAIL = "fail"
    INCONCLUSIVE = "inconclusive"
    PENDING_REVIEW = "pending_review"


class ExecutionReason(str, Enum):
    """Reason for test execution"""
    INITIAL = "initial"
    RETRY = "retry"
    EVIDENCE_UPDATED = "evidence_updated"
    MANUAL_RERUN = "manual_rerun"


class ExecutionMethod(str, Enum):
    """Test execution method"""
    AUTOMATIC = "automatic"
    MANUAL = "manual"
    SCHEDULED = "scheduled"


class ReviewStatus(str, Enum):
    """Review status for test execution"""
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUIRES_REVISION = "requires_revision"


class RecommendedAction(str, Enum):
    """Recommended action after review"""
    APPROVE = "approve"
    RETEST = "retest"
    ESCALATE = "escalate"
    MANUAL_REVIEW = "manual_review"


# Request Schemas
class TestExecutionCreateRequest(BaseModel):
    """Request to create a new test execution"""
    test_case_id: str = Field(..., description="Test case identifier")
    evidence_id: int = Field(..., description="Evidence ID from Request for Information phase")
    execution_reason: Optional[ExecutionReason] = Field(ExecutionReason.INITIAL, description="Reason for execution")
    test_type: TestType = Field(..., description="Type of test execution")
    analysis_method: AnalysisMethod = Field(..., description="Analysis method to use")
    execution_method: ExecutionMethod = Field(ExecutionMethod.AUTOMATIC, description="Execution method")
    configuration: Optional[Dict[str, Any]] = Field(None, description="Additional configuration")
    processing_notes: Optional[str] = Field(None, description="Processing notes")


class TestExecutionUpdateRequest(BaseModel):
    """Request to update test execution"""
    execution_summary: Optional[str] = Field(None, description="Execution summary")
    processing_notes: Optional[str] = Field(None, description="Processing notes")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    error_details: Optional[Dict[str, Any]] = Field(None, description="Error details")


class TestExecutionReviewRequest(BaseModel):
    """Request to review test execution results"""
    review_status: ReviewStatus = Field(..., description="Review status")
    review_notes: Optional[str] = Field(None, description="Review notes")
    reviewer_comments: Optional[str] = Field(None, description="Reviewer comments")
    recommended_action: Optional[RecommendedAction] = Field(None, description="Recommended action")
    accuracy_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Accuracy score")
    completeness_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Completeness score")
    consistency_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Consistency score")
    requires_retest: Optional[bool] = Field(False, description="Whether retest is required")
    retest_reason: Optional[str] = Field(None, description="Reason for retest")
    escalation_required: Optional[bool] = Field(False, description="Whether escalation is required")
    escalation_reason: Optional[str] = Field(None, description="Reason for escalation")


class BulkTestExecutionRequest(BaseModel):
    """Request to execute multiple test cases"""
    test_case_ids: List[str] = Field(..., description="List of test case IDs")
    execution_reason: Optional[ExecutionReason] = Field(ExecutionReason.INITIAL, description="Reason for execution")
    execution_method: ExecutionMethod = Field(ExecutionMethod.AUTOMATIC, description="Execution method")
    configuration: Optional[Dict[str, Any]] = Field(None, description="Additional configuration")


class BulkReviewRequest(BaseModel):
    """Request to review multiple test executions"""
    execution_ids: List[int] = Field(..., description="List of execution IDs")
    review_status: ReviewStatus = Field(..., description="Review status")
    review_notes: Optional[str] = Field(None, description="Review notes")
    reviewer_comments: Optional[str] = Field(None, description="Reviewer comments")
    recommended_action: Optional[RecommendedAction] = Field(None, description="Recommended action")


# Response Schemas
class TestExecutionResponse(BaseModel):
    """Response for test execution"""
    id: int
    phase_id: int
    cycle_id: int
    report_id: int
    test_case_id: str
    evidence_id: int
    
    # Execution versioning
    execution_number: int
    is_latest_execution: bool
    execution_reason: Optional[str]
    
    # Test execution configuration
    test_type: str
    analysis_method: str
    
    # Core test data
    sample_value: Optional[str]
    extracted_value: Optional[str]
    expected_value: Optional[str]
    
    # Test results
    test_result: Optional[str]
    comparison_result: Optional[bool]
    variance_details: Optional[Dict[str, Any]]
    
    # LLM Analysis Results
    llm_confidence_score: Optional[float]
    llm_analysis_rationale: Optional[str]
    llm_model_used: Optional[str]
    llm_tokens_used: Optional[int]
    llm_processing_time_ms: Optional[int]
    
    # Database Test Results
    database_query_executed: Optional[str]
    database_result_count: Optional[int]
    database_execution_time_ms: Optional[int]
    database_result_sample: Optional[Dict[str, Any]]
    
    # Execution status and timing
    execution_status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    processing_time_ms: Optional[int]
    
    # Error handling
    error_message: Optional[str]
    error_details: Optional[Dict[str, Any]]
    retry_count: int
    
    # Comprehensive analysis results
    analysis_results: Dict[str, Any]
    
    # Evidence context
    evidence_validation_status: Optional[str]
    evidence_version_number: Optional[int]
    
    # Test execution summary
    execution_summary: Optional[str]
    processing_notes: Optional[str]
    
    # Execution metadata
    executed_by: int
    execution_method: str
    
    # Audit fields
    created_at: datetime
    updated_at: datetime
    created_by: int
    updated_by: int
    
    class Config:
        from_attributes = True


class TestExecutionReviewResponse(BaseModel):
    """Response for test execution review"""
    id: int
    execution_id: int
    phase_id: int
    
    # Review details
    review_status: str
    review_notes: Optional[str]
    reviewer_comments: Optional[str]
    recommended_action: Optional[str]
    
    # Quality assessment
    accuracy_score: Optional[float]
    completeness_score: Optional[float]
    consistency_score: Optional[float]
    overall_score: Optional[float]
    
    # Review criteria
    review_criteria_used: Optional[Dict[str, Any]]
    
    # Follow-up actions
    requires_retest: bool
    retest_reason: Optional[str]
    escalation_required: bool
    escalation_reason: Optional[str]
    
    # Approval workflow
    reviewed_by: int
    reviewed_at: datetime
    
    # Audit fields
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TestExecutionAuditResponse(BaseModel):
    """Response for test execution audit log"""
    id: int
    execution_id: int
    action: str
    action_details: Optional[Dict[str, Any]]
    performed_by: int
    performed_at: datetime
    
    # Context information
    previous_status: Optional[str]
    new_status: Optional[str]
    change_reason: Optional[str]
    system_info: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True


class TestExecutionListResponse(BaseModel):
    """Response for test execution list"""
    executions: List[TestExecutionResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class TestExecutionReviewListResponse(BaseModel):
    """Response for test execution review list"""
    reviews: List[TestExecutionReviewResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class TestExecutionSummaryResponse(BaseModel):
    """Response for test execution summary"""
    total_executions: int
    completed_executions: int
    failed_executions: int
    pending_executions: int
    pending_reviews: int
    approved_reviews: int
    rejected_reviews: int
    completion_percentage: float
    average_processing_time_ms: Optional[int]
    success_rate: float


class TestExecutionDashboardResponse(BaseModel):
    """Response for test execution dashboard"""
    phase_id: int
    cycle_id: int
    report_id: int
    
    # Summary statistics
    summary: TestExecutionSummaryResponse
    
    # Recent executions
    recent_executions: List[TestExecutionResponse]
    
    # Pending reviews
    pending_reviews: List[TestExecutionResponse]
    
    # Quality metrics
    quality_metrics: Dict[str, Any]
    
    # Performance metrics
    performance_metrics: Dict[str, Any]


class BulkTestExecutionResponse(BaseModel):
    """Response for bulk test execution"""
    total_requested: int
    successful_executions: int
    failed_executions: int
    execution_ids: List[int]
    errors: List[Dict[str, Any]]
    job_id: Optional[str]  # For background processing


class BulkReviewResponse(BaseModel):
    """Response for bulk review"""
    total_requested: int
    successful_reviews: int
    failed_reviews: int
    review_ids: List[int]
    errors: List[Dict[str, Any]]


class TestExecutionCompletionStatusResponse(BaseModel):
    """Response for test execution completion status"""
    can_complete: bool
    completion_requirements: List[str]
    blocking_issues: List[str]
    total_test_cases: int
    completed_test_cases: int
    approved_test_cases: int
    completion_percentage: float


class TestExecutionConfigurationResponse(BaseModel):
    """Response for test execution configuration"""
    available_test_types: List[str]
    available_analysis_methods: List[str]
    available_execution_methods: List[str]
    default_configuration: Dict[str, Any]
    quality_criteria: Dict[str, Any]