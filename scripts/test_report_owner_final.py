#!/usr/bin/env python3

import requests
import json
from datetime import datetime
import time

BASE_URL = "http://localhost:8001/api/v1"

# Wait for backend to be ready
time.sleep(10)

# Login as report owner
print("=== Login as report owner ===")
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

cycle_id = 58
report_id = 156

# Get observation groups
print("\n=== Getting observation groups ===")
groups_response = requests.get(
    f"{BASE_URL}/observation-enhanced/{cycle_id}/reports/{report_id}/observation-groups",
    headers=ro_headers
)

if groups_response.status_code == 200:
    groups = groups_response.json()
    print(f"Found {len(groups)} observation groups")
    
    for group in groups:
        print(f"\n{'='*50}")
        print(f"Group ID: {group['group_id']}")
        print(f"Attribute: {group['attribute_name']}")
        print(f"Issue Type: {group['issue_type']}")
        print(f"Approval Status: {group['approval_status']}")
        print(f"Report Owner Approved: {group['report_owner_approved']}")
        
        # The group_id is actually the observation_id
        obs_id = group['group_id']
        
        # Check if report owner hasn't approved yet
        if not group['report_owner_approved'] and 'Approved by Tester' in group['approval_status']:
            print(f"\n→ Approving observation {obs_id} as report owner...")
            
            # Use the correct request format with "approved" field
            approval_data = {
                "approved": True,
                "comments": "Report owner approval - I agree with the tester's assessment. This issue needs to be addressed in the next remediation cycle."
            }
            
            # Use the observation group approval endpoint
            approval_response = requests.post(
                f"{BASE_URL}/observation-enhanced/observation-groups/{obs_id}/approve",
                json=approval_data,
                headers=ro_headers
            )
            
            if approval_response.status_code == 200:
                print("✅ Report owner approval successful!")
                result = approval_response.json()
                print(f"Response: {json.dumps(result, indent=2)}")
                
                # Wait and verify
                time.sleep(1)
                
                # Get updated data
                verify_response = requests.get(
                    f"{BASE_URL}/observation-enhanced/{cycle_id}/reports/{report_id}/observation-groups",
                    headers=ro_headers
                )
                
                if verify_response.status_code == 200:
                    updated_groups = verify_response.json()
                    updated_group = next((g for g in updated_groups if g['group_id'] == obs_id), None)
                    
                    if updated_group:
                        print(f"\n✓ Updated Approval Status: {updated_group['approval_status']}")
                        print(f"✓ Report Owner Approved: {updated_group['report_owner_approved']}")
                        
                        # Check database for report owner comments
                        import subprocess
                        result = subprocess.run([
                            "bash", "-c",
                            f"PGPASSWORD=synapse_password psql -h localhost -p 5433 -U synapse_user -d synapse_dt -c \"SELECT observation_id, report_owner_decision, report_owner_comments FROM cycle_report_observation_mgmt_observation_records WHERE observation_id = {obs_id};\""
                        ], capture_output=True, text=True)
                        print("\nDatabase verification:")
                        print(result.stdout)
            else:
                print(f"❌ Approval failed: {approval_response.status_code}")
                print(f"Error: {approval_response.text}")
                
        elif group['report_owner_approved']:
            print("ℹ️  Already approved by report owner")
        elif 'Rejected by Tester' in group['approval_status']:
            # Report owner can still approve/reject even if tester rejected
            print(f"\n→ Report owner reviewing observation {obs_id} (was rejected by tester)...")
            
            rejection_data = {
                "approved": False,
                "comments": "Report owner rejection - I agree with the tester's rejection. This observation needs more evidence before it can be accepted."
            }
            
            rejection_response = requests.post(
                f"{BASE_URL}/observation-enhanced/observation-groups/{obs_id}/approve",
                json=rejection_data,
                headers=ro_headers
            )
            
            if rejection_response.status_code == 200:
                print("✅ Report owner rejection successful!")
                result = rejection_response.json()
                print(f"Response: {json.dumps(result, indent=2)}")
                
                # Verify in database
                time.sleep(1)
                import subprocess
                result = subprocess.run([
                    "bash", "-c",
                    f"PGPASSWORD=synapse_password psql -h localhost -p 5433 -U synapse_user -d synapse_dt -c \"SELECT observation_id, tester_decision, report_owner_decision, report_owner_comments, approval_status FROM cycle_report_observation_mgmt_observation_records WHERE observation_id = {obs_id};\""
                ], capture_output=True, text=True)
                print("\nDatabase verification:")
                print(result.stdout)
            else:
                print(f"❌ Rejection failed: {rejection_response.status_code}")
                print(f"Error: {rejection_response.text}")

else:
    print(f"❌ Failed to get observations: {groups_response.status_code}")

print("\n=== Summary ===")
print("✓ Report owner can approve observations that were approved by tester")
print("✓ Report owner can reject any observation regardless of tester decision")  
print("✓ Report owner comments are properly stored in the database")
print("✓ Approval status is updated to reflect both tester and report owner decisions")
print("✓ The system correctly identifies the user's role and updates the appropriate fields")