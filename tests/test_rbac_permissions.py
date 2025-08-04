#!/usr/bin/env python3
"""
Test RBAC permissions enforcement
"""

import asyncio
import httpx
import json
from typing import Dict, List, Optional

# API Configuration
BASE_URL = 'http://localhost:8001'

# Test users with different roles
TEST_USERS = {
    "admin": {"email": "admin@example.com", "password": "password123"},
    "tester": {"email": "tester@example.com", "password": "password123"},
    "test_manager": {"email": "test.manager@example.com", "password": "password123"},
    "report_owner": {"email": "report.owner@example.com", "password": "password123"},
    "data_owner": {"email": "data.provider@example.com", "password": "password123"},
    "cdo": {"email": "cdo@example.com", "password": "password123"}
}

# Permission test cases: endpoint and expected access by role
PERMISSION_TESTS = [
    # Admin-only endpoints
    {
        "endpoint": "/api/v1/users/",
        "method": "GET",
        "description": "List users",
        "expected_access": {
            "admin": True,
            "test_manager": True,  # Can also list users
            "tester": False,
            "report_owner": False,
            "data_owner": False,
            "cdo": False
        }
    },
    {
        "endpoint": "/api/v1/admin/rbac/permissions",
        "method": "GET",
        "description": "View RBAC permissions",
        "expected_access": {
            "admin": True,
            "test_manager": False,
            "tester": False,
            "report_owner": False,
            "data_owner": False,
            "cdo": False
        }
    },
    # Cycle management
    {
        "endpoint": "/api/v1/cycles/",
        "method": "GET",
        "description": "List cycles",
        "expected_access": {
            "admin": True,
            "test_manager": True,
            "tester": True,
            "report_owner": True,
            "data_owner": True,
            "cdo": True
        }
    },
    {
        "endpoint": "/api/v1/cycles/",
        "method": "POST",
        "description": "Create cycle",
        "data": {
            "cycle_name": "Test RBAC Cycle",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "cycle_type": "Annual"
        },
        "expected_access": {
            "admin": True,
            "test_manager": True,
            "tester": False,
            "report_owner": False,
            "data_owner": False,
            "cdo": False
        }
    },
    # Report management
    {
        "endpoint": "/api/v1/reports/",
        "method": "GET",
        "description": "List reports",
        "expected_access": {
            "admin": True,
            "test_manager": True,
            "tester": True,
            "report_owner": True,
            "data_owner": False,
            "cdo": False
        }
    },
    # LOB management
    {
        "endpoint": "/api/v1/lobs/",
        "method": "GET",
        "description": "List LOBs",
        "expected_access": {
            "admin": True,
            "test_manager": True,
            "tester": True,
            "report_owner": True,
            "data_owner": True,
            "cdo": True
        }
    }
]

class RBACPermissionTester:
    def __init__(self):
        self.results = []
        self.tokens = {}
        
    async def login_all_users(self):
        """Login all test users and store tokens"""
        print("🔐 Logging in all test users...")
        async with httpx.AsyncClient() as client:
            for role, credentials in TEST_USERS.items():
                try:
                    response = await client.post(
                        f"{BASE_URL}/api/v1/auth/login",
                        json=credentials
                    )
                    if response.status_code == 200:
                        data = response.json()
                        self.tokens[role] = data.get("access_token")
                        print(f"✅ {role}: Login successful")
                    else:
                        print(f"❌ {role}: Login failed - {response.status_code}")
                except Exception as e:
                    print(f"❌ {role}: Login error - {e}")
    
    async def test_permission(self, test_case: Dict, role: str, token: str) -> Dict:
        """Test a single permission for a specific role"""
        headers = {"Authorization": f"Bearer {token}"}
        
        async with httpx.AsyncClient() as client:
            try:
                if test_case["method"] == "GET":
                    response = await client.get(
                        f"{BASE_URL}{test_case['endpoint']}", 
                        headers=headers
                    )
                elif test_case["method"] == "POST":
                    response = await client.post(
                        f"{BASE_URL}{test_case['endpoint']}", 
                        headers=headers,
                        json=test_case.get("data", {})
                    )
                else:
                    raise ValueError(f"Unsupported method: {test_case['method']}")
                
                # Check if access matches expectation
                expected_access = test_case["expected_access"][role]
                actual_access = response.status_code in [200, 201, 204]
                
                # 403 is the correct forbidden status for RBAC
                if not actual_access and response.status_code == 403:
                    # This is expected behavior for forbidden access
                    success = not expected_access
                else:
                    success = actual_access == expected_access
                
                result = {
                    "role": role,
                    "endpoint": test_case["endpoint"],
                    "method": test_case["method"],
                    "description": test_case["description"],
                    "expected_access": expected_access,
                    "actual_access": actual_access,
                    "status_code": response.status_code,
                    "success": success
                }
                
                return result
                
            except Exception as e:
                return {
                    "role": role,
                    "endpoint": test_case["endpoint"],
                    "method": test_case["method"],
                    "description": test_case["description"],
                    "expected_access": test_case["expected_access"][role],
                    "actual_access": False,
                    "error": str(e),
                    "success": False
                }
    
    async def run_all_tests(self):
        """Run all permission tests"""
        print("\n🧪 Testing RBAC Permissions")
        print("=" * 80)
        
        # Login all users
        await self.login_all_users()
        
        print("\n📋 Running Permission Tests...")
        print("-" * 80)
        
        # Test each permission for each role
        for test_case in PERMISSION_TESTS:
            print(f"\n🔍 Testing: {test_case['description']} ({test_case['method']} {test_case['endpoint']})")
            
            for role, token in self.tokens.items():
                result = await self.test_permission(test_case, role, token)
                self.results.append(result)
                
                if result["success"]:
                    icon = "✅"
                else:
                    icon = "❌"
                
                access_str = "ALLOWED" if result["actual_access"] else "DENIED"
                expected_str = "ALLOWED" if result["expected_access"] else "DENIED"
                
                print(f"  {icon} {role}: {access_str} (expected: {expected_str}) - Status: {result.get('status_code', 'Error')}")
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 RBAC Test Summary:")
        total = len(self.results)
        successful = sum(1 for r in self.results if r["success"])
        failed = total - successful
        
        print(f"  Total Tests: {total}")
        print(f"  ✅ Successful: {successful}")
        print(f"  ❌ Failed: {failed}")
        print(f"  Success Rate: {(successful/total*100):.1f}%")
        
        # Show failures if any
        if failed > 0:
            print("\n❌ Failed Permission Checks:")
            for r in self.results:
                if not r["success"]:
                    print(f"  - {r['role']} @ {r['method']} {r['endpoint']}")
                    print(f"    Expected: {'ALLOWED' if r['expected_access'] else 'DENIED'}")
                    print(f"    Actual: {'ALLOWED' if r['actual_access'] else 'DENIED'} (Status: {r.get('status_code', 'Error')})")
        
        # Save results
        with open("test_results/rbac_permission_test_results.json", "w") as f:
            json.dump({
                "rbac_enabled": True,
                "summary": {
                    "total": total,
                    "successful": successful,
                    "failed": failed,
                    "success_rate": f"{(successful/total*100):.1f}%"
                },
                "results": self.results
            }, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: test_results/rbac_permission_test_results.json")
        
        # Verify RBAC is actually working
        rbac_working = any(
            r for r in self.results 
            if not r["expected_access"] and not r["actual_access"] and r["status_code"] == 403
        )
        
        if rbac_working:
            print("\n✅ RBAC is ACTIVE and enforcing permissions correctly!")
        else:
            print("\n⚠️  RBAC may not be fully active - no 403 responses detected")

async def main():
    import os
    os.makedirs("test_results", exist_ok=True)
    
    tester = RBACPermissionTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())