#!/usr/bin/env python3
"""Test complete submission and review flow with decisions"""

import asyncio
import httpx
import json
from datetime import datetime

async def test():
    async with httpx.AsyncClient() as client:
        print("=== TEST SUBMISSION AND REVIEW FLOW ===")
        print(f"Time: {datetime.now()}")
        
        # Step 1: Login as Tester
        print("\n1. TESTER: Logging in...")
        login = await client.post('http://localhost:8001/api/v1/auth/login', 
            json={'email': 'jane.doe@example.com', 'password': 'password123'})
        
        if login.status_code != 200:
            print(f"Login failed: {login.status_code}")
            print(login.text)
            return
            
        tester_token = login.json()['access_token']
        tester_headers = {'Authorization': f'Bearer {tester_token}'}
        
        # Step 2: Check current samples
        print("\n2. TESTER: Checking current samples...")
        samples_resp = await client.get(
            'http://localhost:8001/api/v1/sample-selection/cycles/13/reports/156/samples',
            headers=tester_headers
        )
        
        if samples_resp.status_code == 200:
            samples = samples_resp.json()['samples']
            print(f"Total samples: {len(samples)}")
            
            # Find samples to include
            samples_to_include = []
            for sample in samples:
                if sample.get('tester_decision') == 'include':
                    samples_to_include.append(sample['sample_id'])
            
            print(f"Samples already marked as include: {len(samples_to_include)}")
            print(f"Sample IDs: {samples_to_include}")
            
            if len(samples_to_include) < 2:
                print("Not enough samples marked as include, marking some...")
                # Mark first 2 samples as include
                for i, sample in enumerate(samples[:2]):
                    if sample['sample_id'] not in samples_to_include:
                        decision_resp = await client.post(
                            f"http://localhost:8001/api/v1/sample-selection/cycles/13/reports/156/samples/{sample['sample_id']}/decision",
                            headers=tester_headers,
                            json={"decision": "include"}
                        )
                        if decision_resp.status_code == 200:
                            samples_to_include.append(sample['sample_id'])
                            print(f"Marked {sample['sample_id']} as include")
                        
            # Step 3: Submit samples
            print(f"\n3. TESTER: Submitting {len(samples_to_include)} samples for approval...")
            submit_resp = await client.post(
                'http://localhost:8001/api/v1/sample-selection/cycles/13/reports/156/samples/submit',
                headers=tester_headers,
                json={
                    "sample_ids": samples_to_include,
                    "notes": "Test submission for review flow"
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
        
        # Step 4: Login as Report Owner
        print("\n4. REPORT OWNER: Logging in...")
        ro_login = await client.post('http://localhost:8001/api/v1/auth/login', 
            json={'email': 'report.owner@example.com', 'password': 'password123'})
        
        ro_token = ro_login.json()['access_token']
        ro_headers = {'Authorization': f'Bearer {ro_token}'}
        
        # Step 5: Get submission details
        print("\n5. REPORT OWNER: Getting submission details...")
        sub_details = await client.get(
            f'http://localhost:8001/api/v1/sample-selection/cycles/13/reports/156/submissions/{submission_id}',
            headers=ro_headers
        )
        
        if sub_details.status_code == 200:
            sub_data = sub_details.json()
            print(f"Submission loaded successfully")
            print(f"Submission metadata: {json.dumps(sub_data['submission'], indent=2)}")
            print(f"Total samples in snapshot: {len(sub_data['samples'])}")
            
            if sub_data['samples']:
                print("\n\nSamples in submission:")
                for i, sample in enumerate(sub_data['samples']):
                    print(f"\n  Sample {i+1}:")
                    print(f"    ID: {sample.get('sample_id')}")
                    print(f"    Tester Decision: {sample.get('tester_decision')}")
                    print(f"    Report Owner Decision: {sample.get('report_owner_decision')}")
                    print(f"    Report Owner Feedback: {sample.get('report_owner_feedback')}")
        
        # Step 6: Review with individual decisions
        print("\n6. REPORT OWNER: Reviewing submission with individual decisions...")
        
        # Create individual decisions (approve first, reject second if exists)
        individual_decisions = {}
        individual_feedback = {}
        
        if len(samples_to_include) >= 2:
            individual_decisions[samples_to_include[0]] = "approved"
            individual_feedback[samples_to_include[0]] = "This sample looks good"
            
            individual_decisions[samples_to_include[1]] = "rejected"
            individual_feedback[samples_to_include[1]] = "This sample needs revision"
        
        review_resp = await client.post(
            f'http://localhost:8001/api/v1/sample-selection/cycles/13/reports/156/submissions/{submission_id}/review',
            headers=ro_headers,
            json={
                "decision": "revision_required",
                "feedback": "Overall: Some samples need revision",
                "individual_decisions": individual_decisions,
                "individual_feedback": individual_feedback
            }
        )
        
        if review_resp.status_code == 200:
            review_data = review_resp.json()
            print(f"Review submitted successfully!")
            print(f"Message: {review_data['message']}")
        else:
            print(f"Error reviewing: {review_resp.status_code}")
            print(review_resp.text)
        
        # Step 7: Check feedback as Tester
        print("\n7. TESTER: Checking feedback...")
        feedback_resp = await client.get(
            'http://localhost:8001/api/v1/sample-selection/cycles/13/reports/156/samples/feedback',
            headers=tester_headers
        )
        
        if feedback_resp.status_code == 200:
            feedback_data = feedback_resp.json()
            print(f"Feedback response: {json.dumps(feedback_data, indent=2)}")

if __name__ == "__main__":
    asyncio.run(test())