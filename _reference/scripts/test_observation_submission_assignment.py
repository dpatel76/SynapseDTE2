#!/usr/bin/env python3

import requests
import json
import time

BASE_URL = "http://localhost:8001/api/v1"

time.sleep(10)  # Wait for backend to start

# Login as tester
print("=== Login as tester ===")
login = requests.post(
    f"{BASE_URL}/auth/login",
    json={"email": "tester@example.com", "password": "password123"}
)

if login.status_code != 200:
    print(f"Login failed: {login.status_code}")
    exit(1)

token = login.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("✅ Login successful")

# Get observations to submit
print("\n=== Getting observations ===")
response = requests.get(
    f"{BASE_URL}/observation-enhanced/58/reports/156/observations",
    headers=headers
)

if response.status_code == 200:
    observations = response.json()
    print(f"Found {len(observations)} observations")
    observation_ids = [obs["observation_id"] for obs in observations]
    print(f"Observation IDs: {observation_ids}")
else:
    print(f"Failed to get observations: {response.status_code}")
    exit(1)

# Submit observations for approval
print("\n=== Submitting observations for approval ===")
submit_data = {
    "observation_ids": observation_ids,
    "submission_notes": "Submitting observations for report owner review"
}

response = requests.post(
    f"{BASE_URL}/observation-enhanced/58/reports/156/versions/create-and-submit",
    json=submit_data,
    headers=headers
)

print(f"Status: {response.status_code}")
if response.status_code == 200:
    print("✅ Observations submitted successfully")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
else:
    print(f"❌ Failed to submit observations")
    print(f"Error: {response.text}")

# Check if assignment was created
print("\n=== Checking for new assignments ===")
import subprocess
result = subprocess.run([
    "bash", "-c",
    """PGPASSWORD=synapse_password psql -h localhost -p 5433 -U synapse_user -d synapse_dt -c "SELECT assignment_id, assignment_type, title, status, created_at FROM universal_assignments WHERE context_data::text LIKE '%\\"cycle_id\\": 58%' AND context_data::text LIKE '%\\"report_id\\": 156%' AND assignment_type = 'Observation Approval' ORDER BY created_at DESC LIMIT 1;" """
], capture_output=True, text=True)

print("Database query result:")
print(result.stdout)

# Also check report owner assignments
print("\n=== Checking report owner assignments ===")
result2 = subprocess.run([
    "bash", "-c",
    """PGPASSWORD=synapse_password psql -h localhost -p 5433 -U synapse_user -d synapse_dt -c "SELECT assignment_id, to_user_id, title, description FROM universal_assignments WHERE context_data::text LIKE '%\\"cycle_id\\": 58%' AND context_data::text LIKE '%\\"report_id\\": 156%' AND to_role = 'Report Owner' AND assignment_type = 'Observation Approval';" """
], capture_output=True, text=True)

print("Report owner assignments:")
print(result2.stdout)