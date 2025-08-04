#!/usr/bin/env python3
"""
Migration script to populate initial RBAC data
Converts existing hardcoded roles to database-driven RBAC
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.user import User
from app.models.rbac import Permission, Role, RolePermission, UserRole
from app.services.permission_service import PermissionService

# Define all permissions in the system
SYSTEM_PERMISSIONS = [
    # Test Cycle Management
    ("cycles", "create", "Create new test cycles"),
    ("cycles", "read", "View test cycles"),
    ("cycles", "update", "Update test cycles"),
    ("cycles", "delete", "Delete test cycles"),
    ("cycles", "assign", "Assign reports to cycles"),
    
    # Report Management
    ("reports", "create", "Create new reports"),
    ("reports", "read", "View reports"),
    ("reports", "update", "Update reports"),
    ("reports", "delete", "Delete reports"),
    ("reports", "assign", "Assign testers to reports"),
    ("reports", "approve", "Approve report results"),
    ("reports", "override", "Override report decisions"),
    
    # User Management
    ("users", "create", "Create new users"),
    ("users", "read", "View users"),
    ("users", "update", "Update users"),
    ("users", "delete", "Delete users"),
    ("users", "assign", "Assign users to tasks"),
    
    # Planning Phase
    ("planning", "execute", "Execute planning phase"),
    ("planning", "upload", "Upload planning documents"),
    ("planning", "create", "Create attributes"),
    ("planning", "update", "Update attributes"),
    ("planning", "delete", "Delete attributes"),
    ("planning", "complete", "Complete planning phase"),
    
    # Scoping Phase
    ("scoping", "execute", "Execute scoping phase"),
    ("scoping", "generate", "Generate scoping recommendations"),
    ("scoping", "submit", "Submit scoping results"),
    ("scoping", "approve", "Approve scoping results"),
    ("scoping", "complete", "Complete scoping phase"),
    
    # Data Provider Phase
    ("data_owner", "execute", "Execute data provider phase"),
    ("data_owner", "identify", "Identify data providers"),
    ("data_owner", "assign", "Assign data providers"),
    ("data_owner", "upload", "Upload data provider info"),
    ("data_owner", "escalate", "Escalate data provider issues"),
    ("data_owner", "complete", "Complete data provider phase"),
    
    # Sample Selection Phase
    ("sample_selection", "execute", "Execute sample selection"),
    ("sample_selection", "generate", "Generate samples"),
    ("sample_selection", "upload", "Upload sample data"),
    ("sample_selection", "approve", "Approve samples"),
    ("sample_selection", "complete", "Complete sample selection"),
    
    # Request Info Phase
    ("request_info", "execute", "Execute request info phase"),
    ("request_info", "upload", "Upload requested documents"),
    ("request_info", "provide", "Provide data sources"),
    ("request_info", "complete", "Complete request info phase"),
    
    # Testing Phase
    ("testing", "execute", "Execute testing"),
    ("testing", "submit", "Submit test results"),
    ("testing", "review", "Review test results"),
    ("testing", "approve", "Approve test results"),
    ("testing", "complete", "Complete testing phase"),
    
    # Observations Phase
    ("observations", "create", "Create observations"),
    ("observations", "submit", "Submit observations"),
    ("observations", "review", "Review observations"),
    ("observations", "approve", "Approve observations"),
    ("observations", "override", "Override observation decisions"),
    ("observations", "complete", "Complete observations phase"),
    
    # Workflow Management
    ("workflow", "view", "View workflow status"),
    ("workflow", "approve", "Approve workflow transitions"),
    ("workflow", "override", "Override workflow rules"),
    
    # LOB Management
    ("lobs", "create", "Create LOBs"),
    ("lobs", "read", "View LOBs"),
    ("lobs", "update", "Update LOBs"),
    ("lobs", "delete", "Delete LOBs"),
    ("lobs", "manage", "Manage LOB assignments"),
    
    # System Administration
    ("system", "admin", "Full system administration"),
    ("permissions", "manage", "Manage permissions and roles"),
]

# Define role to permission mappings
ROLE_PERMISSIONS = {
    "Admin": ["*:*"],  # Special case - all permissions
    
    "Test Executive": [
        "cycles:create", "cycles:read", "cycles:update", "cycles:delete", "cycles:assign",
        "reports:read", "reports:assign",
        "users:read", "users:assign",
        "lobs:read",
        "workflow:view", "workflow:approve",
        "planning:read", "scoping:read", "testing:read", "observations:read"
    ],
    
    "Tester": [
        "cycles:read",
        "reports:read",
        "planning:execute", "planning:upload", "planning:create", "planning:update", 
        "planning:delete", "planning:complete",
        "scoping:execute", "scoping:generate", "scoping:submit", "scoping:complete",
        "sample_selection:execute", "sample_selection:generate", "sample_selection:upload", 
        "sample_selection:complete",
        "testing:execute", "testing:submit", "testing:complete",
        "observations:create", "observations:submit",
        "workflow:view",
        "lobs:read"
    ],
    
    "Report Owner": [
        "reports:read", "reports:approve",
        "scoping:approve",
        "sample_selection:approve",
        "testing:review", "testing:approve",
        "observations:review", "observations:approve",
        "workflow:view", "workflow:approve"
    ],
    
    "Report Owner Executive": [
        "reports:read", "reports:override",
        "workflow:view", "workflow:override",
        "observations:override",
        "cycles:read",
        "testing:read",
        "scoping:read"
    ],
    
    "Data Owner": [
        "data_owner:execute", "data_owner:upload",
        "request_info:provide", "request_info:upload",
        "workflow:view",
        "reports:read"
    ],
    
    "Data Executive": [
        "lobs:read", "lobs:manage",
        "data_owner:identify", "data_owner:assign", "data_owner:escalate",
        "users:read",
        "cycles:read", "reports:read",
        "workflow:view"
    ]
}


async def create_permissions(db: AsyncSession):
    """Create all system permissions"""
    print("Creating permissions...")
    
    for resource, action, description in SYSTEM_PERMISSIONS:
        # Check if already exists
        existing = await db.execute(
            select(Permission).where(
                Permission.resource == resource,
                Permission.action == action
            )
        )
        if not existing.scalar_one_or_none():
            permission = Permission(
                resource=resource,
                action=action,
                description=description
            )
            db.add(permission)
            print(f"  Created permission: {resource}:{action}")
        else:
            print(f"  Permission already exists: {resource}:{action}")
    
    await db.commit()
    print("Permissions created successfully!")


async def create_roles(db: AsyncSession):
    """Create all system roles"""
    print("\nCreating roles...")
    
    role_descriptions = {
        "Admin": "System administrator with full access",
        "Test Executive": "Manages test cycles and team assignments",
        "Tester": "Executes testing workflow phases",
        "Report Owner": "Owns reports and approves testing activities",
        "Report Owner Executive": "Executive oversight of report owners",
        "Data Owner": "Provides source data for testing",
        "Data Executive": "Chief Data Officer - manages LOB data provider assignments"
    }
    
    created_roles = {}
    
    for role_name, description in role_descriptions.items():
        # Check if already exists
        existing = await db.execute(
            select(Role).where(Role.role_name == role_name)
        )
        role = existing.scalar_one_or_none()
        
        if not role:
            role = Role(
                role_name=role_name,
                description=description,
                is_system=True  # System roles cannot be deleted
            )
            db.add(role)
            print(f"  Created role: {role_name}")
        else:
            print(f"  Role already exists: {role_name}")
        
        created_roles[role_name] = role
    
    await db.commit()
    print("Roles created successfully!")
    
    return created_roles


async def assign_permissions_to_roles(db: AsyncSession, roles: dict):
    """Assign permissions to roles"""
    print("\nAssigning permissions to roles...")
    
    # Get all permissions
    perms_result = await db.execute(select(Permission))
    all_permissions = {f"{p.resource}:{p.action}": p for p in perms_result.scalars()}
    
    for role_name, permission_strings in ROLE_PERMISSIONS.items():
        role = roles.get(role_name)
        if not role:
            print(f"  Warning: Role {role_name} not found")
            continue
        
        print(f"\n  Assigning permissions to {role_name}...")
        
        # Handle special case for admin
        if "*:*" in permission_strings:
            # Assign all permissions
            for perm in all_permissions.values():
                existing = await db.execute(
                    select(RolePermission).where(
                        RolePermission.role_id == role.role_id,
                        RolePermission.permission_id == perm.permission_id
                    )
                )
                if not existing.scalar_one_or_none():
                    role_perm = RolePermission(
                        role_id=role.role_id,
                        permission_id=perm.permission_id,
                        granted_by=1  # System user
                    )
                    db.add(role_perm)
            print(f"    Assigned all permissions to {role_name}")
        else:
            # Assign specific permissions
            for perm_string in permission_strings:
                perm = all_permissions.get(perm_string)
                if not perm:
                    print(f"    Warning: Permission {perm_string} not found")
                    continue
                
                existing = await db.execute(
                    select(RolePermission).where(
                        RolePermission.role_id == role.role_id,
                        RolePermission.permission_id == perm.permission_id
                    )
                )
                if not existing.scalar_one_or_none():
                    role_perm = RolePermission(
                        role_id=role.role_id,
                        permission_id=perm.permission_id,
                        granted_by=1  # System user
                    )
                    db.add(role_perm)
                    print(f"    Assigned {perm_string}")
    
    await db.commit()
    print("\nPermissions assigned successfully!")


async def migrate_existing_users(db: AsyncSession, roles: dict):
    """Migrate existing users to new RBAC system"""
    print("\nMigrating existing users to RBAC...")
    
    # Get all users
    users_result = await db.execute(select(User))
    users = users_result.scalars().all()
    
    for user in users:
        # Map old role enum to new role
        old_role = user.role.value if hasattr(user.role, 'value') else str(user.role)
        
        # Find matching role
        role = None
        for role_name, role_obj in roles.items():
            if role_name.lower().replace(" ", "_") == old_role.lower().replace(" ", "_"):
                role = role_obj
                break
        
        if not role:
            print(f"  Warning: No matching role for user {user.email} with role {old_role}")
            continue
        
        # Check if already assigned
        existing = await db.execute(
            select(UserRole).where(
                UserRole.user_id == user.user_id,
                UserRole.role_id == role.role_id
            )
        )
        if not existing.scalar_one_or_none():
            user_role = UserRole(
                user_id=user.user_id,
                role_id=role.role_id,
                assigned_by=1  # System user
            )
            db.add(user_role)
            print(f"  Assigned role {role.role_name} to user {user.email}")
        else:
            print(f"  User {user.email} already has role {role.role_name}")
    
    await db.commit()
    print("User migration completed!")


async def main():
    """Run the migration"""
    print("Starting RBAC migration...")
    
    async for db in get_db():
        try:
            # Create permissions
            await create_permissions(db)
            
            # Create roles
            roles = await create_roles(db)
            
            # Assign permissions to roles
            await assign_permissions_to_roles(db, roles)
            
            # Migrate existing users
            await migrate_existing_users(db, roles)
            
            print("\nRBAC migration completed successfully!")
            break
            
        except Exception as e:
            print(f"\nError during migration: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main())