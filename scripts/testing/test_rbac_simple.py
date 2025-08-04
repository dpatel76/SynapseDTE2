#!/usr/bin/env python3
"""
Simple RBAC test focusing on key functionality
"""

import requests

# Test users
USERS = {
    "tester": {"email": "tester@synapse.com", "password": "TestUser123!"},
    "test_manager": {"email": "testmgr@synapse.com", "password": "TestUser123!"},
    "cdo": {"email": "cdo@synapse.com", "password": "TestUser123!"}
}

CYCLE_ID = 9
REPORT_ID = 156
BASE_URL = "http://localhost:8001/api/v1"

def test_user(role, user_info):
    """Test endpoints for a specific user"""
    print(f"\n{role.upper()}:")
    
    # Login
    resp = requests.post(f"{BASE_URL}/auth/login", json=user_info)
    if resp.status_code != 200:
        print(f"  ❌ Login failed: {resp.status_code}")
        return
    
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"  ✅ Login successful")
    
    # Test key endpoints
    endpoints = [
        ("GET", f"/cycles/{CYCLE_ID}", "View test cycle"),
        ("GET", f"/test-execution/{CYCLE_ID}/reports/{REPORT_ID}/executions", "View test executions"),
        ("GET", f"/observation-management/{CYCLE_ID}/reports/{REPORT_ID}/observations", "View observations"),
    ]
    
    if role == "test_manager":
        endpoints.append(("GET", f"/cycles/{CYCLE_ID}/reports", "View cycle reports"))
    
    for method, path, desc in endpoints:
        resp = requests.request(method, f"{BASE_URL}{path}", headers=headers)
        icon = "✅" if resp.status_code == 200 else "❌"
        print(f"  {icon} {desc}: {resp.status_code}")

def main():
    print("=" * 50)
    print("RBAC Test - Key Functionality")
    print("=" * 50)
    
    for role, user_info in USERS.items():
        test_user(role, user_info)
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()