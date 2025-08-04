#!/usr/bin/env python3
"""
Rename backend _clean files to become the main files
Since only _clean versions are used by API, we'll use them as source of truth
"""

import os
import shutil
from datetime import datetime

def backup_files():
    """Create backup of all files before renaming"""
    backup_dir = f"backup_logs/backend_rename_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)
    
    files_to_backup = [
        # Clean versions (the ones we'll keep)
        "app/api/v1/endpoints/planning_clean.py",
        "app/api/v1/endpoints/scoping_clean.py",
        "app/api/v1/endpoints/data_owner_clean.py",
        "app/api/v1/endpoints/request_info_clean.py",
        "app/api/v1/endpoints/test_execution_clean.py",
        "app/api/v1/endpoints/observation_management_clean.py",
        # Regular versions (the ones we'll remove)
        "app/api/v1/endpoints/planning.py",
        "app/api/v1/endpoints/scoping.py",
        "app/api/v1/endpoints/data_owner.py",
        "app/api/v1/endpoints/request_info.py",
        "app/api/v1/endpoints/test_execution.py",
        "app/api/v1/endpoints/observation_management.py",
        # API router
        "app/api/v1/api.py"
    ]
    
    for filepath in files_to_backup:
        if os.path.exists(filepath):
            backup_path = os.path.join(backup_dir, filepath)
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            shutil.copy2(filepath, backup_path)
            print(f"Backed up: {filepath}")
    
    return backup_dir

def execute_rename(dry_run=True):
    """Execute the rename operation"""
    renames = [
        ("app/api/v1/endpoints/planning_clean.py", "app/api/v1/endpoints/planning.py"),
        ("app/api/v1/endpoints/scoping_clean.py", "app/api/v1/endpoints/scoping.py"),
        ("app/api/v1/endpoints/data_owner_clean.py", "app/api/v1/endpoints/data_owner.py"),
        ("app/api/v1/endpoints/request_info_clean.py", "app/api/v1/endpoints/request_info.py"),
        ("app/api/v1/endpoints/test_execution_clean.py", "app/api/v1/endpoints/test_execution.py"),
        ("app/api/v1/endpoints/observation_management_clean.py", "app/api/v1/endpoints/observation_management.py"),
    ]
    
    print("\nEXECUTING RENAME OPERATIONS")
    print("=" * 80)
    
    for clean_path, regular_path in renames:
        if os.path.exists(clean_path):
            if dry_run:
                print(f"Would rename: {os.path.basename(clean_path)} → {os.path.basename(regular_path)}")
            else:
                # Remove the old regular version if it exists
                if os.path.exists(regular_path):
                    os.remove(regular_path)
                    print(f"Removed old: {regular_path}")
                
                # Rename clean to regular
                os.rename(clean_path, regular_path)
                print(f"✅ Renamed: {os.path.basename(clean_path)} → {os.path.basename(regular_path)}")
        else:
            print(f"⚠️  File not found: {clean_path}")

def update_api_imports(dry_run=True):
    """Update api.py to remove _clean aliases"""
    api_path = "app/api/v1/api.py"
    
    if not os.path.exists(api_path):
        print("⚠️  api.py not found")
        return
    
    with open(api_path, 'r') as f:
        content = f.read()
    
    # Replace clean imports with regular imports
    replacements = [
        ("planning_clean as planning", "planning"),
        ("scoping_clean as scoping", "scoping"),
        ("data_owner_clean as data_owner", "data_owner"),
        ("request_info_clean as request_info", "request_info"),
        ("test_execution_clean as test_execution", "test_execution"),
        ("observation_management_clean as observation_management", "observation_management"),
    ]
    
    new_content = content
    changes_made = []
    
    for old, new in replacements:
        if old in new_content:
            new_content = new_content.replace(old, new)
            changes_made.append((old, new))
    
    if dry_run:
        if changes_made:
            print("\nWould update api.py imports:")
            for old, new in changes_made:
                print(f"  - '{old}' → '{new}'")
        else:
            print("\nNo changes needed in api.py")
    else:
        if new_content != content:
            with open(api_path, 'w') as f:
                f.write(new_content)
            print("\n✅ Updated api.py imports:")
            for old, new in changes_made:
                print(f"  - '{old}' → '{new}'")
        else:
            print("\n✅ No changes needed in api.py")

def create_restore_script(backup_dir):
    """Create a restore script in case we need to revert"""
    restore_script = f"""#!/bin/bash
# Restore script for backend rename operation
# Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

echo "Restoring backend files from backup..."

# Restore all backed up files
cp -r {backup_dir}/* .

echo "✅ Files restored from {backup_dir}"
echo "Note: You may need to restart the backend server"
"""
    
    script_path = f"{backup_dir}/restore.sh"
    with open(script_path, 'w') as f:
        f.write(restore_script)
    os.chmod(script_path, 0o755)
    print(f"\n📝 Restore script created: {script_path}")

def main():
    import sys
    dry_run = "--dry-run" in sys.argv
    auto_yes = "--yes" in sys.argv or "-y" in sys.argv
    
    print("BACKEND ENDPOINT RENAME TOOL")
    print("=" * 80)
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print("\nThis will:")
    print("1. Rename all _clean.py files to regular .py files")
    print("2. Remove the old regular .py files")
    print("3. Update api.py imports to remove aliases")
    print("\nSince only _clean versions are used by API, they become the source of truth.")
    
    if not dry_run and not auto_yes:
        try:
            response = input("\nContinue? (yes/no): ")
            if response.lower() != "yes":
                print("Aborted.")
                return
        except EOFError:
            print("\nNon-interactive mode detected. Use --yes to auto-confirm.")
            return
    
    # Create backup if not dry run
    backup_dir = None
    if not dry_run:
        backup_dir = backup_files()
        print(f"\n✅ Backup created: {backup_dir}")
    
    # Execute rename
    execute_rename(dry_run)
    
    # Update API imports
    update_api_imports(dry_run)
    
    # Create restore script
    if backup_dir:
        create_restore_script(backup_dir)
    
    if dry_run:
        print("\n✅ Dry run complete. Run without --dry-run to execute.")
    else:
        print("\n✅ Backend rename complete!")
        print("\n⚠️  IMPORTANT:")
        print("1. Restart the backend server")
        print("2. Run tests to ensure everything works")
        print("3. Update any test imports that reference the old files")

if __name__ == "__main__":
    main()