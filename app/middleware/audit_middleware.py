"""
Middleware for setting user context for audit tracking
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.context import set_current_user_context, clear_current_user_context
from app.core.auth import decode_access_token
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware that extracts user information from JWT token
    and sets it in the context for audit tracking.
    """
    
    async def dispatch(self, request: Request, call_next):
        """
        Process the request and set user context if authenticated.
        """
        logger.info(f"[AuditMiddleware] Processing {request.method} {request.url.path}")
        try:
            # Extract token from Authorization header
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                
                try:
                    # Decode the token to get user information
                    payload = decode_access_token(token)
                    if payload:
                        # Extract user_id from sub field (stored as string)
                        user_id_str = payload.get("sub")
                        user_id = None
                        if user_id_str:
                            try:
                                user_id = int(user_id_str)
                            except (ValueError, TypeError):
                                logger.debug(f"Could not convert user_id to int: {user_id_str}")
                        
                        # Set user context
                        user_context = {
                            "user_id": user_id,
                            "email": payload.get("email"),
                            "role": payload.get("role")
                        }
                        set_current_user_context(user_context)
                except Exception as e:
                    # Invalid token - proceed without user context
                    logger.debug(f"Could not decode token: {e}")
            
            # Process the request
            response = await call_next(request)
            
            return response
            
        finally:
            # Clear the context after the request
            clear_current_user_context()