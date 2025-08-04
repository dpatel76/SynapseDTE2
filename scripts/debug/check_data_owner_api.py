#!/usr/bin/env python3
"""Check data owner page API calls."""
import requests

# Login
login_resp = requests.post("http://localhost:8001/api/v1/auth/login", 
                          json={"email": "tester@example.com", "password": "password123"})
token = login_resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Check the API endpoint
print("Checking /cycle-reports/9/reports/156...")
resp = requests.get("http://localhost:8001/api/v1/cycle-reports/9/reports/156", headers=headers)
print(f"Status: {resp.status_code}")
if resp.status_code != 200:
    print(f"Error: {resp.text}")
else:
    print("Success - data returned")

# Also check data provider phase status
print("\nChecking data provider phase status...")
resp2 = requests.get("http://localhost:8001/api/v1/data-provider/9/reports/156/status", headers=headers)
print(f"Status: {resp2.status_code}")
if resp2.status_code != 200:
    print(f"Error: {resp2.text}")