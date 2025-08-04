#!/usr/bin/env python3
"""
Create all test users with proper passwords
"""

import psycopg2
import bcrypt

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

try:
    conn = psycopg2.connect(
        host='localhost',
        database='synapse_dt',
        user='synapse_user',
        password='synapse_password'
    )
    
    cur = conn.cursor()
    
    test_users = [
        ('Test', 'Manager', 'testmgr@synapse.com', 'Test Executive', 337),
        ('Test', 'Tester', 'tester@synapse.com', 'Tester', 337),
        ('Report', 'Owner', 'owner@synapse.com', 'Report Owner', 337),
        ('Executive', 'Owner', 'exec@synapse.com', 'Report Owner Executive', 337),
        ('Data', 'Provider', 'provider@synapse.com', 'Data Owner', 337),
        ('Chief', 'DataOfficer', 'cdo@synapse.com', 'Data Executive', None)
    ]
    
    password_hash = hash_password('TestUser123!')
    
    for first, last, email, role, lob_id in test_users:
        # Try to insert or update
        cur.execute("""
            INSERT INTO users (first_name, last_name, email, role, lob_id, hashed_password, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, TRUE)
            ON CONFLICT (email) DO UPDATE
            SET hashed_password = EXCLUDED.hashed_password,
                first_name = EXCLUDED.first_name,
                last_name = EXCLUDED.last_name,
                role = EXCLUDED.role,
                lob_id = EXCLUDED.lob_id
        """, (first, last, email, role, lob_id, password_hash))
        print(f'✅ Created/Updated user: {email} ({role})')
    
    conn.commit()
    cur.close()
    conn.close()
    
    print('✅ All test users created/updated successfully!')
    
except Exception as e:
    print(f'❌ Error: {e}')