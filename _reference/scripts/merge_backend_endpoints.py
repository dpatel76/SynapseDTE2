#!/usr/bin/env python3
"""
Merge backend endpoint files - keep clean versions and merge unique endpoints
"""

import os
import re
import shutil
from datetime import datetime
import ast

def extract_endpoints(filepath):
    """Extract endpoint definitions from a file"""
    endpoints = []
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Find all route decorators
        pattern = r'@router\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']'
        matches = re.findall(pattern, content)
        
        for method, path in matches:
            endpoints.append({
                'method': method.upper(),
                'path': path,
                'signature': f"{method.upper()} {path}"
            })
    except Exception as e:
        print(f"Error extracting from {filepath}: {e}")
    
    return endpoints

def compare_files(clean_file, regular_file):
    """Compare endpoints between clean and regular versions"""
    clean_endpoints = extract_endpoints(clean_file)
    regular_endpoints = extract_endpoints(regular_file)
    
    clean_sigs = {ep['signature'] for ep in clean_endpoints}
    regular_sigs = {ep['signature'] for ep in regular_endpoints}
    
    unique_to_clean = clean_sigs - regular_sigs
    unique_to_regular = regular_sigs - clean_sigs
    common = clean_sigs & regular_sigs
    
    return {
        'clean_count': len(clean_endpoints),
        'regular_count': len(regular_endpoints),
        'unique_to_clean': unique_to_clean,
        'unique_to_regular': unique_to_regular,
        'common': common
    }

def backup_files():
    """Create backup of all files before merging"""
    backup_dir = f"backup_logs/backend_merge_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)
    
    files_to_backup = [
        # Clean versions
        "app/api/v1/endpoints/planning_clean.py",
        "app/api/v1/endpoints/scoping_clean.py",
        "app/api/v1/endpoints/data_owner_clean.py",
        "app/api/v1/endpoints/request_info_clean.py",
        "app/api/v1/endpoints/test_execution_clean.py",
        "app/api/v1/endpoints/observation_management_clean.py",
        # Regular versions
        "app/api/v1/endpoints/planning.py",
        "app/api/v1/endpoints/scoping.py",
        "app/api/v1/endpoints/data_owner.py",
        "app/api/v1/endpoints/request_info.py",
        "app/api/v1/endpoints/test_execution.py",
        "app/api/v1/endpoints/observation_management.py",
        # API router
        "app/api/v1/api.py"
    ]
    
    for filepath in files_to_backup:
        if os.path.exists(filepath):
            backup_path = os.path.join(backup_dir, filepath)
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            shutil.copy2(filepath, backup_path)
    
    return backup_dir

def analyze_conflicts():
    """Analyze all conflicting endpoint files"""
    conflicts = [
        ("planning_clean.py", "planning.py"),
        ("scoping_clean.py", "scoping.py"),
        ("data_owner_clean.py", "data_owner.py"),
        ("request_info_clean.py", "request_info.py"),
        ("test_execution_clean.py", "test_execution.py"),
        ("observation_management_clean.py", "observation_management.py"),
    ]
    
    base_path = "app/api/v1/endpoints"
    
    print("ENDPOINT ANALYSIS")
    print("=" * 80)
    
    merge_plan = []
    
    for clean_name, regular_name in conflicts:
        clean_path = os.path.join(base_path, clean_name)
        regular_path = os.path.join(base_path, regular_name)
        
        if os.path.exists(clean_path) and os.path.exists(regular_path):
            comparison = compare_files(clean_path, regular_path)
            
            print(f"\n{clean_name} vs {regular_name}:")
            print(f"  Clean version: {comparison['clean_count']} endpoints")
            print(f"  Regular version: {comparison['regular_count']} endpoints")
            print(f"  Common endpoints: {len(comparison['common'])}")
            print(f"  Unique to clean: {len(comparison['unique_to_clean'])}")
            print(f"  Unique to regular: {len(comparison['unique_to_regular'])}")
            
            if comparison['unique_to_regular']:
                print("  ⚠️  Regular version has unique endpoints:")
                for ep in sorted(comparison['unique_to_regular']):
                    print(f"     - {ep}")
                merge_plan.append({
                    'clean': clean_path,
                    'regular': regular_path,
                    'action': 'merge',
                    'unique_endpoints': list(comparison['unique_to_regular'])
                })
            else:
                print("  ✅ Clean version has all endpoints")
                merge_plan.append({
                    'clean': clean_path,
                    'regular': regular_path,
                    'action': 'replace'
                })
    
    return merge_plan

def execute_merge(merge_plan, dry_run=True):
    """Execute the merge plan"""
    if not dry_run:
        backup_dir = backup_files()
        print(f"\n✅ Backup created: {backup_dir}")
    
    print("\nEXECUTING MERGE PLAN")
    print("=" * 80)
    
    for item in merge_plan:
        clean_path = item['clean']
        regular_path = item['regular']
        action = item['action']
        
        print(f"\n{os.path.basename(clean_path)}:")
        
        if action == 'replace':
            # Just rename clean to regular
            if not dry_run:
                # Delete old regular version
                os.remove(regular_path)
                # Rename clean to regular
                os.rename(clean_path, regular_path)
                print(f"  ✅ Renamed {os.path.basename(clean_path)} → {os.path.basename(regular_path)}")
            else:
                print(f"  → Would rename {os.path.basename(clean_path)} → {os.path.basename(regular_path)}")
        
        elif action == 'merge':
            print(f"  ⚠️  Manual merge needed - {len(item['unique_endpoints'])} unique endpoints in regular version")
            if not dry_run:
                print("  📝 Creating merge notes...")
                with open(f"{regular_path}.merge_needed", 'w') as f:
                    f.write(f"Merge needed from {os.path.basename(regular_path)}:\n\n")
                    for ep in item['unique_endpoints']:
                        f.write(f"- {ep}\n")

def update_api_imports(dry_run=True):
    """Update api.py to remove _clean aliases"""
    api_path = "app/api/v1/api.py"
    
    if not os.path.exists(api_path):
        return
    
    with open(api_path, 'r') as f:
        content = f.read()
    
    # Replace clean imports with regular imports
    replacements = [
        ("planning_clean as planning", "planning"),
        ("scoping_clean as scoping", "scoping"),
        ("data_owner_clean as data_owner", "data_owner"),
        ("request_info_clean as request_info", "request_info"),
        ("test_execution_clean as test_execution", "test_execution"),
        ("observation_management_clean as observation_management", "observation_management"),
    ]
    
    new_content = content
    for old, new in replacements:
        new_content = new_content.replace(old, new)
    
    if not dry_run and new_content != content:
        with open(api_path, 'w') as f:
            f.write(new_content)
        print("\n✅ Updated api.py imports")
    elif dry_run:
        print("\n→ Would update api.py imports")

def main():
    import sys
    dry_run = "--dry-run" in sys.argv
    
    print("BACKEND ENDPOINT MERGE TOOL")
    print("=" * 80)
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    
    # Analyze conflicts
    merge_plan = analyze_conflicts()
    
    # Check if any merges need manual intervention
    manual_merges = [item for item in merge_plan if item['action'] == 'merge']
    
    if manual_merges:
        print("\n⚠️  MANUAL MERGE REQUIRED")
        print("The following files have unique endpoints that need manual merging:")
        for item in manual_merges:
            print(f"  - {os.path.basename(item['regular'])}: {len(item['unique_endpoints'])} unique endpoints")
        
        print("\nRecommendation: Manually copy unique endpoints before proceeding")
        
        if not dry_run:
            response = input("\nContinue anyway? (yes/no): ")
            if response.lower() != "yes":
                print("Aborted.")
                return
    
    # Execute merge
    execute_merge(merge_plan, dry_run)
    
    # Update API imports
    update_api_imports(dry_run)
    
    if dry_run:
        print("\n✅ Analysis complete. Run without --dry-run to execute.")
    else:
        print("\n✅ Merge complete!")
        print("\n⚠️  IMPORTANT: Check .merge_needed files for manual merge requirements")

if __name__ == "__main__":
    main()