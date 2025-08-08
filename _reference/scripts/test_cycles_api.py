#!/usr/bin/env python
"""Test the cycles API endpoint"""

import asyncio
import httpx
from app.core.security import create_access_token
from datetime import timedelta

async def test_cycles_api():
    # Create a test token
    token = create_access_token(
        subject="test.manager@example.com",
        user_id=2,
        role="Test Manager",
        expires_delta=timedelta(minutes=30)
    )
    
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient() as client:
        # Test the API endpoint
        response = await client.get(
            "http://localhost:8000/api/v1/cycles/?skip=0&limit=10",
            headers=headers
        )
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Total cycles: {data.get('total', 0)}")
            print(f"Cycles returned: {len(data.get('cycles', []))}")
            print(f"Skip: {data.get('skip', 0)}")
            print(f"Limit: {data.get('limit', 0)}")
            
            if data.get('cycles'):
                print("\nFirst few cycles:")
                for i, cycle in enumerate(data['cycles'][:3]):
                    print(f"  {i+1}. {cycle['cycle_name']} (ID: {cycle['cycle_id']})")
        else:
            print(f"Error: {response.text}")

if __name__ == "__main__":
    asyncio.run(test_cycles_api())