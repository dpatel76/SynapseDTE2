#!/usr/bin/env python3
"""
Demo test run showing the comprehensive test system in action
"""

import asyncio
import httpx
from datetime import datetime
import json

# Test Configuration
BASE_URL = 'http://localhost:8001'
FRONTEND_URL = 'http://localhost:3000'

# Test credentials
TEST_USERS = {
    "Admin": {"email": "admin@example.com", "password": "password123"},
    "Tester": {"email": "tester@example.com", "password": "password123"},
    "Test Executive": {"email": "test.manager@example.com", "password": "password123"},
    "Data Executive": {"email": "cdo@example.com", "password": "password123"},
    "Data Owner": {"email": "data.provider@example.com", "password": "password123"},
    "Report Owner": {"email": "report.owner@example.com", "password": "password123"}
}

async def test_api_endpoints():
    """Test various API endpoints for each role"""
    print("\n🔍 Testing API Endpoints")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        results = []
        
        for role, creds in TEST_USERS.items():
            print(f"\n📌 Testing {role} role")
            
            # Login
            try:
                response = await client.post(
                    f"{BASE_URL}/api/v1/auth/login",
                    json=creds
                )
                
                if response.status_code == 200:
                    token = response.json()["access_token"]
                    print(f"  ✅ Login successful")
                    
                    # Test authenticated endpoints
                    headers = {"Authorization": f"Bearer {token}"}
                    
                    # Test user profile
                    profile_resp = await client.get(
                        f"{BASE_URL}/api/v1/users/me",
                        headers=headers
                    )
                    
                    if profile_resp.status_code == 200:
                        user_data = profile_resp.json()
                        print(f"  ✅ Profile access: {user_data.get('email')}")
                    else:
                        print(f"  ❌ Profile access failed: {profile_resp.status_code}")
                    
                    # Test cycles endpoint
                    cycles_resp = await client.get(
                        f"{BASE_URL}/api/v1/cycles",
                        headers=headers
                    )
                    
                    if cycles_resp.status_code == 200:
                        cycles = cycles_resp.json()
                        print(f"  ✅ Cycles access: {len(cycles)} cycles found")
                    else:
                        print(f"  ❌ Cycles access failed: {cycles_resp.status_code}")
                    
                    results.append({
                        "role": role,
                        "login": "pass",
                        "profile": "pass" if profile_resp.status_code == 200 else "fail",
                        "cycles": "pass" if cycles_resp.status_code == 200 else "fail"
                    })
                    
                else:
                    print(f"  ❌ Login failed: {response.status_code}")
                    results.append({
                        "role": role,
                        "login": "fail",
                        "profile": "skip",
                        "cycles": "skip"
                    })
                    
            except Exception as e:
                print(f"  ❌ Error: {str(e)}")
                results.append({
                    "role": role,
                    "login": "error",
                    "profile": "skip",
                    "cycles": "skip"
                })
        
        return results

async def test_role_permissions():
    """Test role-specific permissions"""
    print("\n🔐 Testing Role Permissions")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        # Login as admin
        admin_resp = await client.post(
            f"{BASE_URL}/api/v1/auth/login",
            json=TEST_USERS["Admin"]
        )
        admin_token = admin_resp.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Login as tester
        tester_resp = await client.post(
            f"{BASE_URL}/api/v1/auth/login",
            json=TEST_USERS["Tester"]
        )
        tester_token = tester_resp.json()["access_token"]
        tester_headers = {"Authorization": f"Bearer {tester_token}"}
        
        # Test admin-only endpoint
        print("\n📌 Testing Admin-only endpoints")
        users_resp = await client.get(
            f"{BASE_URL}/api/v1/users",
            headers=admin_headers
        )
        print(f"  Admin access to users: {'✅ Pass' if users_resp.status_code == 200 else '❌ Fail'}")
        
        # Test if tester can access admin endpoint
        tester_users_resp = await client.get(
            f"{BASE_URL}/api/v1/users",
            headers=tester_headers
        )
        print(f"  Tester access to users: {'❌ Correctly denied' if tester_users_resp.status_code == 403 else '⚠️ Unexpected'}")

async def generate_summary_report(api_results):
    """Generate a summary report"""
    print("\n📊 Test Summary Report")
    print("=" * 60)
    
    # Count results
    total_tests = len(api_results) * 3  # login, profile, cycles
    passed = sum(1 for r in api_results for v in r.values() if v == "pass")
    failed = sum(1 for r in api_results for v in r.values() if v == "fail")
    skipped = sum(1 for r in api_results for v in r.values() if v == "skip")
    
    print(f"\n📈 Overall Statistics:")
    print(f"  Total Tests: {total_tests}")
    print(f"  ✅ Passed: {passed}")
    print(f"  ❌ Failed: {failed}")
    print(f"  ⏭️ Skipped: {skipped}")
    print(f"  Success Rate: {(passed/total_tests*100):.1f}%")
    
    print(f"\n📋 Results by Role:")
    for result in api_results:
        print(f"  {result['role']}:")
        print(f"    Login: {result['login']}")
        print(f"    Profile: {result['profile']}")
        print(f"    Cycles: {result['cycles']}")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"test_results/demo_test_report_{timestamp}.json"
    
    report_data = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_tests": total_tests,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "success_rate": f"{(passed/total_tests*100):.1f}%"
        },
        "results_by_role": api_results,
        "test_configuration": {
            "backend_url": BASE_URL,
            "frontend_url": FRONTEND_URL,
            "roles_tested": list(TEST_USERS.keys())
        }
    }
    
    with open(report_file, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    print(f"\n💾 Report saved to: {report_file}")

async def main():
    print("🚀 SynapseDTE Demo Test Run")
    print("This demonstrates the comprehensive testing capabilities")
    print("=" * 60)
    
    # Create results directory
    import os
    os.makedirs("test_results", exist_ok=True)
    
    # Run tests
    api_results = await test_api_endpoints()
    await test_role_permissions()
    await generate_summary_report(api_results)
    
    print("\n✨ Demo test run completed!")
    print("\nFor full comprehensive testing, run: ./scripts/run_comprehensive_tests.sh")

if __name__ == "__main__":
    asyncio.run(main())