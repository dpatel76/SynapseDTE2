#!/usr/bin/env python3
"""
Syntax validation test for unified planning system
Tests that all files have valid Python syntax
"""

import ast
import sys
import os

def test_file_syntax(file_path):
    """Test if a Python file has valid syntax"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Parse the file to check syntax
        ast.parse(content)
        return True, None
    except SyntaxError as e:
        return False, f"Syntax error: {e}"
    except Exception as e:
        return False, f"Error reading file: {e}"

def main():
    """Test syntax of all planning-related files"""
    print("=" * 60)
    print("UNIFIED PLANNING SYSTEM SYNTAX TESTS")
    print("=" * 60)
    
    base_path = "/Users/dineshpatel/code/projects/SynapseDTE"
    
    files_to_test = [
        "app/models/planning.py",
        "app/schemas/planning_unified.py",
        "app/services/planning_service_unified.py",
        "app/api/v1/endpoints/planning_unified.py"
    ]
    
    passed = 0
    total = len(files_to_test)
    
    for file_path in files_to_test:
        full_path = os.path.join(base_path, file_path)
        print(f"Testing syntax: {file_path}")
        
        if not os.path.exists(full_path):
            print(f"✗ File not found: {full_path}")
            continue
        
        success, error = test_file_syntax(full_path)
        if success:
            print(f"✓ Syntax valid")
            passed += 1
        else:
            print(f"✗ {error}")
        print()
    
    # Test migration files
    migration_files = [
        "alembic/versions/2025_07_18_implement_planning_phase_architecture.py",
        "alembic/versions/2025_07_18_drop_legacy_planning_tables.py"
    ]
    
    print("Testing migration file syntax:")
    for file_path in migration_files:
        full_path = os.path.join(base_path, file_path)
        print(f"Testing migration: {file_path}")
        
        if not os.path.exists(full_path):
            print(f"✗ Migration file not found: {full_path}")
            continue
        
        success, error = test_file_syntax(full_path)
        if success:
            print(f"✓ Migration syntax valid")
            passed += 1
            total += 1
        else:
            print(f"✗ Migration syntax error: {error}")
            total += 1
        print()
    
    print("=" * 60)
    print(f"SYNTAX RESULTS: {passed}/{total} files passed")
    
    if passed == total:
        print("🎉 All files have valid syntax!")
        return True
    else:
        print(f"❌ {total - passed} file(s) have syntax errors.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)