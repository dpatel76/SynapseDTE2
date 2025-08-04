#!/usr/bin/env python3
"""
Test PDE mapping endpoint to see what's causing the JavaScript error
"""

import asyncio
import aiohttp
import json

async def test_pde_mapping():
    """Test the PDE mapping endpoint"""
    
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
            
            # Test PDE mapping endpoint
            print("🔍 Testing PDE mapping endpoint...")
            async with session.get(
                "http://localhost:8000/api/v1/planning/cycles/55/reports/156/pde-mappings",
                headers=headers
            ) as response:
                print(f"📊 Response status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"📝 Response type: {type(data)}")
                    print(f"📝 Response content: {json.dumps(data, indent=2, default=str)}")
                else:
                    error_data = await response.text()
                    print(f"❌ PDE mapping failed: {response.status}")
                    print(f"📝 Error details: {error_data}")

if __name__ == "__main__":
    asyncio.run(test_pde_mapping())