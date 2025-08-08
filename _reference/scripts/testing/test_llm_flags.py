#!/usr/bin/env python3
"""Test if LLM flags are properly set in scoping API"""

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

# Get scoping attributes
response = requests.get(
    "http://localhost:8001/api/v1/scoping/cycles/4/reports/156/attributes",
    headers=headers
)

if response.status_code == 200:
    attributes = response.json()
    print(f"Total attributes: {len(attributes)}")
    
    # Check LLM flags
    llm_generated_count = sum(1 for attr in attributes if attr.get('llm_generated'))
    has_description_count = sum(1 for attr in attributes if attr.get('description'))
    has_data_type_count = sum(1 for attr in attributes if attr.get('data_type'))
    has_llm_risk_score = sum(1 for attr in attributes if attr.get('llm_risk_score'))
    
    print(f"\nLLM flags summary:")
    print(f"  llm_generated=True: {llm_generated_count}")
    print(f"  Has description: {has_description_count}")
    print(f"  Has data_type: {has_data_type_count}")
    print(f"  Has llm_risk_score: {has_llm_risk_score}")
    
    # Show sample of attributes with llm_generated flag
    print(f"\nFirst 5 attributes with llm_generated flag:")
    llm_attrs = [attr for attr in attributes if attr.get('llm_generated')]
    for i, attr in enumerate(llm_attrs[:5]):
        print(f"\n{i+1}. {attr['attribute_name']}:")
        print(f"   llm_generated: {attr.get('llm_generated')}")
        print(f"   description: {attr.get('description', 'N/A')[:50]}...")
        print(f"   data_type: {attr.get('data_type', 'N/A')}")
        print(f"   llm_risk_score: {attr.get('llm_risk_score', 'N/A')}")
        
    # Show sample of attributes WITHOUT llm_generated flag
    print(f"\nFirst 5 attributes WITHOUT llm_generated flag:")
    non_llm_attrs = [attr for attr in attributes if not attr.get('llm_generated')]
    for i, attr in enumerate(non_llm_attrs[:5]):
        print(f"\n{i+1}. {attr['attribute_name']}:")
        print(f"   llm_generated: {attr.get('llm_generated')}")
        print(f"   description: {attr.get('description', 'N/A')[:50]}...")
        print(f"   data_type: {attr.get('data_type', 'N/A')}")
        print(f"   llm_risk_score: {attr.get('llm_risk_score', 'N/A')}")
        
else:
    print(f"API error: {response.status_code} - {response.text}")