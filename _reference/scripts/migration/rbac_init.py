#!/usr/bin/env python3
"""
RBAC Initialization Script

This script will:
1. Create all RBAC tables if they don't exist
2. Populate default permissions based on RBAC configuration
3. Create system roles 
4. Assign default permissions to roles
5. Map existing users to RBAC roles
6. Test all permission functions
"""

import os
import sys
import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

# Add the app directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine, AsyncSessionLocal
from app.models import *
from app.core.rbac_config import (
    RESOURCES, DEFAULT_ROLE_PERMISSIONS, get_all_permissions,
    get_resource_actions, is_valid_permission
)
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

class RBACInitializer:
    """RBAC system initializer"""
    
    def __init__(self):
        self.engine = engine
        
    async def get_session(self) -> AsyncSession:
        """Get async database session"""
        return AsyncSessionLocal()
    
    async def check_rbac_tables_exist(self, session: AsyncSession) -> bool:
        """Check if RBAC tables exist"""
        try:
            # Check for key RBAC tables
            result = await session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('permissions', 'roles', 'role_permissions', 'user_roles')
            """))
            existing_tables = [row[0] for row in result.fetchall()]
            
            required_tables = ['permissions', 'roles', 'role_permissions', 'user_roles']
            missing_tables = [table for table in required_tables if table not in existing_tables]
            
            if missing_tables:
                logger.warning(f"Missing RBAC tables: {missing_tables}")
                return False
                
            logger.info("All RBAC tables exist")
            return True
            
        except Exception as e:
            logger.error(f"Error checking RBAC tables: {e}")
            return False
    
    async def create_rbac_tables(self):
        """Create RBAC tables using SQLAlchemy metadata"""
        try:
            logger.info("Creating RBAC tables...")
            
            # Import all models to ensure metadata is populated
            from app.models.rbac import (
                Permission, Role, RolePermission, UserRole, 
                UserPermission, ResourcePermission, RoleHierarchy, 
                PermissionAuditLog
            )
            from app.models.rbac_resource import Resource
            
            # Create only RBAC tables
            rbac_tables = [
                Permission.__table__,
                Role.__table__,
                RolePermission.__table__,
                UserRole.__table__,
                UserPermission.__table__,
                ResourcePermission.__table__,
                RoleHierarchy.__table__,
                PermissionAuditLog.__table__,
                Resource.__table__
            ]
            
            from app.models.base import CustomPKModel
            
            async with self.engine.begin() as conn:
                await conn.run_sync(CustomPKModel.metadata.create_all, tables=rbac_tables)
            
            logger.info("RBAC tables created successfully")
            
        except Exception as e:
            logger.error(f"Error creating RBAC tables: {e}")
            raise
    
    async def populate_permissions(self, session: AsyncSession):
        """Populate permissions table with all defined permissions"""
        try:
            logger.info("Populating permissions...")
            
            permission_count = 0
            for resource, config in RESOURCES.items():
                for action in config["actions"]:
                    # Check if permission already exists
                    result = await session.execute(
                        text("SELECT permission_id FROM permissions WHERE resource = :resource AND action = :action"),
                        {"resource": resource, "action": action.value}
                    )
                    existing = result.fetchone()
                    
                    if not existing:
                        permission = Permission(
                            resource=resource,
                            action=action.value,
                            description=f"{action.value} access to {config['display_name']}"
                        )
                        session.add(permission)
                        permission_count += 1
                        logger.info(f"Created permission: {resource}:{action.value}")
            
            await session.commit()
            logger.info(f"Created {permission_count} new permissions")
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Error populating permissions: {e}")
            raise
    
    async def populate_roles(self, session: AsyncSession):
        """Populate roles table with system roles"""
        try:
            logger.info("Populating roles...")
            
            system_roles = [
                ("Admin", "System Administrator - Full Access", True),
                ("Test Executive", "Test Manager - Manage testing cycles and assignments", True),
                ("Tester", "Tester - Execute testing workflows", True),
                ("Report Owner", "Report Owner - Review and approve reports", True),
                ("Report Owner Executive", "Report Owner Executive - Executive oversight", True),
                ("Data Owner", "Data Provider - Provide data for testing", True),
                ("Data Executive", "Chief Data Officer - Manage LOBs and data providers", True),
            ]
            
            role_count = 0
            for role_name, description, is_system in system_roles:
                # Check if role already exists
                result = await session.execute(
                    text("SELECT role_id FROM roles WHERE role_name = :role_name"),
                    {"role_name": role_name}
                )
                existing = result.fetchone()
                
                if not existing:
                    role = Role(
                        role_name=role_name,
                        description=description,
                        is_system=is_system,
                        is_active=True
                    )
                    session.add(role)
                    role_count += 1
                    logger.info(f"Created role: {role_name}")
            
            await session.commit()
            logger.info(f"Created {role_count} new roles")
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Error populating roles: {e}")
            raise
    
    async def assign_role_permissions(self, session: AsyncSession):
        """Assign permissions to roles based on DEFAULT_ROLE_PERMISSIONS"""
        try:
            logger.info("Assigning permissions to roles...")
            
            assignment_count = 0
            for role_name, permissions in DEFAULT_ROLE_PERMISSIONS.items():
                # Get role
                result = await session.execute(
                    text("SELECT role_id FROM roles WHERE role_name = :role_name"),
                    {"role_name": role_name}
                )
                role_row = result.fetchone()
                if not role_row:
                    logger.warning(f"Role not found: {role_name}")
                    continue
                
                role_id = role_row[0]
                
                for perm_string in permissions:
                    if perm_string == "*:*":
                        # Admin gets all permissions
                        perms_result = await session.execute(text("SELECT permission_id FROM permissions"))
                        all_perms = perms_result.fetchall()
                        for perm_row in all_perms:
                            perm_id = perm_row[0]
                            if await self._assign_permission_to_role(session, role_id, perm_id):
                                assignment_count += 1
                    else:
                        # Parse resource:action
                        if ":" not in perm_string:
                            logger.warning(f"Invalid permission format: {perm_string}")
                            continue
                            
                        resource, action = perm_string.split(":", 1)
                        perm_result = await session.execute(
                            text("SELECT permission_id FROM permissions WHERE resource = :resource AND action = :action"),
                            {"resource": resource, "action": action}
                        )
                        perm_row = perm_result.fetchone()
                        
                        if perm_row:
                            perm_id = perm_row[0]
                            if await self._assign_permission_to_role(session, role_id, perm_id):
                                assignment_count += 1
                        else:
                            logger.warning(f"Permission not found: {perm_string}")
            
            await session.commit()
            logger.info(f"Created {assignment_count} role-permission assignments")
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Error assigning role permissions: {e}")
            raise
    
    async def _assign_permission_to_role(self, session: AsyncSession, role_id: int, permission_id: int) -> bool:
        """Assign a permission to a role if not already assigned"""
        try:
            # Check if assignment already exists
            result = await session.execute(
                text("SELECT 1 FROM role_permissions WHERE role_id = :role_id AND permission_id = :permission_id"),
                {"role_id": role_id, "permission_id": permission_id}
            )
            existing = result.fetchone()
            
            if not existing:
                role_permission = RolePermission(
                    role_id=role_id,
                    permission_id=permission_id,
                    granted_at=datetime.utcnow()
                )
                session.add(role_permission)
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error assigning permission {permission_id} to role {role_id}: {e}")
            return False
    
    async def map_users_to_rbac_roles(self, session: AsyncSession):
        """Map existing users to RBAC roles"""
        try:
            logger.info("Mapping users to RBAC roles...")
            
            # Get all users
            users_result = await session.execute(text("SELECT user_id, email, role FROM users"))
            users = users_result.fetchall()
            mapping_count = 0
            
            for user_row in users:
                user_id, email, user_role = user_row
                
                # Find the corresponding RBAC role
                role_result = await session.execute(
                    text("SELECT role_id FROM roles WHERE role_name = :role_name"),
                    {"role_name": user_role}
                )
                role_row = role_result.fetchone()
                
                if not role_row:
                    logger.warning(f"RBAC role not found for user role: {user_role}")
                    continue
                
                role_id = role_row[0]
                
                # Check if user is already mapped to this role
                existing_result = await session.execute(
                    text("SELECT 1 FROM user_roles WHERE user_id = :user_id AND role_id = :role_id"),
                    {"user_id": user_id, "role_id": role_id}
                )
                existing = existing_result.fetchone()
                
                if not existing:
                    user_role_mapping = UserRole(
                        user_id=user_id,
                        role_id=role_id,
                        assigned_at=datetime.utcnow()
                    )
                    session.add(user_role_mapping)
                    mapping_count += 1
                    logger.info(f"Mapped user {email} to role {user_role}")
            
            await session.commit()
            logger.info(f"Created {mapping_count} user-role mappings")
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Error mapping users to RBAC roles: {e}")
            raise
    
    async def validate_rbac_system(self, session: AsyncSession):
        """Validate that the RBAC system is properly configured"""
        try:
            logger.info("Validating RBAC system...")
            
            # Count statistics
            perm_result = await session.execute(text("SELECT COUNT(*) FROM permissions"))
            permission_count = perm_result.scalar()
            
            role_result = await session.execute(text("SELECT COUNT(*) FROM roles"))
            role_count = role_result.scalar()
            
            role_perm_result = await session.execute(text("SELECT COUNT(*) FROM role_permissions"))
            role_permission_count = role_perm_result.scalar()
            
            user_role_result = await session.execute(text("SELECT COUNT(*) FROM user_roles"))
            user_role_count = user_role_result.scalar()
            
            logger.info(f"RBAC Statistics:")
            logger.info(f"  Permissions: {permission_count}")
            logger.info(f"  Roles: {role_count}")
            logger.info(f"  Role-Permission mappings: {role_permission_count}")
            logger.info(f"  User-Role mappings: {user_role_count}")
            
            # Validate each role has permissions
            roles_result = await session.execute(text("SELECT role_id, role_name FROM roles"))
            roles = roles_result.fetchall()
            
            for role_id, role_name in roles:
                perm_count_result = await session.execute(
                    text("SELECT COUNT(*) FROM role_permissions WHERE role_id = :role_id"),
                    {"role_id": role_id}
                )
                perm_count = perm_count_result.scalar()
                logger.info(f"  {role_name}: {perm_count} permissions")
                
                if perm_count == 0 and role_name != "Admin":
                    logger.warning(f"Role {role_name} has no permissions assigned!")
            
            logger.info("RBAC validation completed")
            
        except Exception as e:
            logger.error(f"Error validating RBAC system: {e}")
            raise
    
    async def test_permission_checks(self, session: AsyncSession):
        """Test permission checking functions"""
        try:
            logger.info("Testing permission checks...")
            
            # Test admin user
            admin_result = await session.execute(
                text("SELECT user_id, email FROM users WHERE role = 'Admin' LIMIT 1")
            )
            admin_user = admin_result.fetchone()
            
            if admin_user:
                user_id, email = admin_user
                logger.info(f"Testing permissions for admin user: {email}")
                
                # Test some permissions
                test_permissions = [
                    ("system", "admin"),
                    ("cycles", "create"),
                    ("reports", "read"),
                ]
                
                for resource, action in test_permissions:
                    has_permission = await self._check_user_permission(session, user_id, resource, action)
                    logger.info(f"  Admin {resource}:{action}: {has_permission}")
            
            # Test non-admin user
            tester_result = await session.execute(
                text("SELECT user_id, email FROM users WHERE role = 'Tester' LIMIT 1")
            )
            tester_user = tester_result.fetchone()
            
            if tester_user:
                user_id, email = tester_user
                logger.info(f"Testing permissions for tester: {email}")
                
                # Test some specific permissions
                test_permissions = [
                    ("planning", "execute"),
                    ("testing", "execute"),
                    ("system", "admin"),  # Should be False
                ]
                
                for resource, action in test_permissions:
                    has_permission = await self._check_user_permission(session, user_id, resource, action)
                    logger.info(f"  Tester {resource}:{action}: {has_permission}")
            
            logger.info("Permission tests completed")
            
        except Exception as e:
            logger.error(f"Error testing permissions: {e}")
            raise
    
    async def _check_user_permission(self, session: AsyncSession, user_id: int, resource: str, action: str) -> bool:
        """Check if user has a specific permission"""
        try:
            # Check if user has permission through roles
            result = await session.execute(text("""
                SELECT 1 FROM user_roles ur
                JOIN role_permissions rp ON ur.role_id = rp.role_id
                JOIN permissions p ON rp.permission_id = p.permission_id
                WHERE ur.user_id = :user_id 
                AND p.resource = :resource 
                AND p.action = :action
                LIMIT 1
            """), {"user_id": user_id, "resource": resource, "action": action})
            
            return result.fetchone() is not None
            
        except Exception as e:
            logger.error(f"Error checking permission: {e}")
            return False
    
    async def run_initialization(self):
        """Run the complete RBAC initialization process"""
        session = None
        try:
            logger.info("Starting RBAC system initialization...")
            session = await self.get_session()
            
            # Check if tables exist, create if needed
            if not await self.check_rbac_tables_exist(session):
                await session.close()
                await self.create_rbac_tables()
                session = await self.get_session()
            
            # Populate base data
            await self.populate_permissions(session)
            await session.close()
            session = await self.get_session()
            
            await self.populate_roles(session)
            await session.close()
            session = await self.get_session()
            
            await self.assign_role_permissions(session)
            await session.close()
            session = await self.get_session()
            
            await self.map_users_to_rbac_roles(session)
            await session.close()
            session = await self.get_session()
            
            # Validate and test
            await self.validate_rbac_system(session)
            await self.test_permission_checks(session)
            
            logger.info("RBAC system initialization completed successfully!")
            logger.info("=" * 60)
            logger.info("NEXT STEPS:")
            logger.info("1. Restart the backend service: ./restart_backend.sh")
            logger.info("2. Test permissions in the application")
            logger.info("3. Review user permissions in the admin panel")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"RBAC initialization failed: {e}")
            raise
        finally:
            if session:
                await session.close()


async def main():
    """Main entry point"""
    print("=" * 60)
    print("RBAC SYSTEM INITIALIZATION")
    print("=" * 60)
    
    try:
        initializer = RBACInitializer()
        await initializer.run_initialization()
        
        print("\n✅ RBAC system initialization completed successfully!")
        print("\nTo test RBAC:")
        print("1. Restart backend: ./restart_backend.sh")
        print("2. Login to application and test permissions")
        print("3. Check logs for permission checks")
        
    except Exception as e:
        print(f"\n❌ RBAC initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 