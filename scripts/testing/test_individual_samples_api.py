#!/usr/bin/env python3
"""
Test the individual samples API endpoints
"""

import requests
import json

# Base URL
BASE_URL = "http://localhost:8001/api/v1"

# Login credentials
login_data = {
    "email": "tester@synapse.com",
    "password": "TestUser123!"
}

# Login to get token
print("Logging in...")
login_response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
if login_response.status_code != 200:
    print(f"Login failed: {login_response.status_code}")
    print(login_response.text)
    exit(1)

token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("✅ Login successful")

# Test cycle and report IDs
cycle_id = 13
report_id = 156

# Test 1: Get samples
print(f"\nTest 1: Getting samples for cycle {cycle_id}, report {report_id}")
response = requests.get(
    f"{BASE_URL}/sample-selection/cycles/{cycle_id}/reports/{report_id}/samples",
    headers=headers
)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"✅ Success! Found {len(data.get('samples', []))} samples")
    print(json.dumps(data, indent=2)[:500] + "...")
else:
    print(f"❌ Error: {response.text}")

# Test 2: Generate samples
print(f"\nTest 2: Generating samples")
generate_data = {
    "sample_size": 5,
    "sample_type": "Population Sample",
    "regulatory_context": "General Regulatory Compliance",
    "scoped_attributes": [
        {
            "attribute_name": "Account ID",
            "is_primary_key": True,
            "data_type": "String",
            "mandatory_flag": True
        },
        {
            "attribute_name": "Account Balance",
            "is_primary_key": False,
            "data_type": "Decimal",
            "mandatory_flag": True
        }
    ]
}
response = requests.post(
    f"{BASE_URL}/sample-selection/cycles/{cycle_id}/reports/{report_id}/samples/generate",
    headers=headers,
    json=generate_data
)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"✅ Success! Generated {data.get('samples_generated', 0)} samples")
else:
    print(f"❌ Error: {response.text}")

# Test 3: Get samples again to see the new ones
print(f"\nTest 3: Getting samples again")
response = requests.get(
    f"{BASE_URL}/sample-selection/cycles/{cycle_id}/reports/{report_id}/samples",
    headers=headers
)
if response.status_code == 200:
    data = response.json()
    print(f"✅ Success! Now have {len(data.get('samples', []))} samples")
    if data.get('samples'):
        print("\nFirst sample:")
        print(json.dumps(data['samples'][0], indent=2))