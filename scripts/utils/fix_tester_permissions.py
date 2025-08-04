"""
Script to fix missing permissions for tester role
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def fix_tester_permissions():
    """Add missing permissions for tester role"""
    
    async with AsyncSessionLocal() as db:
        try:
            # First check what permissions already exist
            result = await db.execute(text("""
                SELECT permission_id, resource, action 
                FROM rbac_permissions 
                WHERE resource IN ('lobs', 'sample_selection', 'testing')
                ORDER BY permission_id
            """))
            existing_permissions = result.fetchall()
            logger.info(f"Existing permissions: {existing_permissions}")
            
            # Check if we already have the permissions we need
            existing_perms_set = {(row[1], row[2]) for row in existing_permissions}
            
            # Get the next available permission ID
            result = await db.execute(text("SELECT MAX(permission_id) FROM rbac_permissions"))
            max_id = result.scalar() or 0
            next_id = max_id + 1
            
            # Define permissions to add
            permissions_to_add = []
            
            if ('lobs', 'read') not in existing_perms_set:
                permissions_to_add.append({
                    'permission_id': next_id,
                    'resource': 'lobs',
                    'action': 'read',
                    'description': 'Read lines of business',
                    'created_at': datetime.utcnow()
                })
                next_id += 1
                
            if ('sample_selection', 'read') not in existing_perms_set:
                permissions_to_add.append({
                    'permission_id': next_id,
                    'resource': 'sample_selection',
                    'action': 'read',
                    'description': 'Read sample selection data',
                    'created_at': datetime.utcnow()
                })
                next_id += 1
                
            if ('testing', 'read') not in existing_perms_set:
                permissions_to_add.append({
                    'permission_id': next_id,
                    'resource': 'testing',
                    'action': 'read',
                    'description': 'Read testing data and execution results',
                    'created_at': datetime.utcnow()
                })
                next_id += 1
            
            # Insert new permissions
            for perm in permissions_to_add:
                await db.execute(text("""
                    INSERT INTO rbac_permissions (permission_id, resource, action, description, created_at)
                    VALUES (:permission_id, :resource, :action, :description, :created_at)
                """), perm)
                logger.info(f"Added permission: {perm['resource']}:{perm['action']}")
            
            # Get permission IDs for the permissions we care about
            result = await db.execute(text("""
                SELECT permission_id, resource, action 
                FROM rbac_permissions 
                WHERE (resource = 'lobs' AND action = 'read')
                   OR (resource = 'sample_selection' AND action = 'read')
                   OR (resource = 'testing' AND action = 'read')
            """))
            permission_map = {(row[1], row[2]): row[0] for row in result.fetchall()}
            
            # Check which role-permission mappings already exist
            existing_role_perms = set()
            for resource, action in [('lobs', 'read'), ('sample_selection', 'read'), ('testing', 'read')]:
                if (resource, action) in permission_map:
                    perm_id = permission_map[(resource, action)]
                    result = await db.execute(text("""
                        SELECT role_id FROM rbac_role_permissions WHERE permission_id = :perm_id
                    """), {'perm_id': perm_id})
                    for row in result.fetchall():
                        existing_role_perms.add((row[0], perm_id))
            
            logger.info(f"Existing role permissions: {existing_role_perms}")
            
            # Grant permissions to roles
            role_permissions_to_add = []
            
            # Tester (role_id = 1)
            for resource, action in [('lobs', 'read'), ('sample_selection', 'read'), ('testing', 'read')]:
                if (resource, action) in permission_map:
                    perm_id = permission_map[(resource, action)]
                    if (1, perm_id) not in existing_role_perms:
                        role_permissions_to_add.append({
                            'role_id': 1, 
                            'permission_id': perm_id, 
                            'created_at': datetime.utcnow()
                        })
            
            # Test Executive (role_id = 2)
            for resource, action in [('lobs', 'read'), ('sample_selection', 'read'), ('testing', 'read')]:
                if (resource, action) in permission_map:
                    perm_id = permission_map[(resource, action)]
                    if (2, perm_id) not in existing_role_perms:
                        role_permissions_to_add.append({
                            'role_id': 2, 
                            'permission_id': perm_id, 
                            'created_at': datetime.utcnow()
                        })
            
            # Report Owner (role_id = 5) 
            for resource, action in [('lobs', 'read'), ('sample_selection', 'read'), ('testing', 'read')]:
                if (resource, action) in permission_map:
                    perm_id = permission_map[(resource, action)]
                    if (5, perm_id) not in existing_role_perms:
                        role_permissions_to_add.append({
                            'role_id': 5, 
                            'permission_id': perm_id, 
                            'created_at': datetime.utcnow()
                        })
            
            # Data Executive (role_id = 4) - only needs lobs:read
            if ('lobs', 'read') in permission_map:
                perm_id = permission_map[('lobs', 'read')]
                if (4, perm_id) not in existing_role_perms:
                    role_permissions_to_add.append({
                        'role_id': 4, 
                        'permission_id': perm_id, 
                        'created_at': datetime.utcnow()
                    })
            
            # Insert role permissions
            for role_perm in role_permissions_to_add:
                await db.execute(text("""
                    INSERT INTO rbac_role_permissions (role_id, permission_id, created_at)
                    VALUES (:role_id, :permission_id, :created_at)
                """), role_perm)
                logger.info(f"Granted permission {role_perm['permission_id']} to role {role_perm['role_id']}")
            
            await db.commit()
            logger.info("Successfully fixed tester permissions!")
            
            # Verify the permissions were added
            result = await db.execute(text("""
                SELECT r.role_name, p.resource, p.action
                FROM rbac_role_permissions rp
                JOIN rbac_roles r ON r.role_id = rp.role_id
                JOIN rbac_permissions p ON p.permission_id = rp.permission_id
                WHERE r.role_name IN ('tester', 'test_executive', 'report_owner', 'data_executive')
                  AND p.resource IN ('lobs', 'sample_selection', 'testing')
                ORDER BY r.role_name, p.resource, p.action
            """))
            
            logger.info("\nCurrent permissions for roles:")
            for row in result.fetchall():
                logger.info(f"  {row[0]}: {row[1]}:{row[2]}")
                
        except Exception as e:
            logger.error(f"Error fixing permissions: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(fix_tester_permissions())