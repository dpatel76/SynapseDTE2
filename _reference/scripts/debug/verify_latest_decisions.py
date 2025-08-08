#!/usr/bin/env python3
"""Verify we're getting the latest decisions"""

import asyncio
import httpx

async def test():
    async with httpx.AsyncClient() as client:
        # Login as tester
        login = await client.post('http://localhost:8001/api/v1/auth/login', 
            json={'email': 'tester@example.com', 'password': 'password123'})
        
        if login.status_code != 200:
            print(f"Login failed: {login.status_code}")
            return
            
        token = login.json()['access_token']
        
        # Get decisions
        resp = await client.get('http://localhost:8001/api/v1/scoping/cycles/13/reports/156/decisions',
            headers={'Authorization': f'Bearer {token}'})
        
        if resp.status_code == 200:
            decisions = resp.json()
            
            # Find the specific attributes we know were in v2
            print("Looking for v2 scoped attributes:")
            scoped_attrs = [d for d in decisions if d['final_scoping']]
            
            print(f"\nFound {len(scoped_attrs)} scoped attributes:")
            for attr in scoped_attrs:
                print(f"  - {attr['attribute_name']}")
                if attr.get('tester_rationale'):
                    print(f"    Rationale: {attr['tester_rationale']}")
                    
            # Check count matches v2
            print(f"\nExpected 5 scoped attributes (v2), got {len(scoped_attrs)}")
        else:
            print(f"Error: {resp.text}")

if __name__ == "__main__":
    asyncio.run(test())