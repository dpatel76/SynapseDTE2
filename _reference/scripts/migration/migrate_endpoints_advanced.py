#!/usr/bin/env python3
"""
Advanced migration script for endpoints to @require_permission decorators
"""

import os
import re
import sys
from typing import List, Tuple, Dict

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Files to migrate with their specific configurations
FILE_CONFIGS = {
    "data_owner.py": {
        "resource": "data_owner",
        "dependencies": {
            "require_tester": "execute",
            "require_cdo": "assign",
            "require_tester_or_cdo": "read"
        },
        "endpoint_mappings": {
            "start_data_owner_phase": ("data_owner", "execute"),
            "get_data_owner_phase_status": ("data_owner", "read"),
            "submit_lob_assignments": ("data_owner", "execute"),
            "get_historical_assignments": ("data_owner", "read"),
            "submit_cdo_assignments": ("data_owner", "assign"),
            "get_assignment_matrix": ("data_owner", "read"),
            "get_sla_violations": ("data_owner", "read"),
            "send_escalation_email": ("data_owner", "escalate"),
            "complete_data_owner_phase": ("data_owner", "complete"),
            "get_data_owner_audit_log": ("data_owner", "read")
        }
    },
    "sample_selection.py": {
        "resource": "sample_selection",
        "dependencies": {
            "require_tester": "execute",
            "require_report_owner": "approve",
            "require_tester_or_report_owner": "read"
        },
        "endpoint_mappings": {
            "start_sample_selection_phase": ("sample_selection", "execute"),
            "generate_llm_samples": ("sample_selection", "generate"),
            "upload_manual_samples": ("sample_selection", "upload"),
            "validate_sample_set": ("sample_selection", "execute"),
            "approve_sample_set": ("sample_selection", "approve"),
            "get_sample_selection_status": ("sample_selection", "read"),
            "get_sample_sets": ("sample_selection", "read"),
            "complete_sample_selection_phase": ("sample_selection", "complete"),
            "get_sample_analytics": ("sample_selection", "read")
        }
    },
    "testing_execution.py": {
        "resource": "testing",
        "dependencies": {
            "check_tester_role": "execute",
            "check_report_owner_role": "review",
            "check_test_manager_role": "approve"
        },
        "endpoint_mappings": {
            "start_testing_execution_phase": ("testing", "execute"),
            "get_testing_execution_status": ("testing", "read"),
            "analyze_document": ("testing", "execute"),
            "test_database": ("testing", "execute"),
            "execute_test": ("testing", "execute"),
            "bulk_execute_tests": ("testing", "execute"),
            "review_test_result": ("testing", "review"),
            "compare_test_results": ("testing", "execute"),
            "get_testing_analytics": ("testing", "read"),
            "complete_testing_execution_phase": ("testing", "approve"),
            "get_testing_execution_audit_logs": ("testing", "read")
        }
    },
    "observation_management.py": {
        "resource": "observations",
        "dependencies": {
            "require_tester_access": "create",
            "require_report_owner_access": "approve",
            "require_test_manager_access": "override"
        },
        "endpoint_mappings": {
            "start_observation_management_phase": ("observations", "create"),
            "get_observation_management_status": ("observations", "read"),
            "auto_detect_observations": ("observations", "create"),
            "create_observation": ("observations", "create"),
            "get_observations": ("observations", "read"),
            "approve_observation": ("observations", "approve", "observation_id"),
            "get_observation_analytics": ("observations", "read"),
            "complete_observation_management_phase": ("observations", "override"),
            "get_observation_audit_logs": ("observations", "read")
        }
    },
    "lobs.py": {
        "resource": "lobs",
        "dependencies": {
            "require_management": "manage"
        },
        "endpoint_mappings": {
            "create_lob": ("lobs", "create"),
            "get_lobs": ("lobs", "read"),
            "get_active_lobs": ("lobs", "read"),
            "get_lob": ("lobs", "read"),
            "update_lob": ("lobs", "update", "lob_id"),
            "delete_lob": ("lobs", "delete", "lob_id"),
            "get_lob_stats": ("lobs", "read")
        }
    }
}


def migrate_endpoints(file_path: str, config: Dict) -> bool:
    """Migrate endpoints in a file based on configuration"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check if already migrated
        if "@require_permission" in content and not any(f"Depends({dep})" in content for dep in config["dependencies"]):
            print(f"✓ {os.path.basename(file_path)} already migrated")
            return True
        
        new_content = content
        changes_made = False
        
        # Add import if not present
        if "from app.core.permissions import require_permission" not in new_content:
            # Find the imports section
            import_match = re.search(r'(from app\.core\.dependencies import[^\n]+)', new_content)
            if import_match:
                import_line = import_match.group(1)
                if "require_permission" not in new_content:
                    new_import = import_line + "\nfrom app.core.permissions import require_permission"
                    new_content = new_content.replace(import_line, new_import)
                    changes_made = True
        
        # Process each endpoint
        for func_name, permission_info in config["endpoint_mappings"].items():
            resource = permission_info[0]
            action = permission_info[1]
            resource_id_param = permission_info[2] if len(permission_info) > 2 else None
            
            # Find the function definition
            func_pattern = rf'(@router\.\w+\([^)]+\)\s*\n)(\s*async def {func_name}\()'
            matches = list(re.finditer(func_pattern, new_content))
            
            for match in matches:
                # Check if already has @require_permission
                func_start = match.start()
                # Look backwards for existing @require_permission
                before_func = new_content[:func_start]
                last_newline = before_func.rfind('\n')
                if last_newline != -1:
                    line_before = new_content[last_newline:func_start]
                    if "@require_permission" in line_before:
                        continue
                
                # Build the decorator
                if resource_id_param:
                    decorator = f'@require_permission("{resource}", "{action}", resource_id_param="{resource_id_param}")\n'
                else:
                    decorator = f'@require_permission("{resource}", "{action}")\n'
                
                # Insert the decorator
                replacement = match.group(1) + decorator + match.group(2)
                new_content = new_content[:match.start()] + replacement + new_content[match.end():]
                changes_made = True
                print(f"  ✓ Added @require_permission to {func_name}")
        
        # Remove old dependencies from function signatures
        for dep_name in config["dependencies"]:
            # Pattern to match dependency parameters
            patterns = [
                rf',\s*_:\s*\w+\s*=\s*Depends\({dep_name}\)',
                rf',\s*\w+:\s*\w+\s*=\s*Depends\({dep_name}\)',
                rf'\s*_:\s*\w+\s*=\s*Depends\({dep_name}\)\s*,',
                rf'\s*\w+:\s*\w+\s*=\s*Depends\({dep_name}\)\s*,'
            ]
            
            for pattern in patterns:
                if re.search(pattern, new_content):
                    new_content = re.sub(pattern, '', new_content)
                    changes_made = True
                    print(f"  ✓ Removed {dep_name} dependency")
        
        # Remove old dependency functions if no longer used
        for dep_name in config["dependencies"]:
            if f"Depends({dep_name})" not in new_content:
                # Pattern to match the function definition
                func_def_pattern = rf'def {dep_name}\([^)]*\):[^{{]*{{[^}}]*}}\s*return[^\n]+\n+'
                if re.search(func_def_pattern, new_content, re.DOTALL):
                    new_content = re.sub(func_def_pattern, '', new_content, flags=re.DOTALL)
                    changes_made = True
                    print(f"  ✓ Removed {dep_name} function")
        
        # Clean up extra blank lines
        new_content = re.sub(r'\n\n\n+', '\n\n', new_content)
        
        if changes_made:
            with open(file_path, 'w') as f:
                f.write(new_content)
            print(f"✓ {os.path.basename(file_path)} migration complete")
        else:
            print(f"✓ {os.path.basename(file_path)} no changes needed")
        
        return True
        
    except Exception as e:
        print(f"✗ Error migrating {os.path.basename(file_path)}: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main migration function"""
    print("Advanced Endpoint Migration to @require_permission")
    print("="*60)
    
    base_path = "/Users/dineshpatel/code/SynapseDT/app/api/v1/endpoints/"
    
    success_count = 0
    failed_files = []
    
    for filename, config in FILE_CONFIGS.items():
        file_path = os.path.join(base_path, filename)
        print(f"\nMigrating {filename}...")
        
        if os.path.exists(file_path):
            if migrate_endpoints(file_path, config):
                success_count += 1
            else:
                failed_files.append(filename)
        else:
            print(f"✗ File not found: {file_path}")
            failed_files.append(filename)
    
    print(f"\n{'='*60}")
    print("Migration Summary")
    print(f"{'='*60}")
    print(f"Total files: {len(FILE_CONFIGS)}")
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