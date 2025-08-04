"""
Request context management for tracking current user
"""

from contextvars import ContextVar
from typing import Optional, Dict, Any

# Context variable to store current user information
_user_context: ContextVar[Optional[Dict[str, Any]]] = ContextVar('user_context', default=None)


def set_current_user_context(user_data: Dict[str, Any]) -> None:
    """
    Set the current user context for the request.
    
    Args:
        user_data: Dictionary containing user information (user_id, email, role, etc.)
    """
    _user_context.set(user_data)


def get_current_user_context() -> Optional[Dict[str, Any]]:
    """
    Get the current user context.
    
    Returns:
        Dictionary with user information or None if not in request context
    """
    return _user_context.get()


def clear_current_user_context() -> None:
    """
    Clear the current user context.
    Should be called at the end of each request.
    """
    _user_context.set(None)