#!/usr/bin/env python
"""Simple workflow test to verify basic functionality"""

import asyncio
import logging
from datetime import datetime
from app.temporal.client import get_temporal_client

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_simple_workflow():
    """Test simple workflow execution through Planning phase"""
    try:
        # Get the Temporal client
        client = await get_temporal_client()
        logger.info("Connected to Temporal")
        
        # Start a test workflow
        workflow_id = await client.start_testing_workflow(
            cycle_id=77777,
            report_id=777777,
            user_id=1
        )
        
        logger.info(f"Started workflow: {workflow_id}")
        
        # Get workflow handle
        handle = client.client.get_workflow_handle(workflow_id)
        
        # Wait for workflow to initialize
        await asyncio.sleep(2)
        
        # Check initial status
        status = await handle.query("get_current_status")
        logger.info(f"\nInitial Status:")
        logger.info(f"  Current phase: {status.get('current_phase')}")
        logger.info(f"  Awaiting action: {status.get('awaiting_action')}")
        logger.info(f"  Workflow status: {status.get('workflow_status')}")
        
        # Send planning documents signal
        logger.info("\nSending planning documents signal...")
        await client.signal_workflow(
            workflow_id=workflow_id,
            signal_name="submit_planning_documents",
            signal_data={
                "input_type": "planning_documents",
                "data": {
                    "documents": [
                        {"name": "test.pdf", "type": "regulatory", "size": 1024}
                    ]
                },
                "user_id": 1,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        await asyncio.sleep(2)
        
        # Check status after document upload
        status = await handle.query("get_current_status")
        logger.info(f"\nStatus after document upload:")
        logger.info(f"  Current phase: {status.get('current_phase')}")
        logger.info(f"  Awaiting action: {status.get('awaiting_action')}")
        logger.info(f"  Workflow status: {status.get('workflow_status')}")
        
        # Send attributes signal
        logger.info("\nSending planning attributes signal...")
        await client.signal_workflow(
            workflow_id=workflow_id,
            signal_name="submit_planning_attributes",
            signal_data={
                "input_type": "planning_attributes",
                "data": {
                    "manual_attributes": [
                        {
                            "attribute_name": "Test Attr",
                            "data_type": "String",
                            "description": "Test",
                            "cde_flag": True,
                            "historical_issues_flag": False
                        }
                    ]
                },
                "user_id": 1,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        await asyncio.sleep(3)
        
        # Check final status
        status = await handle.query("get_current_status")
        logger.info(f"\nFinal Status:")
        logger.info(f"  Current phase: {status.get('current_phase')}")
        logger.info(f"  Awaiting action: {status.get('awaiting_action')}")
        logger.info(f"  Workflow status: {status.get('workflow_status')}")
        logger.info(f"  Phase results: {status.get('phase_results', {})}")
        
        # Check workflow execution status
        try:
            desc = await handle.describe()
            logger.info(f"\nWorkflow execution status: {desc.status}")
            if desc.close_time:
                logger.info(f"Workflow closed at: {desc.close_time}")
        except Exception as e:
            logger.error(f"Failed to describe workflow: {e}")
        
        # Terminate for cleanup
        await handle.terminate()
        logger.info("\nWorkflow terminated for cleanup")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        import traceback
        traceback.print_exc()


async def main():
    """Main function"""
    logger.info("=== Simple Temporal Workflow Test ===\n")
    await test_simple_workflow()


if __name__ == "__main__":
    asyncio.run(main())