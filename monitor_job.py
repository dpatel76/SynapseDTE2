#!/usr/bin/env python3
"""Monitor job progress"""

import requests
import time
import json

# Configuration
BASE_URL = "http://localhost:8000"

# Login first
login_data = {
    "email": "tester@example.com",
    "password": "password123"
}

session = requests.Session()
login_response = session.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
if login_response.status_code != 200:
    print(f"Login failed: {login_response.text}")
    exit(1)

token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

print("=== MONITORING JOB PROGRESS ===\n")

# Get recent jobs
response = session.get(f"{BASE_URL}/api/v1/jobs", headers=headers)
if response.status_code == 200:
    jobs = response.json()
    
    # Find the most recent scoping recommendation job
    scoping_jobs = [j for j in jobs if j.get('job_type') == 'scoping_recommendations']
    scoping_jobs.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    if scoping_jobs:
        latest_job = scoping_jobs[0]
        job_id = latest_job['job_id']
        
        print(f"Latest scoping recommendation job: {job_id[:8]}...")
        print(f"Status: {latest_job['status']}")
        print(f"Created: {latest_job.get('created_at', 'N/A')}")
        
        # Monitor progress
        print("\nMonitoring progress...")
        while True:
            # Get job status
            status_response = session.get(f"{BASE_URL}/api/v1/jobs/{job_id}/status", headers=headers)
            if status_response.status_code == 200:
                status = status_response.json()
                print(f"\r[{time.strftime('%H:%M:%S')}] Status: {status['status']} | Progress: {status.get('progress', 0)}% | Step: {status.get('current_step', 'N/A')}", end='')
                
                if status['status'] in ['completed', 'failed']:
                    print(f"\n\nJob {status['status']}!")
                    if status.get('error'):
                        print(f"Error: {status['error']}")
                    break
            else:
                print(f"\nError getting job status: {status_response.status_code}")
                break
                
            time.sleep(2)
        
        # Check if attributes were imported
        print("\n\nChecking if attributes were imported...")
        attrs_response = session.get(
            f"{BASE_URL}/api/v1/scoping/cycles/55/reports/156/attributes",
            headers=headers
        )
        if attrs_response.status_code == 200:
            attrs = attrs_response.json()
            print(f"Attributes in scoping: {len(attrs)}")
        else:
            print(f"Error getting attributes: {attrs_response.status_code}")
    else:
        print("No scoping recommendation jobs found")
else:
    print(f"Error getting jobs: {response.status_code}")