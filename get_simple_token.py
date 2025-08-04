#!/usr/bin/env python3
import requests

# Login
resp = requests.post("http://localhost:8000/api/v1/auth/login", json={
    "email": "tester@example.com",
    "password": "password123"
})

if resp.status_code == 200:
    print(resp.json()["access_token"])
else:
    print(f"ERROR: {resp.status_code}")