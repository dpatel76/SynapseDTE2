"""Report Assignment Value Object"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ReportAssignment:
    """
    Represents an assignment of a report to a tester
    Immutable value object
    """
    report_id: int
    report_name: str
    tester_id: Optional[int] = None
    assigned_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate assignment"""
        if self.tester_id is not None and self.assigned_at is None:
            raise ValueError("Assignment date required when tester is assigned")
        
        if self.tester_id is None and self.assigned_at is not None:
            raise ValueError("Cannot have assignment date without tester")
    
    @property
    def is_assigned(self) -> bool:
        """Check if report is assigned to a tester"""
        return self.tester_id is not None
    
    def __eq__(self, other):
        if not isinstance(other, ReportAssignment):
            return False
        return self.report_id == other.report_id
    
    def __hash__(self):
        return hash(self.report_id)