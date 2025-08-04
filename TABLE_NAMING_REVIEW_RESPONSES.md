# Table Naming Review - Responses to Feedback

## Planning Phase

### ✓ CORRECT - Need to fix:
- `cycle_report_attributes_planning` → `cycle_report_planning_attributes` 
- `attribute_version_change_logs` → `cycle_report_planning_attribute_version_change_logs`
- `attribute_version_comparisons` → `cycle_report_planning_attribute_version_comparisons`

## Data Profiling Phase

### QUESTION: "why is data_profiling_phases table needed?"
**ANSWER**: This table tracks the overall data profiling phase status for each cycle/report. It stores:
- Phase start/end times
- Overall status (not_started, in_progress, completed)
- Configuration settings
- Links to profiling jobs
**RECOMMENDATION**: Keep but rename to `cycle_report_data_profiling_phase_status`

### ✓ CORRECT - Using DQ (Data Quality) prefix:
- `profiling_rules` → `cycle_report_data_profiling_dq_rules` 
- `profiling_results` → `cycle_report_data_profiling_dq_results`
- `attribute_profiling_scores` → `cycle_report_data_profiling_attribute_dq_scores`

## Data Owner Phase

### ✓ CORRECT:
- `historical_data_owner_assignments` → `cycle_report_data_owner_assignments_history`

### QUESTION: "Why data_owner_sla_violations? Should have universal SLA framework"
**ANSWER**: You're right. This should be replaced by the universal SLA framework.
**RECOMMENDATION**: Remove this table and use universal SLA tables instead

### QUESTION: "Why data_owner_escalation_log? Should have universal escalation"
**ANSWER**: Agreed. Should use universal escalation framework.
**RECOMMENDATION**: Remove and use universal escalation

### QUESTION: "Why data_owner_phase_audit_log?"
**ANSWER**: This appears to be phase-specific audit logging. 
**RECOMMENDATION**: Remove if we have universal audit logging, or rename to `cycle_report_data_owner_activity_log` if we need phase-specific activity tracking

### QUESTION: "Why data_owner_notifications? Should use universal assignments"
**ANSWER**: You're correct. With universal assignments, this is redundant.
**RECOMMENDATION**: Remove this table

## Sample Selection Phase

### QUESTION: "Why cycle_report_sample_sets? Thought we moved away from sample sets"
**ANSWER**: Looking at the model, sample_sets groups individual samples for a report. It tracks:
- Total sample count
- Selection method
- Approval status
**RECOMMENDATION**: Need clarification - are we keeping sample grouping concept?

### QUESTION: "Why sample_selection_phases?"
**ANSWER**: Similar to data_profiling_phases - tracks overall phase status
**RECOMMENDATION**: If keeping, rename to `cycle_report_sample_selection_phase_status`

### QUESTION: "What are sample_validation_results and issues used for?"
**ANSWER**: These tables store:
- `validation_results`: Overall validation status for a sample set
- `validation_issues`: Specific issues found during validation (duplicates, formatting, etc.)
**RECOMMENDATION**: Keep if we're validating uploaded samples, otherwise remove

## Request Info Phase

### QUESTION: "Where do we store document history for re-uploads?"
**ANSWER**: Currently document_submissions has version tracking. Should we:
1. Add version column to track iterations?
2. Create separate `cycle_report_request_info_document_versions` table?
**RECOMMENDATION**: Add versioning to handle re-uploads

### ✓ CORRECT:
- `request_info_audit_log` → `cycle_report_request_info_audit_logs`

## Test Execution Phase

### QUESTION: "Why test_execution_phases?"
**ANSWER**: Phase status tracking table
**RECOMMENDATION**: Rename to `cycle_report_test_execution_phase_status` or remove if using universal status

## Observation Management Phase

### QUESTION: "Why observation_management_phases?"
**ANSWER**: Phase status tracking
**RECOMMENDATION**: Remove if using universal status tracking

### QUESTION: "Where to store preliminary findings?"
**ANSWER**: Good point. Need a table for draft observations
**RECOMMENDATION**: Add `cycle_report_observation_mgmt_drafts` table

### QUESTION: "How is observation_impact_assessments used?"
**ANSWER**: Stores impact analysis for each observation (financial, regulatory, operational impact)
**RECOMMENDATION**: Keep if doing formal impact assessment

### QUESTION: "What is observation_resolutions for?"
**ANSWER**: Tracks how observations were resolved/remediated
**RECOMMENDATION**: Keep if tracking remediation

## Test Report Phase

### QUESTION: "Why test_report_phases?"
**ANSWER**: Phase status tracking
**RECOMMENDATION**: Remove if using universal status

### QUESTION: "Why are observation tables in test_report not observation_mgmt?"
**ANSWER**: These appear to be the final observations that go into the test report, while observation_mgmt handles the workflow. However, this is confusing.
**RECOMMENDATION**: Move all observation tables to observation_mgmt phase:
- `observation_groups` → `cycle_report_observation_mgmt_groups`
- `cycle_report_observations` → `cycle_report_observation_mgmt_observations`
- `observation_clarifications` → `cycle_report_observation_mgmt_clarifications`

## PDEs and Data Sources

### ✓ CORRECT - Should be in planning phase:
- `cycle_report_pde_mappings` → `cycle_report_planning_pde_mappings`
- `cycle_report_pde_classifications` → `cycle_report_planning_pde_classifications`
- `cycle_report_data_sources` → `cycle_report_planning_data_sources`

### QUESTION: "PDE review tables - where used?"
**ANSWER**: Looking at the models, these handle review/approval of PDE mappings created in planning phase. The workflow is:
1. Planning: Create PDE mappings
2. Data Profiling: Review/approve mappings before using them
**RECOMMENDATION**: 
- If reviews happen in planning: `cycle_report_planning_pde_mapping_reviews`
- If reviews happen in data profiling: `cycle_report_data_profiling_pde_mapping_reviews`

## Sample Management

### QUESTION: "How is samples table used vs test cases?"
**ANSWER**: The `samples` table appears to store the actual data samples used for testing, while test_cases define what to test. The relationship:
- Test Case: "Verify customer balance calculations"
- Sample: Actual customer records used to test this
**RECOMMENDATION**: Rename to `cycle_report_test_execution_sample_data`

## Summary of Changes Based on Feedback:

### Tables to Remove (use universal frameworks):
- data_owner_sla_violations
- data_owner_escalation_log  
- data_owner_notifications
- All phase-specific status tables (use universal status)

### Tables to Clarify:
- Sample sets concept - keep or remove?
- Observation workflow - which tables for which phase?
- PDE review timing - planning or data profiling?

### New Tables Needed:
- cycle_report_observation_mgmt_drafts (for preliminary findings)
- cycle_report_request_info_document_versions (for re-uploads)