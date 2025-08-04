#!/usr/bin/env python3
"""Monitor job status"""
import requests
import time
import json

# Get authentication token
auth_response = requests.post(
    'http://localhost:8000/api/v1/auth/login',
    json={
        'email': 'tester@example.com',
        'password': 'password123'
    }
)

if auth_response.status_code == 200:
    token = auth_response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    
    job_id = "de26d473-794f-4fb6-9a42-ea34aea8af63"
    
    # Monitor job
    while True:
        response = requests.get(
            f'http://localhost:8000/api/v1/jobs/{job_id}/status',
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n📊 Job Status: {data.get('status')}")
            print(f"   Progress: {data.get('progress', 0)}%")
            print(f"   Step: {data.get('current_step', 'N/A')}")
            
            if data.get('status') == 'completed':
                print("\n✅ Job completed!")
                if data.get('result'):
                    print(f"   Result: {json.dumps(data['result'], indent=2)}")
                break
            elif data.get('status') == 'failed':
                print(f"\n❌ Job failed: {data.get('error')}")
                break
        else:
            print(f"❌ Error checking status: {response.text}")
            break
            
        time.sleep(2)