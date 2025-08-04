#!/usr/bin/env python3
"""Get test token"""

import requests

# Try common test users
test_users = [
    ("john.doe@example.com", "password123"),
    ("admin@example.com", "admin123"),
    ("tester@example.com", "password123"),
    ("report.owner@example.com", "password123"),
]

base_url = "http://localhost:8000"

for email, password in test_users:
    print(f"Trying {email}...")
    
    response = requests.post(
        f"{base_url}/api/v1/auth/login",
        json={"username": email, "password": password}
    )
    
    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        print(f"✓ Success! Token for {email}")
        
        # Save token
        with open('.test_token', 'w') as f:
            f.write(token)
        
        print(f"Token saved to .test_token")
        break
    else:
        print(f"✗ Failed: {response.status_code}")
else:
    print("No working test user found")