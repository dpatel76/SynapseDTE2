#!/usr/bin/env python3
"""
Add dashboard permissions for all roles
"""

import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Import models
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.models.base import Base
from app.models.user import User
from app.models.rbac import Role, Permission, RolePermission

load_dotenv()

# Convert sync URL to async URL
sync_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/synapse_dt')
DATABASE_URL = sync_url.replace('postgresql://', 'postgresql+asyncpg://')

engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def add_dashboard_permissions():
    """Add dashboard permissions for all roles"""
    print("Adding Dashboard Permissions")
    print("=" * 50)
    
    async with AsyncSessionLocal() as session:
        # Create permissions that may be missing
        permissions_to_add = [
            ("sample_selection", "read", "Read sample selection data"),
            ("scoping", "read", "Read scoping data"),
            ("data_owner", "read", "Read data owner information"),
        ]
        
        for resource, action, description in permissions_to_add:
            result = await session.execute(
                select(Permission).where(
                    Permission.resource == resource,
                    Permission.action == action
                )
            )
            existing = result.scalar_one_or_none()
            
            if not existing:
                permission = Permission(
                    resource=resource,
                    action=action,
                    description=description
                )
                session.add(permission)
                print(f"  Created: {resource}:{action}")
            else:
                print(f"  Already exists: {resource}:{action}")
        
        await session.commit()
        
        # Grant permissions to roles
        role_permissions = [
            # Report Owner needs these permissions for their dashboard
            ("Report Owner", [
                ("metrics", "read"),
                ("sample_selection", "read"),
                ("scoping", "read"),
            ]),
            # Data Executive (CDO) needs these permissions
            ("Data Executive", [
                ("metrics", "read"),
                ("data_owner", "read"),
                ("sample_selection", "read"),
            ]),
            # Data Owner needs these permissions
            ("Data Owner", [
                ("data_owner", "read"),
                ("request_info", "read"),
            ]),
        ]
        
        print("\nGranting permissions to roles...")
        
        for role_name, permissions in role_permissions:
            # Get role
            result = await session.execute(
                select(Role).where(Role.role_name == role_name)
            )
            role = result.scalar_one_or_none()
            
            if not role:
                print(f"  Warning: {role_name} role not found")
                continue
            
            for resource, action in permissions:
                # Get permission
                result = await session.execute(
                    select(Permission).where(
                        Permission.resource == resource,
                        Permission.action == action
                    )
                )
                permission = result.scalar_one_or_none()
                
                if not permission:
                    print(f"  Warning: Permission {resource}:{action} not found")
                    continue
                
                # Check if already granted
                result = await session.execute(
                    select(RolePermission).where(
                        RolePermission.role_id == role.role_id,
                        RolePermission.permission_id == permission.permission_id
                    )
                )
                existing = result.scalar_one_or_none()
                
                if not existing:
                    role_permission = RolePermission(
                        role_id=role.role_id,
                        permission_id=permission.permission_id
                    )
                    session.add(role_permission)
                    print(f"  Granted {resource}:{action} to {role_name}")
                else:
                    print(f"  Already granted: {resource}:{action} to {role_name}")
        
        await session.commit()
        
    print("\nDashboard permissions setup complete!")
    
    # Verify permissions
    print("\n\nVerifying Permissions")
    print("=" * 50)
    
    async with AsyncSessionLocal() as session:
        for role_name in ["Report Owner", "Data Executive", "Data Owner"]:
            result = await session.execute(
                select(Role).where(Role.role_name == role_name)
            )
            role = result.scalar_one_or_none()
            
            if role:
                # Get all permissions for this role
                result = await session.execute(
                    select(Permission).join(RolePermission).where(
                        RolePermission.role_id == role.role_id,
                        Permission.resource.in_(["metrics", "sample_selection", "scoping", "data_owner", "request_info"])
                    )
                )
                permissions = result.scalars().all()
                
                print(f"\n{role_name} dashboard permissions:")
                for perm in permissions:
                    print(f"  - {perm.resource}:{perm.action}")

if __name__ == "__main__":
    asyncio.run(add_dashboard_permissions())