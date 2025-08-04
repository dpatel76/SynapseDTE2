#!/usr/bin/env python3
"""
Grant all required permissions to test_tester user for testing
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
    
    # Get user ID
    cur.execute("SELECT user_id FROM users WHERE email = 'test_tester@synapse.com'")
    user_id = cur.fetchone()[0]
    print(f'User ID: {user_id}')
    
    # Get all testing and observation related permissions
    cur.execute("""
        SELECT permission_id, resource, action 
        FROM rbac_permissions 
        WHERE resource IN ('testing', 'observation', 'testing_execution', 'observation_management')
           OR (resource = 'testing' AND action IN ('read', 'create', 'update'))
           OR (resource = 'observation' AND action IN ('read', 'create', 'update'))
    """)
    
    permissions = cur.fetchall()
    granted = 0
    
    for perm_id, resource, action in permissions:
        # Check if already granted
        cur.execute("""
            SELECT COUNT(*) FROM rbac_user_permissions 
            WHERE user_id = %s AND permission_id = %s
        """, (user_id, perm_id))
        
        if cur.fetchone()[0] == 0:
            # Grant permission
            cur.execute("""
                INSERT INTO rbac_user_permissions (user_id, permission_id, granted, granted_by, granted_at)
                VALUES (%s, %s, TRUE, 1, NOW())
            """, (user_id, perm_id))
            print(f'✅ Granted {resource}:{action} permission')
            granted += 1
        else:
            print(f'ℹ️  Already has {resource}:{action} permission')
    
    conn.commit()
    print(f'\n✅ Granted {granted} new permissions to test_tester@synapse.com')
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f'❌ Error: {e}')