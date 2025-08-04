"""
Deprecation utilities for API endpoints
"""
from functools import wraps
from typing import Callable, Optional
from fastapi import Request
from fastapi.responses import JSONResponse
import logging
import warnings

logger = logging.getLogger(__name__)


def deprecated_endpoint(
    alternative: str,
    removal_version: Optional[str] = None,
    message: Optional[str] = None
) -> Callable:
    """
    Decorator to mark endpoints as deprecated.
    
    Args:
        alternative: The alternative endpoint to use
        removal_version: Version when this endpoint will be removed
        message: Additional deprecation message
    
    Example:
        @deprecated_endpoint(
            alternative="/api/v1/versions/{version_id}/submit",
            removal_version="4.0.0"
        )
        @router.post("/old-endpoint")
        async def old_endpoint():
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find the request object in args/kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            # Log deprecation warning
            endpoint = func.__name__
            warning_msg = f"DEPRECATED: Endpoint '{endpoint}' is deprecated. Use '{alternative}' instead."
            if removal_version:
                warning_msg += f" Will be removed in version {removal_version}."
            if message:
                warning_msg += f" {message}"
            
            logger.warning(warning_msg)
            warnings.warn(warning_msg, DeprecationWarning, stacklevel=2)
            
            # Call the original function
            result = await func(*args, **kwargs)
            
            # Add deprecation headers to response
            if isinstance(result, dict):
                # Convert dict response to JSONResponse to add headers
                response = JSONResponse(content=result)
                response.headers["X-Deprecated"] = "true"
                response.headers["X-Alternative-Endpoint"] = alternative
                if removal_version:
                    response.headers["X-Removal-Version"] = removal_version
                response.headers["Warning"] = f'299 - "Deprecated API: Use {alternative}"'
                return response
            elif hasattr(result, 'headers'):
                # Add headers to existing response
                result.headers["X-Deprecated"] = "true"
                result.headers["X-Alternative-Endpoint"] = alternative
                if removal_version:
                    result.headers["X-Removal-Version"] = removal_version
                result.headers["Warning"] = f'299 - "Deprecated API: Use {alternative}"'
            
            return result
        
        # Mark the function as deprecated for documentation
        wrapper.__doc__ = f"**DEPRECATED**: Use `{alternative}` instead.\n\n{func.__doc__ or ''}"
        wrapper._deprecated = True
        wrapper._alternative = alternative
        
        return wrapper
    return decorator


def log_deprecated_usage(
    endpoint: str,
    alternative: str,
    user_id: Optional[int] = None,
    metadata: Optional[dict] = None
) -> None:
    """
    Log usage of deprecated endpoints for monitoring.
    
    This can be used to track which deprecated endpoints are still being used
    and by whom, helping to plan safe removal.
    """
    log_data = {
        "event": "deprecated_endpoint_usage",
        "endpoint": endpoint,
        "alternative": alternative,
        "user_id": user_id,
        "metadata": metadata or {}
    }
    logger.info(f"Deprecated endpoint usage: {log_data}")