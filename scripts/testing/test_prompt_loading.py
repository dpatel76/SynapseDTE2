#!/usr/bin/env python3
"""Test prompt template loading"""

import sys
sys.path.append('.')

from app.core.prompt_manager import get_prompt_manager

prompt_manager = get_prompt_manager()

# Test loading the template
template = prompt_manager.load_prompt_template(
    "scoping_recommendations",
    regulatory_report="fr_y_14m",
    schedule="schedule_d_1"
)

print(f"Template type: {type(template)}")
print(f"Template object: {template}")

if template:
    # Try to format it
    try:
        formatted = template.safe_substitute(
            regulatory_context="FR Y-14M Schedule D.1",
            report_name="Credit Card Portfolio",
            attributes_json="[]",
            batch_size=1
        )
        print(f"\nFormatted prompt preview (first 200 chars):")
        print(formatted[:200])
    except Exception as e:
        print(f"\nError formatting template: {e}")
        print(f"Error type: {type(e)}")