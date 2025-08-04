#!/usr/bin/env python3
"""
Script to create test users for all 6 roles in SynapseDT system
"""

import psycopg2
from passlib.context import CryptContext

# Password hashing
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

def create_test_users():
    """Create test users for all roles"""
    try:
        # Database connection
        conn = psycopg2.connect(
            host='localhost',
            database='synapse_dt',
            user='synapse_user',
            password='synapse_password'
        )
        
        print('✅ Creating test users for all roles...')
        cur = conn.cursor()
        
        test_users = [
            ('Test', 'Manager', 'testmgr@synapse.com', 'Test Executive', 1),
            ('Test', 'Tester', 'tester@synapse.com', 'Tester', 1),
            ('Report', 'Owner', 'owner@synapse.com', 'Report Owner', 1),
            ('Executive', 'Owner', 'exec@synapse.com', 'Report Owner Executive', 1),
            ('Data', 'Provider', 'provider@synapse.com', 'Data Owner', 1),
            ('Chief', 'DataOfficer', 'cdo@synapse.com', 'Data Executive', None)
        ]
        
        password_hash = pwd_context.hash('TestUser123!')
        
        for first, last, email, role, lob_id in test_users:
            try:
                cur.execute(
                    '''INSERT INTO users (first_name, last_name, email, role, lob_id, hashed_password, is_active) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s)''',
                    (first, last, email, role, lob_id, password_hash, True)
                )
                print(f'  ✅ Created user: {email} ({role})')
            except psycopg2.IntegrityError:
                print(f'  ℹ️  User already exists: {email}')
                conn.rollback()
                continue
        
        conn.commit()
        cur.close()
        conn.close()
        print('✅ Test user creation completed!')
        
    except Exception as e:
        print(f'❌ Error creating test users: {str(e)}')

if __name__ == "__main__":
    create_test_users() 