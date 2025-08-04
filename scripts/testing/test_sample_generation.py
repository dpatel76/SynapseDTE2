#!/usr/bin/env python3
"""Test sample generation endpoint"""

import asyncio
import httpx
import json

async def test():
    async with httpx.AsyncClient() as client:
        # Login as tester
        login = await client.post('http://localhost:8001/api/v1/auth/login', 
            json={'email': 'tester@synapse.com', 'password': 'TestUser123!'})
        
        if login.status_code != 200:
            print(f"Login failed: {login.status_code}")
            return
            
        token = login.json()['access_token']
        
        # Generate samples
        payload = {
            "sample_size": 5,
            "sample_type": "Population Sample",
            "risk_focus_areas": ["Regulatory compliance", "Data quality"],
            "include_edge_cases": True
        }
        
        resp = await client.post(
            'http://localhost:8001/api/v1/sample-selection/cycles/13/reports/156/samples/generate',
            json=payload,
            headers={'Authorization': f'Bearer {token}'},
            timeout=60.0  # 60 second timeout for LLM calls
        )
        
        print(f'Status: {resp.status_code}')
        if resp.status_code == 200:
            result = resp.json()
            print(f"Success! Generated {result.get('samples_generated', 0)} samples")
            print(f"Confidence Score: {result.get('confidence_score', 0)}")
            print(f"Sample Set ID: {result.get('sample_set_id', 'N/A')}")
        else:
            print(f"Error: {resp.text}")

if __name__ == "__main__":
    asyncio.run(test())