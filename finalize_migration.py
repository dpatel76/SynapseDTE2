#!/usr/bin/env python3
"""
Script to finalize the migration refactoring by replacing the original file.
"""

import shutil
import sys
from pathlib import Path


def finalize_migration(original_file: str, refactored_file: str):
    """Replace the original migration file with the refactored version."""
    
    original_path = Path(original_file)
    refactored_path = Path(refactored_file)
    
    if not original_path.exists():
        print(f"❌ Original file not found: {original_file}")
        return False
    
    if not refactored_path.exists():
        print(f"❌ Refactored file not found: {refactored_file}")
        return False
    
    # Create a backup of the original
    backup_path = original_path.with_suffix('.py.backup')
    print(f"📁 Creating backup: {backup_path}")
    shutil.copy2(original_path, backup_path)
    
    # Replace the original with the refactored version
    print(f"🔄 Replacing original file with refactored version...")
    shutil.copy2(refactored_path, original_path)
    
    print("✅ Migration file successfully updated!")
    print(f"📁 Original backed up to: {backup_path}")
    print(f"🚀 Ready to run: alembic upgrade head")
    
    return True


def main():
    if len(sys.argv) < 3:
        print("Usage: python finalize_migration.py <original_file> <refactored_file>")
        print("\nExample:")
        print("python finalize_migration.py \\")
        print("  alembic/versions/2025_08_04_1041-9b46a58d423b_initial_migration_from_all_models.py \\")
        print("  alembic/versions/2025_08_04_1041-9b46a58d423b_initial_migration_from_all_models_final.py")
        sys.exit(1)
    
    original_file = sys.argv[1]
    refactored_file = sys.argv[2]
    
    success = finalize_migration(original_file, refactored_file)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()