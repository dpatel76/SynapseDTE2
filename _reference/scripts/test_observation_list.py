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

# Test the observations list endpoint
cycle_id = 58
report_id = 156

print(f"\n=== Testing observations list endpoint ===")
print(f"GET {BASE_URL}/observation-enhanced/{cycle_id}/reports/{report_id}/observations")

response = requests.get(
    f"{BASE_URL}/observation-enhanced/{cycle_id}/reports/{report_id}/observations",
    headers=headers
)

print(f"\nStatus: {response.status_code}")
if response.status_code == 200:
    print("✅ Success!")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
else:
    print(f"❌ Failed!")
    print(f"Error: {response.text}")
    
    # Try to get more details
    if response.status_code == 500:
        print("\n=== Checking backend logs ===")
        import subprocess
        result = subprocess.run([
            "docker", "logs", "synapse-backend-container", "--tail", "20"
        ], capture_output=True, text=True)
        print(result.stdout)