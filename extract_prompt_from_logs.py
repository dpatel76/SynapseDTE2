#!/usr/bin/env python3
"""Extract the full prompt from backend logs"""

import re

# Read the log file
with open('backend_logs.txt', 'r') as f:
    content = f.read()

# Find all prompts
prompt_pattern = r'=== EXACT PROMPT FOR BATCH (\d+) ===\nPrompt length: (\d+) characters\nFirst 1000 chars of prompt:\n(.*?)\n\.\.\. \(truncated (\d+) characters\)\n=== END PROMPT ==='

matches = re.findall(prompt_pattern, content, re.DOTALL)

print(f"Found {len(matches)} prompts in logs\n")

for i, (batch_num, length, prompt_start, truncated) in enumerate(matches):
    print(f"Batch {batch_num}:")
    print(f"  Total length: {length} characters")
    print(f"  Truncated: {truncated} characters")
    print(f"  First 1000 characters:")
    print("-" * 80)
    print(prompt_start)
    print("-" * 80)
    print()

# Also look for data sources
if "AVAILABLE DATA SOURCES:" in content:
    print("\nLooking for data sources in prompts...")
    # Extract around data sources section
    ds_matches = re.findall(r'(AVAILABLE DATA SOURCES:.*?)(?=\n\n|\Z)', content, re.DOTALL)
    if ds_matches:
        print(f"Found {len(ds_matches)} data source sections")
        for ds in ds_matches[:1]:  # Show first one
            print(ds[:500])
            if len(ds) > 500:
                print(f"... (truncated {len(ds) - 500} chars)")