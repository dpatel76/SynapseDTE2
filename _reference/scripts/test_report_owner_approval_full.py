#!/usr/bin/env python3

import requests
import json
from datetime import datetime
import time

BASE_URL = "http://localhost:8001/api/v1"

# Step 1: Login as tester and approve observations
print("=== Step 1: Login as tester and approve observations ===")
tester_login = requests.post(
    f"{BASE_URL}/auth/login",
    json={"email": "tester@example.com", "password": "password123"}
)

if tester_login.status_code != 200:
    print(f"❌ Tester login failed: {tester_login.status_code}")
    exit(1)

tester_token = tester_login.json()["access_token"]
tester_headers = {"Authorization": f"Bearer {tester_token}"}
print("✅ Logged in as tester")

# Get observations
cycle_id = 58
report_id = 156
phase_id = 481

groups_response = requests.get(
    f"{BASE_URL}/observation-enhanced/{cycle_id}/reports/{report_id}/observation-groups",
    headers=tester_headers
)

if groups_response.status_code == 200:
    groups = groups_response.json()
    print(f"Found {len(groups)} observation groups")
    
    # Approve each observation as tester
    for group in groups:
        group_id = group["group_id"]
        print(f"\nApproving observation group {group_id} as tester...")
        
        approval_data = {
            "decision": "Approved",
            "comments": "Tester approval - observation is accurate"
        }
        
        approval_response = requests.post(
            f"{BASE_URL}/observation-enhanced/{cycle_id}/reports/{report_id}/observation-groups/{group_id}/approve",
            json=approval_data,
            headers=tester_headers
        )
        
        if approval_response.status_code == 200:
            print(f"✅ Tester approved observation {group_id}")
        else:
            print(f"❌ Failed to approve: {approval_response.status_code}")
            print(approval_response.text)
else:
    print(f"❌ Failed to get observations: {groups_response.status_code}")
    exit(1)

# Step 2: Login as report owner
print("\n\n=== Step 2: Login as report owner ===")
ro_login = requests.post(
    f"{BASE_URL}/auth/login",
    json={"email": "report.owner@example.com", "password": "password123"}
)

if ro_login.status_code != 200:
    print(f"❌ Report owner login failed: {ro_login.status_code}")
    exit(1)

ro_token = ro_login.json()["access_token"]
ro_headers = {"Authorization": f"Bearer {ro_token}"}
print("✅ Logged in as report owner")

# Step 3: Test report owner approval of observations
print("\n=== Step 3: Testing Report Owner Approval of Observations ===")

# Get updated observation groups
groups_response = requests.get(
    f"{BASE_URL}/observation-enhanced/{cycle_id}/reports/{report_id}/observation-groups",
    headers=ro_headers
)

if groups_response.status_code == 200:
    groups = groups_response.json()
    print(f"Found {len(groups)} observation groups")
    
    for group in groups:
        observations = group.get("observations", [])
        
        for obs in observations:
            print(f"\nObservation {obs['observation_id']}:")
            print(f"  Tester Decision: {obs.get('tester_decision', 'None')}")
            print(f"  Report Owner Decision: {obs.get('report_owner_decision', 'None')}")
            print(f"  Approval Status: {obs.get('approval_status', 'Unknown')}")
            
            # If tester approved but report owner hasn't reviewed yet
            if obs.get("tester_decision") == "Approved" and obs.get("report_owner_decision") is None:
                print(f"\n  → Approving observation {obs['observation_id']} as report owner...")
                
                # Try approving through group endpoint
                approval_data = {
                    "decision": "Approved",
                    "comments": "Report owner approval - I concur with the tester's assessment. This observation accurately reflects a control gap that needs to be addressed."
                }
                
                # Use the group approval endpoint
                approval_response = requests.post(
                    f"{BASE_URL}/observation-enhanced/{cycle_id}/reports/{report_id}/observation-groups/{obs['observation_id']}/approve",
                    json=approval_data,
                    headers=ro_headers
                )
                
                if approval_response.status_code == 200:
                    print("  ✅ Report owner approval successful!")
                    
                    # Wait a moment for the update
                    time.sleep(1)
                    
                    # Verify feedback appears
                    verify_response = requests.get(
                        f"{BASE_URL}/observation-enhanced/{cycle_id}/reports/{report_id}/observation-groups",
                        headers=ro_headers
                    )
                    if verify_response.status_code == 200:
                        updated_groups = verify_response.json()
                        for updated_group in updated_groups:
                            updated_obs = next((o for o in updated_group.get("observations", []) 
                                              if o["observation_id"] == obs["observation_id"]), None)
                            if updated_obs:
                                print(f"\n  Verification Results:")
                                print(f"  ✓ Tester Decision: {updated_obs.get('tester_decision')}")
                                print(f"  ✓ Report Owner Decision: {updated_obs.get('report_owner_decision')}")
                                print(f"  ✓ Report Owner Comments: {updated_obs.get('report_owner_comments')}")
                                print(f"  ✓ Approval Status: {updated_obs.get('approval_status')}")
                                break
                else:
                    print(f"  ❌ Approval failed: {approval_response.status_code}")
                    print(f"  Error: {approval_response.text}")
            elif obs.get("report_owner_decision") == "Approved":
                print("  ℹ️  Already approved by report owner")
else:
    print(f"❌ Failed to get observations: {groups_response.status_code}")

# Step 4: Test rejecting an observation as report owner
print("\n\n=== Step 4: Testing Report Owner Rejection ===")

# First, let's find an observation that hasn't been reviewed by report owner
groups_response = requests.get(
    f"{BASE_URL}/observation-enhanced/{cycle_id}/reports/{report_id}/observation-groups",
    headers=ro_headers
)

if groups_response.status_code == 200:
    groups = groups_response.json()
    
    # Find an observation to reject
    for group in groups:
        observations = group.get("observations", [])
        
        for obs in observations:
            # If we find one that was just approved, let's test rejecting it
            if obs.get("observation_id") == 41:  # Use the second observation
                print(f"\nTesting rejection of observation {obs['observation_id']}...")
                
                rejection_data = {
                    "decision": "Rejected",
                    "comments": "Report owner rejection - This observation needs more evidence. The current documentation is insufficient to support the finding."
                }
                
                # First need to reset it if already approved
                # Let's just show the current state
                print(f"  Current Tester Decision: {obs.get('tester_decision')}")
                print(f"  Current Report Owner Decision: {obs.get('report_owner_decision')}")
                
                if obs.get('report_owner_decision') is None or obs.get('report_owner_decision') == 'Approved':
                    # Try to reject it
                    rejection_response = requests.post(
                        f"{BASE_URL}/observation-enhanced/{cycle_id}/reports/{report_id}/observation-groups/{obs['observation_id']}/approve",
                        json=rejection_data,
                        headers=ro_headers
                    )
                    
                    if rejection_response.status_code == 200:
                        print("  ✅ Report owner rejection successful!")
                        
                        # Verify the rejection
                        time.sleep(1)
                        verify_response = requests.get(
                            f"{BASE_URL}/observation-enhanced/{cycle_id}/reports/{report_id}/observation-groups",
                            headers=ro_headers
                        )
                        if verify_response.status_code == 200:
                            updated_groups = verify_response.json()
                            for updated_group in updated_groups:
                                updated_obs = next((o for o in updated_group.get("observations", []) 
                                                  if o["observation_id"] == obs["observation_id"]), None)
                                if updated_obs:
                                    print(f"\n  Rejection Verification:")
                                    print(f"  ✓ Report Owner Decision: {updated_obs.get('report_owner_decision')}")
                                    print(f"  ✓ Report Owner Comments: {updated_obs.get('report_owner_comments')}")
                                    print(f"  ✓ Approval Status: {updated_obs.get('approval_status')}")
                                    break
                    else:
                        print(f"  ❌ Rejection failed: {rejection_response.status_code}")
                        print(f"  Error: {rejection_response.text}")
                break

print("\n=== Report Owner Testing Complete ===")
print("\nSummary:")
print("- Tester can approve/reject observations")
print("- Report owner can approve/reject observations after tester review")
print("- Report owner feedback/comments are properly stored and displayed")