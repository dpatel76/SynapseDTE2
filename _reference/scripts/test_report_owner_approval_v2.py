#!/usr/bin/env python3

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8001/api/v1"

# First, let's login as report owner
print("=== Logging in as report owner ===")
login_response = requests.post(
    f"{BASE_URL}/auth/login",
    json={"email": "report.owner@example.com", "password": "password123"}
)

if login_response.status_code != 200:
    print(f"❌ Login failed: {login_response.status_code}")
    print(login_response.text)
    exit(1)

token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
user_info = login_response.json().get("user", {})
print(f"✅ Login successful as: {user_info.get('email', 'Unknown')} (Role: Report Owner)")

# Get test cycles
print("\n=== Getting test cycles ===")
cycles_response = requests.get(f"{BASE_URL}/cycles", headers=headers)
if cycles_response.status_code != 200:
    print(f"❌ Failed to get test cycles: {cycles_response.status_code}")
    exit(1)

cycles = cycles_response.json()
# Look for cycle 58 which has observations
cycle = next((c for c in cycles["cycles"] if c["cycle_id"] == 58), cycles["cycles"][0])
cycle_id = cycle["cycle_id"]
print(f"✅ Using test cycle: {cycle_id} - {cycle['cycle_name']}")

# Get reports
print("\n=== Getting reports ===")
reports_response = requests.get(f"{BASE_URL}/cycles/{cycle_id}/reports", headers=headers)
if reports_response.status_code == 404:
    reports_response = requests.get(f"{BASE_URL}/reports?cycle_id={cycle_id}", headers=headers)

if reports_response.status_code != 200:
    print(f"❌ Failed to get reports: {reports_response.status_code}")
    exit(1)

reports = reports_response.json()
if isinstance(reports, list):
    report = reports[0]
else:
    report = reports[0] if reports else None

report_id = report.get("report_id") or report.get("id")
print(f"✅ Using report: {report_id} - {report.get('report_name', 'Unknown')}")

# Test 1: Observation Report Owner Approval
print("\n=== Testing Observation Report Owner Approval ===")
phase_id = 481  # We know this from previous tests

# Get observation groups
groups_response = requests.get(
    f"{BASE_URL}/observation-enhanced/{cycle_id}/reports/{report_id}/observation-groups",
    headers=headers
)

if groups_response.status_code == 200:
    groups = groups_response.json()
    print(f"Found {len(groups)} observation groups")
    
    # Look for observations that need report owner approval
    approved_count = 0
    for group in groups:
        observations = group.get("observations", [])
        
        for obs in observations:
            print(f"\nObservation {obs['observation_id']}:")
            print(f"  Title: {obs.get('title', 'N/A')}")
            print(f"  Tester Decision: {obs.get('tester_decision', 'None')}")
            print(f"  Report Owner Decision: {obs.get('report_owner_decision', 'None')}")
            
            # If tester approved but report owner hasn't reviewed yet
            if obs.get("tester_decision") == "Approved" and obs.get("report_owner_decision") is None:
                print(f"  → Testing report owner approval for observation {obs['observation_id']}")
                
                # Approve observation as report owner
                approval_data = {
                    "decision": "Approved",
                    "comments": "Report owner approval - observation is valid and accurately reflects the issue"
                }
                
                # Try the direct observation endpoint
                approval_response = requests.post(
                    f"{BASE_URL}/observation-enhanced/observations/{obs['observation_id']}/report-owner-review",
                    json=approval_data,
                    headers=headers
                )
                
                # If that doesn't work, try with cycle/report context
                if approval_response.status_code == 404:
                    approval_response = requests.post(
                        f"{BASE_URL}/observation-enhanced/{cycle_id}/reports/{report_id}/observations/{obs['observation_id']}/report-owner-review",
                        json=approval_data,
                        headers=headers
                    )
                
                if approval_response.status_code == 200:
                    print("  ✅ Report owner approval successful!")
                    approved_count += 1
                    
                    # Verify feedback appears
                    verify_response = requests.get(
                        f"{BASE_URL}/observation-enhanced/{cycle_id}/reports/{report_id}/observation-groups",
                        headers=headers
                    )
                    if verify_response.status_code == 200:
                        updated_groups = verify_response.json()
                        for updated_group in updated_groups:
                            updated_obs = next((o for o in updated_group.get("observations", []) 
                                              if o["observation_id"] == obs["observation_id"]), None)
                            if updated_obs:
                                print(f"  ✓ Report owner decision: {updated_obs.get('report_owner_decision')}")
                                print(f"  ✓ Report owner comments: {updated_obs.get('report_owner_comments')}")
                                break
                else:
                    print(f"  ❌ Approval failed: {approval_response.status_code}")
                    print(f"  Error: {approval_response.text}")
    
    if approved_count == 0:
        print("\nℹ️  No observations pending report owner approval")
        print("Let me check if there are any observations that can be approved by report owner...")
        
        # Show all observations status
        for group in groups:
            for obs in group.get("observations", []):
                print(f"\nObservation {obs['observation_id']}:")
                print(f"  Tester Decision: {obs.get('tester_decision', 'None')}")
                print(f"  Report Owner Decision: {obs.get('report_owner_decision', 'None')}")
                print(f"  Status: {obs.get('status', 'Unknown')}")
else:
    print(f"❌ Failed to get observation groups: {groups_response.status_code}")

# Test 2: Try Data Provider Assignment Approval
print("\n\n=== Testing Data Provider Assignment Report Owner Approval ===")

# First check if there are any assignments
assignments_response = requests.get(
    f"{BASE_URL}/data-owner-assignments",
    params={"cycle_id": cycle_id, "report_id": report_id},
    headers=headers
)

if assignments_response.status_code == 404:
    # Try alternative endpoint
    assignments_response = requests.get(
        f"{BASE_URL}/data-provider-identification/{cycle_id}/reports/{report_id}/assignments",
        headers=headers
    )

if assignments_response.status_code == 200:
    data = assignments_response.json()
    assignments = data.get("assignments", []) if isinstance(data, dict) else data
    print(f"Found {len(assignments)} assignments")
    
    # Check for assignments needing report owner approval
    for assignment in assignments[:3]:  # Check first 3
        print(f"\nAssignment {assignment.get('assignment_id', 'Unknown')}:")
        print(f"  Attribute: {assignment.get('attribute_name', 'N/A')}")
        print(f"  Data Owner: {assignment.get('data_owner_name', 'N/A')}")
        print(f"  Report Owner Decision: {assignment.get('report_owner_decision', 'None')}")
        
        if assignment.get("report_owner_decision") is None:
            print("  → Testing report owner approval")
            
            approval_data = {
                "assignment_ids": [assignment["assignment_id"]],
                "decision": "Approved",
                "feedback": "Report owner approval - correct data owner assigned for this attribute"
            }
            
            approval_response = requests.post(
                f"{BASE_URL}/data-provider-identification/{cycle_id}/reports/{report_id}/assignments/report-owner-review",
                json=approval_data,
                headers=headers
            )
            
            if approval_response.status_code == 200:
                print("  ✅ Report owner approval successful!")
                # Verify the update
                verify_response = requests.get(
                    f"{BASE_URL}/data-provider-identification/{cycle_id}/reports/{report_id}/assignments",
                    headers=headers
                )
                if verify_response.status_code == 200:
                    updated_data = verify_response.json()
                    updated_assignments = updated_data.get("assignments", [])
                    updated_assignment = next((a for a in updated_assignments 
                                             if a["assignment_id"] == assignment["assignment_id"]), None)
                    if updated_assignment:
                        print(f"  ✓ Report owner decision: {updated_assignment.get('report_owner_decision')}")
                        print(f"  ✓ Report owner feedback: {updated_assignment.get('report_owner_feedback')}")
            else:
                print(f"  ❌ Approval failed: {approval_response.status_code}")
                print(f"  Error: {approval_response.text}")
            break
else:
    print(f"ℹ️  Could not get assignments: {assignments_response.status_code}")

print("\n=== Report Owner Approval Testing Complete ===")