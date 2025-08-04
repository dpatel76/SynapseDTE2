"""
Test Cycle Domain Entity
Rich domain model with business logic
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field

from app.domain.value_objects import CycleStatus, ReportAssignment
from app.domain.events import DomainEvent, TestCycleCreated, ReportAddedToCycle, CycleStatusChanged


class DomainError(Exception):
    """Base exception for domain errors"""
    pass


class TestCycleDomainError(DomainError):
    """Test cycle specific domain errors"""
    pass


@dataclass
class TestCycle:
    """
    Test Cycle aggregate root
    Encapsulates all business rules for test cycles
    """
    cycle_id: Optional[int]
    cycle_name: str
    description: Optional[str]
    start_date: datetime
    end_date: datetime
    status: CycleStatus
    created_by: int
    created_at: datetime = field(default_factory=datetime.utcnow)
    _reports: List[ReportAssignment] = field(default_factory=list)
    _events: List[DomainEvent] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate invariants after initialization"""
        self._validate_dates()
        if self.cycle_id is None:
            # New cycle
            self._events.append(TestCycleCreated(
                cycle_name=self.cycle_name,
                start_date=self.start_date,
                end_date=self.end_date,
                created_by=self.created_by
            ))
    
    def _validate_dates(self):
        """Ensure start date is before end date"""
        if self.start_date >= self.end_date:
            raise TestCycleDomainError("Start date must be before end date")
    
    def add_report(self, report_id: int, report_name: str, tester_id: Optional[int] = None) -> None:
        """
        Add a report to the test cycle
        Business rules:
        - Cannot add reports after planning phase
        - Cannot add duplicate reports
        - Validate tester assignment if provided
        """
        if self.status != CycleStatus.PLANNING:
            raise TestCycleDomainError(
                f"Cannot add reports when cycle is in {self.status.value} status. "
                "Reports can only be added during planning."
            )
        
        # Check for duplicates
        if any(r.report_id == report_id for r in self._reports):
            raise TestCycleDomainError(f"Report {report_id} is already in this cycle")
        
        # Create assignment
        assignment = ReportAssignment(
            report_id=report_id,
            report_name=report_name,
            tester_id=tester_id,
            assigned_at=datetime.utcnow() if tester_id else None
        )
        
        self._reports.append(assignment)
        
        # Emit event
        self._events.append(ReportAddedToCycle(
            cycle_id=self.cycle_id,
            report_id=report_id,
            report_name=report_name,
            tester_id=tester_id
        ))
    
    def assign_tester(self, report_id: int, tester_id: int) -> None:
        """
        Assign a tester to a report
        Business rules:
        - Report must be in the cycle
        - Cannot reassign without unassigning first
        - Must be in planning or active status
        """
        if self.status not in [CycleStatus.PLANNING, CycleStatus.ACTIVE]:
            raise TestCycleDomainError(
                f"Cannot assign testers when cycle is {self.status.value}"
            )
        
        report = self._find_report(report_id)
        
        if report.tester_id is not None:
            raise TestCycleDomainError(
                f"Report {report_id} is already assigned to tester {report.tester_id}"
            )
        
        report.tester_id = tester_id
        report.assigned_at = datetime.utcnow()
    
    def unassign_tester(self, report_id: int) -> None:
        """Remove tester assignment from a report"""
        if self.status == CycleStatus.COMPLETED:
            raise TestCycleDomainError("Cannot modify assignments in completed cycle")
        
        report = self._find_report(report_id)
        report.tester_id = None
        report.assigned_at = None
    
    def start_cycle(self) -> None:
        """
        Start the test cycle
        Business rules:
        - Must be in planning status
        - All reports must have testers assigned
        - Current date must be >= start date
        """
        if self.status != CycleStatus.PLANNING:
            raise TestCycleDomainError(
                f"Cannot start cycle from {self.status.value} status"
            )
        
        # Check all reports have testers
        unassigned = [r for r in self._reports if r.tester_id is None]
        if unassigned:
            raise TestCycleDomainError(
                f"{len(unassigned)} reports do not have testers assigned"
            )
        
        # Check start date
        if datetime.utcnow().date() < self.start_date.date():
            raise TestCycleDomainError(
                f"Cannot start cycle before start date {self.start_date.date()}"
            )
        
        self._transition_status(CycleStatus.ACTIVE)
    
    def complete_cycle(self) -> None:
        """
        Complete the test cycle
        Business rules:
        - Must be in active status
        - All reports must be in completed phase
        """
        if self.status != CycleStatus.ACTIVE:
            raise TestCycleDomainError(
                f"Cannot complete cycle from {self.status.value} status"
            )
        
        # In real implementation, would check all report phases
        # For now, just transition
        self._transition_status(CycleStatus.COMPLETED)
    
    def cancel_cycle(self, reason: str) -> None:
        """
        Cancel the test cycle
        Business rules:
        - Cannot cancel completed cycle
        - Must provide cancellation reason
        """
        if self.status == CycleStatus.COMPLETED:
            raise TestCycleDomainError("Cannot cancel a completed cycle")
        
        if not reason or len(reason.strip()) < 10:
            raise TestCycleDomainError(
                "Cancellation reason must be at least 10 characters"
            )
        
        self._transition_status(CycleStatus.CANCELLED)
    
    def _transition_status(self, new_status: CycleStatus) -> None:
        """Internal method to transition status and emit event"""
        old_status = self.status
        self.status = new_status
        
        self._events.append(CycleStatusChanged(
            cycle_id=self.cycle_id,
            old_status=old_status.value,
            new_status=new_status.value,
            changed_at=datetime.utcnow()
        ))
    
    def _find_report(self, report_id: int) -> ReportAssignment:
        """Find a report in the cycle"""
        for report in self._reports:
            if report.report_id == report_id:
                return report
        raise TestCycleDomainError(f"Report {report_id} not found in cycle")
    
    def get_assigned_reports(self, tester_id: Optional[int] = None) -> List[ReportAssignment]:
        """Get reports, optionally filtered by tester"""
        if tester_id is None:
            return list(self._reports)
        return [r for r in self._reports if r.tester_id == tester_id]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get cycle statistics"""
        total_reports = len(self._reports)
        assigned_reports = len([r for r in self._reports if r.tester_id is not None])
        
        return {
            "total_reports": total_reports,
            "assigned_reports": assigned_reports,
            "unassigned_reports": total_reports - assigned_reports,
            "assignment_percentage": (
                (assigned_reports / total_reports * 100) if total_reports > 0 else 0
            ),
            "status": self.status.value,
            "days_remaining": (self.end_date - datetime.utcnow()).days
        }
    
    def pull_events(self) -> List[DomainEvent]:
        """Get and clear domain events"""
        events = list(self._events)
        self._events.clear()
        return events
    
    @property
    def is_active(self) -> bool:
        """Check if cycle is currently active"""
        return self.status == CycleStatus.ACTIVE
    
    @property
    def can_modify(self) -> bool:
        """Check if cycle can be modified"""
        return self.status in [CycleStatus.PLANNING, CycleStatus.ACTIVE]
    
    def __repr__(self) -> str:
        return f"<TestCycle {self.cycle_name} ({self.status.value})>"