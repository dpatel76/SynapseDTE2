from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from enum import Enum

class ObservationSeverity(str, Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

class ObservationStatus(str, Enum):
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"
    CLOSED = "Closed"

class ObservationType(str, Enum):
    DOCUMENT = "Document"
    DATABASE = "Database"
    PROCESS = "Process"
    CONTROL = "Control"

class ObservationResponse(BaseModel):
    observation_id: int
    cycle_id: int
    report_id: int
    phase_id: int
    title: str
    description: str
    observation_type: ObservationType
    severity: ObservationSeverity
    status: ObservationStatus
    detection_method: Optional[str] = None
    financial_impact: Optional[float] = None
    detected_by: int
    assigned_to: Optional[int] = None
    resolution_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None

    class Config:
        from_attributes = True 