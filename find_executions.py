import requests
import json

# Authentication
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

print("Finding test executions...")

# Try different cycle/report combinations
for cycle_id in [1, 2, 3]:
    for report_id in [1, 2, 3]:
        executions_response = requests.get(
            f"{BASE_URL}/api/v1/test-execution/{cycle_id}/reports/{report_id}/executions",
            headers=headers
        )
        
        if executions_response.status_code == 200:
            executions = executions_response.json()
            if executions:
                print(f"\nFound {len(executions)} executions for cycle {cycle_id}, report {report_id}")
                
                # Look for document executions
                for execution in executions[:5]:  # Show first 5
                    if execution.get('analysis_method') == 'llm_analysis':
                        print(f"  - Test case {execution['test_case_id']}: {execution['status']} (Document evidence)")
                        analysis = execution.get('analysis_results', {})
                        if 'primary_key_values' in analysis:
                            print(f"    Has primary keys: {list(analysis['primary_key_values'].keys())}")
                break
    else:
        continue
    break