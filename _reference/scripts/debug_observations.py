#!/usr/bin/env python3

import requests
import json

BASE_URL = "http://localhost:8001/api/v1"

# Login as tester
print("=== Login as tester ===")
login = requests.post(
    f"{BASE_URL}/auth/login",
    json={"email": "tester@example.com", "password": "password123"}
)

token = login.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Get observations
cycle_id = 58
report_id = 156

print("\n=== Getting observation groups ===")
response = requests.get(
    f"{BASE_URL}/observation-enhanced/{cycle_id}/reports/{report_id}/observation-groups",
    headers=headers
)

if response.status_code == 200:
    groups = response.json()
    print(f"Found {len(groups)} groups")
    print("\nFull response structure:")
    print(json.dumps(groups, indent=2))
else:
    print(f"Failed: {response.status_code}")
    print(response.text)

# Also check database directly
print("\n=== Database observation data ===")
import subprocess
result = subprocess.run([
    "bash", "-c",
    f"PGPASSWORD=synapse_password psql -h localhost -p 5433 -U synapse_user -d synapse_dt -c \"SELECT observation_id, observation_title, status, tester_decision, report_owner_decision, approval_status FROM cycle_report_observation_mgmt_observation_records WHERE phase_id = 481;\""
], capture_output=True, text=True)
print(result.stdout)