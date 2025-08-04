#!/usr/bin/env python3
"""Grant observation management permissions to testers"""

import psycopg2
from psycopg2.extras import RealDictCursor

def grant_permissions():
    """Grant observation:read permission to Tester role"""
    conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/synapse_dt")
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Check if permission exists
            cur.execute("""
                SELECT * FROM rbac_permissions WHERE resource = 'observations' AND action = 'read'
            """)
            permission = cur.fetchone()
            
            if not permission:
                # Create the permission
                cur.execute("""
                    INSERT INTO rbac_permissions (resource, action, description) 
                    VALUES ('observations', 'read', 'Read observation management data')
                    RETURNING permission_id
                """)
                permission_id = cur.fetchone()['permission_id']
                print(f"✅ Created permission 'observations:read' with ID {permission_id}")
            else:
                permission_id = permission['permission_id']
                print(f"✅ Permission 'observations:read' already exists with ID {permission_id}")
            
            # Get Tester role ID
            cur.execute("SELECT role_id FROM rbac_roles WHERE role_name = 'Tester'")
            tester_role = cur.fetchone()
            
            if tester_role:
                # Check if permission already granted
                cur.execute("""
                    SELECT * FROM rbac_role_permissions 
                    WHERE role_id = %s AND permission_id = %s
                """, (tester_role['role_id'], permission_id))
                
                existing = cur.fetchone()
                
                if not existing:
                    # Grant permission to Tester role
                    cur.execute("""
                        INSERT INTO rbac_role_permissions (role_id, permission_id)
                        VALUES (%s, %s)
                    """, (tester_role['role_id'], permission_id))
                    print(f"✅ Granted 'observation:read' permission to Tester role")
                else:
                    print("✅ Tester role already has 'observation:read' permission")
            else:
                print("❌ Tester role not found")
            
            # Also grant to Report Owner role
            cur.execute("SELECT role_id FROM rbac_roles WHERE role_name = 'Report Owner'")
            report_owner_role = cur.fetchone()
            
            if report_owner_role:
                # Check if permission already granted
                cur.execute("""
                    SELECT * FROM rbac_role_permissions 
                    WHERE role_id = %s AND permission_id = %s
                """, (report_owner_role['role_id'], permission_id))
                
                existing = cur.fetchone()
                
                if not existing:
                    # Grant permission to Report Owner role
                    cur.execute("""
                        INSERT INTO rbac_role_permissions (role_id, permission_id)
                        VALUES (%s, %s)
                    """, (report_owner_role['role_id'], permission_id))
                    print(f"✅ Granted 'observation:read' permission to Report Owner role")
                else:
                    print("✅ Report Owner role already has 'observation:read' permission")
            
            conn.commit()
            print("\n✅ All permissions granted successfully!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("Granting observation management permissions...")
    grant_permissions()