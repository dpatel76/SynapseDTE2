#!/usr/bin/env python3
"""
Verify test user passwords
"""

from passlib.context import CryptContext
from sqlalchemy import create_engine, text
import os

# Password hashing context
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

# Get database URL
db_url = os.getenv('DATABASE_URL', 'postgresql://synapse_user:securepassword123@localhost:5432/synapse_dt')
if 'asyncpg' in db_url:
    db_url = db_url.replace('postgresql+asyncpg', 'postgresql')

engine = create_engine(db_url)

# Common test passwords to try
test_passwords = [
    'password123',
    'Password123!',
    'TestUser123!',
    'Adminpass1!',
    'admin123',
    'test123',
    'password',
    'admin'
]

print("Checking passwords for test users...")
print("=" * 50)

with engine.connect() as conn:
    # Get all test users
    result = conn.execute(text("""
        SELECT email, hashed_password, role 
        FROM users 
        WHERE email LIKE '%@example.com'
        ORDER BY email
    """))
    
    users = result.fetchall()
    
    for email, hashed_password, role in users:
        print(f"\nUser: {email} (Role: {role})")
        found = False
        
        for password in test_passwords:
            if pwd_context.verify(password, hashed_password):
                print(f"  ✅ Password is: {password}")
                found = True
                break
        
        if not found:
            print("  ❌ None of the common passwords match")
            # Try some variations
            username = email.split('@')[0]
            variations = [
                username,
                username + '123',
                username.capitalize() + '123',
                username.replace('.', '') + '123'
            ]
            
            for password in variations:
                if pwd_context.verify(password, hashed_password):
                    print(f"  ✅ Password is: {password}")
                    found = True
                    break
            
            if not found:
                print("  ❌ Could not determine password")