"""
Database configuration and connection management
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import NullPool
from typing import AsyncGenerator, Generator
import structlog
import time

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

# Create sync engine for Celery tasks
sync_database_url = settings.database_url.replace("+asyncpg", "+psycopg2")
if "postgresql+psycopg2" not in sync_database_url:
    sync_database_url = sync_database_url.replace("postgresql://", "postgresql+psycopg2://")

sync_engine = create_engine(
    sync_database_url,
    echo=settings.debug,
    pool_size=settings.database_pool_size if not settings.debug else 5,
    max_overflow=settings.database_max_overflow if not settings.debug else 10,
    future=True
)

# Create sync session factory for Celery tasks
SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    class_=Session,
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


def get_sync_db() -> Generator[Session, None, None]:
    """
    Sync database session for Celery tasks
    """
    start_time = time.time()
    logger.info("get_sync_db called - attempting to create sync session")
    
    try:
        logger.info("Creating SyncSessionLocal...")
        with SyncSessionLocal() as session:
            logger.info(f"Sync session created successfully in {time.time() - start_time:.2f}s")
            try:
                yield session
                logger.info(f"About to commit sync session after {time.time() - start_time:.2f}s")
                session.commit()
                logger.info(f"Sync session committed successfully after {time.time() - start_time:.2f}s")
            except Exception as e:
                logger.error(f"Sync session error after {time.time() - start_time:.2f}s", error=str(e))
                session.rollback()
                raise
            finally:
                logger.info(f"Closing sync session after {time.time() - start_time:.2f}s")
                session.close()
    except Exception as e:
        logger.error(f"Failed to create sync session after {time.time() - start_time:.2f}s", error=str(e))
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