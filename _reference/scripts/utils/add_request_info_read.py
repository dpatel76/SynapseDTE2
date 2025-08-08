#!/usr/bin/env python3
"""
Add request_info:read permission to Tester role
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
    """Add request_info:read permission to Tester role"""
    async with AsyncSessionLocal() as db:
        try:
            # Check if request_info:read exists
            perm = await db.execute(
                select(Permission).where(
                    Permission.resource == "request_info",
                    Permission.action == "read"
                )
            )
            perm = perm.scalar_one_or_none()
            
            if not perm:
                print("request_info:read permission not found, creating it")
                # Get max permission_id
                max_id = await db.execute(
                    select(Permission.permission_id).order_by(Permission.permission_id.desc()).limit(1)
                )
                max_id = max_id.scalar() or 0
                
                perm = Permission(
                    permission_id=max_id + 1,
                    resource="request_info",
                    action="read",
                    description="Read request info data",
                    created_at=datetime.utcnow()
                )
                db.add(perm)
                await db.commit()
                print(f"Created permission: {perm.resource}:{perm.action} (ID: {perm.permission_id})")
            else:
                print(f"Found permission: {perm.resource}:{perm.action} (ID: {perm.permission_id})")
            
            # Add to Tester role (role_id = 3)
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
                await db.commit()
                print("Added request_info:read permission to Tester role")
            else:
                print("Permission already assigned to Tester role")
                
        except Exception as e:
            print(f"Error: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(add_permissions())