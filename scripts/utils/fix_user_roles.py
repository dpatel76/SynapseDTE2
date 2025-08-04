#!/usr/bin/env python3
"""
Fix user role mappings for test users
"""

import psycopg2

try:
    conn = psycopg2.connect(
        host='localhost',
        database='synapse_dt',
        user='synapse_user',
        password='synapse_password'
    )
    
    cur = conn.cursor()
    
    # Get test users and their roles
    cur.execute("""
        SELECT u.user_id, u.email, u.role::text, r.role_id 
        FROM users u
        JOIN rbac_roles r ON u.role::text = r.role_name
        WHERE u.email IN ('tester@synapse.com', 'testmgr@synapse.com', 'owner@synapse.com', 
                         'exec@synapse.com', 'provider@synapse.com', 'cdo@synapse.com')
    """)
    
    users = cur.fetchall()
    
    for user_id, email, role_name, role_id in users:
        # Check if mapping exists
        cur.execute("""
            SELECT 1 FROM rbac_user_roles WHERE user_id = %s AND role_id = %s
        """, (user_id, role_id))
        
        if not cur.fetchone():
            # Add mapping
            cur.execute("""
                INSERT INTO rbac_user_roles (user_id, role_id, assigned_by, assigned_at)
                VALUES (%s, %s, 1, NOW())
            """, (user_id, role_id))
            print(f'✅ Added role mapping for {email} -> {role_name}')
        else:
            print(f'ℹ️  Role mapping already exists for {email}')
    
    conn.commit()
    cur.close()
    conn.close()
    
    print('✅ User role mappings fixed!')
    
except Exception as e:
    print(f'❌ Error: {e}')