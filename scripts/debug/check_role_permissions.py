#!/usr/bin/env python3

import asyncio
import os
import sys
sys.path.append('.')

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, selectinload
from sqlalchemy import select
from app.models.rbac import Role, RolePermission, Permission

async def check_role_permissions():
    DATABASE_URL = 'postgresql+asyncpg://dineshpatel@localhost:5432/synapse_dt'
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Get all roles with their permissions
        result = await session.execute(
            select(Role)
            .options(selectinload(Role.role_permissions).selectinload(RolePermission.permission))
            .order_by(Role.role_name)
        )
        roles = result.scalars().all()
        
        print('Current Role Permissions Status:')
        print('=' * 50)
        
        total_roles = len(roles)
        roles_with_permissions = 0
        
        for role in roles:
            perm_count = len(role.role_permissions) if role.role_permissions else 0
            if perm_count > 0:
                roles_with_permissions += 1
                
            print(f'{role.role_name}: {perm_count} permissions')
            
            if perm_count > 0:
                print('  Sample permissions:')
                for rp in role.role_permissions[:3]:  # Show first 3
                    perm = rp.permission
                    print(f'    - {perm.resource}:{perm.action}')
                if len(role.role_permissions) > 3:
                    print(f'    ... and {len(role.role_permissions) - 3} more')
            print()
        
        print(f'Summary: {roles_with_permissions}/{total_roles} roles have permissions assigned')

if __name__ == "__main__":
    asyncio.run(check_role_permissions()) 