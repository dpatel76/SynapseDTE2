#!/usr/bin/env python3
"""Test observation management API endpoints"""

import requests
import json

# Test user credentials
test_users = {
    "tester": {"email": "tester@example.com", "password": "password123"},
    "report_owner": {"email": "reportowner@example.com", "password": "password123"},
}

def get_auth_token(email, password):
    """Get authentication token"""
    response = requests.post(
        "http://localhost:8001/api/v1/auth/login",
        json={"email": email, "password": password}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Login failed: {response.status_code} - {response.text}")
        return None

def test_observation_endpoints(token):
    """Test observation management endpoints"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test parameters
    cycle_id = 9
    report_id = 156
    
    print(f"\nTesting observation management endpoints for cycle {cycle_id}, report {report_id}...")
    
    # Test phase status endpoint
    print("\n1. Testing phase status endpoint...")
    response = requests.get(
        f"http://localhost:8001/api/v1/observation-management/{cycle_id}/reports/{report_id}/status",
        headers=headers
    )
    print(f"   Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Phase Status: {data.get('status', 'N/A')}")
        print(f"   Total Observations: {data.get('total_observations', 0)}")
        print(f"   Open Observations: {data.get('open_observations', 0)}")
        print(f"   Completion Rate: {data.get('completion_rate', 0) * 100:.1f}%")
    else:
        print(f"   Error: {response.text}")
    
    # Test observations endpoint
    print("\n2. Testing observations list endpoint...")
    response = requests.get(
        f"http://localhost:8001/api/v1/observation-management/{cycle_id}/reports/{report_id}/observations",
        headers=headers
    )
    print(f"   Status Code: {response.status_code}")
    if response.status_code == 200:
        observations = response.json()
        print(f"   Number of Observations: {len(observations)}")
        if observations:
            print("   Sample Observation:")
            obs = observations[0]
            print(f"     - Type: {obs.get('observation_type')}")
            print(f"     - Severity: {obs.get('severity')}")
            print(f"     - Status: {obs.get('status')}")
            print(f"     - Description: {obs.get('description', '')[:50]}...")
    else:
        print(f"   Error: {response.text}")
    
    # Test analytics endpoint
    print("\n3. Testing analytics endpoint...")
    response = requests.get(
        f"http://localhost:8001/api/v1/observation-management/{cycle_id}/reports/{report_id}/analytics",
        headers=headers
    )
    print(f"   Status Code: {response.status_code}")
    if response.status_code == 200:
        analytics = response.json()
        print(f"   Average Resolution Time: {analytics.get('average_resolution_time', 0)} days")
        print(f"   Resolution Rate: {analytics.get('resolution_rate', 0) * 100:.1f}%")
    else:
        print(f"   Error: {response.text}")

def main():
    print("Testing Observation Management API Endpoints")
    print("=" * 50)
    
    # Test as tester
    print("\nTesting as Tester...")
    token = get_auth_token(test_users["tester"]["email"], test_users["tester"]["password"])
    if token:
        test_observation_endpoints(token)
    
    # Test as report owner
    print("\n\nTesting as Report Owner...")
    token = get_auth_token(test_users["report_owner"]["email"], test_users["report_owner"]["password"])
    if token:
        test_observation_endpoints(token)

if __name__ == "__main__":
    main()