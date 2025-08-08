"""
Test sample generation and storage in WorkflowPhase metadata
"""
import asyncio
import httpx
from datetime import datetime, timezone
import json

# Configuration
BASE_URL = "http://localhost:8001/api/v1"
CYCLE_ID = 13  # Test Cycle 2.4 - Q2 2025
REPORT_ID = 156  # FR Y-14M Schedule D.1

async def get_auth_token():
    """Get authentication token"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{BASE_URL}/auth/login",
            json={"email": "tester@synapse.com", "password": "TestUser123!"}
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            print(f"Login failed: {response.status_code} - {response.text}")
            return None

async def test_sample_workflow():
    """Test the complete sample workflow"""
    token = await get_auth_token()
    if not token:
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # 1. Start the phase
        print("\n1. Starting Sample Selection phase...")
        response = await client.post(
            f"{BASE_URL}/sample-selection/cycles/{CYCLE_ID}/reports/{REPORT_ID}/start",
            headers=headers,
            json={
                "planned_start_date": datetime.now(timezone.utc).isoformat(),
                "notes": "Starting sample selection"
            }
        )
        print(f"Start phase response: {response.status_code}")
        if response.status_code != 200:
            print(f"Error: {response.text}")
        
        # 2. Generate samples
        print("\n2. Generating samples...")
        response = await client.post(
            f"{BASE_URL}/sample-selection/cycles/{CYCLE_ID}/reports/{REPORT_ID}/samples/generate",
            headers=headers,
            json={
                "sample_size": 5,
                "sample_type": "Population Sample",
                "regulatory_context": "FR Y-14M Schedule D.1 regulatory reporting"
            }
        )
        print(f"Generate samples response: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Generated {result.get('samples_generated', 0)} samples")
        else:
            print(f"Error: {response.text}")
        
        # 3. Get samples
        print("\n3. Getting samples...")
        response = await client.get(
            f"{BASE_URL}/sample-selection/cycles/{CYCLE_ID}/reports/{REPORT_ID}/samples",
            headers=headers
        )
        print(f"Get samples response: {response.status_code}")
        if response.status_code == 200:
            samples = response.json()["cycle_report_sample_selection_samples"]
            print(f"Found {len(samples)} samples")
            if samples:
                print("Sample IDs:")
                for sample in samples[:3]:  # Show first 3
                    print(f"  - {sample['sample_id']}: {sample['primary_key_value']}")
        else:
            print(f"Error: {response.text}")
        
        # 4. Get analytics
        print("\n4. Getting analytics...")
        response = await client.get(
            f"{BASE_URL}/sample-selection/cycles/{CYCLE_ID}/reports/{REPORT_ID}/samples/analytics",
            headers=headers
        )
        print(f"Get analytics response: {response.status_code}")
        if response.status_code == 200:
            analytics = response.json()
            print(f"Analytics:")
            print(f"  - Total samples: {analytics['total_samples']}")
            print(f"  - Phase status: {analytics['phase_status']}")
            print(f"  - Pending samples: {analytics['pending_samples']}")
        else:
            print(f"Error: {response.text}")

if __name__ == "__main__":
    asyncio.run(test_sample_workflow())