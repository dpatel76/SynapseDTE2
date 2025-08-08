#!/usr/bin/env python3
"""Complete the pending review to show Report Owner decisions"""

import asyncio
import httpx
import json

async def test():
    async with httpx.AsyncClient() as client:
        print("=== COMPLETING PENDING REVIEW ===")
        
        # Step 1: Login as Report Owner
        print("\n1. REPORT OWNER: Logging in...")
        login = await client.post('http://localhost:8001/api/v1/auth/login', 
            json={'email': 'report.owner@example.com', 'password': 'password123'})
        
        if login.status_code != 200:
            print(f"Login failed: {login.status_code}")
            return
            
        token = login.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        
        # Step 2: Get pending reviews
        print("\n2. Getting pending reviews...")
        pending = await client.get(
            'http://localhost:8001/api/v1/sample-selection/pending-reviews',
            headers=headers
        )
        
        if pending.status_code == 200:
            reviews = pending.json()
            print(f"Found {len(reviews)} pending reviews")
            
            if reviews:
                review = reviews[0]
                print(f"\nReviewing: {review['report_name']}")
                print(f"Version: {review['version_number']}")
                
                # Get submission ID from analytics
                analytics = await client.get(
                    f"http://localhost:8001/api/v1/sample-selection/cycles/{review['cycle_id']}/reports/{review['report_id']}/samples/analytics",
                    headers=headers
                )
                
                if analytics.status_code == 200 and analytics.json().get('latest_submission'):
                    submission_id = analytics.json()['latest_submission']['submission_id']
                    print(f"Submission ID: {submission_id}")
                    
                    # Step 3: Get submission details
                    print("\n3. Getting submission details...")
                    sub_resp = await client.get(
                        f"http://localhost:8001/api/v1/sample-selection/cycles/{review['cycle_id']}/reports/{review['report_id']}/submissions/{submission_id}",
                        headers=headers
                    )
                    
                    if sub_resp.status_code == 200:
                        sub_data = sub_resp.json()
                        included_samples = [s for s in sub_data['samples'] if s.get('tester_decision') == 'include']
                        print(f"Found {len(included_samples)} samples to review")
                        
                        # Create individual decisions
                        individual_decisions = {}
                        individual_feedback = {}
                        
                        for i, sample in enumerate(included_samples):
                            if i == 0:
                                individual_decisions[sample['sample_id']] = "approved"
                                individual_feedback[sample['sample_id']] = "This sample looks good"
                            else:
                                individual_decisions[sample['sample_id']] = "revision_required"
                                individual_feedback[sample['sample_id']] = "Please provide more details for this sample"
                        
                        # Step 4: Submit review
                        print("\n4. Submitting review with individual decisions...")
                        review_resp = await client.post(
                            f"http://localhost:8001/api/v1/sample-selection/cycles/{review['cycle_id']}/reports/{review['report_id']}/submissions/{submission_id}/review",
                            headers=headers,
                            json={
                                "decision": "revision_required",
                                "feedback": "Some samples need additional work. Please see individual feedback.",
                                "individual_decisions": individual_decisions,
                                "individual_feedback": individual_feedback
                            }
                        )
                        
                        if review_resp.status_code == 200:
                            print("Review submitted successfully!")
                            
                            # Step 5: Check as Tester
                            print("\n5. TESTER: Checking updated samples...")
                            tester_login = await client.post('http://localhost:8001/api/v1/auth/login', 
                                json={'email': 'jane.doe@example.com', 'password': 'password123'})
                            tester_token = tester_login.json()['access_token']
                            tester_headers = {'Authorization': f'Bearer {tester_token}'}
                            
                            samples_resp = await client.get(
                                f"http://localhost:8001/api/v1/sample-selection/cycles/{review['cycle_id']}/reports/{review['report_id']}/samples?include_feedback=true",
                                headers=tester_headers
                            )
                            
                            if samples_resp.status_code == 200:
                                samples = samples_resp.json()['samples']
                                print(f"\nTotal samples: {len(samples)}")
                                
                                # Show samples with Report Owner decisions
                                for sample in samples:
                                    if sample.get('report_owner_decision'):
                                        print(f"\nSample: {sample['sample_id']}")
                                        print(f"  Version: {sample.get('version_number', 'N/A')}")
                                        print(f"  Tester Decision: {sample.get('tester_decision', 'None')}")
                                        print(f"  Report Owner Decision: {sample.get('report_owner_decision')}")
                                        print(f"  Report Owner Feedback: {sample.get('report_owner_feedback', 'None')}")
                                        print(f"  Version Reviewed: {sample.get('version_reviewed', 'N/A')}")
                        else:
                            print(f"Review failed: {review_resp.status_code}")
                            print(review_resp.text)
                else:
                    print("No pending reviews found")

if __name__ == "__main__":
    asyncio.run(test())