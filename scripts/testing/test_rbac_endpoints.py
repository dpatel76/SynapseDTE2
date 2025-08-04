#!/usr/bin/env python3
"""
Test RBAC implementation by calling various endpoints with different user roles
"""

import asyncio
import httpx
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Test configuration
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

# Test users (these should exist in your database)
TEST_USERS = {
    "admin": {
        "email": "admin@synapsedt.com",
        "password": "admin123",
        "expected_role": "Admin"
    },
    "test_manager": {
        "email": "john.manager@synapsedt.com", 
        "password": "password123",
        "expected_role": "Test Executive"
    },
    "tester": {
        "email": "jane.tester@synapsedt.com",
        "password": "password123", 
        "expected_role": "Tester"
    },
    "report_owner": {
        "email": "bob.owner@synapsedt.com",
        "password": "password123",
        "expected_role": "Report Owner"
    },
    "data_owner": {
        "email": "charlie.provider@synapsedt.com",
        "password": "password123",
        "expected_role": "Data Owner"
    }
}

# Test endpoints with expected permissions
TEST_ENDPOINTS = [
    # Cycles endpoints
    {
        "method": "GET",
        "path": "/cycles",
        "description": "List test cycles",
        "allowed_roles": ["Admin", "Test Executive", "Tester", "Report Owner"],
        "denied_roles": ["Data Owner"]
    },
    {
        "method": "POST",
        "path": "/cycles",
        "description": "Create test cycle",
        "body": {
            "cycle_name": "RBAC Test Cycle",
            "description": "Testing RBAC permissions",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31"
        },
        "allowed_roles": ["Admin", "Test Executive"],
        "denied_roles": ["Tester", "Report Owner", "Data Owner"]
    },
    # Reports endpoints
    {
        "method": "GET",
        "path": "/reports",
        "description": "List reports",
        "allowed_roles": ["Admin", "Test Executive", "Report Owner", "Tester"],
        "denied_roles": ["Data Owner"]
    },
    {
        "method": "POST",
        "path": "/reports",
        "description": "Create report",
        "body": {
            "report_name": "RBAC Test Report",
            "regulation": "Test Regulation",
            "lob_id": 1,
            "description": "Testing RBAC"
        },
        "allowed_roles": ["Admin", "Test Executive"],
        "denied_roles": ["Tester", "Report Owner", "Data Owner"]
    },
    # Users endpoints
    {
        "method": "GET",
        "path": "/users",
        "description": "List users",
        "allowed_roles": ["Admin", "Test Executive"],
        "denied_roles": ["Tester", "Report Owner", "Data Owner"]
    },
    {
        "method": "POST",
        "path": "/users",
        "description": "Create user",
        "body": {
            "email": "rbac.test@synapsedt.com",
            "password": "Test123!",
            "first_name": "RBAC",
            "last_name": "Test",
            "role": "Tester"
        },
        "allowed_roles": ["Admin"],
        "denied_roles": ["Test Executive", "Tester", "Report Owner", "Data Owner"]
    },
    # Data sources endpoints  
    {
        "method": "GET",
        "path": "/data-sources",
        "description": "List data sources",
        "allowed_roles": ["Admin"],
        "denied_roles": ["Test Executive", "Tester", "Report Owner", "Data Owner"]
    }
]


class RBACTester:
    def __init__(self):
        self.client = httpx.AsyncClient(base_url=BASE_URL, timeout=30.0, follow_redirects=True)
        self.tokens: Dict[str, str] = {}
        self.results: List[Dict] = []
        
    async def login_user(self, user_key: str) -> Optional[str]:
        """Login a user and return their token"""
        user = TEST_USERS[user_key]
        try:
            response = await self.client.post(
                f"{API_PREFIX}/auth/login",
                json={
                    "email": user["email"],
                    "password": user["password"]
                }
            )
            if response.status_code == 200:
                data = response.json()
                token = data["access_token"]
                self.tokens[user_key] = token
                print(f"✅ Logged in as {user['email']} ({user['expected_role']})")
                return token
            else:
                print(f"❌ Failed to login {user['email']}: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Error logging in {user['email']}: {str(e)}")
            return None
    
    async def test_endpoint(self, endpoint: Dict, user_key: str, token: str) -> Dict:
        """Test a single endpoint with a user token"""
        user = TEST_USERS[user_key]
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            # Make request based on method
            if endpoint["method"] == "GET":
                response = await self.client.get(
                    f"{API_PREFIX}{endpoint['path']}", 
                    headers=headers
                )
            elif endpoint["method"] == "POST":
                response = await self.client.post(
                    f"{API_PREFIX}{endpoint['path']}", 
                    headers=headers,
                    json=endpoint.get("body", {})
                )
            else:
                response = None
            
            # Check if access was as expected
            role = user["expected_role"]
            expected_allowed = role in endpoint["allowed_roles"]
            actual_allowed = response.status_code not in [401, 403]
            
            result = {
                "endpoint": f"{endpoint['method']} {endpoint['path']}",
                "description": endpoint["description"],
                "user": user["email"],
                "role": role,
                "expected": "ALLOW" if expected_allowed else "DENY",
                "actual": "ALLOW" if actual_allowed else "DENY",
                "status_code": response.status_code,
                "passed": expected_allowed == actual_allowed
            }
            
            # Print result
            icon = "✅" if result["passed"] else "❌"
            print(f"{icon} {result['endpoint']} - {result['role']}: "
                  f"Expected {result['expected']}, Got {result['actual']} ({result['status_code']})")
            
            return result
            
        except Exception as e:
            print(f"❌ Error testing {endpoint['path']} with {user['email']}: {str(e)}")
            return {
                "endpoint": f"{endpoint['method']} {endpoint['path']}",
                "user": user["email"],
                "role": user["expected_role"],
                "error": str(e),
                "passed": False
            }
    
    async def run_tests(self):
        """Run all RBAC tests"""
        print("\n" + "="*80)
        print("RBAC ENDPOINT TESTING")
        print("="*80)
        
        # First, login all users
        print("\n1. Logging in test users...")
        for user_key in TEST_USERS:
            await self.login_user(user_key)
        
        # Test each endpoint with each user
        print("\n2. Testing endpoints with different roles...")
        print("-"*80)
        
        for endpoint in TEST_ENDPOINTS:
            print(f"\nTesting: {endpoint['description']} ({endpoint['method']} {endpoint['path']})")
            
            for user_key, token in self.tokens.items():
                result = await self.test_endpoint(endpoint, user_key, token)
                self.results.append(result)
        
        # Generate summary
        await self.generate_summary()
    
    async def generate_summary(self):
        """Generate test summary"""
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.get("passed", False))
        failed_tests = total_tests - passed_tests
        
        print(f"\nTotal tests: {total_tests}")
        if total_tests > 0:
            print(f"Passed: {passed_tests} ({passed_tests/total_tests*100:.1f}%)")
            print(f"Failed: {failed_tests} ({failed_tests/total_tests*100:.1f}%)")
        else:
            print("No tests were run (login failed for all users)")
        
        if failed_tests > 0:
            print("\nFailed tests:")
            for result in self.results:
                if not result.get("passed", False):
                    print(f"  - {result['endpoint']} for {result['role']}: "
                          f"Expected {result.get('expected', 'N/A')}, "
                          f"Got {result.get('actual', 'ERROR')}")
        
        # Save results to file
        with open("rbac_test_results.json", "w") as f:
            json.dump({
                "summary": {
                    "total": total_tests,
                    "passed": passed_tests,
                    "failed": failed_tests
                },
                "results": self.results
            }, f, indent=2)
        
        print(f"\nDetailed results saved to: rbac_test_results.json")
        
        # Return success/failure
        return failed_tests == 0
    
    async def cleanup(self):
        """Clean up resources"""
        await self.client.aclose()


async def main():
    """Main test function"""
    # Check if backend is running
    try:
        response = httpx.get(f"{BASE_URL}/api/v1/test/health")
        if response.status_code != 200:
            print("❌ Backend is not running! Start it with: uvicorn app.main:app --reload")
            return
    except:
        print("❌ Cannot connect to backend at http://localhost:8000")
        print("   Start the backend with: USE_RBAC=true uvicorn app.main:app --reload")
        return
    
    # Create tester and run tests
    tester = RBACTester()
    try:
        success = await tester.run_tests()
        if success:
            print("\n✅ All RBAC tests passed!")
        else:
            print("\n❌ Some RBAC tests failed. Check the results above.")
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    print("RBAC Endpoint Test Suite")
    print("Make sure to set USE_RBAC=true when starting the backend!")
    asyncio.run(main())