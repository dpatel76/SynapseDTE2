#!/usr/bin/env python
"""Fix workflow activity references to use string names"""

import re

# List of all activity names
activities = [
    # Planning
    "start_planning_phase_activity",
    "upload_planning_documents_activity", 
    "import_create_attributes_activity",
    "review_planning_checklist_activity",
    "complete_planning_phase_activity",
    
    # Scoping
    "start_scoping_phase_activity",
    "generate_llm_recommendations_activity",
    "tester_review_attributes_activity",
    "report_owner_approval_activity",
    "complete_scoping_phase_activity",
    
    # Sample Selection
    "start_sample_selection_phase_activity",
    "define_selection_criteria_activity",
    "generate_sample_sets_activity",
    "review_approve_samples_activity",
    "complete_sample_selection_phase_activity",
    
    # Data Provider
    "start_data_provider_phase_activity",
    "auto_assign_data_providers_activity",
    "review_data_provider_assignments_activity",
    "send_data_provider_notifications_activity",
    "complete_data_provider_phase_activity",
    
    # Request Info
    "start_request_info_phase_activity",
    "generate_test_cases_activity",
    "create_information_requests_activity",
    "send_rfi_emails_activity",
    "track_rfi_responses_activity",
    "complete_request_info_phase_activity",
    
    # Test Execution
    "start_test_execution_phase_activity",
    "create_test_execution_records_activity",
    "execute_document_tests_activity",
    "execute_database_tests_activity",
    "record_test_results_activity",
    "generate_test_summary_activity",
    "complete_test_execution_phase_activity",
    
    # Observation
    "start_observation_phase_activity",
    "create_observations_activity",
    "auto_group_observations_activity",
    "review_approve_observations_activity",
    "generate_impact_assessment_activity",
    "complete_observation_phase_activity",
    
    # Test Report
    "start_test_report_phase_activity",
    "generate_report_sections_activity",
    "generate_executive_summary_activity",
    "review_edit_report_activity",
    "finalize_report_activity",
    "complete_test_report_phase_activity"
]

# Read the workflow file
with open('app/temporal/workflows/test_cycle_workflow_reconciled.py', 'r') as f:
    content = f.read()

# Replace each activity name with its string version
for activity in activities:
    # Pattern to match the activity name in execute_activity calls
    # This handles both single line and multi-line cases
    pattern = rf'(\s+)(workflow\.execute_activity\(\s*\n?\s*){activity}(\s*,|\s*\n)'
    replacement = rf'\1\2"{activity}"\3'
    content = re.sub(pattern, replacement, content)

# Write the updated content
with open('app/temporal/workflows/test_cycle_workflow_reconciled.py', 'w') as f:
    f.write(content)

print("Fixed all activity references to use string names")