#!/usr/bin/env python3
"""Test versioning workflow"""

import asyncio
import httpx
import json

async def test():
    async with httpx.AsyncClient() as client:
        print("=== VERSIONING WORKFLOW TEST ===")
        
        # Login as tester
        login = await client.post('http://localhost:8001/api/v1/auth/login', 
            json={'email': 'jane.doe@example.com', 'password': 'password123'})
        token = login.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        
        # Check current status
        print("\n1. Checking current status...")
        analytics = await client.get(
            'http://localhost:8001/api/v1/sample-selection/cycles/13/reports/156/samples/analytics',
            headers=headers
        )
        
        if analytics.status_code == 200:
            data = analytics.json()
            print(f"Phase Status: {data['phase_status']}")
            print(f"Total Submissions: {data.get('total_submissions', 0)}")
            if data.get('latest_submission'):
                print(f"Latest Submission Version: {data['latest_submission']['version']}")
                print(f"Latest Submission Status: {data['latest_submission']['status']}")
        
        # Check samples and their versions
        print("\n2. Checking sample versions...")
        samples_resp = await client.get(
            'http://localhost:8001/api/v1/sample-selection/cycles/13/reports/156/samples?include_feedback=true',
            headers=headers
        )
        
        if samples_resp.status_code == 200:
            samples = samples_resp.json()['samples']
            print(f"Total samples: {len(samples)}")
            
            # Group by version
            versions = {}
            for sample in samples:
                version = sample.get('version_number', 1)
                if version not in versions:
                    versions[version] = []
                versions[version].append(sample['sample_id'])
            
            for version, sample_ids in sorted(versions.items()):
                print(f"\nVersion {version}: {len(sample_ids)} samples")
                for sid in sample_ids[:3]:  # Show first 3
                    print(f"  - {sid}")
                if len(sample_ids) > 3:
                    print(f"  ... and {len(sample_ids) - 3} more")

if __name__ == "__main__":
    asyncio.run(test())