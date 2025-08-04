"""Workflow Service for managing Temporal workflows"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from temporalio.client import Client
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.temporal.shared import TestCycleWorkflowInput
from app.temporal.shared.constants import TASK_QUEUE_WORKFLOW
from app.temporal.workflows.enhanced_test_cycle_workflow import EnhancedTestCycleWorkflow
# from app.temporal.workflows.enhanced_test_cycle_workflow_v2 import EnhancedTestCycleWorkflowV2
from app.models import TestCycle, Report, CycleReport, User
from app.models.workflow_tracking import WorkflowExecution
from app.temporal.workflow_versioning import (
    WorkflowVersionManager, 
    create_versioned_workflow_id,
    get_workflow_version_from_id
)

logger = logging.getLogger(__name__)


class WorkflowService:
    """Service for managing workflow execution"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._client: Optional[Client] = None
    
    async def get_client(self) -> Client:
        """Get or create Temporal client"""
        if not self._client:
            self._client = await Client.connect(
                settings.temporal_host or "localhost:7233",
                namespace=settings.temporal_namespace or "default"
            )
        return self._client
    
    async def start_test_cycle_workflow(
        self,
        cycle_id: int,
        user_id: int,
        report_ids: Optional[List[int]] = None,
        skip_phases: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Start a new test cycle workflow"""
        
        try:
            # Validate cycle exists
            cycle = await self.db.get(TestCycle, cycle_id)
            if not cycle:
                raise ValueError(f"Test cycle {cycle_id} not found")
            
            # Get report IDs if not provided
            if not report_ids:
                cycle_reports = await self.db.execute(
                    select(CycleReport.report_id).where(
                        CycleReport.cycle_id == cycle_id
                    )
                )
                report_ids = [row[0] for row in cycle_reports]
            
            if not report_ids:
                raise ValueError(f"No reports found for cycle {cycle_id}")
            
            # Create workflow input
            workflow_input = TestCycleWorkflowInput(
                cycle_id=cycle_id,
                initiated_by_user_id=user_id,
                report_ids=report_ids,
                auto_assign_testers=True,
                auto_generate_attributes=True,
                skip_phases=skip_phases or [],
                metadata=metadata or {}
            )
            
            # Get version manager
            version_manager = WorkflowVersionManager()
            current_version = version_manager.current_version.value
            
            # Generate versioned workflow ID
            base_workflow_id = f"test-cycle-{cycle_id}-{datetime.utcnow().timestamp()}"
            workflow_id = create_versioned_workflow_id(base_workflow_id, current_version)
            
            # Add version to metadata
            if not workflow_input.metadata:
                workflow_input.metadata = {}
            workflow_input.metadata["workflow_version"] = current_version
            
            # Get Temporal client
            client = await self.get_client()
            
            # Use V2 workflow based on configuration
            use_v2_workflow = (
                settings.use_dynamic_workflows and 
                settings.workflow_version == "v2"
            ) or metadata.get("use_v2_workflow", False)
            
            if use_v2_workflow:
                # Start V2 workflow with dynamic activities
                handle = await client.start_workflow(
                    EnhancedTestCycleWorkflow.run,
                    workflow_input,
                    id=workflow_id,
                    task_queue=TASK_QUEUE_WORKFLOW,
                    memo={"workflow_version": current_version, "workflow_type": "v2"}
                )
            else:
                # Start legacy workflow
                handle = await client.start_workflow(
                    EnhancedTestCycleWorkflow.run,
                    workflow_input,
                    id=workflow_id,
                    task_queue=TASK_QUEUE_WORKFLOW,
                    memo={"workflow_version": current_version}
                )
            
            logger.info(f"Started workflow {workflow_id} for cycle {cycle_id}")
            
            return {
                "workflow_id": workflow_id,
                "run_id": handle.result_run_id,
                "cycle_id": cycle_id,
                "report_ids": report_ids,
                "status": "started"
            }
            
        except Exception as e:
            logger.error(f"Failed to start workflow: {str(e)}")
            raise
    
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get current status of a workflow"""
        
        try:
            # Get from database first
            result = await self.db.execute(
                select(WorkflowExecution).where(
                    WorkflowExecution.workflow_id == workflow_id
                )
            )
            execution = result.scalar_one_or_none()
            
            if not execution:
                # Try to get from Temporal
                client = await self.get_client()
                handle = client.get_workflow_handle(workflow_id)
                
                # Query workflow state
                description = await handle.describe()
                
                return {
                    "workflow_id": workflow_id,
                    "status": description.status.name,
                    "started_at": description.start_time.isoformat() if description.start_time else None,
                    "execution_time": description.execution_time.isoformat() if description.execution_time else None
                }
            
            # Get current phase from database
            from app.models.workflow_tracking import WorkflowStep, StepType, WorkflowExecutionStatus
            
            current_phase_query = await self.db.execute(
                select(WorkflowStep.phase_name).where(
                    WorkflowStep.execution_id == execution.execution_id,
                    WorkflowStep.step_type == StepType.PHASE,
                    WorkflowStep.status == WorkflowExecutionStatus.RUNNING
                ).order_by(WorkflowStep.started_at.desc()).limit(1)
            )
            current_phase = current_phase_query.scalar()
            
            # Get completed phases
            completed_phases_query = await self.db.execute(
                select(WorkflowStep.phase_name).where(
                    WorkflowStep.execution_id == execution.execution_id,
                    WorkflowStep.step_type == StepType.PHASE,
                    WorkflowStep.status == WorkflowExecutionStatus.COMPLETED
                ).order_by(WorkflowStep.started_at)
            )
            completed_phases = [row[0] for row in completed_phases_query]
            
            return {
                "workflow_id": workflow_id,
                "execution_id": execution.execution_id,
                "status": execution.status,
                "current_phase": current_phase,
                "completed_phases": completed_phases,
                "started_at": execution.started_at.isoformat() if execution.started_at else None,
                "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
                "duration_seconds": execution.duration_seconds
            }
            
        except Exception as e:
            logger.error(f"Failed to get workflow status: {str(e)}")
            raise
    
    async def cancel_workflow(self, workflow_id: str, reason: str) -> Dict[str, Any]:
        """Cancel a running workflow"""
        
        try:
            client = await self.get_client()
            handle = client.get_workflow_handle(workflow_id)
            
            # Cancel the workflow
            await handle.cancel()
            
            # Update database status
            result = await self.db.execute(
                select(WorkflowExecution).where(
                    WorkflowExecution.workflow_id == workflow_id
                )
            )
            execution = result.scalar_one_or_none()
            
            if execution:
                from app.models.workflow_tracking import WorkflowExecutionStatus
                execution.status = WorkflowExecutionStatus.CANCELLED
                execution.completed_at = datetime.utcnow()
                execution.error_details = {"cancellation_reason": reason}
                await self.db.commit()
            
            logger.info(f"Cancelled workflow {workflow_id}: {reason}")
            
            return {
                "workflow_id": workflow_id,
                "status": "cancelled",
                "reason": reason
            }
            
        except Exception as e:
            logger.error(f"Failed to cancel workflow: {str(e)}")
            raise
    
    async def get_active_workflows_for_cycle(self, cycle_id: int) -> List[Dict[str, Any]]:
        """Get all active workflows for a test cycle"""
        
        from app.models.workflow_tracking import WorkflowExecutionStatus
        
        result = await self.db.execute(
            select(WorkflowExecution).where(
                WorkflowExecution.cycle_id == cycle_id,
                WorkflowExecution.status.in_([
                    WorkflowExecutionStatus.PENDING,
                    WorkflowExecutionStatus.RUNNING
                ])
            )
        )
        
        workflows = []
        for execution in result.scalars():
            workflows.append({
                "workflow_id": execution.workflow_id,
                "execution_id": execution.execution_id,
                "status": execution.status,
                "started_at": execution.started_at.isoformat() if execution.started_at else None
            })
        
        return workflows
    
    async def retry_failed_phase(
        self,
        workflow_id: str,
        phase_name: str,
        user_id: int
    ) -> Dict[str, Any]:
        """Retry a failed phase in a workflow"""
        
        # This would require implementing workflow signals or starting a new workflow
        # from the failed phase. For now, return a placeholder
        
        logger.info(f"Retry requested for phase {phase_name} in workflow {workflow_id}")
        
        return {
            "workflow_id": workflow_id,
            "phase": phase_name,
            "status": "retry_not_implemented",
            "message": "Phase retry functionality will be implemented with workflow signals"
        }


# Convenience function to get service instance
async def get_workflow_service(db: AsyncSession) -> WorkflowService:
    """Get workflow service instance"""
    return WorkflowService(db)