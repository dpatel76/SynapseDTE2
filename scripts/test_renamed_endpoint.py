#!/usr/bin/env python3

import requests
import json
import time

BASE_URL = "http://localhost:8001/api/v1"

time.sleep(10)

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

# Test the renamed endpoint
print("\n=== Testing renamed observations-list endpoint ===")
response = requests.get(
    f"{BASE_URL}/observation-enhanced/58/reports/156/observations-list",
    headers=headers
)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    print("✅ Success!")
    data = response.json()
    print(f"Found {len(data)} observations")
else:
    print(f"❌ Failed: {response.text}")

# Test the original endpoint (should be 404 now)
print("\n=== Testing original observations endpoint (should be 404) ===")
response = requests.get(
    f"{BASE_URL}/observation-enhanced/58/reports/156/observations",
    headers=headers
)
print(f"Status: {response.status_code}")
if response.status_code == 404:
    print("✅ Correctly returns 404")