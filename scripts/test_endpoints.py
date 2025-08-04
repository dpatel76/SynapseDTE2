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

# Test simple endpoint
print("\n=== Testing simple endpoint ===")
response = requests.get(
    f"{BASE_URL}/observation-enhanced/test-simple",
    headers=headers
)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    print(f"Response: {response.json()}")

# Test db endpoint
print("\n=== Testing db endpoint ===")
response = requests.get(
    f"{BASE_URL}/observation-enhanced/test-db",
    headers=headers
)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    print(f"Response: {response.json()}")

# Test original endpoint
print("\n=== Testing observations list endpoint ===")
response = requests.get(
    f"{BASE_URL}/observation-enhanced/58/reports/156/observations",
    headers=headers
)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    print(f"Response: {response.json()}")
else:
    print(f"Error: {response.text}")