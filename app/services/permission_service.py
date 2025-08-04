"""
Permission Service - Core RBAC functionality
"""

from typing import List, Optional, Set, Dict, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from cachetools import TTLCache
import asyncio

from app.models.user import User
from app.models.rbac import (
    Permission, Role, RolePermission, UserRole, 
    UserPermission, ResourcePermission, RoleHierarchy,
    PermissionAuditLog
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class PermissionService:
    """Service for managing and checking permissions"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        # Cache with 5 minute TTL
        self._permission_cache = TTLCache(maxsize=1000, ttl=300)
        self._role_cache = TTLCache(maxsize=100, ttl=300)
    
    async def check_permission(
        self, 
        user_id: int, 
        resource: str, 
        action: str,
        resource_id: Optional[int] = None
    ) -> bool:
        """
        Check if user has permission for resource:action
        
        Priority order:
        1. User is admin (has all permissions)
        2. Direct user permission (can be grant or deny)
        3. Resource-level permission (if resource_id provided)
        4. Role permissions (including inherited)
        """
        # Cache key
        cache_key = f"{user_id}:{resource}:{action}:{resource_id}"
        
        # Check cache
        if cache_key in self._permission_cache:
            return self._permission_cache[cache_key]
        
        try:
            # Check if user is admin (bypass all checks)
            user_result = await self.db.execute(select(User).where(User.user_id == user_id))
            user = user_result.scalar_one_or_none()
            if user and user.is_admin:
                self._permission_cache[cache_key] = True
                return True
            
            # Get permission ID
            permission = await self._get_permission(resource, action)
            if not permission:
                logger.warning(f"Permission not found: {resource}:{action}")
                self._permission_cache[cache_key] = False
                return False
            
            logger.debug(f"Found permission: {permission.permission_id} for {resource}:{action}")
            
            # Check direct user permission (highest priority after admin)
            user_perm = await self._check_user_permission(user_id, permission.permission_id)
            if user_perm is not None:
                self._permission_cache[cache_key] = user_perm
                return user_perm
            
            # Check resource-level permission if resource_id provided
            if resource_id:
                resource_perm = await self._check_resource_permission(
                    user_id, resource, resource_id, permission.permission_id
                )
                if resource_perm is not None:
                    self._permission_cache[cache_key] = resource_perm
                    return resource_perm
            
            # Check role permissions (including inherited)
            logger.debug(f"Checking role permissions for user {user_id}")
            role_perm = await self._check_role_permission(user_id, permission.permission_id)
            logger.debug(f"Role permission result: {role_perm}")
            self._permission_cache[cache_key] = role_perm
            return role_perm
            
        except Exception as e:
            logger.error(f"Error checking permission: {e}")
            return False
    
    async def get_user_permissions(self, user_id: int) -> Set[str]:
        """Get all permissions for a user"""
        permissions = set()
        
        # Get user
        user = await self.db.get(User, user_id)
        if not user:
            return permissions
        
        # Admin has all permissions
        if user.is_admin:
            all_perms = await self.db.execute(select(Permission))
            for perm in all_perms.scalars():
                permissions.add(perm.permission_string)
            return permissions
        
        # Get direct user permissions
        user_perms_query = select(Permission).join(UserPermission).where(
            and_(
                UserPermission.user_id == user_id,
                UserPermission.granted == True,
                or_(
                    UserPermission.expires_at.is_(None),
                    UserPermission.expires_at > datetime.utcnow()
                )
            )
        )
        user_perms = await self.db.execute(user_perms_query)
        for perm in user_perms.scalars():
            permissions.add(perm.permission_string)
        
        # Get role permissions (including inherited)
        role_perms = await self._get_all_role_permissions(user_id)
        permissions.update(role_perms)
        
        return permissions
    
    async def grant_permission_to_role(
        self, 
        role_id: int, 
        permission_id: int, 
        granted_by: int
    ) -> bool:
        """Grant permission to role"""
        try:
            # Check if already exists
            existing = await self.db.execute(
                select(RolePermission).where(
                    and_(
                        RolePermission.role_id == role_id,
                        RolePermission.permission_id == permission_id
                    )
                )
            )
            if existing.scalar_one_or_none():
                return True
            
            # Create new role permission
            role_perm = RolePermission(
                role_id=role_id,
                permission_id=permission_id,
                granted_by=granted_by
            )
            self.db.add(role_perm)
            
            # Add audit log
            audit = PermissionAuditLog(
                action_type='grant',
                target_type='role',
                target_id=role_id,
                permission_id=permission_id,
                performed_by=granted_by
            )
            self.db.add(audit)
            
            await self.db.commit()
            
            # Clear cache
            self._clear_cache()
            
            return True
            
        except Exception as e:
            logger.error(f"Error granting permission to role: {e}")
            await self.db.rollback()
            return False
    
    async def revoke_permission_from_role(
        self, 
        role_id: int, 
        permission_id: int, 
        revoked_by: int
    ) -> bool:
        """Revoke permission from role"""
        try:
            # Find and delete role permission
            result = await self.db.execute(
                select(RolePermission).where(
                    and_(
                        RolePermission.role_id == role_id,
                        RolePermission.permission_id == permission_id
                    )
                )
            )
            role_perm = result.scalar_one_or_none()
            
            if role_perm:
                await self.db.delete(role_perm)
                
                # Add audit log
                audit = PermissionAuditLog(
                    action_type='revoke',
                    target_type='role',
                    target_id=role_id,
                    permission_id=permission_id,
                    performed_by=revoked_by
                )
                self.db.add(audit)
                
                await self.db.commit()
                
                # Clear cache
                self._clear_cache()
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error revoking permission from role: {e}")
            await self.db.rollback()
            return False
    
    async def grant_permission_to_user(
        self, 
        user_id: int, 
        permission_id: int, 
        granted_by: int,
        expires_at: Optional[datetime] = None
    ) -> bool:
        """Grant permission directly to user"""
        try:
            # Check if already exists
            existing = await self.db.execute(
                select(UserPermission).where(
                    and_(
                        UserPermission.user_id == user_id,
                        UserPermission.permission_id == permission_id
                    )
                )
            )
            user_perm = existing.scalar_one_or_none()
            
            if user_perm:
                # Update existing
                user_perm.granted = True
                user_perm.granted_by = granted_by
                user_perm.granted_at = datetime.utcnow()
                user_perm.expires_at = expires_at
            else:
                # Create new
                user_perm = UserPermission(
                    user_id=user_id,
                    permission_id=permission_id,
                    granted=True,
                    granted_by=granted_by,
                    expires_at=expires_at
                )
                self.db.add(user_perm)
            
            # Add audit log
            audit = PermissionAuditLog(
                action_type='grant',
                target_type='user',
                target_id=user_id,
                permission_id=permission_id,
                performed_by=granted_by
            )
            self.db.add(audit)
            
            await self.db.commit()
            
            # Clear cache for this user
            self._clear_user_cache(user_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error granting permission to user: {e}")
            await self.db.rollback()
            return False
    
    async def assign_role_to_user(
        self,
        user_id: int,
        role_id: int,
        assigned_by: int,
        expires_at: Optional[datetime] = None
    ) -> bool:
        """Assign role to user"""
        try:
            # Check if already exists
            existing = await self.db.execute(
                select(UserRole).where(
                    and_(
                        UserRole.user_id == user_id,
                        UserRole.role_id == role_id
                    )
                )
            )
            if existing.scalar_one_or_none():
                return True
            
            # Create new user role
            user_role = UserRole(
                user_id=user_id,
                role_id=role_id,
                assigned_by=assigned_by,
                expires_at=expires_at
            )
            self.db.add(user_role)
            
            # Add audit log
            audit = PermissionAuditLog(
                action_type='grant',
                target_type='user',
                target_id=user_id,
                role_id=role_id,
                performed_by=assigned_by
            )
            self.db.add(audit)
            
            await self.db.commit()
            
            # Clear cache for this user
            self._clear_user_cache(user_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error assigning role to user: {e}")
            await self.db.rollback()
            return False
    
    async def create_permission(
        self,
        resource: str,
        action: str,
        description: Optional[str] = None
    ) -> Optional[Permission]:
        """Create a new permission"""
        try:
            permission = Permission(
                resource=resource,
                action=action,
                description=description
            )
            self.db.add(permission)
            await self.db.commit()
            await self.db.refresh(permission)
            return permission
            
        except Exception as e:
            logger.error(f"Error creating permission: {e}")
            await self.db.rollback()
            return None
    
    async def create_role(
        self,
        role_name: str,
        description: Optional[str] = None,
        is_system: bool = False
    ) -> Optional[Role]:
        """Create a new role"""
        try:
            role = Role(
                role_name=role_name,
                description=description,
                is_system=is_system
            )
            self.db.add(role)
            await self.db.commit()
            await self.db.refresh(role)
            return role
            
        except Exception as e:
            logger.error(f"Error creating role: {e}")
            await self.db.rollback()
            return None
    
    # Private helper methods
    
    async def _get_permission(self, resource: str, action: str) -> Optional[Permission]:
        """Get permission by resource and action"""
        # First try exact match (backward compatibility)
        result = await self.db.execute(
            select(Permission).where(
                and_(
                    Permission.resource == resource,
                    Permission.action == action
                )
            )
        )
        permission = result.scalar_one_or_none()
        
        if permission:
            return permission
        
        # If not found, try with normalized resource name (future compatibility)
        # This allows "report" and "reports" to be treated the same
        normalized_resource = resource.rstrip('s') if resource.endswith('s') else resource
        result = await self.db.execute(
            select(Permission).where(
                and_(
                    Permission.resource == normalized_resource,
                    Permission.action == action
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def _check_user_permission(self, user_id: int, permission_id: int) -> Optional[bool]:
        """Check direct user permission"""
        result = await self.db.execute(
            select(UserPermission).where(
                and_(
                    UserPermission.user_id == user_id,
                    UserPermission.permission_id == permission_id,
                    or_(
                        UserPermission.expires_at.is_(None),
                        UserPermission.expires_at > datetime.utcnow()
                    )
                )
            )
        )
        user_perm = result.scalar_one_or_none()
        
        if user_perm:
            return user_perm.granted
        
        return None
    
    async def _check_resource_permission(
        self, 
        user_id: int, 
        resource_type: str, 
        resource_id: int, 
        permission_id: int
    ) -> Optional[bool]:
        """Check resource-level permission"""
        result = await self.db.execute(
            select(ResourcePermission).where(
                and_(
                    ResourcePermission.user_id == user_id,
                    ResourcePermission.resource_type == resource_type,
                    ResourcePermission.resource_id == resource_id,
                    ResourcePermission.permission_id == permission_id,
                    or_(
                        ResourcePermission.expires_at.is_(None),
                        ResourcePermission.expires_at > datetime.utcnow()
                    )
                )
            )
        )
        resource_perm = result.scalar_one_or_none()
        
        if resource_perm:
            return resource_perm.granted
        
        return None
    
    async def _check_role_permission(self, user_id: int, permission_id: int) -> bool:
        """Check role-based permission including inheritance"""
        # Get all user's roles
        user_roles = await self._get_user_roles(user_id)
        
        # Get all inherited roles
        all_roles = set(user_roles)
        for role_id in user_roles:
            inherited = await self._get_inherited_roles(role_id)
            all_roles.update(inherited)
        
        # Check if any role has the permission
        if all_roles:
            result = await self.db.execute(
                select(RolePermission).where(
                    and_(
                        RolePermission.role_id.in_(all_roles),
                        RolePermission.permission_id == permission_id
                    )
                )
            )
            return result.scalar_one_or_none() is not None
        
        return False
    
    async def _get_user_roles(self, user_id: int) -> List[int]:
        """Get all active roles for a user"""
        result = await self.db.execute(
            select(UserRole.role_id).where(
                and_(
                    UserRole.user_id == user_id,
                    or_(
                        UserRole.expires_at.is_(None),
                        UserRole.expires_at > datetime.utcnow()
                    )
                )
            )
        )
        return [r for r in result.scalars()]
    
    async def _get_inherited_roles(self, role_id: int) -> Set[int]:
        """Get all parent roles (recursive)"""
        inherited = set()
        
        # Get direct parents
        result = await self.db.execute(
            select(RoleHierarchy.parent_role_id).where(
                RoleHierarchy.child_role_id == role_id
            )
        )
        parents = list(result.scalars())
        
        # Recursively get all ancestors
        for parent in parents:
            inherited.add(parent)
            inherited.update(await self._get_inherited_roles(parent))
        
        return inherited
    
    async def _get_all_role_permissions(self, user_id: int) -> Set[str]:
        """Get all permissions from user's roles"""
        permissions = set()
        
        # Get all user's roles (including inherited)
        user_roles = await self._get_user_roles(user_id)
        all_roles = set(user_roles)
        for role_id in user_roles:
            inherited = await self._get_inherited_roles(role_id)
            all_roles.update(inherited)
        
        if all_roles:
            # Get all permissions for these roles
            result = await self.db.execute(
                select(Permission).join(RolePermission).where(
                    RolePermission.role_id.in_(all_roles)
                )
            )
            for perm in result.scalars():
                permissions.add(perm.permission_string)
        
        return permissions
    
    def _clear_cache(self):
        """Clear all caches"""
        self._permission_cache.clear()
        self._role_cache.clear()
    
    def _clear_user_cache(self, user_id: int):
        """Clear cache for specific user"""
        # Remove all entries for this user
        keys_to_remove = [k for k in self._permission_cache.keys() if k.startswith(f"{user_id}:")]
        for key in keys_to_remove:
            del self._permission_cache[key]


async def get_permission_service(db: AsyncSession) -> PermissionService:
    """Get permission service instance"""
    return PermissionService(db)