#!/usr/bin/env python3
"""
Safe migration to add RBAC resources without breaking existing functionality
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, Set

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.core.database import get_db
from app.models.rbac import Permission
from app.core.rbac_config import RESOURCES
from app.core.logging import get_logger

logger = get_logger(__name__)


async def check_existing_permissions(db: AsyncSession) -> Dict[str, Set[str]]:
    """Check what permissions currently exist in the database"""
    result = await db.execute(select(Permission))
    permissions = result.scalars().all()
    
    existing = {}
    for perm in permissions:
        if perm.resource not in existing:
            existing[perm.resource] = set()
        existing[perm.resource].add(perm.action)
    
    return existing


async def analyze_resource_differences(db: AsyncSession):
    """Analyze differences between existing permissions and defined resources"""
    print("\n=== Analyzing Current System ===")
    
    # Get existing permissions
    existing = await check_existing_permissions(db)
    
    print(f"\nFound {len(existing)} unique resources in permissions table:")
    for resource in sorted(existing.keys()):
        actions = sorted(existing[resource])
        print(f"  - {resource}: {', '.join(actions)}")
    
    # Check for resources in config but not in DB
    print("\n=== Resource Analysis ===")
    
    config_resources = set(RESOURCES.keys())
    db_resources = set(existing.keys())
    
    # Resources in config but not in DB
    new_resources = config_resources - db_resources
    if new_resources:
        print(f"\nResources defined in config but not in DB: {sorted(new_resources)}")
    
    # Resources in DB but not in config
    orphan_resources = db_resources - config_resources
    if orphan_resources:
        print(f"\nResources in DB but not in config: {sorted(orphan_resources)}")
        print("  (These will continue to work for backward compatibility)")
    
    # Check for action mismatches
    print("\n=== Action Analysis ===")
    for resource in config_resources & db_resources:
        config_actions = set(action.value for action in RESOURCES[resource]["actions"])
        db_actions = existing.get(resource, set())
        
        missing_actions = config_actions - db_actions
        extra_actions = db_actions - config_actions
        
        if missing_actions or extra_actions:
            print(f"\n{resource}:")
            if missing_actions:
                print(f"  Actions in config but not in DB: {sorted(missing_actions)}")
            if extra_actions:
                print(f"  Actions in DB but not in config: {sorted(extra_actions)}")


async def create_missing_permissions(db: AsyncSession, dry_run: bool = True):
    """Create any missing permissions defined in config"""
    print("\n=== Creating Missing Permissions ===")
    
    existing = await check_existing_permissions(db)
    created_count = 0
    
    for resource, config in RESOURCES.items():
        for action in config["actions"]:
            action_str = action.value
            
            # Check if permission exists
            if resource not in existing or action_str not in existing[resource]:
                if dry_run:
                    print(f"  Would create: {resource}:{action_str}")
                else:
                    # Create the permission
                    permission = Permission(
                        resource=resource,
                        action=action_str,
                        description=f"{config['description']} - {action_str}"
                    )
                    db.add(permission)
                    print(f"  Created: {resource}:{action_str}")
                created_count += 1
    
    if not dry_run:
        await db.commit()
        print(f"\nCreated {created_count} new permissions")
    else:
        print(f"\nDry run: Would create {created_count} new permissions")


async def check_resource_table_exists(db: AsyncSession) -> bool:
    """Check if resources table exists"""
    result = await db.execute(
        text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'resources'
        )
        """)
    )
    return result.scalar()


async def validate_permission_functionality(db: AsyncSession):
    """Validate that permission checks still work"""
    print("\n=== Validating Permission Functionality ===")
    
    from app.services.permission_service import get_permission_service
    
    # Create a test user ID (assuming user 1 exists as admin)
    test_user_id = 1
    
    # Test some common permissions
    test_cases = [
        ("cycles", "create"),
        ("reports", "read"),
        ("planning", "execute"),
        ("workflow", "approve")
    ]
    
    permission_service = await get_permission_service(db)
    
    for resource, action in test_cases:
        try:
            # This should not raise an error
            result = await permission_service.check_permission(
                test_user_id, resource, action
            )
            print(f"  ✓ Permission check works: {resource}:{action} = {result}")
        except Exception as e:
            print(f"  ✗ Permission check failed: {resource}:{action} - {str(e)}")


async def main():
    """Run the safe migration analysis"""
    print("RBAC Resource Migration Safety Check")
    print("====================================")
    
    async for db in get_db():
        try:
            # Check if resources table exists
            has_resources_table = await check_resource_table_exists(db)
            print(f"\nResources table exists: {has_resources_table}")
            
            # Analyze current state
            await analyze_resource_differences(db)
            
            # Show what would be created
            print("\n--- DRY RUN MODE ---")
            await create_missing_permissions(db, dry_run=True)
            
            # Validate existing functionality
            await validate_permission_functionality(db)
            
            # Ask for confirmation
            print("\n" + "="*50)
            response = input("\nProceed with creating missing permissions? (yes/no): ")
            
            if response.lower() == 'yes':
                await create_missing_permissions(db, dry_run=False)
                print("\n✓ Migration completed successfully!")
            else:
                print("\n✗ Migration cancelled")
            
            break
            
        except Exception as e:
            logger.error(f"Migration error: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main())