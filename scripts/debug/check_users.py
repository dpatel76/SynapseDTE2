#!/usr/bin/env python3
"""
Check what users exist in the database
"""

import requests
import json

def check_users():
    """Check what users exist and test different login credentials"""
    print("=== CHECKING DATABASE USERS ===")
    
    base_url = "http://localhost:8000/api/v1"
    
    # Test different CDO users from the various scripts
    test_cdo_users = [
        ("cdo@example.com", "CDO123!"),
        ("lisa.wilson@synapse.com", "CDO123!"),
        ("david.brown@synapse.com", "CDO123!"),
        ("diana.cdo@synapsedt.com", "password123"),
        ("cdo@synapse.com", "TestUser123!"),
        ("jack.jones@gbm.com", "password"),  # From previous conversation
    ]
    
    print("\nTesting CDO user logins...")
    for email, password in test_cdo_users:
        print(f"\n📧 Testing: {email} / {password}")
        
        login_data = {
            "email": email,
            "password": password
        }
        
        try:
            response = requests.post(f"{base_url}/auth/login", json=login_data)
            if response.status_code == 200:
                result = response.json()
                user = result.get("user")
                print(f"   ✅ SUCCESS! Role: {user.get('role')}, LOB: {user.get('lob_id')}")
                return email, password, result.get("access_token")
            else:
                print(f"   ❌ Failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # If no CDO users work, try other users to verify server is working
    print("\nTesting other user types...")
    other_users = [
        ("admin@example.com", "AdminUser123!"),
        ("tester@example.com", "Tester123!"),
        ("admin@synapsedt.com", "admin123"),
    ]
    
    for email, password in other_users:
        print(f"\n📧 Testing: {email} / {password}")
        
        login_data = {
            "email": email,
            "password": password
        }
        
        try:
            response = requests.post(f"{base_url}/auth/login", json=login_data)
            if response.status_code == 200:
                result = response.json()
                user = result.get("user")
                print(f"   ✅ SUCCESS! Role: {user.get('role')}, LOB: {user.get('lob_id')}")
            else:
                print(f"   ❌ Failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    return None, None, None

if __name__ == "__main__":
    check_users() 