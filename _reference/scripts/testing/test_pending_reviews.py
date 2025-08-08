#!/usr/bin/env python3
"""Test pending reviews endpoint"""

import asyncio
import httpx

async def test():
    async with httpx.AsyncClient() as client:
        # Login as report owner
        login = await client.post('http://localhost:8001/api/v1/auth/login', 
            json={'email': 'report.owner@example.com', 'password': 'password123'})
        
        if login.status_code != 200:
            print(f"Login failed: {login.status_code}")
            return
            
        token = login.json()['access_token']
        
        # Get pending reviews
        resp = await client.get(
            'http://localhost:8001/api/v1/sample-selection/pending-reviews',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"\nPending Reviews: {len(data)}")
            for review in data:
                print(f"\n- Report: {review['report_name']}")
                print(f"  Version: {review['version_number']}")
                print(f"  Submitted: {review['submitted_at']}")
                print(f"  By: {review['submitted_by']}")
                print(f"  Samples: {review['sample_count']}")
        else:
            print(f"Error: {resp.text}")

if __name__ == "__main__":
    asyncio.run(test())