#!/usr/bin/env python3
"""Test clean sample generation"""

import requests
import json
import time

# Base URL
BASE_URL = "http://localhost:8001/api/v1"

# Login
login_response = requests.post(f"{BASE_URL}/auth/login", json={
    "email": "tester@synapse.com",
    "password": "TestUser123!"
})
token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# First, clear all existing samples by getting them and deleting if needed
print("Getting current samples...")
response = requests.get(
    f"{BASE_URL}/sample-selection/cycles/13/reports/156/samples",
    headers=headers
)
existing = response.json()
print(f"Found {len(existing['samples'])} existing samples")

# Generate new samples
print("\nGenerating 2 new samples...")
response = requests.post(
    f"{BASE_URL}/sample-selection/cycles/13/reports/156/samples/generate",
    headers=headers,
    json={
        "sample_size": 2,
        "sample_type": "Population Sample",
        "regulatory_context": "FR Y-14M Schedule D.1"
    }
)
print(f"Status: {response.status_code}")
result = response.json()
print(f"Generated: {result.get('samples_generated', 0)} samples")

# Wait a moment
time.sleep(1)

# Get the samples to see format
print("\nFetching samples...")
response = requests.get(
    f"{BASE_URL}/sample-selection/cycles/13/reports/156/samples",
    headers=headers
)

if response.status_code == 200:
    data = response.json()
    samples = data.get('samples', [])
    
    # Find the most recent samples (they should be first due to order by generated_at desc)
    print(f"\nTotal samples: {len(samples)}")
    
    # Show the 2 most recent samples
    for i, sample in enumerate(samples[:2], 1):
        print(f"\n=== Sample {i} ===")
        print(f"Sample ID: {sample['sample_id']}")
        print(f"Primary Key: {sample['primary_key_value']}")
        print(f"Generation Method: {sample['generation_method']}")
        print(f"Generated At: {sample['generated_at']}")
        print(f"\nSample Data:")
        print(json.dumps(sample['sample_data'], indent=2))