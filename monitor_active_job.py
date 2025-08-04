#!/usr/bin/env python3
"""Monitor active scoping job progress"""

import json
import time
import sys

JOB_ID = "814d32d2-3b4e-481b-861c-54133f1a6ac9"
JOBS_FILE = "jobs_storage.json"

print(f"Monitoring job {JOB_ID[:8]}...\n")

previous_step = ""
while True:
    try:
        with open(JOBS_FILE, 'r') as f:
            jobs = json.load(f)
        
        if JOB_ID in jobs:
            job = jobs[JOB_ID]
            status = job['status']
            progress = job['progress_percentage']
            current_step = job['current_step']
            
            # Print update if step changed or status changed
            if current_step != previous_step or status in ['completed', 'failed']:
                print(f"[{time.strftime('%H:%M:%S')}] Status: {status} | Progress: {progress}% | Step: {current_step}")
                previous_step = current_step
            
            if status == 'completed':
                print("\n✅ Job completed successfully!")
                if job.get('result'):
                    print(f"Result: {job['result'].get('message', 'No message')}")
                break
            elif status == 'failed':
                print(f"\n❌ Job failed!")
                if job.get('error'):
                    print(f"Error: {job['error']}")
                break
        else:
            print(f"Job {JOB_ID} not found in storage")
            break
            
    except Exception as e:
        print(f"Error reading job status: {e}")
        
    time.sleep(2)