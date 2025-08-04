#!/usr/bin/env python3
"""
Test data owner dashboard API endpoints
"""
import asyncio
import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"

# Get test credentials
data_owner_credentials = {
    "email": "dataowner@synapse.com",
    "password": "password123"
}

async def main():
    # Login as data owner
    login_response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={
            "email": data_owner_credentials["email"],
            "password": data_owner_credentials["password"]
        }
    )
    
    if login_response.status_code != 200:
        print(f"Login failed: {login_response.text}")
        return
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print("Login successful!")
    
    # Get test cases assigned to data owner
    test_cases_response = requests.get(
        f"{BASE_URL}/api/v1/request-info/data-owner/test-cases",
        headers=headers
    )
    
    if test_cases_response.status_code != 200:
        print(f"Failed to get test cases: {test_cases_response.text}")
        return
    
    data = test_cases_response.json()
    print(f"\nData Owner Dashboard Data:")
    print(f"Total test cases: {data.get('total_assigned', 0)}")
    print(f"Submitted: {data.get('total_submitted', 0)}")
    print(f"Pending: {data.get('total_pending', 0)}")
    print(f"Overdue: {data.get('total_overdue', 0)}")
    
    test_cases = data.get('test_cases', [])
    print(f"\nTest cases returned: {len(test_cases)}")
    
    if test_cases:
        print("\nFirst test case details:")
        tc = test_cases[0]
        print(json.dumps({
            "test_case_id": tc.get("test_case_id"),
            "attribute_name": tc.get("attribute_name"),
            "status": tc.get("status"),
            "submission_count": tc.get("submission_count"),
            "submission_deadline": tc.get("submission_deadline"),
            "has_submissions": tc.get("has_submissions"),
            "document_count": tc.get("document_count")  # Check if this field exists
        }, indent=2))
        
        # Check evidence for first test case
        tc_id = tc.get("test_case_id")
        if tc_id:
            evidence_response = requests.get(
                f"{BASE_URL}/api/v1/request-info/test-cases/{tc_id}/evidence",
                headers=headers
            )
            
            if evidence_response.status_code == 200:
                evidence_data = evidence_response.json()
                print(f"\nEvidence for test case {tc_id}:")
                print(f"Has evidence: {evidence_data.get('has_evidence', False)}")
                evidence_list = evidence_data.get('evidence', [])
                if isinstance(evidence_list, list):
                    print(f"Evidence count: {len(evidence_list)}")
                else:
                    print("Evidence data format unexpected")

if __name__ == "__main__":
    asyncio.run(main())