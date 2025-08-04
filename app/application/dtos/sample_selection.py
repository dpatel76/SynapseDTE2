"""
Sample Selection DTOs for clean architecture
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class SampleTypeEnum(str, Enum):
    """Types of samples"""
    RANDOM = "Random"
    STRATIFIED = "Stratified"
    JUDGMENTAL = "Judgmental"
    SYSTEMATIC = "Systematic"
    TARGETED = "Targeted"


class SampleStatusEnum(str, Enum):
    """Status of samples"""
    DRAFT = "Draft"
    SELECTED = "Selected"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    IN_USE = "In Use"


class SelectionMethodEnum(str, Enum):
    """Sample selection methods"""
    RANDOM = "Random"
    SYSTEMATIC = "Systematic"
    RISK_BASED = "Risk-Based"
    STATISTICAL = "Statistical"
    MANUAL = "Manual"


class SampleSelectionPhaseStartDTO(BaseModel):
    """DTO for starting sample selection phase"""
    phase_notes: Optional[str] = None
    default_sample_size: Optional[int] = None
    selection_criteria: Optional[Dict[str, Any]] = None


class SampleSelectionVersionCreateDTO(BaseModel):
    """DTO for creating sample set"""
    attribute_id: int
    sample_type: SampleTypeEnum
    selection_method: SelectionMethodEnum
    target_sample_size: int
    selection_criteria: Optional[Dict[str, Any]] = None
    risk_factors: Optional[List[str]] = None
    notes: Optional[str] = None


class SampleSelectionSampleCreateDTO(BaseModel):
    """DTO for creating sample record"""
    sample_identifier: str
    primary_key_values: Dict[str, Any]
    risk_score: Optional[float] = None
    selection_reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SampleSelectionVersionResponseDTO(BaseModel):
    """DTO for sample set response"""
    sample_set_id: str
    phase_id: str
    cycle_id: int
    report_id: int
    attribute_id: int
    attribute_name: str
    sample_type: SampleTypeEnum
    selection_method: SelectionMethodEnum
    target_sample_size: int
    actual_sample_size: int
    status: SampleStatusEnum
    selection_criteria: Optional[Dict[str, Any]]
    risk_factors: Optional[List[str]]
    notes: Optional[str]
    created_by: int
    created_at: datetime
    approved_by: Optional[int]
    approved_at: Optional[datetime]
    rejection_reason: Optional[str]


class SampleSelectionSampleResponseDTO(BaseModel):
    """DTO for sample record response"""
    sample_id: str
    sample_set_id: str
    sample_identifier: str
    primary_key_values: Dict[str, Any]
    risk_score: Optional[float]
    selection_reason: Optional[str]
    metadata: Optional[Dict[str, Any]]
    is_selected: bool
    created_at: datetime


class SampleSelectionVersionWithSamplesDTO(SampleSelectionVersionResponseDTO):
    """DTO for sample set with records"""
    sample_records: List[SampleSelectionSampleResponseDTO]


class SampleSelectionPhaseStatusDTO(BaseModel):
    """DTO for sample selection phase status"""
    phase_id: str
    cycle_id: int
    report_id: int
    phase_status: str
    total_attributes: int
    attributes_with_samples: int
    total_sample_sets: int
    approved_sample_sets: int
    pending_approval: int
    total_samples_selected: int
    can_complete: bool
    completion_requirements: List[str]


class SampleApprovalRequestDTO(BaseModel):
    """DTO for sample approval request"""
    action: str = Field(..., pattern="^(approve|reject)$")
    review_notes: Optional[str] = None
    rejection_reason: Optional[str] = None


class SampleStatisticsDTO(BaseModel):
    """DTO for sample statistics"""
    total_population: int
    sample_size: int
    coverage_percentage: float
    confidence_level: Optional[float]
    margin_of_error: Optional[float]
    risk_coverage: Optional[Dict[str, float]]


class AutoSampleSelectionRequestDTO(BaseModel):
    """DTO for auto sample selection"""
    attributes: List[int]
    default_sample_size: int = 30
    selection_method: SelectionMethodEnum = SelectionMethodEnum.RANDOM
    apply_risk_factors: bool = True
    confidence_level: float = 0.95


class BulkSampleApprovalRequestDTO(BaseModel):
    """DTO for bulk sample approval"""
    sample_set_ids: List[str]
    action: str = Field(..., pattern="^(approve|reject)$")
    review_notes: Optional[str] = None


class SampleSelectionSummaryDTO(BaseModel):
    """DTO for sample selection summary"""
    attribute_id: int
    attribute_name: str
    total_population: int
    sample_sets_count: int
    total_samples: int
    coverage_percentage: float
    status: str
    last_updated: datetime


class PhaseCompletionRequestDTO(BaseModel):
    """DTO for phase completion request"""
    completion_notes: Optional[str] = None
    override_checks: bool = False

# Missing DTOs for compatibility
"""Missing DTOs for sample selection use cases"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from datetime import datetime


@dataclass
class SampleSelectionGenerationRequestDTO:
    """Request DTO for generating sample selection"""
    cycle_id: int
    report_id: int
    user_id: int
    use_llm: bool = True
    sample_count: Optional[int] = None
    sampling_criteria: Optional[Dict[str, Any]] = None


@dataclass
class SampleSelectionApprovalRequestDTO:
    """Request DTO for approving sample selection"""
    sample_set_id: str
    user_id: int
    approved: bool
    comments: Optional[str] = None


@dataclass
class SampleDataUploadRequestDTO:
    """Request DTO for uploading sample data"""
    cycle_id: int
    report_id: int
    user_id: int
    samples: List[Dict[str, Any]]
    file_name: Optional[str] = None


@dataclass
class SampleSelectionResponseDTO:
    """Response DTO for sample selection operations"""
    sample_set_id: str
    cycle_id: int
    report_id: int
    status: str
    sample_count: int
    message: str
    errors: Optional[List[Dict[str, Any]]] = None