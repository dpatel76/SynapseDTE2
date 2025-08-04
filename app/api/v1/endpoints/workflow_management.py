"""Workflow Management API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.api.v1.deps import get_current_user, get_db
from app.models.user import User
from app.services.workflow_service import WorkflowService
from app.core.auth import RoleChecker
from app.temporal.shared import WORKFLOW_PHASES
from app.core.dependencies import require_roles

router = APIRouter()


@router.post("/start/{cycle_id}")
async def start_workflow(
    cycle_id: int,
    report_ids: Optional[List[int]] = None,
    skip_phases: Optional[List[str]] = None,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Start a new test cycle workflow"""
    
    # Validate skip phases if provided
    if skip_phases:
        invalid_phases = [p for p in skip_phases if p not in WORKFLOW_PHASES]
        if invalid_phases:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid phase names: {', '.join(invalid_phases)}"
            )
    
    service = WorkflowService(db)
    
    try:
        result = await service.start_test_cycle_workflow(
            cycle_id=cycle_id,
            user_id=current_user.user_id,
            report_ids=report_ids,
            skip_phases=skip_phases,
            metadata={
                "initiated_by": current_user.email,
                "initiated_at": datetime.utcnow().isoformat()
            }
        )
        
        return {
            "message": "Workflow started successfully",
            "workflow": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start workflow: {str(e)}"
        )


@router.get("/status/{workflow_id}")
async def get_workflow_status(
    workflow_id: str,
    current_user: User = Depends(require_roles(["Tester", "Test Manager", "Report Owner Executive"])),
    db = Depends(get_db)
):
    """Get current status of a workflow"""
    
    service = WorkflowService(db)
    
    try:
        status = await service.get_workflow_status(workflow_id)
        return status
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get workflow status: {str(e)}"
        )


@router.get("/cycle/{cycle_id}/workflows")
async def get_cycle_workflows(
    cycle_id: int,
    current_user: User = Depends(require_roles(["Tester", "Test Manager", "Report Owner Executive"])),
    db = Depends(get_db)
):
    """Get all workflows for a test cycle"""
    
    service = WorkflowService(db)
    
    try:
        workflows = await service.get_active_workflows_for_cycle(cycle_id)
        return {
            "cycle_id": cycle_id,
            "count": len(workflows),
            "workflows": workflows
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get workflows: {str(e)}"
        )


@router.post("/cancel/{workflow_id}")
async def cancel_workflow(
    workflow_id: str,
    reason: str,
    current_user: User = Depends(require_roles(["Test Manager"])),
    db = Depends(get_db)
):
    """Cancel a running workflow"""
    
    if not reason:
        raise HTTPException(
            status_code=400,
            detail="Cancellation reason is required"
        )
    
    service = WorkflowService(db)
    
    try:
        result = await service.cancel_workflow(
            workflow_id=workflow_id,
            reason=f"{reason} (cancelled by {current_user.email})"
        )
        
        return {
            "message": "Workflow cancelled successfully",
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel workflow: {str(e)}"
        )


@router.post("/phase/start/{cycle_id}/{report_id}/{phase_name}")
async def start_phase_manually(
    cycle_id: int,
    report_id: int,
    phase_name: str,
    current_user: User = Depends(require_roles(["Tester", "Test Manager"])),
    db = Depends(get_db)
):
    """Manually start a specific phase (outside of workflow)"""
    
    if phase_name not in WORKFLOW_PHASES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid phase name. Must be one of: {', '.join(WORKFLOW_PHASES)}"
        )
    
    # Import the appropriate start activity based on phase
    activity_map = {
        "Planning": "start_planning_phase_activity",
        "Scoping": "start_scoping_phase_activity",
        "CycleReportSampleSelectionSamples Selection": "start_sample_selection_phase_activity",
        "Data Owner Identification": "start_data_owner_identification_phase_activity",
        "Request for Information": "start_request_info_phase_activity",
        "Test Execution": "start_test_execution_phase_activity",
        "Observation Management": "start_observation_management_phase_activity",
        "Finalize Test Report": "start_finalize_report_phase_activity"
    }
    
    activity_name = activity_map.get(phase_name)
    if not activity_name:
        raise HTTPException(
            status_code=400,
            detail=f"No start activity found for phase: {phase_name}"
        )
    
    # Execute the activity directly (outside of workflow)
    # This would typically be done through Temporal, but for manual execution:
    
    try:
        # Dynamic import of the activity
        if phase_name == "Planning":
            from app.temporal.activities.planning_activities import start_planning_phase_activity
            result = await start_planning_phase_activity(cycle_id, report_id, current_user.user_id)
        elif phase_name == "Scoping":
            from app.temporal.activities.scoping_activities import start_scoping_phase_activity
            result = await start_scoping_phase_activity(cycle_id, report_id, current_user.user_id)
        # ... (continue for other phases)
        else:
            raise HTTPException(
                status_code=501,
                detail=f"Manual start not implemented for phase: {phase_name}"
            )
        
        if result.success:
            return {
                "message": f"Phase {phase_name} started successfully",
                "phase_data": result.data
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to start phase: {result.error}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start phase: {str(e)}"
        )


@router.post("/phase/complete/{cycle_id}/{report_id}/{phase_name}")
async def complete_phase_manually(
    cycle_id: int,
    report_id: int,
    phase_name: str,
    completion_notes: Optional[str] = None,
    current_user: User = Depends(require_roles(["Tester", "Test Manager"])),
    db = Depends(get_db)
):
    """Manually complete a specific phase (outside of workflow)"""
    
    if phase_name not in WORKFLOW_PHASES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid phase name. Must be one of: {', '.join(WORKFLOW_PHASES)}"
        )
    
    # Similar implementation to start_phase_manually but for completion
    # This is a placeholder for manual phase completion
    
    return {
        "message": f"Manual phase completion for {phase_name} not fully implemented",
        "phase": phase_name,
        "notes": completion_notes
    }


@router.get("/phases")
async def get_workflow_phases(
    current_user: User = Depends(get_current_user)
):
    """Get list of all workflow phases and their dependencies"""
    
    from app.temporal.shared import PHASE_DEPENDENCIES
    
    phases = []
    for i, phase in enumerate(WORKFLOW_PHASES):
        phases.append({
            "order": i + 1,
            "name": phase,
            "dependencies": PHASE_DEPENDENCIES.get(phase, [])
        })
    
    return {
        "total_phases": len(phases),
        "phases": phases
    }