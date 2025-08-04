#!/usr/bin/env python3
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
