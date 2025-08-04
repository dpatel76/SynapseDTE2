#!/usr/bin/env python3
"""Generate bcrypt hash for test password"""

from passlib.context import CryptContext

# Create the same context as used in the app
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Generate hash for the test password
password = "password123"
hashed = pwd_context.hash(password)

print(f"Password: {password}")
print(f"Bcrypt hash: {hashed}")
print(f"\nSQL Update:")
print(f"UPDATE users SET hashed_password = '{hashed}' WHERE email = 'tester@example.com';")