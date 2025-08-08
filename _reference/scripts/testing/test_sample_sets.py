#!/usr/bin/env python3
import requests
import json

# Login first
login_url = "http://localhost:8001/api/v1/auth/login"
login_data = {
    "email": "john.doe@synapsedt.com",
    "password": "P@ssw0rd"
}

response = requests.post(login_url, json=login_data)
if response.status_code == 200:
    token = response.json()["access_token"]
    print(f"✅ Login successful")
    
    # Test sample-sets endpoint
    headers = {"Authorization": f"Bearer {token}"}
    sample_sets_url = "http://localhost:8001/api/v1/sample-selection/9/reports/156/sample-sets"
    
    response = requests.get(sample_sets_url, headers=headers)
    print(f"\n📋 Sample Sets Response (Status: {response.status_code}):")
    print(json.dumps(response.json(), indent=2))
else:
    print(f"❌ Login failed: {response.status_code}")
    print(response.json())