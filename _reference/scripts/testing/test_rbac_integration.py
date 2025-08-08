#!/usr/bin/env python3
"""
Test RBAC integration to ensure permissions are working correctly
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.user import User
from app.models.rbac import UserRole, Role
from app.services.permission_service import PermissionService
from app.core.auth import UserRoles


async def test_user_permissions(db: AsyncSession, email: str):
    """Test permissions for a specific user"""
    print(f"\n{'='*60}")
    print(f"Testing permissions for: {email}")
    print('='*60)
    
    # Get user
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        print(f"❌ User not found: {email}")
        return
    
    print(f"User: {user.full_name} ({user.email})")
    print(f"Legacy Role: {user.role}")
    print(f"Active: {user.is_active}")
    
    # Get RBAC roles
    result = await db.execute(
        select(UserRole, Role)
        .join(Role, UserRole.role_id == Role.role_id)
        .where(UserRole.user_id == user.user_id)
    )
    user_roles = result.all()
    
    if user_roles:
        print(f"\nRBAC Roles:")
        for ur, role in user_roles:
            print(f"  - {role.role_name}")
    else:
        print(f"\n⚠️  No RBAC roles assigned")
    
    # Test permissions
    permission_service = PermissionService(db)
    
    test_permissions = [
        ("cycles", "create", "Create test cycles"),
        ("cycles", "read", "View test cycles"),
        ("cycles", "update", "Update test cycles"),
        ("cycles", "delete", "Delete test cycles"),
        ("cycles", "assign", "Assign reports to cycles"),
        ("reports", "read", "View reports"),
        ("reports", "approve", "Approve reports"),
        ("planning", "execute", "Execute planning phase"),
        ("scoping", "approve", "Approve scoping"),
        ("users", "create", "Create users"),
        ("permissions", "manage", "Manage permissions"),
    ]
    
    print(f"\nPermission Check Results:")
    print(f"{'Permission':<30} {'Allowed':<10} {'Description'}")
    print("-" * 70)
    
    for resource, action, description in test_permissions:
        has_permission = await permission_service.check_permission(
            user.user_id, resource, action
        )
        status = "✅ Yes" if has_permission else "❌ No"
        print(f"{resource}:{action:<25} {status:<10} {description}")
    
    # Get all permissions
    all_perms = await permission_service.get_user_permissions(user.user_id)
    print(f"\nTotal permissions: {len(all_perms['all_permissions'])}")


async def test_role_permissions(db: AsyncSession):
    """Test permissions for each role"""
    print(f"\n{'='*60}")
    print("Role Permission Summary")
    print('='*60)
    
    result = await db.execute(
        select(Role).where(Role.is_active == True)
    )
    roles = result.scalars().all()
    
    permission_service = PermissionService(db)
    
    for role in roles:
        perms = await permission_service.get_role_permissions(role.role_id)
        print(f"\n{role.role_name}: {len(perms)} permissions")
        
        # Group by resource
        by_resource = {}
        for perm in perms:
            if perm.resource not in by_resource:
                by_resource[perm.resource] = []
            by_resource[perm.resource].append(perm.action)
        
        for resource, actions in sorted(by_resource.items()):
            print(f"  {resource}: {', '.join(sorted(actions))}")


async def main():
    """Main test function"""
    print("RBAC Integration Test")
    print("=" * 60)
    
    async for db in get_db():
        try:
            # Test different user types
            test_users = [
                "admin@synapsedt.com",
                "john.manager@synapsedt.com",
                "jane.tester@synapsedt.com",
                "bob.owner@synapsedt.com",
                "alice.executive@synapsedt.com",
                "charlie.provider@synapsedt.com",
                "diana.cdo@synapsedt.com"
            ]
            
            for email in test_users:
                await test_user_permissions(db, email)
            
            # Show role summary
            await test_role_permissions(db)
            
            print("\n✅ RBAC integration test completed!")
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            await db.close()
            break


if __name__ == "__main__":
    asyncio.run(main())