#!/usr/bin/env python3
import requests

# Login
login_resp = requests.post("http://localhost:8001/api/v1/auth/login", 
    json={"email": "test_tester@synapse.com", "password": "TestUser123!"})
token = login_resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Get failed executions
exec_resp = requests.get("http://localhost:8001/api/v1/testing-execution/9/reports/156/executions", headers=headers)
executions = [e for e in exec_resp.json() if e.get("result") in ["Fail", "Inconclusive"]]

if executions:
    # Try to create observation
    obs_data = {
        "test_execution_id": executions[0]["execution_id"],
        "observation_title": "Test Issue",
        "observation_description": "Test failed",
        "observation_type": "DATA_QUALITY",
        "severity": "MEDIUM",
        "impact_description": "Test impact"
    }
    
    obs_resp = requests.post(
        "http://localhost:8001/api/v1/observation-management/9/reports/156/observations/from-test-result",
        headers=headers,
        json=obs_data
    )
    
    print(f"Status: {obs_resp.status_code}")
    print(f"Response: {obs_resp.text}")
else:
    print("No failed executions found")