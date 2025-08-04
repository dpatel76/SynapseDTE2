#!/usr/bin/env python3
"""Debug sample generation to find where fallback samples come from"""

import requests
import json

# Base URL
BASE_URL = "http://localhost:8001/api/v1"

# Login
print("1. Logging in...")
login_response = requests.post(f"{BASE_URL}/auth/login", json={
    "email": "tester@synapse.com",
    "password": "TestUser123!"
})
token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Check scoped attributes
print("\n2. Checking scoped attributes...")
response = requests.get(
    f"{BASE_URL}/scoping/cycles/13/reports/156/attributes",
    headers=headers
)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    attributes = response.json()
    scoped = [attr for attr in attributes if attr.get('is_scoped') or attr.get('include_in_testing')]
    print(f"Total attributes: {len(attributes)}")
    print(f"Scoped attributes: {len(scoped)}")
    if scoped:
        print("Scoped attribute names:", [attr['attribute_name'] for attr in scoped[:5]])

# Generate with explicit attributes
print("\n3. Generating samples WITH scoped attributes...")
generate_data = {
    "sample_size": 1,
    "sample_type": "Population Sample",
    "regulatory_context": "FR Y-14M Schedule D.1",
    "scoped_attributes": [
        {
            "attribute_name": "Reference Number",
            "is_primary_key": True,
            "data_type": "String",
            "mandatory_flag": "Mandatory"
        },
        {
            "attribute_name": "Account Number",
            "is_primary_key": False,
            "data_type": "String",
            "mandatory_flag": "Mandatory"
        },
        {
            "attribute_name": "Current Balance",
            "is_primary_key": False,
            "data_type": "Decimal",
            "mandatory_flag": "Mandatory"
        }
    ]
}

response = requests.post(
    f"{BASE_URL}/sample-selection/cycles/13/reports/156/samples/generate",
    headers=headers,
    json=generate_data
)

print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

# Get the generated sample
print("\n4. Fetching generated sample...")
response = requests.get(
    f"{BASE_URL}/sample-selection/cycles/13/reports/156/samples",
    headers=headers
)

if response.status_code == 200:
    data = response.json()
    samples = data.get('samples', [])
    if samples:
        latest = samples[0]  # Most recent
        print(f"\nLatest sample:")
        print(f"Sample ID: {latest['sample_id']}")
        print(f"Primary Key: {latest['primary_key_value']}")
        print(f"Sample Data: {json.dumps(latest['sample_data'], indent=2)}")