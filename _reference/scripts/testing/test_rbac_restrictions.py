#!/usr/bin/env python3

import asyncio
import aiohttp
import json

async def test_rbac_restrictions():
    """Test the RBAC restrictions system"""
    
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
                return
            
            login_result = await response.json()
            token = login_result.get("access_token")
            print(f"✅ Login successful")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get roles to test restrictions
        async with session.get(
            "http://localhost:8000/api/v1/admin/rbac/roles", 
            headers=headers
        ) as response:
            if response.status != 200:
                print(f"❌ Failed to get roles")
                return
            
            roles = await response.json()
            print(f"📊 Got {len(roles)} roles to test")
        
        # Test restrictions for each role
        for role in roles:
            role_id = role['role_id']
            role_name = role['role_name']
            
            print(f"\n🔍 Testing restrictions for {role_name}:")
            
            # Get restrictions for this role
            async with session.get(
                f"http://localhost:8000/api/v1/admin/rbac/roles/{role_id}/permissions/restrictions",
                headers=headers
            ) as response:
                if response.status == 200:
                    restrictions = await response.json()
                    print(f"  ✅ Allowed: {restrictions['allowed_count']} permissions")
                    print(f"  ❌ Forbidden: {restrictions['forbidden_count']} permissions")
                    print(f"  📝 Description: {restrictions['role_description']}")
                    
                    # Show sample allowed and forbidden permissions
                    if restrictions['allowed_permissions']:
                        print(f"  📋 Sample allowed: {', '.join(restrictions['allowed_permissions'][:3])}")
                    if restrictions['forbidden_permissions']:
                        print(f"  🚫 Sample forbidden: {', '.join(restrictions['forbidden_permissions'][:3])}")
                else:
                    print(f"  ❌ Failed to get restrictions: {response.status}")
        
        # Test trying to assign a forbidden permission (should fail)
        print(f"\n🧪 Testing forbidden permission assignment:")
        
        # Find a non-admin role
        test_role = None
        for role in roles:
            if role['role_name'] != 'Admin':
                test_role = role
                break
        
        if test_role:
            role_id = test_role['role_id']
            role_name = test_role['role_name']
            
            # Try to assign system:admin permission (should be forbidden for non-admin roles)
            # First, find the permission ID for system:admin
            async with session.get(
                "http://localhost:8000/api/v1/admin/rbac/permissions",
                headers=headers
            ) as response:
                if response.status == 200:
                    permissions = await response.json()
                    system_admin_perm = None
                    for perm in permissions:
                        if perm['resource'] == 'system' and perm['action'] == 'admin':
                            system_admin_perm = perm
                            break
                    
                    if system_admin_perm:
                        print(f"  Attempting to assign 'system:admin' to '{role_name}'...")
                        
                        async with session.post(
                            f"http://localhost:8000/api/v1/admin/rbac/roles/{role_id}/permissions/{system_admin_perm['permission_id']}",
                            headers=headers
                        ) as response:
                            if response.status == 400:
                                error_data = await response.json()
                                print(f"  ✅ Correctly blocked: {error_data.get('detail', 'Forbidden')}")
                            else:
                                print(f"  ❌ Should have been blocked but got status: {response.status}")
                    else:
                        print(f"  ❌ Could not find system:admin permission")

if __name__ == "__main__":
    asyncio.run(test_rbac_restrictions()) 