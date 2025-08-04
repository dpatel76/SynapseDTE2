#!/usr/bin/env python3

import requests
import json

BASE_URL = "http://localhost:8001/api/v1"

# Login as tester
print("=== Login as tester ===")
login = requests.post(
    f"{BASE_URL}/auth/login",
    json={"email": "tester@example.com", "password": "password123"}
)

if login.status_code != 200:
    print(f"Login failed: {login.status_code}")
    exit(1)

token = login.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("✅ Login successful")

# Test a simple working endpoint first
print("\n=== Testing working endpoint ===")
response = requests.get(
    f"{BASE_URL}/users/me",
    headers=headers
)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    print("✅ /users/me works fine")

# Now test observation groups endpoint which should work
print("\n=== Testing observation groups endpoint ===")
response = requests.get(
    f"{BASE_URL}/observation-enhanced/58/reports/156/observation-groups",
    headers=headers
)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    print("✅ observation-groups works fine")
    print(f"Found {len(response.json())} groups")