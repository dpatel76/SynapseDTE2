"""Test cycle related domain events"""
from datetime import datetime
from typing import Optional

from .base import DomainEvent


class TestCycleCreated(DomainEvent):
    """Event raised when a new test cycle is created"""
    
    def __init__(self, cycle_name: str, start_date: datetime, end_date: datetime, created_by: int):
        super().__init__()
        self.cycle_name = cycle_name
        self.start_date = start_date
        self.end_date = end_date
        self.created_by = created_by


class ReportAddedToCycle(DomainEvent):
    """Event raised when a report is added to a cycle"""
    
    def __init__(self, cycle_id: Optional[int], report_id: int, report_name: str, tester_id: Optional[int] = None):
        super().__init__()
        self.cycle_id = cycle_id
        self.report_id = report_id
        self.report_name = report_name
        self.tester_id = tester_id


class CycleStatusChanged(DomainEvent):
    """Event raised when cycle status changes"""
    
    def __init__(self, cycle_id: Optional[int], old_status: str, new_status: str, changed_at: datetime):
        super().__init__()
        self.cycle_id = cycle_id
        self.old_status = old_status
        self.new_status = new_status
        self.changed_at = changed_at


class TesterAssignedToReport(DomainEvent):
    """Event raised when a tester is assigned to a report"""
    
    def __init__(self, cycle_id: int, report_id: int, tester_id: int, assigned_by: int):
        super().__init__()
        self.cycle_id = cycle_id
        self.report_id = report_id
        self.tester_id = tester_id
        self.assigned_by = assigned_by