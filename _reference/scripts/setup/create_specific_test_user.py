#!/usr/bin/env python3
"""
Script to create a specific test user: tester@example.com with password123
"""

import psycopg2
from passlib.context import CryptContext

# Password hashing
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

def create_test_user():
    """Create specific test user"""
    try:
        # Database connection
        conn = psycopg2.connect(
            host='localhost',
            database='synapse_dt',
            user='synapse_user',
            password='synapse_password'
        )
        
        print('✅ Creating test user tester@example.com...')
        cur = conn.cursor()
        
        # Hash the password
        password_hash = pwd_context.hash('password123')
        
        # First check if user exists
        cur.execute("SELECT id FROM users WHERE email = %s", ('tester@example.com',))
        existing = cur.fetchone()
        
        if existing:
            # Update existing user
            cur.execute(
                '''UPDATE users 
                   SET hashed_password = %s, is_active = true
                   WHERE email = %s''',
                (password_hash, 'tester@example.com')
            )
            print('  ✅ Updated existing user: tester@example.com')
        else:
            # Create new user
            cur.execute(
                '''INSERT INTO users (first_name, last_name, email, role, lob_id, hashed_password, is_active) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s)''',
                ('Test', 'User', 'tester@example.com', 'Tester', 1, password_hash, True)
            )
            print('  ✅ Created new user: tester@example.com')
        
        conn.commit()
        cur.close()
        conn.close()
        print('✅ Test user creation completed!')
        print('   Email: tester@example.com')
        print('   Password: password123')
        print('   Role: Tester')
        
    except Exception as e:
        print(f'❌ Error creating test user: {str(e)}')

if __name__ == "__main__":
    create_test_user()