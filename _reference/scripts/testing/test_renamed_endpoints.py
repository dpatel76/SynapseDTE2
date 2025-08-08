#!/usr/bin/env python3
"""
Test renamed endpoints
"""

import requests

BASE_URL = "http://localhost:8001/api/v1"

# Login
resp = requests.post(f"{BASE_URL}/auth/login", 
    json={"email": "tester@synapse.com", "password": "TestUser123!"})

if resp.status_code != 200:
    print(f"❌ Login failed: {resp.status_code}")
    exit(1)

token = resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("✅ Login successful")

# Test old and new endpoints
endpoints = [
    ("/testing-execution/9/reports/156/executions", "Old endpoint"),
    ("/test-execution/9/reports/156/executions", "New endpoint"),
]

for endpoint, desc in endpoints:
    resp = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
    icon = "✅" if resp.status_code == 200 else "❌"
    print(f"{icon} {desc}: {resp.status_code}")