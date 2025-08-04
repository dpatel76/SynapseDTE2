"""API endpoints for sending signals to Temporal workflows"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime
from pydantic import BaseModel

from app.core.dependencies import get_current_user
from app.models.user import User
from app.core.auth import RoleChecker
from app.temporal.client import get_temporal_client
from app.core.logging import get_logger
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)
router = APIRouter()


class WorkflowSignalRequest(BaseModel):
    """Request model for sending workflow signals"""
    signal_name: str
    data: Dict[str, Any]
    
    class Config:
        json_schema_extra = {
            "example": {
                "signal_name": "submit_tester_review",
                "data": {
                    "attribute_decisions": [
                        {
                            "attribute_id": 123,
                            "action": "approve",
                            "notes": "Looks good"
                        }
                    ]
                }
            }
        }


class HumanInput(BaseModel):
    """Standard format for human input signals"""
    input_type: str
    data: Dict[str, Any]
    user_id: int
    timestamp: str


async def check_user_can_perform_action(
    action: str,
    user: User,
    db: AsyncSession
) -> bool:
    """Check if user has permission to perform the awaited action"""
    if not action or action not in SIGNAL_PERMISSIONS:
        return False
    
    from app.services.permission_service import get_permission_service
    permission_service = await get_permission_service(db)
    
    required_permissions = SIGNAL_PERMISSIONS[action]
    for permission_string in required_permissions:
        resource, action_name = permission_string.split('.')
        try:
            if await permission_service.check_permission(
                user.user_id,
                resource,
                action_name
            ):
                return True
        except Exception:
            continue
    
    return False


# Signal name to permission mapping
SIGNAL_PERMISSIONS = {
    # Planning phase
    "submit_planning_documents": ["planning.upload_documents"],
    "submit_planning_attributes": ["planning.create_attributes"],
    
    # Scoping phase
    "submit_tester_review": ["scoping.review_attributes"],
    "submit_report_owner_approval": ["scoping.approve_attributes"],
    
    # CycleReportSampleSelectionSamples Selection phase
    "submit_selection_criteria": ["sample_selection.define_criteria"],
    "submit_sample_approval": ["sample_selection.approve_samples"],
    
    # Data Provider phase
    "submit_dp_assignment_review": ["data_provider.review_assignments"],
    
    # Request Info phase
    "submit_rfi_responses": ["request_info.track_responses"],
    
    # Test Execution phase
    "submit_document_tests": ["test_execution.execute_tests"],
    "submit_database_tests": ["test_execution.execute_tests"],
    
    # Observation phase
    "submit_observations": ["observations.create"],
    "submit_observation_review": ["observations.review"],
    
    # Test Report phase
    "submit_report_review": ["test_report.review"]
}


@router.post("/workflow/{workflow_id}/signal/{signal_name}")
async def send_workflow_signal(
    workflow_id: str,
    signal_name: str,
    request: WorkflowSignalRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Send a signal to a Temporal workflow
    
    This endpoint allows users to send signals to running workflows for
    human-in-the-loop activities like reviews, approvals, and data submission.
    """
    try:
        # Check if signal is valid
        if signal_name not in SIGNAL_PERMISSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid signal name: {signal_name}"
            )
        
        # Check permissions
        required_permissions = SIGNAL_PERMISSIONS[signal_name]
        
        # Use the permission service to check permissions
        from app.services.permission_service import get_permission_service
        permission_service = await get_permission_service(db)
        
        # Check each required permission
        has_permission = False
        for permission_string in required_permissions:
            resource, action = permission_string.split('.')
            try:
                if await permission_service.check_permission(
                    current_user.user_id,
                    resource,
                    action
                ):
                    has_permission = True
                    break
            except Exception:
                continue
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: requires one of {required_permissions}"
            )
        
        # Get Temporal client
        temporal_client = await get_temporal_client()
        
        # Get workflow handle
        try:
            handle = temporal_client.get_workflow_handle(workflow_id)
        except Exception as e:
            logger.error(f"Failed to get workflow handle: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found"
            )
        
        # Prepare signal data
        human_input = HumanInput(
            input_type=signal_name,
            data=request.data,
            user_id=current_user.user_id,
            timestamp=datetime.utcnow().isoformat()
        )
        
        # Send signal
        await handle.signal(signal_name, human_input.dict())
        
        logger.info(
            f"Signal {signal_name} sent to workflow {workflow_id} by user {current_user.user_id}"
        )
        
        return {
            "status": "success",
            "message": f"Signal {signal_name} sent successfully",
            "workflow_id": workflow_id,
            "timestamp": human_input.timestamp
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send workflow signal: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send workflow signal"
        )


@router.get("/workflow/{workflow_id}/status")
async def get_workflow_status(
    workflow_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Query workflow status
    
    Returns the current phase, awaiting action, and phase results.
    """
    try:
        # Get Temporal client
        temporal_client = await get_temporal_client()
        
        # Get workflow handle
        try:
            handle = temporal_client.get_workflow_handle(workflow_id)
        except Exception as e:
            logger.error(f"Failed to get workflow handle: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found"
            )
        
        # Query workflow status
        status = await handle.query("get_current_status")
        
        return {
            "workflow_id": workflow_id,
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to query workflow status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to query workflow status"
        )


@router.get("/workflow/{workflow_id}/awaiting-action")
async def get_awaiting_action(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get the action the workflow is currently waiting for
    
    Returns the specific human action needed to progress the workflow.
    """
    try:
        # Get Temporal client
        temporal_client = await get_temporal_client()
        
        # Get workflow handle
        try:
            handle = temporal_client.get_workflow_handle(workflow_id)
        except Exception as e:
            logger.error(f"Failed to get workflow handle: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found"
            )
        
        # Query awaiting action
        awaiting_action = await handle.query("get_awaiting_action")
        
        return {
            "workflow_id": workflow_id,
            "awaiting_action": awaiting_action,
            "can_perform_action": await check_user_can_perform_action(
                awaiting_action, current_user, db
            ),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to query awaiting action: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to query awaiting action"
        )


# Signal-specific endpoints for better UX

@router.post("/workflow/{workflow_id}/planning/upload-documents")
async def upload_planning_documents(
    workflow_id: str,
    documents: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Upload planning phase documents"""
    return await send_workflow_signal(
        workflow_id=workflow_id,
        signal_name="submit_planning_documents",
        request=WorkflowSignalRequest(
            signal_name="submit_planning_documents",
            data={"documents": documents}
        ),
        current_user=current_user
    )


@router.post("/workflow/{workflow_id}/scoping/tester-review")
async def submit_tester_review(
    workflow_id: str,
    attribute_decisions: list,
    current_user: User = Depends(get_current_user)
):
    """Submit tester attribute review decisions"""
    return await send_workflow_signal(
        workflow_id=workflow_id,
        signal_name="submit_tester_review",
        request=WorkflowSignalRequest(
            signal_name="submit_tester_review",
            data={"attribute_decisions": attribute_decisions}
        ),
        current_user=current_user
    )


@router.post("/workflow/{workflow_id}/scoping/report-owner-approval")
async def submit_report_owner_approval(
    workflow_id: str,
    approval_decision: str,
    attribute_decisions: Optional[list] = None,
    current_user: User = Depends(get_current_user)
):
    """Submit report owner approval decision"""
    return await send_workflow_signal(
        workflow_id=workflow_id,
        signal_name="submit_report_owner_approval",
        request=WorkflowSignalRequest(
            signal_name="submit_report_owner_approval",
            data={
                "approval_decision": approval_decision,
                "attribute_decisions": attribute_decisions
            }
        ),
        current_user=current_user
    )