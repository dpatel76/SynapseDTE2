#!/usr/bin/env python3
"""
Restore script for backup operation performed on 2025-07-06 19:35:03
This script will restore files from their .backup versions.
"""

import json
from pathlib import Path

def restore_files():
    log_file = Path("/Users/dineshpatel/code/projects/SynapseDTE/backup_logs/backup_log_20250706_193503.json")
    
    with open(log_file, 'r') as f:
        log_data = json.load(f)
    
    if log_data.get("dry_run"):
        print("Original backup was a dry run - nothing to restore")
        return
    
    restored = 0
    errors = 0
    
    for category, data in log_data["categories"].items():
        print(f"\nRestoring {category}:")
        for file_info in data["files"]:
            if file_info["status"] == "success":
                backup_path = Path(file_info["backup"])
                original_path = Path(file_info["file"])
                
                if backup_path.exists():
                    try:
                        backup_path.rename(original_path)
                        print(f"  ✓ Restored: {original_path}")
                        restored += 1
                    except Exception as e:
                        print(f"  ❌ Error restoring {original_path}: {e}")
                        errors += 1
                else:
                    print(f"  ⚠️  Backup not found: {backup_path}")
    
    print(f"\nRestored {restored} files with {errors} errors")

if __name__ == "__main__":
    response = input("Are you sure you want to restore the backed up files? (yes/no): ")
    if response.lower() == "yes":
        restore_files()
    else:
        print("Restore cancelled.")
