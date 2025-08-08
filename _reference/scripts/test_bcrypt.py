#!/usr/bin/env python3
"""Test bcrypt password verification"""

import bcrypt
import time

# The password and hash we're using
password = "password123"
hash_from_db = "$2b$12$D/8avO4TQoqLTPI5jVzooOHlgQgaVHdm4pGp303CkmjXcn/vMQpie"

print("Testing bcrypt password verification...")
print(f"Password: {password}")
print(f"Hash: {hash_from_db}")

# Test 1: Direct bcrypt verification
start = time.time()
result = bcrypt.checkpw(password.encode('utf-8'), hash_from_db.encode('utf-8'))
end = time.time()

print(f"\nDirect bcrypt verification:")
print(f"Result: {result}")
print(f"Time: {end - start:.2f} seconds")

# Test 2: Using passlib (what the app uses)
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

start = time.time()
result2 = pwd_context.verify(password, hash_from_db)
end = time.time()

print(f"\nPasslib verification:")
print(f"Result: {result2}")
print(f"Time: {end - start:.2f} seconds")

# Test 3: Generate a new hash
start = time.time()
new_hash = pwd_context.hash(password)
end = time.time()

print(f"\nNew hash generation:")
print(f"New hash: {new_hash}")
print(f"Time: {end - start:.2f} seconds")

# Verify the new hash
start = time.time()
result3 = pwd_context.verify(password, new_hash)
end = time.time()

print(f"\nVerify new hash:")
print(f"Result: {result3}")
print(f"Time: {end - start:.2f} seconds")