#!/usr/bin/env python3
"""
Simple test for Data Profiling Phase
Tests just the Data Profiling phase operations
"""

import asyncio
import aiohttp
import json
from datetime import datetime

# API Base URL
BASE_URL = "http://localhost:8000/api/v1"

# Test user credentials
TEST_USERS = {
    "tester": {"username": "tester@synapse.com", "password": "TestUser123!"},
    "report_owner": {"username": "owner@synapse.com", "password": "TestUser123!"},
    "test_executive": {"username": "testmgr@synapse.com", "password": "TestUser123!"}
}

class DataProfilingSimpleTest:
    def __init__(self):
        self.session = None
        self.tokens = {}
        
    async def setup(self):
        """Setup test session and authenticate users"""
        self.session = aiohttp.ClientSession()
        
        # Authenticate all test users
        for role, creds in TEST_USERS.items():
            token = await self.authenticate(creds["username"], creds["password"])
            self.tokens[role] = token
            print(f"✓ Authenticated {role}: {creds['username']}")
    
    async def cleanup(self):
        """Cleanup test session"""
        if self.session:
            await self.session.close()
    
    async def authenticate(self, username, password):
        """Authenticate user and get token"""
        async with self.session.post(f"{BASE_URL}/auth/login", json={
            "email": username,
            "password": password
        }) as resp:
            if resp.status != 200:
                raise Exception(f"Authentication failed: {await resp.text()}")
            data = await resp.json()
            return data["access_token"]
    
    async def api_request(self, method, endpoint, token_role="tester", **kwargs):
        """Make API request with authentication"""
        headers = {
            "Authorization": f"Bearer {self.tokens[token_role]}",
            "Content-Type": "application/json"
        }
        if "headers" in kwargs:
            headers.update(kwargs["headers"])
            del kwargs["headers"]
        
        url = f"{BASE_URL}{endpoint}"
        async with self.session.request(method, url, headers=headers, **kwargs) as resp:
            text = await resp.text()
            if resp.status >= 400:
                print(f"❌ API Error {resp.status}: {text}")
                raise Exception(f"API request failed: {text}")
            return json.loads(text) if text else None
    
    async def test_data_profiling_endpoints(self):
        """Test Data Profiling endpoints with hardcoded IDs"""
        print("\n=== Testing Data Profiling Endpoints ===\n")
        
        # Use existing cycle and report IDs
        cycle_id = 1  # Assuming there's at least one cycle
        report_id = 1  # Assuming there's at least one report
        
        # 1. Start Data Profiling
        print("1. Starting Data Profiling phase...")
        try:
            await self.api_request("POST", f"/data-profiling/cycles/{cycle_id}/reports/{report_id}/start")
            print("   ✓ Data Profiling phase started")
        except Exception as e:
            print(f"   ✗ Failed to start: {e}")
        
        # 2. Get status
        print("\n2. Getting Data Profiling status...")
        try:
            status = await self.api_request("GET", f"/data-profiling/cycles/{cycle_id}/reports/{report_id}/status")
            print(f"   ✓ Phase status: {status['phase_status']}")
            print(f"   ✓ Current step: {status['current_step']}")
        except Exception as e:
            print(f"   ✗ Failed to get status: {e}")
        
        # 3. Request data
        print("\n3. Requesting data from Report Owner...")
        try:
            await self.api_request("POST", f"/data-profiling/cycles/{cycle_id}/reports/{report_id}/request-data", json={
                "message": "Please upload test data files"
            })
            print("   ✓ Data request sent")
        except Exception as e:
            print(f"   ✗ Failed to request data: {e}")
        
        # 4. Upload file as Report Owner
        print("\n4. Uploading data file (as Report Owner)...")
        try:
            csv_content = """Customer_ID,Account_Balance,Transaction_Date
1,1000.50,2024-01-01
2,2500.75,2024-01-02
3,500.00,2024-01-03"""
            
            form_data = aiohttp.FormData()
            form_data.add_field('file', csv_content.encode(), filename='test_data.csv', content_type='text/csv')
            form_data.add_field('delimiter', ',')
            
            headers = {"Authorization": f"Bearer {self.tokens['report_owner']}"}
            async with self.session.post(
                f"{BASE_URL}/data-profiling/cycles/{cycle_id}/reports/{report_id}/upload-file",
                data=form_data,
                headers=headers
            ) as resp:
                if resp.status != 200:
                    raise Exception(f"File upload failed: {await resp.text()}")
                upload_result = await resp.json()
            
            print(f"   ✓ File uploaded: {upload_result['file_name']}")
        except Exception as e:
            print(f"   ✗ Failed to upload file: {e}")
        
        # 5. List files
        print("\n5. Listing uploaded files...")
        try:
            files = await self.api_request("GET", f"/data-profiling/cycles/{cycle_id}/reports/{report_id}/files")
            print(f"   ✓ Found {len(files)} files")
            for file in files:
                print(f"      - {file['file_name']} ({file['row_count']} rows)")
        except Exception as e:
            print(f"   ✗ Failed to list files: {e}")
        
        print("\n✅ Data Profiling endpoint test completed!")
    
    async def run(self):
        """Run all tests"""
        try:
            await self.setup()
            await self.test_data_profiling_endpoints()
        except Exception as e:
            print(f"\n❌ Test failed: {str(e)}")
            raise
        finally:
            await self.cleanup()


async def main():
    """Main entry point"""
    print("=" * 80)
    print("Data Profiling Simple Test")
    print("=" * 80)
    
    test = DataProfilingSimpleTest()
    await test.run()


if __name__ == "__main__":
    asyncio.run(main())