"""Performance monitoring middleware"""
import time
import logging
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from prometheus_client import Counter, Histogram, Gauge
import psutil
import asyncio

from app.core.performance import performance_monitor

logger = logging.getLogger(__name__)

# Prometheus metrics
request_count = Counter(
    'synapse_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'synapse_http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

active_requests = Gauge(
    'synapse_http_requests_active',
    'Active HTTP requests'
)

system_memory = Gauge(
    'synapse_system_memory_percent',
    'System memory usage percentage'
)

system_cpu = Gauge(
    'synapse_system_cpu_percent',
    'System CPU usage percentage'
)


class PerformanceMiddleware(BaseHTTPMiddleware):
    """Middleware for performance monitoring"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Start timing
        start_time = time.time()
        
        # Get endpoint path
        path = request.url.path
        method = request.method
        
        # Skip health checks and metrics endpoints
        if path in ['/health', '/metrics', '/']:
            return await call_next(request)
        
        # Increment active requests
        active_requests.inc()
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Record metrics
            request_count.labels(
                method=method,
                endpoint=path,
                status=response.status_code
            ).inc()
            
            request_duration.labels(
                method=method,
                endpoint=path
            ).observe(duration)
            
            # Record in custom performance monitor
            performance_monitor.record_metric(
                f"http_{method}_{path}",
                duration,
                {
                    "status_code": response.status_code,
                    "content_length": response.headers.get("content-length", 0)
                }
            )
            
            # Add performance headers
            response.headers["X-Response-Time"] = f"{duration:.3f}"
            
            # Log slow requests
            if duration > 1.0:
                logger.warning(
                    f"Slow request: {method} {path} took {duration:.2f}s",
                    extra={
                        "method": method,
                        "path": path,
                        "duration": duration,
                        "status_code": response.status_code
                    }
                )
            
            return response
            
        finally:
            # Decrement active requests
            active_requests.dec()


class ResourceMonitoringMiddleware(BaseHTTPMiddleware):
    """Monitor system resources"""
    
    def __init__(self, app):
        super().__init__(app)
        # Start background monitoring
        asyncio.create_task(self._monitor_resources())
    
    async def _monitor_resources(self):
        """Background task to monitor system resources"""
        while True:
            try:
                # Update memory usage
                memory = psutil.virtual_memory()
                system_memory.set(memory.percent)
                
                # Update CPU usage
                cpu = psutil.cpu_percent(interval=1)
                system_cpu.set(cpu)
                
                # Log if resources are high
                if memory.percent > 80:
                    logger.warning(f"High memory usage: {memory.percent}%")
                
                if cpu > 80:
                    logger.warning(f"High CPU usage: {cpu}%")
                
                # Sleep for 30 seconds
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Resource monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        return await call_next(request)


class CacheMiddleware(BaseHTTPMiddleware):
    """Middleware for caching responses"""
    
    def __init__(self, app):
        super().__init__(app)
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Only cache GET requests
        if request.method != "GET":
            return await call_next(request)
        
        # Skip if no-cache header
        if request.headers.get("cache-control") == "no-cache":
            return await call_next(request)
        
        # Generate cache key
        cache_key = f"{request.method}:{request.url.path}:{request.url.query}"
        
        # Check cache
        if cache_key in self._cache:
            cached_response, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self._cache_ttl:
                # Return cached response
                response = Response(
                    content=cached_response["content"],
                    status_code=cached_response["status_code"],
                    headers=cached_response["headers"]
                )
                response.headers["X-Cache"] = "HIT"
                return response
        
        # Process request
        response = await call_next(request)
        
        # Cache successful GET responses
        if response.status_code == 200 and request.method == "GET":
            # Read response body
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            
            # Cache response
            self._cache[cache_key] = ({
                "content": body,
                "status_code": response.status_code,
                "headers": dict(response.headers)
            }, time.time())
            
            # Create new response with body
            response = Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
            response.headers["X-Cache"] = "MISS"
        
        return response


class CompressionMiddleware(BaseHTTPMiddleware):
    """Middleware for response compression"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check if client accepts gzip
        accept_encoding = request.headers.get("accept-encoding", "")
        
        response = await call_next(request)
        
        # Only compress if client accepts gzip and response is large enough
        if "gzip" in accept_encoding and len(response.body) > 1000:
            import gzip
            
            # Compress response body
            compressed_body = gzip.compress(response.body)
            
            # Only use compressed if it's smaller
            if len(compressed_body) < len(response.body):
                response.body = compressed_body
                response.headers["content-encoding"] = "gzip"
                response.headers["content-length"] = str(len(compressed_body))
        
        return response