#!/usr/bin/env python3
"""Generate samples directly to test PK inclusion"""
import asyncio
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
    
    # Generate samples using intelligent strategy
    print("🚀 Generating samples with intelligent strategy...")
    response = requests.post(
        'http://localhost:8000/api/v1/sample-selection/cycles/55/reports/156/samples/generate-unified',
        headers=headers,
        json={
            'strategy': 'intelligent',
            'sample_size': 10,
            'use_data_source': True,
            'distribution': {
                'clean': 0.3,
                'anomaly': 0.5,
                'boundary': 0.2
            },
            'include_file_samples': False
        }
    )
    
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        job_id = data.get('job_id')
        print(f"✅ Job created: {job_id}")
        
        # Monitor job
        print("\n📊 Monitoring job...")
        while True:
            status_response = requests.get(
                f'http://localhost:8000/api/v1/jobs/{job_id}/status',
                headers=headers
            )
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                print(f"  Status: {status_data.get('status')} - {status_data.get('current_step', '')} ({status_data.get('progress', 0)}%)")
                
                if status_data.get('status') == 'completed':
                    print("\n✅ Job completed!")
                    break
                elif status_data.get('status') == 'failed':
                    print(f"\n❌ Job failed: {status_data.get('error')}")
                    break
            else:
                print(f"❌ Error checking status: {status_response.text}")
                break
                
            time.sleep(2)
        
        # Check samples
        print("\n🔍 Checking generated samples...")
        samples_response = requests.get(
            'http://localhost:8000/api/v1/sample-selection/cycles/55/reports/156/samples',
            headers=headers
        )
        
        if samples_response.status_code == 200:
            samples_data = samples_response.json()
            samples = samples_data.get('samples', [])
            print(f"\n📦 Total samples: {len(samples)}")
            
            if samples:
                print("\n🔍 First sample:")
                first_sample = samples[0]
                print(f"  ID: {first_sample.get('sample_id')}")
                print(f"  Category: {first_sample.get('sample_category')}")
                print(f"  Primary Key Value: {first_sample.get('primary_key_value')}")
                print(f"  Sample Data:")
                for k, v in first_sample.get('sample_data', {}).items():
                    print(f"    {k}: {v}")
        else:
            print(f"❌ Error getting samples: {samples_response.text}")
    else:
        print(f"❌ Error: {response.text}")
else:
    print(f"❌ Authentication failed: {auth_response.text}")