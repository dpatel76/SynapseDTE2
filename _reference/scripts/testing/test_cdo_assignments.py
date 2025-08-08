#!/usr/bin/env python3
"""
Test CDO Assignments Functionality
Test the new /my-assignments endpoint with CDO authentication
"""

import requests
import json

def test_cdo_assignments():
    """Test CDO assignments endpoint with authentication"""
    print("=== TESTING CDO ASSIGNMENTS ENDPOINT ===")
    
    base_url = "http://localhost:8000/api/v1"
    
    # Step 1: Login as CDO
    print("\n1. Logging in as CDO...")
    login_data = {
        "email": "cdo@example.com",
        "password": "password123"
    }
    
    try:
        response = requests.post(f"{base_url}/auth/login", json=login_data)
        if response.status_code == 200:
            result = response.json()
            token = result.get("access_token")
            user = result.get("user")
            print(f"✅ Login successful")
            print(f"   Token: {token[:20]}...")
            print(f"   User: {user.get('email')} ({user.get('role')})")
            print(f"   LOB ID: {user.get('lob_id')}")
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return
    except Exception as e:
        print(f"❌ Login error: {e}")
        return
    
    # Step 2: Test CDO assignments endpoint
    print("\n2. Testing CDO assignments endpoint...")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test with different cycle/report combinations
    test_cases = [
        (4, 156, "Main test cycle/report"),
        (8, 160, "Alternative cycle/report")
    ]
    
    for cycle_id, report_id, description in test_cases:
        print(f"\n📋 Testing {description} (cycle={cycle_id}, report={report_id})...")
        
        try:
            response = requests.get(
                f"{base_url}/data-owner/{cycle_id}/reports/{report_id}/my-assignments",
                headers=headers
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                assignments = response.json()
                print(f"   ✅ Success! Found {len(assignments)} assignments")
                
                for i, assignment in enumerate(assignments, 1):
                    print(f"   Assignment {i}:")
                    print(f"     - Attribute: {assignment.get('attribute_name')}")
                    print(f"     - Data Provider: {assignment.get('data_owner_name')}")
                    print(f"     - LOB: {assignment.get('lob_name')}")
                    print(f"     - Status: {assignment.get('status')}")
                    print(f"     - Assigned At: {assignment.get('assigned_at')}")
            elif response.status_code == 403:
                print(f"   ⚠️  Access denied: {response.text}")
            elif response.status_code == 404:
                print(f"   ℹ️  Not found: {response.text}")
            else:
                print(f"   ❌ Error: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Request error: {e}")
    
    # Step 3: Test that tester can see "My Assignments" button
    print("\n3. Testing frontend integration...")
    print("   - CDO should see 'My Assignments' button on Data Provider page")
    print("   - Button should navigate to /cycles/{cycleId}/reports/{reportId}/cdo-assignments")
    print("   - Page should display assignments made by this CDO")
    
    print("\n=== TEST COMPLETED ===")
    print("\nNext steps:")
    print("1. Open browser and login as CDO (cdo@example.com / CDO123!)")
    print("2. Navigate to Data Provider page for cycle 4, report 156")
    print("3. Look for 'My Assignments' button")
    print("4. Click button and verify assignments are displayed")

if __name__ == "__main__":
    test_cdo_assignments() 