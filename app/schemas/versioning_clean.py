"""
Pydantic schemas for clean versioning API
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum


class VersionStatus(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"


class WorkflowStartRequest(BaseModel):
    """Request to start a new workflow"""
    cycle_id: int
    report_id: int
    initial_data: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        schema_extra = {
            "example": {
                "cycle_id": 1,
                "report_id": 101,
                "initial_data": {
                    "planning_data": {
                        "attributes": [
                            {
                                "attribute_id": 1,
                                "attribute_name": "Revenue",
                                "include_in_testing": True,
                                "risk_rating": "high"
                            }
                        ]
                    },
                    "lobs": [
                        {"lob_id": "uuid-1", "name": "LOB 1"},
                        {"lob_id": "uuid-2", "name": "LOB 2"}
                    ]
                }
            }
        }


class ApprovalRequest(BaseModel):
    """Request to approve a version"""
    phase: str
    version_id: str
    notes: Optional[str] = None


class RevisionRequest(BaseModel):
    """Request to revise a version"""
    phase: str
    version_id: str
    reason: str
    additional_data: Optional[Dict[str, Any]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "phase": "Sample Selection",
                "version_id": "uuid-here",
                "reason": "Need to add 5 more samples",
                "additional_data": {
                    "cycle_report_sample_selection_samples": [
                        {
                            "identifier": "SAMP-001",
                            "data": {"amount": 1000},
                            "type": "targeted",
                            "source": "tester"
                        }
                    ]
                }
            }
        }


class SignoffRequest(BaseModel):
    """Request to sign off on a report"""
    version_id: str
    role: str = Field(..., regex="^(test_lead|test_executive|report_owner)$")
    approved: bool
    notes: Optional[str] = None


class VersionResponse(BaseModel):
    """Version information response"""
    version_id: str
    version_number: int
    status: VersionStatus
    created_at: datetime
    created_by_id: int
    approved_at: Optional[datetime] = None
    approved_by_id: Optional[int] = None
    workflow_execution_id: str
    phase_name: str


class SampleDecisionResponse(BaseModel):
    """Sample decision information"""
    decision_id: str
    sample_identifier: str
    sample_data: Dict[str, Any]
    status: ApprovalStatus
    source: str
    carried_forward: bool
    decision_notes: Optional[str] = None


class WorkflowStatusResponse(BaseModel):
    """Workflow status response"""
    workflow_id: str
    phase_status: Dict[str, str]
    phase_versions: Dict[str, Any]


class PhaseMetricsResponse(BaseModel):
    """Phase metrics response"""
    phase_name: str
    version_count: int
    average_approval_time_hours: float
    rejection_rate: float
    revision_count: int
    current_version: Optional[str] = None
    status: str