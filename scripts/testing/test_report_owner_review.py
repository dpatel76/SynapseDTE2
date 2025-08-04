#!/usr/bin/env python3
"""Test Report Owner sample review functionality"""

import asyncio
import httpx
import json

async def test():
    async with httpx.AsyncClient() as client:
        # Login as report owner
        print("1. Logging in as Report Owner...")
        login = await client.post('http://localhost:8001/api/v1/auth/login', 
            json={'email': 'report.owner@example.com', 'password': 'password123'})
        
        if login.status_code != 200:
            print(f"Login failed: {login.status_code}")
            return
            
        token = login.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        
        # Get pending reviews
        print("\n2. Getting pending reviews...")
        pending = await client.get(
            'http://localhost:8001/api/v1/sample-selection/pending-reviews',
            headers=headers
        )
        
        print(f"Status: {pending.status_code}")
        if pending.status_code == 200:
            reviews = pending.json()
            print(f"Pending Reviews: {len(reviews)}")
            
            if reviews:
                # Get the first pending review
                review = reviews[0]
                print(f"\nReviewing submission for Report: {review['report_name']}")
                print(f"Submission ID: {review['submission_id']}")
                print(f"Version: {review['version_number']}")
                print(f"Samples: {review['sample_count']}")
                
                # First get analytics to find submission_id
                print("\n3. Getting analytics to find submission ID...")
                analytics_resp = await client.get(
                    f"http://localhost:8001/api/v1/sample-selection/cycles/{review['cycle_id']}/reports/{review['report_id']}/samples/analytics",
                    headers=headers
                )
                
                if analytics_resp.status_code == 200:
                    analytics = analytics_resp.json()
                    if analytics.get('latest_submission'):
                        submission_id = analytics['latest_submission']['submission_id']
                        print(f"Found submission ID: {submission_id}")
                        
                        # Get submission details
                        print("\n4. Getting submission details...")
                        submission_resp = await client.get(
                            f"http://localhost:8001/api/v1/sample-selection/cycles/{review['cycle_id']}/reports/{review['report_id']}/submissions/{submission_id}",
                            headers=headers
                        )
                        
                        if submission_resp.status_code == 200:
                            submission_data = submission_resp.json()
                            print(f"Submission loaded successfully")
                            print(f"Submission data: {submission_data['submission']}")
                            print(f"Total samples in snapshot: {len(submission_data['samples'])}")
                            
                            # If samples are empty, it means old submission format - test anyway
                            if not submission_data['samples']:
                                print("Note: This is an older submission without sample snapshot")
                                print(f"Sample count from metadata: {submission_data['submission'].get('sample_count', 0)}")
                        else:
                            print(f"Error loading submission: {submission_resp.status_code}")
                            print(submission_resp.text)
        else:
            print(f"Error: {pending.text}")

if __name__ == "__main__":
    asyncio.run(test())