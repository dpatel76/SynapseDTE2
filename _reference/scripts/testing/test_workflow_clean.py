#!/usr/bin/env python
"""Test script to start a new Temporal workflow with clean IDs"""

import asyncio
import logging
from app.temporal.client import get_temporal_client
from datetime import datetime
import random

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_clean_workflow():
    """Test starting a workflow with a new ID"""
    try:
        # Get the Temporal client
        client = await get_temporal_client()
        logger.info("Connected to Temporal")
        
        # Generate unique IDs
        cycle_id = random.randint(100, 999)
        report_id = random.randint(1000, 9999)
        user_id = 1
        
        logger.info(f"Starting workflow for cycle {cycle_id}, report {report_id}")
        
        # Start the workflow
        workflow_id = await client.start_testing_workflow(
            cycle_id=cycle_id,
            report_id=report_id,
            user_id=user_id
        )
        
        logger.info(f"✅ Successfully started workflow: {workflow_id}")
        
        # Wait a moment for initialization
        await asyncio.sleep(2)
        
        # Get workflow status
        status = await client.get_workflow_status(workflow_id)
        logger.info(f"Workflow status: {status}")
        
        # Query the workflow for current status
        handle = client.client.get_workflow_handle(workflow_id)
        current_status = await handle.query("get_current_status")
        logger.info(f"Current workflow state: {current_status}")
        
        # Send signals if workflow is waiting
        if current_status.get("awaiting_action") == "upload_planning_documents":
            logger.info("Sending planning documents signal...")
            await client.signal_workflow(
                workflow_id=workflow_id,
                signal_name="submit_planning_documents",
                signal_data={
                    "input_type": "planning_documents",
                    "data": {
                        "documents": [
                            {"name": "test_plan.pdf", "type": "planning"},
                            {"name": "regulatory_spec.pdf", "type": "regulatory"}
                        ]
                    },
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            logger.info("✅ Sent planning documents signal")
            
            # Wait and check status again
            await asyncio.sleep(2)
            current_status = await handle.query("get_current_status")
            logger.info(f"Updated workflow state: {current_status}")
        
        return workflow_id
        
    except Exception as e:
        logger.error(f"Failed to test workflow: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


async def main():
    """Main test function"""
    logger.info("=== Temporal Workflow Test ===")
    
    try:
        workflow_id = await test_clean_workflow()
        logger.info(f"\n✅ Test completed successfully!")
        logger.info(f"Workflow ID: {workflow_id}")
        logger.info(f"Check Temporal UI at http://localhost:8088")
    except Exception as e:
        logger.error(f"\n❌ Test failed: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())