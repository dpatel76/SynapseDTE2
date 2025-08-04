#!/usr/bin/env python3
import requests
import json

# Login first
login_url = "http://localhost:8001/api/v1/auth/login"
login_data = {
    "email": "john.doe@synapsedt.com",
    "password": "testpass123"
}

# Try common test user credentials
test_users = [
    {"email": "john.doe@synapsedt.com", "password": "testpass123"},
    {"email": "test@example.com", "password": "test123"},
    {"email": "admin@synapsedt.com", "password": "admin123"},
    {"email": "tester1@synapsedt.com", "password": "testpass123"}
]

token = None
for user in test_users:
    response = requests.post(login_url, json=user)
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"✅ Login successful with {user['email']}")
        break

if not token:
    print("❌ Could not login with any test user")
    exit(1)

# Test the cycle-reports endpoint
headers = {"Authorization": f"Bearer {token}"}
cycle_id = 9
report_id = 156

# Get cycle report details
url = f"http://localhost:8001/api/v1/cycle-reports/{cycle_id}/reports/{report_id}"
response = requests.get(url, headers=headers)

print(f"\n📋 Cycle Report Details (Status: {response.status_code}):")
if response.status_code == 200:
    data = response.json()
    print(json.dumps(data, indent=2))
    
    # Check specific fields
    print("\n🔍 Key Fields:")
    print(f"  - lob_name: {data.get('lob_name', 'NOT FOUND')}")
    print(f"  - tester_name: {data.get('tester_name', 'NOT FOUND')}")
    print(f"  - report_owner_name: {data.get('report_owner_name', 'NOT FOUND')}")
    print(f"  - report_name: {data.get('report_name', 'NOT FOUND')}")
else:
    print(f"Error: {response.status_code}")
    print(response.text)