# Table Naming Standardization Plan

## Naming Convention: `cycle_report_<phase>_<action>`

## Phases:
1. **planning** - Planning Phase
2. **scoping** - Scoping Phase  
3. **data_profiling** - Data Profiling Phase
4. **data_owner** - Data Owner Identification Phase
5. **sample_selection** - Sample Selection Phase
6. **request_info** - Request for Information Phase
7. **test_execution** - Test Execution Phase
8. **observation_mgmt** - Observation Management Phase
9. **test_report** - Test Report Phase

## Tables to Rename:

### Planning Phase
- `cycle_report_attributes_planning` → OK (already follows convention)
- `cycle_report_attributes_planning_version_history` → `cycle_report_planning_attribute_version_history`
- `attribute_version_change_logs` → `cycle_report_planning_attribute_change_logs`
- `attribute_version_comparisons` → `cycle_report_planning_attribute_comparisons`

### Scoping Phase
- `attribute_scoping_recommendations` → `cycle_report_scoping_recommendations`
- `tester_scoping_decisions` → `cycle_report_scoping_tester_decisions`
- `cycle_report_scoping_submissions` → OK
- `report_owner_scoping_reviews` → `cycle_report_scoping_owner_reviews`
- `scoping_audit_log` → `cycle_report_scoping_audit_log`

### Data Profiling Phase
- `data_profiling_phases` → `cycle_report_data_profiling_phases`
- `data_profiling_files` → `cycle_report_data_profiling_files`
- `profiling_rules` → `cycle_report_data_profiling_rules` (duplicate!)
- `profiling_results` → `cycle_report_data_profiling_results`
- `attribute_profiling_scores` → `cycle_report_data_profiling_attribute_scores`
- Already renamed in data_profiling_enhanced.py - OK

### Data Owner Phase
- `attribute_lob_assignments` → `cycle_report_data_owner_lob_assignments`
- `data_owner_assignments` → `cycle_report_data_owner_assignments`
- `historical_data_owner_assignments` → `cycle_report_data_owner_historical_assignments`
- `data_owner_sla_violations` → `cycle_report_data_owner_sla_violations`
- `data_owner_escalation_log` → `cycle_report_data_owner_escalation_log`
- `data_owner_phase_audit_log` → `cycle_report_data_owner_audit_log`
- `data_owner_notifications` → `cycle_report_data_owner_notifications`

### Sample Selection Phase
- `cycle_report_sample_sets` → OK
- `cycle_report_sample_records` → OK
- `sample_selection_phases` → `cycle_report_sample_selection_phases`
- `sample_validation_results` → `cycle_report_sample_selection_validation_results`
- `sample_validation_issues` → `cycle_report_sample_selection_validation_issues`
- `sample_approval_history` → `cycle_report_sample_selection_approval_history`
- `llm_sample_generations` → `cycle_report_sample_selection_llm_generations`
- `sample_upload_history` → `cycle_report_sample_selection_upload_history`
- `sample_selection_audit_log` → `cycle_report_sample_selection_audit_log`

### Request Info Phase
- `cycle_report_request_info_phases` → OK
- `cycle_report_test_cases` → `cycle_report_request_info_test_cases`
- `document_submissions` → `cycle_report_request_info_document_submissions`
- `request_info_audit_log` → `cycle_report_request_info_audit_log`

### Test Execution Phase
- `test_execution_phases` → `cycle_report_test_execution_phases`
- `cycle_report_test_executions` → OK
- `document_analyses` → `cycle_report_test_execution_document_analyses`
- `database_tests` → `cycle_report_test_execution_database_tests`
- `test_result_reviews` → `cycle_report_test_execution_result_reviews`
- `test_comparisons` → `cycle_report_test_execution_comparisons`
- `bulk_test_executions` → `cycle_report_test_execution_bulk_executions`
- `test_execution_audit_logs` → `cycle_report_test_execution_audit_logs`

### Observation Management Phase
- `observation_management_phases` → `cycle_report_observation_mgmt_phases`
- `observation_records` → `cycle_report_observation_mgmt_records`
- `observation_impact_assessments` → `cycle_report_observation_mgmt_impact_assessments`
- `observation_approvals` → `cycle_report_observation_mgmt_approvals`
- `observation_resolutions` → `cycle_report_observation_mgmt_resolutions`
- `observation_management_audit_logs` → `cycle_report_observation_mgmt_audit_logs`

### Test Report Phase (Enhanced Observation)
- `test_report_phases` → `cycle_report_test_report_phases`
- `observation_groups` → `cycle_report_test_report_observation_groups`
- `cycle_report_observations` → `cycle_report_test_report_observations`
- `observation_clarifications` → `cycle_report_test_report_clarifications`
- `test_report_sections` → `cycle_report_test_report_sections`
- `document_revisions` → `cycle_report_test_report_document_revisions`

### PDEs and Data Sources
- `cycle_report_pde_mappings` → OK
- `cycle_report_pde_classifications` → OK
- `cycle_report_data_sources` → OK
- `pde_mapping_reviews` → `cycle_report_data_profiling_pde_reviews`
- `pde_mapping_review_history` → `cycle_report_data_profiling_pde_review_history`
- `pde_mapping_approval_rules` → `cycle_report_data_profiling_pde_approval_rules`

### Sample Management (Testing)
- `samples` → `cycle_report_test_execution_samples`

## Non Cycle-Report Tables (Keep as is):
- test_cycles
- reports  
- users
- lobs
- documents
- document_access_logs
- document_extractions
- regulatory_data_dictionaries
- workflow_phases
- workflow_activities
- workflow_activity_*
- workflow_tracking tables
- rbac tables
- audit_log
- llm_audit_log
- sla_configurations
- sla_escalation_rules
- sla_violation_tracking
- escalation_email_logs
- universal_assignments
- report_owner_assignments
- metrics tables
- versioning tables (need separate review)