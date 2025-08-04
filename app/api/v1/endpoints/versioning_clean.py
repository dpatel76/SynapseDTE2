"""
Clean versioning service without backward compatibility
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from temporalio.client import Client
import uuid

from app.models.versioning_clean import (
    VersionStatus, ApprovalStatus,
    PlanningVersion, SampleSelectionVersion,
    ObservationVersion, TestReportVersion
)
from app.workflows.clean_test_cycle_workflow import CleanTestCycleWorkflow
from app.workflows.signals import ApprovalSignal, RevisionSignal
from app.core.database import get_async_session
from app.core.temporal import get_temporal_client
from app.core.logger import logger


class CleanVersioningService:
    """Service for managing versions through Temporal workflows"""
    
    def __init__(self, db: AsyncSession, temporal_client: Client):
        self.db = db
        self.temporal_client = temporal_client
    
    async def start_test_cycle_workflow(
        self,
        cycle_id: int,
        report_id: int,
        user_id: int,
        initial_data: Dict[str, Any]
    ) -> str:
        """Start a new test cycle workflow"""
        workflow_id = f"test-cycle-{cycle_id}-{report_id}-{uuid.uuid4()}"
        
        handle = await self.temporal_client.start_workflow(
            CleanTestCycleWorkflow.run,
            {
                "cycle_id": cycle_id,
                "report_id": report_id,
                "user_id": user_id,
                **initial_data
            },
            id=workflow_id,
            task_queue="versioning-queue"
        )
        
        logger.info(f"Started workflow {workflow_id} for cycle {cycle_id}")
        return workflow_id
    
    async def approve_version(
        self,
        workflow_id: str,
        phase: str,
        version_id: str,
        user_id: int,
        notes: Optional[str] = None
    ) -> None:
        """Send approval signal to workflow"""
        handle = self.temporal_client.get_workflow_handle(workflow_id)
        
        signal = ApprovalSignal(
            phase=phase,
            version_id=version_id,
            user_id=user_id,
            approved=True,
            notes=notes,
            timestamp=datetime.utcnow()
        )
        
        await handle.signal("approval_signal", signal)
        logger.info(f"Sent approval for {phase} version {version_id}")
    
    async def request_revision(
        self,
        workflow_id: str,
        phase: str,
        version_id: str,
        user_id: int,
        revision_reason: str,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Request revision for a version"""
        handle = self.temporal_client.get_workflow_handle(workflow_id)
        
        signal = RevisionSignal(
            phase=phase,
            version_id=version_id,
            user_id=user_id,
            reason=revision_reason,
            additional_data=additional_data or {},
            timestamp=datetime.utcnow()
        )
        
        await handle.signal("revision_signal", signal)
        logger.info(f"Requested revision for {phase} version {version_id}")
    
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get current workflow status"""
        handle = self.temporal_client.get_workflow_handle(workflow_id)
        
        phase_status = await handle.query("get_phase_status")
        phase_versions = await handle.query("get_phase_versions")
        
        return {
            "workflow_id": workflow_id,
            "phase_status": phase_status,
            "phase_versions": phase_versions
        }
    
    async def get_current_version(
        self,
        cycle_id: int,
        report_id: int,
        phase: str
    ) -> Optional[Dict[str, Any]]:
        """Get current approved version for a phase"""
        # Map phase to model
        model_map = {
            "Planning": PlanningVersion,
            "CycleReportSampleSelectionSamples Selection": SampleSelectionVersion,
            "Observation Management": ObservationVersion,
            "Finalize Test Report": TestReportVersion
        }
        
        if phase not in model_map:
            return None
        
        model = model_map[phase]
        
        result = await self.db.execute(
            select(model)
            .where(
                and_(
                    model.cycle_id == cycle_id,
                    model.report_id == report_id,
                    model.version_status == VersionStatus.APPROVED
                )
            )
            .order_by(model.version_number.desc())
        )
        
        version = result.scalar()
        
        if version:
            return {
                "version_id": str(version.version_id),
                "version_number": version.version_number,
                "status": version.version_status.value,
                "created_at": version.created_at.isoformat(),
                "approved_at": version.approved_at.isoformat() if version.approved_at else None
            }
        
        return None
    
    async def get_sample_decisions(
        self,
        version_id: str,
        status_filter: Optional[ApprovalStatus] = None
    ) -> List[Dict[str, Any]]:
        """Get sample decisions for a version"""
        from app.models.versioning_clean import SampleDecision
        
        query = select(SampleDecision).where(
            SampleDecision.version_id == uuid.UUID(version_id)
        )
        
        if status_filter:
            query = query.where(SampleDecision.decision_status == status_filter)
        
        result = await self.db.execute(query)
        decisions = result.scalars().all()
        
        return [
            {
                "decision_id": str(d.decision_id),
                "sample_identifier": d.sample_identifier,
                "sample_data": d.sample_data,
                "status": d.decision_status.value,
                "source": d.source.value,
                "carried_forward": d.carried_from_version_id is not None
            }
            for d in decisions
        ]
    
    async def submit_report_signoff(
        self,
        workflow_id: str,
        version_id: str,
        role: str,
        user_id: int,
        approved: bool,
        notes: Optional[str] = None
    ) -> None:
        """Submit report signoff"""
        handle = self.temporal_client.get_workflow_handle(workflow_id)
        
        signal = ApprovalSignal(
            phase="Finalize Test Report",
            version_id=version_id,
            user_id=user_id,
            approved=approved,
            notes=notes,
            metadata={"signoff_role": role},
            timestamp=datetime.utcnow()
        )
        
        await handle.signal("approval_signal", signal)
        logger.info(f"Submitted {role} signoff for report version {version_id}")


# FastAPI endpoints
from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.dependencies import get_db, get_temporal_client
from app.core.auth import get_current_user
from app.schemas.versioning_clean import (
    WorkflowStartRequest, ApprovalRequest,
    RevisionRequest, SignoffRequest
)

router = APIRouter()


@router.post("/workflows/start")
async def start_workflow(
    request: WorkflowStartRequest,
    db: AsyncSession = Depends(get_db),
    temporal: Client = Depends(get_temporal_client),
    current_user: Dict = Depends(get_current_user)
):
    """Start a new test cycle workflow"""
    service = CleanVersioningService(db, temporal)
    
    workflow_id = await service.start_test_cycle_workflow(
        cycle_id=request.cycle_id,
        report_id=request.report_id,
        user_id=current_user["user_id"],
        initial_data=request.initial_data
    )
    
    return {"workflow_id": workflow_id}


@router.get("/workflows/{workflow_id}/status")
async def get_workflow_status(
    workflow_id: str,
    db: AsyncSession = Depends(get_db),
    temporal: Client = Depends(get_temporal_client)
):
    """Get workflow status"""
    service = CleanVersioningService(db, temporal)
    
    try:
        status = await service.get_workflow_status(workflow_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Workflow not found: {str(e)}")


@router.post("/workflows/{workflow_id}/approve")
async def approve_version(
    workflow_id: str,
    request: ApprovalRequest,
    db: AsyncSession = Depends(get_db),
    temporal: Client = Depends(get_temporal_client),
    current_user: Dict = Depends(get_current_user)
):
    """Approve a version"""
    service = CleanVersioningService(db, temporal)
    
    await service.approve_version(
        workflow_id=workflow_id,
        phase=request.phase,
        version_id=request.version_id,
        user_id=current_user["user_id"],
        notes=request.notes
    )
    
    return {"status": "approved"}


@router.post("/workflows/{workflow_id}/revise")
async def request_revision(
    workflow_id: str,
    request: RevisionRequest,
    db: AsyncSession = Depends(get_db),
    temporal: Client = Depends(get_temporal_client),
    current_user: Dict = Depends(get_current_user)
):
    """Request revision"""
    service = CleanVersioningService(db, temporal)
    
    await service.request_revision(
        workflow_id=workflow_id,
        phase=request.phase,
        version_id=request.version_id,
        user_id=current_user["user_id"],
        revision_reason=request.reason,
        additional_data=request.additional_data
    )
    
    return {"status": "revision_requested"}


@router.get("/versions/current")
async def get_current_version(
    cycle_id: int = Query(...),
    report_id: int = Query(...),
    phase: str = Query(...),
    db: AsyncSession = Depends(get_db),
    temporal: Client = Depends(get_temporal_client)
):
    """Get current approved version for a phase"""
    service = CleanVersioningService(db, temporal)
    
    version = await service.get_current_version(cycle_id, report_id, phase)
    
    if not version:
        raise HTTPException(status_code=404, detail="No approved version found")
    
    return version


@router.get("/versions/{version_id}/samples")
async def get_sample_decisions(
    version_id: str,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    temporal: Client = Depends(get_temporal_client)
):
    """Get sample decisions for a version"""
    service = CleanVersioningService(db, temporal)
    
    status_filter = ApprovalStatus(status) if status else None
    
    decisions = await service.get_sample_decisions(version_id, status_filter)
    
    return {"decisions": decisions, "total": len(decisions)}


@router.post("/workflows/{workflow_id}/signoff")
async def submit_signoff(
    workflow_id: str,
    request: SignoffRequest,
    db: AsyncSession = Depends(get_db),
    temporal: Client = Depends(get_temporal_client),
    current_user: Dict = Depends(get_current_user)
):
    """Submit report signoff"""
    service = CleanVersioningService(db, temporal)
    
    await service.submit_report_signoff(
        workflow_id=workflow_id,
        version_id=request.version_id,
        role=request.role,
        user_id=current_user["user_id"],
        approved=request.approved,
        notes=request.notes
    )
    
    return {"status": "signoff_submitted"}