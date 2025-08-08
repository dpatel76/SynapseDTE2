#!/usr/bin/env python3
"""
Test the complete sample selection workflow including submission
"""

import requests
import json
import time

# Base URL
BASE_URL = "http://localhost:8001/api/v1"

# Test cycle and report
cycle_id = 13
report_id = 156

def login(email, password):
    """Login and return token"""
    response = requests.post(f"{BASE_URL}/auth/login", json={"email": email, "password": password})
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Login failed for {email}: {response.text}")
        return None

def test_endpoint(method, path, token, data=None, description=""):
    """Test an endpoint and return response"""
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{BASE_URL}{path}"
    
    print(f"\n{description}")
    print(f"{method} {path}")
    
    if method == "GET":
        response = requests.get(url, headers=headers)
    elif method == "POST":
        response = requests.post(url, headers=headers, json=data)
    elif method == "PUT":
        response = requests.put(url, headers=headers, json=data)
    else:
        raise ValueError(f"Unsupported method: {method}")
    
    print(f"Status: {response.status_code}")
    if response.status_code in [200, 201]:
        print("✅ Success")
        return response.json()
    else:
        print(f"❌ Error: {response.text}")
        return None

def main():
    print("=== Testing Complete Sample Selection Workflow ===\n")
    
    # Step 1: Login as tester
    print("Step 1: Login as tester")
    tester_token = login("tester@synapse.com", "TestUser123!")
    if not tester_token:
        return
    
    # Step 2: Get current samples
    result = test_endpoint(
        "GET", 
        f"/sample-selection/cycles/{cycle_id}/reports/{report_id}/samples",
        tester_token,
        description="Getting current samples"
    )
    
    if result:
        print(f"Found {len(result.get('samples', []))} samples")
        sample_ids = [s['sample_id'] for s in result.get('samples', [])][:3]  # Take first 3
    
    # Step 3: Update sample decisions
    if sample_ids:
        result = test_endpoint(
            "PUT",
            f"/sample-selection/cycles/{cycle_id}/reports/{report_id}/samples/bulk-decision",
            tester_token,
            data={"sample_ids": sample_ids, "decision": "include"},
            description="Setting samples as included"
        )
    
    # Step 4: Submit samples for approval
    if sample_ids:
        result = test_endpoint(
            "POST",
            f"/sample-selection/cycles/{cycle_id}/reports/{report_id}/samples/submit",
            tester_token,
            data={"sample_ids": sample_ids, "notes": "Submitting first batch for review"},
            description="Submitting samples for report owner approval"
        )
    
    # Step 5: Check submissions
    result = test_endpoint(
        "GET",
        f"/sample-selection/cycles/{cycle_id}/reports/{report_id}/samples/submissions",
        tester_token,
        description="Getting submission history"
    )
    
    if result:
        print(f"Found {len(result)} submissions")
        for sub in result[:2]:
            print(f"  - Version {sub['version_number']}: {sub['status']} ({sub['total_samples']} samples)")
    
    # Step 6: Login as report owner
    print("\n\nStep 6: Login as report owner")
    owner_token = login("owner@synapse.com", "TestUser123!")
    if not owner_token:
        return
    
    # Step 7: Get pending reviews
    result = test_endpoint(
        "GET",
        "/sample-selection/pending-reviews",
        owner_token,
        description="Getting pending sample reviews"
    )
    
    if result:
        print(f"Found {len(result)} pending reviews")
        for review in result:
            print(f"  - {review['report_name']}: Version {review['version_number']} ({review['total_samples']} samples)")
    
    # Step 8: Review submission (approve)
    result = test_endpoint(
        "POST",
        f"/sample-selection/cycles/{cycle_id}/reports/{report_id}/samples/review",
        owner_token,
        data={"decision": "approved", "feedback": "Samples look good"},
        description="Approving sample submission"
    )
    
    # Step 9: Check analytics as tester
    result = test_endpoint(
        "GET",
        f"/sample-selection/cycles/{cycle_id}/reports/{report_id}/samples/analytics",
        tester_token,
        description="Getting phase analytics"
    )
    
    if result:
        print(f"Phase Status: {result.get('phase_status')}")
        print(f"Total Samples: {result.get('total_samples')}")
        print(f"Approved Samples: {result.get('approved_samples')}")
        print(f"Can Complete Phase: {result.get('can_complete_phase')}")
    
    # Step 10: Test manual upload
    result = test_endpoint(
        "POST",
        f"/sample-selection/cycles/{cycle_id}/reports/{report_id}/samples/upload",
        tester_token,
        data={
            "cycle_report_sample_selection_samples": [
                {
                    "primary_key_value": "MANUAL_001",
                    "account_id": "ACC_MANUAL_001",
                    "account_type": "Savings",
                    "balance": 50000
                }
            ]
        },
        description="Uploading manual sample"
    )
    
    print("\n=== Workflow Test Complete ===")

if __name__ == "__main__":
    main()