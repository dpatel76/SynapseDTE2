#!/usr/bin/env python3
"""Check workflow status and progress calculation"""

import requests
import json

def check_workflow_progress():
    """Check workflow status API response"""
    
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
        print(f"Current Phase: {workflow_data.get('current_phase', 'Unknown')}")
        
        print("\n📊 Phase Details:")
        for phase in workflow_data.get('phases', []):
            print(f"\n{phase['phase_name']}:")
            print(f"  - State: {phase.get('state', 'Unknown')}")
            print(f"  - Status: {phase.get('status', 'Unknown')}")
            print(f"  - Effective State: {phase.get('effective_state', 'Unknown')}")
            print(f"  - Progress: {phase.get('progress_percentage', 0)}%")
            print(f"  - Started At: {phase.get('started_at', 'Not Started')}")
            print(f"  - Completed At: {phase.get('completed_at', 'Not Completed')}")
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    print("Testing Workflow Progress API")
    print("=" * 60)
    check_workflow_progress()