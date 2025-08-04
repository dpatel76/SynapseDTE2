#!/usr/bin/env python3
"""Mark samples S007 and S009 as include"""

import asyncio
import httpx

async def mark_samples():
    async with httpx.AsyncClient() as client:
        # Login as Jane
        login = await client.post('http://localhost:8001/api/v1/auth/login', 
            json={'email': 'tester@example.com', 'password': 'password123'})
        
        if login.status_code != 200:
            print(f"Login failed: {login.status_code}")
            return
            
        token = login.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        
        # Mark S007 as include
        print("Marking C13_R156_S007 as include...")
        resp = await client.put(
            'http://localhost:8001/api/v1/sample-selection/cycles/13/reports/156/samples/C13_R156_S007/decision',
            json={'decision': 'include', 'notes': 'Good sample for testing'},
            headers=headers
        )
        print(f"Response: {resp.status_code}")
        if resp.status_code != 200:
            print(f"Error: {resp.text}")
        
        # Mark S009 as include  
        print("\nMarking C13_R156_S009 as include...")
        resp = await client.put(
            'http://localhost:8001/api/v1/sample-selection/cycles/13/reports/156/samples/C13_R156_S009/decision',
            json={'decision': 'include', 'notes': 'Another good sample'},
            headers=headers
        )
        print(f"Response: {resp.status_code}")
        if resp.status_code != 200:
            print(f"Error: {resp.text}")
            
        # Now submit for approval
        print("\nSubmitting included samples for approval...")
        resp = await client.post(
            'http://localhost:8001/api/v1/sample-selection/cycles/13/reports/156/samples/submit',
            json={'sample_ids': ['C13_R156_S007', 'C13_R156_S009'], 'notes': 'Submitting 2 samples for review'},
            headers=headers
        )
        print(f"Submit response: {resp.status_code}")
        if resp.status_code == 200:
            print("Success! Samples submitted for approval")
        else:
            print(f"Error: {resp.text}")

if __name__ == "__main__":
    asyncio.run(mark_samples())