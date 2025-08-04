"""
FastAPI dependencies for authentication, database, and authorization
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import verify_token, get_user_by_id, UserRoles
from app.models.user import User
from app.core.exceptions import AuthenticationException, AuthorizationException
from app.core.background_jobs import job_manager

# Security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token"""
    try:
        # Verify token and get payload
        payload = verify_token(credentials.credentials)
        user_id: int = payload.get("sub")
        
        if user_id is None:
            raise AuthenticationException("Invalid token: missing user ID")
        
        # Get user from database
        user = await get_user_by_id(db, user_id)
        if user is None:
            raise AuthenticationException("User not found")
        
        if not user.is_active:
            raise AuthenticationException("User account is inactive")
        
        return user
        
    except AuthenticationException:
        raise
    except Exception as e:
        raise AuthenticationException(f"Authentication failed: {str(e)}")


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> int:
    """Get current user ID from JWT token - for clean architecture"""
    try:
        # Verify token and get payload
        payload = verify_token(credentials.credentials)
        user_id: int = payload.get("sub")
        
        if user_id is None:
            raise AuthenticationException("Invalid token: missing user ID")
        
        return user_id
        
    except Exception as e:
        raise AuthenticationException(f"Authentication failed: {str(e)}")


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user (alias for clarity)"""
    return current_user


def require_roles(allowed_roles: list):
    """Dependency factory for role-based access control"""
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        # Admin role has access to everything
        if current_user.role == UserRoles.ADMIN:
            return current_user
            
        if current_user.role not in allowed_roles:
            raise AuthorizationException(
                f"Access denied. Required roles: {allowed_roles}, user role: {current_user.role}"
            )
        return current_user
    return role_checker


def require_lob_access(required_lob_id: int):
    """Dependency factory for LOB-based access control"""
    async def lob_checker(current_user: User = Depends(get_current_user)) -> User:
        # Admin role has access to all LOBs
        if current_user.role == UserRoles.ADMIN:
            return current_user
            
        # System admins and executives may have broader access
        if current_user.role in [UserRoles.REPORT_OWNER_EXECUTIVE, UserRoles.DATA_EXECUTIVE]:
            return current_user
        
        if current_user.lob_id != required_lob_id:
            raise AuthorizationException(
                f"Access denied. User does not have access to LOB {required_lob_id}"
            )
        return current_user
    return lob_checker


# Pre-defined role dependencies for common use cases
require_admin = require_roles([UserRoles.ADMIN])
require_tester = require_roles([UserRoles.TESTER])
require_test_manager = require_roles([UserRoles.TEST_EXECUTIVE])
require_report_owner = require_roles([UserRoles.REPORT_OWNER])
require_report_owner_executive = require_roles([UserRoles.REPORT_OWNER_EXECUTIVE])
require_data_owner = require_roles([UserRoles.DATA_OWNER])
require_cdo = require_roles([UserRoles.DATA_EXECUTIVE])

# Combined role dependencies
require_management = require_roles(UserRoles.management_roles())
require_testing_roles = require_roles(UserRoles.testing_roles())
require_approval_roles = require_roles(UserRoles.approval_roles())

# Workflow-specific dependencies
require_planning_access = require_roles([UserRoles.TESTER])
require_scoping_approval = require_roles([UserRoles.REPORT_OWNER, UserRoles.REPORT_OWNER_EXECUTIVE])
require_data_owner_assignment = require_roles([UserRoles.DATA_EXECUTIVE])
require_sample_approval = require_roles([UserRoles.REPORT_OWNER, UserRoles.REPORT_OWNER_EXECUTIVE])
require_test_execution = require_roles([UserRoles.TESTER])
require_observation_approval = require_roles([UserRoles.REPORT_OWNER, UserRoles.REPORT_OWNER_EXECUTIVE])


class CurrentUser:
    """Utility class for getting current user with different access levels"""
    
    @staticmethod
    async def get(credentials: HTTPAuthorizationCredentials = Depends(security), 
                  db: AsyncSession = Depends(get_db)) -> User:
        """Get current user (basic authentication)"""
        return await get_current_user(credentials, db)
    
    @staticmethod
    async def admin(current_user: User = Depends(require_admin)) -> User:
        """Get current user with Admin role"""
        return current_user
    
    @staticmethod
    async def tester(current_user: User = Depends(require_tester)) -> User:
        """Get current user with Tester role"""
        return current_user
    
    @staticmethod
    async def test_manager(current_user: User = Depends(require_test_manager)) -> User:
        """Get current user with Test Executive role"""
        return current_user
    
    @staticmethod
    async def report_owner(current_user: User = Depends(require_report_owner)) -> User:
        """Get current user with Report Owner role"""
        return current_user
    
    @staticmethod
    async def report_owner_executive(current_user: User = Depends(require_report_owner_executive)) -> User:
        """Get current user with Report Owner Executive role"""
        return current_user
    
    @staticmethod
    async def data_owner(current_user: User = Depends(require_data_owner)) -> User:
        """Get current user with Data Owner role"""
        return current_user
    
    @staticmethod
    async def cdo(current_user: User = Depends(require_cdo)) -> User:
        """Get current user with Data Executive role"""
        return current_user
    
    @staticmethod
    async def management(current_user: User = Depends(require_management)) -> User:
        """Get current user with management role"""
        return current_user


# Optional authentication (for public endpoints that can benefit from user context)
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """Get current user if authenticated, None otherwise"""
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials, db)
    except (AuthenticationException, AuthorizationException):
        return None


def get_job_manager():
    """Get the background job manager instance"""
    return job_manager 