"""SQLAlchemy implementation of UserRepository"""
from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.models import User, Role, Permission, UserRole
from app.application.interfaces.repositories import UserRepository


class SQLAlchemyUserRepository(UserRepository):
    """SQLAlchemy implementation of the user repository"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get a user by ID"""
        result = await self.session.execute(
            select(User)
            .options(
                selectinload(User.roles).selectinload(UserRole.role)
            )
            .where(User.user_id == user_id)
        )
        db_user = result.scalar_one_or_none()
        
        if not db_user:
            return None
        
        return self._to_dict(db_user)
    
    async def find_by_role(self, role: str) -> List[Dict[str, Any]]:
        """Find users by role"""
        result = await self.session.execute(
            select(User)
            .join(User.roles)
            .join(UserRole.role)
            .options(
                selectinload(User.roles).selectinload(UserRole.role)
            )
            .where(Role.role_name == role)
        )
        db_users = result.scalars().unique().all()
        
        return [self._to_dict(user) for user in db_users]
    
    async def find_testers(self) -> List[Dict[str, Any]]:
        """Find all users with tester role"""
        return await self.find_by_role("Tester")
    
    async def get_user_permissions(self, user_id: int) -> List[str]:
        """Get permissions for a user"""
        # Get user with roles and permissions
        result = await self.session.execute(
            select(User)
            .options(
                selectinload(User.roles)
                .selectinload(UserRole.role)
                .selectinload(Role.permissions)
                .selectinload(Permission.permission)
            )
            .where(User.user_id == user_id)
        )
        db_user = result.scalar_one_or_none()
        
        if not db_user:
            return []
        
        # Collect all permissions from all roles
        permissions = set()
        for user_role in db_user.roles:
            if user_role.role:
                for role_permission in user_role.role.permissions:
                    if role_permission.permission:
                        permissions.add(role_permission.permission.permission_key)
        
        return list(permissions)
    
    def _to_dict(self, db_user: User) -> Dict[str, Any]:
        """Convert database model to dictionary"""
        roles = []
        lobs = []
        
        for user_role in db_user.roles:
            if user_role.role:
                roles.append(user_role.role.role_name)
                # Extract LOB from user_role metadata if available
                if hasattr(user_role, 'lob') and user_role.lob:
                    lobs.append(user_role.lob)
        
        return {
            "user_id": db_user.user_id,
            "username": db_user.username,
            "email": db_user.email,
            "full_name": db_user.full_name,
            "is_active": db_user.is_active,
            "is_superuser": db_user.is_superuser,
            "created_at": db_user.created_at,
            "updated_at": db_user.updated_at,
            "roles": roles,
            "lob": lobs[0] if lobs else None,  # Primary LOB
            "all_lobs": lobs  # All LOBs if user has multiple
        }