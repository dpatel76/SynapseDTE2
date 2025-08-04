#\!/usr/bin/env python3
"""
Find a valid test execution ID
"""
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Get token
response = requests.post(f"{BASE_URL}/auth/login", json={"email": "tester@example.com", "password": "password123"})
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

print("=== Finding Test Executions ===\n")

# Get test execution results
response = requests.get(
    f"{BASE_URL}/test-execution/58/reports/156/executions", 
    headers=headers
)

if response.status_code == 200:
    executions = response.json()
    print(f"Found {len(executions)} test executions")
    
    # Find failed executions
    failed = [e for e in executions if e.get('test_result') == 'fail']
    print(f"Found {len(failed)} failed test executions")
    
    if failed:
        print("\nFirst 5 failed executions:")
        for e in failed[:5]:
            print(f"  ID: {e.get('execution_id')}, Test: {e.get('test_name')}, Result: {e.get('test_result')}")
else:
    print(f"Error: {response.status_code} - {response.text}")
