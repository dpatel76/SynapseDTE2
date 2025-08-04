#!/usr/bin/env python3
"""
Test the Request Info API endpoints
"""

import requests
import json

# Base URL
BASE_URL = "http://localhost:8000"

# Test endpoints
endpoints = [
    "/api/v1/request-info/55/reports/156/status",
    "/api/v1/test-report/55/reports/156/data",
    "/api/v1/test-execution-legacy/55/reports/156/submitted-test-cases",
    "/api/v1/test-execution-legacy/55/reports/156/executions"
]

# Get auth token (assuming there's a login endpoint)
# For now, we'll test without auth

print("Testing API endpoints...")
print("=" * 50)

for endpoint in endpoints:
    url = BASE_URL + endpoint
    print(f"\nTesting: {endpoint}")
    
    try:
        response = requests.get(url)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("Success!")
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)[:200]}...")
        elif response.status_code == 401:
            print("Authentication required")
        elif response.status_code == 404:
            print("Endpoint not found")
        else:
            print(f"Error: {response.text[:200]}...")
            
    except Exception as e:
        print(f"Request failed: {str(e)}")

print("\n" + "=" * 50)
print("Test complete!")