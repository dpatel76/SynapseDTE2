#!/usr/bin/env python3
"""
Grant testing:read permission to test_tester user
"""

import psycopg2

try:
    # Database connection
    conn = psycopg2.connect(
        host='localhost',
        database='synapse_dt',
        user='synapse_user',
        password='synapse_password'
    )
    
    cur = conn.cursor()
    
    # Get user ID and permission ID
    cur.execute("SELECT user_id FROM users WHERE email = 'test_tester@synapse.com'")
    user_id = cur.fetchone()[0]
    print(f'User ID: {user_id}')
    
    cur.execute("SELECT permission_id FROM rbac_permissions WHERE resource = 'testing' AND action = 'read'")
    permission_id = cur.fetchone()[0]
    print(f'Permission ID: {permission_id}')
    
    # Check if user permission already exists
    cur.execute("""
        SELECT COUNT(*) FROM rbac_user_permissions 
        WHERE user_id = %s AND permission_id = %s
    """, (user_id, permission_id))
    
    if cur.fetchone()[0] == 0:
        # Grant permission
        cur.execute("""
            INSERT INTO rbac_user_permissions (user_id, permission_id, granted, granted_by, granted_at)
            VALUES (%s, %s, TRUE, 1, NOW())
        """, (user_id, permission_id))
        print('✅ Granted testing:read permission to test_tester@synapse.com')
    else:
        print('ℹ️  User already has testing:read permission')
    
    # Also grant observation:read permission
    cur.execute("SELECT permission_id FROM rbac_permissions WHERE resource = 'observation' AND action = 'read'")
    obs_permission = cur.fetchone()
    if obs_permission:
        obs_permission_id = obs_permission[0]
        cur.execute("""
            SELECT COUNT(*) FROM rbac_user_permissions 
            WHERE user_id = %s AND permission_id = %s
        """, (user_id, obs_permission_id))
        
        if cur.fetchone()[0] == 0:
            cur.execute("""
                INSERT INTO rbac_user_permissions (user_id, permission_id, granted, granted_by, granted_at)
                VALUES (%s, %s, TRUE, 1, NOW())
            """, (user_id, obs_permission_id))
            print('✅ Granted observation:read permission to test_tester@synapse.com')
    
    conn.commit()
    cur.close()
    conn.close()
    
except Exception as e:
    print(f'❌ Error: {e}')