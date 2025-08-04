#!/usr/bin/env python3
"""
Clean up import references after file backup
"""

import os
import re
from pathlib import Path

# Define changes to make
IMPORT_CHANGES = [
    # Frontend - Remove unused imports
    {
        "file": "frontend/src/App.tsx",
        "changes": [
            {
                "old": "const ObservationManagementPage = React.lazy(() => import('./pages/phases/ObservationManagementPage'));",
                "new": "// Removed - using ObservationManagementEnhanced instead"
            },
            {
                "old": "const ReportTestingPage = React.lazy(() => import('./pages/ReportTestingPage'));",
                "new": "// Removed - using ReportTestingPageRedesigned instead"
            },
            {
                "old": "const MyAssignmentsPage = lazy(() => import('./pages/MyAssignmentsPage'));",
                "new": "// Removed - using UniversalMyAssignmentsPage instead"
            }
        ]
    },
    # Backend - Remove unused ObservationRecord import
    {
        "file": "app/application/use_cases/dashboard.py",
        "changes": [
            {
                "old": "from app.models.observation_management import ObservationRecord",
                "new": "# Removed unused import - ObservationRecord"
            }
        ]
    }
]

def backup_file(filepath):
    """Create a backup of the file before modifying"""
    backup_path = f"{filepath}.pre_import_cleanup"
    if not os.path.exists(backup_path):
        with open(filepath, 'r') as f:
            content = f.read()
        with open(backup_path, 'w') as f:
            f.write(content)
        print(f"  ✓ Backed up: {filepath}")
        return True
    else:
        print(f"  ⚠️  Backup already exists: {backup_path}")
        return False

def apply_changes(filepath, changes):
    """Apply the specified changes to a file"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    changes_made = 0
    
    for change in changes:
        if change["old"] in content:
            content = content.replace(change["old"], change["new"])
            changes_made += 1
            print(f"  ✓ Replaced: {change['old'][:50]}...")
        else:
            print(f"  ⚠️  Not found: {change['old'][:50]}...")
    
    if changes_made > 0:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"  ✓ Updated {filepath} ({changes_made} changes)")
        return True
    else:
        print(f"  ℹ️  No changes needed in {filepath}")
        return False

def create_rollback_script():
    """Create a script to rollback changes"""
    rollback_content = '''#!/usr/bin/env python3
"""Rollback import cleanup changes"""
import os
import shutil

files_to_restore = [
    "frontend/src/App.tsx",
    "app/application/use_cases/dashboard.py"
]

for filepath in files_to_restore:
    backup_path = f"{filepath}.pre_import_cleanup"
    if os.path.exists(backup_path):
        shutil.copy2(backup_path, filepath)
        print(f"✓ Restored: {filepath}")
    else:
        print(f"❌ No backup found: {backup_path}")
'''
    
    with open("scripts/rollback_import_cleanup.py", 'w') as f:
        f.write(rollback_content)
    os.chmod("scripts/rollback_import_cleanup.py", 0o755)
    print("\n🔄 Rollback script created: scripts/rollback_import_cleanup.py")

def main():
    print("=" * 60)
    print("IMPORT CLEANUP")
    print("=" * 60)
    print()
    
    import sys
    dry_run = "--dry-run" in sys.argv
    
    if dry_run:
        print("🔍 Running in DRY RUN mode\n")
    else:
        print("⚠️  Running in LIVE mode\n")
        response = input("Continue? (yes/no): ")
        if response.lower() != "yes":
            print("Aborted.")
            return
    
    total_files = 0
    files_changed = 0
    
    for file_config in IMPORT_CHANGES:
        filepath = file_config["file"]
        print(f"\n📄 Processing: {filepath}")
        
        if not os.path.exists(filepath):
            print(f"  ❌ File not found")
            continue
        
        total_files += 1
        
        if not dry_run:
            # Backup the file
            backup_file(filepath)
            
            # Apply changes
            if apply_changes(filepath, file_config["changes"]):
                files_changed += 1
        else:
            print(f"  Would apply {len(file_config['changes'])} changes")
    
    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print(f"{'=' * 60}")
    print(f"Total files processed: {total_files}")
    
    if not dry_run:
        print(f"Files changed: {files_changed}")
        create_rollback_script()
    else:
        print("\nTo apply changes, run without --dry-run")

if __name__ == "__main__":
    main()