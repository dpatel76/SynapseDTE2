#!/usr/bin/env python3

# Test the primary key generation logic
sample_identifier = "FRY14M-D1-002"
report_name = "FR Y-14M Schedule D.1"

print(f"Sample Identifier: {sample_identifier}")
print(f"Report Name: {report_name}")

# Test the frontend logic
if "FR Y-14M" in report_name and "-" in sample_identifier:
    parts = sample_identifier.split("-")
    print(f"Parts: {parts}")
    if len(parts) >= 3:
        generated_pk = {
            'Report': parts[0],
            'Schedule': parts[1], 
            'Sample_ID': parts[2]
        }
        print(f"Generated PK (should show in frontend): {generated_pk}")
    else:
        print("Not enough parts in sample identifier")
else:
    print("Conditions not met for PK generation")
    print(f"  - 'FR Y-14M' in report_name: {'FR Y-14M' in report_name}")
    print(f"  - '-' in sample_identifier: {'-' in sample_identifier}") 