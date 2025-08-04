#\!/usr/bin/env python3
"""
Generate samples with correct distribution
"""

import requests
import time

# Login as tester
login_response = requests.post(
    'http://localhost:8000/api/v1/auth/login',
    json={'email': 'tester@example.com', 'password': 'password123'}
)
token = login_response.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# Start the phase first
print("1. Starting phase...")
start_response = requests.post(
    'http://localhost:8000/api/v1/sample-selection/cycles/55/reports/156/start',
    headers=headers,
    json={}
)
print(f"   Start response: {start_response.status_code}")

# Generate samples with 30% CLEAN, 50% ANOMALY, 20% BOUNDARY
print("\n2. Generating 20 samples with distribution: 30% CLEAN, 50% ANOMALY, 20% BOUNDARY...")
generate_response = requests.post(
    'http://localhost:8000/api/v1/sample-selection/cycles/55/reports/156/samples/generate-unified',
    headers=headers,
    json={
        "strategy": "intelligent",
        "sample_size": 20,  # Generate 20 samples to see the distribution better
        "use_data_source": True,
        "distribution": {
            "CLEAN": 0.3,      # 30% = 6 samples
            "ANOMALY": 0.5,    # 50% = 10 samples
            "BOUNDARY": 0.2    # 20% = 4 samples
        }
    }
)

if generate_response.status_code == 200:
    result = generate_response.json()
    job_id = result.get('job_id')
    print(f"   Job started: {job_id}")
    
    # Wait for job to complete
    time.sleep(5)
    
    # Check job status
    job_response = requests.get(
        f"http://localhost:8000/api/v1/jobs/{job_id}/status",
        headers=headers
    )
    if job_response.status_code == 200:
        job_data = job_response.json()
        print(f"   Job status: {job_data.get('status')}")

# Check the actual distribution
print("\n3. Checking actual distribution...")
samples_response = requests.get(
    'http://localhost:8000/api/v1/sample-selection/cycles/55/reports/156/samples',
    headers=headers
)

if samples_response.status_code == 200:
    samples = samples_response.json()['samples']
    print(f"\nTotal samples generated: {len(samples)}")
    
    # Count by category
    category_counts = {'CLEAN': 0, 'ANOMALY': 0, 'BOUNDARY': 0}
    for sample in samples:
        category = sample.get('sample_category', 'UNKNOWN')
        if category in category_counts:
            category_counts[category] += 1
    
    # Show distribution
    print("\nExpected vs Actual:")
    print(f"CLEAN:    Expected 6 (30%)  -> Actual {category_counts['CLEAN']} ({category_counts['CLEAN']/len(samples)*100:.1f}%)")
    print(f"ANOMALY:  Expected 10 (50%) -> Actual {category_counts['ANOMALY']} ({category_counts['ANOMALY']/len(samples)*100:.1f}%)")
    print(f"BOUNDARY: Expected 4 (20%)  -> Actual {category_counts['BOUNDARY']} ({category_counts['BOUNDARY']/len(samples)*100:.1f}%)")
    
    # Check for duplicate IDs
    sample_ids = [s['sample_id'] for s in samples]
    unique_ids = set(sample_ids)
    if len(sample_ids) \!= len(unique_ids):
        print(f"\nWARNING: Found duplicate sample IDs\! {len(sample_ids)} total, {len(unique_ids)} unique")
