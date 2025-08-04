"""
Test script to verify enhanced sample selection feedback display
"""

import asyncio
import httpx
import json
from datetime import datetime

BASE_URL = "http://localhost:8001/api/v1"

# Test data
REPORT_OWNER_EMAIL = "report.owner@example.com"
REPORT_OWNER_PASSWORD = "test123"
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

async def test_feedback_display():
    """Test the enhanced feedback display functionality"""
    
    # Get tokens
    tester_token = await get_auth_token(TESTER_EMAIL, TESTER_PASSWORD)
    if not tester_token:
        print("Failed to authenticate as Tester")
        return
    
    tester_headers = {"Authorization": f"Bearer {tester_token}"}
    
    async with httpx.AsyncClient() as client:
        # 1. Get sample sets as Tester to see feedback
        print("\n1. Getting sample sets as Tester...")
        response = await client.get(
            f"{BASE_URL}/sample-selection/{CYCLE_ID}/reports/{REPORT_ID}/sample-sets",
            headers=tester_headers
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            sample_sets = response.json()
            print(f"Found {len(sample_sets)} sample sets")
            
            # Show version information
            for set_data in sample_sets:
                print(f"\nSample Set: {set_data['set_name']}")
                print(f"  - Status: {set_data['status']}")
                print(f"  - Version: {set_data.get('version_number', 1)}")
                print(f"  - Total Samples: {set_data['total_samples']}")
                
                # Check for feedback if status indicates it
                if set_data['status'] in ['Revision Required', 'Rejected', 'Approved']:
                    print(f"\n2. Checking feedback for set {set_data['set_id']}...")
                    
                    feedback_response = await client.get(
                        f"{BASE_URL}/sample-selection/{CYCLE_ID}/reports/{REPORT_ID}/sample-sets/{set_data['set_id']}/feedback",
                        headers=tester_headers
                    )
                    
                    if feedback_response.status_code == 200:
                        feedback = feedback_response.json()
                        print("Feedback found:")
                        print(f"  - Has Feedback: {feedback['has_feedback']}")
                        print(f"  - Decision: {feedback['feedback']['decision']}")
                        print(f"  - Feedback Text: {feedback['feedback']['feedback']}")
                        print(f"  - Reviewed By: {feedback['feedback']['approved_by']}")
                        print(f"  - Can Resubmit: {feedback['can_resubmit']}")
                        
                        if feedback.get('individual_sample_decisions'):
                            print(f"  - Individual Sample Decisions: {len(feedback['individual_sample_decisions'])} samples")
                            
                            # Count decisions
                            decisions = feedback['individual_sample_decisions']
                            approved = sum(1 for d in decisions.values() if d.get('decision') == 'Approved')
                            rejected = sum(1 for d in decisions.values() if d.get('decision') == 'Rejected')
                            changes = sum(1 for d in decisions.values() if d.get('decision') == 'Needs Changes')
                            
                            print(f"    - Approved: {approved}")
                            print(f"    - Rejected: {rejected}")
                            print(f"    - Needs Changes: {changes}")
                        
                        if feedback['feedback'].get('requested_changes'):
                            print(f"  - Requested Changes:")
                            for change in feedback['feedback']['requested_changes']:
                                print(f"    • {change}")
                    else:
                        print(f"No feedback found (Status: {feedback_response.status_code})")
        
        # 3. Test version history endpoint if available
        print("\n3. Testing version history...")
        if sample_sets and len(sample_sets) > 0:
            test_set = sample_sets[0]
            version_response = await client.get(
                f"{BASE_URL}/sample-selection/{CYCLE_ID}/reports/{REPORT_ID}/sample-sets/{test_set['set_id']}/versions",
                headers=tester_headers
            )
            
            if version_response.status_code == 200:
                versions = version_response.json()
                print(f"Version history for {test_set['set_name']}:")
                for v in versions:
                    print(f"  - Version {v['version_number']}: {v['status']} (Created: {v['created_at']})")
            else:
                print(f"Version history endpoint not available or returned {version_response.status_code}")

if __name__ == "__main__":
    print("Testing Enhanced Sample Selection Feedback Display")
    print("=" * 60)
    asyncio.run(test_feedback_display())