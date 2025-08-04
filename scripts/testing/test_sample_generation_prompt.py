#!/usr/bin/env python3
"""Test that sample generation uses the correct prompt with proper variables"""

from string import Template

# Load the prompt template
prompt_path = "prompts/regulatory/fr_y_14m/schedule_d_1/sample_generation.txt"
with open(prompt_path, 'r') as f:
    prompt_template = Template(f.read())

# Example variables (what the code should be passing)
test_variables = {
    "scoped_attributes": """- Reference Number (String)
- Account Number (String)
- Current Balance (Decimal)
- Credit Limit (Decimal)
- Days Past Due (Integer)""",
    "sample_size": 10,
    "regulation_context": "FR Y-14M Schedule D.1",
    "risk_focus_areas": "credit risk, operational risk, market risk",
    "attribute_fields": '''"Reference Number": "<String>",
    "Account Number": "<String>",
    "Current Balance": "<Decimal>",
    "Credit Limit": "<Decimal>",
    "Days Past Due": "<Integer>"''',
    "attribute_details": """- Reference Number: String (Primary Key) - REQUIRED
- Account Number: String - REQUIRED
- Current Balance: Decimal - REQUIRED
- Credit Limit: Decimal - REQUIRED
- Days Past Due: Integer"""
}

# Substitute variables
try:
    prompt = prompt_template.safe_substitute(**test_variables)
    print("✅ Prompt template variables substituted successfully!")
    print("\nVariables passed:")
    for key, value in test_variables.items():
        print(f"\n{key}:")
        print(f"  {repr(value)[:100]}...")
    
    print("\nPrompt begins with:")
    print(prompt[:500])
    
    # Check if any variables were not substituted
    import re
    unsubstituted = re.findall(r'\$\{?\w+\}?', prompt)
    if unsubstituted:
        print("\n⚠️  WARNING: Unsubstituted variables found:", unsubstituted)
    else:
        print("\n✅ All variables were properly substituted")
        
except Exception as e:
    print(f"❌ Error: {e}")