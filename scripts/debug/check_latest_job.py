#!/usr/bin/env python3
"""Check the latest scoping job for cycle 13"""

import json
from datetime import datetime

# Load jobs
with open('jobs_storage.json', 'r') as f:
    data = json.load(f)

# Find cycle 13 jobs
cycle_13_jobs = []
for job_id, job_data in data.items():
    if isinstance(job_data, dict) and job_data.get('metadata', {}).get('cycle_id') == 13:
        cycle_13_jobs.append((job_id, job_data))

# Sort by created_at
cycle_13_jobs.sort(key=lambda x: x[1].get('created_at', ''), reverse=True)

if cycle_13_jobs:
    latest_job_id, latest_job = cycle_13_jobs[0]
    print(f"Latest Job ID: {latest_job_id}")
    print(f"Status: {latest_job.get('status')}")
    print(f"Created: {latest_job.get('created_at')}")
    print(f"Started: {latest_job.get('started_at', 'Not started')}")
    print(f"Completed: {latest_job.get('completed_at', 'Not completed')}")
    
    if latest_job.get('completed_at') and latest_job.get('created_at'):
        start = datetime.fromisoformat(latest_job['created_at'])
        end = datetime.fromisoformat(latest_job['completed_at'])
        duration = (end - start).total_seconds()
        print(f"Duration: {duration:.2f} seconds")
    
    print(f"\nMetadata:")
    for key, value in latest_job.get('metadata', {}).items():
        print(f"  {key}: {value}")
    
    if latest_job.get('error'):
        print(f"\nError: {latest_job['error']}")
    
    if latest_job.get('result'):
        print(f"\nResult: {json.dumps(latest_job['result'], indent=2)[:200]}...")
else:
    print("No jobs found for cycle 13")