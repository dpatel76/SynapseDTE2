#!/usr/bin/env python3
"""
Fix issues in migrated endpoints
"""

import os
import re
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Files to fix
FILES_TO_FIX = [
    "/Users/dineshpatel/code/SynapseDT/app/api/v1/endpoints/data_owner.py",
    "/Users/dineshpatel/code/SynapseDT/app/api/v1/endpoints/sample_selection.py",
    "/Users/dineshpatel/code/SynapseDT/app/api/v1/endpoints/testing_execution.py",
    "/Users/dineshpatel/code/SynapseDT/app/api/v1/endpoints/observation_management.py",
    "/Users/dineshpatel/code/SynapseDT/app/api/v1/endpoints/lobs.py"
]


def fix_current_user_in_endpoints(content: str) -> str:
    """Fix endpoints that are missing current_user parameter"""
    
    # Pattern to find functions with @require_permission that might be missing current_user
    pattern = r'(@require_permission\([^)]+\)\s*\n\s*async def \w+\([^)]*\)):'
    
    def check_and_fix_function(match):
        func_def = match.group(1)
        # Check if current_user is already in the function
        if "current_user" not in func_def:
            # Add current_user parameter before the closing parenthesis
            if "db: AsyncSession = Depends(get_db)" in func_def:
                # Add after db parameter
                func_def = func_def.replace(
                    "db: AsyncSession = Depends(get_db)",
                    "db: AsyncSession = Depends(get_db),\n    current_user: User = Depends(get_current_user)"
                )
            else:
                # Add before the closing parenthesis
                func_def = func_def[:-1] + ",\n    current_user: User = Depends(get_current_user))"
        return func_def + ":"
    
    return re.sub(pattern, check_and_fix_function, content)


def fix_old_dependency_references(content: str) -> str:
    """Remove any remaining old dependency function calls and definitions"""
    
    # Remove old function definitions more thoroughly
    old_functions = [
        "require_tester", "require_cdo", "require_tester_or_cdo",
        "require_report_owner", "require_tester_or_report_owner",
        "check_tester_role", "check_report_owner_role", "check_test_manager_role",
        "require_tester_access", "require_report_owner_access", "require_test_manager_access"
    ]
    
    for func in old_functions:
        # Pattern to match the entire function definition
        func_pattern = rf'^def {func}\([^)]*\):.*?return \w+\s*$'
        content = re.sub(func_pattern, '', content, flags=re.MULTILINE | re.DOTALL)
    
    return content


def fix_observation_endpoints(content: str) -> str:
    """Fix specific issues in observation_management.py"""
    
    # Fix the issue where current_user is referenced but not in scope
    if "observation_management.py" in content or "started_by=current_user.user_id" in content:
        # Pattern to find functions that use current_user but don't have it as parameter
        pattern = r'(@require_permission\([^)]+\)\s*\n\s*async def \w+\([^)]*\)):(.*?)(?=\n@|\nclass|\ndef|\Z)'
        
        def fix_function(match):
            func_def = match.group(1)
            func_body = match.group(2)
            
            # Check if function body uses current_user but it's not in parameters
            if "current_user" in func_body and "current_user" not in func_def:
                # Add current_user parameter
                if "db: AsyncSession = Depends(get_db)" in func_def:
                    func_def = func_def.replace(
                        "db: AsyncSession = Depends(get_db)",
                        "db: AsyncSession = Depends(get_db),\n    current_user: User = Depends(get_current_user)"
                    )
                else:
                    func_def = func_def[:-1] + ",\n    current_user: User = Depends(get_current_user))"
            
            return func_def + ":" + func_body
        
        content = re.sub(pattern, fix_function, content, flags=re.DOTALL)
    
    return content


def fix_lobs_endpoints(content: str) -> str:
    """Fix specific issues in lobs.py"""
    
    # Fix endpoints that reference current_user but don't have it as parameter
    if "lobs.py" in content:
        # Pattern to find functions that might need current_user
        pattern = r'(@require_permission\([^)]+\)\s*\n\s*async def \w+\([^)]*\)):(.*?)(?=\n@|\nclass|\ndef|\Z)'
        
        def fix_function(match):
            func_def = match.group(1)
            func_body = match.group(2)
            
            # Check if function body uses current_user but it's not in parameters
            if "current_user" in func_body and "current_user" not in func_def:
                # Add current_user parameter
                if "db: AsyncSession = Depends(get_db)" in func_def:
                    func_def = func_def.replace(
                        "db: AsyncSession = Depends(get_db)",
                        "db: AsyncSession = Depends(get_db),\n    current_user: User = Depends(get_current_user)"
                    )
                else:
                    func_def = func_def[:-1] + ",\n    current_user: User = Depends(get_current_user))"
            
            return func_def + ":" + func_body
        
        content = re.sub(pattern, fix_function, content, flags=re.DOTALL)
    
    return content


def clean_up_file(content: str) -> str:
    """General cleanup of the file"""
    
    # Remove multiple blank lines
    content = re.sub(r'\n\n\n+', '\n\n', content)
    
    # Remove trailing whitespace
    content = re.sub(r'[ \t]+$', '', content, flags=re.MULTILINE)
    
    return content


def fix_file(file_path: str) -> bool:
    """Fix issues in a single file"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Apply fixes
        content = fix_current_user_in_endpoints(content)
        content = fix_old_dependency_references(content)
        content = fix_observation_endpoints(content)
        content = fix_lobs_endpoints(content)
        content = clean_up_file(content)
        
        if content != original_content:
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"✓ Fixed {os.path.basename(file_path)}")
        else:
            print(f"✓ No fixes needed for {os.path.basename(file_path)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error fixing {os.path.basename(file_path)}: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function"""
    print("Fixing Migration Issues")
    print("="*60)
    
    success_count = 0
    failed_files = []
    
    for file_path in FILES_TO_FIX:
        if os.path.exists(file_path):
            if fix_file(file_path):
                success_count += 1
            else:
                failed_files.append(file_path)
        else:
            print(f"✗ File not found: {file_path}")
            failed_files.append(file_path)
    
    print(f"\n{'='*60}")
    print("Fix Summary")
    print(f"{'='*60}")
    print(f"Total files: {len(FILES_TO_FIX)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {len(failed_files)}")
    
    if failed_files:
        print("\nFailed files:")
        for file in failed_files:
            print(f"  - {file}")
    
    return len(failed_files) == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)