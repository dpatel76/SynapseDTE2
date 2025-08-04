#!/usr/bin/env python3
"""
Execute safe renaming for non-conflicting files
"""

import os
import shutil
import json
from datetime import datetime

# Frontend files to rename (no conflicts expected)
FRONTEND_RENAMES = [
    ("frontend/src/components/phase/DynamicActivityCardsEnhanced.tsx", "frontend/src/components/phase/DynamicActivityCards.tsx"),
    ("frontend/src/pages/ReportTestingPageRedesigned.tsx", "frontend/src/pages/ReportTestingPage.tsx"),
    ("frontend/src/pages/dashboards/TestExecutiveDashboardRedesigned.tsx", "frontend/src/pages/dashboards/TestExecutiveDashboard.tsx"),
    ("frontend/src/pages/dashboards/TesterDashboardEnhanced.tsx", "frontend/src/pages/dashboards/TesterDashboard.tsx"),
    ("frontend/src/pages/phases/DataProfilingEnhanced.tsx", "frontend/src/pages/phases/DataProfiling.tsx"),
    ("frontend/src/pages/phases/ObservationManagementEnhanced.tsx", "frontend/src/pages/phases/ObservationManagement.tsx"),
    ("frontend/src/pages/phases/SimplifiedPlanningPage.tsx", "frontend/src/pages/phases/PlanningPage.tsx"),
]

# Backend files to check for conflicts
BACKEND_CONFLICTS = [
    ("app/api/v1/endpoints/planning_clean.py", "app/api/v1/endpoints/planning.py"),
    ("app/api/v1/endpoints/scoping_clean.py", "app/api/v1/endpoints/scoping.py"),
    ("app/api/v1/endpoints/data_owner_clean.py", "app/api/v1/endpoints/data_owner.py"),
    ("app/api/v1/endpoints/request_info_clean.py", "app/api/v1/endpoints/request_info.py"),
    ("app/api/v1/endpoints/test_execution_clean.py", "app/api/v1/endpoints/test_execution.py"),
    ("app/api/v1/endpoints/observation_management_clean.py", "app/api/v1/endpoints/observation_management.py"),
]

def check_file_usage(filepath):
    """Check if a file is imported anywhere in the codebase"""
    filename = os.path.basename(filepath).replace('.py', '')
    imports = []
    
    for root, dirs, files in os.walk('.'):
        if any(skip in root for skip in ['.git', 'node_modules', 'venv', '__pycache__', 'backup']):
            continue
            
        for file in files:
            if file.endswith('.py'):
                full_path = os.path.join(root, file)
                if full_path == filepath:
                    continue
                    
                try:
                    with open(full_path, 'r') as f:
                        content = f.read()
                        if filename in content:
                            imports.append(full_path)
                except:
                    pass
    
    return imports

def create_backup():
    """Create a backup before any operations"""
    backup_dir = f"backup_logs/rename_execution_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)
    
    # Backup all files we might touch
    all_files = []
    for old, new in FRONTEND_RENAMES:
        all_files.extend([old, new])
    for old, new in BACKEND_CONFLICTS:
        all_files.extend([old, new])
    
    for filepath in all_files:
        if os.path.exists(filepath):
            backup_path = os.path.join(backup_dir, filepath)
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            shutil.copy2(filepath, backup_path)
    
    return backup_dir

def rename_frontend_files():
    """Rename frontend files that have no conflicts"""
    results = []
    
    for old_path, new_path in FRONTEND_RENAMES:
        if os.path.exists(old_path):
            if os.path.exists(new_path):
                # Check if new_path is a backup
                if new_path.endswith('.backup'):
                    results.append(f"⏭️  Skipped {old_path} - target is backup")
                else:
                    results.append(f"⚠️  Conflict: {old_path} -> {new_path} (target exists)")
            else:
                try:
                    os.rename(old_path, new_path)
                    results.append(f"✅ Renamed: {old_path} -> {new_path}")
                except Exception as e:
                    results.append(f"❌ Error renaming {old_path}: {e}")
        else:
            results.append(f"❌ Not found: {old_path}")
    
    return results

def analyze_backend_conflicts():
    """Analyze which backend files are actually in use"""
    analysis = []
    
    for clean_file, regular_file in BACKEND_CONFLICTS:
        clean_usage = check_file_usage(clean_file) if os.path.exists(clean_file) else []
        regular_usage = check_file_usage(regular_file) if os.path.exists(regular_file) else []
        
        analysis.append({
            "clean_file": clean_file,
            "regular_file": regular_file,
            "clean_exists": os.path.exists(clean_file),
            "regular_exists": os.path.exists(regular_file),
            "clean_imports": len(clean_usage),
            "regular_imports": len(regular_usage),
            "clean_imported_by": clean_usage[:3],  # First 3 files
            "regular_imported_by": regular_usage[:3]
        })
    
    return analysis

def update_imports():
    """Update imports after renaming"""
    # Import mappings for renamed files
    mappings = [
        ("DynamicActivityCardsEnhanced", "DynamicActivityCards"),
        ("ReportTestingPageRedesigned", "ReportTestingPage"),
        ("TestExecutiveDashboardRedesigned", "TestExecutiveDashboard"),
        ("TesterDashboardEnhanced", "TesterDashboard"),
        ("DataProfilingEnhanced", "DataProfiling"),
        ("ObservationManagementEnhanced", "ObservationManagement"),
        ("SimplifiedPlanningPage", "PlanningPage"),
    ]
    
    updated_files = []
    
    for root, dirs, files in os.walk('./frontend'):
        if any(skip in root for skip in ['.git', 'node_modules', 'backup']):
            continue
            
        for file in files:
            if file.endswith(('.ts', '.tsx', '.js', '.jsx')):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r') as f:
                        content = f.read()
                    
                    original = content
                    for old_name, new_name in mappings:
                        content = content.replace(f"'{old_name}'", f"'{new_name}'")
                        content = content.replace(f'"{old_name}"', f'"{new_name}"')
                        content = content.replace(f"/{old_name}", f"/{new_name}")
                        content = content.replace(f" as {new_name} from", f" from")  # Fix double aliasing
                    
                    if content != original:
                        with open(filepath, 'w') as f:
                            f.write(content)
                        updated_files.append(filepath)
                except:
                    pass
    
    return updated_files

def main():
    print("FILE RENAMING EXECUTION")
    print("=" * 60)
    
    # Create backup
    print("\n1. Creating backup...")
    backup_dir = create_backup()
    print(f"✅ Backup created: {backup_dir}")
    
    # Rename frontend files
    print("\n2. Renaming frontend files...")
    frontend_results = rename_frontend_files()
    for result in frontend_results:
        print(result)
    
    # Update imports
    print("\n3. Updating imports...")
    updated = update_imports()
    print(f"✅ Updated {len(updated)} files")
    
    # Analyze backend conflicts
    print("\n4. Analyzing backend conflicts...")
    backend_analysis = analyze_backend_conflicts()
    
    print("\nBACKEND FILE ANALYSIS:")
    print("-" * 60)
    
    for info in backend_analysis:
        print(f"\n{info['clean_file']}:")
        print(f"  Exists: {info['clean_exists']}")
        print(f"  Imported by {info['clean_imports']} files")
        if info['clean_imported_by']:
            for imp in info['clean_imported_by']:
                print(f"    - {imp}")
        
        print(f"\n{info['regular_file']}:")
        print(f"  Exists: {info['regular_exists']}")
        print(f"  Imported by {info['regular_imports']} files")
        if info['regular_imported_by']:
            for imp in info['regular_imported_by']:
                print(f"    - {imp}")
        
        # Recommendation
        if info['clean_exists'] and info['regular_exists']:
            if info['clean_imports'] > 0 and info['regular_imports'] == 0:
                print(f"  📌 RECOMMENDATION: Use clean version, delete regular")
            elif info['clean_imports'] == 0 and info['regular_imports'] > 0:
                print(f"  📌 RECOMMENDATION: Use regular version, delete clean")
            elif info['clean_imports'] > 0 and info['regular_imports'] > 0:
                print(f"  📌 RECOMMENDATION: Both in use - needs merge")
            else:
                print(f"  📌 RECOMMENDATION: Neither imported - check which is registered")
    
    # Save analysis
    with open('backend_conflict_analysis.json', 'w') as f:
        json.dump(backend_analysis, f, indent=2)
    
    print(f"\n✅ Analysis saved to backend_conflict_analysis.json")
    print(f"\n✅ Frontend renaming complete. Backend conflicts need manual review.")

if __name__ == "__main__":
    main()