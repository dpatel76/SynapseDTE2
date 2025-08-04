"""Test endpoint to debug dependency injection issue"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import time
import structlog

from app.core.database import get_db

router = APIRouter()
logger = structlog.get_logger()

@router.get("/test-db")
async def test_db(db: AsyncSession = Depends(get_db)):
    """Test database connection through dependency injection"""
    start_time = time.time()
    logger.info("Test endpoint called")
    
    try:
        result = await db.execute(text("SELECT 1"))
        value = result.scalar()
        elapsed = time.time() - start_time
        logger.info(f"Database query successful in {elapsed:.2f}s")
        return {"status": "success", "result": value, "elapsed": elapsed}
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Database query failed after {elapsed:.2f}s", error=str(e))
        return {"status": "error", "error": str(e), "elapsed": elapsed}

@router.get("/test-simple")
async def test_simple():
    """Test simple endpoint without dependencies"""
    logger.info("Simple test endpoint called")
    return {"status": "success", "message": "Simple endpoint works"}