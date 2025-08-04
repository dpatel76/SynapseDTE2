-- Standardize database table names for consistency
-- This script renames tables to follow consistent naming conventions

-- Fix audit log tables that incorrectly use plural
ALTER TABLE IF EXISTS test_execution_audit_logs RENAME TO test_execution_audit_log;
ALTER TABLE IF EXISTS observation_management_audit_logs RENAME TO observation_management_audit_log;

-- Fix redundant table name
ALTER TABLE IF EXISTS testing_test_executions RENAME TO test_executions;

-- Standardize entity tables to plural (only those currently singular)
-- Note: Many core tables are already plural (users, reports, documents, etc.)

-- Audit and logging tables
ALTER TABLE IF EXISTS audit_log RENAME TO audit_logs;
ALTER TABLE IF EXISTS llm_audit_log RENAME TO llm_audit_logs;
ALTER TABLE IF EXISTS version_history RENAME TO universal_version_histories;
ALTER TABLE IF EXISTS regulatory_data_dictionary RENAME TO regulatory_data_dictionaries;

-- Data owner related tables
ALTER TABLE IF EXISTS data_owner_assignment RENAME TO data_owner_assignments;
ALTER TABLE IF EXISTS attribute_lob_assignment RENAME TO attribute_lob_assignments;
ALTER TABLE IF EXISTS historical_data_owner_assignment RENAME TO historical_data_owner_assignments;
ALTER TABLE IF EXISTS data_owner_sla_violation RENAME TO data_owner_sla_violations;
ALTER TABLE IF EXISTS data_owner_escalation_log RENAME TO data_owner_escalation_logs;
ALTER TABLE IF EXISTS data_owner_phase_audit_log RENAME TO data_owner_phase_audit_logs;

-- Data profiling tables
ALTER TABLE IF EXISTS data_profiling_phase RENAME TO data_profiling_phases;
ALTER TABLE IF EXISTS data_profiling_file RENAME TO data_profiling_files;
ALTER TABLE IF EXISTS profiling_rule RENAME TO profiling_rules;
ALTER TABLE IF EXISTS profiling_result RENAME TO profiling_results;
ALTER TABLE IF EXISTS attribute_profiling_score RENAME TO attribute_profiling_scores;

-- Document related tables
ALTER TABLE IF EXISTS document_access_log RENAME TO document_access_logs;
ALTER TABLE IF EXISTS document_extraction RENAME TO document_extractions;
ALTER TABLE IF EXISTS document_revision RENAME TO document_revisions;

-- Observation tables
ALTER TABLE IF EXISTS observation_group RENAME TO observation_groups;
ALTER TABLE IF EXISTS observation_clarification RENAME TO observation_clarifications;
ALTER TABLE IF EXISTS test_report_phase RENAME TO test_report_phases;
ALTER TABLE IF EXISTS test_report_section RENAME TO test_report_sections;
ALTER TABLE IF EXISTS observation_management_phase RENAME TO observation_management_phases;
ALTER TABLE IF EXISTS observation_record RENAME TO observation_records;
ALTER TABLE IF EXISTS observation_impact_assessment RENAME TO observation_impact_assessments;
ALTER TABLE IF EXISTS observation_approval RENAME TO observation_approvals;
ALTER TABLE IF EXISTS observation_resolution RENAME TO observation_resolutions;

-- RBAC tables
ALTER TABLE IF EXISTS role_permission RENAME TO role_permissions;
ALTER TABLE IF EXISTS user_role RENAME TO user_roles;
ALTER TABLE IF EXISTS user_permission RENAME TO user_permissions;
ALTER TABLE IF EXISTS resource_permission RENAME TO resource_permissions;
ALTER TABLE IF EXISTS role_hierarchy RENAME TO role_hierarchies;
ALTER TABLE IF EXISTS permission_audit_log RENAME TO permission_audit_logs;

-- Report related tables
ALTER TABLE IF EXISTS data_source RENAME TO data_sources;
ALTER TABLE IF EXISTS report_attribute RENAME TO report_attributes;
ALTER TABLE IF EXISTS attribute_version_change_log RENAME TO attribute_version_change_logs;
ALTER TABLE IF EXISTS attribute_version_comparison RENAME TO attribute_version_comparisons;
ALTER TABLE IF EXISTS report_owner_assignment RENAME TO report_owner_assignments;
ALTER TABLE IF EXISTS report_owner_assignment_history RENAME TO report_owner_assignment_histories;

-- Request info tables
ALTER TABLE IF EXISTS request_info_phase RENAME TO request_info_phases;
ALTER TABLE IF EXISTS data_provider_notification RENAME TO data_provider_notifications;
ALTER TABLE IF EXISTS document_submission RENAME TO document_submissions;
ALTER TABLE IF EXISTS request_info_audit_log RENAME TO request_info_audit_logs;

-- Sample selection tables
ALTER TABLE IF EXISTS sample_set RENAME TO sample_sets;
ALTER TABLE IF EXISTS sample_record RENAME TO sample_records;
ALTER TABLE IF EXISTS sample_validation_result RENAME TO sample_validation_results;
ALTER TABLE IF EXISTS sample_validation_issue RENAME TO sample_validation_issues;
ALTER TABLE IF EXISTS sample_approval_history RENAME TO sample_approval_histories;
ALTER TABLE IF EXISTS llm_sample_generation RENAME TO llm_sample_generations;
ALTER TABLE IF EXISTS sample_upload_history RENAME TO sample_upload_histories;
ALTER TABLE IF EXISTS sample_selection_audit_log RENAME TO sample_selection_audit_logs;
ALTER TABLE IF EXISTS sample_selection_phase RENAME TO sample_selection_phases;

-- Scoping tables
ALTER TABLE IF EXISTS attribute_scoping_recommendation RENAME TO attribute_scoping_recommendations;
ALTER TABLE IF EXISTS tester_scoping_decision RENAME TO tester_scoping_decisions;
ALTER TABLE IF EXISTS scoping_submission RENAME TO scoping_submissions;
ALTER TABLE IF EXISTS report_owner_scoping_review RENAME TO report_owner_scoping_reviews;
ALTER TABLE IF EXISTS scoping_audit_log RENAME TO scoping_audit_logs;

-- SLA tables
ALTER TABLE IF EXISTS sla_configuration RENAME TO sla_configurations;
ALTER TABLE IF EXISTS sla_escalation_rule RENAME TO sla_escalation_rules;
ALTER TABLE IF EXISTS sla_violation_tracking RENAME TO sla_violation_trackings;
ALTER TABLE IF EXISTS escalation_email_log RENAME TO escalation_email_logs;

-- Test execution tables
ALTER TABLE IF EXISTS test_execution_phase RENAME TO test_execution_phases;
ALTER TABLE IF EXISTS test_execution RENAME TO test_executions;
ALTER TABLE IF EXISTS document_analysis RENAME TO document_analyses;
ALTER TABLE IF EXISTS database_test RENAME TO database_tests;
ALTER TABLE IF EXISTS test_result_review RENAME TO test_result_reviews;
ALTER TABLE IF EXISTS test_comparison RENAME TO test_comparisons;
ALTER TABLE IF EXISTS bulk_test_execution RENAME TO bulk_test_executions;

-- Universal assignment tables
ALTER TABLE IF EXISTS universal_assignment RENAME TO universal_assignments;
ALTER TABLE IF EXISTS universal_assignment_history RENAME TO universal_assignment_histories;
ALTER TABLE IF EXISTS assignment_template RENAME TO assignment_templates;

-- Versioning tables
ALTER TABLE IF EXISTS data_profiling_rule_version RENAME TO data_profiling_rule_versions;
ALTER TABLE IF EXISTS test_execution_version RENAME TO test_execution_versions;
ALTER TABLE IF EXISTS observation_version RENAME TO observation_versions;
ALTER TABLE IF EXISTS scoping_decision_version RENAME TO scoping_decision_versions;
ALTER TABLE IF EXISTS versioned_attribute_scoping_recommendation RENAME TO versioned_attribute_scoping_recommendations;

-- Workflow tables
ALTER TABLE IF EXISTS workflow_phase RENAME TO workflow_phases;
ALTER TABLE IF EXISTS workflow_activity RENAME TO workflow_activities;
ALTER TABLE IF EXISTS workflow_activity_history RENAME TO workflow_activity_histories;
ALTER TABLE IF EXISTS workflow_activity_dependency RENAME TO workflow_activity_dependencies;
ALTER TABLE IF EXISTS workflow_activity_template RENAME TO workflow_activity_templates;
ALTER TABLE IF EXISTS workflow_execution RENAME TO workflow_executions;
ALTER TABLE IF EXISTS workflow_step RENAME TO workflow_steps;
ALTER TABLE IF EXISTS workflow_transition RENAME TO workflow_transitions;
ALTER TABLE IF EXISTS workflow_metric RENAME TO workflow_metrics;
ALTER TABLE IF EXISTS workflow_alert RENAME TO workflow_alerts;

-- Metrics tables
ALTER TABLE IF EXISTS phase_metric RENAME TO metrics_phases;
ALTER TABLE IF EXISTS execution_metric RENAME TO metrics_execution;