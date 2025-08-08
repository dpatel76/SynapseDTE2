"""
SynapseDT - End-to-End Data Testing System with Clean Architecture
Main FastAPI application entry point
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import structlog
import time
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import engine, Base, init_db, close_db
from app.core.logging import setup_logging
from app.api.v1.api import api_router
from app.core.exceptions import (
    ValidationException,
    AuthenticationException,
    AuthorizationException,
    NotFoundException,
    BusinessLogicException
)
from app.core.middleware import setup_middleware
from app.middleware.audit_middleware import AuditMiddleware
from app.models.audit_mixin import register_audit_listeners

# Setup structured logging
setup_logging()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting SynapseDT application - Clean Architecture Edition")
    
    # Initialize database
    await init_db()
    
    # Register audit listeners for models
    # NOTE: Commented out to switch to explicit audit field handling
    # register_audit_listeners()
    # logger.info("Audit listeners registered for user tracking")
    
    # Import and check job manager
    from app.core.background_jobs import job_manager
    logger.info(f"Job manager initialized with {len(job_manager.jobs)} jobs")
    
    # Setup clean architecture dependencies
    from app.infrastructure.di import setup_dependencies
    setup_dependencies()
    logger.info("Clean architecture dependencies initialized")
    
    # Initialize Temporal client
    try:
        from app.temporal.client import get_temporal_client
        app.state.temporal_client = await get_temporal_client()
        logger.info("Temporal client initialized and connected")
    except Exception as e:
        logger.warning(f"Failed to initialize Temporal client: {e}")
        logger.info("Application will continue without Temporal workflow support")
        app.state.temporal_client = None
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    await close_db()
    logger.info("Shutting down SynapseDT application")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="End-to-End Data Testing System for Regulatory and Risk Management Reports - Clean Architecture Edition",
    openapi_url=f"{settings.api_v1_str}/openapi.json",
    docs_url=f"{settings.api_v1_str}/docs",
    redoc_url=f"{settings.api_v1_str}/redoc",
    lifespan=lifespan
)

# Add CORS middleware with permissive settings for development
# This should come BEFORE other middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:8001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Add middleware to ensure CORS headers on all responses, including errors
@app.middleware("http")
async def ensure_cors_on_errors(request: Request, call_next):
    """Ensure CORS headers are present on all responses, including error responses"""
    logger.info(f"[CORS MIDDLEWARE] Processing {request.method} {request.url}")
    try:
        logger.info(f"[CORS MIDDLEWARE] Calling next handler...")
        response = await call_next(request)
        logger.info(f"[CORS MIDDLEWARE] Got response with status {response.status_code}")
        # Add CORS headers if they're missing (shouldn't happen with CORSMiddleware, but just in case)
        origin = request.headers.get("origin")
        if origin in ["http://localhost:3000", "http://localhost:3001"]:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
        return response
    except Exception as e:
        # For any unhandled exceptions, create a response with proper CORS headers
        logger.error(f"Unhandled exception in middleware: {e}")
        
        from fastapi.responses import JSONResponse
        response = JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
        # Ensure CORS headers are set
        origin = request.headers.get("origin")
        if origin in ["http://localhost:3000", "http://localhost:3001"]:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "*"
            response.headers["Access-Control-Allow-Headers"] = "*"
        return response

# Setup advanced security middleware
setup_middleware(app)

# Add audit middleware for user tracking
app.add_middleware(AuditMiddleware)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure this appropriately for production
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time header to response"""
    start_time = time.time()
    logger.info(f"[PROCESS TIME MIDDLEWARE] Processing {request.method} {request.url}")
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"[PROCESS TIME MIDDLEWARE] Completed in {process_time:.3f}s")
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Log all HTTP requests"""
    start_time = time.time()
    
    # Log request
    logger.info(
        "HTTP request started",
        method=request.method,
        url=str(request.url),
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(
        "HTTP request completed",
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
        process_time=round(process_time, 4),
    )
    
    return response


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response


# Exception handlers
@app.exception_handler(ValidationException)
async def validation_exception_handler(request: Request, exc: ValidationException):
    """Handle validation exceptions"""
    logger.warning(
        "Validation error",
        error=str(exc),
        url=str(request.url),
        method=request.method
    )
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc), "type": "validation_error"}
    )


@app.exception_handler(AuthenticationException)
async def authentication_exception_handler(request: Request, exc: AuthenticationException):
    """Handle authentication exceptions"""
    logger.warning(
        "Authentication error",
        error=str(exc),
        url=str(request.url),
        method=request.method
    )
    return JSONResponse(
        status_code=401,
        content={"detail": str(exc), "type": "authentication_error"}
    )


@app.exception_handler(AuthorizationException)
async def authorization_exception_handler(request: Request, exc: AuthorizationException):
    """Handle authorization exceptions"""
    logger.warning(
        "Authorization error",
        error=str(exc),
        url=str(request.url),
        method=request.method
    )
    return JSONResponse(
        status_code=403,
        content={"detail": str(exc), "type": "authorization_error"}
    )


@app.exception_handler(NotFoundException)
async def not_found_exception_handler(request: Request, exc: NotFoundException):
    """Handle not found exceptions"""
    logger.warning(
        "Resource not found",
        error=str(exc),
        url=str(request.url),
        method=request.method
    )
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc), "type": "not_found_error"}
    )


@app.exception_handler(BusinessLogicException)
async def business_logic_exception_handler(request: Request, exc: BusinessLogicException):
    """Handle business logic exceptions"""
    logger.error(
        "Business logic error",
        error=str(exc),
        url=str(request.url),
        method=request.method
    )
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc), "type": "business_logic_error"}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions"""
    logger.error(
        "Unhandled exception",
        error=str(exc),
        error_type=type(exc).__name__,
        url=str(request.url),
        method=request.method,
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": "internal_error"}
    )


# Include API router
app.include_router(api_router, prefix=settings.api_v1_str)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "SynapseDT - End-to-End Data Testing System",
        "version": settings.app_version,
        "architecture": "clean",
        "status": "running",
        "docs_url": f"{settings.api_v1_str}/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": settings.app_version,
        "architecture": "clean"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )