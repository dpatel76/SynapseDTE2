#!/usr/bin/env python3
"""
Migrate remaining endpoints from custom dependencies to @require_permission decorators
"""

import os
import re
import sys
from typing import List, Tuple, Dict

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Permission mapping for each endpoint
PERMISSION_MAPPINGS = {
    "data_owner.py": {
        "require_tester": [("data_owner", "execute")],
        "require_cdo": [("data_owner", "assign")],
        "require_tester_or_cdo": [("data_owner", "read")]
    },
    "sample_selection.py": {
        "require_tester": [("sample_selection", "execute")],
        "require_report_owner": [("sample_selection", "approve")],
        "require_tester_or_report_owner": [("sample_selection", "read")]
    },
    "testing_execution.py": {
        "check_tester_role": [("testing", "execute")],
        "check_report_owner_role": [("testing", "review")],
        "check_test_manager_role": [("testing", "approve")]
    },
    "observation_management.py": {
        "require_tester_access": [("observations", "create")],
        "require_report_owner_access": [("observations", "approve")],
        "require_test_manager_access": [("observations", "override")]
    },
    "lobs.py": {
        "require_management": [("lobs", "manage")]
    }
}

# Files to migrate
FILES_TO_MIGRATE = [
    "/Users/dineshpatel/code/SynapseDT/app/api/v1/endpoints/data_owner.py",
    "/Users/dineshpatel/code/SynapseDT/app/api/v1/endpoints/sample_selection.py",
    "/Users/dineshpatel/code/SynapseDT/app/api/v1/endpoints/testing_execution.py",
    "/Users/dineshpatel/code/SynapseDT/app/api/v1/endpoints/observation_management.py",
    "/Users/dineshpatel/code/SynapseDT/app/api/v1/endpoints/lobs.py"
]


def get_endpoint_info(file_content: str) -> List[Dict]:
    """Extract endpoint information from file content"""
    endpoints = []
    
    # Pattern to match endpoint decorators and function signatures
    pattern = r'@router\.(get|post|put|patch|delete)\([^)]+\)\s*\n\s*async def (\w+)\([^)]*\):'
    matches = re.finditer(pattern, file_content, re.MULTILINE)
    
    for match in matches:
        method = match.group(1)
        function_name = match.group(2)
        
        # Find the function definition and its dependencies
        func_start = match.start()
        func_pattern = rf'async def {function_name}\([^)]*\):'
        func_match = re.search(func_pattern, file_content[func_start:])
        
        if func_match:
            func_def_start = func_start + func_match.start()
            func_def_end = func_start + func_match.end()
            
            # Extract function signature
            func_signature = file_content[func_def_start:func_def_end]
            
            # Check for custom dependencies
            custom_deps = []
            for dep in ["require_tester", "require_cdo", "require_tester_or_cdo", 
                       "require_report_owner", "require_tester_or_report_owner",
                       "check_tester_role", "check_report_owner_role", "check_test_manager_role",
                       "require_tester_access", "require_report_owner_access", "require_test_manager_access",
                       "require_management"]:
                if f"Depends({dep})" in func_signature:
                    custom_deps.append(dep)
            
            endpoints.append({
                "method": method,
                "function_name": function_name,
                "custom_deps": custom_deps,
                "start": func_start,
                "signature": func_signature
            })
    
    return endpoints


def determine_permissions(function_name: str, method: str, custom_deps: List[str], file_name: str) -> Tuple[str, str]:
    """Determine resource and action based on function name and method"""
    base_name = os.path.basename(file_name)
    
    # Use mappings if available
    if base_name in PERMISSION_MAPPINGS and custom_deps:
        for dep in custom_deps:
            if dep in PERMISSION_MAPPINGS[base_name]:
                return PERMISSION_MAPPINGS[base_name][dep][0]
    
    # Default mappings based on function name patterns
    if "create" in function_name or method == "post" and not any(x in function_name for x in ["approve", "complete", "submit"]):
        action = "create"
    elif "update" in function_name or method in ["put", "patch"]:
        action = "update"
    elif "delete" in function_name or method == "delete":
        action = "delete"
    elif "approve" in function_name:
        action = "approve"
    elif "complete" in function_name:
        action = "complete"
    elif "submit" in function_name:
        action = "submit"
    elif "execute" in function_name or "start" in function_name:
        action = "execute"
    elif "upload" in function_name:
        action = "upload"
    elif "generate" in function_name:
        action = "generate"
    elif "review" in function_name:
        action = "review"
    elif "assign" in function_name:
        action = "assign"
    elif "escalate" in function_name:
        action = "escalate"
    else:
        action = "read"
    
    # Determine resource based on file name
    if "data_owner" in file_name:
        resource = "data_owner"
    elif "sample_selection" in file_name:
        resource = "sample_selection"
    elif "testing_execution" in file_name:
        resource = "testing"
    elif "observation_management" in file_name:
        resource = "observations"
    elif "lobs" in file_name:
        resource = "lobs"
    else:
        resource = "unknown"
    
    return resource, action


def migrate_file(file_path: str) -> bool:
    """Migrate a single file"""
    print(f"\n{'='*60}")
    print(f"Migrating: {file_path}")
    print(f"{'='*60}")
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check if already migrated
        if "@require_permission" in content:
            print("✓ File already migrated")
            return True
        
        # Get endpoint information
        endpoints = get_endpoint_info(content)
        print(f"Found {len(endpoints)} endpoints")
        
        # Process content
        new_content = content
        
        # Add import if not present
        if "from app.core.permissions import require_permission" not in new_content:
            # Find the imports section
            import_match = re.search(r'(from app\.core\.dependencies import[^\n]+)', new_content)
            if import_match:
                import_line = import_match.group(1)
                new_import = import_line + "\nfrom app.core.permissions import require_permission"
                new_content = new_content.replace(import_line, new_import)
        
        # Process each endpoint
        for endpoint in endpoints:
            if not endpoint["custom_deps"]:
                continue
            
            print(f"\nProcessing: {endpoint['function_name']} ({endpoint['method'].upper()})")
            print(f"  Custom deps: {endpoint['custom_deps']}")
            
            # Determine permissions
            resource, action = determine_permissions(
                endpoint['function_name'], 
                endpoint['method'], 
                endpoint['custom_deps'],
                file_path
            )
            print(f"  Permission: {resource}:{action}")
            
            # Find the complete function definition
            func_pattern = rf'(@router\.{endpoint["method"]}[^\n]+\n(?:\s*@[^\n]+\n)*)\s*(async def {endpoint["function_name"]}\([^)]*\)):'
            func_match = re.search(func_pattern, new_content, re.MULTILINE)
            
            if func_match:
                # Add decorator before the function
                decorator_line = f'@require_permission("{resource}", "{action}")'
                
                # Check for resource_id_param need
                if action in ["update", "delete", "approve"] and any(param in endpoint["function_name"] for param in ["cycle_id", "report_id", "observation_id"]):
                    # Look for common ID parameters
                    if "observation_id" in func_match.group(2):
                        decorator_line = f'@require_permission("{resource}", "{action}", resource_id_param="observation_id")'
                    elif "report_id" in func_match.group(2):
                        decorator_line = f'@require_permission("{resource}", "{action}", resource_id_param="report_id")'
                
                # Insert decorator
                new_func_def = f"{func_match.group(1)}{decorator_line}\n{func_match.group(2)}:"
                new_content = new_content.replace(func_match.group(0), new_func_def)
                
                # Remove custom dependency from function signature
                for dep in endpoint["custom_deps"]:
                    # Remove the dependency parameter
                    patterns = [
                        rf',\s*_:\s*\w+\s*=\s*Depends\({dep}\)',  # Named underscore parameter
                        rf',\s*\w+:\s*\w+\s*=\s*Depends\({dep}\)',  # Named parameter
                        rf'\s*_:\s*\w+\s*=\s*Depends\({dep}\),',   # Underscore parameter at start
                        rf'\s*\w+:\s*\w+\s*=\s*Depends\({dep}\),'   # Named parameter at start
                    ]
                    
                    for pattern in patterns:
                        new_content = re.sub(pattern, '', new_content)
        
        # Remove old role check functions if they're no longer used
        old_functions = [
            "require_tester", "require_cdo", "require_tester_or_cdo",
            "require_report_owner", "require_tester_or_report_owner",
            "check_tester_role", "check_report_owner_role", "check_test_manager_role",
            "require_tester_access", "require_report_owner_access", "require_test_manager_access"
        ]
        
        for func in old_functions:
            # Check if function is still used
            if f"Depends({func})" not in new_content:
                # Remove the function definition
                func_def_pattern = rf'def {func}\([^)]*\):[^}}]+}}\s*return \w+\s*\n\n'
                new_content = re.sub(func_def_pattern, '', new_content, flags=re.MULTILINE | re.DOTALL)
        
        # Clean up extra blank lines
        new_content = re.sub(r'\n\n\n+', '\n\n', new_content)
        
        # Write the migrated content
        with open(file_path, 'w') as f:
            f.write(new_content)
        
        print("✓ Migration complete")
        return True
        
    except Exception as e:
        print(f"✗ Error migrating file: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main migration function"""
    print("Starting migration of remaining endpoints to @require_permission decorators")
    
    success_count = 0
    failed_files = []
    
    for file_path in FILES_TO_MIGRATE:
        if os.path.exists(file_path):
            if migrate_file(file_path):
                success_count += 1
            else:
                failed_files.append(file_path)
        else:
            print(f"✗ File not found: {file_path}")
            failed_files.append(file_path)
    
    print(f"\n{'='*60}")
    print("Migration Summary")
    print(f"{'='*60}")
    print(f"Total files: {len(FILES_TO_MIGRATE)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {len(failed_files)}")
    
    if failed_files:
        print("\nFailed files:")
        for file in failed_files:
            print(f"  - {file}")
    
    return len(failed_files) == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)