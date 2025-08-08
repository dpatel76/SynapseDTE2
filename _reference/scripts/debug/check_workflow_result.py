#!/usr/bin/env python
"""Check the result of the just-run workflow"""

import asyncio
import logging
from app.temporal.client import get_temporal_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def check_result():
    """Check the result of the workflow we just ran"""
    try:
        client = await get_temporal_client()
        workflow_id = "test-cycle-98886-report-812969"
        
        handle = client.client.get_workflow_handle(workflow_id)
        
        # Get current status
        status = await handle.query("get_current_status")
        logger.info(f"\nWorkflow Status:")
        logger.info(f"Current Phase: {status.get('current_phase')}")
        logger.info(f"Awaiting Action: {status.get('awaiting_action')}")
        logger.info(f"Phase Results: {status.get('phase_results')}")
        
        # Get result
        try:
            result = await handle.result()
            logger.info(f"\nFinal Result: {result}")
        except Exception as e:
            logger.info(f"Result not available (workflow may still be running): {e}")
            
        # Check execution status
        desc = await handle.describe()
        logger.info(f"\nExecution Status: {desc.status}")
        
    except Exception as e:
        logger.error(f"Failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(check_result())