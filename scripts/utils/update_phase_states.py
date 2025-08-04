#!/usr/bin/env python3
"""Update phase states to reflect correct status"""

import requests
import json

def update_phase_states():
    """Update phase states for Request Info, Testing, and Observations"""
    
    # Login as Test Manager
    print("1. Logging in as Test Manager...")
    login_response = requests.post(
        "http://localhost:8001/api/v1/auth/login",
        json={"email": "test.manager@example.com", "password": "password123"}
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return
        
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login successful")
    
    # Update phase states
    phases_to_update = [
        ("Request Info", "In Progress"),
        ("Testing", "In Progress"), 
        ("Observations", "In Progress")
    ]
    
    for phase_name, new_state in phases_to_update:
        print(f"\n2. Updating {phase_name} to {new_state}...")
        
        response = requests.put(
            f"http://localhost:8001/api/v1/cycle-reports/9/reports/156/phases/{phase_name}/state",
            headers=headers,
            json={
                "state": new_state,
                "notes": f"{phase_name} phase is currently active"
            }
        )
        
        if response.status_code == 200:
            print(f"✅ {phase_name} updated successfully")
            phase_data = response.json()
            print(f"   - State: {phase_data.get('state')}")
            print(f"   - Effective State: {phase_data.get('effective_state')}")
        else:
            print(f"❌ Failed to update {phase_name}: {response.status_code} - {response.text}")

if __name__ == "__main__":
    print("Updating Workflow Phase States")
    print("=" * 60)
    update_phase_states()