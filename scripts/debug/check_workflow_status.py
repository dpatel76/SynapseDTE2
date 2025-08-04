#!/usr/bin/env python
"""Check the status of recent workflow executions"""

import asyncio
import logging
from app.temporal.client import get_temporal_client
from temporalio.client import WorkflowExecutionStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def check_workflows():
    """Check recent workflow executions"""
    try:
        client = await get_temporal_client()
        logger.info("Connected to Temporal")
        
        # List recent workflows
        workflows = []
        async for workflow in client.client.list_workflows(
            page_size=10
        ):
            workflows.append({
                "id": workflow.id,
                "status": workflow.status,
                "start_time": workflow.start_time,
                "close_time": workflow.close_time if hasattr(workflow, 'close_time') else None
            })
        
        logger.info(f"\nFound {len(workflows)} recent workflows:")
        for wf in workflows:
            logger.info(f"  ID: {wf['id']}")
            logger.info(f"  Status: {wf['status']}")
            logger.info(f"  Started: {wf['start_time']}")
            if wf['close_time']:
                logger.info(f"  Closed: {wf['close_time']}")
            
            # Try to get workflow result if completed
            if wf['status'] == WorkflowExecutionStatus.COMPLETED:
                try:
                    handle = client.client.get_workflow_handle(wf['id'])
                    result = await handle.result()
                    logger.info(f"  Result: {result}")
                except Exception as e:
                    logger.error(f"  Could not get result: {e}")
            logger.info("")
        
        return workflows
        
    except Exception as e:
        logger.error(f"Failed to check workflows: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(check_workflows())