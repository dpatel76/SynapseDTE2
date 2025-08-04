#!/usr/bin/env python3
"""
Test script to verify observation management functionality
"""

import asyncio
import aiohttp
import json
from datetime import datetime

BASE_URL = "http://localhost:8001/api/v1"

# Test credentials
TEST_USER = {
    "email": "test_tester@synapse.com",
    "password": "TestUser123!"
}

# Test data
CYCLE_ID = 9
REPORT_ID = 156

async def login(session):
    """Login and get access token"""
    async with session.post(f"{BASE_URL}/auth/login", 
                          json={"email": TEST_USER["email"], "password": TEST_USER["password"]}) as resp:
        if resp.status == 200:
            data = await resp.json()
            return data["access_token"]
        else:
            print(f"Login failed: {resp.status}")
            text = await resp.text()
            print(f"Response: {text}")
            return None

async def get_failed_executions(session, token):
    """Get failed test executions"""
    headers = {"Authorization": f"Bearer {token}"}
    
    async with session.get(f"{BASE_URL}/testing-execution/{CYCLE_ID}/reports/{REPORT_ID}/executions", 
                          headers=headers) as resp:
        if resp.status == 200:
            executions = await resp.json()
            # Filter for failed/inconclusive
            failed = [e for e in executions if e.get("status") == "Completed" 
                     and e.get("result") in ["Fail", "Inconclusive"]]
            return failed
        else:
            print(f"Failed to get executions: {resp.status}")
            return []

async def create_observation_from_test(session, token, test_execution_id):
    """Create observation from failed test"""
    headers = {"Authorization": f"Bearer {token}"}
    
    data = {
        "test_execution_id": test_execution_id,
        "observation_title": "Test Data Quality Issue",
        "observation_description": "Value mismatch detected during testing",
        "observation_type": "DATA_QUALITY",
        "severity": "MEDIUM",
        "impact_description": "May affect regulatory reporting accuracy"
    }
    
    async with session.post(
        f"{BASE_URL}/observation-management/{CYCLE_ID}/reports/{REPORT_ID}/observations/from-test-result",
        headers=headers,
        json=data
    ) as resp:
        if resp.status == 200:
            result = await resp.json()
            return result
        else:
            print(f"Failed to create observation: {resp.status}")
            text = await resp.text()
            print(f"Response: {text}")
            return None

async def get_grouped_observations(session, token):
    """Get grouped observations"""
    headers = {"Authorization": f"Bearer {token}"}
    
    async with session.get(
        f"{BASE_URL}/observation-management/{CYCLE_ID}/reports/{REPORT_ID}/observations/grouped",
        headers=headers
    ) as resp:
        if resp.status == 200:
            return await resp.json()
        else:
            print(f"Failed to get grouped observations: {resp.status}")
            return []

async def resend_test_case(session, token, test_case_id):
    """Resend test case to data provider"""
    headers = {"Authorization": f"Bearer {token}"}
    
    data = {
        "test_case_id": test_case_id,
        "reason": "Documentation provided does not contain required information"
    }
    
    async with session.post(
        f"{BASE_URL}/testing-execution/{CYCLE_ID}/reports/{REPORT_ID}/resend-test-case",
        headers=headers,
        json=data
    ) as resp:
        if resp.status == 200:
            return await resp.json()
        else:
            print(f"Failed to resend test case: {resp.status}")
            text = await resp.text()
            print(f"Response: {text}")
            return None

async def main():
    """Main test function"""
    print("=" * 50)
    print("Testing Observation Management Functionality")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        # 1. Login
        print("\n1. Logging in...")
        token = await login(session)
        if not token:
            print("❌ Login failed")
            return
        print("✅ Login successful")
        
        # 2. Get failed test executions
        print("\n2. Getting failed test executions...")
        failed_executions = await get_failed_executions(session, token)
        print(f"✅ Found {len(failed_executions)} failed test executions")
        
        if failed_executions:
            # 3. Create observation from first failed test
            print("\n3. Creating observation from failed test...")
            first_failed = failed_executions[0]
            observation = await create_observation_from_test(session, token, first_failed["execution_id"])
            if observation:
                print(f"✅ Created observation: {observation['observation_id']}")
            else:
                print("❌ Failed to create observation")
            
            # 4. Get grouped observations
            print("\n4. Getting grouped observations...")
            grouped = await get_grouped_observations(session, token)
            print(f"✅ Found {len(grouped)} observation groups")
            for group in grouped:
                print(f"   - {group.get('attribute_name', 'Unknown')} ({group.get('observation_type')}): "
                      f"{group.get('total_count')} observations")
            
            # 5. Test resending test case
            # Note: This requires test_case_id which is not available in test execution data
            print("\n5. Testing resend to data provider...")
            print("⚠️  Skipping - test_case_id not available in test execution data")
        else:
            print("\n⚠️  No failed test executions found to test with")
            print("   Please run some test executions that fail first")
        
        print("\n" + "=" * 50)
        print("Test completed!")

if __name__ == "__main__":
    asyncio.run(main())