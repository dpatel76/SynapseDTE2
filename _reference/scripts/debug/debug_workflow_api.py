#!/usr/bin/env python3
"""Debug workflow API response structure"""

import requests
import json

def debug_workflow_api():
    """Debug workflow API response"""
    
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
        
        # Pretty print the full response
        print("\n📋 Full API Response:")
        print(json.dumps(workflow_data, indent=2))
        
        # Check first phase structure
        if workflow_data.get('phases'):
            print("\n📊 First Phase Structure:")
            print(json.dumps(workflow_data['phases'][0], indent=2))
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    print("Debugging Workflow API Response")
    print("=" * 60)
    debug_workflow_api()