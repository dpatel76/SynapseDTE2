#!/usr/bin/env python3
"""
Simple test script to verify backend login functionality
"""
import asyncio
import httpx
import json
from typing import Dict, Any

BASE_URL = "http://127.0.0.1:8000"

async def test_login(email: str, password: str) -> Dict[str, Any]:
    """Test login endpoint with provided credentials"""
    async with httpx.AsyncClient() as client:
        try:
            # Test login endpoint
            login_data = {
                "email": email,  # Try with email field
                "password": password
            }
            
            print(f"Testing login with: {email}")
            print(f"Sending request to: {BASE_URL}/api/v1/auth/login")
            
            response = await client.post(
                f"{BASE_URL}/api/v1/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Login successful!")
                print(f"Access token: {result.get('access_token', 'N/A')[:50]}...")
                print(f"Token type: {result.get('token_type', 'N/A')}")
                return result
            else:
                print(f"❌ Login failed with status {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"Error details: {json.dumps(error_detail, indent=2)}")
                except:
                    print(f"Error response: {response.text}")
                return {"error": response.text, "status_code": response.status_code}
                
        except httpx.ConnectError as e:
            print(f"❌ Connection error: {e}")
            print("Make sure the backend server is running on localhost:8000")
            return {"error": "Connection failed", "details": str(e)}
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return {"error": "Unexpected error", "details": str(e)}

async def test_protected_endpoint(token: str) -> Dict[str, Any]:
    """Test a protected endpoint using the access token"""
    async with httpx.AsyncClient() as client:
        try:
            headers = {"Authorization": f"Bearer {token}"}
            print(f"\nTesting protected endpoint with token...")
            
            response = await client.get(
                f"{BASE_URL}/api/v1/auth/me",
                headers=headers
            )
            
            print(f"Protected endpoint status: {response.status_code}")
            
            if response.status_code == 200:
                user_info = response.json()
                print("✅ Protected endpoint access successful!")
                print(f"User info: {json.dumps(user_info, indent=2)}")
                return user_info
            else:
                print(f"❌ Protected endpoint failed with status {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"Error details: {json.dumps(error_detail, indent=2)}")
                except:
                    print(f"Error response: {response.text}")
                return {"error": response.text, "status_code": response.status_code}
                
        except Exception as e:
            print(f"❌ Error testing protected endpoint: {e}")
            return {"error": "Protected endpoint test failed", "details": str(e)}

async def main():
    """Main test function"""
    print("🔐 Testing Backend Login Functionality")
    print("=" * 50)
    
    # Test credentials
    email = "tester@example.com"
    password = "password123"
    
    # Test login
    login_result = await test_login(email, password)
    
    # If login successful, test protected endpoint
    if "access_token" in login_result:
        await test_protected_endpoint(login_result["access_token"])
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    asyncio.run(main())