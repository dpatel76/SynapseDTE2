#!/usr/bin/env python3
"""
Test RBAC Permission Decorators
Demonstrates how the new permission system protects endpoints
"""

import asyncio
import httpx
from typing import Dict, List, Tuple

# Test configuration
BASE_URL = "http://localhost:8000"

# Test users with different roles
TEST_USERS = [
    {"email": "admin@company.com", "password": "admin123", "role": "Admin"},
    {"email": "testmanager@company.com", "password": "password123", "role": "Test Executive"},
    {"email": "tester@company.com", "password": "password123", "role": "Tester"},
    {"email": "reportowner@company.com", "password": "password123", "role": "Report Owner"},
    {"email": "dataprovider@company.com", "password": "password123", "role": "Data Owner"},
]

# Endpoints to test with required permissions
ENDPOINTS_TO_TEST = [
    # Format: (method, path, required_permission, description)
    ("POST", "/api/v1/cycles", "cycles:create", "Create test cycle"),
    ("GET", "/api/v1/cycles", "cycles:read", "List test cycles"),
    ("PUT", "/api/v1/cycles/1", "cycles:update", "Update test cycle"),
    ("DELETE", "/api/v1/cycles/1", "cycles:delete", "Delete test cycle"),
    
    ("POST", "/api/v1/planning/1/reports/1/attributes", "planning:create", "Create attribute"),
    ("POST", "/api/v1/planning/1/reports/1/upload", "planning:upload", "Upload document"),
    ("POST", "/api/v1/planning/1/reports/1/complete", "planning:complete", "Complete planning"),
    
    ("POST", "/api/v1/scoping/1/reports/1/generate", "scoping:generate", "Generate scoping"),
    ("POST", "/api/v1/scoping/1/reports/1/approve", "scoping:approve", "Approve scoping"),
    
    ("GET", "/api/v1/admin/rbac/permissions", "permissions:manage", "List permissions"),
    ("POST", "/api/v1/admin/rbac/roles", "permissions:manage", "Create role"),
]


class PermissionTester:
    def __init__(self):
        self.client = httpx.AsyncClient(base_url=BASE_URL)
        self.user_tokens = {}
        
    async def login_all_users(self):
        """Login all test users and store tokens"""
        print("🔐 Logging in test users...\n")
        
        for user in TEST_USERS:
            response = await self.client.post(
                "/api/v1/auth/login",
                json={"email": user["email"], "password": user["password"]}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.user_tokens[user["role"]] = data["access_token"]
                print(f"✅ {user['role']}: Logged in successfully")
            else:
                print(f"❌ {user['role']}: Login failed")
    
    async def test_endpoint_permissions(self):
        """Test each endpoint with different user roles"""
        print("\n" + "="*80)
        print("TESTING ENDPOINT PERMISSIONS")
        print("="*80)
        
        results = []
        
        for method, path, permission, description in ENDPOINTS_TO_TEST:
            print(f"\n🎯 Testing: {description}")
            print(f"   Endpoint: {method} {path}")
            print(f"   Required: {permission}")
            print(f"   Results:")
            
            endpoint_results = []
            
            for role, token in self.user_tokens.items():
                headers = {"Authorization": f"Bearer {token}"}
                
                # Make request based on method
                if method == "GET":
                    response = await self.client.get(path, headers=headers)
                elif method == "POST":
                    response = await self.client.post(path, headers=headers, json={})
                elif method == "PUT":
                    response = await self.client.put(path, headers=headers, json={})
                elif method == "DELETE":
                    response = await self.client.delete(path, headers=headers)
                
                # Check response
                if response.status_code == 403:
                    result = "❌ Denied"
                    allowed = False
                elif response.status_code in [200, 201, 204, 400, 404, 422]:
                    # 400/404/422 means permission passed but other validation failed
                    result = "✅ Allowed"
                    allowed = True
                else:
                    result = f"❓ {response.status_code}"
                    allowed = None
                
                print(f"     {role:20} {result}")
                endpoint_results.append((role, allowed))
            
            results.append((description, endpoint_results))
        
        return results
    
    async def test_resource_specific_permissions(self):
        """Test resource-specific permission checks"""
        print("\n" + "="*80)
        print("TESTING RESOURCE-SPECIFIC PERMISSIONS")
        print("="*80)
        
        # This would test endpoints that check resource-specific permissions
        # For example, updating a specific report where the user has permission
        # only for that particular report
        
        print("\n🎯 Testing: Update specific report")
        print("   Scenario: User has permission to update report 1 but not report 2")
        
        # Would need to set up resource-specific permissions first
        # Then test access to different resources
        
    async def generate_permission_matrix(self, results: List):
        """Generate a permission matrix from test results"""
        print("\n" + "="*80)
        print("PERMISSION MATRIX")
        print("="*80)
        
        # Header
        roles = list(self.user_tokens.keys())
        header = "Endpoint".ljust(40) + " | " + " | ".join(r.center(12) for r in roles)
        print(header)
        print("-" * len(header))
        
        # Results
        for description, endpoint_results in results:
            row = description[:40].ljust(40) + " | "
            for role in roles:
                result = next((r[1] for r in endpoint_results if r[0] == role), None)
                if result is True:
                    symbol = "✅"
                elif result is False:
                    symbol = "❌"
                else:
                    symbol = "❓"
                row += symbol.center(12) + " | "
            print(row)
    
    async def verify_permission_inheritance(self):
        """Test role hierarchy and permission inheritance"""
        print("\n" + "="*80)
        print("TESTING PERMISSION INHERITANCE")
        print("="*80)
        
        # This would test if child roles inherit parent role permissions
        print("\n🎯 Testing: Role hierarchy")
        print("   (Would test if roles properly inherit permissions from parent roles)")
    
    async def run_all_tests(self):
        """Run all permission tests"""
        try:
            # Login all users
            await self.login_all_users()
            
            # Test endpoint permissions
            results = await self.test_endpoint_permissions()
            
            # Generate permission matrix
            await self.generate_permission_matrix(results)
            
            # Test resource-specific permissions
            await self.test_resource_specific_permissions()
            
            # Test permission inheritance
            await self.verify_permission_inheritance()
            
            print("\n" + "="*80)
            print("✅ Permission testing completed!")
            print("="*80)
            
        finally:
            await self.client.aclose()


def show_example_decorator_usage():
    """Show how decorators are used in the code"""
    print("\n" + "="*80)
    print("EXAMPLE: How Permission Decorators Work")
    print("="*80)
    
    example_code = '''
# Before (hardcoded role check):
@router.post("/cycles")
async def create_cycle(
    current_user: User = Depends(require_roles([UserRoles.TEST_EXECUTIVE]))
):
    # Only Test Managers can create cycles
    pass

# After (flexible permission check):
@router.post("/cycles")
@require_permission("cycles", "create")
async def create_cycle(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Anyone with cycles:create permission can create cycles
    pass

# Resource-specific permission:
@router.put("/reports/{report_id}")
@require_permission("reports", "update", resource_id_param="report_id")
async def update_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Checks if user has permission to update this specific report
    pass

# Multiple permissions (ANY):
@router.get("/reports/{report_id}")
@require_any_permission(("reports", "read"), ("reports", "update"))
async def view_report(...):
    # User needs either read OR update permission
    pass

# Multiple permissions (ALL):
@router.post("/reports/{report_id}/approve")
@require_all_permissions(("reports", "read"), ("reports", "approve"))
async def approve_report(...):
    # User needs BOTH read AND approve permissions
    pass
'''
    
    print(example_code)


async def main():
    # Show decorator examples
    show_example_decorator_usage()
    
    # Run permission tests
    print("\n⚠️  Make sure the backend is running on http://localhost:8000")
    print("⚠️  Make sure all test users exist in the database\n")
    input("Press Enter to start permission tests...")
    
    tester = PermissionTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())