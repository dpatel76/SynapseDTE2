#!/usr/bin/env python3
"""Test scoping API response"""

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

# Test the scoping decisions endpoint for cycle 13, report 156
print("Testing scoping decisions endpoint...")
response = requests.get(
    "http://localhost:8001/api/v1/scoping/cycles/13/reports/156/decisions",
    headers=headers
)

if response.status_code == 200:
    data = response.json()
    print(f"\nDecisions API Response:")
    print(f"  Total attributes with decisions: {data.get('total_attributes')}")
    print(f"  Scoped count: {data.get('scoped_count')}")
    print(f"  Not scoped count: {data.get('not_scoped_count')}")
    print(f"\n  Number of decisions: {len(data.get('decisions', []))}")
    
    # Show first few decisions
    decisions = data.get('decisions', [])
    if decisions:
        print(f"\n  First 3 decisions:")
        for i, decision in enumerate(decisions[:3]):
            print(f"\n  Decision {i+1}:")
            print(f"    attribute_id: {decision.get('attribute_id')}")
            print(f"    attribute_name: {decision.get('attribute_name')}")
            print(f"    is_scoped: {decision.get('is_scoped')}")
            print(f"    is_primary_key: {decision.get('is_primary_key')}")
else:
    print(f"API error: {response.status_code} - {response.text}")

# Also check the attributes endpoint
print("\n\nTesting attributes endpoint...")
attr_response = requests.get(
    "http://localhost:8001/api/v1/scoping/cycles/13/reports/156/attributes",
    headers=headers
)

if attr_response.status_code == 200:
    attributes = attr_response.json()
    print(f"\nAttributes API Response:")
    print(f"  Total attributes: {len(attributes)}")
    
    # Count approved attributes
    approved_count = sum(1 for a in attributes if a.get('approval_status') == 'approved')
    print(f"  Approved attributes: {approved_count}")
    
    # Count primary key attributes
    pk_count = sum(1 for a in attributes if a.get('is_primary_key') == True)
    print(f"  Primary key attributes: {pk_count}")
    
    # Find specific primary key attributes
    pk_attrs = [a for a in attributes if a.get('attribute_name') in ['Period ID', 'Customer ID', 'Reference Number', 'Bank ID']]
    if pk_attrs:
        print(f"\n  Primary Key Attributes:")
        for pk in pk_attrs:
            print(f"    - {pk.get('attribute_name')}: is_primary_key={pk.get('is_primary_key')}, is_scoped={pk.get('is_scoped')}")
    
    # Show first attribute
    if attributes:
        attr = attributes[0]
        print(f"\n  First attribute:")
        print(f"    attribute_id: {attr.get('attribute_id')}")
        print(f"    attribute_name: {attr.get('attribute_name')}")
        print(f"    approval_status: {attr.get('approval_status')}")
        print(f"    is_scoped: {attr.get('is_scoped')}")
        print(f"    is_primary_key: {attr.get('is_primary_key')}")
        print(f"\n  Raw attribute keys: {list(attr.keys())}")
else:
    print(f"API error: {attr_response.status_code} - {attr_response.text}")