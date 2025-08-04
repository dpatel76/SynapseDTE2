#!/usr/bin/env python3
"""
Test script to verify scoping LLM integration with background job manager
"""

import asyncio
import requests
import time
import json

# Configuration
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

# Test credentials (update as needed)
USERNAME = "test@example.com"
PASSWORD = "test123"

def login():
    """Login and get access token"""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": USERNAME, "password": PASSWORD}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Login failed: {response.status_code} - {response.text}")
        return None

def test_scoping_llm_integration(token, version_id):
    """Test the scoping LLM recommendation generation"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Generate recommendations
    print("\n1. Starting LLM recommendation generation...")
    response = requests.post(
        f"{BASE_URL}{API_PREFIX}/scoping/versions/{version_id}/generate-recommendations",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"Failed to start generation: {response.status_code} - {response.text}")
        return
    
    result = response.json()
    job_id = result.get("job_id")
    print(f"Job started with ID: {job_id}")
    print(f"Processing {result.get('attributes_count')} attributes")
    print(f"Estimated time: {result.get('estimated_time_minutes')} minutes")
    
    if not job_id:
        print("No job ID returned")
        return
    
    # 2. Monitor job progress
    print("\n2. Monitoring job progress...")
    completed = False
    last_progress = -1
    
    while not completed:
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/background-jobs/{job_id}/status",
            headers=headers
        )
        
        if response.status_code != 200:
            print(f"Failed to get job status: {response.status_code}")
            break
        
        job_status = response.json()
        status = job_status.get("status")
        progress = job_status.get("progress_percentage", 0)
        
        if progress != last_progress:
            print(f"Progress: {progress}% - {job_status.get('current_step')} - {job_status.get('message')}")
            last_progress = progress
        
        if status == "completed":
            completed = True
            print("\n✅ Job completed successfully!")
            print(f"Result: {json.dumps(job_status.get('result'), indent=2)}")
        elif status == "failed":
            completed = True
            print("\n❌ Job failed!")
            print(f"Error: {job_status.get('error')}")
        
        if not completed:
            time.sleep(2)  # Poll every 2 seconds
    
    # 3. Verify attributes have recommendations
    print("\n3. Verifying scoping attributes...")
    response = requests.get(
        f"{BASE_URL}{API_PREFIX}/scoping/versions/{version_id}",
        headers=headers
    )
    
    if response.status_code == 200:
        version_data = response.json()
        print(f"Version status: {version_data.get('version_status')}")
        print(f"Total attributes: {version_data.get('attribute_summary', {}).get('total_attributes', 0)}")

def main():
    """Main test function"""
    print("Testing Scoping LLM Integration with Background Job Manager")
    print("=" * 60)
    
    # Login
    token = login()
    if not token:
        print("Failed to login. Exiting.")
        return
    
    print("✅ Logged in successfully")
    
    # Get version ID from user
    version_id = input("\nEnter the scoping version ID to test: ").strip()
    if not version_id:
        print("No version ID provided. Exiting.")
        return
    
    # Run the test
    test_scoping_llm_integration(token, version_id)
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    main()