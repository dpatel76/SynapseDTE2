"""
Refactored database configuration with improved connection management
"""
import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool, QueuePool
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Get database URL from environment or settings
DATABASE_URL = os.getenv("DATABASE_URL", settings.database_url)

# Ensure URL uses asyncpg driver
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Create async engine with optimized settings
engine = create_async_engine(
    DATABASE_URL,
    echo=settings.debug and os.getenv("SQL_ECHO", "false").lower() == "true",
    pool_pre_ping=True,  # Verify connections before using
    pool_size=int(os.getenv("DATABASE_POOL_SIZE", "20")),
    max_overflow=int(os.getenv("DATABASE_MAX_OVERFLOW", "10")),
    pool_timeout=int(os.getenv("DATABASE_POOL_TIMEOUT", "30")),
    pool_recycle=int(os.getenv("DATABASE_POOL_RECYCLE", "3600")),
    pool_class=NullPool if settings.debug else QueuePool,
    connect_args={
        "server_settings": {
            "application_name": "synapse_dte_refactored",
            "jit": "off"
        },
        "command_timeout": int(os.getenv("STATEMENT_TIMEOUT", "60")),
        "timeout": int(os.getenv("CONNECTION_TIMEOUT", "30")),
        # Connection pool settings
        "min_size": 5,
        "max_size": int(os.getenv("DATABASE_POOL_SIZE", "20")),
        # Prepared statement cache
        "prepared_statement_cache_size": 0,  # Disable to avoid issues with pooling
        # SSL settings if needed
        "ssl": os.getenv("DATABASE_SSL", "prefer"),
    }
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Don't expire objects after commit
    autocommit=False,
    autoflush=False,  # Explicit flushes only
)

# Base class for models
Base = declarative_base()

# Dependency for FastAPI
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to get database session.
    Properly handles transaction boundaries.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            # Commit only if no exception occurred
            await session.commit()
        except Exception:
            # Rollback on any exception
            await session.rollback()
            raise
        finally:
            # Always close the session
            await session.close()

# Context manager for background tasks
async def get_db_context() -> AsyncSession:
    """
    Get database session for use in background tasks.
    Caller is responsible for commit/rollback.
    """
    return AsyncSessionLocal()

# Health check function
async def check_database_connection() -> bool:
    """
    Check if database is accessible
    """
    try:
        async with AsyncSessionLocal() as session:
            await session.execute("SELECT 1")
            return True
    except Exception as e:
        logger.error(f"Database connection check failed: {str(e)}")
        return False

# Shutdown function
async def close_database_connection():
    """
    Close database connections gracefully
    """
    await engine.dispose()

# Initialize database tables (for development)
async def init_database():
    """
    Create all tables (development only)
    """
    if settings.debug:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

# Drop all tables (for testing)
async def drop_database():
    """
    Drop all tables (testing only)
    """
    if settings.testing:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)