#!/usr/bin/env python3
# Auto-generated script to update imports after renaming
import os
import re

replacements = [
    ('frontend_clean', 'frontend'),
    ('UNIVERSAL_PHASE_STATUS_FRAMEWORK_V2', 'UNIVERSAL_PHASE_STATUS_FRAMEWORK_'),
    ('api_clean', 'api'),
    ('data_sources_clean', 'data_sources'),
    ('planning_clean', 'planning'),
    ('reports_clean', 'reports'),
    ('admin_rbac_clean', 'admin_rbac'),
    ('metrics_clean', 'metrics'),
    ('data_profiling_clean', 'data_profiling'),
    ('llm_clean', 'llm'),
    ('admin_clean', 'admin'),
    ('admin_sla_clean', 'admin_sla'),
    ('scoping_clean', 'scoping'),
    ('cycles_clean', 'cycles'),
    ('dashboards_clean', 'dashboards'),
    ('request_info_clean', 'request_info'),
    ('users_clean', 'users'),
    ('auth_clean', 'auth'),
    ('data_owner_clean', 'data_owner'),
    ('cycle_reports_clean', 'cycle_reports'),
    ('observation_management_clean', 'observation_management'),
    ('test_execution_clean', 'test_execution'),
    ('activity_state_manager_v2', 'activity_state_manager'),
    ('DynamicActivityCardsEnhanced', 'DynamicActivityCards'),
    ('ReportTestingPageRedesigned', 'ReportTestingPage'),
    ('TestExecutiveDashboardRedesigned', 'TestExecutiveDashboard'),
    ('TesterDashboardEnhanced', 'TesterDashboard'),
    ('DataProfilingEnhanced', 'DataProfiling'),
    ('ObservationManagementEnhanced', 'ObservationManagement'),
    ('SimplifiedPlanningPage', 'planningPage'),
    ('fix_cdo_assignments_v2', 'fix_cdo_assignments'),
    ('test_workflow_clean', 'test_workflow'),
    ('start_backend_clean', 'start_backend'),
    ('restart_backend_clean', 'restart_backend'),

]

def update_imports(filepath):
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        original_content = content
        for old, new in replacements:
            # Update various import patterns
            content = re.sub(rf'\b{old}\b', new, content)
        
        if content != original_content:
            with open(filepath, 'w') as f:
                f.write(content)
            return True
    except Exception as e:
        print(f"Error updating {filepath}: {e}")
    return False

# Update all files
root_dir = '/Users/dineshpatel/code/projects/SynapseDTE'
updated_files = 0

for dirpath, dirnames, filenames in os.walk(root_dir):
    if any(skip in dirpath for skip in ['__pycache__', '.git', 'venv', 'backup', 'node_modules']):
        continue
        
    for filename in filenames:
        if filename.endswith(('.py', '.ts', '.tsx', '.js', '.jsx')):
            filepath = os.path.join(dirpath, filename)
            if update_imports(filepath):
                updated_files += 1
                print(f"Updated: {filepath}")

print(f"\nUpdated {updated_files} files")
