#!/usr/bin/env python3
"""Fix get_current_active_user to get_current_user in all files"""

import os
import re

# Files to fix
files = [
    "app/api/v1/endpoints/planning_clean.py",
    "app/api/v1/endpoints/scoping_clean.py",
    "app/api/v1/endpoints/workflow_clean.py",
    "app/api/v1/endpoints/test_execution_clean.py",
    "app/api/v1/endpoints/testing_execution_clean.py",
]

# Pattern to replace
pattern = r'deps\.get_current_active_user'
replacement = 'deps.get_current_user'

for file_path in files:
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Replace the pattern
        new_content = re.sub(pattern, replacement, content)
        
        if new_content != content:
            with open(file_path, 'w') as f:
                f.write(new_content)
            print(f"Fixed {file_path}")
        else:
            print(f"No changes needed in {file_path}")
    else:
        print(f"File not found: {file_path}")

print("Done!")