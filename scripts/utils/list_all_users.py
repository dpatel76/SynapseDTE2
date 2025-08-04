#!/usr/bin/env python3
"""List all users in the system"""

import psycopg2
from psycopg2.extras import RealDictCursor

def list_users():
    conn = psycopg2.connect(
        host="localhost",
        database="synapse_dt",
        user="postgres",
        password="postgres"
    )
    
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get all users with their roles
    cur.execute("""
        SELECT 
            u.user_id,
            u.email,
            u.first_name,
            u.last_name,
            u.is_active,
            r.role_name
        FROM users u
        LEFT JOIN rbac_user_roles ur ON u.user_id = ur.user_id
        LEFT JOIN rbac_roles r ON ur.role_id = r.role_id
        ORDER BY u.user_id
    """)
    
    users = cur.fetchall()
    
    print("\nAll Users in System:")
    print("="*80)
    for user in users:
        status = "Active" if user['is_active'] else "Inactive"
        print(f"{user['user_id']:3d} | {user['email']:30s} | {user['first_name']:10s} {user['last_name']:10s} | {user['role_name']:20s} | {status}")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    list_users()