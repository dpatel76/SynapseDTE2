"""Test Cycle DTOs"""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any


@dataclass
class CreateTestCycleDTO:
    """DTO for creating a test cycle"""
    cycle_name: str
    start_date: datetime
    end_date: datetime
    created_by: int
    description: Optional[str] = None
    regulations: Optional[List[str]] = None


@dataclass
class UpdateTestCycleDTO:
    """DTO for updating a test cycle"""
    cycle_id: int
    cycle_name: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    description: Optional[str] = None
    status: Optional[str] = None


@dataclass
class TestCycleDTO:
    """DTO for test cycle data"""
    cycle_id: int
    cycle_name: str
    start_date: datetime
    end_date: datetime
    status: str
    created_by: int
    created_at: datetime
    updated_at: datetime
    description: Optional[str] = None
    reports: List[Dict[str, Any]] = None
    metrics: Optional[Dict[str, Any]] = None


@dataclass
class AddReportToCycleDTO:
    """DTO for adding a report to a cycle"""
    cycle_id: int
    report_id: int
    requested_by: int
    tester_id: Optional[int] = None


@dataclass
class AssignTesterDTO:
    """DTO for assigning a tester to a report"""
    cycle_id: int
    report_id: int
    tester_id: int
    assigned_by: int