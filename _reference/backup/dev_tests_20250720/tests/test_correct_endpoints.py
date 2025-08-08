"""
Test API with correct endpoint paths
"""
import requests
import json

BASE_URL = "http://localhost:8001"

def test_login():
    """Test login with JSON format"""
    login_data = {
        "username": "tester1",
        "password": "TestPass123!"
    }
    
    print("Testing login endpoint with JSON...")
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json=login_data  # Send as JSON
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Success! Token received")
        return data.get("access_token")
    else:
        print(f"Failed: {response.text}")
        
        # Try with different credentials
        print("\nTrying with admin credentials...")
        login_data = {
            "username": "admin",
            "password": "AdminPass123!"
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json=login_data
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Success! Token received")
            return data.get("access_token")
        else:
            print(f"Failed: {response.text}")
            return None

def test_correct_endpoints(token):
    """Test with correct endpoint paths"""
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    # Correct endpoint paths based on api.py
    endpoints = [
        "/api/v1/cycles/",
        "/api/v1/reports/",
        "/api/v1/planning/",
        "/api/v1/scoping/",
        "/api/v1/sample-selection/",
        "/api/v1/data-owner/",
        "/api/v1/request-info/",
        "/api/v1/testing-execution/",
        "/api/v1/observation-management/"
    ]
    
    print("\nTesting endpoints...")
    for endpoint in endpoints:
        response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
        status = "✅" if response.status_code in [200, 201] else "❌"
        print(f"{status} {endpoint}: {response.status_code}")

def test_create_test_user():
    """Try to create a test user"""
    print("\nAttempting to create test user...")
    # First check if we can reach the database
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        print("Backend is healthy")
    
    # Try to access auth test endpoint
    response = requests.get(f"{BASE_URL}/api/v1/auth/test-db")
    print(f"Database test: {response.status_code}")

if __name__ == "__main__":
    test_create_test_user()
    token = test_login()
    test_correct_endpoints(token)