#!/usr/bin/env python3
"""
Script to rename prior version files with .backup extension
This helps distinguish between clean architecture and legacy versions
"""

import os
import shutil
from pathlib import Path

# Root directory for the app
APP_ROOT = Path("app")

# Files to rename (non-clean versions)
FILES_TO_RENAME = {
    # API endpoints - prior versions that have clean counterparts
    "app/api/v1/endpoints/auth.py": "app/api/v1/endpoints/auth.backup",
    "app/api/v1/endpoints/admin_sla.py": "app/api/v1/endpoints/admin_sla.backup",
    "app/api/v1/endpoints/cycle_reports.py": "app/api/v1/endpoints/cycle_reports.backup",
    "app/api/v1/endpoints/cycles.py": "app/api/v1/endpoints/cycles.backup",
    "app/api/v1/endpoints/dashboards.py": "app/api/v1/endpoints/dashboards.backup",
    "app/api/v1/endpoints/data_sources.py": "app/api/v1/endpoints/data_sources.backup",
    "app/api/v1/endpoints/llm.py": "app/api/v1/endpoints/llm.backup",
    "app/api/v1/endpoints/metrics.py": "app/api/v1/endpoints/metrics.backup",
    "app/api/v1/endpoints/observation_management.py": "app/api/v1/endpoints/observation_management.backup",
    "app/api/v1/endpoints/planning.py": "app/api/v1/endpoints/planning.backup",
    "app/api/v1/endpoints/reports.py": "app/api/v1/endpoints/reports.backup",
    "app/api/v1/endpoints/request_info.py": "app/api/v1/endpoints/request_info.backup",
    "app/api/v1/endpoints/sla.py": "app/api/v1/endpoints/sla.backup",
    "app/api/v1/endpoints/users.py": "app/api/v1/endpoints/users.backup",
    "app/api/v1/endpoints/test_execution.py": "app/api/v1/endpoints/test_execution.backup",
    "app/api/v1/endpoints/data_owner.py": "app/api/v1/endpoints/data_owner.backup",
    
    # Main files
    "app/main.py": "app/main.backup",
    
    # Router files
    "app/api/v1/api.py": "app/api/v1/api.backup",
}

def rename_files():
    """Rename prior version files to .backup extension"""
    renamed_count = 0
    skipped_count = 0
    
    print("Starting to rename prior version files to .backup extension...")
    print("-" * 60)
    
    for old_path, new_path in FILES_TO_RENAME.items():
        old_file = Path(old_path)
        new_file = Path(new_path)
        
        if old_file.exists():
            # Check if backup already exists
            if new_file.exists():
                print(f"⚠️  Backup already exists: {new_path}")
                skipped_count += 1
            else:
                try:
                    shutil.move(str(old_file), str(new_file))
                    print(f"✅ Renamed: {old_path} → {new_path}")
                    renamed_count += 1
                except Exception as e:
                    print(f"❌ Error renaming {old_path}: {e}")
        else:
            print(f"ℹ️  File not found (might already be renamed): {old_path}")
            skipped_count += 1
    
    print("-" * 60)
    print(f"Summary:")
    print(f"  - Files renamed: {renamed_count}")
    print(f"  - Files skipped: {skipped_count}")
    print(f"  - Total processed: {len(FILES_TO_RENAME)}")
    
    # List clean architecture files
    print("\n" + "=" * 60)
    print("Clean architecture files in use:")
    print("=" * 60)
    
    clean_files = [
        "app/main_clean.py",
        "app/api/v1/clean_router.py",
        "app/api/v1/api_clean.py",
        "app/api/v1/endpoints/*_clean.py"
    ]
    
    for pattern in clean_files:
        if "*" in pattern:
            # Handle glob pattern
            base_dir = Path(pattern).parent
            file_pattern = Path(pattern).name
            if base_dir.exists():
                matching_files = list(base_dir.glob(file_pattern))
                for f in sorted(matching_files):
                    print(f"  ✨ {f}")
        else:
            # Handle specific file
            if Path(pattern).exists():
                print(f"  ✨ {pattern}")

if __name__ == "__main__":
    rename_files()