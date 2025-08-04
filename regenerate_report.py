#!/usr/bin/env python3
"""Regenerate test report with all phase details"""

import requests
import json

# Test credentials
BASE_URL = "http://localhost:8000"
USERNAME = "test.manager@example.com"
PASSWORD = "password123"

def login():
    """Login and get JWT token"""
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"email": USERNAME, "password": PASSWORD}
    )
    if response.status_code == 200:
        token_data = response.json()
        return token_data["access_token"]
    else:
        print(f"Login failed: {response.status_code}")
        print(response.text)
        return None

def regenerate_report(token, cycle_id=21, report_id=156):
    """Regenerate the test report"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"\n🔄 Regenerating report for cycle {cycle_id}, report {report_id}...")
    
    # First, configure to include all sections
    config = {
        "include_executive_summary": True,
        "include_phase_artifacts": True,
        "include_detailed_observations": True,
        "include_metrics_dashboard": True
    }
    
    response = requests.put(
        f"{BASE_URL}/api/v1/test-report/{cycle_id}/reports/{report_id}/configure",
        headers=headers,
        json=config
    )
    
    if response.status_code == 200:
        print("✅ Configuration updated")
    else:
        print(f"❌ Failed to update config: {response.status_code}")
        return
    
    # Generate the report
    response = requests.post(
        f"{BASE_URL}/api/v1/test-report/{cycle_id}/reports/{report_id}/generate",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print("\n✅ Report regenerated successfully!")
        
        # Save the new report
        with open('regenerated_test_report.json', 'w') as f:
            json.dump(data, f, indent=2)
        
        # Check if phase details exist in formatted report
        if 'formatted_report' in data and 'phase_analysis' in data['formatted_report']:
            phase_analysis = data['formatted_report']['phase_analysis']
            if 'phases' in phase_analysis:
                phases = phase_analysis['phases']
                print(f"\n📊 Found {len(phases)} phases in report:")
                for phase in phases:
                    print(f"  - {phase.get('phase_name', 'Unknown')}")
                    if 'executive_summary' in phase:
                        print(f"    Summary: {phase['executive_summary'][:60]}...")
        
        # Check HTML content
        if 'formatted_report' in data and 'html' in data['formatted_report']:
            html = data['formatted_report']['html']
            phases_to_check = [
                'Planning Phase',
                'Data Profiling Phase', 
                'Scoping Phase',
                'Sample Selection Phase',
                'Request Info Phase',
                'Data Provider ID Phase',
                'Test Execution Phase',
                'Observations Management Phase'
            ]
            
            print("\n📄 HTML Content Check:")
            for phase in phases_to_check:
                if phase in html:
                    print(f"  ✓ {phase} found in HTML")
                else:
                    print(f"  ✗ {phase} NOT found in HTML")
        
    else:
        print(f"\n❌ Failed to generate report: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    print("🔐 Logging in...")
    token = login()
    if token:
        print("✅ Logged in successfully")
        regenerate_report(token)