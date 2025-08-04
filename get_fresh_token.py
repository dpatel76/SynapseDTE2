"""
Get a fresh authentication token for testing
"""
import requests
import json

API_BASE = "http://localhost:8000/api/v1"

# Login credentials (Tester role)
credentials = {
    "email": "tester@example.com",
    "password": "password123"
}

print("Attempting to login...")
response = requests.post(f"{API_BASE}/auth/login", json=credentials)

if response.status_code == 200:
    data = response.json()
    token = data.get('access_token')
    
    # Save token to file
    with open('.test_token', 'w') as f:
        f.write(token)
    
    print(f"✓ Login successful!")
    print(f"  User: {data.get('user', {}).get('email')}")
    print(f"  Role: {data.get('user', {}).get('role')}")
    print(f"  Token saved to .test_token")
else:
    print(f"✗ Login failed with status {response.status_code}")
    print(f"  Response: {response.text}")