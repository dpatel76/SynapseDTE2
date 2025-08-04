"""Report DTOs"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List


@dataclass
class ReportDTO:
    """DTO for report data"""
    report_id: int
    report_name: str
    regulation: str
    report_type: str
    frequency: str
    submission_deadline: Optional[datetime] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ReportAttributeDTO:
    """DTO for report attribute"""
    attribute_id: int
    cycle_id: int
    report_id: int
    attribute_name: str
    description: str
    data_type: str
    is_critical: bool
    validation_rules: Optional[Dict[str, Any]] = None
    expected_value: Optional[Any] = None
    test_approach: Optional[str] = None
    risk_score: Optional[int] = None


@dataclass
class TestExecutionDTO:
    """DTO for test execution"""
    execution_id: int
    cycle_id: int
    report_id: int
    attribute_id: int
    test_type: str
    status: str
    executed_by: int
    executed_at: datetime
    result: Optional[str] = None
    evidence: Optional[List[Dict[str, Any]]] = None
    comments: Optional[str] = None


@dataclass
class TestResultDTO:
    """DTO for test result"""
    execution_id: int
    attribute_name: str
    expected_value: Any
    actual_value: Any
    status: str
    variance: Optional[str] = None
    evidence_documents: Optional[List[str]] = None
    notes: Optional[str] = None


@dataclass
class CreateObservationDTO:
    """DTO for creating an observation"""
    cycle_id: int
    report_id: int
    observation_type: str
    severity: str
    title: str
    description: str
    test_executions: List[int]
    created_by: int
    recommendations: Optional[str] = None


@dataclass
class ObservationDTO:
    """DTO for observation data"""
    observation_id: int
    cycle_id: int
    report_id: int
    observation_type: str
    severity: str
    title: str
    description: str
    status: str
    created_by: int
    created_at: datetime
    test_executions: List[int]
    recommendations: Optional[str] = None
    management_response: Optional[str] = None
    target_date: Optional[datetime] = None