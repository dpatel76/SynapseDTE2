#!/usr/bin/env python3
"""
Quick test script for clean architecture endpoints
"""

import httpx
import asyncio
import json
from datetime import datetime

BASE_URL = "http://localhost:8001"

async def test_clean_endpoints():
    """Test clean architecture endpoints"""
    
    print("Testing Clean Architecture Endpoints")
    print("=" * 50)
    
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # Test health endpoint
        print("\n1. Testing health endpoint...")
        try:
            response = await client.get("/api/v1/clean/health")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
        except Exception as e:
            print(f"Error: {e}")
        
        # Test auth endpoint
        print("\n2. Testing auth endpoint...")
        try:
            response = await client.post("/api/v1/clean/auth/login", json={
                "email": "tester@synapsefinancial.com",
                "password": "Test123!"
            })
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Login successful for: {data.get('user', {}).get('email')}")
                token = data.get('access_token')
                
                # Test authenticated endpoints
                headers = {"Authorization": f"Bearer {token}"}
                
                # Test metrics endpoint
                print("\n3. Testing metrics endpoint...")
                response = await client.get("/api/v1/clean/metrics/dashboard/current-user", headers=headers)
                print(f"Status: {response.status_code}")
                if response.status_code == 200:
                    print("Metrics retrieved successfully")
                
                # Test dashboards endpoint
                print("\n4. Testing dashboards endpoint...")
                response = await client.get("/api/v1/clean/dashboards/executive", headers=headers)
                print(f"Status: {response.status_code}")
                
            else:
                print(f"Login failed: {response.text}")
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_clean_endpoints())