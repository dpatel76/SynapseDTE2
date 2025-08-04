#!/usr/bin/env python3
"""Check generated samples"""

import asyncio
import httpx
import json

async def check_samples():
    async with httpx.AsyncClient() as client:
        # Login
        login = await client.post('http://localhost:8001/api/v1/auth/login', 
            json={'email': 'tester@synapse.com', 'password': 'TestUser123!'})
        
        if login.status_code != 200:
            print(f"Login failed: {login.status_code}")
            return
            
        token = login.json()['access_token']
        
        # Get samples
        resp = await client.get(
            'http://localhost:8001/api/v1/sample-selection/cycles/13/reports/156/samples',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        if resp.status_code == 200:
            data = resp.json()
            print(f'Found {len(data["cycle_report_sample_selection_samples"])} samples\n')
            
            # Show first 2 samples
            for i, sample in enumerate(data['samples'][:2]):
                print(f'=== Sample {i+1} ===')
                print(f'Sample ID: {sample["sample_id"]}')
                print(f'Generation Method: {sample.get("generation_method", "Unknown")}')
                print(f'Sample Data:')
                print(json.dumps(sample['sample_data'], indent=2))
                print()
        else:
            print(f'Error: {resp.status_code} - {resp.text}')

if __name__ == "__main__":
    asyncio.run(check_samples())