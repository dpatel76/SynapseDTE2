#!/usr/bin/env python3
"""
Update frontend role references
"""

import os
import re

# Role mappings
ROLE_MAPPINGS = {
    # In strings/text
    "CDO": "Data Executive",
    "Test Manager": "Test Executive", 
    "Data Provider": "Data Owner",
    
    # In file imports/references
    "CDOAssignmentsPage": "DataExecutiveAssignmentsPage",
    "CDOAssignmentInterface": "DataExecutiveAssignmentInterface",
    "DataProviderPage": "DataOwnerPage",
    "CDODashboard": "DataExecutiveDashboard",
    "DataProviderDashboard": "DataOwnerDashboard",
    "TestManagerDashboard": "TestExecutiveDashboard",
}

# Frontend paths to update
FRONTEND_PATHS = [
    "frontend/src/pages",
    "frontend/src/components", 
    "frontend/src/types",
    "frontend/src/App.tsx"
]

def update_file_content(file_path):
    """Update role references in file content"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        original_content = content
        
        # Apply all mappings
        for old_name, new_name in ROLE_MAPPINGS.items():
            # Update import statements
            content = re.sub(rf'\b{re.escape(old_name)}\b', new_name, content)
            
        # Only write if content changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Updated: {file_path}")
            return True
            
    except Exception as e:
        print(f"❌ Error updating {file_path}: {e}")
    
    return False

def update_frontend_roles():
    """Update all frontend role references"""
    print("Updating frontend role references...")
    print("=" * 60)
    
    updated_count = 0
    
    for path in FRONTEND_PATHS:
        full_path = os.path.join(os.path.dirname(__file__), "..", path)
        
        if os.path.isfile(full_path):
            # Single file
            if full_path.endswith(('.ts', '.tsx', '.js', '.jsx')):
                if update_file_content(full_path):
                    updated_count += 1
        else:
            # Directory
            for root, dirs, files in os.walk(full_path):
                # Skip node_modules and build directories
                if 'node_modules' in root or 'build' in root:
                    continue
                    
                for file in files:
                    if file.endswith(('.ts', '.tsx', '.js', '.jsx')):
                        file_path = os.path.join(root, file)
                        if update_file_content(file_path):
                            updated_count += 1
    
    print("=" * 60)
    print(f"Updated {updated_count} files")

if __name__ == "__main__":
    update_frontend_roles()