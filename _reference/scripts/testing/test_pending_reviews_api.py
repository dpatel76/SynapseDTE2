#!/usr/bin/env python3
"""Test the pending reviews API endpoint"""

import asyncio
import httpx
import json

BASE_URL = "http://localhost:8001"

async def test_pending_reviews():
    async with httpx.AsyncClient() as client:
        # 1. Login as Report Owner
        print("1. Logging in as Report Owner...")
        login_response = await client.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"email": "report.owner@example.com", "password": "password123"}
        )
        
        if login_response.status_code != 200:
            print(f"Login failed: {login_response.status_code}")
            print(login_response.text)
            return
        
        token = login_response.json()["access_token"]
        print(f"✅ Logged in successfully")
        
        # 2. Test pending reviews endpoint
        print("\n2. Testing /scoping/pending-reviews endpoint...")
        headers = {"Authorization": f"Bearer {token}"}
        
        reviews_response = await client.get(
            f"{BASE_URL}/api/v1/scoping/pending-reviews",
            headers=headers
        )
        
        print(f"Response status: {reviews_response.status_code}")
        
        if reviews_response.status_code == 200:
            data = reviews_response.json()
            print(f"✅ Success! Found {len(data)} pending reviews")
            
            for review in data:
                print(f"\n  Review:")
                print(f"    Report: {review.get('report_name')} (ID: {review.get('report_id')})")
                print(f"    Cycle: {review.get('cycle_id')}")
                print(f"    LOB: {review.get('lob')}")
                print(f"    Submitted by: {review.get('submitted_by')}")
                print(f"    Date: {review.get('submitted_date')}")
                print(f"    Attributes: {review.get('attributes_selected')}/{review.get('total_attributes')}")
        else:
            print(f"❌ Error: {reviews_response.text}")
        
        # 3. Check current user info
        print("\n3. Checking current user info...")
        user_response = await client.get(
            f"{BASE_URL}/api/v1/users/me",
            headers=headers
        )
        
        if user_response.status_code == 200:
            user_data = user_response.json()
            print(f"Current user: {user_data.get('username')} ({user_data.get('email')})")
            print(f"Role: {user_data.get('role')}")
            print(f"User ID: {user_data.get('user_id')}")
        
        # 4. Check which reports this user owns
        print("\n4. Checking owned reports...")
        # This would require a separate endpoint, but we can check via debug

if __name__ == "__main__":
    asyncio.run(test_pending_reviews())