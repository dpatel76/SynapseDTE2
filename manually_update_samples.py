#\!/usr/bin/env python3
"""
Manually update samples with report owner decisions to fix the issue
"""

import requests
import json

# Login as admin/tester
login_response = requests.post(
    'http://localhost:8000/api/v1/auth/login',
    json={'email': 'tester@example.com', 'password': 'password123'}
)
token = login_response.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# The decisions from the assignment completion data
decisions = {
    'C55_R156_S001': 'rejected',
    'C55_R156_S002': 'rejected', 
    'C55_R156_S003': 'approved',
    'C55_R156_S004': 'approved',
    'C55_R156_S005': 'approved',
    'C55_R156_S006': 'approved'
}

feedback = {
    'C55_R156_S001': 'Not a good sample',
    'C55_R156_S002': 'Not a goo sample'
}

print("Updating samples with report owner decisions...")

# Use bulk operation endpoint to update decisions
for sample_id, decision in decisions.items():
    print(f"\nUpdating {sample_id} to {decision}...")
    
    # Use the bulk operation endpoint
    response = requests.post(
        'http://localhost:8000/api/v1/sample-selection/cycles/55/reports/156/samples/bulk-operation',
        headers=headers,
        json={
            'action': 'decide',
            'sample_ids': [sample_id],
            'decision': decision,
            'notes': feedback.get(sample_id, ''),
            'role': 'Report Owner'  # Force report owner role
        }
    )
    
    if response.status_code == 200:
        print(f"  ✓ Updated successfully")
    else:
        print(f"  ✗ Failed: {response.status_code}")
        print(f"    {response.text}")

# Check the results
print("\n\nChecking updated samples...")
samples_response = requests.get(
    'http://localhost:8000/api/v1/sample-selection/cycles/55/reports/156/samples?version=1',
    headers=headers
)

if samples_response.status_code == 200:
    samples = samples_response.json()['samples']
    for sample in samples:
        print(f"  - {sample['sample_id']}: report_owner={sample.get('report_owner_decision')}")
