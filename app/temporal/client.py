"""
Temporal Client for SynapseDTE
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import timedelta, datetime
from temporalio.client import Client
from temporalio.common import RetryPolicy

from app.core.config import settings
from app.temporal.workflows.test_cycle_workflow_reconciled import (
    TestCycleWorkflowReconciled,
    TestCycleWorkflowInput as WorkflowInput
)

logger = logging.getLogger(__name__)

class TemporalClient:
    """Client for interacting with Temporal workflows"""
    
    def __init__(self):
        self.client: Optional[Client] = None
        self.task_queue = "test-cycle-queue"
        
    async def connect(self):
        """Connect to Temporal server"""
        if not self.client:
            self.client = await Client.connect(
                settings.TEMPORAL_HOST or "localhost:7233",
                namespace=settings.TEMPORAL_NAMESPACE or "default"
            )
            logger.info("Connected to Temporal server")
    
    async def start_testing_workflow(
        self,
        cycle_id: int,
        report_id: int,
        user_id: int,
        metadata: Dict[str, Any] = None
    ) -> str:
        """Start a new regulatory testing workflow for a single report
        
        Note: Each report in a test cycle gets its own workflow instance.
        The workflow ID includes both cycle_id and report_id to ensure uniqueness.
        """
        await self.connect()
        
        workflow_id = f"test-cycle-{cycle_id}-report-{report_id}"
        
        # First check if workflow already exists
        try:
            handle = self.client.get_workflow_handle(workflow_id)
            description = await handle.describe()
            
            # If we get here, workflow exists
            status = description.status.name
            if status in ["RUNNING", "PENDING"]:
                logger.info(f"Workflow {workflow_id} already exists with status {status}")
                return workflow_id
            elif status in ["COMPLETED", "FAILED", "CANCELED", "TERMINATED"]:
                logger.warning(f"Workflow {workflow_id} exists but has status {status}. Creating new workflow with different ID.")
                # Append timestamp to make unique
                workflow_id = f"{workflow_id}-{int(datetime.now().timestamp())}"
        except Exception as e:
            # Workflow doesn't exist, we can create it
            logger.debug(f"Workflow {workflow_id} not found, will create new workflow")
        
        # Prepare workflow input
        workflow_input = WorkflowInput(
            cycle_id=cycle_id,
            report_id=report_id,
            user_id=user_id,
            skip_phases=None
        )
        
        # Start workflow execution
        handle = await self.client.start_workflow(
            TestCycleWorkflowReconciled.run,
            workflow_input,
            id=workflow_id,
            task_queue=self.task_queue,
            execution_timeout=timedelta(days=30),  # 30 day timeout for entire workflow
            retry_policy=RetryPolicy(
                maximum_attempts=3,
                initial_interval=timedelta(seconds=1),
                maximum_interval=timedelta(seconds=10)
            )
        )
        
        logger.info(f"Started workflow {workflow_id}")
        return workflow_id
    
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get the status of a workflow"""
        await self.connect()
        
        handle = self.client.get_workflow_handle(workflow_id)
        description = await handle.describe()
        
        return {
            "workflow_id": workflow_id,
            "status": description.status.name,
            "start_time": description.start_time,
            "close_time": description.close_time,
            "execution_time": description.execution_time
        }
    
    async def signal_workflow(
        self, 
        workflow_id: str, 
        signal_name: str,
        signal_data: Dict[str, Any] = None
    ):
        """Send a signal to a running workflow"""
        await self.connect()
        
        handle = self.client.get_workflow_handle(workflow_id)
        await handle.signal(signal_name, signal_data or {})
        
        logger.info(f"Sent signal {signal_name} to workflow {workflow_id}")
    
    async def cancel_workflow(self, workflow_id: str):
        """Cancel a running workflow"""
        await self.connect()
        
        handle = self.client.get_workflow_handle(workflow_id)
        await handle.cancel()
        
        logger.info(f"Cancelled workflow {workflow_id}")
    
    async def get_workflow_result(self, workflow_id: str) -> Dict[str, Any]:
        """Get the result of a completed workflow"""
        await self.connect()
        
        handle = self.client.get_workflow_handle(workflow_id)
        result = await handle.result()
        
        return result
    
    async def start_workflows_for_cycle(
        self,
        cycle_id: int,
        report_ids: List[int],
        user_id: int,
        metadata: Dict[str, Any] = None
    ) -> List[str]:
        """Start workflows for all reports in a test cycle
        
        Args:
            cycle_id: The test cycle ID
            report_ids: List of report IDs in this cycle
            user_id: User starting the workflows
            metadata: Optional metadata for all workflows
            
        Returns:
            List of workflow IDs, one for each report
        """
        workflow_ids = []
        
        for report_id in report_ids:
            workflow_id = await self.start_testing_workflow(
                cycle_id=cycle_id,
                report_id=report_id,
                user_id=user_id,
                metadata=metadata
            )
            workflow_ids.append(workflow_id)
            logger.info(f"Started workflow for report {report_id}: {workflow_id}")
        
        logger.info(f"Started {len(workflow_ids)} workflows for cycle {cycle_id}")
        return workflow_ids

# Global client instance
temporal_client = TemporalClient()

async def get_temporal_client() -> TemporalClient:
    """Get the global Temporal client instance"""
    await temporal_client.connect()
    return temporal_client