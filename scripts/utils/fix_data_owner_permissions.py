#!/usr/bin/env python3
"""Fix data owner permissions for tester role."""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

try:
    # Check if data_owner:read permission exists
    cur.execute("SELECT permission_id FROM rbac_permissions WHERE resource = 'data_owner' AND action = 'read'")
    permission = cur.fetchone()
    
    if not permission:
        # Create the permission
        cur.execute("""
            INSERT INTO rbac_permissions (resource, action, description, created_at, updated_at)
            VALUES ('data_owner', 'read', 'Read data owner/provider information', NOW(), NOW())
            RETURNING permission_id
        """)
        permission_id = cur.fetchone()[0]
        print(f"Created data_owner:read permission with ID: {permission_id}")
    else:
        permission_id = permission[0]
        print(f"Found existing data_owner:read permission with ID: {permission_id}")
    
    # Grant permission to Tester role (role_id=1)
    cur.execute("""
        INSERT INTO rbac_role_permissions (role_id, permission_id)
        VALUES (1, %s)
        ON CONFLICT (role_id, permission_id) DO NOTHING
    """, (permission_id,))
    
    # Also grant to Test Executive (role_id=2) and Report Owner (role_id=5)
    for role_id in [2, 5]:
        cur.execute("""
            INSERT INTO rbac_role_permissions (role_id, permission_id)
            VALUES (%s, %s)
            ON CONFLICT (role_id, permission_id) DO NOTHING
        """, (role_id, permission_id))
    
    # Check if data_owner:execute permission exists for assignment matrix
    cur.execute("SELECT permission_id FROM rbac_permissions WHERE resource = 'data_owner' AND action = 'execute'")
    execute_permission = cur.fetchone()
    
    if not execute_permission:
        cur.execute("""
            INSERT INTO rbac_permissions (resource, action, description, created_at, updated_at)
            VALUES ('data_owner', 'execute', 'Execute data owner operations', NOW(), NOW())
            RETURNING permission_id
        """)
        execute_permission_id = cur.fetchone()[0]
        print(f"Created data_owner:execute permission with ID: {execute_permission_id}")
    else:
        execute_permission_id = execute_permission[0]
        print(f"Found existing data_owner:execute permission with ID: {execute_permission_id}")
    
    # Grant execute permission to Test Executive only
    cur.execute("""
        INSERT INTO rbac_role_permissions (role_id, permission_id)
        VALUES (2, %s)
        ON CONFLICT (role_id, permission_id) DO NOTHING
    """, (execute_permission_id,))
    
    conn.commit()
    print("\nPermissions updated successfully!")
    
    # Show current permissions for Tester role
    cur.execute("""
        SELECT p.resource || ':' || p.action as permission_name
        FROM rbac_permissions p
        JOIN rbac_role_permissions rp ON p.permission_id = rp.permission_id
        WHERE rp.role_id = 1
        ORDER BY p.resource, p.action
    """)
    
    print("\nCurrent Tester permissions:")
    for row in cur.fetchall():
        print(f"  - {row[0]}")
        
except Exception as e:
    print(f"Error: {e}")
    conn.rollback()
finally:
    cur.close()
    conn.close()