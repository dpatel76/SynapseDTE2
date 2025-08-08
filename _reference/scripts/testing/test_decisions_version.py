#!/usr/bin/env python3
"""Test the decisions endpoint returns only latest version"""

import asyncio
import httpx

async def test():
    async with httpx.AsyncClient() as client:
        # Login as tester
        login = await client.post('http://localhost:8001/api/v1/auth/login', 
            json={'email': 'tester@example.com', 'password': 'password123'})
        
        if login.status_code != 200:
            print(f"Login failed: {login.status_code}")
            print(login.text)
            return
            
        token = login.json()['access_token']
        
        # Get decisions
        resp = await client.get('http://localhost:8001/api/v1/scoping/cycles/13/reports/156/decisions',
            headers={'Authorization': f'Bearer {token}'})
        
        print(f'Status: {resp.status_code}')
        if resp.status_code == 200:
            decisions = resp.json()
            print(f'\nTotal decisions returned: {len(decisions)}')
            scoped = sum(1 for d in decisions if d['final_scoping'])
            print(f'Scoped attributes: {scoped}')
            
            # Show first few decisions
            print("\nFirst 5 decisions:")
            for i, d in enumerate(decisions[:5]):
                print(f"  {i+1}. {d['attribute_name']}: {'Include' if d['final_scoping'] else 'Exclude'}")
        else:
            print(resp.text)

if __name__ == "__main__":
    asyncio.run(test())