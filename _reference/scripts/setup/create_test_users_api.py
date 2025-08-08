#!/usr/bin/env python3
"""
Script to create test users for all 6 roles via API calls
"""

import requests
import json

def create_test_users_via_api():
    """Create test users using API endpoints"""
    try:
        # Get admin token
        print('🔐 Authenticating as admin...')
        auth_response = requests.post('http://localhost:8000/api/v1/auth/login', 
                                    json={'email': 'admin@example.com', 'password': 'AdminUser123!'})
        
        if auth_response.status_code != 200:
            print(f'❌ Authentication failed: {auth_response.status_code}')
            return
            
        token = auth_response.json()['access_token']
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        
        print('✅ Creating test users via API...')
        
        test_users = [
            {
                'first_name': 'Test', 'last_name': 'Manager', 'email': 'testmgr@synapse.com', 
                'role': 'Test Executive', 'lob_id': 1, 'phone': '555-0001', 
                'password': 'TestUser123!', 'is_active': True
            },
            {
                'first_name': 'Test', 'last_name': 'Tester', 'email': 'tester@synapse.com', 
                'role': 'Tester', 'lob_id': 1, 'phone': '555-0002', 
                'password': 'TestUser123!', 'is_active': True
            },
            {
                'first_name': 'Report', 'last_name': 'Owner', 'email': 'owner@synapse.com', 
                'role': 'Report Owner', 'lob_id': 1, 'phone': '555-0003', 
                'password': 'TestUser123!', 'is_active': True
            },
            {
                'first_name': 'Executive', 'last_name': 'Owner', 'email': 'exec@synapse.com', 
                'role': 'Report Owner Executive', 'lob_id': 1, 'phone': '555-0004', 
                'password': 'TestUser123!', 'is_active': True
            },
            {
                'first_name': 'Data', 'last_name': 'Provider', 'email': 'provider@synapse.com', 
                'role': 'Data Owner', 'lob_id': 1, 'phone': '555-0005', 
                'password': 'TestUser123!', 'is_active': True
            },
            {
                'first_name': 'Chief', 'last_name': 'DataOfficer', 'email': 'cdo@synapse.com', 
                'role': 'Data Executive', 'lob_id': None, 'phone': '555-0006', 
                'password': 'TestUser123!', 'is_active': True
            }
        ]
        
        for user in test_users:
            try:
                response = requests.post('http://localhost:8000/api/v1/users/', 
                                       headers=headers, json=user, timeout=10)
                if response.status_code in [200, 201]:
                    result = response.json()
                    print(f'  ✅ Created user: {user["email"]} ({user["role"]}) - ID: {result.get("user_id")}')
                else:
                    print(f'  ❌ Failed to create {user["email"]}: {response.status_code} - {response.text[:200]}')
            except Exception as e:
                print(f'  ❌ Error creating {user["email"]}: {str(e)}')
        
        print('✅ Test user creation completed!')
        
    except Exception as e:
        print(f'❌ Error in user creation process: {str(e)}')

if __name__ == "__main__":
    create_test_users_via_api() 