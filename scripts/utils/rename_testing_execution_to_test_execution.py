#!/usr/bin/env python3
"""
Script to rename testing_execution to test_execution throughout the codebase.
This script:
1. Creates backup copies of all affected files
2. Renames files from testing_execution to test_execution
3. Updates all imports and references in the codebase
"""

import os
import shutil
import re
from pathlib import Path
import argparse

# Define files to rename
FILES_TO_RENAME = {
    # Backend files
    "app/api/v1/endpoints/testing_execution.py": "app/api/v1/endpoints/test_execution.py",
    "app/api/v1/endpoints/testing_execution_clean.py": "app/api/v1/endpoints/test_execution_clean.py",
    "app/api/v1/endpoints/testing_execution_refactored.py": "app/api/v1/endpoints/test_execution_refactored.py",
    "app/models/testing_execution.py": "app/models/test_execution.py",
    "app/schemas/testing_execution.py": "app/schemas/test_execution.py",
    "app/application/use_cases/testing_execution.py": "app/application/use_cases/test_execution.py",
    
    # Frontend files
    "frontend/src/pages/phases/TestingExecutionPage.tsx": "frontend/src/pages/phases/TestExecutionPage.tsx",
}

# Define patterns to replace in file contents
CONTENT_REPLACEMENTS = [
    # Python imports and references
    (r'from app\.api\.v1\.endpoints import testing_execution', 'from app.api.v1.endpoints import test_execution'),
    (r'from app\.models\.testing_execution', 'from app.models.test_execution'),
    (r'from app\.schemas\.testing_execution', 'from app.schemas.test_execution'),
    (r'from app\.application\.use_cases\.testing_execution', 'from app.application.use_cases.test_execution'),
    (r'import testing_execution', 'import test_execution'),
    (r'testing_execution\.router', 'test_execution.router'),
    (r'testing_execution\.', 'test_execution.'),
    (r'"testing-execution"', '"test-execution"'),
    (r"'testing-execution'", "'test-execution'"),
    (r'Testing Execution', 'Test Execution'),
    (r'testing_execution', 'test_execution'),  # General replacement
    
    # TypeScript/React imports and references
    (r'TestingExecutionPage', 'TestExecutionPage'),
    (r'TestingExecution', 'TestExecution'),
    (r'/testing-execution', '/test-execution'),
    (r'"Testing Execution"', '"Test Execution"'),
    (r"'Testing Execution'", "'Test Execution'"),
]

def create_backup(file_path):
    """Create a backup copy of a file."""
    backup_path = f"{file_path}.backup"
    if os.path.exists(file_path):
        shutil.copy2(file_path, backup_path)
        print(f"Created backup: {backup_path}")
        return True
    else:
        print(f"Warning: File not found: {file_path}")
        return False

def rename_file(old_path, new_path):
    """Rename a file from old_path to new_path."""
    if os.path.exists(old_path):
        os.makedirs(os.path.dirname(new_path), exist_ok=True)
        shutil.move(old_path, new_path)
        print(f"Renamed: {old_path} -> {new_path}")
        return True
    else:
        print(f"Warning: Cannot rename, file not found: {old_path}")
        return False

def update_file_contents(file_path, replacements):
    """Update the contents of a file with the given replacements."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        for pattern, replacement in replacements:
            content = re.sub(pattern, replacement, content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated contents: {file_path}")
            return True
        return False
    except Exception as e:
        print(f"Error updating {file_path}: {e}")
        return False

def find_files_to_update(root_dirs, extensions):
    """Find all files that might need content updates."""
    files = []
    for root_dir in root_dirs:
        for ext in extensions:
            files.extend(Path(root_dir).rglob(f"*{ext}"))
    return files

def main(dry_run=False):
    """Main function to perform the renaming."""
    print("Starting testing_execution -> test_execution rename process...")
    
    if dry_run:
        print("\n*** DRY RUN MODE - No changes will be made ***\n")
    
    # Step 1: Create backups of files to be renamed
    print("\nStep 1: Creating backups...")
    if not dry_run:
        for old_path in FILES_TO_RENAME.keys():
            create_backup(old_path)
    else:
        for old_path in FILES_TO_RENAME.keys():
            print(f"Would backup: {old_path}")
    
    # Step 2: Find all files that need content updates
    print("\nStep 2: Finding files to update...")
    backend_files = find_files_to_update(['app'], ['.py'])
    frontend_files = find_files_to_update(['frontend/src'], ['.ts', '.tsx', '.js', '.jsx'])
    all_files = list(backend_files) + list(frontend_files)
    
    # Step 3: Update file contents
    print(f"\nStep 3: Updating contents in {len(all_files)} files...")
    updated_count = 0
    if not dry_run:
        for file_path in all_files:
            if update_file_contents(str(file_path), CONTENT_REPLACEMENTS):
                updated_count += 1
    else:
        # In dry run, check which files would be updated
        for file_path in all_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                for pattern, _ in CONTENT_REPLACEMENTS:
                    if re.search(pattern, content):
                        print(f"Would update: {file_path}")
                        updated_count += 1
                        break
            except Exception as e:
                print(f"Error checking {file_path}: {e}")
    
    print(f"Updated {updated_count} files")
    
    # Step 4: Rename files
    print("\nStep 4: Renaming files...")
    if not dry_run:
        for old_path, new_path in FILES_TO_RENAME.items():
            rename_file(old_path, new_path)
    else:
        for old_path, new_path in FILES_TO_RENAME.items():
            print(f"Would rename: {old_path} -> {new_path}")
    
    # Step 5: Clean up __pycache__ directories
    print("\nStep 5: Cleaning up __pycache__ directories...")
    if not dry_run:
        for root, dirs, files in os.walk('app'):
            if '__pycache__' in dirs:
                pycache_dir = os.path.join(root, '__pycache__')
                shutil.rmtree(pycache_dir)
                print(f"Removed: {pycache_dir}")
    else:
        print("Would remove all __pycache__ directories")
    
    print("\nRename process completed!")
    
    if not dry_run:
        print("\nIMPORTANT: Please run the following commands:")
        print("1. cd frontend && npm install")
        print("2. alembic upgrade head")
        print("3. Restart both backend and frontend servers")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rename testing_execution to test_execution")
    parser.add_argument('--dry-run', action='store_true', help="Show what would be changed without making changes")
    args = parser.parse_args()
    
    main(dry_run=args.dry_run)