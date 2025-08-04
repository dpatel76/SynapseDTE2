#!/usr/bin/env python
"""Minimal test to isolate workflow validation issue"""

import asyncio
import logging
from temporalio.client import Client
from temporalio.worker import Worker

# Import just the workflow
from app.temporal.workflows.test_cycle_workflow_reconciled import TestCycleWorkflowReconciled

logging.basicConfig(level=logging.DEBUG)


async def test_minimal():
    """Test with minimal worker setup"""
    print("Connecting to Temporal...")
    client = await Client.connect("localhost:7233")
    print("Connected!")
    
    try:
        print("Creating worker...")
        worker = Worker(
            client,
            task_queue="test-queue",
            workflows=[TestCycleWorkflowReconciled],
            activities=[]  # No activities for this test
        )
        print("Worker created successfully!")
        
    except Exception as e:
        print(f"Failed to create worker: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_minimal())