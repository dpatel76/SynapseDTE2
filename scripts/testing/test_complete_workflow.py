"""
Test complete sample selection workflow with metadata storage
"""
import asyncio
import httpx
from datetime import datetime, timezone
import json

# Configuration
BASE_URL = "http://localhost:8001/api/v1"
CYCLE_ID = 13  # Test Cycle 2.4 - Q2 2025
REPORT_ID = 156  # FR Y-14M Schedule D.1

async def get_auth_token(email, password):
    """Get authentication token"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{BASE_URL}/auth/login",
            json={"email": email, "password": password}
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            print(f"Login failed for {email}: {response.status_code} - {response.text}")
            return None

async def test_complete_workflow():
    """Test the complete sample selection workflow"""
    # Login as tester
    tester_token = await get_auth_token("tester@synapse.com", "TestUser123!")
    if not tester_token:
        return
    
    tester_headers = {"Authorization": f"Bearer {tester_token}"}
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # 1. Get initial analytics
        print("\n1. Initial analytics...")
        response = await client.get(
            f"{BASE_URL}/sample-selection/cycles/{CYCLE_ID}/reports/{REPORT_ID}/samples/analytics",
            headers=tester_headers
        )
        if response.status_code == 200:
            analytics = response.json()
            print(f"   Phase status: {analytics['phase_status']}")
            print(f"   Total samples: {analytics['total_samples']}")
        
        # 2. Generate more samples
        print("\n2. Generating additional samples...")
        response = await client.post(
            f"{BASE_URL}/sample-selection/cycles/{CYCLE_ID}/reports/{REPORT_ID}/samples/generate",
            headers=tester_headers,
            json={
                "sample_size": 3,
                "sample_type": "Population Sample",
                "regulatory_context": "FR Y-14M Schedule D.1 testing"
            }
        )
        if response.status_code == 200:
            result = response.json()
            print(f"   Generated {result.get('samples_generated', 0)} new samples")
        
        # 3. Get all samples
        print("\n3. Getting all samples...")
        response = await client.get(
            f"{BASE_URL}/sample-selection/cycles/{CYCLE_ID}/reports/{REPORT_ID}/samples",
            headers=tester_headers
        )
        if response.status_code == 200:
            samples = response.json()["cycle_report_sample_selection_samples"]
            print(f"   Total samples: {len(samples)}")
            print(f"   Sample IDs: {[s['sample_id'] for s in samples[:3]]}")
            
            # 4. Update decisions on some samples
            print("\n4. Updating tester decisions...")
            sample_ids = [s['sample_id'] for s in samples[:3]]
            for i, sample_id in enumerate(sample_ids):
                decision = "include" if i % 2 == 0 else "exclude"
                response = await client.put(
                    f"{BASE_URL}/sample-selection/cycles/{CYCLE_ID}/reports/{REPORT_ID}/samples/{sample_id}/decision",
                    headers=tester_headers,
                    json={
                        "decision": decision,
                        "notes": f"Test decision for sample {i+1}"
                    }
                )
                if response.status_code == 200:
                    print(f"   Updated sample {i+1}: {decision}")
            
            # 5. Submit samples for approval
            print("\n5. Submitting samples for approval...")
            response = await client.post(
                f"{BASE_URL}/sample-selection/cycles/{CYCLE_ID}/reports/{REPORT_ID}/samples/submit",
                headers=tester_headers,
                json={
                    "sample_ids": sample_ids,
                    "notes": "Submitting test samples for approval"
                }
            )
            if response.status_code == 200:
                result = response.json()
                print(f"   Submitted {result['samples_submitted']} samples")
                print(f"   Submission ID: {result['submission_id']}")
                print(f"   Version: {result['version_number']}")
            else:
                print(f"   Error: {response.status_code} - {response.text}")
        
        # 6. Login as report owner
        print("\n6. Switching to Report Owner...")
        owner_token = await get_auth_token("owner@synapse.com", "TestUser123!")
        if not owner_token:
            print("   Failed to login as report owner")
            return
        
        owner_headers = {"Authorization": f"Bearer {owner_token}"}
        
        # 7. Get pending reviews
        print("\n7. Getting pending reviews...")
        response = await client.get(
            f"{BASE_URL}/sample-selection/pending-reviews",
            headers=owner_headers
        )
        if response.status_code == 200:
            reviews = response.json()
            print(f"   Found {len(reviews)} pending reviews")
            if reviews:
                print(f"   First review: Cycle {reviews[0]['cycle_id']}, Report {reviews[0]['report_id']}")
        
        # 8. Review and approve samples
        print("\n8. Approving samples...")
        response = await client.post(
            f"{BASE_URL}/sample-selection/cycles/{CYCLE_ID}/reports/{REPORT_ID}/samples/review",
            headers=owner_headers,
            json={
                "decision": "approved",
                "feedback": "Samples look good for testing"
            }
        )
        if response.status_code == 200:
            result = response.json()
            print(f"   {result['message']}")
        else:
            print(f"   Error: {response.status_code} - {response.text}")
        
        # 9. Final analytics
        print("\n9. Final analytics...")
        response = await client.get(
            f"{BASE_URL}/sample-selection/cycles/{CYCLE_ID}/reports/{REPORT_ID}/samples/analytics",
            headers=tester_headers
        )
        if response.status_code == 200:
            analytics = response.json()
            print(f"   Phase status: {analytics['phase_status']}")
            print(f"   Total samples: {analytics['total_samples']}")
            print(f"   Approved samples: {analytics['approved_samples']}")
            print(f"   Can complete phase: {analytics['can_complete_phase']}")

if __name__ == "__main__":
    asyncio.run(test_complete_workflow())