#!/usr/bin/env python3
"""Test the complete scoping endpoint"""

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
        
        # Complete scoping phase
        resp = await client.post('http://localhost:8001/api/v1/scoping/cycles/13/reports/156/complete',
            headers={'Authorization': f'Bearer {token}'})
        
        print(f'Status: {resp.status_code}')
        if resp.status_code == 200:
            result = resp.json()
            print(f"Success: {result['message']}")
            print(f"Next phase: {result.get('next_phase')}")
        else:
            print(f"Error: {resp.text}")

if __name__ == "__main__":
    asyncio.run(test())