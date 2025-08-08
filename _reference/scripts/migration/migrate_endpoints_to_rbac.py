#!/usr/bin/env python3
"""
Migrate endpoints from RoleChecker to @require_permission decorators
"""

import re
import os
from pathlib import Path
from typing import Dict, List, Tuple

# Map old role checks to new permissions
ROLE_TO_PERMISSION_MAP = {
    # Cycles
    "RoleChecker(admin_roles)": ("cycles", "create|update|delete"),
    "RoleChecker(management_roles)": ("cycles", "read"),
    "RoleChecker([UserRoles.TEST_EXECUTIVE])": ("cycles", "create|update|delete|assign"),
    
    # Reports
    "RoleChecker([UserRoles.REPORT_OWNER])": ("reports", "approve"),
    "RoleChecker([UserRoles.REPORT_OWNER_EXECUTIVE])": ("reports", "override"),
    
    # Planning
    "RoleChecker([UserRoles.TESTER])": ("planning", "execute"),
    "RoleChecker([UserRoles.TEST_EXECUTIVE, UserRoles.REPORT_OWNER])": ("planning", "approve"),
    
    # Users
    "RoleChecker([UserRoles.ADMIN])": ("users", "create|update|delete"),
    
    # System
    "require_admin": ("system", "admin"),
}

# Endpoint to permission mapping
ENDPOINT_PERMISSION_MAP = {
    # Cycles
    "create_test_cycle": ("cycles", "create"),
    "list_test_cycles": ("cycles", "read"),
    "get_test_cycle": ("cycles", "read"),
    "update_test_cycle": ("cycles", "update"),
    "delete_test_cycle": ("cycles", "delete"),
    "assign_reports_to_cycle": ("cycles", "assign"),
    "remove_report_from_cycle": ("cycles", "assign"),
    
    # Reports
    "list_reports": ("reports", "read"),
    "get_report": ("reports", "read"),
    "update_report": ("reports", "update"),
    "approve_report": ("reports", "approve"),
    "override_report": ("reports", "override"),
    
    # Planning
    "start_planning_phase": ("planning", "execute"),
    "upload_planning_document": ("planning", "upload"),
    "create_attribute": ("planning", "create"),
    "update_attribute": ("planning", "update"),
    "delete_attribute": ("planning", "delete"),
    "generate_attributes": ("planning", "generate"),
    "complete_planning_phase": ("planning", "complete"),
    
    # Scoping
    "start_scoping_phase": ("scoping", "execute"),
    "generate_scoping": ("scoping", "generate"),
    "submit_scoping": ("scoping", "submit"),
    "approve_scoping": ("scoping", "approve"),
    "complete_scoping_phase": ("scoping", "complete"),
    
    # Data Provider
    "identify_data_owner": ("data_owner", "identify"),
    "assign_data_owner": ("data_owner", "assign"),
    "upload_data": ("data_owner", "upload"),
    "escalate_data_owner": ("data_owner", "escalate"),
    
    # Sample Selection
    "generate_samples": ("sample_selection", "generate"),
    "upload_samples": ("sample_selection", "upload"),
    "approve_samples": ("sample_selection", "approve"),
    
    # Testing
    "execute_test": ("testing", "execute"),
    "submit_test_results": ("testing", "submit"),
    "review_test_results": ("testing", "review"),
    "approve_test_results": ("testing", "approve"),
    
    # Observations
    "create_observation": ("observations", "create"),
    "submit_observation": ("observations", "submit"),
    "review_observation": ("observations", "review"),
    "approve_observation": ("observations", "approve"),
    "override_observation": ("observations", "override"),
}


def get_permission_for_endpoint(func_name: str, endpoint_path: str) -> Tuple[str, str]:
    """Determine permission based on function name and endpoint path"""
    
    # Direct mapping
    if func_name in ENDPOINT_PERMISSION_MAP:
        return ENDPOINT_PERMISSION_MAP[func_name]
    
    # Infer from HTTP method and path
    if "POST" in endpoint_path:
        if "assign" in func_name:
            return extract_resource(endpoint_path), "assign"
        elif "upload" in func_name:
            return extract_resource(endpoint_path), "upload"
        else:
            return extract_resource(endpoint_path), "create"
    elif "GET" in endpoint_path:
        return extract_resource(endpoint_path), "read"
    elif "PUT" in endpoint_path or "PATCH" in endpoint_path:
        return extract_resource(endpoint_path), "update"
    elif "DELETE" in endpoint_path:
        return extract_resource(endpoint_path), "delete"
    
    return extract_resource(endpoint_path), "read"


def extract_resource(path: str) -> str:
    """Extract resource name from endpoint path"""
    parts = path.strip("/").split("/")
    if parts:
        resource = parts[0]
        # Convert to singular form and handle special cases
        if resource == "cycles":
            return "cycles"
        elif resource == "reports":
            return "reports"
        elif resource == "users":
            return "users"
        elif resource == "planning":
            return "planning"
        elif resource == "scoping":
            return "scoping"
        elif resource.startswith("data"):
            return "data_owner"
        elif resource.startswith("sample"):
            return "sample_selection"
        elif resource.startswith("test"):
            return "testing"
        elif resource.startswith("observ"):
            return "observations"
    return "system"


def migrate_endpoint_file(filepath: Path) -> bool:
    """Migrate a single endpoint file"""
    print(f"\nProcessing {filepath.name}...")
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    changes_made = False
    
    # Check if already has require_permission import
    if "from app.core.permissions import require_permission" not in content:
        # Add import after other core imports
        import_pattern = r'(from app\.core\..*\n)'
        last_import = list(re.finditer(import_pattern, content))[-1]
        insert_pos = last_import.end()
        content = (
            content[:insert_pos] + 
            "from app.core.permissions import require_permission\n" +
            content[insert_pos:]
        )
        changes_made = True
    
    # Find all endpoint functions
    endpoint_pattern = r'@router\.(get|post|put|patch|delete)\("([^"]+)"[^)]*\)\s*\n(async )?def (\w+)\([^)]*\):\s*\n\s*"""([^"]*)"""\s*\n(\s*#.*\n)*\s*RoleChecker\([^)]+\)\([^)]+\)'
    
    for match in re.finditer(endpoint_pattern, content):
        http_method = match.group(1).upper()
        endpoint_path = match.group(2)
        func_name = match.group(4)
        
        # Get appropriate permission
        resource, action = get_permission_for_endpoint(func_name, f"{http_method} {endpoint_path}")
        
        # Build the decorator line
        decorator_line = f'@require_permission("{resource}", "{action}")'
        
        # Find where to insert the decorator (after the router decorator)
        router_decorator_end = match.start() + len(f'@router.{match.group(1)}("{match.group(2)}"')
        # Find the end of the router decorator line
        line_end = content.find('\n', router_decorator_end)
        
        # Insert the permission decorator
        new_content = (
            content[:line_end] + '\n' +
            decorator_line +
            content[line_end:]
        )
        
        # Remove the RoleChecker line
        role_checker_pattern = r'\s*#.*\n\s*RoleChecker\([^)]+\)\([^)]+\)\s*\n'
        new_content = re.sub(role_checker_pattern, '\n', new_content, count=1)
        
        if new_content != content:
            content = new_content
            changes_made = True
            print(f"  - Updated {func_name}: @require_permission('{resource}', '{action}')")
    
    if changes_made:
        # Write updated content
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"  ✓ File updated successfully")
        return True
    else:
        print(f"  - No changes needed")
        return False


def main():
    """Main migration function"""
    endpoint_dir = Path("app/api/v1/endpoints")
    
    if not endpoint_dir.exists():
        print(f"Error: {endpoint_dir} not found. Run from project root.")
        return
    
    files_to_migrate = [
        "cycles.py",
        "reports.py", 
        "planning.py",
        "scoping.py",
        "data_owner.py",
        "sample_selection.py",
        "request_info.py",
        "testing_execution.py",
        "observation_management.py",
        "users.py",
        "admin.py"
    ]
    
    total_updated = 0
    
    for filename in files_to_migrate:
        filepath = endpoint_dir / filename
        if filepath.exists():
            if migrate_endpoint_file(filepath):
                total_updated += 1
        else:
            print(f"\nSkipping {filename} - file not found")
    
    print(f"\n{'='*50}")
    print(f"Migration complete! Updated {total_updated} files.")
    print("\nNext steps:")
    print("1. Review the changes")
    print("2. Run tests to ensure everything works")
    print("3. Update any custom permission checks")


if __name__ == "__main__":
    main()