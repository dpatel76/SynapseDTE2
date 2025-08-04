#!/usr/bin/env python3
"""Test workflow progress and phase status synchronization fixes"""

import requests
import json
from datetime import datetime

def test_workflow_fixes():
    """Test workflow status fixes"""
    
    # Login as Tester
    print("1. Logging in as Tester...")
    login_response = requests.post(
        "http://localhost:8001/api/v1/auth/login",
        json={"email": "tester@example.com", "password": "password123"}
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return
        
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login successful")
    
    # Get workflow status
    print("\n2. Getting workflow status for cycle 9, report 156...")
    response = requests.get(
        "http://localhost:8001/api/v1/cycle-reports/9/reports/156/workflow-status",
        headers=headers
    )
    
    if response.status_code == 200:
        workflow_data = response.json()
        print("\n📋 Workflow Status:")
        print(f"Overall Progress: {workflow_data.get('overall_progress', 0)}%")
        print(f"Overall State: {workflow_data.get('overall_state', 'Unknown')}")
        print(f"Current Phase: {workflow_data.get('current_phase', 'None')}")
        print(f"Completed Phases: {workflow_data.get('completed_phases', 0)}/{workflow_data.get('total_phases', 0)}")
        
        print("\n📊 Phase Details:")
        for phase in workflow_data.get('phases', []):
            print(f"\n{phase['phase_name']}:")
            print(f"  - State: {phase.get('state', 'Unknown')}")
            print(f"  - Effective State: {phase.get('effective_state', 'Unknown')}")
            print(f"  - Progress: {phase.get('progress_percentage', 0)}%")
            print(f"  - Schedule Status: {phase.get('schedule_status', 'Unknown')}")
            print(f"  - Started At: {phase.get('started_at', 'Not Started')}")
            print(f"  - Completed At: {phase.get('completed_at', 'Not Completed')}")
            
        # Check specific issues
        print("\n🔍 Checking for reported issues:")
        for phase in workflow_data.get('phases', []):
            # Check if completed phases show 100%
            if phase.get('effective_state') == 'Complete' and phase.get('progress_percentage', 0) < 100:
                print(f"❌ {phase['phase_name']} is completed but shows {phase.get('progress_percentage', 0)}% progress")
            elif phase.get('effective_state') == 'Complete':
                print(f"✅ {phase['phase_name']} correctly shows 100% when completed")
                
            # Check if phases show correct status
            if phase['phase_name'] in ['Request Info', 'Testing', 'Observations']:
                if phase.get('state') == 'In Progress' and phase.get('effective_state') == 'Not Started':
                    print(f"❌ {phase['phase_name']} incorrectly shows as 'In Progress' when it should be 'Not Started'")
                elif phase.get('state') == phase.get('effective_state'):
                    print(f"✅ {phase['phase_name']} status correctly synchronized: {phase.get('state')}")
                    
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")
        
    # Test phase details endpoint
    print("\n3. Testing individual phase status...")
    test_phases = ['Planning', 'Scoping', 'Data Provider ID', 'Sample Selection', 
                   'Request Info', 'Testing', 'Observations']
    
    for phase_name in test_phases:
        response = requests.get(
            f"http://localhost:8001/api/v1/cycle-reports/9/reports/156/phases/{phase_name}",
            headers=headers
        )
        if response.status_code == 200:
            phase_data = response.json()
            print(f"\n{phase_name}: State={phase_data.get('state')}, Status={phase_data.get('status')}")

if __name__ == "__main__":
    print("Testing Workflow Progress and Status Fixes")
    print("=" * 60)
    test_workflow_fixes()