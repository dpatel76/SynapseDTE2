#!/usr/bin/env python
"""Test script to start a Temporal workflow"""

import asyncio
import logging
from app.temporal.client import get_temporal_client
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_start_workflow():
    """Test starting a workflow for a single report"""
    try:
        # Get the Temporal client
        client = await get_temporal_client()
        logger.info("Connected to Temporal")
        
        # Test data - in a real scenario, you would get these from your database
        # IMPORTANT: Each report in a test cycle gets its own workflow
        cycle_id = 1  # Test cycle ID
        report_id = 1  # Single report ID within the cycle
        user_id = 1   # User starting the workflow
        
        # Start the workflow for this specific report
        workflow_id = await client.start_testing_workflow(
            cycle_id=cycle_id,
            report_id=report_id,
            user_id=user_id,
            metadata={
                "started_at": datetime.utcnow().isoformat(),
                "started_by": "test_script",
                "report_name": "Sample Report 1"  # You'd get this from DB
            }
        )
        
        logger.info(f"Successfully started workflow: {workflow_id}")
        
        # Get workflow status
        status = await client.get_workflow_status(workflow_id)
        logger.info(f"Workflow status: {status}")
        
        # Query the workflow for current status
        handle = client.client.get_workflow_handle(workflow_id)
        current_status = await handle.query("get_current_status")
        logger.info(f"Current workflow state: {current_status}")
        
        return workflow_id
        
    except Exception as e:
        logger.error(f"Failed to start workflow: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


async def test_signal_workflow(workflow_id: str):
    """Test sending signals to the workflow"""
    try:
        client = await get_temporal_client()
        
        # Example: Submit planning documents
        await client.signal_workflow(
            workflow_id=workflow_id,
            signal_name="submit_planning_documents",
            signal_data={
                "input_type": "planning_documents",
                "data": {
                    "documents": [
                        {"name": "test_plan.pdf", "type": "planning"},
                        {"name": "schedule.xlsx", "type": "schedule"}
                    ]
                },
                "user_id": 1,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        logger.info("Sent planning documents signal")
        
        # Example: Submit planning attributes
        await client.signal_workflow(
            workflow_id=workflow_id,
            signal_name="submit_planning_attributes",
            signal_data={
                "input_type": "planning_attributes",
                "data": {
                    "attributes": [
                        {"name": "Account Number", "type": "identifier"},
                        {"name": "Balance", "type": "numeric"}
                    ]
                },
                "user_id": 1,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        logger.info("Sent planning attributes signal")
        
    except Exception as e:
        logger.error(f"Failed to signal workflow: {str(e)}")
        raise


async def test_start_multiple_workflows():
    """Test starting workflows for multiple reports in a cycle"""
    try:
        client = await get_temporal_client()
        
        # Example: A test cycle with 3 reports
        cycle_id = 2
        report_ids = [10, 11, 12]  # Three different reports in the same cycle
        user_id = 1
        
        # Start workflows for all reports
        workflow_ids = await client.start_workflows_for_cycle(
            cycle_id=cycle_id,
            report_ids=report_ids,
            user_id=user_id,
            metadata={
                "started_at": datetime.utcnow().isoformat(),
                "started_by": "test_script",
                "test_cycle_name": "Q1 2024 Testing"
            }
        )
        
        logger.info(f"Started {len(workflow_ids)} workflows:")
        for wf_id in workflow_ids:
            logger.info(f"  - {wf_id}")
            
        return workflow_ids
        
    except Exception as e:
        logger.error(f"Failed to start multiple workflows: {str(e)}")
        raise


async def main():
    """Main test function"""
    logger.info("Starting workflow test...")
    
    # Test 1: Start a single workflow for one report
    logger.info("\n=== Test 1: Single Report Workflow ===")
    workflow_id = await test_start_workflow()
    
    # Wait a moment for the workflow to start
    await asyncio.sleep(2)
    
    # Send some signals to the single workflow
    await test_signal_workflow(workflow_id)
    
    # Test 2: Start workflows for multiple reports in a cycle
    logger.info("\n=== Test 2: Multiple Report Workflows ===")
    workflow_ids = await test_start_multiple_workflows()
    
    logger.info("\nTest completed!")


if __name__ == "__main__":
    asyncio.run(main())