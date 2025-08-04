#!/usr/bin/env python
"""Start a Temporal workflow for a specific report in a test cycle"""

import asyncio
import logging
from app.temporal.client import get_temporal_client
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def start_workflow_for_report():
    """Start workflow for report 156 in cycle 9"""
    try:
        # Get the Temporal client
        client = await get_temporal_client()
        logger.info("Connected to Temporal")
        
        # Use the existing cycle and report
        cycle_id = 9  # Existing test cycle
        report_id = 156  # Existing report 
        user_id = 3   # Tester user ID
        
        # Start the workflow for this specific report
        workflow_id = await client.start_testing_workflow(
            cycle_id=cycle_id,
            report_id=report_id,
            user_id=user_id,
            metadata={
                "started_at": datetime.utcnow().isoformat(),
                "started_by": "manual_start_script",
                "report_name": "Sample Report for Testing"
            }
        )
        
        logger.info(f"Successfully started workflow: {workflow_id}")
        
        # Update the test_cycles table with workflow_id
        # Note: In production, this would be done by the service layer
        logger.info(f"Workflow ID to store: {workflow_id}")
        
        # Get workflow status
        status = await client.get_workflow_status(workflow_id)
        logger.info(f"Workflow status: {status}")
        
        return workflow_id
        
    except Exception as e:
        logger.error(f"Failed to start workflow: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    workflow_id = asyncio.run(start_workflow_for_report())
    print(f"\nWorkflow started with ID: {workflow_id}")
    print(f"Monitor the worker logs to see workflow progress")