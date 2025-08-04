#!/usr/bin/env python
"""Test the cycles API endpoint directly"""

import httpx
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def test_api():
    # First, let's simulate a login to get a token
    async with httpx.AsyncClient() as client:
        # Login as test.manager@example.com
        login_response = await client.post(
            "http://localhost:8000/api/v1/auth/login",
            json={
                "email": "test.manager@example.com",
                "password": "password123"
            }
        )
        
        if login_response.status_code != 200:
            print(f"Login failed: {login_response.status_code}")
            print(login_response.text)
            return
            
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        print("Login successful!")
        
        # Test the cycles endpoint
        cycles_response = await client.get(
            "http://localhost:8000/api/v1/cycles/?skip=0&limit=10",
            headers=headers
        )
        
        print(f"\nCycles API Response:")
        print(f"Status: {cycles_response.status_code}")
        
        if cycles_response.status_code == 200:
            data = cycles_response.json()
            print(f"Total: {data.get('total', 0)}")
            print(f"Skip: {data.get('skip', 0)}")
            print(f"Limit: {data.get('limit', 0)}")
            print(f"Cycles returned: {len(data.get('cycles', []))}")
            
            if data.get('cycles'):
                print("\nCycles:")
                for i, cycle in enumerate(data['cycles'][:5]):
                    print(f"  {i+1}. {cycle['cycle_name']} (ID: {cycle['cycle_id']}, Status: {cycle['status']})")
        else:
            print(f"Error: {cycles_response.text}")

if __name__ == "__main__":
    asyncio.run(test_api())