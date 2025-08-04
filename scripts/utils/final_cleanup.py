#!/usr/bin/env python3
"""
Final cleanup for migration issues
"""

import os
import re
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Files to clean up
FILES_TO_CLEAN = [
    "/Users/dineshpatel/code/SynapseDT/app/api/v1/endpoints/data_owner.py",
    "/Users/dineshpatel/code/SynapseDT/app/api/v1/endpoints/sample_selection.py",
    "/Users/dineshpatel/code/SynapseDT/app/api/v1/endpoints/testing_execution.py",
    "/Users/dineshpatel/code/SynapseDT/app/api/v1/endpoints/observation_management.py",
    "/Users/dineshpatel/code/SynapseDT/app/api/v1/endpoints/lobs.py"
]


def fix_newline_issues(content: str) -> str:
    """Fix 'No newline at end of file' issues"""
    # Ensure file ends with a newline
    if not content.endswith('\n'):
        content += '\n'
    
    # Remove duplicate "No newline at end of file" messages
    content = re.sub(r'\s*No newline at end of file\s*$', '', content, flags=re.MULTILINE)
    
    return content


def fix_testing_execution_issues(content: str) -> str:
    """Fix specific issues in testing_execution.py"""
    if "testing_execution.py" in content or "check_tester_role" in content:
        # Remove the orphaned check_tester_role, check_report_owner_role, check_test_manager_role calls
        # These are called but never used since we're using @require_permission
        content = re.sub(r'\s+check_tester_role\(current_user\)\s*\n', '', content)
        content = re.sub(r'\s+check_report_owner_role\(current_user\)\s*\n', '', content)
        content = re.sub(r'\s+check_test_manager_role\(current_user\)\s*\n', '', content)
        
        # Remove the helper function definitions if they exist
        content = re.sub(r'def check_tester_role\([^)]*\):[^}]+}\s*', '', content, flags=re.DOTALL)
        content = re.sub(r'def check_report_owner_role\([^)]*\):[^}]+}\s*', '', content, flags=re.DOTALL)
        content = re.sub(r'def check_test_manager_role\([^)]*\):[^}]+}\s*', '', content, flags=re.DOTALL)
    
    return content


def fix_observation_management_issues(content: str) -> str:
    """Fix specific issues in observation_management.py"""
    if "observation_management.py" in content:
        # Add current_user parameter where it's used but missing
        pattern = r'(@require_permission\([^)]+\)\s*\n\s*async def \w+\([^)]*\)):(.*?)(?=\n@|\nclass|\ndef|\Z)'
        
        def fix_function(match):
            func_def = match.group(1)
            func_body = match.group(2)
            
            # Check if function uses current_user but doesn't have it as parameter
            if "current_user" in func_body and "current_user" not in func_def:
                # Add current_user parameter
                if "db: AsyncSession = Depends(get_db)" in func_def:
                    func_def = func_def.replace(
                        "db: AsyncSession = Depends(get_db)",
                        "db: AsyncSession = Depends(get_db),\n    current_user: User = Depends(get_current_user)"
                    )
                else:
                    # Add before the closing parenthesis
                    func_def = func_def[:-1] + ",\n    current_user: User = Depends(get_current_user))"
            
            return func_def + ":" + func_body
        
        content = re.sub(pattern, fix_function, content, flags=re.DOTALL)
    
    return content


def fix_lobs_issues(content: str) -> str:
    """Fix specific issues in lobs.py"""
    if "lobs.py" in content:
        # Add current_user parameter to functions that use it
        funcs_needing_user = ["create_lob", "delete_lob", "get_lob_stats"]
        
        for func_name in funcs_needing_user:
            pattern = rf'(@require_permission\([^)]+\)\s*\n\s*async def {func_name}\([^)]*\)):'
            
            def fix_function(match):
                func_def = match.group(1)
                
                # Check if current_user is already in the function
                if "current_user" not in func_def:
                    # Add current_user parameter
                    if "db: AsyncSession = Depends(get_db)" in func_def:
                        func_def = func_def.replace(
                            "db: AsyncSession = Depends(get_db)",
                            "db: AsyncSession = Depends(get_db),\n    current_user: User = Depends(get_current_user)"
                        )
                    else:
                        # Add before the closing parenthesis
                        func_def = func_def[:-1] + ",\n    current_user: User = Depends(get_current_user))"
                
                return func_def + ":"
            
            content = re.sub(pattern, fix_function, content)
    
    return content


def remove_unused_dependencies(content: str) -> str:
    """Remove unused dependency imports"""
    # If require_management is not used in the file, remove its import
    if "require_management" in content and "Depends(require_management)" not in content:
        content = re.sub(r'from app\.core\.dependencies import[^\n]*require_management[^\n]*\n', '', content)
        # Clean up the import line if it's now empty or just has get_current_user
        content = re.sub(r'from app\.core\.dependencies import\s*,?\s*get_current_user\s*\n', 
                        'from app.core.dependencies import get_current_user\n', content)
    
    return content


def clean_file(file_path: str) -> bool:
    """Clean a single file"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Apply fixes
        content = fix_newline_issues(content)
        content = fix_testing_execution_issues(content)
        content = fix_observation_management_issues(content)
        content = fix_lobs_issues(content)
        content = remove_unused_dependencies(content)
        
        # Clean up multiple blank lines
        content = re.sub(r'\n\n\n+', '\n\n', content)
        
        if content != original_content:
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"✓ Cleaned {os.path.basename(file_path)}")
        else:
            print(f"✓ {os.path.basename(file_path)} already clean")
        
        return True
        
    except Exception as e:
        print(f"✗ Error cleaning {os.path.basename(file_path)}: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function"""
    print("Final Cleanup for Migration")
    print("="*60)
    
    success_count = 0
    failed_files = []
    
    for file_path in FILES_TO_CLEAN:
        if os.path.exists(file_path):
            if clean_file(file_path):
                success_count += 1
            else:
                failed_files.append(file_path)
        else:
            print(f"✗ File not found: {file_path}")
            failed_files.append(file_path)
    
    print(f"\n{'='*60}")
    print("Cleanup Summary")
    print(f"{'='*60}")
    print(f"Total files: {len(FILES_TO_CLEAN)}")
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