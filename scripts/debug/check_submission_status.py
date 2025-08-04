#!/usr/bin/env python3
"""Check submission status"""

import asyncio
import httpx
import json
from datetime import datetime

async def check_status():
    async with httpx.AsyncClient() as client:
        # Login as Jane
        login = await client.post('http://localhost:8001/api/v1/auth/login', 
            json={'email': 'tester@example.com', 'password': 'password123'})
        
        if login.status_code != 200:
            print(f"Login failed: {login.status_code}")
            return
            
        token = login.json()['access_token']
        
        # Get analytics/status
        resp = await client.get(
            'http://localhost:8001/api/v1/sample-selection/cycles/13/reports/156/samples/analytics',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        if resp.status_code == 200:
            data = resp.json()
            print("\n=== Sample Selection Phase Status ===")
            print(f"Phase Status: {data.get('phase_status', 'Unknown')}")
            print(f"Total Samples: {data.get('total_samples', 0)}")
            print(f"Included: {data.get('included_samples', 0)}")
            print(f"Excluded: {data.get('excluded_samples', 0)}")
            print(f"Pending Decision: {data.get('pending_samples', 0)}")
            print(f"Submitted: {data.get('submitted_samples', 0)}")
            print(f"Total Submissions: {data.get('total_submissions', 0)}")
            
            if data.get('latest_submission'):
                print(f"\nLatest Submission:")
                print(f"  Version: {data['latest_submission']['version']}")
                print(f"  Status: {data['latest_submission']['status']}")
                print(f"  Submitted At: {data['latest_submission']['submitted_at']}")

if __name__ == "__main__":
    asyncio.run(check_status())