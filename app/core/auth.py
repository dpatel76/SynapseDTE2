"""
Authentication utilities for JWT token handling and password management
"""

from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models.user import User
from app.core.exceptions import AuthenticationException, AuthorizationException
from app.core.database import get_db

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
ALGORITHM = settings.algorithm
SECRET_KEY = settings.secret_key
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

# Security scheme for FastAPI
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> dict:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise AuthenticationException("Invalid token: missing user ID")
        
        # Convert user_id to integer
        try:
            user_id = int(user_id_str)
            payload["sub"] = user_id  # Update payload with integer user_id
        except (ValueError, TypeError):
            raise AuthenticationException("Invalid token: user ID must be a number")
            
        return payload
    except JWTError as e:
        raise AuthenticationException(f"Invalid token: {str(e)}")


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Get user by email address"""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    """Get user by ID"""
    result = await db.execute(select(User).where(User.user_id == user_id))
    return result.scalar_one_or_none()


async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    """Authenticate user with email and password"""
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        return None
    return user


def validate_password_strength(password: str) -> bool:
    """Validate password meets security requirements"""
    if len(password) < settings.password_min_length:
        return False
    
    has_upper = any(c.isupper() for c in password) if settings.password_require_uppercase else True
    has_lower = any(c.islower() for c in password) if settings.password_require_lowercase else True
    has_digit = any(c.isdigit() for c in password) if settings.password_require_numbers else True
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password) if settings.password_require_special else True
    
    return all([has_upper, has_lower, has_digit, has_special])


def check_role_permission(user_role: str, required_roles: list) -> bool:
    """Check if user role has required permissions"""
    # Admin role has access to everything
    if user_role == UserRoles.ADMIN:
        return True
    return user_role in required_roles


def check_lob_access(user_lob_id: Optional[int], required_lob_id: int) -> bool:
    """Check if user has access to specific LOB"""
    # CDO and executives may have broader access
    if user_lob_id is None:  # System admin or cross-LOB role
        return True
    return user_lob_id == required_lob_id


def decode_access_token(token: str) -> Optional[dict]:
    """Decode JWT access token and return payload"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


class RoleChecker:
    """Role-based access control checker"""
    
    def __init__(self, allowed_roles: list):
        self.allowed_roles = allowed_roles
    
    def __call__(self, user: User) -> bool:
        if not user.is_active:
            raise AuthorizationException("User account is inactive")
        
        # Admin role has access to everything
        if user.role == UserRoles.ADMIN:
            return True
        
        if user.role not in self.allowed_roles:
            raise AuthorizationException(
                f"Access denied. Required roles: {self.allowed_roles}, user role: {user.role}"
            )
        
        return True


class LOBChecker:
    """LOB-based access control checker"""
    
    def __init__(self, required_lob_id: int):
        self.required_lob_id = required_lob_id
    
    def __call__(self, user: User) -> bool:
        if not check_lob_access(user.lob_id, self.required_lob_id):
            raise AuthorizationException(
                f"Access denied. User does not have access to LOB {self.required_lob_id}"
            )
        
        return True


# Role definitions for easy reference
class UserRoles:
    TESTER = "Tester"
    TEST_EXECUTIVE = "Test Executive"
    REPORT_OWNER = "Report Owner"
    REPORT_OWNER_EXECUTIVE = "Report Owner Executive"
    DATA_OWNER = "Data Owner"
    DATA_EXECUTIVE = "Data Executive"
    ADMIN = "Admin"
    
    @classmethod
    def all_roles(cls) -> list:
        return [cls.TESTER, cls.TEST_EXECUTIVE, cls.REPORT_OWNER, 
                cls.REPORT_OWNER_EXECUTIVE, cls.DATA_OWNER, cls.DATA_EXECUTIVE, cls.ADMIN]
    
    @classmethod
    def management_roles(cls) -> list:
        return [cls.TEST_EXECUTIVE, cls.REPORT_OWNER_EXECUTIVE, cls.DATA_EXECUTIVE, cls.ADMIN]
    
    @classmethod
    def testing_roles(cls) -> list:
        return [cls.TESTER, cls.TEST_EXECUTIVE, cls.ADMIN]
    
    @classmethod
    def approval_roles(cls) -> list:
        return [cls.REPORT_OWNER, cls.REPORT_OWNER_EXECUTIVE, cls.ADMIN]
    
    @classmethod
    def admin_roles(cls) -> list:
        return [cls.ADMIN]


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token"""
    try:
        # Verify the token
        payload = verify_token(credentials.credentials)
        user_id = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user from database
        user = await get_user_by_id(db, user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
        
    except AuthenticationException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user (convenience function)"""
    return current_user 