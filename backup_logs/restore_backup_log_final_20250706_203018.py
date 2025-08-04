#!/usr/bin/env python3
"""
Restore script for backup operation performed on 2025-07-06 20:30:18
This script will restore files from their .backup versions and tables from _backup suffix.
"""

import json
import asyncio
from pathlib import Path
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings

async def restore_files():
    log_file = Path("/Users/dineshpatel/code/projects/SynapseDTE/backup_logs/backup_log_final_20250706_203018.json")
    
    with open(log_file, 'r') as f:
        log_data = json.load(f)
    
    if log_data.get("dry_run"):
        print("Original backup was a dry run - nothing to restore")
        return
    
    restored = 0
    errors = 0
    
    # Restore files
    for category, data in log_data["categories"].items():
        print(f"\nRestoring {category}:")
        for file_info in data["files"]:
            if file_info["status"] == "success":
                backup_path = Path(file_info["backup"])
                original_path = Path(file_info["file"])
                
                if backup_path.exists():
                    try:
                        backup_path.rename(original_path)
                        print(f"  ✓ Restored: {original_path.name}")
                        restored += 1
                    except Exception as e:
                        print(f"  ❌ Error restoring {original_path}: {e}")
                        errors += 1
                else:
                    print(f"  ⚠️  Backup not found: {backup_path}")
    
    # Restore tables
    if "tables" in log_data:
        print("\nRestoring database tables:")
        engine = create_async_engine(settings.DATABASE_URL)
        async with engine.begin() as conn:
            for table_info in log_data["tables"]:
                if table_info["status"] == "success":
                    backup_table = table_info["backup"]
                    original_table = table_info["table"]
                    
                    try:
                        await conn.execute(text(f'ALTER TABLE "{backup_table}" RENAME TO "{original_table}"'))
                        print(f"  ✓ Restored table: {original_table}")
                        restored += 1
                    except Exception as e:
                        print(f"  ❌ Error restoring table {original_table}: {e}")
                        errors += 1
    
    print(f"\nRestored {restored} items with {errors} errors")

if __name__ == "__main__":
    response = input("Are you sure you want to restore the backed up files and tables? (yes/no): ")
    if response.lower() == "yes":
        asyncio.run(restore_files())
    else:
        print("Restore cancelled.")
