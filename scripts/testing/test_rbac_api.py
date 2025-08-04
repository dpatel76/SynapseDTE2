#!/usr/bin/env python3
"""
RBAC API Integration Tests
Tests the admin RBAC endpoints
"""

import asyncio
import httpx
import json
from typing import Dict, Any

# Test configuration
BASE_URL = "http://localhost:8000"
ADMIN_EMAIL = "admin@company.com"
ADMIN_PASSWORD = "admin123"

# Test results tracking
test_results = []


class RBACAPITester:
    def __init__(self):
        self.client = httpx.AsyncClient(base_url=BASE_URL)
        self.token = None
        self.headers = {}
        
    async def setup(self):
        """Login and set auth headers"""
        print("🔐 Authenticating as admin...")
        response = await self.client.post(
            "/api/v1/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        if response.status_code == 200:
            data = response.json()
            self.token = data["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
            print("✅ Authentication successful")
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            raise Exception("Failed to authenticate")
    
    async def test_list_permissions(self):
        """Test: List all permissions"""
        print("\n📋 Test: List Permissions")
        response = await self.client.get(
            "/api/v1/admin/rbac/permissions",
            headers=self.headers
        )
        
        if response.status_code == 200:
            permissions = response.json()
            print(f"✅ Found {len(permissions)} permissions")
            # Show first 5
            for perm in permissions[:5]:
                print(f"  - {perm['resource']}:{perm['action']}")
            return True, permissions
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return False, None
    
    async def test_create_permission(self):
        """Test: Create a new permission"""
        print("\n➕ Test: Create Permission")
        
        test_permission = {
            "resource": "test_module",
            "action": "test_action",
            "description": "Test permission created by API test"
        }
        
        response = await self.client.post(
            "/api/v1/admin/rbac/permissions",
            headers=self.headers,
            json=test_permission
        )
        
        if response.status_code == 200:
            created = response.json()
            print(f"✅ Created permission: {created['resource']}:{created['action']} (ID: {created['permission_id']})")
            return True, created
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return False, None
    
    async def test_list_roles(self):
        """Test: List all roles with permissions"""
        print("\n👥 Test: List Roles")
        
        response = await self.client.get(
            "/api/v1/admin/rbac/roles?include_permissions=true&include_user_count=true",
            headers=self.headers
        )
        
        if response.status_code == 200:
            roles = response.json()
            print(f"✅ Found {len(roles)} roles:")
            for role in roles:
                perm_count = len(role.get('role_permissions', []))
                user_count = role.get('user_count', 0)
                print(f"  - {role['role_name']}: {perm_count} permissions, {user_count} users")
            return True, roles
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return False, None
    
    async def test_create_role(self):
        """Test: Create a new role"""
        print("\n🎭 Test: Create Role")
        
        test_role = {
            "role_name": "Test_API_Role",
            "description": "Test role created by API test",
            "is_system": False
        }
        
        response = await self.client.post(
            "/api/v1/admin/rbac/roles",
            headers=self.headers,
            json=test_role
        )
        
        if response.status_code == 200:
            created = response.json()
            print(f"✅ Created role: {created['role_name']} (ID: {created['role_id']})")
            return True, created
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return False, None
    
    async def test_assign_permission_to_role(self, role_id: int, permission_id: int):
        """Test: Assign permission to role"""
        print("\n🔗 Test: Assign Permission to Role")
        
        response = await self.client.post(
            f"/api/v1/admin/rbac/roles/{role_id}/permissions/{permission_id}",
            headers=self.headers
        )
        
        if response.status_code == 200:
            print(f"✅ Assigned permission {permission_id} to role {role_id}")
            return True
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return False
    
    async def test_user_permissions(self, user_id: int = 2):
        """Test: Get user permissions"""
        print(f"\n🔍 Test: Get User {user_id} Permissions")
        
        response = await self.client.get(
            f"/api/v1/admin/rbac/users/{user_id}/permissions",
            headers=self.headers
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ User {user_id} has:")
            print(f"  - {len(data['all_permissions'])} total permissions")
            print(f"  - {len(data['direct_permissions'])} direct permissions")
            print(f"  - {len(data['roles'])} roles")
            
            # Show roles
            for role in data['roles']:
                print(f"    • {role['role_name']}")
                
            return True, data
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return False, None
    
    async def test_assign_role_to_user(self, user_id: int, role_id: int):
        """Test: Assign role to user"""
        print(f"\n👤 Test: Assign Role {role_id} to User {user_id}")
        
        response = await self.client.post(
            f"/api/v1/admin/rbac/users/{user_id}/roles",
            headers=self.headers,
            json={"role_id": role_id}
        )
        
        if response.status_code == 200:
            print(f"✅ Assigned role {role_id} to user {user_id}")
            return True
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return False
    
    async def test_resource_permission(self):
        """Test: Grant resource-specific permission"""
        print("\n🎯 Test: Resource-Specific Permission")
        
        # Get a permission for reports
        perms_response = await self.client.get(
            "/api/v1/admin/rbac/permissions?resource=reports&action=read",
            headers=self.headers
        )
        
        if perms_response.status_code == 200:
            permissions = perms_response.json()
            if permissions:
                perm_id = permissions[0]['permission_id']
                
                # Grant permission for specific report
                grant_data = {
                    "user_id": 3,  # Some test user
                    "resource_type": "report",
                    "resource_id": 42,  # Specific report ID
                    "permission_id": perm_id
                }
                
                response = await self.client.post(
                    "/api/v1/admin/rbac/resource-permissions",
                    headers=self.headers,
                    json=grant_data
                )
                
                if response.status_code == 200:
                    print(f"✅ Granted reports:read on report 42 to user 3")
                    return True
                else:
                    print(f"❌ Failed to grant: {response.status_code}")
                    return False
        
        return False
    
    async def test_audit_log(self):
        """Test: Get audit log"""
        print("\n📜 Test: Audit Log")
        
        response = await self.client.get(
            "/api/v1/admin/rbac/audit-log?limit=10",
            headers=self.headers
        )
        
        if response.status_code == 200:
            logs = response.json()
            print(f"✅ Found {len(logs)} audit log entries:")
            for log in logs[:5]:
                print(f"  - {log['action_type']} on {log['target_type']} "
                      f"at {log['performed_at']}")
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            return False
    
    async def cleanup(self, role_id: int = None, permission_id: int = None):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        
        # Delete test role
        if role_id:
            response = await self.client.delete(
                f"/api/v1/admin/rbac/roles/{role_id}",
                headers=self.headers
            )
            if response.status_code == 200:
                print(f"  ✅ Deleted test role {role_id}")
        
        # Delete test permission
        if permission_id:
            response = await self.client.delete(
                f"/api/v1/admin/rbac/permissions/{permission_id}",
                headers=self.headers
            )
            if response.status_code == 200:
                print(f"  ✅ Deleted test permission {permission_id}")
    
    async def run_all_tests(self):
        """Run all API tests"""
        print("\n" + "="*60)
        print("RBAC API INTEGRATION TESTS")
        print("="*60)
        
        test_role_id = None
        test_perm_id = None
        
        try:
            await self.setup()
            
            # Run tests
            success, perms = await self.test_list_permissions()
            test_results.append(("List Permissions", success))
            
            success, perm = await self.test_create_permission()
            test_results.append(("Create Permission", success))
            if success:
                test_perm_id = perm['permission_id']
            
            success, roles = await self.test_list_roles()
            test_results.append(("List Roles", success))
            
            success, role = await self.test_create_role()
            test_results.append(("Create Role", success))
            if success:
                test_role_id = role['role_id']
            
            if test_role_id and test_perm_id:
                success = await self.test_assign_permission_to_role(test_role_id, test_perm_id)
                test_results.append(("Assign Permission to Role", success))
            
            success, _ = await self.test_user_permissions()
            test_results.append(("Get User Permissions", success))
            
            if test_role_id:
                success = await self.test_assign_role_to_user(2, test_role_id)
                test_results.append(("Assign Role to User", success))
            
            success = await self.test_resource_permission()
            test_results.append(("Resource-Specific Permission", success))
            
            success = await self.test_audit_log()
            test_results.append(("Audit Log", success))
            
            # Clean up
            await self.cleanup(test_role_id, test_perm_id)
            
            # Print summary
            print("\n" + "="*60)
            print("TEST SUMMARY")
            print("="*60)
            passed = sum(1 for _, success in test_results if success)
            total = len(test_results)
            print(f"Total Tests: {total}")
            print(f"Passed: {passed} ✅")
            print(f"Failed: {total - passed} ❌")
            print(f"Success Rate: {passed/total*100:.1f}%")
            
            if passed < total:
                print("\nFailed Tests:")
                for test_name, success in test_results:
                    if not success:
                        print(f"  - {test_name}")
                        
        finally:
            await self.client.aclose()


async def main():
    tester = RBACAPITester()
    await tester.run_all_tests()


if __name__ == "__main__":
    print("\n⚠️  Make sure the backend is running on http://localhost:8000")
    print("⚠️  Make sure admin user exists with email: admin@company.com\n")
    input("Press Enter to start tests...")
    asyncio.run(main())