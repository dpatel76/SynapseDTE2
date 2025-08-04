"""
Sample Selection phase schemas
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum
import json


class SampleGenerationMethod(str, Enum):
    """Sample generation method enumeration"""
    LLM_GENERATED = "LLM Generated"
    MANUAL_UPLOAD = "Manual Upload"
    HYBRID = "Hybrid"


class SampleStatus(str, Enum):
    """Sample status enumeration"""
    DRAFT = "Draft"
    PENDING_APPROVAL = "Pending Approval"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    REVISION_REQUIRED = "Revision Required"


class SampleValidationStatus(str, Enum):
    """Sample validation status enumeration"""
    VALID = "Valid"
    INVALID = "Invalid"
    WARNING = "Warning"
    NEEDS_REVIEW = "Needs Review"


class SampleType(str, Enum):
    """Sample type enumeration"""
    POPULATION_SAMPLE = "Population Sample"
    TARGETED_SAMPLE = "Targeted Sample"
    EXCEPTION_SAMPLE = "Exception Sample"
    CONTROL_SAMPLE = "Control Sample"


# Sample Selection Phase Management
class SampleSelectionPhaseStart(BaseModel):
    """Schema for starting sample selection phase"""
    planned_start_date: Optional[datetime] = Field(None, description="Planned start date")
    planned_end_date: Optional[datetime] = Field(None, description="Planned end date")
    target_sample_size: Optional[int] = Field(None, description="Target sample size")
    sampling_methodology: Optional[str] = Field(None, description="Sampling methodology notes")
    notes: Optional[str] = Field(None, description="Sample selection phase notes")


# LLM Sample Generation
class LLMSampleGenerationRequest(BaseModel):
    """Schema for LLM sample generation request"""
    sample_size: int = Field(..., ge=1, le=10000, description="Number of samples to generate")
    sample_type: SampleType = Field(..., description="Type of sample to generate")
    regulation_context: Optional[str] = Field(None, description="Regulatory framework context for sample generation")
    scoped_attributes: Optional[List[Dict[str, Any]]] = Field(None, description="Scoped attributes for sample generation")
    selection_criteria: Optional[Dict[str, Any]] = Field(None, description="Sample selection criteria")
    risk_focus_areas: Optional[List[str]] = Field(None, description="Risk areas to focus on")
    exclude_criteria: Optional[Dict[str, Any]] = Field(None, description="Exclusion criteria")
    include_edge_cases: bool = Field(default=True, description="Include edge cases in sampling")
    randomization_seed: Optional[int] = Field(None, description="Seed for reproducible sampling")
    regenerate_existing_set_id: Optional[str] = Field(None, description="Set ID to regenerate (for updating existing Draft/Rejected/Revision Required samples)")


class LLMSampleGenerationResponse(BaseModel):
    """Schema for LLM sample generation response"""
    generation_id: str = Field(..., description="Unique generation ID")
    samples_generated: int = Field(..., description="Number of samples generated")
    generation_rationale: str = Field(..., description="LLM rationale for sample selection")
    selection_criteria_used: Dict[str, Any] = Field(..., description="Actual criteria used")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in sample quality")
    risk_coverage: Dict[str, float] = Field(..., description="Risk area coverage percentages")
    sample_preview: List[Dict[str, Any]] = Field(..., description="Preview of first 5 samples")
    estimated_testing_time: Optional[int] = Field(None, description="Estimated testing time in minutes")


# Manual Sample Upload
class ManualSampleUpload(BaseModel):
    """Schema for manual sample upload"""
    upload_method: str = Field(..., description="Upload method (CSV, Excel, JSON)")
    sample_data: Union[str, List[Dict[str, Any]]] = Field(..., description="Sample data or file content")
    primary_key_column: str = Field(..., description="Primary key column name")
    data_mapping: Optional[Dict[str, str]] = Field(None, description="Column mapping")
    validate_on_upload: bool = Field(default=True, description="Validate data on upload")
    notes: Optional[str] = Field(None, description="Upload notes")

    @validator('sample_data')
    def validate_sample_data(cls, v):
        if isinstance(v, str):
            try:
                # Try to parse as JSON if it's a string
                json.loads(v)
            except json.JSONDecodeError:
                raise ValueError("Sample data must be valid JSON string or list of dictionaries")
        return v


class SampleUploadResponse(BaseModel):
    """Schema for sample upload response"""
    upload_id: str = Field(..., description="Unique upload ID")
    samples_uploaded: int = Field(..., description="Number of samples uploaded")
    validation_results: Dict[str, Any] = Field(..., description="Validation results")
    data_quality_score: float = Field(..., ge=0.0, le=1.0, description="Data quality score")
    issues_found: List[Dict[str, Any]] = Field(..., description="Issues found during validation")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")


# Sample Validation
class SampleValidationRule(BaseModel):
    """Schema for sample validation rule"""
    rule_name: str = Field(..., description="Validation rule name")
    rule_type: str = Field(..., description="Rule type (required, format, range, etc.)")
    field_name: str = Field(..., description="Field to validate")
    validation_criteria: Dict[str, Any] = Field(..., description="Validation criteria")
    severity: str = Field(default="Error", description="Error severity (Error, Warning)")


class SampleValidationRequest(BaseModel):
    """Schema for sample validation request"""
    validation_rules: List[SampleValidationRule] = Field(..., description="Validation rules to apply")
    validate_completeness: bool = Field(default=True, description="Check data completeness")
    validate_consistency: bool = Field(default=True, description="Check data consistency")
    validate_business_rules: bool = Field(default=True, description="Check business rules")


class SampleValidationResult(BaseModel):
    """Schema for individual sample validation result"""
    sample_id: str = Field(..., description="Sample identifier")
    validation_status: SampleValidationStatus = Field(..., description="Validation status")
    validation_score: float = Field(..., ge=0.0, le=1.0, description="Validation score")
    issues: List[Dict[str, Any]] = Field(..., description="Validation issues")
    warnings: List[Dict[str, Any]] = Field(..., description="Validation warnings")


class SampleValidationSummary(BaseModel):
    """Schema for sample validation summary"""
    total_samples: int = Field(..., description="Total samples validated")
    valid_samples: int = Field(..., description="Number of valid samples")
    invalid_samples: int = Field(..., description="Number of invalid samples")
    warning_samples: int = Field(..., description="Number of samples with warnings")
    overall_quality_score: float = Field(..., ge=0.0, le=1.0, description="Overall quality score")
    validation_results: List[SampleValidationResult] = Field(..., description="Individual results")
    recommendations: List[str] = Field(..., description="Improvement recommendations")


# Sample Data Management
class SampleRecord(BaseModel):
    """Schema for individual sample record"""
    sample_id: str = Field(..., description="Unique sample identifier")
    primary_key_value: str = Field(..., description="Primary key value")
    sample_data: Dict[str, Any] = Field(..., description="Sample data fields")
    generation_method: SampleGenerationMethod = Field(..., description="How sample was generated")
    sample_type: SampleType = Field(..., description="Type of sample")
    risk_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Risk score")
    validation_status: SampleValidationStatus = Field(..., description="Validation status")
    lob_assignments: Optional[List[str]] = Field(None, description="LOB assignments for this sample")
    sample_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional sample metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    created_by: int = Field(..., description="User who created the sample")


class SampleSet(BaseModel):
    """Schema for complete sample set"""
    set_id: str = Field(..., description="Unique sample set identifier")
    cycle_id: int = Field(..., description="Test cycle ID")
    report_id: int = Field(..., description="Report ID")
    set_name: str = Field(..., description="Sample set name")
    description: Optional[str] = Field(None, description="Sample set description")
    total_samples: int = Field(..., description="Total number of samples")
    generation_method: SampleGenerationMethod = Field(..., description="Primary generation method")
    status: SampleStatus = Field(..., description="Sample set status")
    samples: List[SampleRecord] = Field(..., description="Individual samples")
    metadata: Dict[str, Any] = Field(..., description="Sample set metadata")


# Report Owner Approval
class SampleApprovalRequest(BaseModel):
    """Schema for sample approval request"""
    approval_decision: str = Field(..., description="Approval decision (Approve/Reject/Request Changes)")
    feedback: Optional[str] = Field(None, description="Approval feedback")
    requested_changes: Optional[List[str]] = Field(None, description="Specific changes requested")
    conditional_approval: bool = Field(default=False, description="Conditional approval flag")
    approval_conditions: Optional[List[str]] = Field(None, description="Conditions for approval")


class SampleApprovalResponse(BaseModel):
    """Schema for sample approval response"""
    approval_id: str = Field(..., description="Unique approval ID")
    approved: bool = Field(..., description="Whether samples were approved")
    approval_timestamp: datetime = Field(..., description="Approval timestamp")
    approved_by: int = Field(..., description="User who provided approval")
    approval_notes: Optional[str] = Field(None, description="Approval notes")
    next_steps: List[str] = Field(..., description="Next steps after approval")


# Sample Selection Status and Progress
class SampleSelectionStatus(BaseModel):
    """Schema for sample selection phase status"""
    cycle_id: int = Field(..., description="Cycle ID")
    report_id: int = Field(..., description="Report ID")
    phase_status: str = Field(..., description="Phase status")
    total_sample_sets: int = Field(..., description="Total sample sets")
    approved_sample_sets: int = Field(..., description="Approved sample sets")
    pending_approval_sets: int = Field(..., description="Sets pending approval")
    rejected_sample_sets: int = Field(..., description="Rejected sample sets")
    total_samples: int = Field(..., description="Total individual samples")
    sample_quality_score: float = Field(..., ge=0.0, le=1.0, description="Overall sample quality")
    can_proceed_to_testing: bool = Field(..., description="Can proceed to testing phase")
    completion_requirements: List[str] = Field(..., description="Requirements to complete phase")


# Sample Analytics and Insights
class SampleAnalytics(BaseModel):
    """Schema for sample analytics"""
    cycle_id: int = Field(..., description="Cycle ID")
    report_id: int = Field(..., description="Report ID")
    generation_method_breakdown: Dict[str, int] = Field(..., description="Breakdown by generation method")
    sample_type_distribution: Dict[str, int] = Field(..., description="Distribution by sample type")
    risk_coverage_analysis: Dict[str, float] = Field(..., description="Risk area coverage")
    data_quality_trends: List[Dict[str, Any]] = Field(..., description="Quality trends over time")
    validation_issue_patterns: List[Dict[str, Any]] = Field(..., description="Common validation issues")
    recommendations: List[str] = Field(..., description="Analytics-based recommendations")


# Phase Completion
class SampleSelectionPhaseComplete(BaseModel):
    """Schema for completing sample selection phase"""
    completion_notes: Optional[str] = Field(None, description="Completion notes")
    final_sample_count: int = Field(..., description="Final approved sample count")
    quality_assurance_complete: bool = Field(..., description="QA process complete")
    confirm_completion: bool = Field(..., description="Confirm completion")


# Sample Audit and Versioning
class SampleAuditEntry(BaseModel):
    """Schema for sample audit entry"""
    audit_id: str = Field(..., description="Audit entry ID")
    sample_set_id: str = Field(..., description="Sample set ID")
    action: str = Field(..., description="Action performed")
    performed_by: int = Field(..., description="User who performed action")
    performed_at: datetime = Field(..., description="Action timestamp")
    changes_made: Optional[Dict[str, Any]] = Field(None, description="Changes made")
    notes: Optional[str] = Field(None, description="Audit notes")


class SampleVersionInfo(BaseModel):
    """Schema for sample version information"""
    version_id: str = Field(..., description="Version ID")
    version_number: int = Field(..., description="Version number")
    created_at: datetime = Field(..., description="Version creation time")
    created_by: int = Field(..., description="User who created version")
    changes_summary: str = Field(..., description="Summary of changes")
    sample_count: int = Field(..., description="Number of samples in version")


class ReportOwnerReviewRequest(BaseModel):
    """Request for report owner review submission"""
    decision: Literal["approved", "rejected", "revision_required"]
    feedback: Optional[str] = None
    sample_decisions: Optional[Dict[str, Dict[str, Any]]] = None
    assignment_id: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "decision": "approved",
                "feedback": "All samples reviewed and approved",
                "sample_decisions": {
                    "sample-id-1": {
                        "decision": "approved",
                        "notes": "Good sample"
                    }
                },
                "assignment_id": "assignment-id"
            }
        }
    is_active: bool = Field(..., description="Is active version") 