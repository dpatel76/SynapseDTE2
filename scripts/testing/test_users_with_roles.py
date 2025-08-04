#!/usr/bin/env python3

import asyncio
import aiohttp
import json

async def test_users_with_roles():
    """Test the users endpoint with include_roles parameter"""
    
    # First login to get token
    async with aiohttp.ClientSession() as session:
        # Login
        login_data = {
            "email": "admin@synapsedt.com",
            "password": "password123"
        }
        
        async with session.post("http://localhost:8000/api/v1/auth/login", json=login_data) as response:
            if response.status != 200:
                print(f"❌ Login failed: {response.status}")
                text = await response.text()
                print(f"Response: {text}")
                return
            
            login_result = await response.json()
            token = login_result.get("access_token")
            print(f"✅ Login successful")
        
        # Test users endpoint with include_roles
        headers = {"Authorization": f"Bearer {token}"}
        
        async with session.get(
            "http://localhost:8000/api/v1/users", 
            headers=headers,
            params={"include_roles": "true", "limit": 5}
        ) as response:
            print(f"📝 Users endpoint status: {response.status}")
            
            if response.status == 200:
                users_data = await response.json()
                print(f"✅ Users with roles endpoint working!")
                print(f"📊 Got {len(users_data)} users")
                
                # Show first user structure
                if users_data and len(users_data) > 0:
                    print(f"👤 First user structure:")
                    first_user = users_data[0]
                    print(f"  - user_id: {first_user.get('user_id')}")
                    print(f"  - email: {first_user.get('email')}")
                    print(f"  - full_name: {first_user.get('full_name')}")
                    print(f"  - traditional role: {first_user.get('role')}")
                    print(f"  - RBAC roles: {len(first_user.get('roles', []))} roles")
                    
                    for role in first_user.get('roles', []):
                        print(f"    * {role.get('role_name')} (ID: {role.get('role_id')})")
                
            else:
                text = await response.text()
                print(f"❌ Users endpoint failed: {text}")

if __name__ == "__main__":
    asyncio.run(test_users_with_roles()) 