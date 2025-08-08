#!/usr/bin/env python3
"""
Test the new sample generation with scoped attributes
"""

import requests
import json

# Base URL
BASE_URL = "http://localhost:8001/api/v1"
cycle_id = 13
report_id = 156

# Login
login_response = requests.post(f"{BASE_URL}/auth/login", json={
    "email": "tester@synapse.com",
    "password": "TestUser123!"
})
token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# First, get the scoped attributes for this report
print("1. Getting scoped attributes...")
response = requests.get(
    f"{BASE_URL}/scoping/cycles/{cycle_id}/reports/{report_id}/attributes",
    headers=headers
)
if response.status_code == 200:
    attributes = response.json()
    scoped_attrs = [attr for attr in attributes if attr.get('is_scoped') or attr.get('include_in_testing')]
    print(f"Found {len(scoped_attrs)} scoped attributes:")
    for attr in scoped_attrs[:5]:  # Show first 5
        print(f"  - {attr['attribute_name']} ({attr['data_type']})")
else:
    print(f"Failed to get attributes: {response.text}")
    exit(1)

# Clear existing samples first
print("\n2. Clearing existing samples...")
response = requests.get(
    f"{BASE_URL}/sample-selection/cycles/{cycle_id}/reports/{report_id}/samples",
    headers=headers
)
if response.status_code == 200:
    existing = response.json()
    print(f"Found {len(existing['samples'])} existing samples")

# Generate new samples
print("\n3. Generating new samples with scoped attributes...")
generate_data = {
    "sample_size": 3,  # Small number for testing
    "sample_type": "Population Sample",
    "regulatory_context": "FR Y-14M Schedule D.1"
}

response = requests.post(
    f"{BASE_URL}/sample-selection/cycles/{cycle_id}/reports/{report_id}/samples/generate",
    headers=headers,
    json=generate_data
)

if response.status_code == 200:
    result = response.json()
    print(f"✅ Generated {result.get('samples_generated', 0)} samples")
else:
    print(f"❌ Failed to generate: {response.text}")

# Get the new samples to see the format
print("\n4. Retrieving generated samples...")
response = requests.get(
    f"{BASE_URL}/sample-selection/cycles/{cycle_id}/reports/{report_id}/samples",
    headers=headers
)

if response.status_code == 200:
    data = response.json()
    samples = data.get('samples', [])
    
    # Find the newly generated samples (they should be at the beginning due to order by generated_at desc)
    new_samples = [s for s in samples if s['generation_method'] == 'LLM Generated'][-3:]
    
    print(f"\nShowing {len(new_samples)} newly generated samples:")
    for i, sample in enumerate(new_samples, 1):
        print(f"\n--- Sample {i} ---")
        print(f"Sample ID: {sample['sample_id']}")
        print(f"Primary Key: {sample['primary_key_value']}")
        print(f"Generated: {sample['generated_at']}")
        print(f"Sample Data:")
        print(json.dumps(sample['sample_data'], indent=2))
else:
    print(f"Failed to get samples: {response.text}")