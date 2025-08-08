#!/usr/bin/env python3
"""
Debug authentication and permission issues
"""

import requests
import jwt

BASE_URL = "http://localhost:8001/api/v1"

# Login as tester
print("1. Logging in as tester...")
resp = requests.post(f"{BASE_URL}/auth/login", 
    json={"email": "tester@synapse.com", "password": "TestUser123!"})

if resp.status_code != 200:
    print(f"   ❌ Login failed: {resp.status_code}")
    print(f"   Response: {resp.text}")
    exit(1)

auth_data = resp.json()
token = auth_data["access_token"]
print(f"   ✅ Login successful")
print(f"   Token (first 50 chars): {token[:50]}...")

# Decode token (without verification) to see contents
try:
    payload = jwt.decode(token, options={"verify_signature": False})
    print(f"   Token payload: {payload}")
except Exception as e:
    print(f"   ❌ Failed to decode token: {e}")

# Test basic endpoint
print("\n2. Testing /auth/me endpoint...")
headers = {"Authorization": f"Bearer {token}"}
resp = requests.get(f"{BASE_URL}/auth/me", headers=headers)
print(f"   Status: {resp.status_code}")
if resp.status_code == 200:
    user_data = resp.json()
    print(f"   User: {user_data.get('email')} (ID: {user_data.get('user_id')})")
    print(f"   Role: {user_data.get('role')}")
else:
    print(f"   Response: {resp.text}")

# Test cycles endpoint
print("\n3. Testing /cycles/9 endpoint...")
resp = requests.get(f"{BASE_URL}/cycles/9", headers=headers)
print(f"   Status: {resp.status_code}")
if resp.status_code != 200:
    print(f"   Response: {resp.text}")

# Test permission check endpoint directly
print("\n4. Checking permissions in database...")
import psycopg2
try:
    conn = psycopg2.connect(
        host='localhost',
        database='synapse_dt',
        user='synapse_user',
        password='synapse_password'
    )
    cur = conn.cursor()
    
    # Get user ID
    cur.execute("SELECT user_id, role FROM users WHERE email = 'tester@synapse.com'")
    user_id, role = cur.fetchone()
    print(f"   User ID: {user_id}, Role: {role}")
    
    # Check permissions
    cur.execute("""
        SELECT p.resource, p.action 
        FROM rbac_permissions p 
        JOIN rbac_role_permissions rp ON p.permission_id = rp.permission_id 
        JOIN rbac_roles r ON rp.role_id = r.role_id 
        WHERE r.role_name = 'Tester' 
        AND p.resource = 'cycles' 
        AND p.action = 'read'
    """)
    result = cur.fetchone()
    if result:
        print(f"   ✅ Tester has cycles:read permission")
    else:
        print(f"   ❌ Tester does NOT have cycles:read permission")
    
    cur.close()
    conn.close()
except Exception as e:
    print(f"   ❌ Database error: {e}")