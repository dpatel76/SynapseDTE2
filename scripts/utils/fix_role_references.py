#!/usr/bin/env python3
"""
Fix all role references in the codebase to use the new role names
"""

import os
import re
from pathlib import Path

# Role mappings from old to new
ROLE_MAPPINGS = {
    "TEST_MANAGER": "TEST_EXECUTIVE",
    "CDO": "DATA_EXECUTIVE",
    "DATA_PROVIDER": "DATA_OWNER"
}

def fix_role_references(file_path):
    """Fix role references in a single file"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        original_content = content
        changed = False
        
        for old_role, new_role in ROLE_MAPPINGS.items():
            # Replace UserRoles.OLD_ROLE with UserRoles.NEW_ROLE
            pattern = f"UserRoles\\.{old_role}"
            replacement = f"UserRoles.{new_role}"
            
            if pattern in content:
                content = content.replace(pattern, replacement)
                changed = True
                print(f"  Replaced {pattern} with {replacement}")
        
        if changed:
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"✅ Fixed roles in: {file_path}")
            return True
        return False
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False

def main():
    """Main function to fix all Python files"""
    root_path = Path("app")
    fixed_count = 0
    total_count = 0
    
    print("Fixing role references in Python files...")
    print("-" * 60)
    
    # Find all Python files
    for py_file in root_path.rglob("*.py"):
        # Skip backup files
        if '.backup' in str(py_file) or '.role_backup' in str(py_file):
            continue
        
        total_count += 1
        if fix_role_references(py_file):
            fixed_count += 1
    
    print("-" * 60)
    print(f"Summary:")
    print(f"  - Files checked: {total_count}")
    print(f"  - Files fixed: {fixed_count}")

if __name__ == "__main__":
    main()