#!/usr/bin/env python3
"""
Create observation permissions and assign to appropriate roles
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
    
    # Create observations:read permission if it doesn't exist
    cur.execute("""
        INSERT INTO permissions (resource, action, description, created_at, updated_at)
        VALUES ('observations', 'read', 'View observations and observation reports', NOW(), NOW())
        ON CONFLICT (resource, action) DO NOTHING
        RETURNING permission_id
    """)
    
    result = cur.fetchone()
    if result:
        perm_id = result[0]
        print(f'✅ Created observations:read permission (ID: {perm_id})')
        
        # Get role IDs
        cur.execute("SELECT role_id, role_name FROM roles WHERE role_name IN ('Tester', 'Test Executive', 'Report Owner', 'Report Owner Executive', 'Admin')")
        roles = cur.fetchall()
        
        # Assign permission to roles
        for role_id, role_name in roles:
            cur.execute("""
                INSERT INTO role_permissions (role_id, permission_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
            """, (role_id, perm_id))
            print(f'  ✅ Granted to {role_name} role')
        
        # Also grant directly to our test user
        cur.execute("SELECT user_id FROM users WHERE email = 'test_tester@synapse.com'")
        user_result = cur.fetchone()
        if user_result:
            user_id = user_result[0]
            cur.execute("""
                INSERT INTO user_permissions (user_id, permission_id, granted, granted_by, granted_at)
                VALUES (%s, %s, TRUE, 1, NOW())
                ON CONFLICT DO NOTHING
            """, (user_id, perm_id))
            print(f'  ✅ Granted to test_tester@synapse.com')
    else:
        print('ℹ️  observations:read permission already exists')
    
    conn.commit()
    cur.close()
    conn.close()
    
except Exception as e:
    print(f'❌ Error: {e}')