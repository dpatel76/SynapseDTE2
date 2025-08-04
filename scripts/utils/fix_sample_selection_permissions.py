#!/usr/bin/env python3
"""
Fix sample selection permissions by adding the correct resource names
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.models.rbac import Permission, RolePermission
from sqlalchemy import select
from datetime import datetime


async def fix_permissions():
    """Add missing sample_selection permissions"""
    async with AsyncSessionLocal() as db:
        try:
            # Check if sample_selection permissions already exist
            existing = await db.execute(
                select(Permission).where(Permission.resource == "sample_selection")
            )
            existing_perms = existing.scalars().all()
            
            if existing_perms:
                print(f"Found {len(existing_perms)} existing sample_selection permissions")
                return
            
            # Get the highest permission_id
            max_id_result = await db.execute(
                select(Permission.permission_id).order_by(Permission.permission_id.desc()).limit(1)
            )
            max_id = max_id_result.scalar() or 0
            
            # Add sample_selection permissions
            new_permissions = [
                {
                    'permission_id': max_id + 1,
                    'permission_name': 'read_sample_selection',
                    'resource': 'sample_selection',
                    'action': 'read',
                    'description': 'Read sample selection data',
                    'created_at': datetime.utcnow()
                },
                {
                    'permission_id': max_id + 2,
                    'permission_name': 'execute_sample_selection',
                    'resource': 'sample_selection',
                    'action': 'execute',
                    'description': 'Execute sample selection phase',
                    'created_at': datetime.utcnow()
                },
                {
                    'permission_id': max_id + 3,
                    'permission_name': 'generate_sample_selection',
                    'resource': 'sample_selection',
                    'action': 'generate',
                    'description': 'Generate sample selection',
                    'created_at': datetime.utcnow()
                },
                {
                    'permission_id': max_id + 4,
                    'permission_name': 'upload_sample_selection',
                    'resource': 'sample_selection',
                    'action': 'upload',
                    'description': 'Upload sample selection',
                    'created_at': datetime.utcnow()
                },
                {
                    'permission_id': max_id + 5,
                    'permission_name': 'approve_sample_selection',
                    'resource': 'sample_selection',
                    'action': 'approve',
                    'description': 'Approve sample selection',
                    'created_at': datetime.utcnow()
                }
            ]
            
            # Insert new permissions
            for perm_data in new_permissions:
                perm = Permission(**perm_data)
                db.add(perm)
            
            await db.commit()
            print(f"Added {len(new_permissions)} new sample_selection permissions")
            
            # Now add role permissions for Tester role
            # Get Tester role ID
            tester_role = await db.execute(
                select(RolePermission.role_id).where(RolePermission.role_id == 1).limit(1)
            )
            tester_role_id = tester_role.scalar()
            
            if tester_role_id:
                # Add permissions for Tester role
                tester_permissions = [max_id + 1, max_id + 2, max_id + 3, max_id + 4]  # read, execute, generate, upload
                
                for perm_id in tester_permissions:
                    # Check if already exists
                    existing_rp = await db.execute(
                        select(RolePermission).where(
                            RolePermission.role_id == tester_role_id,
                            RolePermission.permission_id == perm_id
                        )
                    )
                    if not existing_rp.scalar():
                        rp = RolePermission(
                            role_id=tester_role_id,
                            permission_id=perm_id,
                            created_at=datetime.utcnow()
                        )
                        db.add(rp)
                
                # Add permissions for Test Executive role (role_id = 2)
                test_exec_permissions = [max_id + 1, max_id + 2, max_id + 3, max_id + 4, max_id + 5]  # all permissions
                
                for perm_id in test_exec_permissions:
                    # Check if already exists
                    existing_rp = await db.execute(
                        select(RolePermission).where(
                            RolePermission.role_id == 2,
                            RolePermission.permission_id == perm_id
                        )
                    )
                    if not existing_rp.scalar():
                        rp = RolePermission(
                            role_id=2,
                            permission_id=perm_id,
                            created_at=datetime.utcnow()
                        )
                        db.add(rp)
                
                # Add approve permission for Report Owner role (role_id = 5)
                existing_rp = await db.execute(
                    select(RolePermission).where(
                        RolePermission.role_id == 5,
                        RolePermission.permission_id == max_id + 5
                    )
                )
                if not existing_rp.scalar():
                    rp = RolePermission(
                        role_id=5,
                        permission_id=max_id + 5,  # approve permission
                        created_at=datetime.utcnow()
                    )
                    db.add(rp)
                
                await db.commit()
                print("Added role permissions for sample_selection")
            
        except Exception as e:
            print(f"Error: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(fix_permissions())