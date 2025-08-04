#!/usr/bin/env python3

import asyncio
import aiohttp
import json

async def test_permissions_api():
    """Test the permissions API endpoint"""
    
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
        
        # Test permissions endpoint
        headers = {"Authorization": f"Bearer {token}"}
        
        async with session.get(
            "http://localhost:8000/api/v1/admin/rbac/permissions", 
            headers=headers
        ) as response:
            print(f"📝 Permissions endpoint status: {response.status}")
            
            if response.status == 200:
                permissions_data = await response.json()
                print(f"✅ Permissions endpoint working!")
                print(f"📊 Got {len(permissions_data)} permissions")
                
                # Show first few permissions
                if permissions_data and len(permissions_data) > 0:
                    print(f"🔐 First 5 permissions:")
                    for i, perm in enumerate(permissions_data[:5]):
                        print(f"  {i+1}. {perm.get('resource')}:{perm.get('action')} - {perm.get('description', 'No description')}")
                
            else:
                text = await response.text()
                print(f"❌ Permissions endpoint failed: {text}")
        
        # Test roles endpoint
        async with session.get(
            "http://localhost:8000/api/v1/admin/rbac/roles", 
            headers=headers,
            params={"include_permissions": "true"}
        ) as response:
            print(f"\n📝 Roles endpoint status: {response.status}")
            
            if response.status == 200:
                roles_data = await response.json()
                print(f"✅ Roles endpoint working!")
                print(f"📊 Got {len(roles_data)} roles")
                
                # Show first role with permissions
                if roles_data and len(roles_data) > 0:
                    first_role = roles_data[0]
                    print(f"👤 First role: {first_role.get('role_name')}")
                    
                    # Check different permission fields
                    role_perms = first_role.get('role_permissions', [])
                    permissions = first_role.get('permissions', [])
                    
                    print(f"  - Has {len(role_perms)} role_permissions")
                    print(f"  - Has {len(permissions)} permissions")
                    
                    if permissions:
                        print(f"  - First few permissions:")
                        for i, perm in enumerate(permissions[:3]):
                            print(f"    {i+1}. {perm.get('resource')}:{perm.get('action')}")
                    else:
                        print(f"  - ⚠️  No permissions found")
                        print(f"  - Role data keys: {list(first_role.keys())}")
                        if role_perms:
                            print(f"  - role_permissions exists but permissions is empty")
                
            else:
                text = await response.text()
                print(f"❌ Roles endpoint failed: {text}")

if __name__ == "__main__":
    asyncio.run(test_permissions_api()) 