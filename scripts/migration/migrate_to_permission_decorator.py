#!/usr/bin/env python3
"""
Script to migrate endpoints from RoleChecker to @require_permission decorator
"""

import os
import re
from typing import List, Tuple, Dict

# Mapping of common patterns to permissions
ROLE_TO_PERMISSION_MAP = {
    # Management roles
    "management_roles": [
        ("read", "Basic read operations"),
        ("update", "Update operations"),
        ("approve", "Approval operations"),
    ],
    "admin_roles": [
        ("create", "Create operations"), 
        ("update", "Update operations"),
        ("delete", "Delete operations"),
        ("assign", "Assignment operations"),
    ],
    "tester_roles": [
        ("execute", "Start/execute operations"),
        ("create", "Create attributes/documents"),
        ("update", "Update attributes/documents"),
        ("upload", "Upload documents"),
        ("submit", "Submit for approval"),
        ("complete", "Complete phase"),
        ("generate", "Generate with LLM"),
    ],
    "owner_roles": [
        ("read", "Read operations"),
        ("approve", "Approve operations"),
        ("review", "Review operations"),
    ],
    "data_owner_roles": [
        ("read", "Read operations"),
        ("upload", "Upload documents"),
        ("provide", "Provide information"),
    ],
    "cdo_roles": [
        ("read", "Read operations"),
        ("manage", "Management operations"),
        ("assign", "Assignment operations"),
        ("escalate", "Escalation operations"),
    ]
}

# Common operation patterns to permission mapping
OPERATION_PATTERNS = {
    # CRUD operations
    r"create_": "create",
    r"add_": "create",
    r"new_": "create",
    r"list_": "read",
    r"get_": "read",
    r"view_": "read", 
    r"show_": "read",
    r"update_": "update",
    r"edit_": "update",
    r"modify_": "update",
    r"patch_": "update",
    r"delete_": "delete",
    r"remove_": "delete",
    
    # Workflow operations
    r"start_": "execute",
    r"begin_": "execute",
    r"execute_": "execute",
    r"submit_": "submit",
    r"complete_": "complete",
    r"finish_": "complete",
    r"approve_": "approve",
    r"reject_": "approve",  # Approval includes rejection
    r"override_": "override",
    
    # Document operations
    r"upload_": "upload",
    r"download_": "read",
    
    # Assignment operations
    r"assign_": "assign",
    r"unassign_": "assign",
    
    # Generation operations
    r"generate_": "generate",
    
    # Special operations
    r"escalate_": "escalate",
    r"review_": "review",
    r"identify_": "identify",
}

# Resource name mapping
RESOURCE_MAP = {
    "reports.py": "reports",
    "planning.py": "planning", 
    "scoping.py": "scoping",
    "data_owner.py": "data_owner",
    "sample_selection.py": "sample_selection",
    "testing_execution.py": "testing",
    "observation_management.py": "observations",
    "users.py": "users",
    "lobs.py": "lobs",
    "cycles.py": "cycles",
    "cycle_reports.py": "cycles",
}


def determine_permission_from_function(func_name: str, role_checker_roles: List[str]) -> str:
    """Determine the appropriate permission action based on function name and roles"""
    
    # Check function name patterns
    for pattern, permission in OPERATION_PATTERNS.items():
        if re.search(pattern, func_name):
            return permission
    
    # Check specific role patterns
    if "admin_roles" in role_checker_roles:
        if "toggle" in func_name or "status" in func_name:
            return "update"
        return "update"  # Default for admin operations
    
    if "tester_roles" in role_checker_roles:
        return "execute"  # Default for tester operations
        
    if "owner_roles" in role_checker_roles:
        return "approve"  # Default for owner operations
        
    if "data_owner_roles" in role_checker_roles:
        return "provide"  # Default for data provider operations
    
    # Default fallback
    return "read"


def process_file(file_path: str) -> Tuple[bool, str]:
    """Process a single file and replace RoleChecker with @require_permission"""
    
    # Get resource name from filename
    filename = os.path.basename(file_path)
    resource = RESOURCE_MAP.get(filename, filename.replace('.py', ''))
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Skip if already migrated (has require_permission decorator)
    if "@require_permission" in content and "RoleChecker" not in content:
        return False, "Already migrated"
    
    # Skip if no RoleChecker
    if "RoleChecker" not in content:
        return False, "No RoleChecker found"
    
    original_content = content
    changes_made = False
    
    # Add import if not present
    if "from app.core.permissions import require_permission" not in content:
        # Find the imports section
        import_match = re.search(r'(from app\.core\.auth import.*?\n)', content)
        if import_match:
            content = content.replace(
                import_match.group(0),
                import_match.group(0) + "from app.core.permissions import require_permission\n"
            )
            changes_made = True
    
    # Find all function definitions with RoleChecker
    pattern = r'(@router\.[a-z]+\([^)]+\)\s*\n)([^\n]*\n)?async def ([a-zA-Z_]+)\([^)]*\):\s*\n((?:.*?\n)*?)(\s*RoleChecker\(([^)]+)\)\(current_user\))'
    
    matches = list(re.finditer(pattern, content, re.MULTILINE))
    
    for match in reversed(matches):  # Process in reverse to maintain positions
        router_decorator = match.group(1)
        existing_decorator = match.group(2) or ""
        func_name = match.group(3)
        func_body_before_check = match.group(4)
        role_checker_line = match.group(5)
        role_list = match.group(6)
        
        # Determine permission based on function name and roles
        permission = determine_permission_from_function(func_name, role_list)
        
        # Build new decorator
        new_decorator = f'@require_permission("{resource}", "{permission}")\n'
        
        # Replace the function definition with decorator and remove RoleChecker
        new_function = router_decorator + existing_decorator + new_decorator + f"async def {func_name}("
        
        # Find the complete function definition
        func_start = match.start()
        func_content_start = match.end(3) + 1  # After function name and opening paren
        
        # Find the RoleChecker line to remove it
        role_checker_start = content.find(role_checker_line, func_content_start)
        role_checker_end = role_checker_start + len(role_checker_line)
        
        # Check if there's a newline after RoleChecker to remove it too
        if role_checker_end < len(content) and content[role_checker_end] == '\n':
            role_checker_end += 1
        
        # Remove the RoleChecker line
        content = content[:role_checker_start] + content[role_checker_end:]
        
        # Add the decorator
        decorator_insert_pos = func_start + len(router_decorator) + len(existing_decorator)
        content = content[:decorator_insert_pos] + new_decorator + content[decorator_insert_pos:]
        
        changes_made = True
    
    if changes_made:
        with open(file_path, 'w') as f:
            f.write(content)
        return True, f"Migrated {len(matches)} endpoints"
    
    return False, "No changes needed"


def main():
    """Main function to process all endpoint files"""
    
    endpoints_dir = "/Users/dineshpatel/code/SynapseDT/app/api/v1/endpoints"
    
    # Files to process
    target_files = [
        "reports.py",
        "planning.py", 
        "scoping.py",
        "data_owner.py",
        "sample_selection.py",
        "testing_execution.py",
        "observation_management.py",
        "users.py",
        "lobs.py",
        "cycles.py",
        "cycle_reports.py"
    ]
    
    print("Starting migration from RoleChecker to @require_permission...\n")
    
    for filename in target_files:
        file_path = os.path.join(endpoints_dir, filename)
        
        if not os.path.exists(file_path):
            print(f"❌ {filename}: File not found")
            continue
            
        success, message = process_file(file_path)
        
        if success:
            print(f"✅ {filename}: {message}")
        else:
            print(f"⏭️  {filename}: {message}")
    
    print("\nMigration complete!")
    print("\nIMPORTANT: Please review the changes and adjust permissions as needed.")
    print("Some endpoints may need more specific permissions based on their actual functionality.")


if __name__ == "__main__":
    main()