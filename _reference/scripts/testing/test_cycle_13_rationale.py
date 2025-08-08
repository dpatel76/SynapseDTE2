#!/usr/bin/env python3
"""Check what rationale data exists for cycle 13"""

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
    
    # Find attributes with rationale
    attrs_with_rationale = [attr for attr in attributes if attr.get('llm_rationale')]
    
    print(f"Total attributes: {len(attributes)}")
    print(f"Attributes with llm_rationale: {len(attrs_with_rationale)}")
    
    # Show first few attributes with rationale
    print(f"\nFirst 3 attributes with rationale:")
    for i, attr in enumerate(attrs_with_rationale[:3]):
        print(f"\n{i+1}. {attr['attribute_name']}:")
        print(f"   llm_generated: {attr.get('llm_generated')}")
        print(f"   llm_rationale preview: {attr.get('llm_rationale', '')[:200]}...")
        
    # Check a specific attribute like Customer ID
    customer_id_attrs = [attr for attr in attributes if 'Customer ID' in attr['attribute_name']]
    if customer_id_attrs:
        print(f"\n\nCustomer ID attribute details:")
        for attr in customer_id_attrs:
            print(f"\nAttribute: {attr['attribute_name']}")
            print(f"  llm_generated: {attr.get('llm_generated')}")
            print(f"  description: {attr.get('description')}")
            print(f"  llm_rationale: {attr.get('llm_rationale', 'N/A')[:300]}...")
            print(f"  llm_risk_score: {attr.get('llm_risk_score')}")
            
else:
    print(f"API error: {response.status_code} - {response.text}")