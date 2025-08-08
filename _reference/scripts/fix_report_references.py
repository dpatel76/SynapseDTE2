#!/usr/bin/env python
"""Fix all report_inventory references to reports in the models"""

import os
import re

def fix_report_references():
    models_dir = os.path.join(os.path.dirname(__file__), '..', 'app', 'models')
    
    # Pattern to match report_inventory references
    patterns = [
        # Foreign key references
        (r'ForeignKey\(["\']report_inventory\.', 'ForeignKey("reports.'),
        # Relationship references  
        (r'report_inventory\.id', 'reports.id'),
        # String references in relationships
        (r'["\']report_inventory["\']', '"reports"'),
    ]
    
    files_updated = 0
    
    # Walk through all Python files in models directory
    for root, dirs, files in os.walk(models_dir):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                
                # Read file content
                with open(filepath, 'r') as f:
                    content = f.read()
                
                # Apply all patterns
                original_content = content
                for pattern, replacement in patterns:
                    content = re.sub(pattern, replacement, content)
                
                # Write back if changed
                if content != original_content:
                    with open(filepath, 'w') as f:
                        f.write(content)
                    print(f"Updated: {filepath}")
                    files_updated += 1
    
    print(f"\nTotal files updated: {files_updated}")

if __name__ == '__main__':
    fix_report_references()