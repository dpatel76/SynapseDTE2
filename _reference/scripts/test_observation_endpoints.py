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

# List all observation management endpoints we know work
endpoints_to_test = [
    ("GET", "/observation-enhanced/58/reports/156/observation-groups", "Observation Groups"),
    ("GET", "/observation-enhanced/58/reports/156/phase-status", "Phase Status"),
    ("GET", "/observation-enhanced/58/reports/156/observations", "Observations List"),
]

for method, endpoint, name in endpoints_to_test:
    print(f"\n=== Testing {name} ===")
    print(f"{method} {BASE_URL}{endpoint}")
    
    if method == "GET":
        response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Success")
        data = response.json()
        if isinstance(data, list):
            print(f"Found {len(data)} items")
        else:
            print(f"Response type: {type(data)}")
    else:
        print(f"❌ Failed: {response.text[:200]}")