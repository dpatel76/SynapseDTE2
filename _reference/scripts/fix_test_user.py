#!/usr/bin/env python
"""Fix test user password directly in database"""

import psycopg2
from passlib.context import CryptContext

# Database connection
conn = psycopg2.connect(
    host="localhost",
    database="synapse_dt",
    user="synapse_user",
    password="synapse_password"
)

# Password hasher
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Create hashed password
hashed_password = pwd_context.hash("password123")

try:
    with conn.cursor() as cur:
        # Update password for test user
        cur.execute(
            "UPDATE users SET hashed_password = %s WHERE email = %s",
            (hashed_password, "owner@synapse.com")
        )
        
        # Check if updated
        cur.execute("SELECT email, role, is_active FROM users WHERE email = %s", ("owner@synapse.com",))
        user = cur.fetchone()
        
        if user:
            print(f"Updated password for user: {user[0]}")
            print(f"Role: {user[1]}")
            print(f"Is Active: {user[2]}")
        else:
            print("User not found!")
        
        conn.commit()
        print("Password updated successfully!")
        
        # Verify password
        if pwd_context.verify("password123", hashed_password):
            print("Password verification test passed!")
        
except Exception as e:
    print(f"Error: {e}")
    conn.rollback()
finally:
    conn.close()