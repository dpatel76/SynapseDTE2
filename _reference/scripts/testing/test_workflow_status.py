#!/usr/bin/env python
"""Simple test to check workflow status"""

import asyncio
import logging
from app.temporal.client import get_temporal_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_workflow_status():
    """Test workflow status queries"""
    try:
        # Get the Temporal client
        client = await get_temporal_client()
        logger.info("Connected to Temporal")
        
        # Start a test workflow
        workflow_id = await client.start_testing_workflow(
            cycle_id=99999,
            report_id=999999,
            user_id=1
        )
        
        logger.info(f"Started workflow: {workflow_id}")
        
        # Get workflow handle
        handle = client.client.get_workflow_handle(workflow_id)
        
        # Wait a bit for workflow to initialize
        await asyncio.sleep(2)
        
        # Query status
        status = await handle.query("get_current_status")
        logger.info(f"Current status: {status}")
        
        # Check what action is awaited
        logger.info(f"Current phase: {status.get('current_phase')}")
        logger.info(f"Awaiting action: {status.get('awaiting_action')}")
        logger.info(f"Workflow status: {status.get('workflow_status')}")
        
        # Terminate the workflow to clean up
        await handle.terminate()
        logger.info("Workflow terminated for cleanup")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        import traceback
        traceback.print_exc()


async def main():
    """Main function"""
    await test_workflow_status()


if __name__ == "__main__":
    asyncio.run(main())