"""API endpoint for starting test workflows"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.api.v1.deps import get_current_user
from app.core.permissions import require_permission
from app.models import User, TestCycle, Report, CycleReport
from app.models.workflow import WorkflowPhase
from app.temporal.client import get_temporal_client
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


class PhaseDateRequest(BaseModel):
    """Request model for setting phase dates"""
    start_date: date
    end_date: date


@router.post("/cycles/{cycle_id}/reports/{report_id}/start-workflow")
@require_permission("testing", "execute")
async def start_testing_workflow(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Start a Temporal workflow for testing a specific report in a cycle.
    This endpoint should be called when a tester clicks "Start Testing".
    """
    
    # Verify the cycle exists
    cycle_result = await db.execute(
        select(TestCycle).where(TestCycle.cycle_id == cycle_id)
    )
    cycle = cycle_result.scalar_one_or_none()
    if not cycle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test cycle not found"
        )
    
    # Verify the report exists
    report_result = await db.execute(
        select(Report).where(Report.report_id == report_id)
    )
    report = report_result.scalar_one_or_none()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    # Verify the report is assigned to this cycle and the current user is the assigned tester
    assignment_result = await db.execute(
        select(CycleReport).where(
            and_(
                CycleReport.cycle_id == cycle_id,
                CycleReport.report_id == report_id
            )
        )
    )
    assignment = assignment_result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report is not assigned to this cycle"
        )
    
    # Check if the current user is the assigned tester
    if assignment.tester_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not the assigned tester for this report"
        )
    
    # Check if workflow already exists
    if assignment.workflow_id:
        return {
            "message": "Workflow already exists",
            "workflow_id": assignment.workflow_id,
            "status": "existing"
        }
    
    try:
        # Get Temporal client and start/get workflow
        temporal_client = await get_temporal_client()
        workflow_id = await temporal_client.start_testing_workflow(
            cycle_id=cycle_id,
            report_id=report_id,
            user_id=current_user.user_id,
            metadata={
                "started_at": datetime.utcnow().isoformat(),
                "started_by": current_user.email,
                "report_name": report.report_name,
                "cycle_name": cycle.cycle_name
            }
        )
        logger.info(f"Workflow {workflow_id} ready for cycle {cycle_id}, report {report_id}")
        
        # Update the assignment with the workflow ID
        assignment.workflow_id = workflow_id
        assignment.status = "In Progress"
        assignment.started_at = datetime.utcnow()
        
        # Check if phases already exist
        existing_phases_result = await db.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id
                )
            )
        )
        existing_phases = existing_phases_result.scalars().all()
        
        if not existing_phases:
            # Create all workflow phases (must match workflow_phase_enum)
            phases = [
                "Planning",
                "Data Profiling",
                "Scoping",
                "Sample Selection",
                "Data Provider ID",
                "Request Info",
                "Testing",
                "Observations",
                "Finalize Test Report"
            ]
            
            created_phases = []
            for phase_name in phases:
                phase = WorkflowPhase(
                    cycle_id=cycle_id,
                    report_id=report_id,
                    phase_name=phase_name,
                    status="Not Started",
                    state="Not Started",
                    schedule_status="On Track",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(phase)
                created_phases.append(phase_name)
        else:
            created_phases = [p.phase_name for p in existing_phases]
            logger.info(f"Workflow phases already exist for cycle {cycle_id}, report {report_id}")
        
        # No need to create phase-specific records anymore
        # All phase tracking is done through WorkflowPhase table
        
        # Ensure phases are saved
        await db.flush()
        await db.commit()
        
        logger.info(f"Created {len(created_phases)} workflow phases for cycle {cycle_id}, report {report_id}")
        
        # Get workflow status from Temporal
        workflow_status = await temporal_client.get_workflow_status(workflow_id)
        
        return {
            "message": "Workflow started successfully",
            "workflow_id": workflow_id,
            "status": "started",
            "workflow_status": workflow_status,
            "phases_created": len(created_phases),
            "phase_names": created_phases
        }
        
    except Exception as e:
        logger.error(f"Failed to start workflow: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start workflow: {str(e)}"
        )


@router.get("/cycles/{cycle_id}/reports/{report_id}/workflow-status")
@require_permission("testing", "read")
async def get_workflow_status(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the status of a workflow for a specific report"""
    
    # Get the assignment to find workflow ID
    assignment_result = await db.execute(
        select(CycleReport).where(
            and_(
                CycleReport.cycle_id == cycle_id,
                CycleReport.report_id == report_id
            )
        )
    )
    assignment = assignment_result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report is not assigned to this cycle"
        )
    
    if not assignment.workflow_id:
        return {
            "workflow_exists": False,
            "message": "No workflow has been started for this report"
        }
    
    try:
        temporal_client = await get_temporal_client()
        workflow_status = await temporal_client.get_workflow_status(assignment.workflow_id)
        
        return {
            "workflow_exists": True,
            "workflow_id": assignment.workflow_id,
            "workflow_status": workflow_status
        }
        
    except Exception as e:
        logger.error(f"Failed to get workflow status: {str(e)}")
        return {
            "workflow_exists": True,
            "workflow_id": assignment.workflow_id,
            "error": str(e)
        }


@router.post("/cycles/{cycle_id}/reports/{report_id}/phases/{phase_name}/dates")
@require_permission("testing", "execute")
async def set_phase_dates(
    cycle_id: int,
    report_id: int,
    phase_name: str,
    phase_dates: PhaseDateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Set start and end dates for a specific workflow phase"""
    
    # Verify the phase exists
    phase_result = await db.execute(
        select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == phase_name
            )
        )
    )
    phase = phase_result.scalar_one_or_none()
    
    if not phase:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Phase '{phase_name}' not found for this report"
        )
    
    # Validate dates
    if phase_dates.end_date < phase_dates.start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date must be after start date"
        )
    
    # Update phase dates
    phase.planned_start_date = phase_dates.start_date
    phase.planned_end_date = phase_dates.end_date
    phase.updated_at = datetime.utcnow()
    
    await db.commit()
    
    logger.info(f"Updated dates for phase {phase_name} in cycle {cycle_id}, report {report_id}")
    
    return {
        "message": "Phase dates updated successfully",
        "phase_name": phase_name,
        "start_date": phase_dates.start_date.isoformat(),
        "end_date": phase_dates.end_date.isoformat()
    }