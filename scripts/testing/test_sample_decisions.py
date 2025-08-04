#!/usr/bin/env python3
"""Test to check sample decisions"""

import asyncio
import httpx
import json

async def test():
    async with httpx.AsyncClient() as client:
        # Login as tester
        login = await client.post('http://localhost:8001/api/v1/auth/login', 
            json={'email': 'jane.doe@example.com', 'password': 'password123'})
        token = login.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        
        # Get samples with feedback
        print("Getting samples with feedback...")
        resp = await client.get(
            'http://localhost:8001/api/v1/sample-selection/cycles/13/reports/156/samples?include_feedback=true',
            headers=headers
        )
        
        if resp.status_code == 200:
            samples = resp.json()['samples']
            print(f"\nTotal samples: {len(samples)}")
            
            # Show samples with decisions
            for sample in samples:
                if sample.get('tester_decision') or sample.get('report_owner_decision'):
                    print(f"\nSample: {sample['sample_id']}")
                    print(f"  Version: {sample.get('version_number', 'N/A')}")
                    print(f"  Tester Decision: {sample.get('tester_decision', 'None')}")
                    print(f"  Report Owner Decision: {sample.get('report_owner_decision', 'None')}")
                    print(f"  Report Owner Feedback: {sample.get('report_owner_feedback', 'None')}")
                    print(f"  Version Reviewed: {sample.get('version_reviewed', 'N/A')}")
                    print(f"  Reviewed By: {sample.get('report_owner_reviewed_by', 'N/A')}")

if __name__ == "__main__":
    asyncio.run(test())