#!/usr/bin/env python3
"""Check if tester APIs are working correctly"""

import requests
import json

# Base URL
BASE_URL = "http://localhost:8001/api/v1"

# Test login
print("1. Testing login...")
login_response = requests.post(
    f"{BASE_URL}/auth/login",
    json={
        "email": "tester@synapse.com",  # Test tester user
        "password": "TestUser123!"
    }
)

if login_response.status_code == 200:
    auth_data = login_response.json()
    token = auth_data['access_token']
    user = auth_data['user']
    print(f"✓ Login successful!")
    print(f"  User: {user['email']} ({user['role']})")
    print(f"  User ID: {user['user_id']}")
    
    # Test tester-specific endpoints
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    print("\n2. Testing tester dashboard endpoints...")
    
    # Test tester stats
    print("\n   a) Testing tester-stats endpoint...")
    stats_response = requests.get(
        f"{BASE_URL}/cycle-reports/tester-stats/{user['user_id']}",
        headers=headers
    )
    print(f"   Status: {stats_response.status_code}")
    if stats_response.status_code == 200:
        print(f"   ✓ Stats: {stats_response.json()}")
    else:
        print(f"   ✗ Error: {stats_response.text}")
    
    # Test reports by tester
    print("\n   b) Testing by-tester endpoint...")
    reports_response = requests.get(
        f"{BASE_URL}/cycle-reports/by-tester/{user['user_id']}",
        headers=headers
    )
    print(f"   Status: {reports_response.status_code}")
    if reports_response.status_code == 200:
        reports = reports_response.json()
        print(f"   ✓ Found {len(reports)} reports")
        if reports:
            print(f"   First report: {reports[0].get('report_name', 'N/A')}")
    else:
        print(f"   ✗ Error: {reports_response.text}")
        
    # Test generic cycles endpoint
    print("\n   c) Testing cycles endpoint...")
    cycles_response = requests.get(
        f"{BASE_URL}/cycles/",
        headers=headers
    )
    print(f"   Status: {cycles_response.status_code}")
    if cycles_response.status_code == 200:
        cycles_data = cycles_response.json()
        print(f"   ✓ Response received")
    else:
        print(f"   ✗ Error: {cycles_response.text}")
        
else:
    print(f"✗ Login failed: {login_response.status_code}")
    print(f"Error: {login_response.text}")