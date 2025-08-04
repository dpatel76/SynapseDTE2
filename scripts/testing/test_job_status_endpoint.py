#!/usr/bin/env python3
"""Test script to verify the job status endpoint is working correctly."""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_USER = {
    "username": "tester@synapse.com",
    "password": "Test123!"
}

def login():
    """Login and get access token."""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": TEST_USER["username"],  # API expects 'email' field
            "password": TEST_USER["password"]
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Logged in as {data['user']['email']} (Role: {data['user']['role']['name']})")
        return data['access_token']
    else:
        print(f"❌ Login failed: {response.status_code} - {response.text}")
        return None

def test_job_status_endpoint(token, job_id):
    """Test the job status endpoint."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    url = f"{BASE_URL}/background_jobs/{job_id}/status"
    print(f"\n🔍 Testing job status endpoint: {url}")
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Job status retrieved successfully:")
        print(json.dumps(data, indent=2))
        return data
    elif response.status_code == 404:
        print(f"❌ Job not found (404)")
        return None
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")
        return None

def test_llm_generation(token):
    """Trigger LLM generation and get job ID."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Use cycle 1, report 12 which we know exists
    url = f"{BASE_URL}/planning/1/reports/12/generate-attributes-llm-async"
    
    payload = {
        "document_ids": [],  # Will use any uploaded documents
        "generation_type": "full",
        "include_cde_matching": True,
        "include_historical_matching": True,
        "provider": "gemini",  # or "claude"
        "regulatory_context": "Test generation"
    }
    
    print(f"\n🚀 Triggering LLM generation...")
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ LLM generation started successfully:")
        print(f"   Job ID: {data.get('job_id')}")
        print(f"   Message: {data.get('message')}")
        return data.get('job_id')
    else:
        print(f"❌ Failed to start LLM generation: {response.status_code}")
        print(f"   Error: {response.text}")
        return None

def monitor_job(token, job_id, max_polls=30):
    """Monitor job progress until completion."""
    print(f"\n📊 Monitoring job {job_id}...")
    
    for i in range(max_polls):
        status = test_job_status_endpoint(token, job_id)
        
        if not status:
            break
            
        if status['status'] in ['completed', 'failed']:
            print(f"\n🏁 Job finished with status: {status['status']}")
            if status['status'] == 'failed':
                print(f"   Error: {status.get('error', 'Unknown error')}")
            else:
                print(f"   Result: {status.get('result', {})}")
            break
            
        # Show progress
        progress = status.get('progress', {})
        print(f"\r⏳ Poll {i+1}/{max_polls} - Status: {status['status']} - Progress: {progress.get('percentage', 0):.1f}% - {progress.get('message', '')}", end='', flush=True)
        
        time.sleep(2)  # Wait 2 seconds between polls
    else:
        print(f"\n⏱️  Timeout: Job did not complete within {max_polls * 2} seconds")

def main():
    """Main test function."""
    print("🧪 Testing Job Status Endpoint")
    print("=" * 50)
    
    # Login
    token = login()
    if not token:
        return
    
    # Test with a fake job ID first
    print("\n1️⃣  Testing with fake job ID...")
    test_job_status_endpoint(token, "fake-job-id-12345")
    
    # Trigger a real LLM generation job
    print("\n2️⃣  Testing with real LLM generation job...")
    job_id = test_llm_generation(token)
    
    if job_id:
        # Monitor the job
        monitor_job(token, job_id)
    
    print("\n✅ Test complete!")

if __name__ == "__main__":
    main()