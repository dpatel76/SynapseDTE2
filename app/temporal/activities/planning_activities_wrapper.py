"""Planning Phase Activities - Wrappers for existing use cases

These activities are thin wrappers around the existing, tested planning phase
use cases and services. They preserve all existing business logic.
"""

from temporalio import activity
from datetime import datetime
from typing import Dict, Any, List
import logging

from app.core.database import get_db
from app.services.workflow_orchestrator import get_workflow_orchestrator
from app.api.v1.endpoints.planning import (
    start_planning_phase,
    get_planning_checklist,
    update_planning_item,
    complete_planning_phase,
    reopen_planning_phase
)
from app.models.user import User

logger = logging.getLogger(__name__)


@activity.defn
async def start_planning_phase_activity(
    cycle_id: int,
    report_id: int,
    user_id: int
) -> Dict[str, Any]:
    """Wrapper for existing start_planning_phase endpoint logic"""
    try:
        # Get database session
        async for db in get_db():
            # Create a mock user object for the existing function
            user = User(user_id=user_id)
            
            # Call the existing endpoint logic directly
            # This reuses all the tested business logic
            from app.api.v1.endpoints.planning import StartPlanningRequest
            request = StartPlanningRequest(
                notes="Started via Temporal workflow"
            )
            
            # Get workflow orchestrator (same as endpoint does)
            orchestrator = get_workflow_orchestrator(db)
            
            # Start planning phase using existing logic
            phase = await orchestrator.start_planning_phase(
                cycle_id=cycle_id,
                report_id=report_id,
                notes=request.notes,
                user_id=user.user_id
            )
            
            logger.info(f"Started planning phase for cycle {cycle_id}, report {report_id}")
            
            return {
                "success": True,
                "phase_id": phase.phase_id,
                "state": phase.state,
                "status": phase.schedule_status,
                "data": {
                    "phase_name": phase.phase_name,
                    "started_at": phase.actual_start_date.isoformat() if phase.actual_start_date else None
                }
            }
            
    except Exception as e:
        logger.error(f"Failed to start planning phase: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@activity.defn
async def execute_planning_activities(
    cycle_id: int,
    report_id: int,
    user_id: int
) -> Dict[str, Any]:
    """Execute planning phase activities using existing business logic"""
    try:
        async for db in get_db():
            # Get checklist using existing endpoint logic
            orchestrator = get_workflow_orchestrator(db)
            checklist = await orchestrator.get_planning_checklist(
                cycle_id=cycle_id,
                report_id=report_id
            )
            
            # Auto-complete items that can be automated
            completed_items = []
            for item in checklist:
                if item['can_be_automated']:
                    # Use existing update logic
                    updated_phase = await orchestrator.update_planning_item(
                        cycle_id=cycle_id,
                        report_id=report_id,
                        item_id=item['item_id'],
                        completed=True,
                        notes=f"Completed by workflow at {datetime.utcnow().isoformat()}",
                        user_id=user_id
                    )
                    completed_items.append(item['item_id'])
            
            logger.info(f"Completed {len(completed_items)} planning items")
            
            return {
                "success": True,
                "data": {
                    "total_items": len(checklist),
                    "completed_items": len(completed_items),
                    "checklist": checklist
                }
            }
            
    except Exception as e:
        logger.error(f"Failed to execute planning activities: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@activity.defn
async def complete_planning_phase_activity(
    cycle_id: int,
    report_id: int,
    user_id: int,
    phase_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Complete planning phase using existing endpoint logic"""
    try:
        async for db in get_db():
            orchestrator = get_workflow_orchestrator(db)
            
            # Complete phase using existing business logic
            phase = await orchestrator.complete_planning_phase(
                cycle_id=cycle_id,
                report_id=report_id,
                completion_notes=f"Completed via workflow with data: {phase_data}",
                user_id=user_id
            )
            
            # Advance to next phase (Scoping)
            await orchestrator.advance_phase(
                cycle_id=cycle_id,
                report_id=report_id,
                from_phase="Planning",
                to_phase="Scoping",
                user_id=user_id
            )
            
            logger.info(f"Completed planning phase for cycle {cycle_id}, report {report_id}")
            
            return {
                "success": True,
                "data": {
                    "phase_name": phase.phase_name,
                    "completed_at": phase.actual_end_date.isoformat() if phase.actual_end_date else None,
                    "next_phase": "Scoping"
                }
            }
            
    except Exception as e:
        logger.error(f"Failed to complete planning phase: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }