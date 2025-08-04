#!/usr/bin/env python3
"""
Grant planning permissions to test users
"""

import asyncio
import aiohttp
import json

async def grant_planning_permissions():
    """Grant planning permissions using the API"""
    
    # First try to find an admin user - let's try cdo first
    login_data = {
        "email": "cdo@example.com",
        "password": "password123"
    }
    
    async with aiohttp.ClientSession() as session:
        # Login as CDO (Chief Data Officer - likely has admin privileges)
        async with session.post(
            "http://localhost:8000/api/v1/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status != 200:
                print(f"❌ CDO Login failed: {response.status}")
                # Try data provider instead
                login_data["email"] = "data.provider@example.com"
                async with session.post(
                    "http://localhost:8000/api/v1/auth/login",
                    json=login_data,
                    headers={"Content-Type": "application/json"}
                ) as response2:
                    if response2.status != 200:
                        print(f"❌ Data Provider Login failed: {response2.status}")
                        return
                    data = await response2.json()
            else:
                data = await response.json()
            
            token = data.get("access_token")
            if not token:
                print("❌ No token received")
                return
            
            print(f"✅ Authentication successful as {login_data['email']}")
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # Check current user's permissions
            async with session.get(
                "http://localhost:8000/api/v1/auth/me",
                headers=headers
            ) as response:
                if response.status == 200:
                    user_data = await response.json()
                    print(f"📊 Current user: {user_data.get('email')} - Role: {user_data.get('role_name')}")
                
            # Try to access data dictionary stats to see if we have permissions now
            print("🔍 Testing data dictionary access...")
            async with session.get(
                "http://localhost:8000/api/v1/data-dictionary/stats",
                headers=headers
            ) as response:
                if response.status == 200:
                    stats = await response.json()
                    print(f"✅ Data dictionary access works! Stats: {stats}")
                else:
                    error_data = await response.text()
                    print(f"❌ Data dictionary access failed: {response.status} - {error_data}")

if __name__ == "__main__":
    asyncio.run(grant_planning_permissions())