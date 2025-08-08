#!/usr/bin/env python3
"""
Migrate all API endpoints from RoleChecker to @require_permission
"""

import re
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Files to skip (already have RBAC or don't need it)
SKIP_FILES = [
    "auth.py",  # Authentication endpoints
    "test.py",  # Test endpoints
    "admin_rbac.py",  # Already has RBAC
]

# Map endpoint patterns to permissions
ENDPOINT_PATTERNS = {
    # Reports
    r"list_reports": ("reports", "read"),
    r"get_report": ("reports", "read"),
    r"create_report": ("reports", "create"),
    r"update_report": ("reports", "update"),
    r"delete_report": ("reports", "delete"),
    r"approve_report": ("reports", "approve"),
    r"override_report": ("reports", "override"),
    
    # Planning
    r"start_planning": ("planning", "execute"),
    r"upload_planning": ("planning", "upload"),
    r"create.*attribute": ("planning", "create"),
    r"update.*attribute": ("planning", "update"),
    r"delete.*attribute": ("planning", "delete"),
    r"generate.*attributes": ("planning", "generate"),
    r"complete_planning": ("planning", "complete"),
    r"approve_planning": ("planning", "approve"),
    
    # Scoping
    r"start_scoping": ("scoping", "execute"),
    r"generate_scoping": ("scoping", "generate"),
    r"submit_scoping": ("scoping", "submit"),
    r"approve_scoping": ("scoping", "approve"),
    r"complete_scoping": ("scoping", "complete"),
    
    # Data Provider
    r"identify_data_owner": ("data_owner", "identify"),
    r"assign_data_owner": ("data_owner", "assign"),
    r"upload_data": ("data_owner", "upload"),
    r"escalate.*provider": ("data_owner", "escalate"),
    r"complete_data_owner": ("data_owner", "complete"),
    
    # Sample Selection
    r"generate_samples": ("sample_selection", "generate"),
    r"upload_samples": ("sample_selection", "upload"),
    r"approve_samples": ("sample_selection", "approve"),
    r"complete_sample": ("sample_selection", "complete"),
    
    # Request Info
    r"create_request": ("request_info", "execute"),
    r"provide_info": ("request_info", "provide"),
    r"upload_info": ("request_info", "upload"),
    r"complete_request": ("request_info", "complete"),
    
    # Testing
    r"start_testing": ("testing", "execute"),
    r"execute_test": ("testing", "execute"),
    r"submit_test": ("testing", "submit"),
    r"review_test": ("testing", "review"),
    r"approve_test": ("testing", "approve"),
    r"complete_testing": ("testing", "complete"),
    
    # Observations
    r"create_observation": ("observations", "create"),
    r"update_observation": ("observations", "update"),
    r"submit_observation": ("observations", "submit"),
    r"review_observation": ("observations", "review"),
    r"approve_observation": ("observations", "approve"),
    r"override_observation": ("observations", "override"),
    
    # Users
    r"list_users": ("users", "read"),
    r"get_user": ("users", "read"),
    r"create_user": ("users", "create"),
    r"update_user": ("users", "update"),
    r"delete_user": ("users", "delete"),
    
    # LOBs
    r"list_lobs": ("lobs", "read"),
    r"get_lob": ("lobs", "read"),
    r"create_lob": ("lobs", "create"),
    r"update_lob": ("lobs", "update"),
    r"delete_lob": ("lobs", "delete"),
    r"manage_lob": ("lobs", "manage"),
    
    # Data Sources
    r"list_data_sources": ("data_sources", "read"),
    r"create_data_source": ("data_sources", "create"),
    r"update_data_source": ("data_sources", "update"),
    r"delete_data_source": ("data_sources", "delete"),
    r"test_connection": ("data_sources", "test"),
    
    # SLA
    r"get_sla": ("sla", "read"),
    r"update_sla": ("sla", "update"),
    r"configure_sla": ("sla", "configure"),
    
    # Dashboards
    r"dashboard": ("dashboards", "read"),
    r"metrics": ("metrics", "read"),
    
    # Admin
    r"admin": ("system", "admin"),
    r"system": ("system", "configure"),
    
    # Background Jobs
    r"jobs": ("jobs", "manage"),
    
    # LLM
    r"llm": ("llm", "use"),
}

# HTTP method to default action mapping
METHOD_ACTION_MAP = {
    "get": "read",
    "post": "create",
    "put": "update",
    "patch": "update",
    "delete": "delete",
}


def infer_permission(func_name: str, http_method: str, path: str) -> Tuple[str, str]:
    """Infer permission from function name, HTTP method, and path"""
    
    # Try pattern matching first
    for pattern, permission in ENDPOINT_PATTERNS.items():
        if re.search(pattern, func_name, re.IGNORECASE):
            return permission
    
    # Infer from path
    path_parts = path.strip("/").split("/")
    if path_parts:
        # Extract resource from path
        resource = path_parts[0]
        
        # Clean up resource name
        if resource.endswith("s"):
            resource = resource  # Keep plural form
        
        # Special cases
        if "planning" in path:
            resource = "planning"
        elif "scoping" in path:
            resource = "scoping"
        elif "data-owner" in path or "data_owner" in path:
            resource = "data_owner"
        elif "sample" in path:
            resource = "sample_selection"
        elif "request" in path:
            resource = "request_info"
        elif "test" in path and "execution" in path:
            resource = "testing"
        elif "observation" in path:
            resource = "observations"
        elif "workflow" in path:
            resource = "workflow"
        elif "cycle-reports" in path or "cycle_reports" in path:
            resource = "cycles"
        
        # Get action from method
        action = METHOD_ACTION_MAP.get(http_method.lower(), "read")
        
        # Special action cases
        if "approve" in func_name:
            action = "approve"
        elif "override" in func_name:
            action = "override"
        elif "submit" in func_name:
            action = "submit"
        elif "execute" in func_name or "start" in func_name:
            action = "execute"
        elif "generate" in func_name:
            action = "generate"
        elif "upload" in func_name:
            action = "upload"
        elif "assign" in func_name:
            action = "assign"
        elif "complete" in func_name:
            action = "complete"
        
        return resource, action
    
    # Default fallback
    return "system", "read"


def migrate_file(filepath: Path) -> int:
    """Migrate a single file and return number of changes made"""
    print(f"\n{'='*60}")
    print(f"Processing: {filepath.name}")
    print('='*60)
    
    if filepath.name in SKIP_FILES:
        print("⏭️  Skipping (in skip list)")
        return 0
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    changes_made = 0
    
    # Check if file already uses require_permission
    if "@require_permission" in content:
        print("✅ Already uses @require_permission")
        # Still need to check if import exists
        if "from app.core.permissions import require_permission" not in content:
            # Add import
            import_added = add_import(content)
            if import_added != content:
                content = import_added
                changes_made += 1
    else:
        # Add import if not present
        if "from app.core.permissions import require_permission" not in content:
            content = add_import(content)
            if content != original_content:
                changes_made += 1
    
    # Find all endpoint functions with RoleChecker
    pattern = r'(@router\.(get|post|put|patch|delete)\("([^"]+)"[^)]*\))\s*\n(async )?def (\w+)\([^)]*\):[^{]*?\n\s*"""([^"]*)"""\s*\n(\s*#[^\n]*\n)*\s*RoleChecker\([^)]+\)\([^)]+\)'
    
    for match in re.finditer(pattern, content, re.MULTILINE | re.DOTALL):
        router_decorator = match.group(1)
        http_method = match.group(2)
        path = match.group(3)
        func_name = match.group(5)
        
        # Infer permission
        resource, action = infer_permission(func_name, http_method, path)
        
        print(f"\n📝 Found: {func_name}")
        print(f"   Method: {http_method.upper()} {path}")
        print(f"   Permission: @require_permission('{resource}', '{action}')")
        
        changes_made += 1
    
    # Replace RoleChecker with @require_permission
    if changes_made > 0:
        content = replace_role_checkers(content)
        
        # Save file
        with open(filepath, 'w') as f:
            f.write(content)
        
        print(f"\n✅ Updated {changes_made} endpoints")
    else:
        print("\n✨ No changes needed")
    
    return changes_made


def add_import(content: str) -> str:
    """Add require_permission import after other core imports"""
    # Find the last core import
    import_pattern = r'from app\.core\.[^\n]+\n'
    imports = list(re.finditer(import_pattern, content))
    
    if imports:
        last_import = imports[-1]
        insert_pos = last_import.end()
        return (
            content[:insert_pos] +
            "from app.core.permissions import require_permission\n" +
            content[insert_pos:]
        )
    else:
        # Add after other imports
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('from app.') and not line.startswith('from app.core'):
                return '\n'.join(
                    lines[:i] +
                    ['from app.core.permissions import require_permission'] +
                    lines[i:]
                )
    return content


def replace_role_checkers(content: str) -> str:
    """Replace RoleChecker calls with @require_permission decorators"""
    
    # Pattern to match router decorator + function + RoleChecker
    pattern = r'(@router\.(get|post|put|patch|delete)\("([^"]+)"[^)]*\))\s*\n(async )?def (\w+)\([^)]*\):[^{]*?\n\s*"""([^"]*)"""\s*\n(\s*#[^\n]*\n)*\s*RoleChecker\([^)]+\)\([^)]+\)'
    
    def replacer(match):
        router_decorator = match.group(1)
        http_method = match.group(2)
        path = match.group(3)
        async_keyword = match.group(4) or ""
        func_name = match.group(5)
        docstring = match.group(6)
        
        # Infer permission
        resource, action = infer_permission(func_name, http_method, path)
        
        # Build replacement
        result = f"{router_decorator}\n"
        result += f'@require_permission("{resource}", "{action}")\n'
        result += f"{async_keyword}def {func_name}("
        
        return result
    
    # First pass: Add decorators
    content = re.sub(pattern, replacer, content, flags=re.MULTILINE | re.DOTALL)
    
    # Second pass: Remove RoleChecker lines
    content = re.sub(
        r'\s*#[^\n]*\n\s*RoleChecker\([^)]+\)\([^)]+\)\s*\n',
        '\n',
        content
    )
    
    # Clean up any remaining standalone RoleChecker calls
    content = re.sub(
        r'\s*RoleChecker\([^)]+\)\([^)]+\)\s*\n',
        '',
        content
    )
    
    return content


def main():
    """Main migration function"""
    endpoint_dir = Path("app/api/v1/endpoints")
    
    if not endpoint_dir.exists():
        print("Error: app/api/v1/endpoints not found. Run from project root.")
        return
    
    total_files = 0
    total_changes = 0
    migrated_files = []
    
    # Get all Python files
    files = sorted([f for f in endpoint_dir.glob("*.py") if f.name != "__init__.py"])
    
    print(f"Found {len(files)} endpoint files to process")
    
    for filepath in files:
        changes = migrate_file(filepath)
        total_files += 1
        if changes > 0:
            total_changes += changes
            migrated_files.append(filepath.name)
    
    print("\n" + "="*60)
    print("MIGRATION SUMMARY")
    print("="*60)
    print(f"Total files processed: {total_files}")
    print(f"Files migrated: {len(migrated_files)}")
    print(f"Total endpoints updated: {total_changes}")
    
    if migrated_files:
        print("\nMigrated files:")
        for filename in migrated_files:
            print(f"  ✅ {filename}")
    
    print("\n🎉 Migration complete!")
    print("\nNext steps:")
    print("1. Review the changes")
    print("2. Run tests with USE_RBAC=true")
    print("3. Fix any permission mappings if needed")


if __name__ == "__main__":
    main()