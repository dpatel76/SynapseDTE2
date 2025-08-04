#!/usr/bin/env python3
"""Test complete sample workflow: generate, submit, and review"""

import asyncio
import httpx
import json
from datetime import datetime

async def test():
    async with httpx.AsyncClient() as client:
        print("=== COMPLETE SAMPLE WORKFLOW TEST ===")
        print(f"Time: {datetime.now()}")
        
        # Step 1: Login as Tester
        print("\n1. TESTER: Logging in...")
        login = await client.post('http://localhost:8001/api/v1/auth/login', 
            json={'email': 'jane.doe@example.com', 'password': 'password123'})
        
        if login.status_code != 200:
            print(f"Login failed: {login.status_code}")
            return
            
        tester_token = login.json()['access_token']
        tester_headers = {'Authorization': f'Bearer {tester_token}'}
        
        # Step 2: Generate new samples
        print("\n2. TESTER: Generating 3 new samples...")
        gen_resp = await client.post(
            'http://localhost:8001/api/v1/sample-selection/cycles/13/reports/156/samples/generate',
            headers=tester_headers,
            json={
                "sample_size": 3,
                "sample_type": "Population Sample"
            }
        )
        
        if gen_resp.status_code == 200:
            gen_data = gen_resp.json()
            print(f"Generated {gen_data['samples_generated']} samples")
            print(f"Sample IDs: {gen_data.get('sample_ids', [])}")
        else:
            print(f"Error generating samples: {gen_resp.status_code}")
            print(gen_resp.text)
            return
        
        # Step 3: Get current samples
        print("\n3. TESTER: Getting current samples...")
        samples_resp = await client.get(
            'http://localhost:8001/api/v1/sample-selection/cycles/13/reports/156/samples',
            headers=tester_headers
        )
        
        if samples_resp.status_code == 200:
            samples = samples_resp.json()['samples']
            print(f"Total samples: {len(samples)}")
            
            # Mark some samples for inclusion
            include_count = 0
            for sample in samples[-3:]:  # Last 3 samples
                if not sample.get('tester_decision'):
                    decision_resp = await client.post(
                        f"http://localhost:8001/api/v1/sample-selection/cycles/13/reports/156/samples/{sample['sample_id']}/decision",
                        headers=tester_headers,
                        json={"decision": "include"}
                    )
                    if decision_resp.status_code == 200:
                        include_count += 1
                        print(f"Marked {sample['sample_id']} as include")
            
            print(f"Marked {include_count} samples for inclusion")
        
        # Step 4: Submit samples for approval
        print("\n4. TESTER: Submitting samples for approval...")
        included_samples = [s['sample_id'] for s in samples if s.get('tester_decision') == 'include']
        
        submit_resp = await client.post(
            'http://localhost:8001/api/v1/sample-selection/cycles/13/reports/156/samples/submit',
            headers=tester_headers,
            json={
                "sample_ids": included_samples,
                "notes": "New submission for testing the complete workflow"
            }
        )
        
        if submit_resp.status_code == 200:
            submit_data = submit_resp.json()
            print(f"Submission successful!")
            print(f"Submission ID: {submit_data['submission_id']}")
            print(f"Version: {submit_data['version_number']}")
            submission_id = submit_data['submission_id']
        else:
            print(f"Error submitting: {submit_resp.status_code}")
            print(submit_resp.text)
            return
        
        # Step 5: Login as Report Owner
        print("\n5. REPORT OWNER: Logging in...")
        ro_login = await client.post('http://localhost:8001/api/v1/auth/login', 
            json={'email': 'report.owner@example.com', 'password': 'password123'})
        
        ro_token = ro_login.json()['access_token']
        ro_headers = {'Authorization': f'Bearer {ro_token}'}
        
        # Step 6: Get submission details
        print("\n6. REPORT OWNER: Getting submission details...")
        sub_details = await client.get(
            f'http://localhost:8001/api/v1/sample-selection/cycles/13/reports/156/submissions/{submission_id}',
            headers=ro_headers
        )
        
        if sub_details.status_code == 200:
            sub_data = sub_details.json()
            print(f"Submission loaded successfully")
            print(f"Total samples in snapshot: {len(sub_data['samples'])}")
            print(f"Included samples: {sub_data['submission']['included_samples']}")
            
            if sub_data['samples']:
                print("\nSample IDs in submission:")
                for sample in sub_data['samples']:
                    if sample.get('tester_decision') == 'include':
                        print(f"  - {sample['sample_id']}: {sample['primary_key_value']}")
        
        # Step 7: Approve the submission
        print("\n7. REPORT OWNER: Approving submission...")
        review_resp = await client.post(
            f'http://localhost:8001/api/v1/sample-selection/cycles/13/reports/156/submissions/{submission_id}/review',
            headers=ro_headers,
            json={
                "decision": "approved",
                "feedback": "Samples look good. Approved for testing."
            }
        )
        
        if review_resp.status_code == 200:
            review_data = review_resp.json()
            print(f"Review submitted successfully!")
            print(f"Message: {review_data['message']}")
        else:
            print(f"Error reviewing: {review_resp.status_code}")
            print(review_resp.text)
        
        # Step 8: Check final status
        print("\n8. Checking final phase status...")
        analytics = await client.get(
            'http://localhost:8001/api/v1/sample-selection/cycles/13/reports/156/samples/analytics',
            headers=tester_headers
        )
        
        if analytics.status_code == 200:
            analytics_data = analytics.json()
            print(f"Phase Status: {analytics_data['phase_status']}")
            print(f"Can Complete Phase: {analytics_data['can_complete_phase']}")
            print(f"Approved Samples: {analytics_data['approved_samples']}")

if __name__ == "__main__":
    asyncio.run(test())