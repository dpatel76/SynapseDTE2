"""
Dynamic Activity Execution for Temporal Workflows
Handles both sequential and parallel activity execution
"""

from temporalio import activity
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
import asyncio

from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.config import settings
from app.models.workflow_activity import (
    WorkflowActivity, WorkflowActivityTemplate,
    ActivityStatus, ActivityType
)
from app.models.workflow import WorkflowPhase
from app.temporal.shared import ActivityResult
from app.temporal.activities.activity_handler import (
    ActivityContext, ActivityHandlerRegistry, ActivityExecutionMode
)

logger = logging.getLogger(__name__)


@activity.defn
async def get_activities_for_phase_activity(
    cycle_id: int,
    report_id: int, 
    phase_name: str
) -> List[Dict[str, Any]]:
    """Get all activities configured for a phase"""
    try:
        async with get_db() as db:
            # Get activity templates for the phase
            result = await db.execute(
                select(WorkflowActivityTemplate)
                .where(
                    and_(
                        WorkflowActivityTemplate.phase_name == phase_name,
                        WorkflowActivityTemplate.is_active == True
                    )
                )
                .order_by(WorkflowActivityTemplate.activity_order)
            )
            templates = result.scalars().all()
            
            activities = []
            for template in templates:
                # Check if activity already exists
                activity_result = await db.execute(
                    select(WorkflowActivity).where(
                        and_(
                            WorkflowActivity.cycle_id == cycle_id,
                            WorkflowActivity.report_id == report_id,
                            WorkflowActivity.phase_name == phase_name,
                            WorkflowActivity.activity_name == template.activity_name
                        )
                    )
                )
                existing_activity = activity_result.scalar_one_or_none()
                
                # Use timeout from template if dynamic timeout is enabled
                timeout = template.timeout_seconds if (
                    settings.dynamic_activity_timeout_enabled and 
                    template.timeout_seconds
                ) else settings.temporal_activity_timeout
                
                activity_data = {
                    "name": template.activity_name,
                    "type": template.activity_type.value,
                    "order": template.activity_order,
                    "is_manual": template.is_manual,
                    "is_optional": template.is_optional,
                    "required_role": template.required_role,
                    "timeout": timeout,
                    "handler_name": template.handler_name or settings.fallback_handler,
                    "execution_mode": template.execution_mode or "sequential",
                    "retry_policy": template.retry_policy if settings.dynamic_activity_retry_enabled else None,
                    "conditional_expression": template.conditional_expression if settings.enable_conditional_activities else None,
                    "metadata": {
                        "description": template.description,
                        "auto_complete_on_event": template.auto_complete_on_event
                    },
                    "status": existing_activity.status.value if existing_activity else ActivityStatus.NOT_STARTED.value,
                    "can_start": existing_activity.can_start if existing_activity else False
                }
                
                activities.append(activity_data)
            
            logger.info(f"Found {len(activities)} activities for phase {phase_name}")
            return activities
            
    except Exception as e:
        logger.error(f"Error getting activities for phase: {str(e)}")
        raise


@activity.defn
async def execute_workflow_activity(
    cycle_id: int,
    report_id: int,
    phase_name: str,
    activity_name: str,
    activity_type: str,
    metadata: Dict[str, Any],
    instance_id: Optional[str] = None,
    parent_results: Optional[Dict[str, Any]] = None
) -> ActivityResult:
    """Execute a single workflow activity"""
    try:
        async with get_db() as db:
            # Create activity context
            context = ActivityContext(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_name=phase_name,
                activity_name=activity_name,
                activity_type=activity_type,
                metadata=metadata,
                instance_id=instance_id,
                parent_results=parent_results
            )
            
            # Get handler for the activity using configuration
            handler_name = metadata.get("handler_name")
            handler = None
            
            if handler_name and settings.use_dynamic_workflows:
                # Try to get specific handler by name
                handler_class = ActivityHandlerRegistry.get_handler_by_name(handler_name)
                if handler_class:
                    handler = handler_class(db)
            
            if not handler:
                # Fall back to type-based lookup
                handler = ActivityHandlerRegistry.get_handler(phase_name, activity_type, db)
            
            if not handler:
                # Use configured fallback handlers
                if metadata.get("is_manual", False):
                    handler_class = ActivityHandlerRegistry.get_handler_by_name(settings.manual_activity_handler)
                else:
                    handler_class = ActivityHandlerRegistry.get_handler_by_name(settings.fallback_handler)
                
                if handler_class:
                    handler = handler_class(db)
            
            if not handler:
                raise ValueError(f"No handler found for activity {activity_name} of type {activity_type}")
            
            # Check if activity can execute
            if not await handler.can_execute(context):
                return ActivityResult(
                    success=False,
                    error="Dependencies not met",
                    data={"status": "waiting_for_dependencies"}
                )
            
            # Execute the activity
            result = await handler.execute(context)
            
            # Log execution
            logger.info(f"Executed activity {activity_name} for phase {phase_name}: {result.success}")
            
            return result
            
    except Exception as e:
        logger.error(f"Error executing activity {activity_name}: {str(e)}")
        return ActivityResult(
            success=False,
            error=str(e)
        )


@activity.defn
async def check_manual_activity_completed_activity(
    cycle_id: int,
    report_id: int,
    phase_name: str,
    activity_name: str,
    instance_id: Optional[str] = None
) -> bool:
    """Check if a manual activity has been completed"""
    try:
        async with get_db() as db:
            query = select(WorkflowActivity).where(
                and_(
                    WorkflowActivity.cycle_id == cycle_id,
                    WorkflowActivity.report_id == report_id,
                    WorkflowActivity.phase_name == phase_name,
                    WorkflowActivity.activity_name == activity_name,
                    WorkflowActivity.status == ActivityStatus.COMPLETED
                )
            )
            
            if instance_id:
                # Check specific instance
                query = query.where(
                    WorkflowActivity.activity_metadata.contains({"instance_id": instance_id})
                )
            
            result = await db.execute(query.limit(1))
            return result.scalar_one_or_none() is not None
            
    except Exception as e:
        logger.error(f"Error checking activity completion: {str(e)}")
        return False


@activity.defn
async def get_parallel_instances_activity(
    cycle_id: int,
    report_id: int,
    phase_name: str
) -> List[Dict[str, Any]]:
    """Get instances for parallel execution based on phase"""
    try:
        async with get_db() as db:
            config = ActivityHandlerRegistry.get_parallel_execution_config(phase_name)
            
            if not config:
                # Not a parallel phase
                return []
            
            instances = []
            
            if phase_name == "Request for Information":
                # Get all assigned data owners
                from app.models.testing import DataProviderAssignment
                result = await db.execute(
                    select(DataProviderAssignment)
                    .where(
                        and_(
                            DataProviderAssignment.cycle_id == cycle_id,
                            DataProviderAssignment.report_id == report_id
                        )
                    )
                    .distinct(DataProviderAssignment.data_provider_id)
                    .options(selectinload(DataProviderAssignment.data_provider))
                )
                assignments = result.scalars().all()
                
                for assignment in assignments:
                    instances.append({
                        "instance_id": f"data_owner_{assignment.data_provider_id}",
                        "instance_data": {
                            "data_owner_id": assignment.data_provider_id,
                            "data_owner_name": assignment.data_provider.full_name
                        }
                    })
                    
            elif phase_name == "Test Execution":
                # Get all uploaded documents
                from app.models.document import Document
                result = await db.execute(
                    select(Document)
                    .where(
                        and_(
                            Document.cycle_id == cycle_id,
                            Document.report_id == report_id,
                            Document.document_type == "test_data"
                        )
                    )
                )
                documents = result.scalars().all()
                
                for doc in documents:
                    instances.append({
                        "instance_id": f"document_{doc.document_id}",
                        "instance_data": {
                            "document_id": doc.document_id,
                            "document_name": doc.document_name
                        }
                    })
                    
            elif phase_name == "Observation Management":
                # Get all completed test executions
                from app.models.test_execution import TestExecution
                result = await db.execute(
                    select(TestExecution)
                    .where(
                        and_(
                            TestExecution.cycle_id == cycle_id,
                            TestExecution.report_id == report_id,
                            TestExecution.status == "Completed"
                        )
                    )
                )
                test_executions = result.scalars().all()
                
                for test_exec in test_executions:
                    instances.append({
                        "instance_id": f"test_execution_{test_exec.execution_id}",
                        "instance_data": {
                            "test_execution_id": test_exec.execution_id,
                            "test_case_id": test_exec.test_case_id
                        }
                    })
            
            logger.info(f"Found {len(instances)} instances for parallel execution in {phase_name}")
            return instances
            
    except Exception as e:
        logger.error(f"Error getting parallel instances: {str(e)}")
        return []


@activity.defn
async def check_phase_completion_dependencies_activity(
    cycle_id: int,
    report_id: int,
    phase_name: str
) -> bool:
    """Check if phase completion dependencies are met"""
    try:
        async with get_db() as db:
            # Special check for Finalize Test Report
            if phase_name == "Finalize Test Report":
                # Check if ALL observations are complete
                from app.models.observation_management import Observation
                
                # Get total test executions
                from app.models.test_execution import TestExecution
                test_result = await db.execute(
                    select(TestExecution)
                    .where(
                        and_(
                            TestExecution.cycle_id == cycle_id,
                            TestExecution.report_id == report_id,
                            TestExecution.status == "Completed"
                        )
                    )
                )
                test_executions = test_result.scalars().all()
                
                if not test_executions:
                    return False
                
                # Check if all have observations
                for test_exec in test_executions:
                    obs_result = await db.execute(
                        select(Observation)
                        .where(
                            and_(
                                Observation.cycle_id == cycle_id,
                                Observation.report_id == report_id,
                                Observation.test_execution_id == test_exec.execution_id,
                                Observation.status.in_(["Reviewed", "Closed"])
                            )
                        )
                        .limit(1)
                    )
                    if not obs_result.scalar_one_or_none():
                        logger.info(f"Test execution {test_exec.execution_id} has no completed observations")
                        return False
                
                return True
            
            # For other phases, use standard dependency check
            return True
            
    except Exception as e:
        logger.error(f"Error checking phase completion dependencies: {str(e)}")
        return False


@activity.defn
async def create_workflow_activity_record_activity(
    cycle_id: int,
    report_id: int,
    phase_name: str,
    activity_name: str,
    activity_type: str,
    activity_order: int,
    metadata: Dict[str, Any]
) -> ActivityResult:
    """Create a workflow activity record in the database"""
    try:
        async with get_db() as db:
            # Check if activity already exists
            result = await db.execute(
                select(WorkflowActivity).where(
                    and_(
                        WorkflowActivity.cycle_id == cycle_id,
                        WorkflowActivity.report_id == report_id,
                        WorkflowActivity.phase_name == phase_name,
                        WorkflowActivity.activity_name == activity_name
                    )
                )
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                return ActivityResult(
                    success=True,
                    data={"activity_id": existing.activity_id, "already_exists": True}
                )
            
            # Create new activity
            # Convert activity_type string to enum, with fallback
            try:
                activity_type_enum = ActivityType(activity_type)
            except ValueError:
                # Fallback to TASK if invalid type provided
                logger.warning(f"Invalid activity_type '{activity_type}', defaulting to TASK")
                activity_type_enum = ActivityType.TASK
            
            activity = WorkflowActivity(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_name=phase_name,
                activity_name=activity_name,
                activity_type=activity_type_enum,
                activity_order=activity_order,
                status=ActivityStatus.NOT_STARTED,
                can_start=metadata.get("can_start", False),
                is_manual=metadata.get("is_manual", True),
                is_optional=metadata.get("is_optional", False),
                activity_metadata=metadata
            )
            
            db.add(activity)
            await db.commit()
            
            return ActivityResult(
                success=True,
                data={"activity_id": activity.activity_id, "created": True}
            )
            
    except Exception as e:
        logger.error(f"Error creating activity record: {str(e)}")
        return ActivityResult(
            success=False,
            error=str(e)
        )