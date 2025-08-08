#!/usr/bin/env python3
"""Check current running job for cycle 13"""

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

# Show last 3 jobs
print("Recent cycle 13 jobs:\n")
for i, (job_id, job) in enumerate(cycle_13_jobs[:3]):
    created = datetime.fromisoformat(job['created_at']) if job.get('created_at') else None
    
    print(f"{i+1}. Job ID: {job_id}")
    print(f"   Status: {job.get('status')}")
    print(f"   Created: {created.strftime('%Y-%m-%d %H:%M:%S') if created else 'Unknown'}")
    
    if job.get('status') == 'running':
        print(f"   Progress: {job.get('progress', 0)}%")
        print(f"   Message: {job.get('message', 'No message')}")
        print(f"   Current step: {job.get('current_step', 'Unknown')}")
        if job.get('metadata'):
            print(f"   Completed steps: {job['metadata'].get('completed_steps', 0)} / {job['metadata'].get('total_steps', '?')}")
    elif job.get('status') == 'completed':
        if job.get('completed_at'):
            completed = datetime.fromisoformat(job['completed_at'])
            duration = (completed - created).total_seconds() if created else 0
            print(f"   Duration: {duration:.1f} seconds")
        if job.get('result'):
            print(f"   Recommendations generated: {job['result'].get('recommendations_generated', 0)}")
    
    print()