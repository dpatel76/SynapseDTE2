#!/usr/bin/env python
"""Check the latest workflow execution in detail"""

import asyncio
import logging
from app.temporal.client import get_temporal_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def check_latest_workflow():
    """Check the most recent completed workflow in detail"""
    try:
        client = await get_temporal_client()
        logger.info("Connected to Temporal")
        
        # The most recent workflow with the gather error
        workflow_id = "test-cycle-85008-report-608482"
        
        try:
            handle = client.client.get_workflow_handle(workflow_id)
            
            # Get current status
            status = await handle.query("get_current_status")
            logger.info(f"\nWorkflow: {workflow_id}")
            logger.info(f"Current Status: {status}")
            
            # Get result
            try:
                result = await handle.result()
                logger.info(f"\nFinal Result: {result}")
            except Exception as e:
                logger.error(f"Could not get result: {e}")
                
            # Get description
            desc = await handle.describe()
            logger.info(f"\nWorkflow Status: {desc.status}")
            logger.info(f"Started: {desc.start_time}")
            if hasattr(desc, 'close_time') and desc.close_time:
                logger.info(f"Closed: {desc.close_time}")
                
        except Exception as e:
            logger.error(f"Error checking workflow {workflow_id}: {e}")
            
        # Check a running workflow
        logger.info("\n" + "="*60)
        running_id = "test-cycle-97237-report-573926"
        logger.info(f"\nChecking running workflow: {running_id}")
        
        try:
            handle = client.client.get_workflow_handle(running_id)
            status = await handle.query("get_current_status")
            logger.info(f"Current Status: {status}")
        except Exception as e:
            logger.error(f"Error checking running workflow: {e}")
        
    except Exception as e:
        logger.error(f"Failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(check_latest_workflow())