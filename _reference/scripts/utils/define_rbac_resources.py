#!/usr/bin/env python3
"""
Define all RBAC resources in the system
This creates a centralized resource registry
"""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.rbac_resource import Resource

# Define all system resources with hierarchy
SYSTEM_RESOURCES = [
    # System-level resources
    {
        "name": "system",
        "display_name": "System Administration",
        "description": "Core system administration functions",
        "type": "system",
        "children": [
            {
                "name": "permissions",
                "display_name": "Permission Management",
                "description": "Manage roles and permissions",
                "type": "module"
            }
        ]
    },
    
    # Workflow resources
    {
        "name": "workflow",
        "display_name": "Workflow Management",
        "description": "7-phase testing workflow",
        "type": "workflow",
        "children": [
            {
                "name": "planning",
                "display_name": "Planning Phase",
                "description": "Phase 1: Document upload and attribute definition",
                "type": "module"
            },
            {
                "name": "scoping",
                "display_name": "Scoping Phase",
                "description": "Phase 2: Attribute scoping and recommendations",
                "type": "module"
            },
            {
                "name": "data_owner",
                "display_name": "Data Provider ID Phase",
                "description": "Phase 3: Identify and assign data providers",
                "type": "module"
            },
            {
                "name": "sample_selection",
                "display_name": "Sample Selection Phase",
                "description": "Phase 4: Generate and approve test samples",
                "type": "module"
            },
            {
                "name": "request_info",
                "display_name": "Request Information Phase",
                "description": "Phase 5: Request and collect data",
                "type": "module"
            },
            {
                "name": "testing",
                "display_name": "Testing Execution Phase",
                "description": "Phase 6: Execute tests on samples",
                "type": "module"
            },
            {
                "name": "observations",
                "display_name": "Observation Management Phase",
                "description": "Phase 7: Manage and resolve observations",
                "type": "module"
            }
        ]
    },
    
    # Entity management resources
    {
        "name": "entities",
        "display_name": "Entity Management",
        "description": "Core business entities",
        "type": "system",
        "children": [
            {
                "name": "cycles",
                "display_name": "Test Cycles",
                "description": "Test cycle management",
                "type": "entity"
            },
            {
                "name": "reports",
                "display_name": "Reports",
                "description": "Report management",
                "type": "entity"
            },
            {
                "name": "users",
                "display_name": "Users",
                "description": "User management",
                "type": "entity"
            },
            {
                "name": "lobs",
                "display_name": "Lines of Business",
                "description": "LOB management",
                "type": "entity"
            }
        ]
    }
]


async def create_resource(db: AsyncSession, resource_data: dict, parent: Resource = None) -> Resource:
    """Create a resource and its children recursively"""
    
    # Check if resource exists
    existing = await db.execute(
        select(Resource).where(Resource.resource_name == resource_data["name"])
    )
    resource = existing.scalar_one_or_none()
    
    if not resource:
        resource = Resource(
            resource_name=resource_data["name"],
            display_name=resource_data["display_name"],
            description=resource_data["description"],
            resource_type=resource_data["type"],
            parent_resource_id=parent.resource_id if parent else None
        )
        db.add(resource)
        await db.flush()  # Get the ID without committing
        print(f"Created resource: {resource.full_path}")
    else:
        print(f"Resource exists: {resource.full_path}")
    
    # Create children
    for child_data in resource_data.get("children", []):
        await create_resource(db, child_data, resource)
    
    return resource


async def update_permissions_with_resources(db: AsyncSession):
    """Update existing permissions to link with resources"""
    from app.models.rbac import Permission
    
    print("\nLinking permissions to resources...")
    
    # Get all permissions
    perms_result = await db.execute(select(Permission))
    permissions = perms_result.scalars().all()
    
    # Get all resources
    resources_result = await db.execute(select(Resource))
    resources = {r.resource_name: r for r in resources_result.scalars()}
    
    for permission in permissions:
        # Find matching resource
        resource = resources.get(permission.resource)
        if resource:
            permission.resource_id = resource.resource_id
            print(f"  Linked {permission.permission_string} to resource {resource.resource_name}")
        else:
            print(f"  Warning: No resource found for permission {permission.permission_string}")
    
    await db.commit()


async def main():
    """Create all resources"""
    print("Creating RBAC resources...")
    
    async for db in get_db():
        try:
            # Create all resources
            for resource_data in SYSTEM_RESOURCES:
                await create_resource(db, resource_data)
            
            await db.commit()
            print("\nResources created successfully!")
            
            # Link existing permissions
            await update_permissions_with_resources(db)
            
            print("\nRBAC resources setup completed!")
            break
            
        except Exception as e:
            print(f"\nError: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main())