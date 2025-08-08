#!/usr/bin/env python3
"""
Add request_info permissions to Tester role
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
    """Add request_info permissions to Tester role"""
    async with AsyncSessionLocal() as db:
        try:
            # Find all request_info permissions
            perms = await db.execute(
                select(Permission).where(
                    Permission.resource == "request_info"
                )
            )
            perms = perms.scalars().all()
            
            if not perms:
                print("No request_info permissions found in database")
                # Check what permissions exist
                all_resources = await db.execute(
                    select(Permission.resource).distinct()
                )
                print("Available resources:")
                for r in all_resources.scalars():
                    print(f"  - {r}")
                return
                
            print(f"Found {len(perms)} request_info permissions")
            
            added_count = 0
            # Add to Tester role (role_id = 3)
            for perm in perms:
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
                print(f"Added {added_count} permissions to Tester role")
            else:
                print("All permissions already assigned")
                
        except Exception as e:
            print(f"Error: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(add_permissions())