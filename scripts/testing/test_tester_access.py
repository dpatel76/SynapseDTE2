#!/usr/bin/env python3
"""Test script to verify tester user access and permissions"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.rbac import Role, Permission, RolePermission
from app.services.permission_service import PermissionService

async def test_tester_permissions():
    """Test tester user permissions"""
    async with AsyncSessionLocal() as db:
        # Find a tester user
        result = await db.execute(
            select(User)
            .where(User.role == 'Tester')
            .limit(1)
        )
        tester = result.scalar_one_or_none()
        
        if not tester:
            print("No tester user found in database")
            return
            
        print(f"Testing permissions for tester: {tester.email}")
        print(f"User ID: {tester.user_id}")
        print(f"Role: {tester.role}")
        
        # Get tester role
        result = await db.execute(
            select(Role)
            .where(Role.role_name == 'tester')
        )
        role = result.scalar_one_or_none()
        
        if not role:
            print("Tester role not found in database")
            return
            
        print(f"\nRole ID: {role.role_id}")
        print(f"Role Name: {role.role_name}")
        
        # Get permissions for tester role
        result = await db.execute(
            select(Permission)
            .join(RolePermission)
            .where(RolePermission.role_id == role.role_id)
            .order_by(Permission.resource, Permission.action)
        )
        permissions = result.scalars().all()
        
        print(f"\nPermissions for tester role ({len(permissions)} total):")
        for perm in permissions:
            print(f"  - {perm.resource}:{perm.action} ({perm.permission_name})")
        
        # Test specific permissions using PermissionService
        perm_service = PermissionService(db)
        
        print("\nTesting specific permissions:")
        test_cases = [
            ("cycles", "read"),
            ("test_cycle", "read"),
            ("planning_phase", "execute"),
            ("scoping_phase", "execute"),
            ("testing_phase", "execute"),
            ("dashboard", "view_tester"),
        ]
        
        for resource, action in test_cases:
            has_perm = await perm_service.check_permission(
                tester.user_id, resource, action
            )
            print(f"  - {resource}:{action} = {has_perm}")

if __name__ == "__main__":
    asyncio.run(test_tester_permissions())