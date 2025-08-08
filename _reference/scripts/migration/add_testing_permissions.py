#!/usr/bin/env python3
"""
Add testing permissions to Tester role
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.models.rbac import Permission, RolePermission
from sqlalchemy import select
from datetime import datetime


async def add_permissions():
    """Add testing permissions to Tester role"""
    async with AsyncSessionLocal() as db:
        try:
            # Check what testing related permissions exist
            testing_perms = await db.execute(
                select(Permission).where(
                    Permission.resource.in_(["testing", "test_execution", "testing_execution"])
                )
            )
            testing_perms = testing_perms.scalars().all()
            
            print(f"Found {len(testing_perms)} testing related permissions:")
            for p in testing_perms:
                print(f"  - {p.resource}:{p.action} (ID: {p.permission_id})")
            
            # Add all to Tester role
            added_count = 0
            for perm in testing_perms:
                existing = await db.execute(
                    select(RolePermission).where(
                        RolePermission.role_id == 3,
                        RolePermission.permission_id == perm.permission_id
                    )
                )
                
                if not existing.scalar_one_or_none():
                    rp = RolePermission(
                        role_id=3,
                        permission_id=perm.permission_id,
                        created_at=datetime.utcnow()
                    )
                    db.add(rp)
                    added_count += 1
                    print(f"Added {perm.resource}:{perm.action} to Tester role")
            
            if added_count > 0:
                await db.commit()
                print(f"\nAdded {added_count} permissions to Tester role")
            else:
                print("\nAll permissions already assigned")
                
        except Exception as e:
            print(f"Error: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(add_permissions())