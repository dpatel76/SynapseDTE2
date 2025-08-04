#!/usr/bin/env python3
"""Verify Data Executive can see data providers"""

import requests
import json

def test_data_executive_interface():
    """Test that Data Executive can see data providers in dropdown"""
    
    # Login as Data Executive
    print("1. Logging in as Data Executive...")
    login_response = requests.post(
        "http://localhost:8001/api/v1/auth/login",
        json={"email": "cdo@example.com", "password": "password123"}
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return
        
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login successful")
    
    # Get assignment matrix
    print("\n2. Fetching assignment matrix...")
    response = requests.get(
        "http://localhost:8001/api/v1/data-owner/9/reports/156/assignment-matrix",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to get assignment matrix: {response.text}")
        return
        
    data = response.json()
    print("✅ Assignment matrix fetched successfully")
    
    # Check for pending assignments
    pending_assignments = [
        a for a in data.get('assignments', []) 
        if not a['is_primary_key'] and a['data_owner_id'] is None and a['status'] == 'Assigned'
    ]
    
    print(f"\n3. Pending assignments requiring data provider: {len(pending_assignments)}")
    for assignment in pending_assignments:
        print(f"   - {assignment['attribute_name']} (LOB: {assignment['assigned_lobs'][0]['lob_name']})")
    
    # Check available data providers
    data_providers = data.get('data_providers', [])
    print(f"\n4. Available data providers: {len(data_providers)}")
    for provider in data_providers:
        print(f"   - {provider['first_name']} {provider['last_name']} ({provider['email']}) - LOB: {provider['lob_name']}")
    
    if data_providers and pending_assignments:
        print(f"\n✅ SUCCESS: Data Executive can now see {len(data_providers)} data provider(s) to assign to {len(pending_assignments)} pending attribute(s)")
        print("\nThe Data Executive should now be able to:")
        print("1. See Product Type (and other non-PK attributes) in the pending assignments list")
        print("2. Click the dropdown and see Lisa Chen as an available data provider")
        print("3. Select Lisa Chen and submit the assignment")
    else:
        if not data_providers:
            print("\n❌ ISSUE: No data providers found in the response")
        if not pending_assignments:
            print("\n❌ ISSUE: No pending assignments found")

if __name__ == "__main__":
    print("Verifying Data Executive Assignment Interface Fix")
    print("=" * 60)
    test_data_executive_interface()