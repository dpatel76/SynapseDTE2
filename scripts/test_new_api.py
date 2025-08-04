#!/usr/bin/env python3
"""Test the new report inventory API"""

import requests
import json

# Base URL for the API
BASE_URL = "http://localhost:8000/api/v1"

# Test credentials (adjust as needed)
TEST_USER = "admin@example.com"
TEST_PASSWORD = "admin123"

def get_auth_token():
    """Get authentication token"""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={
            "username": TEST_USER,
            "password": TEST_PASSWORD
        }
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Login failed: {response.status_code} - {response.text}")
        return None

def test_report_inventory():
    """Test report inventory endpoints"""
    token = get_auth_token()
    if not token:
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Create a new report
    print("\n1. Creating new report...")
    new_report = {
        "report_number": "RPT-2025-001",
        "report_name": "Monthly Sales Report",
        "description": "Monthly sales metrics and analysis",
        "frequency": "Monthly",
        "business_unit": "Sales",
        "regulatory_requirement": False,
        "status": "Active"
    }
    
    response = requests.post(
        f"{BASE_URL}/report-inventory/",
        json=new_report,
        headers=headers
    )
    
    if response.status_code == 201:
        report = response.json()
        print(f"✓ Report created: {report['report_number']}")
        report_id = report['id']
    else:
        print(f"✗ Failed to create report: {response.status_code} - {response.text}")
        return
    
    # 2. Get all reports
    print("\n2. Getting all reports...")
    response = requests.get(
        f"{BASE_URL}/report-inventory/",
        headers=headers
    )
    
    if response.status_code == 200:
        reports = response.json()
        print(f"✓ Found {len(reports)} reports")
    else:
        print(f"✗ Failed to get reports: {response.status_code}")
    
    # 3. Get specific report
    print(f"\n3. Getting report {report_id}...")
    response = requests.get(
        f"{BASE_URL}/report-inventory/{report_id}",
        headers=headers
    )
    
    if response.status_code == 200:
        report = response.json()
        print(f"✓ Retrieved report: {report['report_name']}")
    else:
        print(f"✗ Failed to get report: {response.status_code}")
    
    # 4. Update report
    print(f"\n4. Updating report {report_id}...")
    update_data = {
        "description": "Updated monthly sales metrics and detailed analysis",
        "regulatory_requirement": True
    }
    
    response = requests.put(
        f"{BASE_URL}/report-inventory/{report_id}",
        json=update_data,
        headers=headers
    )
    
    if response.status_code == 200:
        report = response.json()
        print(f"✓ Report updated: regulatory_requirement = {report['regulatory_requirement']}")
    else:
        print(f"✗ Failed to update report: {response.status_code}")
    
    # 5. Archive report (soft delete)
    print(f"\n5. Archiving report {report_id}...")
    response = requests.delete(
        f"{BASE_URL}/report-inventory/{report_id}",
        headers=headers
    )
    
    if response.status_code == 200:
        print(f"✓ Report archived successfully")
    else:
        print(f"✗ Failed to archive report: {response.status_code}")

if __name__ == "__main__":
    print("Testing Report Inventory API...")
    print("=" * 50)
    test_report_inventory()
    print("\n" + "=" * 50)
    print("Test completed!")