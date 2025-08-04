#!/usr/bin/env python3
"""Detailed monitoring of PDE mapping job with retry logic verification"""

import asyncio
import httpx
import json
from datetime import datetime
import time

BASE_URL = "http://localhost:8000/api/v1"

async def get_token():
    """Login and get token"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/auth/login",
            json={
                "email": "tester@example.com",
                "password": "password123"
            }
        )
        response.raise_for_status()
        return response.json()["access_token"]

async def monitor_job_realtime(job_id: str, token: str):
    """Monitor a specific job in real-time"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"\n🔍 Monitoring job {job_id}")
    print("=" * 80)
    
    last_status = None
    last_progress = -1
    start_time = time.time()
    
    while True:
        try:
            async with httpx.AsyncClient() as client:
                # Get job status
                response = await client.get(
                    f"{BASE_URL}/jobs/{job_id}/status",
                    headers=headers
                )
                
                if response.status_code == 404:
                    print("\n❌ Job no longer exists")
                    break
                    
                response.raise_for_status()
                status_data = response.json()
                
                current_status = status_data.get('status', 'unknown')
                current_progress = status_data.get('progress', 0)
                
                # Print updates only when something changes
                if current_status != last_status or current_progress != last_progress:
                    elapsed = int(time.time() - start_time)
                    print(f"\n[{elapsed}s] Status: {current_status} | Progress: {current_progress}%")
                    print(f"Message: {status_data.get('message', 'N/A')}")
                    
                    if current_status != last_status:
                        print(f"🔄 Status changed: {last_status} → {current_status}")
                    
                    # Show additional details
                    if status_data.get('current_batch'):
                        print(f"Current batch: {status_data['current_batch']}")
                    
                    if status_data.get('error'):
                        print(f"❌ Error: {status_data['error']}")
                    
                    if status_data.get('mappings_created') is not None:
                        print(f"✅ Mappings created: {status_data['mappings_created']}")
                    
                    # Check logs for retry messages
                    if status_data.get('logs'):
                        for log in status_data['logs']:
                            if 'overloaded' in log.lower() or 'retry' in log.lower():
                                print(f"🔁 Retry detected: {log}")
                    
                    last_status = current_status
                    last_progress = current_progress
                
                # Exit conditions
                if current_status in ['completed', 'failed']:
                    print(f"\n{'='*80}")
                    print(f"Job {current_status.upper()}")
                    print(f"Total time: {int(time.time() - start_time)} seconds")
                    
                    # Get final results
                    if current_status == 'completed':
                        print(f"\n✅ Success Summary:")
                        print(f"  - Total attributes: {status_data.get('total_attributes', 0)}")
                        print(f"  - Processed: {status_data.get('processed_attributes', 0)}")
                        print(f"  - Mappings created: {status_data.get('mappings_created', 0)}")
                    else:
                        print(f"\n❌ Failure Summary:")
                        print(f"  - Error: {status_data.get('error', 'Unknown error')}")
                        print(f"  - Last message: {status_data.get('message', 'N/A')}")
                    
                    break
                
                # Wait before next check
                await asyncio.sleep(2)
                
        except Exception as e:
            print(f"\n⚠️ Error monitoring job: {e}")
            await asyncio.sleep(5)

async def check_llm_health(token: str):
    """Check LLM service health"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n🏥 Checking LLM Service Health...")
    print("-" * 40)
    
    try:
        async with httpx.AsyncClient() as client:
            # Try to check if there's a health endpoint
            # This is a test call to see if LLM is responding
            response = await client.get(
                f"{BASE_URL}/health",
                headers=headers
            )
            
            if response.status_code == 200:
                print("✅ API is healthy")
            else:
                print(f"⚠️ API health check returned: {response.status_code}")
                
    except Exception as e:
        print(f"❌ Error checking health: {e}")

async def main():
    """Main monitoring function"""
    try:
        print("🔐 Logging in...")
        token = await get_token()
        
        # Check LLM health first
        await check_llm_health(token)
        
        # Monitor the specific job
        job_id = "9fad9db4-0ead-4b77-859a-275e4b97f5f8"  # Latest job
        await monitor_job_realtime(job_id, token)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())