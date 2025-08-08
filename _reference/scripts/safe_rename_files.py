#!/usr/bin/env python3
"""
Safe file renaming script with rollback capability
"""

import os
import shutil
import json
from datetime import datetime

# Files to rename (from our analysis)
RENAME_OPERATIONS = [
    # Frontend files
    ("frontend/src/components/phase/DynamicActivityCardsEnhanced.tsx", "frontend/src/components/phase/DynamicActivityCards.tsx"),
    ("frontend/src/pages/ReportTestingPageRedesigned.tsx", "frontend/src/pages/ReportTestingPage.tsx"),
    ("frontend/src/pages/dashboards/TestExecutiveDashboardRedesigned.tsx", "frontend/src/pages/dashboards/TestExecutiveDashboard.tsx"),
    ("frontend/src/pages/dashboards/TesterDashboardEnhanced.tsx", "frontend/src/pages/dashboards/TesterDashboard.tsx"),
    ("frontend/src/pages/phases/DataProfilingEnhanced.tsx", "frontend/src/pages/phases/DataProfiling.tsx"),
    ("frontend/src/pages/phases/ObservationManagementEnhanced.tsx", "frontend/src/pages/phases/ObservationManagement.tsx"),
    ("frontend/src/pages/phases/SimplifiedPlanningPage.tsx", "frontend/src/pages/phases/PlanningPage.tsx"),
    
    # Backend files - API endpoints
    ("app/api/v1/endpoints/planning_clean.py", "app/api/v1/endpoints/planning.py"),
    ("app/api/v1/endpoints/scoping_clean.py", "app/api/v1/endpoints/scoping.py"),
    ("app/api/v1/endpoints/data_owner_clean.py", "app/api/v1/endpoints/data_owner.py"),
    ("app/api/v1/endpoints/request_info_clean.py", "app/api/v1/endpoints/request_info.py"),
    ("app/api/v1/endpoints/test_execution_clean.py", "app/api/v1/endpoints/test_execution.py"),
    ("app/api/v1/endpoints/observation_management_clean.py", "app/api/v1/endpoints/observation_management.py"),
    
    # Services
    ("app/services/activity_state_manager_v2.py", "app/services/activity_state_manager_enhanced.py"),  # Don't overwrite existing
]

# Import updates needed after renaming
IMPORT_UPDATES = [
    # Frontend imports
    ("DynamicActivityCardsEnhanced", "DynamicActivityCards"),
    ("ReportTestingPageRedesigned", "ReportTestingPage"),
    ("TestExecutiveDashboardRedesigned", "TestExecutiveDashboard"),
    ("TesterDashboardEnhanced", "TesterDashboard"),
    ("DataProfilingEnhanced", "DataProfiling"),
    ("ObservationManagementEnhanced", "ObservationManagement"),
    ("SimplifiedPlanningPage", "PlanningPage"),
    
    # Backend imports
    ("planning_clean", "planning"),
    ("scoping_clean", "scoping"),
    ("data_owner_clean", "data_owner"),
    ("request_info_clean", "request_info"),
    ("test_execution_clean", "test_execution"),
    ("observation_management_clean", "observation_management"),
    ("activity_state_manager_v2", "activity_state_manager_enhanced"),
]

def create_backup():
    """Create a backup of files before renaming"""
    backup_dir = f"backup_logs/rename_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)
    
    backup_log = {
        "timestamp": datetime.now().isoformat(),
        "operations": []
    }
    
    for old_path, new_path in RENAME_OPERATIONS:
        if os.path.exists(old_path):
            backup_path = os.path.join(backup_dir, old_path)
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            shutil.copy2(old_path, backup_path)
            backup_log["operations"].append({
                "original": old_path,
                "backup": backup_path,
                "target": new_path
            })
    
    # Save backup log
    with open(os.path.join(backup_dir, "backup_log.json"), "w") as f:
        json.dump(backup_log, f, indent=2)
    
    return backup_dir

def perform_renames(dry_run=True):
    """Perform the file renames"""
    results = []
    
    for old_path, new_path in RENAME_OPERATIONS:
        if os.path.exists(old_path):
            if os.path.exists(new_path):
                # Check if it's a backup file
                if new_path.endswith('.backup'):
                    results.append({
                        "old": old_path,
                        "new": new_path,
                        "status": "skipped",
                        "reason": "Target is a backup file"
                    })
                else:
                    results.append({
                        "old": old_path,
                        "new": new_path,
                        "status": "conflict",
                        "reason": "Target already exists"
                    })
            else:
                if not dry_run:
                    os.rename(old_path, new_path)
                results.append({
                    "old": old_path,
                    "new": new_path,
                    "status": "success" if not dry_run else "would_rename"
                })
        else:
            results.append({
                "old": old_path,
                "new": new_path,
                "status": "not_found"
            })
    
    return results

def update_imports(dry_run=True):
    """Update imports in all files"""
    updated_files = []
    
    for root, dirs, files in os.walk('.'):
        # Skip certain directories
        if any(skip in root for skip in ['.git', 'node_modules', 'venv', '__pycache__', 'backup']):
            continue
            
        for file in files:
            if file.endswith(('.py', '.ts', '.tsx', '.js', '.jsx')):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r') as f:
                        content = f.read()
                    
                    original_content = content
                    
                    # Apply all replacements
                    for old_import, new_import in IMPORT_UPDATES:
                        # Handle different import patterns
                        patterns = [
                            (f"from '{old_import}'", f"from '{new_import}'"),
                            (f'from "{old_import}"', f'from "{new_import}"'),
                            (f"import {old_import}", f"import {new_import}"),
                            (f"from .{old_import}", f"from .{new_import}"),
                            (f"from ..{old_import}", f"from ..{new_import}"),
                            (f"/{old_import}'", f"/{new_import}'"),
                            (f'/{old_import}"', f'/{new_import}"'),
                        ]
                        
                        for old_pattern, new_pattern in patterns:
                            content = content.replace(old_pattern, new_pattern)
                    
                    if content != original_content:
                        if not dry_run:
                            with open(filepath, 'w') as f:
                                f.write(content)
                        updated_files.append(filepath)
                        
                except Exception as e:
                    print(f"Error processing {filepath}: {e}")
    
    return updated_files

def main():
    import sys
    
    dry_run = "--dry-run" in sys.argv
    
    print("FILE RENAMING SCRIPT")
    print("=" * 60)
    print(f"Mode: {'LIVE' if not dry_run else 'DRY RUN'}")
    print()
    
    if not dry_run:
        response = input("This will rename files. Continue? (yes/no): ")
        if response.lower() != "yes":
            print("Aborted.")
            return
        
        # Create backup
        print("\nCreating backup...")
        backup_dir = create_backup()
        print(f"✓ Backup created: {backup_dir}")
    
    # Perform renames
    print("\nRenaming files...")
    results = perform_renames(dry_run)
    
    for result in results:
        status_icon = {
            "success": "✓",
            "would_rename": "→",
            "conflict": "⚠️",
            "not_found": "❌",
            "skipped": "⏭️"
        }.get(result["status"], "?")
        
        print(f"{status_icon} {result['old']} → {result['new']}")
        if "reason" in result:
            print(f"   {result['reason']}")
    
    # Update imports
    print("\nUpdating imports...")
    updated_files = update_imports(dry_run)
    
    print(f"\n{len(updated_files)} files {'would be' if dry_run else 'were'} updated:")
    for file in updated_files[:10]:  # Show first 10
        print(f"  ✓ {file}")
    if len(updated_files) > 10:
        print(f"  ... and {len(updated_files) - 10} more")
    
    # Summary
    success_count = len([r for r in results if r["status"] in ["success", "would_rename"]])
    conflict_count = len([r for r in results if r["status"] == "conflict"])
    not_found_count = len([r for r in results if r["status"] == "not_found"])
    
    print(f"\nSummary:")
    print(f"  Renamed: {success_count}")
    print(f"  Conflicts: {conflict_count}")
    print(f"  Not found: {not_found_count}")
    
    if dry_run:
        print("\nThis was a dry run. To perform actual renaming, run without --dry-run")

if __name__ == "__main__":
    main()