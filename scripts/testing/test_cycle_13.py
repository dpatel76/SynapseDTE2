#!/usr/bin/env python3
"""Test scoping API for cycle 13 report 156"""

import requests
import json

# Login first
login_data = {
    "email": "tester@example.com",
    "password": "password123"
}

login_response = requests.post("http://localhost:8001/api/v1/auth/login", json=login_data)
if login_response.status_code != 200:
    print(f"Login failed: {login_response.text}")
    exit(1)

token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Get scoping attributes for cycle 13 report 156
response = requests.get(
    "http://localhost:8001/api/v1/scoping/cycles/13/reports/156/attributes",
    headers=headers
)

if response.status_code == 200:
    attributes = response.json()
    print(f"Total attributes for cycle 13: {len(attributes)}")
    
    # Check LLM fields
    llm_generated_count = sum(1 for attr in attributes if attr.get('llm_generated'))
    has_description_count = sum(1 for attr in attributes if attr.get('description'))
    has_data_type_count = sum(1 for attr in attributes if attr.get('data_type'))
    has_historical_issues = sum(1 for attr in attributes if attr.get('has_historical_issues'))
    
    print(f"\nLLM fields summary:")
    print(f"  llm_generated=True: {llm_generated_count}")
    print(f"  Has description: {has_description_count}")
    print(f"  Has data_type: {has_data_type_count}")
    print(f"  Has historical_issues flag: {has_historical_issues}")
    
    # Show first few attributes
    print(f"\nFirst 5 attributes:")
    for i, attr in enumerate(attributes[:5]):
        print(f"\n{i+1}. {attr['attribute_name']}:")
        print(f"   attribute_id: {attr.get('attribute_id')}")
        print(f"   llm_generated: {attr.get('llm_generated')}")
        print(f"   description: {attr.get('description', 'N/A')[:50]}...")
        print(f"   data_type: {attr.get('data_type', 'N/A')}")
        print(f"   has_historical_issues: {attr.get('has_historical_issues', False)}")
        print(f"   historical_issues_flag: {attr.get('historical_issues_flag', False)}")
        
    # Check which attributes have historical issues
    print(f"\n\nAttributes with historical_issues=True:")
    hist_attrs = [attr for attr in attributes if attr.get('has_historical_issues') or attr.get('historical_issues_flag')]
    for attr in hist_attrs[:10]:  # Show first 10
        print(f"  - {attr['attribute_name']} (id: {attr['attribute_id']})")
        
else:
    print(f"API error: {response.status_code} - {response.text}")