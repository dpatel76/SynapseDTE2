#!/usr/bin/env python3
"""
Check user permissions
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.models.rbac import Permission, RolePermission, Role
from app.models.user import User
from sqlalchemy import select
from sqlalchemy.orm import selectinload


async def check_permissions():
    """Check permissions for tester user"""
    async with AsyncSessionLocal() as db:
        try:
            # Get tester user
            user = await db.execute(
                select(User).where(User.email == "tester@example.com")
            )
            user = user.scalar_one_or_none()
            
            if not user:
                print("User not found")
                return
                
            print(f"User: {user.email}, Role: {user.role}")
            
            # Get role - handle case sensitivity
            role = await db.execute(
                select(Role).where(Role.role_name == user.role)
            )
            role = role.scalar_one_or_none()
            
            if not role:
                # Try case-insensitive
                all_roles = await db.execute(select(Role))
                for r in all_roles.scalars():
                    if r.role_name.lower() == user.role.lower():
                        role = r
                        break
                
                if not role:
                    print(f"Role '{user.role}' not found. Available roles:")
                    for r in all_roles.scalars():
                        print(f"  - role_id: {r.role_id}, role_name: {r.role_name}")
                    return
                
            print(f"Role ID: {role.role_id}, Name: {role.role_name}")
            
            # Get permissions for this role
            role_perms = await db.execute(
                select(RolePermission, Permission)
                .join(Permission, RolePermission.permission_id == Permission.permission_id)
                .where(RolePermission.role_id == role.role_id)
                .where(Permission.resource == "sample_selection")
            )
            
            print("\nSample Selection Permissions:")
            for rp, perm in role_perms:
                print(f"  - {perm.resource}:{perm.action} (permission_id: {perm.permission_id})")
            
            # Check all permissions for the role
            all_perms = await db.execute(
                select(Permission)
                .join(RolePermission, RolePermission.permission_id == Permission.permission_id)
                .where(RolePermission.role_id == role.role_id)
                .order_by(Permission.resource, Permission.action)
            )
            
            print("\nAll Permissions for Role:")
            current_resource = None
            for perm in all_perms.scalars():
                if perm.resource != current_resource:
                    current_resource = perm.resource
                    print(f"\n  {perm.resource}:")
                print(f"    - {perm.action}")
                
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(check_permissions())