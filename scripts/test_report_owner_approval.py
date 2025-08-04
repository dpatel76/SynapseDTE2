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
    # Try alternative email
    print("\n=== Trying alternative login ===")
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": "admin@example.com", "password": "password123"}
    )
    if login_response.status_code != 200:
        print(f"❌ Alternative login also failed: {login_response.status_code}")
        exit(1)

token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
user_info = login_response.json().get("user", {})
print(f"✅ Login successful as: {user_info.get('email', 'Unknown')}")

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

# Get workflow phases to find different phase types
print("\n=== Checking different phases for report owner approval ===")

# Let's check multiple phases that might have report owner approval
phase_names = ["Scoping", "Data Provider ID", "Observations"]

for phase_name in phase_names:
    print(f"\n--- Checking {phase_name} phase ---")
    
    # Get phase ID from database query result
    if phase_name == "Observations":
        phase_id = 481  # We know this from previous tests
    else:
        # For other phases, we'll query the database directly
        # Since the API endpoint structure might be different
        print(f"  Querying for {phase_name} phase...")
        continue  # Skip for now since we need to find the correct API endpoint
            if phase:
                phase_id = phase["phase_id"]
            else:
                print(f"  ❌ {phase_name} phase not found")
                continue
        else:
            print(f"  ❌ Could not get workflow phases")
            continue
    
    print(f"  ✅ Found {phase_name} phase: {phase_id}")
    
    # Check what endpoints are available for this phase
    if phase_name == "Scoping":
        # Test scoping approval
        print("\n  === Testing Scoping Report Owner Approval ===")
        
        # Get scoping samples that need approval
        samples_response = requests.get(
            f"{BASE_URL}/scoping/{cycle_id}/reports/{report_id}/samples",
            headers=headers
        )
        
        if samples_response.status_code == 200:
            samples = samples_response.json()
            print(f"  Found {len(samples)} samples")
            
            # Look for samples that need report owner approval
            pending_samples = [s for s in samples if s.get("report_owner_decision") is None]
            if pending_samples:
                sample = pending_samples[0]
                print(f"  Testing approval for sample: {sample.get('sample_id', 'Unknown')}")
                
                # Approve sample as report owner
                approval_data = {
                    "sample_ids": [sample["sample_id"]],
                    "decision": "Approved",
                    "comments": "Approved by report owner - test feedback"
                }
                
                approval_response = requests.post(
                    f"{BASE_URL}/scoping/{cycle_id}/reports/{report_id}/samples/report-owner-review",
                    json=approval_data,
                    headers=headers
                )
                
                if approval_response.status_code == 200:
                    print("  ✅ Report owner approval successful!")
                    result = approval_response.json()
                    print(f"  Result: {json.dumps(result, indent=2)}")
                    
                    # Verify feedback appears
                    verify_response = requests.get(
                        f"{BASE_URL}/scoping/{cycle_id}/reports/{report_id}/samples",
                        headers=headers
                    )
                    if verify_response.status_code == 200:
                        updated_samples = verify_response.json()
                        updated_sample = next((s for s in updated_samples if s["sample_id"] == sample["sample_id"]), None)
                        if updated_sample:
                            print(f"  Report owner decision: {updated_sample.get('report_owner_decision')}")
                            print(f"  Report owner comments: {updated_sample.get('report_owner_comments')}")
                else:
                    print(f"  ❌ Approval failed: {approval_response.status_code}")
                    print(f"  Error: {approval_response.text}")
            else:
                print("  ℹ️  No samples pending report owner approval")
                
    elif phase_name == "Data Provider ID":
        # Test data provider assignment approval
        print("\n  === Testing Data Provider Assignment Report Owner Approval ===")
        
        # Get assignments
        assignments_response = requests.get(
            f"{BASE_URL}/data-provider-identification/{cycle_id}/reports/{report_id}/assignments",
            headers=headers
        )
        
        if assignments_response.status_code == 200:
            assignments = assignments_response.json()
            print(f"  Found {len(assignments.get('assignments', []))} assignments")
            
            # Look for assignments that need report owner approval
            pending_assignments = [a for a in assignments.get("assignments", []) 
                                 if a.get("report_owner_decision") is None]
            if pending_assignments:
                assignment = pending_assignments[0]
                print(f"  Testing approval for assignment: {assignment.get('assignment_id', 'Unknown')}")
                
                # Approve assignment as report owner
                approval_data = {
                    "assignment_ids": [assignment["assignment_id"]],
                    "decision": "Approved",
                    "feedback": "Report owner approval test - looks good!"
                }
                
                approval_response = requests.post(
                    f"{BASE_URL}/data-provider-identification/{cycle_id}/reports/{report_id}/assignments/report-owner-review",
                    json=approval_data,
                    headers=headers
                )
                
                if approval_response.status_code == 200:
                    print("  ✅ Report owner approval successful!")
                    result = approval_response.json()
                    print(f"  Result: {json.dumps(result, indent=2)}")
                    
                    # Verify feedback appears
                    verify_response = requests.get(
                        f"{BASE_URL}/data-provider-identification/{cycle_id}/reports/{report_id}/assignments",
                        headers=headers
                    )
                    if verify_response.status_code == 200:
                        updated_assignments = verify_response.json()
                        updated_assignment = next((a for a in updated_assignments.get("assignments", []) 
                                                 if a["assignment_id"] == assignment["assignment_id"]), None)
                        if updated_assignment:
                            print(f"  Report owner decision: {updated_assignment.get('report_owner_decision')}")
                            print(f"  Report owner feedback: {updated_assignment.get('report_owner_feedback')}")
                else:
                    print(f"  ❌ Approval failed: {approval_response.status_code}")
                    print(f"  Error: {approval_response.text}")
            else:
                print("  ℹ️  No assignments pending report owner approval")
                
    elif phase_name == "Observations":
        # Test observation approval
        print("\n  === Testing Observation Report Owner Approval ===")
        
        # Get observation groups
        groups_response = requests.get(
            f"{BASE_URL}/observation-enhanced/{cycle_id}/reports/{report_id}/observation-groups",
            headers=headers
        )
        
        if groups_response.status_code == 200:
            groups = groups_response.json()
            print(f"  Found {len(groups)} observation groups")
            
            # Look for observations that need report owner approval
            for group in groups:
                observations = group.get("observations", [])
                pending_obs = [o for o in observations if o.get("report_owner_decision") is None]
                
                if pending_obs:
                    obs = pending_obs[0]
                    print(f"  Testing approval for observation: {obs.get('observation_id', 'Unknown')}")
                    
                    # Approve observation as report owner
                    approval_data = {
                        "decision": "Approved",
                        "comments": "Report owner approval - observation is valid"
                    }
                    
                    approval_response = requests.post(
                        f"{BASE_URL}/observation-enhanced/{cycle_id}/reports/{report_id}/observations/{obs['observation_id']}/report-owner-review",
                        json=approval_data,
                        headers=headers
                    )
                    
                    if approval_response.status_code == 200:
                        print("  ✅ Report owner approval successful!")
                        result = approval_response.json()
                        print(f"  Result: {json.dumps(result, indent=2)}")
                        
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
                                    print(f"  Report owner decision: {updated_obs.get('report_owner_decision')}")
                                    print(f"  Report owner comments: {updated_obs.get('report_owner_comments')}")
                                    break
                    else:
                        print(f"  ❌ Approval failed: {approval_response.status_code}")
                        print(f"  Error: {approval_response.text}")
                    break
            else:
                print("  ℹ️  No observations pending report owner approval")

print("\n=== Report Owner Approval Testing Complete ===")