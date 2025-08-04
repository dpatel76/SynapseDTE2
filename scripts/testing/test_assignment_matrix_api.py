#!/usr/bin/env python3
"""Test assignment matrix API to see what fields are returned"""

import requests
import json

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

def test_assignment_matrix():
    """Test assignment matrix endpoint"""
    # Login as Data Executive
    token = get_auth_token("cdo@example.com", "password123")
    if not token:
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test assignment matrix
    print("\nFetching assignment matrix for cycle 9, report 156...")
    response = requests.get(
        "http://localhost:8001/api/v1/data-owner/9/reports/156/assignment-matrix",
        headers=headers
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        print(f"\nTotal Assignments: {len(data.get('assignments', []))}")
        
        # Look for Product Type specifically
        for assignment in data.get('assignments', []):
            if 'Product Type' in assignment.get('attribute_name', ''):
                print(f"\nFound Product Type assignment:")
                print(json.dumps(assignment, indent=2))
                break
        
        # Show first assignment as example
        if data.get('assignments'):
            print(f"\nExample assignment structure:")
            print(json.dumps(data['assignments'][0], indent=2))
            
        # Show available data providers
        if data.get('data_providers'):
            print(f"\nAvailable Data Providers: {len(data['data_providers'])}")
            for dp in data['data_providers'][:3]:  # Show first 3
                print(f"  - {dp['first_name']} {dp['last_name']} ({dp['email']}) - LOB: {dp.get('lob_name', 'N/A')}")
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    print("Testing Assignment Matrix API...")
    print("=" * 60)
    test_assignment_matrix()