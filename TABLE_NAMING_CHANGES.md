# Table Naming Changes - Current vs Proposed

## Format: Current → Proposed

### Planning Phase
```
cycle_report_attributes_planning → cycle_report_planning_attributes ✓
cycle_report_attributes_planning_version_history → cycle_report_planning_attribute_version_history
attribute_version_change_logs → cycle_report_planning_attribute_change_logs
attribute_version_comparisons → cycle_report_planning_attribute_comparisons
```

### Scoping Phase
```
attribute_scoping_recommendations → cycle_report_scoping_attribute_recommendations
tester_scoping_decisions → cycle_report_scoping_tester_decisions
cycle_report_scoping_submissions → cycle_report_scoping_submissions (OK)
report_owner_scoping_reviews → cycle_report_scoping_report_owner_reviews
scoping_audit_log → cycle_report_scoping_audit_log
```

### Data Profiling Phase
```
data_profiling_phases → cycle_report_data_profiling_phases
data_profiling_files → cycle_report_data_profiling_files
profiling_rules → cycle_report_data_profiling_rules_old (conflicts with enhanced)
profiling_results → cycle_report_data_profiling_results
attribute_profiling_scores → cycle_report_data_profiling_attribute_scores

# From data_profiling_enhanced.py (already updated):
cycle_report_data_profiling_configurations → cycle_report_data_profiling_configurations (OK)
cycle_report_data_profiling_jobs → cycle_report_data_profiling_jobs (OK)
cycle_report_attribute_profile_results → cycle_report_data_profiling_attribute_results
cycle_report_data_profiling_rules → cycle_report_data_profiling_rules (OK)
cycle_report_anomaly_patterns_data_profiling → cycle_report_data_profiling_anomaly_patterns
```

### Data Owner Phase
```
attribute_lob_assignments → cycle_report_data_owner_attribute_lob_assignments
data_owner_assignments → cycle_report_data_owner_assignments
historical_data_owner_assignments → cycle_report_data_owner_historical_assignments
data_owner_sla_violations → cycle_report_data_owner_sla_violations
data_owner_escalation_log → cycle_report_data_owner_escalation_log
data_owner_phase_audit_log → cycle_report_data_owner_audit_log
data_owner_notifications → cycle_report_data_owner_notifications
```

### Sample Selection Phase
```
cycle_report_sample_sets → cycle_report_sample_selection_sets
cycle_report_sample_records → cycle_report_sample_selection_records
sample_selection_phases → cycle_report_sample_selection_phases
sample_validation_results → cycle_report_sample_selection_validation_results
sample_validation_issues → cycle_report_sample_selection_validation_issues
sample_approval_history → cycle_report_sample_selection_approval_history
llm_sample_generations → cycle_report_sample_selection_llm_generations
sample_upload_history → cycle_report_sample_selection_upload_history
sample_selection_audit_log → cycle_report_sample_selection_audit_log
```

### Request Info Phase
```
cycle_report_request_info_phases → cycle_report_request_info_phases (OK)
cycle_report_test_cases → cycle_report_request_info_test_cases
document_submissions → cycle_report_request_info_document_submissions
request_info_audit_log → cycle_report_request_info_audit_log
```

### Test Execution Phase
```
test_execution_phases → cycle_report_test_execution_phases
cycle_report_test_executions → cycle_report_test_execution_executions
document_analyses → cycle_report_test_execution_document_analyses
database_tests → cycle_report_test_execution_database_tests
test_result_reviews → cycle_report_test_execution_result_reviews
test_comparisons → cycle_report_test_execution_comparisons
bulk_test_executions → cycle_report_test_execution_bulk_executions
test_execution_audit_logs → cycle_report_test_execution_audit_logs
samples → cycle_report_test_execution_samples
```

### Observation Management Phase
```
observation_management_phases → cycle_report_observation_mgmt_phases
observation_records → cycle_report_observation_mgmt_records
observation_impact_assessments → cycle_report_observation_mgmt_impact_assessments
observation_approvals → cycle_report_observation_mgmt_approvals
observation_resolutions → cycle_report_observation_mgmt_resolutions
observation_management_audit_logs → cycle_report_observation_mgmt_audit_logs
```

### Test Report Phase (Enhanced Observation)
```
test_report_phases → cycle_report_test_report_phases
observation_groups → cycle_report_test_report_observation_groups
cycle_report_observations → cycle_report_test_report_observations
observation_clarifications → cycle_report_test_report_observation_clarifications
test_report_sections → cycle_report_test_report_sections
document_revisions → cycle_report_test_report_document_revisions
```

### PDEs and Data Sources
```
cycle_report_pde_mappings → cycle_report_pde_mappings (OK)
cycle_report_pde_classifications → cycle_report_pde_classifications (OK)
cycle_report_data_sources → cycle_report_data_sources (OK)
pde_mapping_reviews → cycle_report_pde_mapping_reviews
pde_mapping_review_history → cycle_report_pde_mapping_review_history
pde_mapping_approval_rules → cycle_report_pde_mapping_approval_rules
```

### Enhanced Models (profiling_enhanced.py)
```
profiling_jobs → cycle_report_data_profiling_enhanced_jobs
profiling_partitions → cycle_report_data_profiling_enhanced_partitions
partition_results → cycle_report_data_profiling_enhanced_partition_results
profiling_rule_sets → cycle_report_data_profiling_enhanced_rule_sets
profiling_anomaly_patterns → cycle_report_data_profiling_enhanced_anomaly_patterns
profiling_cache → cycle_report_data_profiling_enhanced_cache
```

### Enhanced Sample Selection Models
```
intelligent_sampling_jobs → cycle_report_sample_selection_intelligent_jobs
sample_pools → cycle_report_sample_selection_pools
intelligent_samples → cycle_report_sample_selection_intelligent_samples
sampling_rules → cycle_report_sample_selection_rules
sample_lineage → cycle_report_sample_selection_lineage
```

### Enhanced Data Source Models
```
data_sources_v2 → cycle_report_data_sources_enhanced
attribute_mappings → cycle_report_data_source_attribute_mappings
data_queries → cycle_report_data_source_queries
profiling_executions → cycle_report_data_source_profiling_executions
secure_data_access_logs → cycle_report_data_source_access_logs
```

## Summary Statistics:
- Total tables to rename: ~75
- Tables already correct: ~10
- New naming pattern: cycle_report_<phase>_<entity/action>

## Key Principles:
1. All cycle/report related tables start with `cycle_report_`
2. Next comes the phase name (e.g., `planning`, `scoping`, `data_profiling`)
3. Finally the entity or action (e.g., `attributes`, `recommendations`, `audit_log`)
4. Keep singular/plural consistent with the entity type