#!/usr/bin/env python3

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import AsyncSessionLocal
from app.services.permission_service import PermissionService
from sqlalchemy import text

async def check_admin_rbac_permission():
    session = AsyncSessionLocal()
    try:
        # Get admin user
        result = await session.execute(text("SELECT user_id FROM users WHERE role = 'Admin' LIMIT 1"))
        admin_user = result.fetchone()
        if not admin_user:
            print('❌ No admin user found')
            return
        
        admin_user_id = admin_user[0]
        print(f'👤 Admin user ID: {admin_user_id}')
        
        # Check permissions:manage permission
        permission_service = PermissionService(session)
        has_permission = await permission_service.check_permission(
            user_id=admin_user_id,
            resource='permissions',
            action='manage'
        )
        print(f'🔐 Admin has permissions:manage: {"✅" if has_permission else "❌"} {has_permission}')
        
        # Check system:admin permission
        has_system_admin = await permission_service.check_permission(
            user_id=admin_user_id,
            resource='system',
            action='admin'
        )
        print(f'🔑 Admin has system:admin: {"✅" if has_system_admin else "❌"} {has_system_admin}')
        
        # Check if admin should have all permissions (because of *:* assignment)
        all_perms_result = await session.execute(text("""
            SELECT COUNT(*) FROM rbac_permissions p
            WHERE EXISTS (
                SELECT 1 FROM rbac_user_roles ur
                JOIN rbac_role_permissions rp ON ur.role_id = rp.role_id
                WHERE ur.user_id = :user_id AND rp.permission_id = p.permission_id
            )
        """), {"user_id": admin_user_id})
        admin_perm_count = all_perms_result.scalar()
        
        total_perms_result = await session.execute(text("SELECT COUNT(*) FROM rbac_permissions"))
        total_perm_count = total_perms_result.scalar()
        
        print(f'📊 Admin has {admin_perm_count}/{total_perm_count} permissions')
        
        if admin_perm_count == total_perm_count:
            print('✅ Admin has all permissions (as expected)')
        else:
            print('⚠️  Admin does not have all permissions')
        
    finally:
        await session.close()

if __name__ == "__main__":
    asyncio.run(check_admin_rbac_permission()) 