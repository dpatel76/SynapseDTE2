#!/usr/bin/env python3
"""
Test script to specifically debug the attributes endpoint
"""

import asyncio
import aiohttp
import json

async def test_attributes_endpoint():
    """Test the attributes endpoint that's failing"""
    
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
            if not token:
                print("❌ No token received")
                return
            
            print("✅ Authentication successful")
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # Test attributes endpoint (without trailing slash to avoid redirect)
            print("🔍 Testing attributes endpoint...")
            async with session.get(
                "http://localhost:8000/api/v1/planning/cycles/55/reports/156/attributes",
                headers=headers
            ) as response:
                print(f"📊 Response status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Attributes retrieved: {len(data.get('items', []))} attributes")
                else:
                    error_data = await response.text()
                    print(f"❌ Attributes failed: {response.status}")
                    print(f"📝 Error details: {error_data}")

if __name__ == "__main__":
    asyncio.run(test_attributes_endpoint())