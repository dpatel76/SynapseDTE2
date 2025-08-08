#!/usr/bin/env python3
"""
Grant missing permissions to roles for RBAC to work properly
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
    
    # First check if test-cycles permissions exist
    cur.execute("SELECT permission_id FROM rbac_permissions WHERE resource = 'test-cycles' AND action = 'read'")
    result = cur.fetchone()
    
    if not result:
        # Create test-cycles permissions
        cur.execute("""
            INSERT INTO rbac_permissions (resource, action, description, created_at, updated_at)
            VALUES ('test-cycles', 'read', 'View test cycles', NOW(), NOW())
            RETURNING permission_id
        """)
        test_cycles_read_id = cur.fetchone()[0]
        print('✅ Created test-cycles:read permission')
    else:
        test_cycles_read_id = result[0]
    
    # Grant test-cycles:read to all roles
    cur.execute("""
        INSERT INTO rbac_role_permissions (role_id, permission_id, granted_at)
        SELECT r.role_id, %s, NOW()
        FROM rbac_roles r
        WHERE NOT EXISTS (
            SELECT 1 FROM rbac_role_permissions rp 
            WHERE rp.role_id = r.role_id AND rp.permission_id = %s
        )
    """, (test_cycles_read_id, test_cycles_read_id))
    
    print(f'✅ Granted test-cycles:read permission to all roles')
    
    # Check and create analytics permissions for executives
    cur.execute("SELECT permission_id FROM rbac_permissions WHERE resource = 'analytics' AND action = 'read'")
    result = cur.fetchone()
    
    if not result:
        cur.execute("""
            INSERT INTO rbac_permissions (resource, action, description, created_at, updated_at)
            VALUES ('analytics', 'read', 'View analytics dashboard', NOW(), NOW())
            RETURNING permission_id
        """)
        analytics_read_id = cur.fetchone()[0]
        print('✅ Created analytics:read permission')
    else:
        analytics_read_id = result[0]
    
    # Grant analytics:read to executives and test managers
    cur.execute("""
        INSERT INTO rbac_role_permissions (role_id, permission_id, granted_at)
        SELECT r.role_id, %s, NOW()
        FROM rbac_roles r
        WHERE r.role_name IN ('Report Owner Executive', 'Test Executive')
        AND NOT EXISTS (
            SELECT 1 FROM rbac_role_permissions rp 
            WHERE rp.role_id = r.role_id AND rp.permission_id = %s
        )
    """, (analytics_read_id, analytics_read_id))
    
    print('✅ Granted analytics:read permission to executives and test managers')
    
    conn.commit()
    cur.close()
    conn.close()
    
except Exception as e:
    print(f'❌ Error: {e}')