"""Performance optimization configurations and utilities"""
from typing import Any, Dict, Optional
from functools import lru_cache, wraps
import asyncio
import time
from datetime import datetime, timedelta
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Monitor and log performance metrics"""
    
    def __init__(self):
        self.metrics: Dict[str, list] = {}
    
    def record_metric(self, operation: str, duration: float, metadata: Optional[Dict[str, Any]] = None):
        """Record a performance metric"""
        if operation not in self.metrics:
            self.metrics[operation] = []
        
        self.metrics[operation].append({
            "duration": duration,
            "timestamp": datetime.utcnow(),
            "metadata": metadata or {}
        })
        
        # Log slow operations
        if duration > 1.0:  # More than 1 second
            logger.warning(
                f"Slow operation detected: {operation} took {duration:.2f}s",
                extra={"metadata": metadata}
            )
    
    def get_stats(self, operation: str) -> Dict[str, float]:
        """Get statistics for an operation"""
        if operation not in self.metrics:
            return {}
        
        durations = [m["duration"] for m in self.metrics[operation]]
        
        return {
            "count": len(durations),
            "total": sum(durations),
            "average": sum(durations) / len(durations),
            "min": min(durations),
            "max": max(durations)
        }
    
    def clear_old_metrics(self, days: int = 7):
        """Clear metrics older than specified days"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        for operation in self.metrics:
            self.metrics[operation] = [
                m for m in self.metrics[operation]
                if m["timestamp"] > cutoff
            ]


# Global performance monitor
performance_monitor = PerformanceMonitor()


def measure_performance(operation_name: Optional[str] = None):
    """Decorator to measure function performance"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            operation = operation_name or f"{func.__module__}.{func.__name__}"
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                performance_monitor.record_metric(operation, duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                performance_monitor.record_metric(
                    operation,
                    duration,
                    {"error": str(e)}
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            operation = operation_name or f"{func.__module__}.{func.__name__}"
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                performance_monitor.record_metric(operation, duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                performance_monitor.record_metric(
                    operation,
                    duration,
                    {"error": str(e)}
                )
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class ConnectionPool:
    """Optimized connection pool for database"""
    
    def __init__(self, min_size: int = 10, max_size: int = 100):
        self.min_size = min_size
        self.max_size = max_size
        self._pool = []
        self._in_use = set()
    
    async def acquire(self):
        """Acquire a connection from the pool"""
        # Simplified implementation
        # In production, use asyncpg's built-in pool
        pass
    
    async def release(self, conn):
        """Release a connection back to the pool"""
        pass


class QueryOptimizer:
    """Optimize database queries"""
    
    @staticmethod
    def add_query_hints(query, hints: Dict[str, Any]):
        """Add query hints for optimization"""
        # PostgreSQL specific hints
        if hints.get("parallel"):
            query = query.prefix_with("/*+ PARALLEL(4) */")
        
        if hints.get("index"):
            query = query.with_hint(hints["index"], "USE INDEX")
        
        return query
    
    @staticmethod
    def enable_query_cache(query, cache_time: int = 300):
        """Enable query result caching"""
        # This would integrate with Redis for caching
        return query


class BatchProcessor:
    """Process items in optimized batches"""
    
    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size
    
    async def process_in_batches(self, items: list, processor_func):
        """Process items in batches for better performance"""
        results = []
        
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            
            # Process batch concurrently
            batch_results = await asyncio.gather(
                *[processor_func(item) for item in batch]
            )
            results.extend(batch_results)
        
        return results


# Cache configuration
@lru_cache(maxsize=1000)
def get_cached_config(key: str) -> Any:
    """Get cached configuration value"""
    return getattr(settings, key, None)


# Query result cache
class QueryCache:
    """Simple query result cache using memory"""
    
    def __init__(self, ttl: int = 300):
        self._cache = {}
        self.ttl = ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached result"""
        if key in self._cache:
            result, timestamp = self._cache[key]
            if datetime.utcnow() - timestamp < timedelta(seconds=self.ttl):
                return result
            else:
                del self._cache[key]
        return None
    
    def set(self, key: str, value: Any):
        """Set cache value"""
        self._cache[key] = (value, datetime.utcnow())
    
    def clear(self):
        """Clear all cache"""
        self._cache.clear()


# Global query cache
query_cache = QueryCache()


# Performance optimization settings
PERFORMANCE_CONFIG = {
    # Database
    "db_pool_size": 20,
    "db_max_overflow": 10,
    "db_pool_timeout": 30,
    "db_pool_recycle": 3600,
    
    # Caching
    "cache_ttl": 300,
    "cache_max_size": 10000,
    
    # Batching
    "default_batch_size": 100,
    "max_batch_size": 1000,
    
    # Timeouts
    "request_timeout": 30,
    "llm_timeout": 120,
    "file_upload_timeout": 300,
    
    # Rate limiting
    "rate_limit_requests": 100,
    "rate_limit_window": 60,
    
    # Query optimization
    "enable_query_cache": True,
    "enable_parallel_queries": True,
    "query_timeout": 60
}


def optimize_for_production():
    """Apply production optimizations"""
    import gc
    
    # Optimize garbage collection
    gc.set_threshold(700, 10, 10)
    
    # Enable query plan caching in PostgreSQL
    # This would be done at database configuration level
    
    # Pre-warm caches
    # This would load frequently accessed data into cache
    
    logger.info("Production optimizations applied")