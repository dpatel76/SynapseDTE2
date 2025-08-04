#!/usr/bin/env python3
"""Detailed test of scoping API response structure"""

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
    print(f"Found {len(attributes)} attributes\n")
    
    # Show detailed structure of first few LLM-generated attributes
    llm_attrs = [attr for attr in attributes if attr.get('llm_generated')]
    print(f"LLM-generated attributes: {len(llm_attrs)}")
    
    for i, attr in enumerate(llm_attrs[:3]):
        print(f"\n--- Attribute {i+1}: {attr.get('attribute_name')} ---")
        print(f"  llm_generated: {attr.get('llm_generated')}")
        print(f"  description: {attr.get('description', 'N/A')}")
        print(f"  data_type: {attr.get('data_type', 'N/A')}")
        print(f"  llm_risk_score: {attr.get('llm_risk_score', 'N/A')}")
        print(f"  is_cde: {attr.get('is_cde', False)}")
        print(f"  has_historical_issues: {attr.get('has_historical_issues', False)}")
        
        # Show rationale structure
        rationale = attr.get('llm_rationale', '')
        if rationale:
            print(f"\n  llm_rationale preview:")
            lines = rationale.split('\n')[:3]
            for line in lines:
                print(f"    {line}")
            if len(rationale.split('\n')) > 3:
                print(f"    ... ({len(rationale.split('\n'))} total lines)")
        
        # Show risk score details if present
        details = attr.get('llm_risk_score_details')
        if details:
            print(f"\n  llm_risk_score_details:")
            try:
                if isinstance(details, str):
                    details_dict = json.loads(details)
                else:
                    details_dict = details
                for key, value in list(details_dict.items())[:4]:
                    print(f"    {key}: {value}")
            except:
                print(f"    (unable to parse details)")
                
    # Check scoping decisions API
    print("\n\n=== Testing Scoping Decisions API ===")
    decisions_response = requests.get(
        "http://localhost:8001/api/v1/scoping/cycles/4/reports/156/decisions",
        headers=headers
    )
    
    if decisions_response.status_code == 200:
        data = decisions_response.json()
        print(f"Response type: {type(data)}")
        print(f"Response keys: {list(data.keys()) if isinstance(data, dict) else 'N/A'}")
        
        if isinstance(data, dict) and 'decisions' in data:
            decisions = data['decisions']
            print(f"Decisions array length: {len(decisions)}")
            if decisions:
                print(f"First decision keys: {list(decisions[0].keys())}")
                print(f"Sample decision: {decisions[0].get('attribute_name')} - is_scoped: {decisions[0].get('is_scoped')}")
        
else:
    print(f"API error: {response.status_code} - {response.text}")