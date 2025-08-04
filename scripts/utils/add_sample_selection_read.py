#!/usr/bin/env python3
"""
Add sample_selection:read permission to Tester role
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.models.rbac import Permission, RolePermission
from sqlalchemy import select
from datetime import datetime


async def add_read_permission():
    """Add sample_selection:read permission to Tester role"""
    async with AsyncSessionLocal() as db:
        try:
            # Find the sample_selection:read permission
            perm = await db.execute(
                select(Permission).where(
                    Permission.resource == "sample_selection",
                    Permission.action == "read"
                )
            )
            perm = perm.scalar_one_or_none()
            
            if not perm:
                print("sample_selection:read permission not found")
                return
                
            print(f"Found permission: {perm.resource}:{perm.action} (ID: {perm.permission_id})")
            
            # Add to Tester role (role_id = 3)
            existing = await db.execute(
                select(RolePermission).where(
                    RolePermission.role_id == 3,
                    RolePermission.permission_id == perm.permission_id
                )
            )
            
            if existing.scalar_one_or_none():
                print("Permission already assigned to Tester role")
            else:
                rp = RolePermission(
                    role_id=3,
                    permission_id=perm.permission_id,
                    created_at=datetime.utcnow()
                )
                db.add(rp)
                await db.commit()
                print("Added sample_selection:read permission to Tester role")
                
            # Also add to Test Executive role (role_id = 2)
            existing = await db.execute(
                select(RolePermission).where(
                    RolePermission.role_id == 2,
                    RolePermission.permission_id == perm.permission_id
                )
            )
            
            if not existing.scalar_one_or_none():
                rp = RolePermission(
                    role_id=2,
                    permission_id=perm.permission_id,
                    created_at=datetime.utcnow()
                )
                db.add(rp)
                await db.commit()
                print("Added sample_selection:read permission to Test Executive role")
                
        except Exception as e:
            print(f"Error: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(add_read_permission())