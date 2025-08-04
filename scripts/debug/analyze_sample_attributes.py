#!/usr/bin/env python3
"""Analyze attributes in generated samples"""

import asyncio
import httpx

async def analyze():
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
            if data['samples']:
                sample = data['samples'][0]
                print(f'Number of attributes in sample: {len(sample["sample_data"])}')
                print()
                
                # Check if it includes our 5 scoped attributes
                scoped = ['Reference Number', 'Bank ID', 'Period ID', 'Customer ID', 'Product Type']
                print("Checking for scoped attributes:")
                for attr in scoped:
                    if attr in sample['sample_data']:
                        print(f'✓ Found: {attr} = {sample["sample_data"][attr]}')
                    else:
                        print(f'✗ Missing: {attr}')

if __name__ == "__main__":
    asyncio.run(analyze())