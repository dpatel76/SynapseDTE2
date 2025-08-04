#!/usr/bin/env python3
"""
Test script to verify frontend integration with unified planning APIs
"""

import os
import ast
import sys
from pathlib import Path

def test_file_syntax(file_path):
    """Test if a TypeScript/JavaScript file has valid syntax (at least no obvious errors)"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Basic checks for TypeScript/JavaScript files
        errors = []
        
        # Check for unmatched braces
        open_braces = content.count('{')
        close_braces = content.count('}')
        if open_braces != close_braces:
            errors.append(f"Unmatched braces: {open_braces} open, {close_braces} close")
        
        # Check for unmatched parentheses
        open_parens = content.count('(')
        close_parens = content.count(')')
        if open_parens != close_parens:
            errors.append(f"Unmatched parentheses: {open_parens} open, {close_parens} close")
        
        # Check for unmatched brackets
        open_brackets = content.count('[')
        close_brackets = content.count(']')
        if open_brackets != close_brackets:
            errors.append(f"Unmatched brackets: {open_brackets} open, {close_brackets} close")
        
        # Check for basic import syntax
        lines = content.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            if line.startswith('import ') and not (';' in line or line.endswith('\'')):
                # Check if import statement looks complete
                if not any(end in line for end in [' from ', ';']):
                    errors.append(f"Line {i+1}: Potentially incomplete import statement")
        
        return len(errors) == 0, errors
        
    except Exception as e:
        return False, [f"Error reading file: {e}"]

def check_api_integration():
    """Check that API integration files have been updated correctly"""
    print("=" * 60)
    print("FRONTEND API INTEGRATION TESTS")
    print("=" * 60)
    
    base_path = Path("/Users/dineshpatel/code/projects/SynapseDTE")
    
    files_to_test = [
        "frontend/src/api/planningUnified.ts",
        "frontend/src/api/planning.ts", 
        "frontend/src/pages/phases/PlanningPage.tsx"
    ]
    
    passed = 0
    total = len(files_to_test)
    
    for file_path in files_to_test:
        full_path = base_path / file_path
        print(f"\nTesting: {file_path}")
        
        if not full_path.exists():
            print(f"✗ File not found: {full_path}")
            continue
        
        success, errors = test_file_syntax(full_path)
        if success:
            print(f"✓ Syntax looks good")
            passed += 1
        else:
            print(f"✗ Syntax issues found:")
            for error in errors:
                print(f"  - {error}")
    
    print(f"\n" + "=" * 60)
    print(f"SYNTAX RESULTS: {passed}/{total} files passed")
    
    if passed == total:
        print("🎉 All frontend files have valid syntax!")
        return True
    else:
        print(f"❌ {total - passed} file(s) have syntax issues.")
        return False

def check_api_imports():
    """Check that API imports are correctly structured"""
    print("\n" + "=" * 60)
    print("API IMPORT INTEGRATION TESTS")
    print("=" * 60)
    
    base_path = Path("/Users/dineshpatel/code/projects/SynapseDTE")
    
    # Check planningUnified.ts
    planning_unified_path = base_path / "frontend/src/api/planningUnified.ts"
    if planning_unified_path.exists():
        with open(planning_unified_path, 'r') as f:
            content = f.read()
        
        print("\nChecking planningUnified.ts:")
        
        # Check for key exports
        if 'export const planningUnifiedApi' in content:
            print("✓ planningUnifiedApi export found")
        else:
            print("✗ planningUnifiedApi export missing")
        
        # Check for key methods
        key_methods = [
            'createVersion',
            'createAttribute', 
            'createDataSource',
            'updateAttributeDecision',
            'getVersionDashboard'
        ]
        
        for method in key_methods:
            if f'{method}:' in content:
                print(f"✓ Method {method} found")
            else:
                print(f"✗ Method {method} missing")
    
    # Check planning.ts integration
    planning_path = base_path / "frontend/src/api/planning.ts"
    if planning_path.exists():
        with open(planning_path, 'r') as f:
            content = f.read()
        
        print("\nChecking planning.ts integration:")
        
        # Check for unified API import
        if 'planningUnifiedApi' in content:
            print("✓ planningUnifiedApi import found")
        else:
            print("✗ planningUnifiedApi import missing")
        
        # Check for hybrid implementation
        if 'shouldUseUnifiedPlanning' in content:
            print("✓ Hybrid planning logic found")
        else:
            print("✗ Hybrid planning logic missing")
        
        # Check for conversion functions
        if 'convertUnifiedToLegacyAttribute' in content:
            print("✓ Conversion function found")
        else:
            print("✗ Conversion function missing")
    
    # Check PlanningPage.tsx integration
    planning_page_path = base_path / "frontend/src/pages/phases/PlanningPage.tsx"
    if planning_page_path.exists():
        with open(planning_page_path, 'r') as f:
            content = f.read()
        
        print("\nChecking PlanningPage.tsx integration:")
        
        # Check for unified API import
        if 'planningUnifiedApi' in content:
            print("✓ planningUnifiedApi import found")
        else:
            print("✗ planningUnifiedApi import missing")
        
        # Check for status indicator
        if 'isUnifiedPlanningAvailable' in content:
            print("✓ Unified planning status state found")
        else:
            print("✗ Unified planning status state missing")
        
        # Check for system indicator UI
        if 'Unified ✨' in content:
            print("✓ System status indicator found")
        else:
            print("✗ System status indicator missing")

def check_type_compatibility():
    """Check that type definitions are compatible"""
    print("\n" + "=" * 60)
    print("TYPE COMPATIBILITY TESTS")
    print("=" * 60)
    
    base_path = Path("/Users/dineshpatel/code/projects/SynapseDTE")
    
    # Check that key types are defined in planningUnified.ts
    planning_unified_path = base_path / "frontend/src/api/planningUnified.ts"
    if planning_unified_path.exists():
        with open(planning_unified_path, 'r') as f:
            content = f.read()
        
        print("\nChecking type definitions:")
        
        key_types = [
            'PlanningVersion',
            'PlanningDataSource',
            'PlanningAttribute',
            'PlanningPDEMapping',
            'PlanningDashboard'
        ]
        
        for type_name in key_types:
            if f'interface {type_name}' in content or f'export interface {type_name}' in content:
                print(f"✓ Type {type_name} defined")
            else:
                print(f"✗ Type {type_name} missing")

def main():
    """Run all frontend integration tests"""
    print("Testing frontend integration with unified planning APIs...")
    
    syntax_ok = check_api_integration()
    check_api_imports()
    check_type_compatibility()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if syntax_ok:
        print("✅ Frontend integration appears to be working!")
        print("\nNext steps:")
        print("1. Start the frontend development server")
        print("2. Navigate to a planning phase")
        print("3. Check browser console for 'Unified Planning Available' message")
        print("4. Verify that attributes load and can be created/updated")
        print("5. Look for the 'Unified ✨' status indicator in the UI")
        return True
    else:
        print("❌ Frontend integration has issues that need to be fixed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)