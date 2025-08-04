#!/usr/bin/env python
"""Test script to verify worker connection to Temporal"""

import asyncio
import logging
from app.temporal.worker import EnhancedTemporalWorker

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_connection():
    """Test connecting the worker to Temporal"""
    logger.info("Testing Temporal worker connection...")
    
    worker = EnhancedTemporalWorker()
    
    try:
        # Start the worker (this will connect and begin polling)
        logger.info("Starting worker...")
        await worker.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
        await worker.stop()
    except Exception as e:
        logger.error(f"Connection test failed: {str(e)}")
        await worker.stop()
        raise


if __name__ == "__main__":
    asyncio.run(test_connection())