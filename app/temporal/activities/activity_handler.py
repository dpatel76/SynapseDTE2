"""
Activity Handler Framework for Dynamic Workflow Activities
Supports sequential dependencies and parallel execution paths
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
import logging
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.workflow_activity import WorkflowActivity, ActivityStatus
from app.temporal.shared import ActivityResult

logger = logging.getLogger(__name__)


class ActivityExecutionMode(str, Enum):
    """Defines how activities should be executed"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    MANUAL = "manual"
    AUTOMATED = "automated"


class DependencyType(str, Enum):
    """Types of dependencies between activities"""
    COMPLETION = "completion"  # Previous activity must complete
    APPROVAL = "approval"      # Previous activity must be approved
    DATA_READY = "data_ready"  # Data from previous activity must be ready
    ALL_INSTANCES = "all_instances"  # All parallel instances must complete


@dataclass
class ActivityContext:
    """Context for activity execution"""
    cycle_id: int
    report_id: int
    phase_name: str
    activity_name: str
    activity_type: str
    metadata: Dict[str, Any]
    instance_id: Optional[str] = None  # For parallel instances (e.g., per data owner)
    parent_results: Optional[Dict[str, Any]] = None  # Results from dependencies


@dataclass
class ActivityDependency:
    """Defines a dependency between activities"""
    depends_on_phase: str
    depends_on_activity: str
    dependency_type: DependencyType
    wait_for_all_instances: bool = False  # For parallel activities


class BaseActivityHandler(ABC):
    """Base class for all activity handlers"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    async def can_execute(self, context: ActivityContext) -> bool:
        """Check if activity can be executed based on dependencies"""
        pass
    
    @abstractmethod
    async def execute(self, context: ActivityContext) -> ActivityResult:
        """Execute the activity logic"""
        pass
    
    @abstractmethod
    async def compensate(self, context: ActivityContext, result: ActivityResult) -> None:
        """Compensate/rollback the activity if needed"""
        pass
    
    @abstractmethod
    def get_dependencies(self) -> List[ActivityDependency]:
        """Get list of dependencies for this activity"""
        pass
    
    async def check_dependencies_met(self, context: ActivityContext) -> bool:
        """Check if all dependencies are satisfied"""
        dependencies = self.get_dependencies()
        
        for dep in dependencies:
            if not await self._check_dependency(context, dep):
                return False
        
        return True
    
    async def _check_dependency(self, context: ActivityContext, dependency: ActivityDependency) -> bool:
        """Check if a specific dependency is satisfied"""
        query = select(WorkflowActivity).where(
            and_(
                WorkflowActivity.cycle_id == context.cycle_id,
                WorkflowActivity.report_id == context.report_id,
                WorkflowActivity.phase_name == dependency.depends_on_phase,
                WorkflowActivity.activity_name == dependency.depends_on_activity
            )
        )
        
        if dependency.wait_for_all_instances:
            # Check all instances are complete
            result = await self.db.execute(query)
            activities = result.scalars().all()
            
            if not activities:
                return False
            
            # All instances must be in completed state
            return all(
                activity.status == ActivityStatus.COMPLETED 
                for activity in activities
            )
        else:
            # Check at least one instance is complete
            query = query.where(
                WorkflowActivity.status == ActivityStatus.COMPLETED
            )
            result = await self.db.execute(query.limit(1))
            return result.scalar_one_or_none() is not None


class ActivityHandlerRegistry:
    """Registry for activity handlers with dependency management"""
    
    _handlers: Dict[str, type[BaseActivityHandler]] = {}
    _handlers_by_name: Dict[str, type[BaseActivityHandler]] = {}
    _phase_dependencies: Dict[str, Set[str]] = {
        "Planning": set(),
        "Data Profiling": {"Planning"},
        "Scoping": {"Data Profiling"},
        "Sample Selection": {"Scoping"},
        "Data Owner Identification": {"Sample Selection"},
        "Request for Information": {"Data Owner Identification"},
        "Test Execution": {"Request for Information"},
        "Observation Management": {"Test Execution"},
        "Finalize Test Report": {"Observation Management"}
    }
    
    @classmethod
    def register(cls, phase: str, activity_type: str, handler_class: type[BaseActivityHandler]):
        """Register an activity handler"""
        key = f"{phase}:{activity_type}"
        cls._handlers[key] = handler_class
        cls._handlers_by_name[handler_class.__name__] = handler_class
        logger.info(f"Registered handler {handler_class.__name__} for {key}")
    
    @classmethod
    def get_handler(cls, phase: str, activity_type: str, db: AsyncSession) -> Optional[BaseActivityHandler]:
        """Get handler instance for an activity"""
        key = f"{phase}:{activity_type}"
        handler_class = cls._handlers.get(key)
        
        if not handler_class:
            # Try generic handler
            key = f"*:{activity_type}"
            handler_class = cls._handlers.get(key)
        
        if handler_class:
            return handler_class(db)
        
        return None
    
    @classmethod
    def get_handler_by_name(cls, handler_name: str) -> Optional[BaseActivityHandler]:
        """Get handler by class name"""
        handler_class = cls._handlers_by_name.get(handler_name)
        if handler_class:
            # Note: This returns the class, not an instance
            # The caller needs to instantiate with db session
            return handler_class
        return None
    
    @classmethod
    def can_phase_start(cls, phase: str, completed_phases: Set[str]) -> bool:
        """Check if a phase can start based on phase dependencies"""
        required_phases = cls._phase_dependencies.get(phase, set())
        return required_phases.issubset(completed_phases)
    
    @classmethod
    def get_parallel_execution_config(cls, phase: str) -> Dict[str, Any]:
        """Get parallel execution configuration for a phase"""
        parallel_configs = {
            "Request for Information": {
                "parallel_by": "data_owner",
                "instance_key": "data_owner_id"
            },
            "Test Execution": {
                "parallel_by": "document",
                "instance_key": "document_id"
            },
            "Observation Management": {
                "parallel_by": "test_execution",
                "instance_key": "test_execution_id"
            }
        }
        return parallel_configs.get(phase, {})


# Example specific handlers

class ManualActivityHandler(BaseActivityHandler):
    """Generic handler for manual activities"""
    
    async def can_execute(self, context: ActivityContext) -> bool:
        """Manual activities can always start if dependencies are met"""
        return await self.check_dependencies_met(context)
    
    async def execute(self, context: ActivityContext) -> ActivityResult:
        """Create a pending activity record for manual completion"""
        # Create or update activity record
        result = await self.db.execute(
            select(WorkflowActivity).where(
                and_(
                    WorkflowActivity.cycle_id == context.cycle_id,
                    WorkflowActivity.report_id == context.report_id,
                    WorkflowActivity.phase_name == context.phase_name,
                    WorkflowActivity.activity_name == context.activity_name
                )
            )
        )
        activity = result.scalar_one_or_none()
        
        if not activity:
            activity = WorkflowActivity(
                cycle_id=context.cycle_id,
                report_id=context.report_id,
                phase_name=context.phase_name,
                activity_name=context.activity_name,
                activity_type=context.activity_type,
                status=ActivityStatus.IN_PROGRESS,
                started_at=datetime.utcnow(),
                can_start=True,
                is_manual=True,
                activity_metadata=context.metadata
            )
            self.db.add(activity)
        else:
            activity.status = ActivityStatus.IN_PROGRESS
            activity.started_at = datetime.utcnow()
        
        await self.db.commit()
        
        return ActivityResult(
            success=True,
            data={
                "activity_id": activity.activity_id,
                "status": "pending_manual_completion",
                "requires_user_action": True
            }
        )
    
    async def compensate(self, context: ActivityContext, result: ActivityResult) -> None:
        """Reset manual activity status"""
        await self.db.execute(
            select(WorkflowActivity).where(
                and_(
                    WorkflowActivity.cycle_id == context.cycle_id,
                    WorkflowActivity.report_id == context.report_id,
                    WorkflowActivity.phase_name == context.phase_name,
                    WorkflowActivity.activity_name == context.activity_name
                )
            ).update({"status": ActivityStatus.NOT_STARTED})
        )
        await self.db.commit()
    
    def get_dependencies(self) -> List[ActivityDependency]:
        """Manual activities typically depend on previous activities in the phase"""
        return []  # Override in specific handlers


class AutomatedActivityHandler(BaseActivityHandler):
    """Base handler for automated activities"""
    
    async def can_execute(self, context: ActivityContext) -> bool:
        """Check dependencies and any additional conditions"""
        return await self.check_dependencies_met(context)
    
    def get_dependencies(self) -> List[ActivityDependency]:
        """Default no dependencies - override in specific handlers"""
        return []


# Register generic handlers
ActivityHandlerRegistry.register("*", "manual", ManualActivityHandler)
ActivityHandlerRegistry.register("*", "automated", AutomatedActivityHandler)