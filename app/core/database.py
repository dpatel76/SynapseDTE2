"""
Database configuration and connection management
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import NullPool
from typing import AsyncGenerator
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)

# Create async engine
if settings.debug:
    # In debug mode, use NullPool without pool parameters
    engine = create_async_engine(
        settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
        echo=settings.debug,
        poolclass=NullPool,
        future=True
    )
else:
    # In production mode, use default pool with parameters
    engine = create_async_engine(
        settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
        echo=settings.debug,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        future=True
    )

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Create declarative base
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session
    """
    import time
    start_time = time.time()
    logger.info("get_db called - attempting to create session")
    
    try:
        logger.info("Creating AsyncSessionLocal...")
        async with AsyncSessionLocal() as session:
            logger.info(f"Session created successfully in {time.time() - start_time:.2f}s")
            try:
                yield session
                logger.info(f"About to commit session after {time.time() - start_time:.2f}s")
                await session.commit()
                logger.info(f"Session committed successfully after {time.time() - start_time:.2f}s")
            except Exception as e:
                logger.error(f"Session error after {time.time() - start_time:.2f}s", error=str(e))
                await session.rollback()
                raise
            finally:
                logger.info(f"Closing session after {time.time() - start_time:.2f}s")
                await session.close()
    except Exception as e:
        logger.error(f"Failed to create session after {time.time() - start_time:.2f}s", error=str(e))
        raise


async def init_db() -> None:
    """Initialize database connection (tables created by migrations)"""
    # Tables are created by Alembic migrations, not here
    # Just test the connection
    from sqlalchemy import text
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection verified")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise


async def close_db() -> None:
    """Close database connections"""
    await engine.dispose()
    logger.info("Database connections closed") 