"""
Workflow signal definitions for clean versioning system
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional


@dataclass
class ApprovalSignal:
    """Signal for version approval"""
    phase: str
    version_id: str
    user_id: int
    approved: bool
    notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}


@dataclass
class RevisionSignal:
    """Signal for version revision request"""
    phase: str
    version_id: str
    user_id: int
    reason: str
    additional_data: Dict[str, Any]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class StatusUpdateSignal:
    """Signal for phase status updates"""
    phase: str
    status: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.details is None:
            self.details = {}