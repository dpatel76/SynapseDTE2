#!/usr/bin/env python3
"""
Add metrics:read permission for Report Owner role
This script adds the missing metrics resource and grants read permission to Report Owner
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.rbac import Permission, Role, RolePermission
from app.core.auth import UserRoles


async def add_metrics_resource_permissions(db: AsyncSession):
    """Add metrics resource and permissions"""
    print("Adding Metrics Resource Permissions")
    print("=" * 50)
    
    # Define metrics permissions to create
    metrics_permissions = [
        {
            "resource": "metrics",
            "action": "read",
            "description": "Read metrics and analytics data"
        },
        {
            "resource": "metrics",
            "action": "generate",
            "description": "Generate metrics reports"
        }
    ]
    
    created_permissions = []
    
    # Create permissions
    for perm_data in metrics_permissions:
        # Check if permission already exists
        result = await db.execute(
            select(Permission).where(
                Permission.resource == perm_data["resource"],
                Permission.action == perm_data["action"]
            )
        )
        existing_perm = result.scalar_one_or_none()
        
        if not existing_perm:
            permission = Permission(**perm_data)
            db.add(permission)
            created_permissions.append(permission)
            print(f"  Created: {perm_data['resource']}:{perm_data['action']}")
        else:
            created_permissions.append(existing_perm)
            print(f"  Exists: {perm_data['resource']}:{perm_data['action']}")
    
    await db.commit()
    
    # Now grant metrics:read to Report Owner role
    print("\nGranting metrics:read to Report Owner role...")
    
    # Get Report Owner role
    result = await db.execute(
        select(Role).where(Role.role_name == "Report Owner")
    )
    report_owner_role = result.scalar_one_or_none()
    
    if not report_owner_role:
        print("  ERROR: Report Owner role not found!")
        return
    
    # Get metrics:read permission
    result = await db.execute(
        select(Permission).where(
            Permission.resource == "metrics",
            Permission.action == "read"
        )
    )
    metrics_read_perm = result.scalar_one_or_none()
    
    if not metrics_read_perm:
        print("  ERROR: metrics:read permission not found!")
        return
    
    # Check if role already has this permission
    result = await db.execute(
        select(RolePermission).where(
            RolePermission.role_id == report_owner_role.role_id,
            RolePermission.permission_id == metrics_read_perm.permission_id
        )
    )
    existing_role_perm = result.scalar_one_or_none()
    
    if not existing_role_perm:
        role_permission = RolePermission(
            role_id=report_owner_role.role_id,
            permission_id=metrics_read_perm.permission_id
        )
        db.add(role_permission)
        await db.commit()
        print(f"  Granted metrics:read to Report Owner role")
    else:
        print(f"  Report Owner already has metrics:read permission")
    
    # Also grant metrics:read to other roles that need it
    roles_needing_metrics = [
        "Administrator",
        "Test Executive", 
        "Report Owner Executive",
        "Chief Data Officer"
    ]
    
    print("\nGranting metrics:read to other management roles...")
    
    for role_name in roles_needing_metrics:
        result = await db.execute(
            select(Role).where(Role.role_name == role_name)
        )
        role = result.scalar_one_or_none()
        
        if not role:
            print(f"  Warning: {role_name} role not found")
            continue
        
        # Check if already has permission
        result = await db.execute(
            select(RolePermission).where(
                RolePermission.role_id == role.role_id,
                RolePermission.permission_id == metrics_read_perm.permission_id
            )
        )
        existing = result.scalar_one_or_none()
        
        if not existing:
            role_permission = RolePermission(
                role_id=role.role_id,
                permission_id=metrics_read_perm.permission_id
            )
            db.add(role_permission)
            print(f"  Granted metrics:read to {role_name}")
        else:
            print(f"  {role_name} already has metrics:read")
    
    await db.commit()
    print("\nMetrics permissions setup complete!")


async def verify_permissions(db: AsyncSession):
    """Verify the permissions were added correctly"""
    print("\n\nVerifying Permissions")
    print("=" * 50)
    
    # Check Report Owner permissions
    result = await db.execute(
        select(Role).where(Role.role_name == "Report Owner")
    )
    report_owner_role = result.scalar_one_or_none()
    
    if report_owner_role:
        # Get all permissions for Report Owner
        result = await db.execute(
            select(Permission)
            .join(RolePermission, Permission.permission_id == RolePermission.permission_id)
            .where(RolePermission.role_id == report_owner_role.role_id)
            .where(Permission.resource == "metrics")
        )
        metrics_perms = result.scalars().all()
        
        print(f"\nReport Owner metrics permissions:")
        for perm in metrics_perms:
            print(f"  - {perm.resource}:{perm.action}")
        
        if not metrics_perms:
            print("  No metrics permissions found!")


async def main():
    """Main function"""
    async for db in get_db():
        try:
            await add_metrics_resource_permissions(db)
            await verify_permissions(db)
            
        except Exception as e:
            print(f"\nError: {str(e)}")
            await db.rollback()
            raise
        finally:
            await db.close()
            break


if __name__ == "__main__":
    asyncio.run(main())