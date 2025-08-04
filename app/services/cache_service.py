"""
Advanced Redis Caching Service
Provides distributed caching with TTL, pattern-based operations, and performance monitoring
"""

import logging
import json
import asyncio
import redis.asyncio as redis
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import hashlib
from dataclasses import dataclass, asdict

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class CacheMetrics:
    """Cache performance metrics"""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    total_size_bytes: int = 0
    average_response_time_ms: float = 0.0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate percentage"""
        if self.total_requests == 0:
            return 0.0
        return (self.cache_hits / self.total_requests) * 100
    
    @property
    def miss_rate(self) -> float:
        """Calculate cache miss rate percentage"""
        return 100.0 - self.hit_rate


class CacheService:
    """Advanced Redis-based caching service"""
    
    def __init__(self):
        self.redis_url = getattr(settings, 'redis_url', 'redis://localhost:6379')
        self.redis_password = getattr(settings, 'redis_password', None)
        self.redis_db = getattr(settings, 'redis_db', 0)
        self.default_ttl = getattr(settings, 'cache_default_ttl_seconds', 3600)  # 1 hour
        self.key_prefix = getattr(settings, 'cache_key_prefix', 'synapse:')
        
        # Performance settings
        self.max_connections = getattr(settings, 'redis_max_connections', 20)
        self.connection_timeout = getattr(settings, 'redis_timeout_seconds', 5)
        
        # Cache configuration by category
        self.cache_configs = {
            'user_sessions': {'ttl': 28800, 'prefix': 'session:'},  # 8 hours
            'metrics': {'ttl': 1800, 'prefix': 'metrics:'},  # 30 minutes
            'benchmarks': {'ttl': 86400, 'prefix': 'bench:'},  # 24 hours
            'llm_responses': {'ttl': 7200, 'prefix': 'llm:'},  # 2 hours
            'reports': {'ttl': 3600, 'prefix': 'report:'},  # 1 hour
            'dashboard_data': {'ttl': 900, 'prefix': 'dash:'},  # 15 minutes
            'system_health': {'ttl': 300, 'prefix': 'health:'},  # 5 minutes
            'temp_data': {'ttl': 300, 'prefix': 'temp:'}  # 5 minutes
        }
        
        self._redis = None
        self._metrics = CacheMetrics()
        self._connected = False
        
        logger.info("Cache service initialized")
    
    async def connect(self) -> bool:
        """Establish Redis connection with connection pooling"""
        try:
            if self._connected and self._redis:
                return True
            
            # Create Redis connection
            self._redis = redis.from_url(
                self.redis_url,
                password=self.redis_password,
                db=self.redis_db,
                max_connections=self.max_connections,
                socket_timeout=self.connection_timeout,
                socket_connect_timeout=self.connection_timeout,
                decode_responses=True,
                encoding='utf-8'
            )
            
            # Test connection
            await self._redis.ping()
            self._connected = True
            
            logger.info("Successfully connected to Redis")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            self._connected = False
            return False
    
    async def disconnect(self):
        """Close Redis connection"""
        try:
            if self._redis:
                await self._redis.close()
                self._connected = False
                logger.info("Disconnected from Redis")
        except Exception as e:
            logger.error(f"Error disconnecting from Redis: {str(e)}")
    
    def _build_key(self, key: str, category: str = 'default') -> str:
        """Build standardized cache key with prefix"""
        config = self.cache_configs.get(category, {})
        prefix = config.get('prefix', '')
        return f"{self.key_prefix}{prefix}{key}"
    
    def _get_ttl(self, category: str, custom_ttl: Optional[int] = None) -> int:
        """Get TTL for cache category"""
        if custom_ttl is not None:
            return custom_ttl
        
        config = self.cache_configs.get(category, {})
        return config.get('ttl', self.default_ttl)
    
    def _serialize_value(self, value: Any) -> str:
        """Serialize value for Redis storage"""
        try:
            if isinstance(value, (dict, list)):
                return json.dumps(value, default=str)
            elif isinstance(value, (int, float, bool)):
                return str(value)
            else:
                return str(value)
        except Exception as e:
            logger.error(f"Serialization failed: {str(e)}")
            return str(value)
    
    def _deserialize_value(self, value: str) -> Any:
        """Deserialize value from Redis"""
        try:
            # Try JSON first
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            # Return as string if not JSON
            return value
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        category: str = 'default',
        ttl: Optional[int] = None
    ) -> bool:
        """Set cache value with optional TTL"""
        if not await self.connect():
            return False
        
        try:
            start_time = datetime.utcnow()
            
            cache_key = self._build_key(key, category)
            serialized_value = self._serialize_value(value)
            cache_ttl = self._get_ttl(category, ttl)
            
            await self._redis.setex(cache_key, cache_ttl, serialized_value)
            
            # Update metrics
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            self._update_metrics(response_time, hit=False)
            
            logger.debug(f"Cached key: {cache_key} (TTL: {cache_ttl}s)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set cache key {key}: {str(e)}")
            return False
    
    async def get(self, key: str, category: str = 'default') -> Optional[Any]:
        """Get cache value"""
        if not await self.connect():
            return None
        
        try:
            start_time = datetime.utcnow()
            
            cache_key = self._build_key(key, category)
            value = await self._redis.get(cache_key)
            
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            if value is not None:
                self._update_metrics(response_time, hit=True)
                return self._deserialize_value(value)
            else:
                self._update_metrics(response_time, hit=False)
                return None
                
        except Exception as e:
            logger.error(f"Failed to get cache key {key}: {str(e)}")
            self._update_metrics(0, hit=False)
            return None
    
    async def delete(self, key: str, category: str = 'default') -> bool:
        """Delete cache key"""
        if not await self.connect():
            return False
        
        try:
            cache_key = self._build_key(key, category)
            result = await self._redis.delete(cache_key)
            
            logger.debug(f"Deleted cache key: {cache_key}")
            return result > 0
            
        except Exception as e:
            logger.error(f"Failed to delete cache key {key}: {str(e)}")
            return False
    
    async def exists(self, key: str, category: str = 'default') -> bool:
        """Check if cache key exists"""
        if not await self.connect():
            return False
        
        try:
            cache_key = self._build_key(key, category)
            return await self._redis.exists(cache_key) > 0
            
        except Exception as e:
            logger.error(f"Failed to check cache key existence {key}: {str(e)}")
            return False
    
    async def expire(self, key: str, ttl: int, category: str = 'default') -> bool:
        """Set expiration time for existing key"""
        if not await self.connect():
            return False
        
        try:
            cache_key = self._build_key(key, category)
            return await self._redis.expire(cache_key, ttl)
            
        except Exception as e:
            logger.error(f"Failed to set expiration for cache key {key}: {str(e)}")
            return False
    
    async def get_ttl(self, key: str, category: str = 'default') -> int:
        """Get remaining TTL for key"""
        if not await self.connect():
            return -1
        
        try:
            cache_key = self._build_key(key, category)
            return await self._redis.ttl(cache_key)
            
        except Exception as e:
            logger.error(f"Failed to get TTL for cache key {key}: {str(e)}")
            return -1
    
    async def clear_pattern(self, pattern: str, category: str = 'default') -> int:
        """Clear all keys matching pattern"""
        if not await self.connect():
            return 0
        
        try:
            cache_pattern = self._build_key(pattern, category)
            
            # Get all matching keys
            keys = await self._redis.keys(cache_pattern)
            
            if keys:
                deleted = await self._redis.delete(*keys)
                logger.info(f"Cleared {deleted} cache keys matching pattern: {cache_pattern}")
                return deleted
            
            return 0
            
        except Exception as e:
            logger.error(f"Failed to clear cache pattern {pattern}: {str(e)}")
            return 0
    
    async def clear_category(self, category: str) -> int:
        """Clear all keys in a category"""
        config = self.cache_configs.get(category, {})
        prefix = config.get('prefix', '')
        pattern = f"{prefix}*"
        
        return await self.clear_pattern(pattern, 'default')
    
    async def get_multiple(self, keys: List[str], category: str = 'default') -> Dict[str, Any]:
        """Get multiple cache values at once"""
        if not await self.connect():
            return {}
        
        try:
            cache_keys = [self._build_key(key, category) for key in keys]
            values = await self._redis.mget(*cache_keys)
            
            result = {}
            for i, key in enumerate(keys):
                value = values[i]
                if value is not None:
                    result[key] = self._deserialize_value(value)
                    self._update_metrics(0, hit=True)
                else:
                    self._update_metrics(0, hit=False)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get multiple cache keys: {str(e)}")
            return {}
    
    async def set_multiple(
        self, 
        data: Dict[str, Any], 
        category: str = 'default',
        ttl: Optional[int] = None
    ) -> bool:
        """Set multiple cache values at once"""
        if not await self.connect():
            return False
        
        try:
            cache_ttl = self._get_ttl(category, ttl)
            
            # Use pipeline for efficiency
            pipe = self._redis.pipeline()
            
            for key, value in data.items():
                cache_key = self._build_key(key, category)
                serialized_value = self._serialize_value(value)
                pipe.setex(cache_key, cache_ttl, serialized_value)
            
            await pipe.execute()
            
            logger.debug(f"Set {len(data)} cache keys in category {category}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set multiple cache keys: {str(e)}")
            return False
    
    async def increment(self, key: str, amount: int = 1, category: str = 'default') -> Optional[int]:
        """Increment numeric cache value"""
        if not await self.connect():
            return None
        
        try:
            cache_key = self._build_key(key, category)
            result = await self._redis.incrby(cache_key, amount)
            
            # Set TTL if key is new
            if result == amount:
                cache_ttl = self._get_ttl(category)
                await self._redis.expire(cache_key, cache_ttl)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to increment cache key {key}: {str(e)}")
            return None
    
    async def add_to_set(self, key: str, value: str, category: str = 'default') -> bool:
        """Add value to Redis set"""
        if not await self.connect():
            return False
        
        try:
            cache_key = self._build_key(key, category)
            result = await self._redis.sadd(cache_key, value)
            
            # Set TTL for new sets
            if result > 0:
                cache_ttl = self._get_ttl(category)
                await self._redis.expire(cache_key, cache_ttl)
            
            return result > 0
            
        except Exception as e:
            logger.error(f"Failed to add to set {key}: {str(e)}")
            return False
    
    async def get_set_members(self, key: str, category: str = 'default') -> List[str]:
        """Get all members of a Redis set"""
        if not await self.connect():
            return []
        
        try:
            cache_key = self._build_key(key, category)
            members = await self._redis.smembers(cache_key)
            return list(members)
            
        except Exception as e:
            logger.error(f"Failed to get set members {key}: {str(e)}")
            return []
    
    def _update_metrics(self, response_time_ms: float, hit: bool):
        """Update cache performance metrics"""
        self._metrics.total_requests += 1
        
        if hit:
            self._metrics.cache_hits += 1
        else:
            self._metrics.cache_misses += 1
        
        # Update average response time
        current_total = self._metrics.average_response_time_ms * (self._metrics.total_requests - 1)
        self._metrics.average_response_time_ms = (current_total + response_time_ms) / self._metrics.total_requests
    
    async def get_cache_info(self) -> Dict[str, Any]:
        """Get Redis server information"""
        if not await self.connect():
            return {"error": "Not connected to Redis"}
        
        try:
            info = await self._redis.info()
            
            return {
                "connection_status": "connected",
                "redis_version": info.get("redis_version", "unknown"),
                "used_memory": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "uptime_seconds": info.get("uptime_in_seconds", 0)
            }
            
        except Exception as e:
            logger.error(f"Failed to get cache info: {str(e)}")
            return {"error": str(e)}
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get cache performance metrics"""
        cache_info = await self.get_cache_info()
        
        return {
            "service_metrics": asdict(self._metrics),
            "redis_info": cache_info,
            "configuration": {
                "default_ttl_seconds": self.default_ttl,
                "max_connections": self.max_connections,
                "key_prefix": self.key_prefix,
                "categories_configured": len(self.cache_configs)
            },
            "categories": {
                category: {
                    "ttl_seconds": config.get("ttl", self.default_ttl),
                    "prefix": config.get("prefix", "")
                }
                for category, config in self.cache_configs.items()
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive cache service health check"""
        try:
            if not await self.connect():
                return {
                    "service": "cache",
                    "status": "unhealthy",
                    "error": "Unable to connect to Redis"
                }
            
            # Test basic operations
            test_key = "health_check_test"
            test_value = "test_data"
            
            # Test set/get
            await self.set(test_key, test_value, 'temp_data', 60)
            retrieved = await self.get(test_key, 'temp_data')
            
            if retrieved != test_value:
                return {
                    "service": "cache",
                    "status": "unhealthy",
                    "error": "Set/Get operation failed"
                }
            
            # Clean up test key
            await self.delete(test_key, 'temp_data')
            
            # Get metrics
            metrics = await self.get_metrics()
            
            return {
                "service": "cache",
                "status": "healthy",
                "performance": {
                    "hit_rate_percent": round(self._metrics.hit_rate, 2),
                    "average_response_time_ms": round(self._metrics.average_response_time_ms, 2),
                    "total_requests": self._metrics.total_requests
                },
                "redis_status": metrics.get("redis_info", {}),
                "configuration_status": "configured"
            }
            
        except Exception as e:
            logger.error(f"Cache health check failed: {str(e)}")
            return {
                "service": "cache",
                "status": "unhealthy",
                "error": str(e)
            }


# Global service instance
cache_service = CacheService()


def get_cache_service() -> CacheService:
    """Get the global cache service instance"""
    return cache_service


# Decorator for automatic caching
def cached(category: str = 'default', ttl: Optional[int] = None, key_func: Optional[callable] = None):
    """Decorator for automatic function result caching"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key generation
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = hashlib.md5(":".join(key_parts).encode()).hexdigest()
            
            # Try to get from cache
            cached_result = await cache_service.get(cache_key, category)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache_service.set(cache_key, result, category, ttl)
            
            return result
        
        return wrapper
    return decorator 