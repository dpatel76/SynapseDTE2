#!/usr/bin/env python3
"""
Seed RBAC permissions and default roles from rbac_config.py
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.rbac_config import (
    RESOURCES, Action, RESOURCE_LEVEL_PERMISSIONS,
    DEFAULT_ROLE_PERMISSIONS
)
from app.models.rbac import Permission, Role, RolePermission
from app.models.rbac_resource import Resource
from app.core.auth import UserRoles


async def seed_permissions(db: AsyncSession):
    """Create all permissions from rbac_config"""
    print("Seeding Permissions")
    print("=" * 50)
    
    created_count = 0
    
    # Get all existing permissions for checking
    existing_perms = await db.execute(
        select(Permission.resource, Permission.action)
    )
    existing_set = {(p.resource, p.action) for p in existing_perms}
    
    # Create permissions for each resource
    for resource_key, resource_info in RESOURCES.items():
        actions = resource_info.get("actions", [])
        
        for action in actions:
            action_value = action.value if hasattr(action, 'value') else action
            if (resource_key, action_value) not in existing_set:
                permission = Permission(
                    resource=resource_key,
                    action=action_value,
                    description=f"{action_value.title()} {resource_info.get('display_name', resource_key)}"
                )
                db.add(permission)
                created_count += 1
                print(f"  Created: {resource_key}:{action_value}")
            else:
                print(f"  Exists: {resource_key}:{action_value}")
    
    await db.commit()
    print(f"\nCreated {created_count} new permissions")
    
    # Count total permissions
    result = await db.execute(select(Permission))
    total = len(result.scalars().all())
    print(f"Total permissions in database: {total}")
    
    return created_count


async def seed_roles(db: AsyncSession):
    """Create default roles"""
    print("\n\nSeeding Roles")
    print("=" * 50)
    
    # Define role mappings
    role_mappings = {
        UserRoles.ADMIN: {
            "name": "Administrator",
            "description": "Full system access",
            "is_system": True
        },
        UserRoles.TEST_EXECUTIVE: {
            "name": "Test Executive",
            "description": "Manages test cycles and assignments",
            "is_system": True
        },
        UserRoles.TESTER: {
            "name": "Tester",
            "description": "Executes test procedures",
            "is_system": True
        },
        UserRoles.REPORT_OWNER: {
            "name": "Report Owner",
            "description": "Owns and approves reports",
            "is_system": True
        },
        UserRoles.REPORT_OWNER_EXECUTIVE: {
            "name": "Report Owner Executive",
            "description": "Executive oversight of reports",
            "is_system": True
        },
        UserRoles.DATA_OWNER: {
            "name": "Data Owner",
            "description": "Provides data for testing",
            "is_system": True
        },
        UserRoles.DATA_EXECUTIVE: {
            "name": "Chief Data Officer",
            "description": "Oversees data governance",
            "is_system": True
        }
    }
    
    created_count = 0
    
    for role_key, role_info in role_mappings.items():
        # Check if role exists
        result = await db.execute(
            select(Role).where(Role.role_name == role_info["name"])
        )
        existing_role = result.scalar_one_or_none()
        
        if not existing_role:
            role = Role(
                role_name=role_info["name"],
                description=role_info["description"],
                is_system=role_info["is_system"]
            )
            db.add(role)
            created_count += 1
            print(f"  Created: {role_info['name']}")
        else:
            print(f"  Exists: {role_info['name']}")
    
    await db.commit()
    print(f"\nCreated {created_count} new roles")
    
    return created_count


async def seed_role_permissions(db: AsyncSession):
    """Assign default permissions to roles"""
    print("\n\nAssigning Role Permissions")
    print("=" * 50)
    
    # Get all permissions
    result = await db.execute(select(Permission))
    all_permissions = {
        f"{p.resource}:{p.action}": p for p in result.scalars().all()
    }
    
    # Get all roles
    result = await db.execute(select(Role))
    all_roles = {r.role_name: r for r in result.scalars().all()}
    
    created_count = 0
    
    # Map UserRoles to Role names
    role_name_mapping = {
        UserRoles.ADMIN: "Administrator",
        UserRoles.TEST_EXECUTIVE: "Test Executive",
        UserRoles.TESTER: "Tester",
        UserRoles.REPORT_OWNER: "Report Owner",
        UserRoles.REPORT_OWNER_EXECUTIVE: "Report Owner Executive",
        UserRoles.DATA_OWNER: "Data Owner",
        UserRoles.DATA_EXECUTIVE: "Chief Data Officer"
    }
    
    for role_enum, permissions in DEFAULT_ROLE_PERMISSIONS.items():
        role_name = role_name_mapping.get(role_enum)
        if not role_name or role_name not in all_roles:
            print(f"  Warning: Role {role_enum} not found")
            continue
            
        role = all_roles[role_name]
        
        # Get existing permissions for this role
        result = await db.execute(
            select(RolePermission.permission_id)
            .where(RolePermission.role_id == role.role_id)
        )
        existing_perm_ids = {rp.permission_id for rp in result}
        
        # Handle wildcard permissions for ADMIN
        if permissions == ["*:*"]:
            # Grant all permissions to admin
            for perm_key, permission in all_permissions.items():
                if permission.permission_id not in existing_perm_ids:
                    role_perm = RolePermission(
                        role_id=role.role_id,
                        permission_id=permission.permission_id
                    )
                    db.add(role_perm)
                    created_count += 1
            print(f"  {role_name}: Granted all permissions")
        else:
            # Grant specific permissions
            granted = []
            for perm_str in permissions:
                if perm_str in all_permissions:
                    permission = all_permissions[perm_str]
                    if permission.permission_id not in existing_perm_ids:
                        role_perm = RolePermission(
                            role_id=role.role_id,
                            permission_id=permission.permission_id
                        )
                        db.add(role_perm)
                        created_count += 1
                        granted.append(perm_str)
                else:
                    print(f"    Warning: Permission {perm_str} not found")
            
            if granted:
                print(f"  {role_name}: Granted {len(granted)} permissions")
    
    await db.commit()
    print(f"\nCreated {created_count} new role-permission assignments")
    
    return created_count


async def verify_setup(db: AsyncSession):
    """Verify the RBAC setup"""
    print("\n\nVerifying RBAC Setup")
    print("=" * 50)
    
    # Count resources
    result = await db.execute(select(Resource))
    resources = result.scalars().all()
    print(f"Resources: {len(resources)}")
    
    # Count permissions
    result = await db.execute(select(Permission))
    permissions = result.scalars().all()
    print(f"Permissions: {len(permissions)}")
    
    # Count roles
    result = await db.execute(select(Role))
    roles = result.scalars().all()
    print(f"Roles: {len(roles)}")
    
    # Show role permission counts
    print("\nPermissions per Role:")
    for role in roles:
        result = await db.execute(
            select(RolePermission)
            .where(RolePermission.role_id == role.role_id)
        )
        count = len(result.scalars().all())
        print(f"  {role.role_name}: {count} permissions")


async def main():
    """Main function"""
    async for db in get_db():
        try:
            # Seed permissions
            perm_count = await seed_permissions(db)
            
            # Seed roles
            role_count = await seed_roles(db)
            
            # Assign permissions to roles
            assignment_count = await seed_role_permissions(db)
            
            # Verify setup
            await verify_setup(db)
            
            print("\n\nRBAC Seeding Complete!")
            print(f"- Created {perm_count} permissions")
            print(f"- Created {role_count} roles")
            print(f"- Created {assignment_count} role-permission assignments")
            
        except Exception as e:
            print(f"\nError: {str(e)}")
            await db.rollback()
            raise
        finally:
            await db.close()
            break


if __name__ == "__main__":
    asyncio.run(main())