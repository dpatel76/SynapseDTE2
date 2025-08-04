import requests
import json

BASE_URL = "http://localhost:8000"

# Login as tester
login_response = requests.post(
    f"{BASE_URL}/api/v1/auth/login",
    json={"email": "tester@example.com", "password": "password123"}
)

if login_response.status_code != 200:
    print(f"Failed to login: {login_response.text}")
    exit(1)

auth_token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {auth_token}"}

print("Checking test executions...")

# Get test executions
executions_response = requests.get(
    f"{BASE_URL}/api/v1/test-execution/3/reports/3/executions",
    headers=headers
)

print(f"Response status: {executions_response.status_code}")
if executions_response.status_code == 200:
    data = executions_response.json()
    print(f"Response type: {type(data)}")
    if isinstance(data, list):
        print(f"Number of executions: {len(data)}")
        if data:
            print(f"First execution: {json.dumps(data[0], indent=2)}")
    else:
        print(f"Response: {json.dumps(data, indent=2)}")
else:
    print(f"Error: {executions_response.text}")