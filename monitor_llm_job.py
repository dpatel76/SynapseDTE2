#!/usr/bin/env python3
"""Monitor LLM job progress"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
TESTER_EMAIL = "tester@example.com"
TESTER_PASSWORD = "password123"

def get_auth_token():
    """Get JWT token for tester user"""
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"email": TESTER_EMAIL, "password": TESTER_PASSWORD}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Failed to login: {response.status_code} - {response.text}")
        return None

def get_latest_job():
    """Get the latest LLM job"""
    token = get_auth_token()
    if not token:
        return None
        
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get all jobs
    response = requests.get(
        f"{BASE_URL}/api/v1/jobs",
        headers=headers
    )
    
    if response.status_code == 200:
        jobs = response.json()
        # Filter for LLM jobs
        llm_jobs = [j for j in jobs if 'llm' in j.get('job_type', '').lower() or 'scoping' in j.get('job_type', '').lower()]
        if llm_jobs:
            # Sort by created_at descending and get the latest
            llm_jobs.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            return llm_jobs[0]
    return None

def monitor_job(job_id):
    """Monitor a specific job"""
    token = get_auth_token()
    if not token:
        return
        
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"\nMonitoring job: {job_id}")
    print("-" * 80)
    
    last_status = None
    last_progress = None
    
    while True:
        response = requests.get(
            f"{BASE_URL}/api/v1/jobs/{job_id}/status",
            headers=headers
        )
        
        if response.status_code == 200:
            job_data = response.json()
            status = job_data.get('status', 'unknown')
            progress = job_data.get('progress', {})
            current_step = progress.get('current_step', 'N/A')
            percentage = progress.get('percentage', 0)
            
            # Only print if something changed
            if status != last_status or current_step != last_progress:
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] Status: {status} | Step: {current_step} | Progress: {percentage}%")
                
                if 'error' in job_data:
                    print(f"  ERROR: {job_data['error']}")
                
                if 'result' in job_data and job_data['result']:
                    result = job_data['result']
                    if isinstance(result, dict):
                        processed = result.get('processed', 0)
                        failed = result.get('failed', 0)
                        total = result.get('total', 0)
                        print(f"  Processed: {processed}/{total} | Failed: {failed}")
                
                last_status = status
                last_progress = current_step
            
            # Check if job is complete
            if status in ['completed', 'failed', 'cancelled']:
                print(f"\nJob {status}!")
                if status == 'completed' and 'result' in job_data:
                    result = job_data['result']
                    print("\nFinal Results:")
                    print(json.dumps(result, indent=2))
                break
        else:
            print(f"Failed to get job status: {response.status_code}")
            break
        
        time.sleep(2)  # Poll every 2 seconds

def main():
    # Get the latest job
    job = get_latest_job()
    
    if job:
        job_id = job.get('job_id')
        job_type = job.get('job_type', 'Unknown')
        created_at = job.get('created_at', '')
        
        print(f"Found latest LLM job:")
        print(f"  Job ID: {job_id}")
        print(f"  Type: {job_type}")
        print(f"  Created: {created_at}")
        
        monitor_job(job_id)
    else:
        print("No LLM jobs found. Waiting for new job...")
        
        # Keep checking for new jobs
        while True:
            job = get_latest_job()
            if job:
                print(f"\nNew job detected: {job.get('job_id')}")
                monitor_job(job.get('job_id'))
                break
            time.sleep(5)

if __name__ == "__main__":
    main()