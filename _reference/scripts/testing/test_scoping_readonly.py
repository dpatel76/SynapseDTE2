#!/usr/bin/env python3
"""
Test script to verify scoping page read-only behavior
"""

import asyncio
import httpx
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_CYCLE_ID = 1
TEST_REPORT_ID = 1

# Test user credentials
TESTER_EMAIL = "tester1@synapse.com"
TESTER_PASSWORD = "password123"
REPORT_OWNER_EMAIL = "report_owner1@synapse.com"
REPORT_OWNER_PASSWORD = "password123"


async def login(email: str, password: str) -> str:
    """Login and return access token"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/v1/auth/login",
            data={"username": email, "password": password}
        )
        response.raise_for_status()
        return response.json()["access_token"]


async def get_scoping_status(token: str):
    """Get current scoping phase status"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/v1/scoping/cycles/{TEST_CYCLE_ID}/reports/{TEST_REPORT_ID}/status",
            headers={"Authorization": f"Bearer {token}"}
        )
        response.raise_for_status()
        return response.json()


async def get_scoping_feedback(token: str):
    """Get scoping feedback"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/v1/scoping/cycles/{TEST_CYCLE_ID}/reports/{TEST_REPORT_ID}/feedback",
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()


async def get_scoping_versions(token: str):
    """Get scoping version history"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/v1/scoping/cycles/{TEST_CYCLE_ID}/reports/{TEST_REPORT_ID}/versions",
            headers={"Authorization": f"Bearer {token}"}
        )
        response.raise_for_status()
        return response.json()


async def submit_scoping_decisions(token: str, decisions: list, notes: str = "Test submission"):
    """Submit scoping decisions"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/v1/scoping/cycles/{TEST_CYCLE_ID}/reports/{TEST_REPORT_ID}/decisions",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "decisions": decisions,
                "confirm_submission": True,
                "submission_notes": notes
            }
        )
        response.raise_for_status()
        return response.json()


async def review_scoping_submission(token: str, decision: str, comments: str):
    """Review scoping submission as Report Owner"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/v1/scoping/cycles/{TEST_CYCLE_ID}/reports/{TEST_REPORT_ID}/review",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "review_decision": decision,
                "review_comments": comments
            }
        )
        response.raise_for_status()
        return response.json()


async def main():
    print("🧪 Testing Scoping Page Read-Only Behavior")
    print("=" * 50)
    
    # Login as tester
    print("\n1. Logging in as Tester...")
    tester_token = await login(TESTER_EMAIL, TESTER_PASSWORD)
    print("✅ Tester logged in successfully")
    
    # Check initial status
    print("\n2. Checking initial scoping status...")
    status = await get_scoping_status(tester_token)
    print(f"   Phase Status: {status.get('phase_status')}")
    print(f"   Has Submission: {status.get('has_submission', False)}")
    print(f"   Needs Revision: {status.get('needs_revision', False)}")
    print(f"   Current Version: {status.get('current_version', 0)}")
    
    # Check if we can submit
    if not status.get('has_submission'):
        print("\n3. No submission exists - creating initial submission...")
        
        # Create sample decisions
        decisions = [
            {
                "attribute_id": 1,
                "decision": "Accept",
                "final_scoping": True,
                "tester_rationale": "Selected for testing",
                "override_reason": None
            },
            {
                "attribute_id": 2,
                "decision": "Decline",
                "final_scoping": False,
                "tester_rationale": "Not selected for testing",
                "override_reason": None
            }
        ]
        
        try:
            submission_result = await submit_scoping_decisions(tester_token, decisions, "Initial test submission")
            print(f"✅ Submission created successfully (Version {submission_result.get('version', 1)})")
        except Exception as e:
            print(f"❌ Failed to submit: {e}")
            return
    
    # Check status after submission
    print("\n4. Checking status after submission...")
    status = await get_scoping_status(tester_token)
    print(f"   Has Submission: {status.get('has_submission', False)}")
    print(f"   Submission Status: {status.get('submission_status')}")
    print(f"   Current Version: {status.get('current_version', 0)}")
    
    # Check feedback
    print("\n5. Checking feedback...")
    feedback = await get_scoping_feedback(tester_token)
    if feedback:
        print(f"   Can Resubmit: {feedback.get('can_resubmit', False)}")
        print(f"   Submission Version: {feedback.get('submission_version', 0)}")
        print(f"   Review Decision: {feedback.get('review_decision')}")
    else:
        print("   No feedback available")
    
    # Check version history
    print("\n6. Checking version history...")
    versions = await get_scoping_versions(tester_token)
    print(f"   Total Versions: {versions.get('total_versions', 0)}")
    for v in versions.get('versions', []):
        print(f"   - Version {v.get('version')}: {v.get('status')} ({v.get('submitted_at')})")
    
    # Login as Report Owner
    print("\n7. Logging in as Report Owner...")
    owner_token = await login(REPORT_OWNER_EMAIL, REPORT_OWNER_PASSWORD)
    print("✅ Report Owner logged in successfully")
    
    # Request revision
    print("\n8. Requesting revision as Report Owner...")
    try:
        review_result = await review_scoping_submission(
            owner_token, 
            "Revision Required",
            "Please include more attributes for comprehensive testing coverage."
        )
        print("✅ Revision requested successfully")
    except Exception as e:
        print(f"❌ Failed to request revision: {e}")
    
    # Check status after revision request
    print("\n9. Checking status after revision request (as Tester)...")
    status = await get_scoping_status(tester_token)
    print(f"   Needs Revision: {status.get('needs_revision', False)}")
    print(f"   Review Comments: {status.get('review_comments')}")
    
    # Check feedback after revision
    feedback = await get_scoping_feedback(tester_token)
    if feedback:
        print(f"   Can Resubmit: {feedback.get('can_resubmit', False)}")
    
    print("\n✅ Test Summary:")
    print("   - Page should be read-only after submission")
    print("   - Page should allow editing when revision is requested")
    print("   - Version selector should show submission history")
    print("   - Toggles should be disabled when viewing submitted versions")
    
    print("\n🎯 Frontend Behavior to Verify:")
    print("   1. After submission: All controls should be disabled")
    print("   2. Version selector should appear showing v1")
    print("   3. After revision request: Controls should be re-enabled")
    print("   4. Submission button should say 'Resubmit Scoping Decisions'")
    print("   5. Warning banner should show revision is requested")


if __name__ == "__main__":
    asyncio.run(main())