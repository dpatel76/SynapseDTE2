#!/usr/bin/env python
"""Test workflow with activity tracking"""

import asyncio
import logging
from datetime import datetime
from app.temporal.client import get_temporal_client
from temporalio import activity

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


# Create a simple test activity to verify basic flow
@activity.defn
async def test_activity(message: str) -> dict:
    """Simple test activity"""
    logger.info(f"Test activity executed: {message}")
    return {"success": True, "message": message}


async def test_basic_workflow():
    """Test basic workflow functionality"""
    try:
        # Get the Temporal client
        client = await get_temporal_client()
        logger.info("Connected to Temporal")
        
        # Start a simple workflow
        workflow_id = await client.start_testing_workflow(
            cycle_id=88888,
            report_id=888888,
            user_id=1
        )
        
        logger.info(f"Started workflow: {workflow_id}")
        
        # Get workflow handle
        handle = client.client.get_workflow_handle(workflow_id)
        
        # Monitor workflow for 20 seconds
        for i in range(10):
            await asyncio.sleep(2)
            
            # Query status
            status = await handle.query("get_current_status")
            logger.info(f"\nIteration {i+1}:")
            logger.info(f"  Phase: {status.get('current_phase')}")
            logger.info(f"  Action: {status.get('awaiting_action')}")
            logger.info(f"  Status: {status.get('workflow_status')}")
            logger.info(f"  Completed: {list(status.get('phase_results', {}).keys())}")
            
            # Check workflow execution status
            try:
                desc = await handle.describe()
                logger.info(f"  Execution Status: {desc.status}")
                if desc.close_time:
                    logger.info(f"  WORKFLOW CLOSED AT: {desc.close_time}")
                    break
            except Exception as e:
                logger.error(f"  Failed to describe: {e}")
        
        # Terminate workflow for cleanup
        try:
            await handle.terminate()
            logger.info("\nWorkflow terminated for cleanup")
        except:
            pass
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        import traceback
        traceback.print_exc()


async def main():
    """Main function"""
    await test_basic_workflow()


if __name__ == "__main__":
    asyncio.run(main())