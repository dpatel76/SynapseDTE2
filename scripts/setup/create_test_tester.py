#!/usr/bin/env python3
"""
Create a test tester user with known credentials
"""

import psycopg2
from passlib.context import CryptContext

# Password hashing
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

try:
    # Database connection
    conn = psycopg2.connect(
        host='localhost',
        database='synapse_dt',
        user='synapse_user',
        password='synapse_password'
    )
    
    cur = conn.cursor()
    
    # Delete existing test tester if exists
    cur.execute("DELETE FROM users WHERE email = 'test_tester@synapse.com'")
    
    # Create new test tester
    password_hash = pwd_context.hash('TestUser123!')
    
    cur.execute(
        '''INSERT INTO users (first_name, last_name, email, role, lob_id, hashed_password, is_active) 
           VALUES (%s, %s, %s, %s, %s, %s, %s)''',
        ('Test', 'Tester', 'test_tester@synapse.com', 'Tester', 337, password_hash, True)
    )
    
    conn.commit()
    print('✅ Created test tester user: test_tester@synapse.com with password TestUser123!')
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f'❌ Error: {e}')