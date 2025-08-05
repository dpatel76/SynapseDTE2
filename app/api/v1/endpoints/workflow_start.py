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
from app.models.workflow_activity import WorkflowActivity, ActivityType, ActivityStatus
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
            for idx, phase_name in enumerate(phases, start=1):
                phase = WorkflowPhase(
                    cycle_id=cycle_id,
                    report_id=report_id,
                    phase_name=phase_name,
                    phase_order=idx,  # Add phase order starting from 1
                    status="Not Started",
                    state="Not Started",
                    schedule_status="On Track",
                    progress_percentage=0,  # Initialize to 0
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(phase)
                created_phases.append(phase_name)
        else:
            created_phases = [p.phase_name for p in existing_phases]
            logger.info(f"Workflow phases already exist for cycle {cycle_id}, report {report_id}")
        
        # Create activities for each phase
        await db.flush()  # Ensure phases have IDs
        
        # Define activities for each phase - matching the migration
        phase_activities = {
            "Planning": [
                ("Start Planning Phase", ActivityType.START, 1, True, False),
                ("Load Attributes", ActivityType.TASK, 2, True, False),
                ("Add Data Source", ActivityType.TASK, 3, True, True),  # optional
                ("Map PDEs", ActivityType.TASK, 4, True, True),  # optional
                ("Review & Approve Attributes", ActivityType.REVIEW, 5, True, False),
                ("Complete Planning Phase", ActivityType.COMPLETE, 6, False, False),
            ],
            "Scoping": [
                ("Start Scoping Phase", ActivityType.START, 1, False, False),
                ("Generate LLM Recommendations", ActivityType.TASK, 2, False, False),
                ("Make Scoping Decisions", ActivityType.TASK, 3, True, False),
                ("Report Owner Approval", ActivityType.APPROVAL, 4, True, False),
                ("Complete Scoping Phase", ActivityType.COMPLETE, 5, False, False),
            ],
            "Data Profiling": [
                ("Start Data Profiling Phase", ActivityType.START, 1, False, False),
                ("Upload Data Files", ActivityType.TASK, 2, True, False),
                ("Generate LLM Data Profiling Rules", ActivityType.TASK, 3, True, False),
                ("Review Profiling Rules", ActivityType.REVIEW, 4, True, False),
                ("Report Owner Rule Approval", ActivityType.APPROVAL, 5, True, False),
                ("Execute Data Profiling", ActivityType.TASK, 6, True, False),
                ("Complete Data Profiling Phase", ActivityType.COMPLETE, 7, False, False),
            ],
            "Data Provider ID": [
                ("Start Data Provider ID Phase", ActivityType.START, 1, False, False),
                ("Assign Data Providers", ActivityType.TASK, 2, True, False),
                ("Review Provider Assignments", ActivityType.TASK, 3, True, False),
                ("Complete Data Provider ID Phase", ActivityType.COMPLETE, 4, False, False),
            ],
            "Request Info": [
                ("Start Request Info Phase", ActivityType.START, 1, False, False),
                ("Create Test Cases", ActivityType.TASK, 2, True, False),
                ("Notify Data Providers", ActivityType.TASK, 3, True, False),
                ("Collect Documents", ActivityType.TASK, 4, True, False),
                ("Review Submissions", ActivityType.REVIEW, 5, True, False),
                ("Complete Request Info Phase", ActivityType.COMPLETE, 6, False, False),
            ],
            "Sample Selection": [
                ("Start Sample Selection", ActivityType.START, 1, False, False),
                ("Generate Samples", ActivityType.TASK, 2, True, False),
                ("Review Samples", ActivityType.REVIEW, 3, True, False),
                ("Approve Samples", ActivityType.APPROVAL, 4, True, False),
                ("Complete Sample Selection", ActivityType.COMPLETE, 5, False, False),
            ],
            "Testing": [  # This will be mapped to Test Execution
                ("Start Test Execution Phase", ActivityType.START, 1, False, False),
                ("Load Test Cases", ActivityType.TASK, 2, True, False),
                ("Execute Tests", ActivityType.TASK, 3, True, False),
                ("Complete Test Execution", ActivityType.COMPLETE, 4, False, False),
            ],
            "Observations": [
                ("Start Observations Phase", ActivityType.START, 1, False, False),
                ("Review Test Results", ActivityType.TASK, 2, True, False),
                ("Manage Observations", ActivityType.TASK, 3, True, False),
                ("Complete Observations", ActivityType.COMPLETE, 4, False, False),
            ],
            "Finalize Test Report": [
                ("Start Finalize Phase", ActivityType.START, 1, False, False),
                ("Generate Report", ActivityType.TASK, 2, True, False),
                ("Review Report", ActivityType.REVIEW, 3, True, False),
                ("Approve Report", ActivityType.APPROVAL, 4, True, False),
                ("Complete Report", ActivityType.COMPLETE, 5, False, False),
            ],
        }
        
        # Get all phases that were just created or already exist
        phases_result = await db.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id
                )
            )
        )
        all_phases = phases_result.scalars().all()
        
        # Create activities for each phase
        for phase in all_phases:
            # Check if activities already exist for this phase
            existing_activities_result = await db.execute(
                select(WorkflowActivity).where(
                    and_(
                        WorkflowActivity.phase_id == phase.phase_id,
                        WorkflowActivity.cycle_id == cycle_id,
                        WorkflowActivity.report_id == report_id
                    )
                )
            )
            existing_activities = existing_activities_result.scalars().all()
            
            if not existing_activities and phase.phase_name in phase_activities:
                activities = phase_activities[phase.phase_name]
                for activity_name, activity_type, order, is_manual, is_optional in activities:
                    activity = WorkflowActivity(
                        cycle_id=cycle_id,
                        report_id=report_id,
                        phase_id=phase.phase_id,
                        phase_name=phase.phase_name,
                        activity_name=activity_name,
                        activity_type=activity_type,
                        activity_order=order,
                        status=ActivityStatus.NOT_STARTED,
                        can_start=(order == 1),  # Only first activity can start initially
                        can_complete=False,
                        is_manual=is_manual,
                        is_optional=is_optional,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    db.add(activity)
        
        # Ensure everything is saved
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