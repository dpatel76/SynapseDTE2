#!/usr/bin/env python3
"""
Grant data_owner:read permission to Tester role
This allows testers to view data owner phase information
"""

import asyncio
import sys
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://synapse_user:synapse_password@localhost:5432/synapse_dt")
# Convert to sync URL if needed
if DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

def grant_permission():
    """Grant data_owner:read permission to Tester role"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        trans = conn.begin()
        
        try:
            # Get Tester role ID
            result = conn.execute(
                text("SELECT role_id FROM rbac_roles WHERE role_name = 'Tester'")
            )
            role = result.fetchone()
            if not role:
                print("❌ Tester role not found")
                trans.rollback()
                return
            tester_role_id = role[0]
            
            # Check if data_owner:read permission exists
            result = conn.execute(
                text("""
                    SELECT permission_id FROM rbac_permissions 
                    WHERE resource = 'data_owner' AND action = 'read'
                """)
            )
            permission = result.fetchone()
            
            if not permission:
                # Create the permission
                result = conn.execute(
                    text("""
                        INSERT INTO rbac_permissions (resource, action, description)
                        VALUES ('data_owner', 'read', 'View data owner phase information')
                        RETURNING permission_id
                    """)
                )
                data_owner_read_id = result.fetchone()[0]
                print("✅ Created data_owner:read permission")
            else:
                data_owner_read_id = permission[0]
            
            # Check if tester already has this permission
            result = conn.execute(
                text("""
                    SELECT 1 FROM rbac_role_permissions 
                    WHERE role_id = :role_id AND permission_id = :permission_id
                """),
                {"role_id": tester_role_id, "permission_id": data_owner_read_id}
            )
            
            if not result.fetchone():
                # Grant the permission
                conn.execute(
                    text("""
                        INSERT INTO rbac_role_permissions (role_id, permission_id)
                        VALUES (:role_id, :permission_id)
                    """),
                    {"role_id": tester_role_id, "permission_id": data_owner_read_id}
                )
                print("✅ Granted data_owner:read permission to Tester role")
            else:
                print("✅ Tester role already has data_owner:read permission")
            
            # Also check request_info:read
            result = conn.execute(
                text("""
                    SELECT permission_id FROM rbac_permissions 
                    WHERE resource = 'request_info' AND action = 'read'
                """)
            )
            permission = result.fetchone()
            
            if not permission:
                # Create the permission
                result = conn.execute(
                    text("""
                        INSERT INTO rbac_permissions (resource, action, description)
                        VALUES ('request_info', 'read', 'View request for information phase')
                        RETURNING permission_id
                    """)
                )
                request_info_read_id = result.fetchone()[0]
                print("✅ Created request_info:read permission")
            else:
                request_info_read_id = permission[0]
            
            # Check if tester already has this permission
            result = conn.execute(
                text("""
                    SELECT 1 FROM rbac_role_permissions 
                    WHERE role_id = :role_id AND permission_id = :permission_id
                """),
                {"role_id": tester_role_id, "permission_id": request_info_read_id}
            )
            
            if not result.fetchone():
                # Grant the permission
                conn.execute(
                    text("""
                        INSERT INTO rbac_role_permissions (role_id, permission_id)
                        VALUES (:role_id, :permission_id)
                    """),
                    {"role_id": tester_role_id, "permission_id": request_info_read_id}
                )
                print("✅ Granted request_info:read permission to Tester role")
            else:
                print("✅ Tester role already has request_info:read permission")
            
            trans.commit()
            print("\n✅ Permissions granted successfully!")
            
        except Exception as e:
            trans.rollback()
            print(f"❌ Error granting permissions: {e}")
            raise

if __name__ == "__main__":
    print("Granting data_owner:read permission to Tester role...")
    grant_permission()