#!/usr/bin/env python3
"""
Test Clean Architecture Endpoints
"""

import requests
import json

BASE_URL = "http://localhost:8001/api/v1"

def test_clean_architecture():
    print("Testing Clean Architecture Endpoints...")
    print("=" * 50)
    
    # Test health check
    resp = requests.get(f"{BASE_URL}/health")
    if resp.status_code == 200:
        data = resp.json()
        print(f"✅ Health Check: {data}")
    else:
        print(f"❌ Health Check Failed: {resp.status_code}")
    
    # Test login
    login_data = {
        "email": "testmgr@synapse.com",
        "password": "TestUser123!"
    }
    resp = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    
    if resp.status_code == 200:
        token = resp.json()["access_token"]
        print("✅ Login successful")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test clean architecture endpoints
        endpoints = [
            ("/planning/test", "Planning (Clean)"),
            ("/scoping/test", "Scoping (Clean)"),
            ("/test-execution/test", "Test Execution (Clean)"),
            ("/workflow/status", "Workflow (Clean)"),
        ]
        
        for endpoint, name in endpoints:
            resp = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
            icon = "✅" if resp.status_code in [200, 404] else "❌"
            print(f"{icon} {name}: {resp.status_code}")
    else:
        print(f"❌ Login failed: {resp.status_code}")
    
    print("=" * 50)

if __name__ == "__main__":
    test_clean_architecture()
