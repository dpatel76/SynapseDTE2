#!/usr/bin/env python3
import requests
import json

# Login
login_data = {"email": "tester@example.com", "password": "password123"}
r = requests.post("http://localhost:8000/api/v1/auth/login", json=login_data)
token = r.json()["access_token"]

# Test endpoint
headers = {"Authorization": f"Bearer {token}"}
r = requests.get("http://localhost:8000/api/v1/scoping/phases/467/versions/history", headers=headers)

print(f"Status: {r.status_code}")
print(f"Response: {json.dumps(r.json(), indent=2)}")