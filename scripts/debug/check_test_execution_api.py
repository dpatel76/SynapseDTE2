#!/usr/bin/env python3
"""Check test execution API."""
import requests

# Login
login_resp = requests.post("http://localhost:8001/api/v1/auth/login", 
                          json={"email": "tester@example.com", "password": "password123"})
print(f"Login status: {login_resp.status_code}")
print(f"Login response: {login_resp.text}")

if login_resp.status_code == 200:
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
else:
    print("Login failed!")
    exit(1)

# Test the endpoint
resp = requests.get("http://localhost:8001/api/v1/test-execution/9/reports/156/submitted-test-cases", 
                   headers=headers)

print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    import json
    print(json.dumps(resp.json(), indent=2))
else:
    print(f"Error: {resp.text}")