#!/usr/bin/env python3
"""
Start observation phase for testing
"""

import requests
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8001/api/v1"

# Login as test manager
resp = requests.post(f"{BASE_URL}/auth/login", 
    json={"email": "testmgr@synapse.com", "password": "TestUser123!"})

if resp.status_code != 200:
    print(f"❌ Login failed: {resp.status_code}")
    exit(1)

token = resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("✅ Login successful")

# Start observation phase
data = {
    "observation_deadline": (datetime.utcnow() + timedelta(days=7)).isoformat(),
    "instructions": "Review test results and create observations"
}

resp = requests.post(
    f"{BASE_URL}/observation-management/9/reports/156/start",
    headers=headers,
    json=data
)

if resp.status_code == 200:
    print("✅ Observation phase started successfully")
else:
    print(f"❌ Failed to start phase: {resp.status_code}")
    print(f"   Response: {resp.text}")