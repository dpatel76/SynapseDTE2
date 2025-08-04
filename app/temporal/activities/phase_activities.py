"""Temporal activities for generic workflow phase management"""

from temporalio import activity
from datetime import datetime
from typing import Dict, Any
import logging
from sqlalchemy import select

from app.core.database import get_db
from app.models import WorkflowPhase
from app.temporal.shared import ActivityResult, PhaseResult, PhaseStatus

logger = logging.getLogger(__name__)


@activity.defn
async def start_phase_activity(cycle_id: int, report_id: int, phase_name: str) -> ActivityResult:
    """Generic start phase activity for phases without specific implementation"""
    try:
        async with get_db() as db:
            # Get or create workflow phase record
            result = await db.execute(
                select(WorkflowPhase).where(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == phase_name
                )
            )
            phase = result.scalar_one_or_none()
            
            if not phase:
                # Create phase record
                phase = WorkflowPhase(
                    cycle_id=cycle_id,
                    report_id=report_id,
                    phase_name=phase_name,
                    state="In Progress",
                    status="On Schedule",
                    actual_start_date=datetime.utcnow(),
                    started_by=1  # System user
                )
                db.add(phase)
            else:
                # Update existing phase
                phase.state = "In Progress"
                phase.actual_start_date = datetime.utcnow()
                phase.started_by = 1
            
            await db.commit()
            
            logger.info(f"Started generic phase: {phase_name}")
            return ActivityResult(
                success=True,
                data={
                    "phase_id": phase.phase_id,
                    "phase_name": phase_name,
                    "started_at": phase.actual_start_date.isoformat()
                }
            )
            
    except Exception as e:
        logger.error(f"Error starting phase {phase_name}: {str(e)}")
        return ActivityResult(
            success=False,
            error=str(e)
        )


@activity.defn
async def complete_phase_activity(
    cycle_id: int, 
    report_id: int, 
    phase_name: str, 
    phase_data: Dict[str, Any]
) -> ActivityResult:
    """Generic complete phase activity for phases without specific implementation"""
    try:
        async with get_db() as db:
            # Get workflow phase
            result = await db.execute(
                select(WorkflowPhase).where(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == phase_name
                )
            )
            phase = result.scalar_one_or_none()
            
            if not phase:
                return ActivityResult(
                    success=False,
                    error=f"Phase {phase_name} not found"
                )
            
            # Mark phase as complete
            phase.state = "Completed"
            phase.actual_end_date = datetime.utcnow()
            phase.completed_by = 1  # System user
            
            # Calculate if on schedule
            if phase.planned_end_date and phase.actual_end_date > phase.planned_end_date:
                phase.status = "Behind Schedule"
            else:
                phase.status = "Complete"
            
            await db.commit()
            
            logger.info(f"Completed generic phase: {phase_name}")
            return ActivityResult(
                success=True,
                data={
                    "phase_id": phase.phase_id,
                    "phase_name": phase_name,
                    "completed_at": phase.actual_end_date.isoformat(),
                    "duration_days": (phase.actual_end_date - phase.actual_start_date).days if phase.actual_start_date else 0
                }
            )
            
    except Exception as e:
        logger.error(f"Error completing phase {phase_name}: {str(e)}")
        return ActivityResult(
            success=False,
            error=str(e)
        )


@activity.defn
async def check_phase_dependencies_activity(
    cycle_id: int, 
    report_id: int, 
    phase_name: str
) -> bool:
    """Check if phase dependencies are met"""
    try:
        from app.temporal.shared import PHASE_DEPENDENCIES
        
        dependencies = PHASE_DEPENDENCIES.get(phase_name, [])
        if not dependencies:
            return True  # No dependencies
        
        async with get_db() as db:
            # Check if all dependency phases are complete
            for dep_phase in dependencies:
                result = await db.execute(
                    select(WorkflowPhase).where(
                        WorkflowPhase.cycle_id == cycle_id,
                        WorkflowPhase.report_id == report_id,
                        WorkflowPhase.phase_name == dep_phase,
                        WorkflowPhase.state == "Completed"
                    )
                )
                if not result.scalar_one_or_none():
                    logger.warning(f"Dependency not met: {dep_phase} not completed for {phase_name}")
                    return False
            
            return True
            
    except Exception as e:
        logger.error(f"Error checking phase dependencies: {str(e)}")
        return False