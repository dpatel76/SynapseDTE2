"""
Manual API testing script
"""
import requests
import json

BASE_URL = "http://localhost:8001"

def test_login():
    """Test login with correct format"""
    # Try form data format
    login_data = {
        "username": "tester1",
        "password": "TestPass123!"
    }
    
    print("Testing login endpoint...")
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        data=login_data  # Form data, not JSON
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Success! Token: {data.get('access_token')[:20]}...")
        return data.get('access_token')
    else:
        print(f"Failed: {response.text}")
        return None

def test_endpoints_with_token(token):
    """Test various endpoints with auth token"""
    headers = {"Authorization": f"Bearer {token}"}
    
    endpoints = [
        "/api/v1/users/me",
        "/api/v1/cycles",
        "/api/v1/reports"
    ]
    
    for endpoint in endpoints:
        print(f"\nTesting {endpoint}...")
        response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {json.dumps(response.json(), indent=2)[:200]}...")

def test_docs():
    """Test API documentation"""
    print("\nTesting OpenAPI docs...")
    response = requests.get(f"{BASE_URL}/openapi.json")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"API Title: {data.get('info', {}).get('title')}")
        print(f"Version: {data.get('info', {}).get('version')}")
        print(f"Total Paths: {len(data.get('paths', {}))}")

if __name__ == "__main__":
    test_docs()
    token = test_login()
    if token:
        test_endpoints_with_token(token)