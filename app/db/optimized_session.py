"""Optimized database session configuration"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool, AsyncAdaptedQueuePool
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.core.performance import PERFORMANCE_CONFIG

logger = logging.getLogger(__name__)


# Create optimized async engine
def create_optimized_engine():
    """Create database engine with performance optimizations"""
    
    # Connection arguments for PostgreSQL
    connect_args = {
        "server_settings": {
            "application_name": "synapse_dte_clean",
            "jit": "off"  # Disable JIT for consistent performance
        },
        "command_timeout": PERFORMANCE_CONFIG["query_timeout"],
    }
    
    # Pool class based on environment
    if settings.ENVIRONMENT == "production":
        pool_class = AsyncAdaptedQueuePool
        pool_size = PERFORMANCE_CONFIG["db_pool_size"]
        max_overflow = PERFORMANCE_CONFIG["db_max_overflow"]
    else:
        # Use NullPool for development to avoid connection issues
        pool_class = NullPool
        pool_size = 5
        max_overflow = 10
    
    engine = create_async_engine(
        settings.DATABASE_URL,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=PERFORMANCE_CONFIG["db_pool_timeout"],
        pool_recycle=PERFORMANCE_CONFIG["db_pool_recycle"],
        pool_pre_ping=True,  # Verify connections before use
        poolclass=pool_class,
        connect_args=connect_args,
        echo=settings.DEBUG_SQL,
        future=True
    )
    
    return engine


# Create engine
engine = create_optimized_engine()

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Don't expire objects after commit
    autocommit=False,
    autoflush=False  # Manual flush for better control
)


# Session dependency with optimizations
async def get_optimized_db() -> AsyncGenerator[AsyncSession, None]:
    """Get optimized database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Context manager for manual session handling
@asynccontextmanager
async def get_db_context():
    """Context manager for database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Query optimization helpers
class QueryOptimizations:
    """Helper class for query optimizations"""
    
    @staticmethod
    def with_joined_loading(query, *relationships):
        """Add joined loading for relationships"""
        from sqlalchemy.orm import joinedload
        
        for relationship in relationships:
            query = query.options(joinedload(relationship))
        
        return query
    
    @staticmethod
    def with_subquery_loading(query, *relationships):
        """Add subquery loading for relationships"""
        from sqlalchemy.orm import subqueryload
        
        for relationship in relationships:
            query = query.options(subqueryload(relationship))
        
        return query
    
    @staticmethod
    def with_pagination(query, page: int = 1, size: int = 100):
        """Add pagination to query"""
        offset = (page - 1) * size
        return query.offset(offset).limit(size)
    
    @staticmethod
    def with_batch_loading(query, batch_size: int = 100):
        """Enable batch loading for better performance"""
        return query.yield_per(batch_size)


# Connection pool monitoring
async def get_pool_status():
    """Get current connection pool status"""
    pool = engine.pool
    
    return {
        "size": pool.size(),
        "checked_in": pool.checkedin(),
        "overflow": pool.overflow(),
        "total": pool.size() + pool.overflow()
    }


# Database health check
async def check_database_health():
    """Check database health and performance"""
    try:
        async with engine.connect() as conn:
            # Simple query to test connection
            result = await conn.execute("SELECT 1")
            await result.fetchone()
            
            # Get database statistics
            stats_query = """
            SELECT 
                numbackends as active_connections,
                xact_commit as commits,
                xact_rollback as rollbacks,
                blks_hit as cache_hits,
                blks_read as disk_reads,
                tup_returned as rows_returned,
                tup_fetched as rows_fetched
            FROM pg_stat_database 
            WHERE datname = current_database()
            """
            
            stats_result = await conn.execute(stats_query)
            stats = dict(stats_result.fetchone())
            
            # Calculate cache hit ratio
            total_blocks = stats["cache_hits"] + stats["disk_reads"]
            cache_hit_ratio = (
                stats["cache_hits"] / total_blocks * 100 
                if total_blocks > 0 else 0
            )
            
            return {
                "status": "healthy",
                "active_connections": stats["active_connections"],
                "cache_hit_ratio": f"{cache_hit_ratio:.2f}%",
                "commits": stats["commits"],
                "rollbacks": stats["rollbacks"],
                "pool_status": await get_pool_status()
            }
            
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


# Initialize database on startup
async def init_db():
    """Initialize database with optimizations"""
    try:
        # Test connection
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        
        # Log pool configuration
        logger.info(
            f"Database initialized with pool_size={PERFORMANCE_CONFIG['db_pool_size']}, "
            f"max_overflow={PERFORMANCE_CONFIG['db_max_overflow']}"
        )
        
        # Warm up connection pool
        if settings.ENVIRONMENT == "production":
            await warm_up_pool()
            
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def warm_up_pool():
    """Pre-create connections to avoid cold start"""
    connections = []
    try:
        for _ in range(PERFORMANCE_CONFIG["db_pool_size"] // 2):
            conn = await engine.connect()
            connections.append(conn)
        
        # Close all connections
        for conn in connections:
            await conn.close()
            
        logger.info("Connection pool warmed up")
        
    except Exception as e:
        logger.error(f"Failed to warm up connection pool: {e}")


# Cleanup on shutdown
async def close_db():
    """Close database connections"""
    await engine.dispose()
    logger.info("Database connections closed")