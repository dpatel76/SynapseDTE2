#!/usr/bin/env python3
"""Test generating exactly 2 samples"""

import asyncio
import httpx
import json

async def test():
    async with httpx.AsyncClient() as client:
        # Login as tester
        login = await client.post('http://localhost:8001/api/v1/auth/login', 
            json={'email': 'tester@synapse.com', 'password': 'TestUser123!'})
        
        if login.status_code != 200:
            print(f"Login failed: {login.status_code}")
            return
            
        token = login.json()['access_token']
        
        # Generate exactly 2 samples
        payload = {
            "sample_size": 2,  # Generate only 2 samples
            "sample_type": "Population Sample",
            "regulatory_context": "FR Y-14M Schedule D.1"
        }
        
        print("Generating 2 samples...")
        resp = await client.post(
            'http://localhost:8001/api/v1/sample-selection/cycles/13/reports/156/samples/generate',
            json=payload,
            headers={'Authorization': f'Bearer {token}'},
            timeout=60.0
        )
        
        print(f'Generate Status: {resp.status_code}')
        if resp.status_code == 200:
            result = resp.json()
            print(f"Success! Generated {result.get('samples_generated', 0)} samples")
            print(f"Message: {result.get('message', '')}")
        else:
            print(f"Error: {resp.text}")
            
        # Now check the samples
        print("\nChecking generated samples...")
        resp = await client.get(
            'http://localhost:8001/api/v1/sample-selection/cycles/13/reports/156/samples',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        if resp.status_code == 200:
            data = resp.json()
            print(f'\nTotal samples found: {len(data["cycle_report_sample_selection_samples"])}\n')
            
            for i, sample in enumerate(data['samples']):
                print(f'Sample {i+1}:')
                print(f'  ID: {sample["sample_id"]}')
                print(f'  Sample Data: {json.dumps(sample["sample_data"], indent=4)}')
                print()

if __name__ == "__main__":
    asyncio.run(test())