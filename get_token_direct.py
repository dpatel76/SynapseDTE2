#!/usr/bin/env python3
"""Get token using correct login format"""

import requests

# Login credentials
email = "tester@example.com"
password = "password123"

base_url = "http://localhost:8000"

print(f"Logging in as {email}...")

# Use JSON format
response = requests.post(
    f"{base_url}/api/v1/auth/login",
    json={
        "email": email,
        "password": password
    }
)

print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    token = data.get("access_token")
    print(f"✓ Success! Got token")
    
    # Save token
    with open('.test_token', 'w') as f:
        f.write(token)
    
    print(f"Token saved to .test_token")
else:
    print(f"Error: {response.text}")