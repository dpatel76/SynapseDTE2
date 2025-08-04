"""Repository interfaces (ports) for the application layer"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.domain.entities.test_cycle import TestCycle
from app.domain.value_objects import CycleStatus


class TestCycleRepository(ABC):
    """Repository interface for test cycles"""
    
    @abstractmethod
    async def get(self, cycle_id: int) -> Optional[TestCycle]:
        """Get a test cycle by ID"""
        pass
    
    @abstractmethod
    async def get_by_name(self, cycle_name: str) -> Optional[TestCycle]:
        """Get a test cycle by name"""
        pass
    
    @abstractmethod
    async def save(self, cycle: TestCycle) -> TestCycle:
        """Save a test cycle (create or update)"""
        pass
    
    @abstractmethod
    async def delete(self, cycle_id: int) -> None:
        """Delete a test cycle"""
        pass
    
    @abstractmethod
    async def find_by_status(self, status: CycleStatus) -> List[TestCycle]:
        """Find all cycles with a specific status"""
        pass
    
    @abstractmethod
    async def find_by_date_range(self, start_date: datetime, end_date: datetime) -> List[TestCycle]:
        """Find cycles within a date range"""
        pass
    
    @abstractmethod
    async def find_by_user(self, user_id: int) -> List[TestCycle]:
        """Find cycles created by a specific user"""
        pass


class ReportRepository(ABC):
    """Repository interface for reports"""
    
    @abstractmethod
    async def get(self, report_id: int) -> Optional[dict]:
        """Get a report by ID"""
        pass
    
    @abstractmethod
    async def get_multiple(self, report_ids: List[int]) -> List[dict]:
        """Get multiple reports by IDs"""
        pass
    
    @abstractmethod
    async def find_by_regulation(self, regulation: str) -> List[dict]:
        """Find reports by regulation type"""
        pass
    
    @abstractmethod
    async def find_available_for_cycle(self) -> List[dict]:
        """Find reports available for assignment to cycles"""
        pass


class UserRepository(ABC):
    """Repository interface for users"""
    
    @abstractmethod
    async def get(self, user_id: int) -> Optional[dict]:
        """Get a user by ID"""
        pass
    
    @abstractmethod
    async def find_by_role(self, role: str) -> List[dict]:
        """Find users by role"""
        pass
    
    @abstractmethod
    async def find_testers(self) -> List[dict]:
        """Find all users with tester role"""
        pass
    
    @abstractmethod
    async def get_user_permissions(self, user_id: int) -> List[str]:
        """Get permissions for a user"""
        pass


class WorkflowRepository(ABC):
    """Repository interface for workflow phases"""
    
    @abstractmethod
    async def get_phase_status(self, cycle_id: int, report_id: int, phase_name: str) -> Optional[dict]:
        """Get the status of a specific workflow phase"""
        pass
    
    @abstractmethod
    async def save_phase_status(self, cycle_id: int, report_id: int, phase_name: str, status: dict) -> None:
        """Save the status of a workflow phase"""
        pass
    
    @abstractmethod
    async def get_all_phases(self, cycle_id: int, report_id: int) -> List[dict]:
        """Get all workflow phases for a cycle/report"""
        pass
    
    @abstractmethod
    async def can_advance_to_phase(self, cycle_id: int, report_id: int, target_phase: str) -> bool:
        """Check if workflow can advance to target phase"""
        pass


class ISampleSelectionRepository(ABC):
    """Repository interface for sample selection operations"""
    
    @abstractmethod
    async def create_sample_set(self, cycle_id: int, report_id: int, created_by: int, 
                               generation_method: str, sample_count: int) -> Any:
        """Create a new sample set"""
        pass
    
    @abstractmethod
    async def get_sample_set(self, sample_set_id: str) -> Any:
        """Get sample set by ID"""
        pass
    
    @abstractmethod
    async def add_sample_record(self, sample_set_id: str, **kwargs) -> Any:
        """Add sample record to set"""
        pass
    
    @abstractmethod
    async def update_sample_set_status(self, sample_set_id: str, status: str, 
                                      reviewed_by: int, review_comments: Optional[str] = None) -> Any:
        """Update sample set status"""
        pass
    
    @abstractmethod
    async def check_all_samples_approved(self, cycle_id: int, report_id: int) -> bool:
        """Check if all samples are approved"""
        pass


class IWorkflowRepository(ABC):
    """Interface alias for WorkflowRepository"""
    
    @abstractmethod
    async def update_phase_status(self, cycle_id: int, report_id: int, 
                                 phase_name: str, status: str) -> Any:
        """Update workflow phase status"""
        pass