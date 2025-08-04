"""
Test script to verify sample selection versioning functionality
"""

import asyncio
import httpx
import json
from datetime import datetime

BASE_URL = "http://localhost:8001/api/v1"

# Test data
TEST_USER_EMAIL = "report.owner@example.com"
TEST_PASSWORD = "test123"
TESTER_EMAIL = "john.tester@example.com"
TESTER_PASSWORD = "test123"
CYCLE_ID = 13
REPORT_ID = 156

async def get_auth_token(email, password):
    """Get authentication token"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/auth/login",
            json={"email": email, "password": password}
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            print(f"Login failed for {email}: {response.status_code} - {response.text}")
            return None

async def test_sample_versioning():
    """Test sample selection versioning workflow"""
    # Get Report Owner token
    ro_token = await get_auth_token(TEST_USER_EMAIL, TEST_PASSWORD)
    if not ro_token:
        print("Failed to authenticate as Report Owner")
        return
    
    # Get Tester token
    tester_token = await get_auth_token(TESTER_EMAIL, TESTER_PASSWORD)
    if not tester_token:
        print("Failed to authenticate as Tester")
        return
    
    ro_headers = {"Authorization": f"Bearer {ro_token}"}
    tester_headers = {"Authorization": f"Bearer {tester_token}"}
    
    async with httpx.AsyncClient() as client:
        # 1. Get pending sample reviews as Report Owner
        print("\n1. Getting pending sample reviews...")
        response = await client.get(
            f"{BASE_URL}/sample-selection/pending-reviews",
            headers=ro_headers
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            reviews = response.json()
            print(f"Found {len(reviews)} pending reviews")
            for review in reviews:
                print(f"  - {review['report_name']} (Set: {review['set_id']}, Version: {review.get('version_number', 1)})")
        
        # 2. Test approval status check for a sample set
        if response.status_code == 200 and len(reviews) > 0:
            test_set_id = reviews[0]['set_id']
            print(f"\n2. Checking approval status for set {test_set_id}...")
            
            status_response = await client.get(
                f"{BASE_URL}/sample-selection/{CYCLE_ID}/reports/{REPORT_ID}/sample-sets/{test_set_id}/approval-status",
                headers=ro_headers
            )
            print(f"Status: {status_response.status_code}")
            if status_response.status_code == 200:
                status_data = status_response.json()
                print(f"Approval Status:")
                print(f"  - Has Decision: {status_data['has_decision']}")
                print(f"  - Can Approve: {status_data['can_approve']}")
                print(f"  - Current Status: {status_data['status']}")
                print(f"  - Version: {status_data['version_number']}")
                
                if status_data.get('latest_decision'):
                    print(f"  - Latest Decision: {status_data['latest_decision']['decision']}")
            
            # 3. Test approval with revision request
            if status_response.status_code == 200 and status_data['can_approve']:
                print(f"\n3. Requesting changes for sample set...")
                
                approval_response = await client.post(
                    f"{BASE_URL}/sample-selection/{CYCLE_ID}/reports/{REPORT_ID}/sample-sets/{test_set_id}/approve",
                    headers=ro_headers,
                    json={
                        "approval_decision": "Request Changes",
                        "feedback": "Please add more high-risk samples and improve coverage for edge cases",
                        "requested_changes": [
                            "Add at least 10 more high-risk samples