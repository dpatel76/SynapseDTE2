#!/usr/bin/env python3

import asyncio
import aiohttp

async def test_endpoint():
    async with aiohttp.ClientSession() as session:
        # Login
        login_data = {"email": "admin@synapsedt.com", "password": "password123"}
        async with session.post("http://localhost:8000/api/v1/auth/login", json=login_data) as response:
            login_result = await response.json()
            token = login_result.get("access_token")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test the restrictions endpoint
        async with session.get(
            "http://localhost:8000/api/v1/admin/rbac/roles/1/permissions/restrictions",
            headers=headers
        ) as response:
            print(f"Status: {response.status}")
            print(f"Headers: {dict(response.headers)}")
            text = await response.text()
            print(f"Response: {text}")

if __name__ == "__main__":
    asyncio.run(test_endpoint()) 