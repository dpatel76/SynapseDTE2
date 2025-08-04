#!/usr/bin/env python3
"""
Test all Planning page endpoints to ensure they work without fallback system
"""

import asyncio
import aiohttp
import json

async def test_planning_endpoints():
    """Test all planning endpoints used by the Planning page"""
    
    # First authenticate
    login_data = {
        "email": "data.provider@example.com",
        "password": "password123"
    }
    
    async with aiohttp.ClientSession() as session:
        # Login
        async with session.post(
            "http://localhost:8000/api/v1/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status != 200:
                print(f"❌ Login failed: {response.status}")
                return
            
            data = await response.json()
            token = data.get("access_token")
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            print(f"✅ Authentication successful")
            
            # Test all endpoints used by Planning page
            endpoints = [
                {
                    "name": "Attributes",
                    "url": "/api/v1/planning/cycles/55/reports/156/attributes",
                    "expected_fields": ["total", "attributes"]
                },
                {
                    "name": "PDE Mappings", 
                    "url": "/api/v1/planning/cycles/55/reports/156/pde-mappings",
                    "expected_fields": ["mappings", "total"]
                },
                {
                    "name": "Phase Status",
                    "url": "/api/v1/status/cycles/55/reports/156/phases/Planning/status",
                    "expected_fields": ["cycle_id", "report_id"]
                }
            ]
            
            for endpoint in endpoints:
                print(f"\n🔍 Testing {endpoint['name']} endpoint...")
                try:
                    async with session.get(
                        f"http://localhost:8000{endpoint['url']}",
                        headers=headers
                    ) as response:
                        print(f"📊 Response status: {response.status}")
                        
                        if response.status == 200:
                            data = await response.json()
                            print(f"✅ {endpoint['name']} endpoint working")
                            
                            # Check expected fields
                            for field in endpoint['expected_fields']:
                                if field in data:
                                    if field in ['attributes', 'mappings']:
                                        count = len(data[field]) if isinstance(data[field], list) else 'N/A'
                                        print(f"   📝 {field}: {count} items")
                                    else:
                                        print(f"   📝 {field}: {data[field]}")
                                else:
                                    print(f"   ⚠️ Missing expected field: {field}")
                        else:
                            error_data = await response.text()
                            print(f"❌ {endpoint['name']} failed: {response.status}")
                            print(f"   📝 Error: {error_data[:200]}...")
                            
                except Exception as e:
                    print(f"❌ {endpoint['name']} error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_planning_endpoints())