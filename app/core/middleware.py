"""
Advanced Security and Error Handling Middleware
Provides rate limiting, input validation, and comprehensive error handling
"""

import time
import json
import logging
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_413_REQUEST_ENTITY_TOO_LARGE, HTTP_429_TOO_MANY_REQUESTS
import asyncio
from collections import defaultdict, deque
from datetime import datetime, timedelta
import re
import ipaddress

logger = logging.getLogger(__name__)


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware with sliding window"""
    
    def __init__(self, app: FastAPI, calls_per_minute: int = 100, burst_limit: int = 20):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute
        self.burst_limit = burst_limit
        self.request_times: Dict[str, deque] = defaultdict(deque)
        self.burst_tracker: Dict[str, List[float]] = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next) -> Response:
        logger.info(f"[RateLimitingMiddleware] Processing {request.method} {request.url.path}")
        client_ip = self._get_client_ip(request)
        current_time = time.time()
        
        # Check burst limit (requests in last 10 seconds)
        burst_window = current_time - 10
        self.burst_tracker[client_ip] = [
            req_time for req_time in self.burst_tracker[client_ip] 
            if req_time > burst_window
        ]
        
        if len(self.burst_tracker[client_ip]) >= self.burst_limit:
            logger.warning(f"Rate limit exceeded (burst) for IP: {client_ip}")
            response = JSONResponse(
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded - burst protection"}
            )
            # Add CORS headers for rate limit responses
            origin = request.headers.get("origin")
            if origin in ["http://localhost:3000", "http://localhost:3001"]:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = "true"
            return response
        
        # Check per-minute limit
        minute_window = current_time - 60
        request_times = self.request_times[client_ip]
        
        # Remove old requests outside the window
        while request_times and request_times[0] < minute_window:
            request_times.popleft()
        
        if len(request_times) >= self.calls_per_minute:
            logger.warning(f"Rate limit exceeded (per-minute) for IP: {client_ip}")
            response = JSONResponse(
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded - too many requests per minute"}
            )
            # Add CORS headers for rate limit responses
            origin = request.headers.get("origin")
            if origin in ["http://localhost:3000", "http://localhost:3001"]:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = "true"
            return response
        
        # Record this request
        request_times.append(current_time)
        self.burst_tracker[client_ip].append(current_time)
        
        logger.info(f"[RateLimitingMiddleware] Calling next handler for {request.url.path}")
        response = await call_next(request)
        logger.info(f"[RateLimitingMiddleware] Completed {request.url.path}")
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP handling proxy headers"""
        # Check for forwarded IP
        forwarded_ip = request.headers.get("X-Forwarded-For")
        if forwarded_ip:
            return forwarded_ip.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"


class InputValidationMiddleware(BaseHTTPMiddleware):
    """Input validation and sanitization middleware"""
    
    MALICIOUS_PATTERNS = [
        r"<script[^>]*>.*?</script>",  # XSS
        r"javascript:",  # JavaScript injection
        r"vbscript:",   # VBScript injection
        r"onload\s*=",  # Event handler injection
        r"onerror\s*=", # Error handler injection
        r"(\bUNION\b|\bSELECT\b|\bINSERT\b|\bDELETE\b|\bDROP\b|\bCREATE\b).*?\b(FROM|INTO|TABLE)\b",  # SQL injection
        r"../",  # Path traversal
        r"\.\.\\",  # Windows path traversal
    ]
    
    # Endpoints that should have relaxed validation for legitimate long text content
    RELAXED_VALIDATION_ENDPOINTS = [
        "/api/v1/llm/generate-attributes",
        "/api/v1/planning",
        "/api/v1/documents",
        "/api/v1/scoping",
        "/api/v1/rfi",  # RFI endpoints need to handle SQL queries
        "/api/v1/request-info",  # Request info endpoints need to handle SQL queries for data source validation
        "/api/v1/observation-enhanced"  # Observation endpoints need to handle long descriptions
    ]
    
    MAX_REQUEST_SIZE = 20 * 1024 * 1024  # 20MB
    MAX_FIELD_LENGTH = 10000
    MAX_FIELD_LENGTH_RELAXED = 100000  # 100KB for LLM endpoints
    
    def __init__(self, app: FastAPI):
        super().__init__(app)
        self.patterns = [re.compile(pattern, re.IGNORECASE | re.DOTALL) for pattern in self.MALICIOUS_PATTERNS]
    
    async def dispatch(self, request: Request, call_next) -> Response:
        logger.info(f"[InputValidationMiddleware] Processing {request.method} {request.url.path}")
        # Completely skip validation for LLM endpoints
        if "/api/v1/llm/" in str(request.url.path):
            logger.info(f"Bypassing all security validation for LLM endpoint: {request.url.path}")
            response = await call_next(request)
            return response
        
        # Also bypass validation for planning endpoints when they contain LLM data
        if "/api/v1/planning/" in str(request.url.path) and request.method == "POST":
            logger.info(f"Bypassing security validation for planning POST: {request.url.path}")
            response = await call_next(request)
            return response
        
        # Bypass validation for query-validation endpoint that needs to accept SQL queries
        if "/api/v1/request-info/query-validation" in str(request.url.path):
            logger.info(f"Bypassing security validation for query validation endpoint: {request.url.path}")
            response = await call_next(request)
            return response
        
        # Bypass validation for query-evidence endpoint that needs to accept SQL queries
        if "/api/v1/request-info/query-evidence" in str(request.url.path):
            logger.info(f"Bypassing security validation for query evidence endpoint: {request.url.path}")
            response = await call_next(request)
            return response
        
        # Check if this is a relaxed validation endpoint
        is_relaxed_endpoint = any(endpoint in str(request.url.path) for endpoint in self.RELAXED_VALIDATION_ENDPOINTS)
        
        # Check request size
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.MAX_REQUEST_SIZE:
            logger.warning(f"Request too large: {content_length} bytes from {self._get_client_ip(request)}")
            return JSONResponse(
                status_code=HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={"detail": "Request entity too large"}
            )
        
        # Validate request content if it's JSON
        if request.headers.get("content-type", "").startswith("application/json"):
            logger.info(f"[InputValidationMiddleware] Reading body for {request.url.path}")
            try:
                body = await request.body()
                logger.info(f"[InputValidationMiddleware] Body read: {len(body)} bytes")
                if len(body) > self.MAX_REQUEST_SIZE:
                    return JSONResponse(
                        status_code=HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        content={"detail": "Request body too large"}
                    )
                
                if body:
                    try:
                        json_data = json.loads(body)
                        if not self._validate_json_data(json_data, is_relaxed_endpoint):
                            logger.warning(f"Malicious input detected from {self._get_client_ip(request)}")
                            return JSONResponse(
                                status_code=400,
                                content={"detail": "Invalid input detected"}
                            )
                    except json.JSONDecodeError:
                        return JSONResponse(
                            status_code=400,
                            content={"detail": "Invalid JSON format"}
                        )
                
                # CRITICAL: Set up the request to allow re-reading the body
                # This is needed because body() can only be called once
                async def receive():
                    return {"type": "http.request", "body": body}
                
                request._receive = receive
                
            except Exception as e:
                logger.error(f"Error validating request: {str(e)}")
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Request validation failed"}
                )
        
        response = await call_next(request)
        return response
    
    def _validate_json_data(self, data: Any, is_relaxed: bool = False) -> bool:
        """Recursively validate JSON data for malicious patterns"""
        max_length = self.MAX_FIELD_LENGTH_RELAXED if is_relaxed else self.MAX_FIELD_LENGTH
        
        if isinstance(data, dict):
            for key, value in data.items():
                if not self._validate_string(str(key), is_relaxed) or not self._validate_json_data(value, is_relaxed):
                    return False
        elif isinstance(data, list):
            for item in data:
                if not self._validate_json_data(item, is_relaxed):
                    return False
        elif isinstance(data, str):
            if not self._validate_string(data, is_relaxed):
                return False
            if len(data) > max_length:
                return False
        
        return True
    
    def _validate_string(self, text: str, is_relaxed: bool = False) -> bool:
        """Check string for malicious patterns"""
        # For relaxed endpoints, only check for critical security patterns
        if is_relaxed:
            critical_patterns = [
                r"<script[^>]*>.*?</script>",  # XSS
                r"javascript:",  # JavaScript injection
                r"(\bUNION\b|\bSELECT\b|\bINSERT\b|\bDELETE\b|\bDROP\b|\bCREATE\b).*?\b(FROM|INTO|TABLE)\b",  # SQL injection
            ]
            relaxed_compiled_patterns = [re.compile(pattern, re.IGNORECASE | re.DOTALL) for pattern in critical_patterns]
            for pattern in relaxed_compiled_patterns:
                if pattern.search(text):
                    return False
        else:
            # Full validation for non-relaxed endpoints
            for pattern in self.patterns:
                if pattern.search(text):
                    return False
        return True
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP"""
        return request.headers.get("X-Real-IP", request.client.host if request.client else "unknown")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'"
        
        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Comprehensive error handling middleware"""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        try:
            response = await call_next(request)
            return response
        except HTTPException as e:
            # Log HTTP exceptions
            logger.warning(f"HTTP Exception {e.status_code}: {e.detail} for {request.url}")
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail}
            )
        except ConnectionError as e:
            logger.error(f"Database connection error: {str(e)}")
            return JSONResponse(
                status_code=503,
                content={"detail": "Service temporarily unavailable"}
            )
        except TimeoutError as e:
            logger.error(f"Request timeout: {str(e)}")
            return JSONResponse(
                status_code=504,
                content={"detail": "Request timeout"}
            )
        except Exception as e:
            # Log unexpected errors
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"}
            )


class CORSMiddleware(BaseHTTPMiddleware):
    """Custom CORS middleware with security controls"""
    
    ALLOWED_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:3001", 
        "https://synapse-frontend.company.com"
    ]
    
    ALLOWED_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    ALLOWED_HEADERS = ["Authorization", "Content-Type", "X-Requested-With"]
    
    async def dispatch(self, request: Request, call_next) -> Response:
        origin = request.headers.get("origin")
        
        # Handle preflight requests
        if request.method == "OPTIONS":
            response = Response()
            if origin in self.ALLOWED_ORIGINS:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Methods"] = ", ".join(self.ALLOWED_METHODS)
                response.headers["Access-Control-Allow-Headers"] = ", ".join(self.ALLOWED_HEADERS)
                response.headers["Access-Control-Max-Age"] = "600"
            return response
        
        response = await call_next(request)
        
        # Add CORS headers to actual requests
        if origin in self.ALLOWED_ORIGINS:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
        
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Request logging with security event tracking"""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()
        client_ip = request.headers.get("X-Real-IP", request.client.host if request.client else "unknown")
        
        # Log request with more detail
        logger.info(f"[REQUEST START] {request.method} {request.url} from {client_ip}")
        
        # Log headers for debugging
        if str(request.url.path).endswith("/login"):
            logger.info(f"[LOGIN REQUEST] Headers: {dict(request.headers)}")
        
        try:
            logger.info(f"[MIDDLEWARE] About to call next handler at {time.time() - start_time:.3f}s")
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log response
            logger.info(f"[RESPONSE] Status {response.status_code} in {process_time:.3f}s")
            
            # Track security events
            if response.status_code == 401:
                self._log_security_event("UNAUTHORIZED_ACCESS", client_ip, request.url)
            elif response.status_code == 403:
                self._log_security_event("FORBIDDEN_ACCESS", client_ip, request.url)
            elif response.status_code == 429:
                self._log_security_event("RATE_LIMIT_EXCEEDED", client_ip, request.url)
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(f"[REQUEST FAILED] Failed in {process_time:.3f}s: {str(e)}")
            raise
    
    def _log_security_event(self, event_type: str, client_ip: str, url: str):
        """Log security events for monitoring"""
        from app.core.security import SecurityAudit
        SecurityAudit.log_security_event(
            event_type,
            None,  # User ID not available at middleware level
            {
                "client_ip": client_ip,
                "url": str(url),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


def setup_middleware(app: FastAPI):
    """Setup all middleware in correct order"""
    # Add in reverse order since middleware wraps around
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    # Custom CORS middleware disabled - using FastAPI's built-in CORS middleware instead
    # app.add_middleware(CORSMiddleware)
    # DISABLED - Causing request body reading issues in containerized environment
    # The InputValidationMiddleware reads the request body but doesn't properly
    # reconstruct it for FastAPI to read again, causing timeouts
    # app.add_middleware(InputValidationMiddleware)
    # Very high limits for development - essentially disabling rate limiting
    # In production, these should be much lower (e.g., 100 calls/min, 20 burst)
    app.add_middleware(RateLimitingMiddleware, calls_per_minute=1000, burst_limit=500)
    
    logger.info("Security middleware configured successfully") 