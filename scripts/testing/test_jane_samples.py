#!/usr/bin/env python3
"""Test sample generation as Jane (the assigned tester)"""

import asyncio
import httpx
import json

async def test():
    async with httpx.AsyncClient() as client:
        # Login as Jane (the assigned tester)
        print("Logging in as Jane Doe (tester@example.com)...")
        login = await client.post('http://localhost:8001/api/v1/auth/login', 
            json={'email': 'tester@example.com', 'password': 'password123'})
        
        if login.status_code != 200:
            print(f"Login failed: {login.status_code}")
            print(f"Response: {login.text}")
            return
            
        token = login.json()['access_token']
        print("Login successful!")
        
        # First, check existing samples
        print("\nChecking existing samples...")
        resp = await client.get(
            'http://localhost:8001/api/v1/sample-selection/cycles/13/reports/156/samples',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        if resp.status_code == 200:
            data = resp.json()
            print(f'Current samples: {len(data["cycle_report_sample_selection_samples"])}')
            for s in data['samples']:
                print(f'  - {s["sample_id"]} by {s.get("generated_by", "Unknown")}')
        
        # Generate 2 new samples as Jane
        print("\nGenerating 2 samples as Jane...")
        payload = {
            "sample_size": 2,
            "sample_type": "Population Sample",
            "regulatory_context": "FR Y-14M Schedule D.1"
        }
        
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
        else:
            print(f"Error: {resp.text}")
            
        # Check samples again
        print("\nChecking samples after generation...")
        resp = await client.get(
            'http://localhost:8001/api/v1/sample-selection/cycles/13/reports/156/samples',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        if resp.status_code == 200:
            data = resp.json()
            print(f'Total samples now: {len(data["cycle_report_sample_selection_samples"])}')
            for s in data['samples']:
                print(f'  - {s["sample_id"]} by {s.get("generated_by", "Unknown")}')

if __name__ == "__main__":
    asyncio.run(test())