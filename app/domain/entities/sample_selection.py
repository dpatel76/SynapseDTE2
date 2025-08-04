"""Sample Selection domain entities"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

from app.domain.entities.base import BaseEntity
from app.domain.value_objects.identifiers import CycleId, ReportId, UserId, AttributeId, SampleId


class SampleStatus(str, Enum):
    """Sample status enumeration"""
    DRAFT = "Draft"
    SELECTED = "Selected"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    IN_USE = "In Use"


class SelectionMethod(str, Enum):
    """Sample selection method enumeration"""
    RANDOM = "Random"
    SYSTEMATIC = "Systematic"
    RISK_BASED = "Risk-Based"
    STATISTICAL = "Statistical"
    MANUAL = "Manual"


@dataclass
class SampleSet(BaseEntity):
    """Sample set entity"""
    sample_set_id: str
    cycle_id: CycleId
    report_id: ReportId
    attribute_id: AttributeId
    attribute_name: str
    sample_type: str
    selection_method: SelectionMethod
    target_sample_size: int
    actual_sample_size: int
    status: SampleStatus
    selection_criteria: Dict[str, Any]
    risk_factors: Optional[List[str]] = None
    notes: Optional[str] = None
    created_by: UserId = None
    approved_by: Optional[UserId] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    samples: List['SampleRecord'] = field(default_factory=list)
    
    def add_sample(self, sample: 'SampleRecord'):
        """Add a sample to the set"""
        self.samples.append(sample)
        self.actual_sample_size = len(self.samples)
    
    def approve(self, approved_by: UserId):
        """Approve the sample set"""
        self.status = SampleStatus.APPROVED
        self.approved_by = approved_by
        self.approved_at = datetime.utcnow()
    
    def reject(self, reason: str):
        """Reject the sample set"""
        self.status = SampleStatus.REJECTED
        self.rejection_reason = reason
    
    def is_complete(self) -> bool:
        """Check if sample set is complete"""
        return self.actual_sample_size >= self.target_sample_size


@dataclass
class SampleRecord:
    """Individual sample record"""
    sample_id: SampleId
    sample_set_id: str
    sample_identifier: str
    primary_key_values: Dict[str, Any]
    risk_score: Optional[float] = None
    selection_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_selected: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)