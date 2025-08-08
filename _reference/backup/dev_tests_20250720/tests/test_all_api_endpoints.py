#!/usr/bin/env python3
"""
Test all API endpoints to ensure they work correctly
"""

import asyncio
import httpx
import json
from typing import Dict, List, Optional

# API Configuration
BASE_URL = 'http://localhost:8001'
TEST_USER = {"email": "admin@example.com", "password": "password123"}

class APIEndpointTester:
    def __init__(self):
        self.results = []
        self.token = None
        
    async def login(self) -> bool:
        """Login and get auth token"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{BASE_URL}/api/v1/auth/login",
                    json=TEST_USER
                )
                if response.status_code == 200:
                    data = response.json()
                    self.token = data.get("access_token")
                    print(f"✅ Login successful - Token received")
                    return True
                else:
                    print(f"❌ Login failed: {response.status_code}")
                    return False
            except Exception as e:
                print(f"❌ Login error: {e}")
                return False
    
    async def test_endpoint(self, method: str, path: str, data: Optional[Dict] = None, expected_status: List[int] = None):
        """Test a single endpoint"""
        if expected_status is None:
            expected_status = [200, 201, 204]
            
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        
        async with httpx.AsyncClient() as client:
            try:
                if method == "GET":
                    response = await client.get(f"{BASE_URL}{path}", headers=headers)
                elif method == "POST":
                    response = await client.post(f"{BASE_URL}{path}", headers=headers, json=data)
                elif method == "PUT":
                    response = await client.put(f"{BASE_URL}{path}", headers=headers, json=data)
                elif method == "DELETE":
                    response = await client.delete(f"{BASE_URL}{path}", headers=headers)
                else:
                    raise ValueError(f"Unsupported method: {method}")
                
                success = response.status_code in expected_status
                result = {
                    "method": method,
                    "path": path,
                    "status": response.status_code,
                    "success": success,
                    "response": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
                }
                
                if success:
                    print(f"✅ {method} {path} - {response.status_code}")
                else:
                    print(f"❌ {method} {path} - {response.status_code}")
                    if response.status_code == 422:
                        print(f"   Validation error: {response.json()}")
                    elif response.status_code == 307:
                        print(f"   Redirect to: {response.headers.get('location')}")
                
                self.results.append(result)
                return result
                
            except Exception as e:
                print(f"❌ {method} {path} - Error: {e}")
                self.results.append({
                    "method": method,
                    "path": path,
                    "status": 0,
                    "success": False,
                    "error": str(e)
                })
                return None
    
    async def run_all_tests(self):
        """Run all API endpoint tests"""
        print("🧪 Testing All API Endpoints")
        print("=" * 60)
        
        # Login first
        if not await self.login():
            print("Cannot proceed without authentication")
            return
        
        print("\n📌 Testing Authentication Endpoints")
        await self.test_endpoint("GET", "/api/v1/auth/me")
        # Test with a password that meets security requirements
        await self.test_endpoint("POST", "/api/v1/auth/change-password", {
            "current_password": "password123",
            "new_password": "NewPassword123!",
            "confirm_password": "NewPassword123!"
        }, [200, 400, 422])  # 422 if validation fails, 400 if other error
        
        print("\n📌 Testing User Endpoints")
        await self.test_endpoint("GET", "/api/v1/users/")
        await self.test_endpoint("GET", "/api/v1/users/238")  # Admin user ID
        
        print("\n📌 Testing Cycle Endpoints")
        await self.test_endpoint("GET", "/api/v1/cycles/")
        
        print("\n📌 Testing Report Endpoints")
        await self.test_endpoint("GET", "/api/v1/reports/")
        
        print("\n📌 Testing LOB Endpoints")
        await self.test_endpoint("GET", "/api/v1/lobs/")
        
        print("\n📌 Testing Dashboard Endpoints")
        await self.test_endpoint("GET", "/api/v1/dashboards/executive", expected_status=[200, 403, 404])
        
        print("\n📌 Testing RBAC Endpoints")
        await self.test_endpoint("GET", "/api/v1/admin/rbac/permissions")
        await self.test_endpoint("GET", "/api/v1/admin/rbac/roles")
        
        # Get a cycle to test workflow endpoints
        cycles_response = next((r for r in self.results if r["path"] == "/api/v1/cycles" and r["success"]), None)
        if cycles_response and cycles_response["response"]:
            cycles = cycles_response["response"]
            if len(cycles) > 0:
                cycle_id = cycles[0]["cycle_id"]
                
                # Get reports for this cycle
                print(f"\n📌 Testing Cycle {cycle_id} Endpoints")
                await self.test_endpoint("GET", f"/api/v1/cycle-reports/{cycle_id}")
                
                # Test workflow status
                reports_response = await self.test_endpoint("GET", f"/api/v1/cycle-reports/{cycle_id}")
                if reports_response and reports_response["success"] and reports_response["response"]:
                    reports = reports_response["response"]
                    if len(reports) > 0:
                        report_id = reports[0]["report_id"]
                        print(f"\n📌 Testing Workflow Endpoints for Cycle {cycle_id}, Report {report_id}")
                        await self.test_endpoint("GET", f"/api/v1/planning/cycles/{cycle_id}/reports/{report_id}/attributes")
                        await self.test_endpoint("GET", f"/api/v1/scoping/cycles/{cycle_id}/reports/{report_id}/samples")
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Test Summary:")
        total = len(self.results)
        success = sum(1 for r in self.results if r.get("success", False))
        failed = total - success
        
        print(f"  Total: {total}")
        print(f"  ✅ Success: {success}")
        print(f"  ❌ Failed: {failed}")
        print(f"  Success Rate: {(success/total*100):.1f}%")
        
        # List failed endpoints
        if failed > 0:
            print("\n❌ Failed Endpoints:")
            for r in self.results:
                if not r.get("success", False):
                    print(f"  - {r['method']} {r['path']} (Status: {r['status']})")
        
        # Save results
        with open("test_results/api_endpoint_test_results.json", "w") as f:
            json.dump({
                "summary": {
                    "total": total,
                    "success": success,
                    "failed": failed,
                    "success_rate": f"{(success/total*100):.1f}%"
                },
                "results": self.results
            }, f, indent=2)
        
        print("\n💾 Detailed results saved to: test_results/api_endpoint_test_results.json")

async def main():
    import os
    os.makedirs("test_results", exist_ok=True)
    
    tester = APIEndpointTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())