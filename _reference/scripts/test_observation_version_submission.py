#!/usr/bin/env python3

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8001/api/v1"

# Login as tester
print("=== Logging in as tester ===")
login_response = requests.post(
    f"{BASE_URL}/auth/login",
    json={"email": "tester@example.com", "password": "password123"}
)

if login_response.status_code != 200:
    print(f"❌ Login failed: {login_response.status_code}")
    print(login_response.text)
    exit(1)

token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("✅ Login successful")

# Get phases
print("\n=== Getting phases ===")
phases_response = requests.get(f"{BASE_URL}/workflow/phases", headers=headers)
if phases_response.status_code != 200:
    print(f"❌ Failed to get phases: {phases_response.status_code}")
    print(phases_response.text)
    exit(1)

# Need to get phases for current test cycle/report
# First get test cycles
cycles_response = requests.get(f"{BASE_URL}/cycles", headers=headers)
if cycles_response.status_code != 200:
    print(f"❌ Failed to get test cycles: {cycles_response.status_code}")
    exit(1)

cycles = cycles_response.json()
print(f"Cycles response: {json.dumps(cycles, indent=2)}")

# Check if it's a paginated response
if isinstance(cycles, dict) and "cycles" in cycles:
    cycles_list = cycles["cycles"]
elif isinstance(cycles, list):
    cycles_list = cycles
else:
    print("❌ Unexpected cycles response format")
    exit(1)

if not cycles_list:
    print("❌ No test cycles found")
    exit(1)

# Look for cycle 58 which has observations, or use the first one
cycle = next((c for c in cycles_list if c["cycle_id"] == 58), cycles_list[0])
cycle_id = cycle["cycle_id"]
print(f"✅ Using test cycle: {cycle_id} - {cycle['cycle_name']}")

# Get reports for this cycle - try different endpoint formats
reports_response = requests.get(f"{BASE_URL}/cycles/{cycle_id}/reports", headers=headers)
if reports_response.status_code == 404:
    # Try alternative endpoint
    reports_response = requests.get(f"{BASE_URL}/reports?cycle_id={cycle_id}", headers=headers)
if reports_response.status_code != 200:
    print(f"❌ Failed to get reports: {reports_response.status_code}")
    exit(1)

reports = reports_response.json()
print(f"Reports response: {json.dumps(reports, indent=2) if isinstance(reports, (dict, list)) else reports}")

# Handle different response formats
if isinstance(reports, dict) and "reports" in reports:
    reports_list = reports["reports"]
elif isinstance(reports, list):
    reports_list = reports
else:
    print("❌ Unexpected reports response format")
    exit(1)

if not reports_list:
    print("❌ No reports found")
    exit(1)

report = reports_list[0]
# Try different id field names
report_id = report.get("report_id") or report.get("id")
print(f"✅ Using report: {report_id}")

# We know from database that cycle 58, report 156 has observations
# Let's query the database directly to get the phase_id
print("\n=== Getting Observation phase ID ===")
# For now, let's use the phase_id we know exists from our database query
# In a real scenario, we would get this from the API
phase_id = 481  # This is the phase_id for cycle 58, report 156, phase "Observations"
print(f"✅ Using Observation Management phase: {phase_id}")

# Get observation groups
print("\n=== Getting observation groups ===")
groups_response = requests.get(
    f"{BASE_URL}/observation-enhanced/{cycle_id}/reports/{report_id}/observation-groups",
    headers=headers
)

if groups_response.status_code != 200:
    print(f"❌ Failed to get observation groups: {groups_response.status_code}")
    print(groups_response.text)
    exit(1)

groups = groups_response.json()
print(f"✅ Found {len(groups)} observation groups")

# Get all observation IDs from the groups
observation_ids = []
for group in groups:
    if "observations" in group and group["observations"]:
        for obs in group["observations"]:
            observation_ids.append(obs["observation_id"])

print(f"Observation IDs to submit: {observation_ids}")

# Test observation version submission
print("\n=== Testing observation version submission ===")
version_response = requests.post(
    f"{BASE_URL}/observation-enhanced/{cycle_id}/reports/{report_id}/versions/create-and-submit",
    json={
        "observation_ids": observation_ids,
        "submission_notes": "Submitting observations for review"
    },
    headers=headers
)

print(f"Response status: {version_response.status_code}")
if version_response.status_code == 200:
    print("✅ Version submission successful!")
    version_data = version_response.json()
    print(json.dumps(version_data, indent=2))
else:
    print(f"❌ Version submission failed: {version_response.status_code}")
    print(version_response.text)

# Check observation statuses after submission
print("\n=== Checking observation statuses after submission ===")
groups_response2 = requests.get(
    f"{BASE_URL}/observation-enhanced/{cycle_id}/reports/{report_id}/observation-groups",
    headers=headers
)

if groups_response2.status_code == 200:
    groups2 = groups_response2.json()
    for group in groups2:
        obs = group["observations"][0] if group["observations"] else None
        if obs:
            print(f"Observation {obs['observation_id']}: {obs.get('observation_title', 'N/A')} - Status: {obs.get('status', 'N/A')}")