"""
Enhanced permission system with database-driven RBAC
"""

from functools import wraps
from typing import Optional, List, Union, Callable
from fastapi import HTTPException, status

from app.core.exceptions import AuthorizationException
from app.services.permission_service import get_permission_service
from app.core.logging import get_logger
from app.core.config import settings
from app.core.auth import RoleChecker, UserRoles

logger = get_logger(__name__)


def require_permission(
    resource: str, 
    action: str, 
    resource_id_param: Optional[str] = None
):
    """
    Decorator to check permissions using the database-driven RBAC system with feature flag support
    
    Args:
        resource: Resource name (e.g., 'cycles', 'reports', 'planning')
        action: Action name (e.g., 'create', 'read', 'update', 'delete', 'execute')
        resource_id_param: Parameter name containing resource ID for resource-level checks
    
    Usage:
        @require_permission("reports", "update", resource_id_param="report_id")
        async def update_report(report_id: int, current_user: User = Depends(get_current_user)):
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current user from kwargs
            current_user = kwargs.get('current_user')
            if not current_user:
                raise AuthorizationException("User not authenticated")
            
            # RBAC is always enabled - no fallback
            
            # Get database session from kwargs
            db = kwargs.get('db')
            if not db:
                raise AuthorizationException("Database session not available")
            
            # Get resource ID if specified
            resource_id = None
            if resource_id_param and resource_id_param in kwargs:
                resource_id = kwargs[resource_id_param]
            
            # Check permission using service
            try:
                permission_service = await get_permission_service(db)
                has_permission = await permission_service.check_permission(
                    current_user.user_id,
                    resource,
                    action,
                    resource_id
                )
                
                if not has_permission:
                    logger.warning(
                        f"Permission denied for user {current_user.email} "
                        f"on {resource}:{action} (resource_id={resource_id})"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Permission denied: {resource}:{action}"
                    )
                
                logger.debug(
                    f"Permission granted for user {current_user.email} "
                    f"on {resource}:{action} (resource_id={resource_id})"
                )
                
            except Exception as e:
                logger.error(f"Error checking permission: {e}")
                if isinstance(e, HTTPException):
                    raise
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error checking permissions"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_any_permission(*permissions: tuple):
    """
    Decorator to check if user has ANY of the specified permissions
    
    Args:
        permissions: Tuples of (resource, action) pairs
    
    Usage:
        @require_any_permission(("reports", "read"), ("reports", "update"))
        async def view_or_edit_report(...):
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                raise AuthorizationException("User not authenticated")
            
            db = kwargs.get('db')
            if not db:
                raise AuthorizationException("Database session not available")
            
            permission_service = await get_permission_service(db)
            
            # Check each permission
            for resource, action in permissions:
                try:
                    has_permission = await permission_service.check_permission(
                        current_user.user_id,
                        resource,
                        action
                    )
                    if has_permission:
                        return await func(*args, **kwargs)
                except Exception:
                    continue
            
            # No permissions matched
            perm_strings = [f"{r}:{a}" for r, a in permissions]
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires any of: {', '.join(perm_strings)}"
            )
        
        return wrapper
    return decorator


def require_all_permissions(*permissions: tuple):
    """
    Decorator to check if user has ALL of the specified permissions
    
    Args:
        permissions: Tuples of (resource, action) pairs
    
    Usage:
        @require_all_permissions(("reports", "read"), ("reports", "approve"))
        async def review_and_approve_report(...):
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                raise AuthorizationException("User not authenticated")
            
            db = kwargs.get('db')
            if not db:
                raise AuthorizationException("Database session not available")
            
            permission_service = await get_permission_service(db)
            
            # Check all permissions
            for resource, action in permissions:
                try:
                    has_permission = await permission_service.check_permission(
                        current_user.user_id,
                        resource,
                        action
                    )
                    if not has_permission:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"Missing permission: {resource}:{action}"
                        )
                except HTTPException:
                    raise
                except Exception as e:
                    logger.error(f"Error checking permission {resource}:{action}: {e}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Error checking permissions"
                    )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# Backward compatibility wrapper
def check_permission_legacy(user_role: str, resource: str, action: str) -> bool:
    """
    Legacy permission check for backward compatibility
    Maps old role-based checks to new permission system
    """
    # This is a temporary mapping until all code is migrated
    role_permission_map = {
        "Admin": True,  # Admin has all permissions
        "Test Executive": {
            "cycles": ["create", "read", "update", "delete"],
            "reports": ["read", "assign"],
            "users": ["read", "assign"],
            "workflow": ["approve"]
        },
        "Tester": {
            "planning": ["execute", "upload", "create", "update"],
            "scoping": ["execute", "submit"],
            "testing": ["execute", "submit"],
            "observations": ["create", "submit", "delete"],
            "request_info": ["write", "read", "provide"]
        },
        "Report Owner": {
            "reports": ["read", "approve"],
            "scoping": ["approve"],
            "testing": ["review"],
            "observations": ["approve"]
        },
        "Report Owner Executive": {
            "reports": ["read", "override"],
            "workflow": ["override"],
            "observations": ["override"]
        },
        "Data Owner": {
            "data_owner": ["read", "upload"],
            "request_info": ["provide"]
        },
        "Data Executive": {
            "lobs": ["read", "manage"],
            "data_owner": ["assign", "escalate"]
        }
    }
    
    if user_role == "Admin":
        return True
    
    role_perms = role_permission_map.get(user_role, {})
    if isinstance(role_perms, dict):
        resource_actions = role_perms.get(resource, [])
        return action in resource_actions
    
    return False


def get_legacy_roles_for_permission(resource: str, action: str) -> List[str]:
    """
    Map permission requirements to legacy roles for backward compatibility
    """
    # Permission to role mapping
    permission_role_map = {
        # Cycles permissions
        ("cycles", "create"): [UserRoles.TEST_EXECUTIVE],
        ("cycles", "read"): [UserRoles.TEST_EXECUTIVE, UserRoles.REPORT_OWNER_EXECUTIVE, UserRoles.TESTER, UserRoles.REPORT_OWNER, UserRoles.DATA_EXECUTIVE],
        ("cycles", "update"): [UserRoles.TEST_EXECUTIVE],
        ("cycles", "delete"): [UserRoles.TEST_EXECUTIVE],
        ("cycles", "assign"): [UserRoles.TEST_EXECUTIVE],
        
        # Reports permissions
        ("reports", "read"): [UserRoles.TEST_EXECUTIVE, UserRoles.REPORT_OWNER, UserRoles.REPORT_OWNER_EXECUTIVE, UserRoles.TESTER, UserRoles.DATA_OWNER, UserRoles.DATA_EXECUTIVE],
        ("reports", "update"): [UserRoles.TEST_EXECUTIVE],
        ("reports", "approve"): [UserRoles.REPORT_OWNER],
        ("reports", "override"): [UserRoles.REPORT_OWNER_EXECUTIVE],
        ("reports", "assign"): [UserRoles.TEST_EXECUTIVE],
        
        # Planning permissions
        ("planning", "execute"): [UserRoles.TESTER],
        ("planning", "upload"): [UserRoles.TESTER],
        ("planning", "create"): [UserRoles.TESTER],
        ("planning", "update"): [UserRoles.TESTER],
        ("planning", "delete"): [UserRoles.TESTER],
        ("planning", "generate"): [UserRoles.TESTER],
        ("planning", "complete"): [UserRoles.TESTER],
        ("planning", "approve"): [UserRoles.TEST_EXECUTIVE],
        
        # Scoping permissions
        ("scoping", "execute"): [UserRoles.TESTER],
        ("scoping", "generate"): [UserRoles.TESTER],
        ("scoping", "submit"): [UserRoles.TESTER],
        ("scoping", "approve"): [UserRoles.REPORT_OWNER],
        ("scoping", "complete"): [UserRoles.TESTER],
        
        # Sample Selection permissions
        ("sample_selection", "read"): [UserRoles.TESTER, UserRoles.REPORT_OWNER],
        ("sample_selection", "execute"): [UserRoles.TESTER],
        ("sample_selection", "generate"): [UserRoles.TESTER],
        ("sample_selection", "upload"): [UserRoles.TESTER],
        ("sample_selection", "approve"): [UserRoles.REPORT_OWNER],
        ("sample_selection", "complete"): [UserRoles.TESTER],
        
        # Data Provider permissions
        ("data_provider", "read"): [UserRoles.DATA_OWNER, UserRoles.DATA_EXECUTIVE, UserRoles.TESTER],
        ("data_provider", "identify"): [UserRoles.DATA_EXECUTIVE],
        ("data_provider", "assign"): [UserRoles.DATA_EXECUTIVE],
        ("data_provider", "execute"): [UserRoles.TESTER],
        ("data_provider", "upload"): [UserRoles.DATA_OWNER],
        ("data_provider", "escalate"): [UserRoles.DATA_EXECUTIVE],
        ("data_provider", "complete"): [UserRoles.TESTER],
        
        # Request Info permissions
        ("request_info", "read"): [UserRoles.TESTER, UserRoles.DATA_OWNER, UserRoles.DATA_EXECUTIVE],
        ("request_info", "write"): [UserRoles.TESTER, UserRoles.DATA_OWNER],
        ("request_info", "provide"): [UserRoles.TESTER, UserRoles.DATA_OWNER],
        
        # Testing permissions
        ("testing", "read"): [UserRoles.TESTER, UserRoles.REPORT_OWNER],
        ("testing", "execute"): [UserRoles.TESTER],
        ("testing", "submit"): [UserRoles.TESTER],
        ("testing", "review"): [UserRoles.REPORT_OWNER],
        ("testing", "approve"): [UserRoles.REPORT_OWNER],
        
        # Observation permissions
        ("observations", "create"): [UserRoles.TESTER],
        ("observations", "submit"): [UserRoles.TESTER],
        ("observations", "review"): [UserRoles.REPORT_OWNER],
        ("observations", "approve"): [UserRoles.REPORT_OWNER],
        ("observations", "override"): [UserRoles.REPORT_OWNER_EXECUTIVE],
        ("observations", "delete"): [UserRoles.TESTER],
        
        # User permissions
        ("users", "read"): [UserRoles.TEST_EXECUTIVE, UserRoles.DATA_EXECUTIVE],
        ("users", "create"): [UserRoles.ADMIN],
        ("users", "update"): [UserRoles.ADMIN],
        ("users", "delete"): [UserRoles.ADMIN],
        
        # LOB permissions
        ("lobs", "read"): [UserRoles.DATA_EXECUTIVE, UserRoles.TESTER, UserRoles.REPORT_OWNER, UserRoles.TEST_EXECUTIVE],
        ("lobs", "manage"): [UserRoles.DATA_EXECUTIVE],
        
        # System permissions
        ("system", "admin"): [UserRoles.ADMIN],
        ("system", "configure"): [UserRoles.ADMIN],
        
        # Permission management
        ("permissions", "manage"): [UserRoles.ADMIN],
    }
    
    # Always include ADMIN role for any permission
    roles = [UserRoles.ADMIN]
    
    # Add specific roles for the permission
    specific_roles = permission_role_map.get((resource, action), [])
    roles.extend(specific_roles)
    
    return list(set(roles))  # Remove duplicates