#!/usr/bin/env python3
"""Debug sample generation"""

import requests
import json

# Base URL
BASE_URL = "http://localhost:8001/api/v1"

# Login
print("Logging in...")
login_response = requests.post(f"{BASE_URL}/auth/login", json={
    "email": "tester@synapse.com",
    "password": "TestUser123!"
})

if login_response.status_code != 200:
    print(f"Login failed: {login_response.text}")
    exit(1)

token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("✅ Logged in successfully")

# Generate samples with minimal data
print("\nGenerating samples...")
generate_data = {
    "sample_size": 2,
    "sample_type": "Population Sample",
    "regulatory_context": "FR Y-14M Schedule D.1"
}

response = requests.post(
    f"{BASE_URL}/sample-selection/cycles/13/reports/156/samples/generate",
    headers=headers,
    json=generate_data
)

print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

# Check backend logs
print("\nCheck backend logs with:")
print("tail -100 backend.log | grep -i 'sample\\|error\\|exception'")