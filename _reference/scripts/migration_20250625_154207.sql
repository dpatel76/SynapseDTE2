-- Database Migration Script
-- Generated: 2025-06-25T15:42:07.255613
-- This script recreates the database schema and seed data

-- Drop existing tables
SET client_min_messages TO WARNING;
DROP TABLE IF EXISTS workflow_transitions CASCADE;
DROP TABLE IF EXISTS workflow_steps CASCADE;
DROP TABLE IF EXISTS workflow_phases CASCADE;
DROP TABLE IF EXISTS workflow_metrics CASCADE;
DROP TABLE IF EXISTS workflow_executions CASCADE;
DROP TABLE IF EXISTS workflow_alerts CASCADE;
DROP TABLE IF EXISTS workflow_activity_templates CASCADE;
DROP TABLE IF EXISTS workflow_activity_history CASCADE;
DROP TABLE IF EXISTS workflow_activity_dependencies CASCADE;
DROP TABLE IF EXISTS workflow_activities CASCADE;
DROP TABLE IF EXISTS version_history CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS user_roles CASCADE;
DROP TABLE IF EXISTS user_permissions CASCADE;
DROP TABLE IF EXISTS universal_assignments CASCADE;
DROP TABLE IF EXISTS universal_assignment_history CASCADE;
DROP TABLE IF EXISTS testing_test_executions CASCADE;
DROP TABLE IF EXISTS testing_execution_phases CASCADE;
DROP TABLE IF EXISTS testing_execution_audit_logs CASCADE;
DROP TABLE IF EXISTS tester_scoping_decisions CASCADE;
DROP TABLE IF EXISTS test_result_reviews CASCADE;
DROP TABLE IF EXISTS test_report_sections CASCADE;
DROP TABLE IF EXISTS test_report_phases CASCADE;
DROP TABLE IF EXISTS test_executions CASCADE;
DROP TABLE IF EXISTS test_execution_versions CASCADE;
DROP TABLE IF EXISTS test_execution_phases CASCADE;
DROP TABLE IF EXISTS test_execution_audit_logs CASCADE;
DROP TABLE IF EXISTS test_cycles CASCADE;
DROP TABLE IF EXISTS test_comparisons CASCADE;
DROP TABLE IF EXISTS test_cases CASCADE;
DROP TABLE IF EXISTS submission_validations CASCADE;
DROP TABLE IF EXISTS submission_reminders CASCADE;
DROP TABLE IF EXISTS submission_documents CASCADE;
DROP TABLE IF EXISTS sla_violation_tracking CASCADE;
DROP TABLE IF EXISTS sla_escalation_rules CASCADE;
DROP TABLE IF EXISTS sla_configurations CASCADE;
DROP TABLE IF EXISTS scoping_submissions CASCADE;
DROP TABLE IF EXISTS scoping_decision_versions CASCADE;
DROP TABLE IF EXISTS scoping_audit_log CASCADE;
DROP TABLE IF EXISTS samples CASCADE;
DROP TABLE IF EXISTS sample_validation_results CASCADE;
DROP TABLE IF EXISTS sample_validation_issues CASCADE;
DROP TABLE IF EXISTS sample_upload_history CASCADE;
DROP TABLE IF EXISTS sample_submissions CASCADE;
DROP TABLE IF EXISTS sample_submission_items CASCADE;
DROP TABLE IF EXISTS sample_sets CASCADE;
DROP TABLE IF EXISTS sample_selection_phases CASCADE;
DROP TABLE IF EXISTS sample_selection_audit_log CASCADE;
DROP TABLE IF EXISTS sample_records CASCADE;
DROP TABLE IF EXISTS sample_feedback CASCADE;
DROP TABLE IF EXISTS sample_audit_logs CASCADE;
DROP TABLE IF EXISTS sample_approval_history CASCADE;
DROP TABLE IF EXISTS roles CASCADE;
DROP TABLE IF EXISTS role_permissions CASCADE;
DROP TABLE IF EXISTS role_hierarchy CASCADE;
DROP TABLE IF EXISTS resources CASCADE;
DROP TABLE IF EXISTS resource_permissions CASCADE;
DROP TABLE IF EXISTS request_info_phases CASCADE;
DROP TABLE IF EXISTS request_info_audit_logs CASCADE;
DROP TABLE IF EXISTS request_info_audit_log CASCADE;
DROP TABLE IF EXISTS reports CASCADE;
DROP TABLE IF EXISTS report_owner_scoping_reviews CASCADE;
DROP TABLE IF EXISTS report_owner_executives CASCADE;
DROP TABLE IF EXISTS report_owner_assignments CASCADE;
DROP TABLE IF EXISTS report_owner_assignment_history CASCADE;
DROP TABLE IF EXISTS report_attributes CASCADE;
DROP TABLE IF EXISTS regulatory_data_dictionary CASCADE;
DROP TABLE IF EXISTS profiling_rules CASCADE;
DROP TABLE IF EXISTS profiling_results CASCADE;
DROP TABLE IF EXISTS metrics_phases CASCADE;
DROP TABLE IF EXISTS permissions CASCADE;
DROP TABLE IF EXISTS permission_audit_log CASCADE;
DROP TABLE IF EXISTS observations CASCADE;
DROP TABLE IF EXISTS observation_versions CASCADE;
DROP TABLE IF EXISTS observation_resolutions CASCADE;
DROP TABLE IF EXISTS observation_records CASCADE;
DROP TABLE IF EXISTS observation_management_phases CASCADE;
DROP TABLE IF EXISTS observation_management_audit_logs CASCADE;
DROP TABLE IF EXISTS observation_impact_assessments CASCADE;
DROP TABLE IF EXISTS observation_groups CASCADE;
DROP TABLE IF EXISTS observation_clarifications CASCADE;
DROP TABLE IF EXISTS observation_approvals CASCADE;
DROP TABLE IF EXISTS lobs CASCADE;
DROP TABLE IF EXISTS llm_sample_generations CASCADE;
DROP TABLE IF EXISTS llm_audit_log CASCADE;
DROP TABLE IF EXISTS individual_samples CASCADE;
DROP TABLE IF EXISTS historical_data_provider_assignments CASCADE;
DROP TABLE IF EXISTS historical_data_owner_assignments CASCADE;
DROP TABLE IF EXISTS metrics_execution CASCADE;
DROP TABLE IF EXISTS escalation_email_logs CASCADE;
DROP TABLE IF EXISTS documents CASCADE;
DROP TABLE IF EXISTS document_submissions CASCADE;
DROP TABLE IF EXISTS document_revisions CASCADE;
DROP TABLE IF EXISTS document_extractions CASCADE;
DROP TABLE IF EXISTS document_analyses CASCADE;
DROP TABLE IF EXISTS document_access_logs CASCADE;
DROP TABLE IF EXISTS database_tests CASCADE;
DROP TABLE IF EXISTS database_submissions CASCADE;
DROP TABLE IF EXISTS data_sources CASCADE;
DROP TABLE IF EXISTS data_provider_submissions CASCADE;
DROP TABLE IF EXISTS data_provider_sla_violations CASCADE;
DROP TABLE IF EXISTS data_provider_phase_audit_log CASCADE;
DROP TABLE IF EXISTS data_provider_notifications CASCADE;
DROP TABLE IF EXISTS data_provider_escalation_log CASCADE;
DROP TABLE IF EXISTS data_provider_assignments CASCADE;
DROP TABLE IF EXISTS data_profiling_rule_versions CASCADE;
DROP TABLE IF EXISTS data_profiling_phases CASCADE;
DROP TABLE IF EXISTS data_profiling_files CASCADE;
DROP TABLE IF EXISTS data_owner_sla_violations CASCADE;
DROP TABLE IF EXISTS data_owner_phase_audit_log CASCADE;
DROP TABLE IF EXISTS data_owner_notifications CASCADE;
DROP TABLE IF EXISTS data_owner_escalation_log CASCADE;
DROP TABLE IF EXISTS data_owner_assignments CASCADE;
DROP TABLE IF EXISTS cycle_reports CASCADE;
DROP TABLE IF EXISTS cdo_notifications CASCADE;
DROP TABLE IF EXISTS bulk_test_executions CASCADE;
DROP TABLE IF EXISTS audit_log CASCADE;
DROP TABLE IF EXISTS attribute_version_comparisons CASCADE;
DROP TABLE IF EXISTS attribute_version_change_logs CASCADE;
DROP TABLE IF EXISTS attribute_scoping_recommendations CASCADE;
DROP TABLE IF EXISTS attribute_scoping_recommendation_versions CASCADE;
DROP TABLE IF EXISTS attribute_profiling_scores CASCADE;
DROP TABLE IF EXISTS attribute_lob_assignments CASCADE;
DROP TABLE IF EXISTS assignment_templates CASCADE;

-- Drop and recreate custom types
DROP TYPE IF EXISTS activity_status_enum CASCADE;
DROP TYPE IF EXISTS activity_type_enum CASCADE;
DROP TYPE IF EXISTS activitystatus CASCADE;
DROP TYPE IF EXISTS activitytype CASCADE;
DROP TYPE IF EXISTS analysis_method_enum CASCADE;
DROP TYPE IF EXISTS approval_status_enum CASCADE;
DROP TYPE IF EXISTS assignment_priority_enum CASCADE;
DROP TYPE IF EXISTS assignment_status_enum CASCADE;
DROP TYPE IF EXISTS assignment_type_enum CASCADE;
DROP TYPE IF EXISTS cycle_report_status_enum CASCADE;
DROP TYPE IF EXISTS data_source_type_enum CASCADE;
DROP TYPE IF EXISTS data_type_enum CASCADE;
DROP TYPE IF EXISTS document_type_enum CASCADE;
DROP TYPE IF EXISTS escalation_level_enum CASCADE;
DROP TYPE IF EXISTS escalationlevel CASCADE;
DROP TYPE IF EXISTS impact_level_enum CASCADE;
DROP TYPE IF EXISTS impactcategoryenum CASCADE;
DROP TYPE IF EXISTS mandatory_flag_enum CASCADE;
DROP TYPE IF EXISTS observation_status_enum CASCADE;
DROP TYPE IF EXISTS observation_type_enum CASCADE;
DROP TYPE IF EXISTS observationapprovalstatusenum CASCADE;
DROP TYPE IF EXISTS observationratingenum CASCADE;
DROP TYPE IF EXISTS observationseverityenum CASCADE;
DROP TYPE IF EXISTS observationstatusenum CASCADE;
DROP TYPE IF EXISTS observationtypeenum CASCADE;
DROP TYPE IF EXISTS phase_status_enum CASCADE;
DROP TYPE IF EXISTS profilingrulestatus CASCADE;
DROP TYPE IF EXISTS profilingruletype CASCADE;
DROP TYPE IF EXISTS reportownerdecision CASCADE;
DROP TYPE IF EXISTS request_info_phase_status_enum CASCADE;
DROP TYPE IF EXISTS resolutionstatusenum CASCADE;
DROP TYPE IF EXISTS review_status_enum CASCADE;
DROP TYPE IF EXISTS sample_approval_status_enum CASCADE;
DROP TYPE IF EXISTS sample_generation_method_enum CASCADE;
DROP TYPE IF EXISTS sample_status_enum CASCADE;
DROP TYPE IF EXISTS sample_type_enum CASCADE;
DROP TYPE IF EXISTS sample_validation_status_enum CASCADE;
DROP TYPE IF EXISTS scoping_decision_enum CASCADE;
DROP TYPE IF EXISTS scoping_recommendation_enum CASCADE;
DROP TYPE IF EXISTS slatype CASCADE;
DROP TYPE IF EXISTS steptype CASCADE;
DROP TYPE IF EXISTS submission_status_enum CASCADE;
DROP TYPE IF EXISTS submission_type_enum CASCADE;
DROP TYPE IF EXISTS submissionstatus CASCADE;
DROP TYPE IF EXISTS test_case_status_enum CASCADE;
DROP TYPE IF EXISTS test_result_enum CASCADE;
DROP TYPE IF EXISTS test_status_enum CASCADE;
DROP TYPE IF EXISTS test_type_enum CASCADE;
DROP TYPE IF EXISTS testerdecision CASCADE;
DROP TYPE IF EXISTS universal_assignment_priority_enum CASCADE;
DROP TYPE IF EXISTS universal_assignment_status_enum CASCADE;
DROP TYPE IF EXISTS universal_assignment_type_enum CASCADE;
DROP TYPE IF EXISTS universal_context_type_enum CASCADE;
DROP TYPE IF EXISTS user_role_enum CASCADE;
DROP TYPE IF EXISTS validation_status_enum CASCADE;
DROP TYPE IF EXISTS version_change_type_enum CASCADE;
DROP TYPE IF EXISTS workflow_phase_enum CASCADE;
DROP TYPE IF EXISTS workflow_phase_state_enum CASCADE;
DROP TYPE IF EXISTS workflow_phase_status_enum CASCADE;
DROP TYPE IF EXISTS workflowexecutionstatus CASCADE;

-- Create custom types
CREATE TYPE activity_status_enum AS ENUM ('NOT_STARTED', 'IN_PROGRESS', 'COMPLETED', 'REVISION_REQUESTED', 'BLOCKED', 'SKIPPED');
CREATE TYPE activity_type_enum AS ENUM ('START', 'TASK', 'REVIEW', 'APPROVAL', 'COMPLETE', 'CUSTOM');
CREATE TYPE activitystatus AS ENUM ('NOT_STARTED', 'IN_PROGRESS', 'COMPLETED', 'REVISION_REQUESTED', 'BLOCKED', 'SKIPPED');
CREATE TYPE activitytype AS ENUM ('START', 'TASK', 'REVIEW', 'APPROVAL', 'COMPLETE', 'CUSTOM');
CREATE TYPE analysis_method_enum AS ENUM ('LLM Analysis', 'Database Query', 'Manual Review', 'Automated Comparison');
CREATE TYPE approval_status_enum AS ENUM ('Pending', 'Approved', 'Declined', 'Needs Revision');
CREATE TYPE assignment_priority_enum AS ENUM ('Low', 'Medium', 'High', 'Critical');
CREATE TYPE assignment_status_enum AS ENUM ('Assigned', 'In Progress', 'Completed', 'Overdue');
CREATE TYPE assignment_type_enum AS ENUM ('Data Upload Request', 'File Review', 'Documentation Review', 'Approval Required', 'Information Request', 'Phase Review');
CREATE TYPE cycle_report_status_enum AS ENUM ('Not Started', 'In Progress', 'Complete');
CREATE TYPE data_source_type_enum AS ENUM ('Document', 'Database');
CREATE TYPE data_type_enum AS ENUM ('String', 'Integer', 'Decimal', 'Date', 'DateTime', 'Boolean', 'JSON');
CREATE TYPE document_type_enum AS ENUM ('Source Document', 'Supporting Evidence', 'Data Extract', 'Query Result', 'Other');
CREATE TYPE escalation_level_enum AS ENUM ('None', 'Level 1', 'Level 2', 'Level 3');
CREATE TYPE escalationlevel AS ENUM ('LEVEL_1', 'LEVEL_2', 'LEVEL_3', 'LEVEL_4');
CREATE TYPE impact_level_enum AS ENUM ('Low', 'Medium', 'High', 'Critical');
CREATE TYPE impactcategoryenum AS ENUM ('FINANCIAL', 'REGULATORY', 'OPERATIONAL', 'REPUTATIONAL', 'STRATEGIC', 'CUSTOMER');
CREATE TYPE mandatory_flag_enum AS ENUM ('Mandatory', 'Conditional', 'Optional');
CREATE TYPE observation_status_enum AS ENUM ('Open', 'In Review', 'Approved', 'Rejected', 'Resolved');
CREATE TYPE observation_type_enum AS ENUM ('Data Quality', 'Documentation');
CREATE TYPE observationapprovalstatusenum AS ENUM ('PENDING_REVIEW', 'PENDING_REPORT_OWNER_APPROVAL', 'PENDING_DATA_EXECUTIVE_APPROVAL', 'APPROVED_BY_REPORT_OWNER', 'APPROVED_BY_DATA_EXECUTIVE', 'FULLY_APPROVED', 'REJECTED_BY_REPORT_OWNER', 'REJECTED_BY_DATA_EXECUTIVE', 'NEEDS_CLARIFICATION', 'FINALIZED');
CREATE TYPE observationratingenum AS ENUM ('HIGH', 'MEDIUM', 'LOW');
CREATE TYPE observationseverityenum AS ENUM ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFORMATIONAL');
CREATE TYPE observationstatusenum AS ENUM ('DETECTED', 'UNDER_REVIEW', 'CONFIRMED', 'DISPUTED', 'APPROVED', 'REJECTED', 'IN_REMEDIATION', 'RESOLVED', 'CLOSED');
CREATE TYPE observationtypeenum AS ENUM ('DATA_QUALITY', 'PROCESS_CONTROL', 'REGULATORY_COMPLIANCE', 'SYSTEM_CONTROL', 'DOCUMENTATION', 'CALCULATION_ERROR', 'TIMING_ISSUE', 'ACCESS_CONTROL');
CREATE TYPE phase_status_enum AS ENUM ('Not Started', 'In Progress', 'Pending Approval', 'Complete');
CREATE TYPE profilingrulestatus AS ENUM ('PENDING', 'APPROVED', 'REJECTED', 'draft', 'under_review', 'needs_revision', 'resubmitted');
CREATE TYPE profilingruletype AS ENUM ('COMPLETENESS', 'VALIDITY', 'ACCURACY', 'CONSISTENCY', 'UNIQUENESS', 'TIMELINESS', 'REGULATORY');
CREATE TYPE reportownerdecision AS ENUM ('APPROVED', 'REJECTED', 'REVISION_REQUIRED');
CREATE TYPE request_info_phase_status_enum AS ENUM ('Not Started', 'In Progress', 'Complete');
CREATE TYPE resolutionstatusenum AS ENUM ('NOT_STARTED', 'IN_PROGRESS', 'PENDING_VALIDATION', 'COMPLETED', 'FAILED', 'CANCELLED');
CREATE TYPE review_status_enum AS ENUM ('Pending', 'In Review', 'Approved', 'Rejected', 'Requires Revision');
CREATE TYPE sample_approval_status_enum AS ENUM ('Pending', 'Approved', 'Rejected', 'Needs Changes');
CREATE TYPE sample_generation_method_enum AS ENUM ('LLM Generated', 'Manual Upload', 'Hybrid');
CREATE TYPE sample_status_enum AS ENUM ('Draft', 'Pending Approval', 'Approved', 'Rejected', 'Revision Required');
CREATE TYPE sample_type_enum AS ENUM ('Population Sample', 'Targeted Sample', 'Exception Sample', 'Control Sample');
CREATE TYPE sample_validation_status_enum AS ENUM ('Valid', 'Invalid', 'Warning', 'Needs Review');
CREATE TYPE scoping_decision_enum AS ENUM ('Accept', 'Decline', 'Override');
CREATE TYPE scoping_recommendation_enum AS ENUM ('Test', 'Skip');
CREATE TYPE slatype AS ENUM ('DATA_PROVIDER_IDENTIFICATION', 'DATA_PROVIDER_RESPONSE', 'DOCUMENT_SUBMISSION', 'TESTING_COMPLETION', 'OBSERVATION_RESPONSE', 'ISSUE_RESOLUTION');
CREATE TYPE steptype AS ENUM ('PHASE', 'ACTIVITY', 'TRANSITION', 'DECISION', 'PARALLEL_BRANCH', 'SUB_WORKFLOW');
CREATE TYPE submission_status_enum AS ENUM ('Pending', 'In Progress', 'Evidence Uploaded', 'In Testing', 'Submitted', 'Validated', 'Requires Revision', 'Overdue');
CREATE TYPE submission_type_enum AS ENUM ('Document', 'Database', 'Mixed');
CREATE TYPE submissionstatus AS ENUM ('DRAFT', 'PENDING_APPROVAL', 'APPROVED', 'REJECTED', 'REVISION_REQUIRED');
CREATE TYPE test_case_status_enum AS ENUM ('Pending', 'Submitted', 'Overdue');
CREATE TYPE test_result_enum AS ENUM ('Pass', 'Fail', 'Exception', 'Inconclusive', 'Pending Review');
CREATE TYPE test_status_enum AS ENUM ('Pending', 'Running', 'Completed', 'Failed', 'Cancelled', 'Requires Review');
CREATE TYPE test_type_enum AS ENUM ('Document Based', 'Database Based', 'Hybrid');
CREATE TYPE testerdecision AS ENUM ('INCLUDE', 'EXCLUDE', 'REVIEW_REQUIRED');
CREATE TYPE universal_assignment_priority_enum AS ENUM ('Low', 'Medium', 'High', 'Critical', 'Urgent');
CREATE TYPE universal_assignment_status_enum AS ENUM ('Assigned', 'Acknowledged', 'In Progress', 'Completed', 'Approved', 'Rejected', 'Cancelled', 'Overdue', 'Escalated', 'On Hold', 'Delegated');
CREATE TYPE universal_assignment_type_enum AS ENUM ('Data Upload Request', 'File Review', 'File Approval', 'Document Review', 'Data Validation', 'Scoping Approval', 'Sample Selection Approval', 'Rule Approval', 'Observation Approval', 'Report Approval', 'Version Approval', 'Phase Review', 'Phase Approval', 'Phase Completion', 'Workflow Progression', 'LOB Assignment', 'Test Execution Review', 'Quality Review', 'Compliance Review', 'Risk Assessment', 'Information Request', 'Clarification Required', 'Additional Data Required', 'Role Assignment', 'Permission Grant', 'System Configuration');
CREATE TYPE universal_context_type_enum AS ENUM ('Test Cycle', 'Report', 'Phase', 'Attribute', 'Sample', 'Rule', 'Observation', 'File', 'System', 'User');
CREATE TYPE user_role_enum AS ENUM ('Tester', 'Test Manager', 'Report Owner', 'Report Owner Executive', 'Data Provider', 'CDO', 'Admin', 'Data Executive', 'Test Executive', 'Data Owner');
CREATE TYPE validation_status_enum AS ENUM ('Pending', 'Passed', 'Failed', 'Warning');
CREATE TYPE version_change_type_enum AS ENUM ('created', 'updated', 'approved', 'rejected', 'archived', 'restored');
CREATE TYPE workflow_phase_enum AS ENUM ('Planning', 'Data Profiling', 'Scoping', 'Data Provider ID', 'Sampling', 'Request Info', 'Testing', 'Observations', 'Sample Selection', 'Data Owner ID', 'Test Execution', 'Preparing Test Report', 'Finalize Test Report');
CREATE TYPE workflow_phase_state_enum AS ENUM ('Not Started', 'In Progress', 'Complete');
CREATE TYPE workflow_phase_status_enum AS ENUM ('On Track', 'At Risk', 'Past Due');
CREATE TYPE workflowexecutionstatus AS ENUM ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED', 'TIMED_OUT');

-- Create sequences
CREATE SEQUENCE IF NOT EXISTS attribute_lob_assignments_assignment_id_seq;
CREATE SEQUENCE IF NOT EXISTS attribute_profiling_scores_score_id_seq;
CREATE SEQUENCE IF NOT EXISTS attribute_scoping_recommendations_recommendation_id_seq;
CREATE SEQUENCE IF NOT EXISTS attribute_version_change_logs_log_id_seq;
CREATE SEQUENCE IF NOT EXISTS attribute_version_comparisons_comparison_id_seq;
CREATE SEQUENCE IF NOT EXISTS audit_log_audit_id_seq;
CREATE SEQUENCE IF NOT EXISTS bulk_test_executions_bulk_execution_id_seq;
CREATE SEQUENCE IF NOT EXISTS cdo_notifications_notification_id_seq;
CREATE SEQUENCE IF NOT EXISTS data_owner_assignments_assignment_id_seq;
CREATE SEQUENCE IF NOT EXISTS data_owner_escalation_log_email_id_seq;
CREATE SEQUENCE IF NOT EXISTS data_owner_phase_audit_log_audit_id_seq;
CREATE SEQUENCE IF NOT EXISTS data_owner_sla_violations_violation_id_seq;
CREATE SEQUENCE IF NOT EXISTS data_profiling_files_file_id_seq;
CREATE SEQUENCE IF NOT EXISTS data_profiling_phases_phase_id_seq;
CREATE SEQUENCE IF NOT EXISTS data_provider_assignments_assignment_id_seq;
CREATE SEQUENCE IF NOT EXISTS data_provider_escalation_log_email_id_seq;
CREATE SEQUENCE IF NOT EXISTS data_provider_phase_audit_log_audit_id_seq;
CREATE SEQUENCE IF NOT EXISTS data_provider_sla_violations_violation_id_seq;
CREATE SEQUENCE IF NOT EXISTS data_provider_submissions_submission_id_seq;
CREATE SEQUENCE IF NOT EXISTS data_sources_data_source_id_seq;
CREATE SEQUENCE IF NOT EXISTS database_tests_test_id_seq;
CREATE SEQUENCE IF NOT EXISTS document_access_logs_log_id_seq;
CREATE SEQUENCE IF NOT EXISTS document_analyses_analysis_id_seq;
CREATE SEQUENCE IF NOT EXISTS document_extractions_extraction_id_seq;
CREATE SEQUENCE IF NOT EXISTS document_revisions_revision_id_seq;
CREATE SEQUENCE IF NOT EXISTS documents_document_id_seq;
CREATE SEQUENCE IF NOT EXISTS escalation_email_logs_log_id_seq;
CREATE SEQUENCE IF NOT EXISTS historical_data_owner_assignments_history_id_seq;
CREATE SEQUENCE IF NOT EXISTS historical_data_provider_assignments_history_id_seq;
CREATE SEQUENCE IF NOT EXISTS individual_samples_id_seq;
CREATE SEQUENCE IF NOT EXISTS llm_audit_log_log_id_seq;
CREATE SEQUENCE IF NOT EXISTS lobs_lob_id_seq;
CREATE SEQUENCE IF NOT EXISTS observation_approvals_approval_id_seq;
CREATE SEQUENCE IF NOT EXISTS observation_clarifications_clarification_id_seq;
CREATE SEQUENCE IF NOT EXISTS observation_groups_group_id_seq;
CREATE SEQUENCE IF NOT EXISTS observation_impact_assessments_assessment_id_seq;
CREATE SEQUENCE IF NOT EXISTS observation_management_audit_logs_log_id_seq;
CREATE SEQUENCE IF NOT EXISTS observation_records_observation_id_seq;
CREATE SEQUENCE IF NOT EXISTS observation_resolutions_resolution_id_seq;
CREATE SEQUENCE IF NOT EXISTS observations_observation_id_seq;
CREATE SEQUENCE IF NOT EXISTS permission_audit_log_audit_id_seq;
CREATE SEQUENCE IF NOT EXISTS permissions_permission_id_seq;
CREATE SEQUENCE IF NOT EXISTS profiling_results_result_id_seq;
CREATE SEQUENCE IF NOT EXISTS profiling_rules_rule_id_seq;
CREATE SEQUENCE IF NOT EXISTS regulatory_data_dictionary_dict_id_seq;
CREATE SEQUENCE IF NOT EXISTS report_attributes_attribute_id_seq;
CREATE SEQUENCE IF NOT EXISTS report_owner_assignment_history_history_id_seq;
CREATE SEQUENCE IF NOT EXISTS report_owner_assignments_assignment_id_seq;
CREATE SEQUENCE IF NOT EXISTS report_owner_scoping_reviews_review_id_seq;
CREATE SEQUENCE IF NOT EXISTS reports_report_id_seq;
CREATE SEQUENCE IF NOT EXISTS request_info_audit_logs_log_id_seq;
CREATE SEQUENCE IF NOT EXISTS resource_permissions_resource_permission_id_seq;
CREATE SEQUENCE IF NOT EXISTS resources_resource_id_seq;
CREATE SEQUENCE IF NOT EXISTS roles_role_id_seq;
CREATE SEQUENCE IF NOT EXISTS sample_audit_logs_id_seq;
CREATE SEQUENCE IF NOT EXISTS sample_feedback_id_seq;
CREATE SEQUENCE IF NOT EXISTS sample_selection_phases_phase_id_seq;
CREATE SEQUENCE IF NOT EXISTS sample_submission_items_id_seq;
CREATE SEQUENCE IF NOT EXISTS sample_submissions_id_seq;
CREATE SEQUENCE IF NOT EXISTS samples_sample_id_seq;
CREATE SEQUENCE IF NOT EXISTS scoping_audit_log_audit_id_seq;
CREATE SEQUENCE IF NOT EXISTS scoping_submissions_submission_id_seq;
CREATE SEQUENCE IF NOT EXISTS sla_configurations_sla_config_id_seq;
CREATE SEQUENCE IF NOT EXISTS sla_escalation_rules_escalation_rule_id_seq;
CREATE SEQUENCE IF NOT EXISTS sla_violation_tracking_violation_id_seq;
CREATE SEQUENCE IF NOT EXISTS submission_documents_document_id_seq;
CREATE SEQUENCE IF NOT EXISTS test_comparisons_comparison_id_seq;
CREATE SEQUENCE IF NOT EXISTS test_cycles_cycle_id_seq;
CREATE SEQUENCE IF NOT EXISTS test_execution_audit_logs_log_id_seq;
CREATE SEQUENCE IF NOT EXISTS test_executions_execution_id_seq;
CREATE SEQUENCE IF NOT EXISTS test_report_sections_section_id_seq;
CREATE SEQUENCE IF NOT EXISTS test_result_reviews_review_id_seq;
CREATE SEQUENCE IF NOT EXISTS tester_scoping_decisions_decision_id_seq;
CREATE SEQUENCE IF NOT EXISTS testing_execution_audit_logs_log_id_seq;
CREATE SEQUENCE IF NOT EXISTS testing_test_executions_execution_id_seq;
CREATE SEQUENCE IF NOT EXISTS universal_assignment_history_history_id_seq;
CREATE SEQUENCE IF NOT EXISTS users_user_id_seq;
CREATE SEQUENCE IF NOT EXISTS workflow_activities_activity_id_seq;
CREATE SEQUENCE IF NOT EXISTS workflow_activity_dependencies_dependency_id_seq;
CREATE SEQUENCE IF NOT EXISTS workflow_activity_history_history_id_seq;
CREATE SEQUENCE IF NOT EXISTS workflow_activity_templates_template_id_seq;
CREATE SEQUENCE IF NOT EXISTS workflow_alerts_alert_id_seq;
CREATE SEQUENCE IF NOT EXISTS workflow_metrics_metric_id_seq;
CREATE SEQUENCE IF NOT EXISTS workflow_phases_phase_id_seq;

-- Create tables

-- Table: assignment_templates
CREATE TABLE assignment_templates (
    template_id character varying(36) NOT NULL,
    template_name character varying(255) NOT NULL,
    assignment_type universal_assignment_type_enum NOT NULL,
    from_role character varying(50) NOT NULL,
    to_role character varying(50) NOT NULL,
    title_template character varying(255) NOT NULL,
    description_template text,
    task_instructions_template text,
    default_priority universal_assignment_priority_enum NOT NULL,
    default_due_days integer,
    requires_approval boolean NOT NULL,
    approval_role character varying(50),
    context_type universal_context_type_enum NOT NULL,
    workflow_step character varying(100),
    is_active boolean NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    PRIMARY KEY (template_id)
);

-- Table: attribute_lob_assignments
CREATE TABLE attribute_lob_assignments (
    assignment_id integer NOT NULL DEFAULT nextval('attribute_lob_assignments_assignment_id_seq'::regclass),
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    attribute_id integer NOT NULL,
    lob_id integer NOT NULL,
    assigned_by integer NOT NULL,
    assigned_at timestamp with time zone NOT NULL,
    assignment_rationale text,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (assignment_id)
);

-- Table: attribute_profiling_scores
CREATE TABLE cycle_report_data_profiling_attribute_scores (
    score_id integer NOT NULL DEFAULT nextval('attribute_profiling_scores_score_id_seq'::regclass),
    phase_id integer NOT NULL,
    attribute_id integer NOT NULL,
    overall_quality_score double precision,
    completeness_score double precision,
    validity_score double precision,
    accuracy_score double precision,
    consistency_score double precision,
    uniqueness_score double precision,
    total_rules_executed integer,
    rules_passed integer,
    rules_failed integer,
    total_values integer,
    null_count integer,
    unique_count integer,
    data_type_detected character varying(50),
    pattern_detected character varying(255),
    distribution_type character varying(50),
    has_anomalies boolean,
    anomaly_count integer,
    anomaly_types json,
    testing_recommendation text,
    risk_assessment text,
    calculated_at timestamp without time zone NOT NULL,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (score_id)
);

-- Table: attribute_scoping_recommendation_versions
CREATE TABLE cycle_report_scoping_attribute_recommendation_versions (
    recommendation_version_id uuid NOT NULL DEFAULT gen_random_uuid(),
    recommendation_id uuid NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    attribute_id integer NOT NULL,
    llm_recommendation boolean NOT NULL,
    llm_confidence_score double precision,
    llm_reasoning text,
    llm_provider character varying(50),
    tester_decision boolean,
    tester_reasoning text,
    decision_timestamp timestamp with time zone,
    is_override boolean,
    override_justification text,
    risk_indicators jsonb,
    testing_complexity character varying(20),
    estimated_effort_hours double precision,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    version_number integer NOT NULL,
    is_latest_version boolean NOT NULL,
    version_created_at timestamp with time zone,
    version_created_by character varying(255),
    version_notes text,
    change_reason character varying(500),
    parent_version_id uuid,
    version_status character varying(50),
    approved_version_id uuid,
    approved_at timestamp with time zone,
    approved_by character varying(255),
    PRIMARY KEY (recommendation_version_id)
);

-- Table: attribute_scoping_recommendations
CREATE TABLE cycle_report_scoping_attribute_recommendations (
    recommendation_id integer NOT NULL DEFAULT nextval('attribute_scoping_recommendations_recommendation_id_seq'::regclass),
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    attribute_id integer NOT NULL,
    recommendation_score double precision NOT NULL,
    recommendation scoping_recommendation_enum NOT NULL,
    rationale text NOT NULL,
    expected_source_documents json NOT NULL,
    search_keywords json NOT NULL,
    other_reports_using json,
    risk_factors json,
    priority_level character varying(20) NOT NULL,
    llm_provider character varying(50) NOT NULL,
    processing_time_ms integer NOT NULL,
    llm_request_payload json,
    llm_response_payload json,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (recommendation_id)
);

-- Table: attribute_version_change_logs
CREATE TABLE attribute_version_change_logs (
    log_id integer NOT NULL DEFAULT nextval('attribute_version_change_logs_log_id_seq'::regclass),
    attribute_id integer NOT NULL,
    change_type version_change_type_enum NOT NULL,
    version_number integer NOT NULL,
    change_notes text,
    changed_at timestamp without time zone NOT NULL,
    changed_by integer NOT NULL,
    field_changes text,
    impact_assessment text,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (log_id)
);

-- Table: attribute_version_comparisons
CREATE TABLE attribute_version_comparisons (
    comparison_id integer NOT NULL DEFAULT nextval('attribute_version_comparisons_comparison_id_seq'::regclass),
    version_a_id integer NOT NULL,
    version_b_id integer NOT NULL,
    differences_found integer NOT NULL,
    comparison_summary text,
    impact_score double precision,
    compared_at timestamp without time zone NOT NULL,
    compared_by integer NOT NULL,
    comparison_notes text,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (comparison_id)
);

-- Table: audit_log
CREATE TABLE audit_log (
    audit_id integer NOT NULL DEFAULT nextval('audit_log_audit_id_seq'::regclass),
    user_id integer,
    action character varying(100) NOT NULL,
    table_name character varying(100),
    record_id integer,
    old_values jsonb,
    new_values jsonb,
    timestamp timestamp with time zone NOT NULL,
    session_id character varying(255),
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (audit_id)
);

-- Table: bulk_test_executions
CREATE TABLE bulk_test_executions (
    bulk_execution_id integer NOT NULL DEFAULT nextval('bulk_test_executions_bulk_execution_id_seq'::regclass),
    phase_id character varying(36) NOT NULL,
    execution_mode character varying(20) NOT NULL,
    max_concurrent_tests integer NOT NULL,
    total_tests integer NOT NULL,
    tests_started integer NOT NULL,
    tests_completed integer NOT NULL,
    tests_failed integer NOT NULL,
    execution_ids jsonb NOT NULL,
    status character varying(50) NOT NULL,
    started_at timestamp with time zone,
    completed_at timestamp with time zone,
    processing_time_ms integer,
    initiated_by integer NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (bulk_execution_id)
);

-- Table: cdo_notifications
CREATE TABLE cdo_notifications (
    notification_id integer NOT NULL DEFAULT nextval('cdo_notifications_notification_id_seq'::regclass),
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    cdo_id integer NOT NULL,
    lob_id integer NOT NULL,
    notification_sent_at timestamp with time zone NOT NULL,
    assignment_deadline timestamp with time zone NOT NULL,
    sla_hours integer NOT NULL,
    notification_data jsonb,
    responded_at timestamp with time zone,
    is_complete boolean NOT NULL,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (notification_id)
);

-- Table: cycle_reports
CREATE TABLE cycle_reports (
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    tester_id integer,
    status cycle_report_status_enum NOT NULL,
    started_at timestamp with time zone,
    completed_at timestamp with time zone,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    workflow_id character varying(255),
    PRIMARY KEY (cycle_id, report_id)
);

-- Table: data_owner_assignments
CREATE TABLE data_owner_assignments (
    assignment_id integer NOT NULL DEFAULT nextval('data_owner_assignments_assignment_id_seq'::regclass),
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    attribute_id integer,
    lob_id integer,
    cdo_id integer,
    data_owner_id integer,
    assigned_by integer NOT NULL,
    assigned_at timestamp with time zone NOT NULL,
    status assignment_status_enum NOT NULL,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (assignment_id)
);

-- Table: data_owner_escalation_log
CREATE TABLE data_owner_escalation_log (
    email_id integer NOT NULL DEFAULT nextval('data_owner_escalation_log_email_id_seq'::regclass),
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    violation_ids jsonb NOT NULL,
    escalation_level escalation_level_enum NOT NULL,
    sent_by integer NOT NULL,
    sent_to jsonb NOT NULL,
    cc_recipients jsonb,
    email_subject character varying(255) NOT NULL,
    email_body text NOT NULL,
    sent_at timestamp with time zone NOT NULL,
    delivery_status character varying(50) NOT NULL,
    custom_message text,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (email_id)
);

-- Table: data_owner_notifications
CREATE TABLE data_owner_notifications (
    notification_id character varying(36) NOT NULL,
    phase_id character varying(36) NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    data_owner_id integer NOT NULL,
    assigned_attributes jsonb NOT NULL,
    sample_count integer NOT NULL,
    submission_deadline timestamp with time zone NOT NULL,
    portal_access_url character varying(500) NOT NULL,
    custom_instructions text,
    notification_sent_at timestamp with time zone,
    first_access_at timestamp with time zone,
    last_access_at timestamp with time zone,
    access_count integer NOT NULL,
    is_acknowledged boolean NOT NULL,
    acknowledged_at timestamp with time zone,
    status submission_status_enum NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    PRIMARY KEY (notification_id)
);

-- Table: data_owner_phase_audit_log
CREATE TABLE data_owner_phase_audit_log (
    audit_id integer NOT NULL DEFAULT nextval('data_owner_phase_audit_log_audit_id_seq'::regclass),
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    action character varying(100) NOT NULL,
    entity_type character varying(50) NOT NULL,
    entity_id integer,
    performed_by integer NOT NULL,
    performed_at timestamp with time zone NOT NULL,
    old_values jsonb,
    new_values jsonb,
    notes text,
    ip_address character varying(45),
    user_agent text,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (audit_id)
);

-- Table: data_owner_sla_violations
CREATE TABLE data_owner_sla_violations (
    violation_id integer NOT NULL DEFAULT nextval('data_owner_sla_violations_violation_id_seq'::regclass),
    assignment_id integer NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    attribute_id integer NOT NULL,
    cdo_id integer NOT NULL,
    violation_detected_at timestamp with time zone NOT NULL,
    original_deadline timestamp with time zone NOT NULL,
    hours_overdue double precision NOT NULL,
    escalation_level escalation_level_enum NOT NULL,
    last_escalation_at timestamp with time zone,
    is_resolved boolean NOT NULL,
    resolved_at timestamp with time zone,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (violation_id)
);

-- Table: data_profiling_files
CREATE TABLE cycle_report_data_profiling_files (
    file_id integer NOT NULL DEFAULT nextval('data_profiling_files_file_id_seq'::regclass),
    phase_id integer NOT NULL,
    file_name character varying(255) NOT NULL,
    file_path text NOT NULL,
    file_size integer NOT NULL,
    file_format character varying(50) NOT NULL,
    delimiter character varying(10),
    row_count integer,
    column_count integer,
    columns_metadata json,
    is_validated boolean,
    validation_errors json,
    missing_attributes json,
    uploaded_by integer NOT NULL,
    uploaded_at timestamp without time zone NOT NULL,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (file_id)
);

-- Table: data_profiling_phases
CREATE TABLE data_profiling_phases (
    phase_id integer NOT NULL DEFAULT nextval('data_profiling_phases_phase_id_seq'::regclass),
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    status character varying(50) NOT NULL,
    data_requested_at timestamp without time zone,
    data_received_at timestamp without time zone,
    rules_generated_at timestamp without time zone,
    profiling_executed_at timestamp without time zone,
    phase_completed_at timestamp without time zone,
    started_by integer,
    data_requested_by integer,
    completed_by integer,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (phase_id)
);

-- Table: data_profiling_rule_versions
CREATE TABLE cycle_report_data_profiling_rule_versions (
    rule_version_id uuid NOT NULL DEFAULT gen_random_uuid(),
    rule_id uuid NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    attribute_id integer NOT NULL,
    rule_type character varying(50) NOT NULL,
    rule_definition jsonb NOT NULL,
    rule_description text,
    threshold_value double precision,
    threshold_type character varying(20),
    execution_status character varying(50),
    execution_results jsonb,
    issues_found integer,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    version_number integer NOT NULL,
    is_latest_version boolean NOT NULL,
    version_created_at timestamp with time zone,
    version_created_by character varying(255),
    version_notes text,
    change_reason character varying(500),
    parent_version_id uuid,
    version_status character varying(50),
    approved_version_id uuid,
    approved_at timestamp with time zone,
    approved_by character varying(255),
    PRIMARY KEY (rule_version_id)
);

-- Table: data_provider_assignments
CREATE TABLE data_provider_assignments (
    assignment_id integer NOT NULL DEFAULT nextval('data_provider_assignments_assignment_id_seq'::regclass),
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    attribute_id integer,
    lob_id integer,
    data_provider_id integer,
    assigned_by integer NOT NULL,
    assigned_at timestamp with time zone NOT NULL,
    status assignment_status_enum NOT NULL,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    cdo_id integer,
    PRIMARY KEY (assignment_id)
);

-- Table: data_provider_escalation_log
CREATE TABLE data_provider_escalation_log (
    email_id integer NOT NULL DEFAULT nextval('data_provider_escalation_log_email_id_seq'::regclass),
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    violation_ids jsonb NOT NULL,
    escalation_level escalation_level_enum NOT NULL,
    sent_by integer NOT NULL,
    sent_to jsonb NOT NULL,
    cc_recipients jsonb,
    email_subject character varying(255) NOT NULL,
    email_body text NOT NULL,
    sent_at timestamp with time zone NOT NULL,
    delivery_status character varying(50) NOT NULL,
    custom_message text,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (email_id)
);

-- Table: data_provider_notifications
CREATE TABLE data_provider_notifications (
    notification_id character varying(36) NOT NULL,
    phase_id character varying(36) NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    data_provider_id integer NOT NULL,
    assigned_attributes jsonb NOT NULL,
    sample_count integer NOT NULL,
    submission_deadline timestamp with time zone NOT NULL,
    portal_access_url character varying(500) NOT NULL,
    custom_instructions text,
    notification_sent_at timestamp with time zone,
    first_access_at timestamp with time zone,
    last_access_at timestamp with time zone,
    access_count integer NOT NULL,
    is_acknowledged boolean NOT NULL,
    acknowledged_at timestamp with time zone,
    status submission_status_enum NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    PRIMARY KEY (notification_id)
);

-- Table: data_provider_phase_audit_log
CREATE TABLE data_provider_phase_audit_log (
    audit_id integer NOT NULL DEFAULT nextval('data_provider_phase_audit_log_audit_id_seq'::regclass),
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    action character varying(100) NOT NULL,
    entity_type character varying(50) NOT NULL,
    entity_id integer,
    performed_by integer NOT NULL,
    performed_at timestamp with time zone NOT NULL,
    old_values jsonb,
    new_values jsonb,
    notes text,
    ip_address character varying(45),
    user_agent text,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (audit_id)
);

-- Table: data_provider_sla_violations
CREATE TABLE data_provider_sla_violations (
    violation_id integer NOT NULL DEFAULT nextval('data_provider_sla_violations_violation_id_seq'::regclass),
    assignment_id integer NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    attribute_id integer NOT NULL,
    cdo_id integer NOT NULL,
    violation_detected_at timestamp with time zone NOT NULL,
    original_deadline timestamp with time zone NOT NULL,
    hours_overdue double precision NOT NULL,
    escalation_level escalation_level_enum NOT NULL,
    last_escalation_at timestamp with time zone,
    is_resolved boolean NOT NULL,
    resolved_at timestamp with time zone,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (violation_id)
);

-- Table: data_provider_submissions
CREATE TABLE data_provider_submissions (
    submission_id integer NOT NULL DEFAULT nextval('data_provider_submissions_submission_id_seq'::regclass),
    phase_id character varying(36) NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    data_provider_id integer NOT NULL,
    attribute_id integer NOT NULL,
    sample_record_id character varying(100) NOT NULL,
    submission_type submission_type_enum NOT NULL,
    status submission_status_enum NOT NULL,
    document_ids jsonb,
    database_submission_id character varying(36),
    expected_value character varying(500),
    confidence_level character varying(20),
    notes text,
    validation_status validation_status_enum NOT NULL,
    validation_messages jsonb,
    validation_score double precision,
    submitted_at timestamp with time zone,
    validated_at timestamp with time zone,
    last_updated_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (submission_id)
);

-- Table: data_sources
CREATE TABLE data_sources (
    data_source_id integer NOT NULL DEFAULT nextval('data_sources_data_source_id_seq'::regclass),
    data_source_name character varying(255) NOT NULL,
    database_type character varying(50) NOT NULL,
    database_url text NOT NULL,
    database_user character varying(255) NOT NULL,
    database_password_encrypted text NOT NULL,
    is_active boolean NOT NULL,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    description text,
    PRIMARY KEY (data_source_id)
);

-- Table: database_submissions
CREATE TABLE database_submissions (
    db_submission_id character varying(36) NOT NULL,
    phase_id character varying(36) NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    data_provider_id integer NOT NULL,
    attribute_id integer NOT NULL,
    sample_record_id character varying(100) NOT NULL,
    database_name character varying(255) NOT NULL,
    table_name character varying(255) NOT NULL,
    column_name character varying(255) NOT NULL,
    primary_key_column character varying(255) NOT NULL,
    primary_key_value character varying(255) NOT NULL,
    query_filter text,
    connection_details jsonb,
    expected_value character varying(500),
    confidence_level character varying(20),
    notes text,
    validation_status validation_status_enum NOT NULL,
    validation_messages jsonb,
    connectivity_test_passed boolean,
    connectivity_test_at timestamp with time zone,
    submitted_at timestamp with time zone NOT NULL,
    validated_at timestamp with time zone,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (db_submission_id)
);

-- Table: database_tests
CREATE TABLE cycle_report_test_execution_database_tests (
    test_id integer NOT NULL DEFAULT nextval('database_tests_test_id_seq'::regclass),
    database_submission_id character varying(36) NOT NULL,
    sample_record_id character varying(100) NOT NULL,
    attribute_id integer NOT NULL,
    test_query text,
    connection_timeout integer NOT NULL,
    query_timeout integer NOT NULL,
    connection_successful boolean NOT NULL,
    query_successful boolean NOT NULL,
    retrieved_value text,
    record_count integer,
    execution_time_ms integer NOT NULL,
    error_message text,
    connection_string_hash character varying(64),
    database_version character varying(100),
    actual_query_executed text,
    query_plan text,
    tested_at timestamp with time zone NOT NULL,
    tested_by integer,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (test_id)
);

-- Table: document_access_logs
CREATE TABLE document_access_logs (
    log_id integer NOT NULL DEFAULT nextval('document_access_logs_log_id_seq'::regclass),
    document_id integer NOT NULL,
    user_id integer NOT NULL,
    access_type character varying(20) NOT NULL,
    accessed_at timestamp without time zone NOT NULL,
    ip_address character varying(45),
    user_agent text,
    session_id character varying(100),
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (log_id)
);

-- Table: document_analyses
CREATE TABLE cycle_report_test_execution_document_analyses (
    analysis_id integer NOT NULL DEFAULT nextval('document_analyses_analysis_id_seq'::regclass),
    submission_document_id integer NOT NULL,
    sample_record_id character varying(100) NOT NULL,
    attribute_id integer NOT NULL,
    analysis_prompt text,
    expected_value character varying(500),
    confidence_threshold double precision NOT NULL,
    extracted_value text,
    confidence_score double precision NOT NULL,
    analysis_rationale text NOT NULL,
    matches_expected boolean,
    validation_notes jsonb,
    llm_model_used character varying(100),
    llm_tokens_used integer,
    llm_response_raw text,
    analyzed_at timestamp with time zone NOT NULL,
    analysis_duration_ms integer NOT NULL,
    analyzed_by integer,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (analysis_id)
);

-- Table: document_extractions
CREATE TABLE document_extractions (
    extraction_id integer NOT NULL DEFAULT nextval('document_extractions_extraction_id_seq'::regclass),
    document_id integer NOT NULL,
    attribute_name character varying(255) NOT NULL,
    extracted_value text,
    confidence_score integer,
    extraction_method character varying(50),
    source_location text,
    supporting_context text,
    data_quality_flags json,
    alternative_values json,
    is_validated boolean NOT NULL,
    validated_by_user_id integer,
    validation_notes text,
    extracted_at timestamp without time zone NOT NULL,
    llm_provider character varying(50),
    llm_model character varying(100),
    processing_time_ms integer,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (extraction_id)
);

-- Table: document_revisions
CREATE TABLE document_revisions (
    revision_id integer NOT NULL DEFAULT nextval('document_revisions_revision_id_seq'::regclass),
    test_case_id character varying(36) NOT NULL,
    document_id integer NOT NULL,
    revision_number integer NOT NULL,
    revision_reason text NOT NULL,
    requested_by integer NOT NULL,
    requested_at timestamp without time zone,
    uploaded_by integer,
    uploaded_at timestamp without time zone,
    upload_notes text,
    previous_document_id integer,
    status character varying,
    reviewed_by integer,
    reviewed_at timestamp without time zone,
    review_notes text,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (revision_id)
);

-- Table: document_submissions
CREATE TABLE document_submissions (
    submission_id character varying(36) NOT NULL,
    test_case_id character varying(36) NOT NULL,
    data_provider_id integer NOT NULL,
    original_filename character varying(255) NOT NULL,
    stored_filename character varying(255) NOT NULL,
    file_path character varying(500) NOT NULL,
    file_size_bytes integer NOT NULL,
    document_type document_type_enum NOT NULL,
    mime_type character varying(100) NOT NULL,
    submission_notes text,
    submitted_at timestamp with time zone NOT NULL,
    is_valid boolean NOT NULL,
    validation_notes text,
    validated_by integer,
    validated_at timestamp with time zone,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    revision_number integer NOT NULL DEFAULT 1,
    parent_submission_id character varying(36),
    is_current boolean NOT NULL DEFAULT true,
    notes text,
    data_owner_id integer,
    PRIMARY KEY (submission_id)
);

-- Table: documents
CREATE TABLE documents (
    document_id integer NOT NULL DEFAULT nextval('documents_document_id_seq'::regclass),
    document_name character varying(255) NOT NULL,
    document_type character varying(50) NOT NULL,
    file_path text NOT NULL,
    file_size bigint NOT NULL,
    mime_type character varying(100) NOT NULL,
    report_id integer NOT NULL,
    cycle_id integer,
    uploaded_by_user_id integer NOT NULL,
    status character varying(20) NOT NULL,
    processing_notes text,
    file_hash character varying(64) NOT NULL,
    is_encrypted boolean NOT NULL,
    encryption_key_id character varying(100),
    document_metadata json,
    tags json,
    description text,
    business_date timestamp without time zone,
    parent_document_id integer,
    version integer NOT NULL,
    is_latest_version boolean NOT NULL,
    is_confidential boolean NOT NULL,
    access_level character varying(20) NOT NULL,
    uploaded_at timestamp without time zone NOT NULL,
    last_accessed_at timestamp without time zone,
    expires_at timestamp without time zone,
    is_archived boolean NOT NULL,
    archived_at timestamp without time zone,
    retention_date timestamp without time zone,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (document_id)
);

-- Table: escalation_email_logs
CREATE TABLE escalation_email_logs (
    log_id integer NOT NULL DEFAULT nextval('escalation_email_logs_log_id_seq'::regclass),
    sla_violation_id integer NOT NULL,
    escalation_rule_id integer NOT NULL,
    report_id integer NOT NULL,
    sent_at timestamp without time zone NOT NULL,
    sent_to_emails text NOT NULL,
    email_subject character varying(255) NOT NULL,
    email_body text NOT NULL,
    delivery_status character varying(50) NOT NULL,
    delivery_error text,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (log_id)
);

-- Table: metrics_execution
CREATE TABLE metrics_execution (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    phase_name character varying(50) NOT NULL,
    activity_name character varying(100) NOT NULL,
    user_id character varying(255),
    start_time timestamp with time zone NOT NULL,
    end_time timestamp with time zone,
    duration_minutes double precision,
    status character varying(50) NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (id)
);

-- Table: historical_data_owner_assignments
CREATE TABLE historical_data_owner_assignments (
    history_id integer NOT NULL DEFAULT nextval('historical_data_owner_assignments_history_id_seq'::regclass),
    report_name character varying(255) NOT NULL,
    attribute_name character varying(255) NOT NULL,
    data_owner_id integer NOT NULL,
    assigned_by integer NOT NULL,
    cycle_id integer NOT NULL,
    assigned_at timestamp with time zone NOT NULL,
    completion_status character varying(50) NOT NULL,
    completion_time_hours double precision,
    success_rating double precision,
    notes text,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (history_id)
);

-- Table: historical_data_provider_assignments
CREATE TABLE historical_data_provider_assignments (
    history_id integer NOT NULL DEFAULT nextval('historical_data_provider_assignments_history_id_seq'::regclass),
    report_name character varying(255) NOT NULL,
    attribute_name character varying(255) NOT NULL,
    data_provider_id integer NOT NULL,
    assigned_by integer NOT NULL,
    cycle_id integer NOT NULL,
    assigned_at timestamp with time zone NOT NULL,
    completion_status character varying(50) NOT NULL,
    completion_time_hours double precision,
    success_rating double precision,
    notes text,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (history_id)
);

-- Table: individual_samples
CREATE TABLE individual_samples (
    id integer NOT NULL DEFAULT nextval('individual_samples_id_seq'::regclass),
    sample_id character varying,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    primary_key_value character varying NOT NULL,
    sample_data json NOT NULL,
    generation_method character varying NOT NULL,
    generated_at timestamp with time zone DEFAULT now(),
    generated_by_user_id integer,
    tester_decision testerdecision,
    tester_decision_date timestamp with time zone,
    tester_decision_by_user_id integer,
    tester_notes text,
    report_owner_decision reportownerdecision,
    report_owner_feedback text,
    is_submitted boolean,
    submission_id integer,
    version_number integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    PRIMARY KEY (id)
);

-- Table: llm_audit_log
CREATE TABLE llm_audit_log (
    log_id integer NOT NULL DEFAULT nextval('llm_audit_log_log_id_seq'::regclass),
    cycle_id integer,
    report_id integer,
    llm_provider character varying(50) NOT NULL,
    prompt_template character varying(255) NOT NULL,
    request_payload jsonb NOT NULL,
    response_payload jsonb NOT NULL,
    execution_time_ms integer,
    token_usage jsonb,
    executed_at timestamp with time zone NOT NULL,
    executed_by integer NOT NULL,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (log_id)
);

-- Table: llm_sample_generations
CREATE TABLE llm_sample_generations (
    generation_id character varying(36) NOT NULL,
    set_id character varying(36) NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    requested_sample_size integer NOT NULL,
    actual_samples_generated integer NOT NULL,
    generation_prompt text,
    selection_criteria jsonb NOT NULL,
    risk_focus_areas jsonb,
    exclude_criteria jsonb,
    include_edge_cases boolean NOT NULL,
    randomization_seed integer,
    llm_model_used character varying(100),
    generation_rationale text NOT NULL,
    confidence_score double precision NOT NULL,
    risk_coverage jsonb,
    estimated_testing_time integer,
    llm_metadata jsonb,
    generated_by integer NOT NULL,
    generated_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (generation_id)
);

-- Table: lobs
CREATE TABLE lobs (
    lob_id integer NOT NULL DEFAULT nextval('lobs_lob_id_seq'::regclass),
    lob_name character varying(255) NOT NULL,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (lob_id)
);

-- Table: observation_approvals
CREATE TABLE cycle_report_observation_mgmt_approvals (
    approval_id integer NOT NULL DEFAULT nextval('observation_approvals_approval_id_seq'::regclass),
    observation_id integer NOT NULL,
    approval_status character varying NOT NULL,
    approval_level character varying NOT NULL,
    approver_comments text,
    approval_rationale text,
    severity_assessment character varying,
    impact_validation boolean,
    evidence_sufficiency boolean,
    regulatory_significance boolean,
    requires_escalation boolean,
    recommended_action character varying,
    priority_level character varying,
    estimated_effort character varying,
    target_resolution_date timestamp without time zone,
    approval_criteria_met json,
    approval_checklist json,
    conditional_approval boolean,
    conditions json,
    approved_by integer,
    approved_at timestamp without time zone,
    escalated_to integer,
    escalated_at timestamp without time zone,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (approval_id)
);

-- Table: observation_clarifications
CREATE TABLE observation_clarifications (
    clarification_id integer NOT NULL DEFAULT nextval('observation_clarifications_clarification_id_seq'::regclass),
    group_id integer NOT NULL,
    clarification_text text NOT NULL,
    supporting_documents json,
    requested_by_role character varying NOT NULL,
    requested_by_user_id integer NOT NULL,
    requested_at timestamp without time zone,
    response_text text,
    response_documents json,
    responded_by integer,
    responded_at timestamp without time zone,
    status character varying,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (clarification_id)
);

-- Table: observation_groups
CREATE TABLE observation_groups (
    group_id integer NOT NULL DEFAULT nextval('observation_groups_group_id_seq'::regclass),
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    attribute_id integer NOT NULL,
    issue_type character varying NOT NULL,
    first_detected_at timestamp without time zone,
    last_updated_at timestamp without time zone,
    total_test_cases integer,
    total_samples integer,
    rating observationratingenum,
    approval_status observationapprovalstatusenum,
    report_owner_approved boolean,
    report_owner_approved_by integer,
    report_owner_approved_at timestamp without time zone,
    report_owner_comments text,
    data_executive_approved boolean,
    data_executive_approved_by integer,
    data_executive_approved_at timestamp without time zone,
    data_executive_comments text,
    finalized boolean,
    finalized_by integer,
    finalized_at timestamp without time zone,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    UNIQUE (cycle_id, report_id, attribute_id, issue_type),
    PRIMARY KEY (group_id)
);

-- Table: observation_impact_assessments
CREATE TABLE cycle_report_observation_mgmt_impact_assessments (
    assessment_id integer NOT NULL DEFAULT nextval('observation_impact_assessments_assessment_id_seq'::regclass),
    observation_id integer NOT NULL,
    impact_category impactcategoryenum NOT NULL,
    impact_severity character varying NOT NULL,
    impact_likelihood character varying NOT NULL,
    impact_score double precision NOT NULL,
    financial_impact_min double precision,
    financial_impact_max double precision,
    financial_impact_currency character varying,
    regulatory_requirements_affected json,
    regulatory_deadlines json,
    potential_penalties double precision,
    process_disruption_level character varying,
    system_availability_impact character varying,
    resource_requirements json,
    resolution_time_estimate integer,
    business_disruption_duration integer,
    assessment_method character varying,
    assessment_confidence double precision,
    assessment_rationale text,
    assessment_assumptions json,
    assessed_by integer,
    assessed_at timestamp without time zone,
    reviewed_by integer,
    reviewed_at timestamp without time zone,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (assessment_id)
);

-- Table: observation_management_audit_logs
CREATE TABLE cycle_report_observation_mgmt_audit_logss (
    log_id integer NOT NULL DEFAULT nextval('observation_management_audit_logs_log_id_seq'::regclass),
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    phase_id character varying,
    observation_id integer,
    action character varying NOT NULL,
    entity_type character varying NOT NULL,
    entity_id character varying,
    old_values json,
    new_values json,
    changes_summary text,
    performed_by integer NOT NULL,
    performed_at timestamp without time zone,
    user_role character varying,
    ip_address character varying,
    user_agent character varying,
    session_id character varying,
    notes text,
    execution_time_ms integer,
    business_justification text,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    source_test_execution_id integer,
    PRIMARY KEY (log_id)
);

-- Table: observation_management_phases
CREATE TABLE observation_management_phases (
    phase_id character varying NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    phase_status character varying NOT NULL,
    planned_start_date timestamp without time zone,
    planned_end_date timestamp without time zone,
    observation_deadline timestamp without time zone NOT NULL,
    started_at timestamp without time zone,
    completed_at timestamp without time zone,
    observation_strategy text,
    detection_criteria json,
    approval_threshold double precision,
    instructions text,
    notes text,
    started_by integer,
    completed_by integer,
    assigned_testers json,
    total_observations integer,
    auto_detected_observations integer,
    manual_observations integer,
    approved_observations integer,
    rejected_observations integer,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (phase_id)
);

-- Table: observation_records
CREATE TABLE cycle_report_observation_mgmt_observation_records (
    observation_id integer NOT NULL DEFAULT nextval('observation_records_observation_id_seq'::regclass),
    phase_id character varying NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    observation_title character varying NOT NULL,
    observation_description text NOT NULL,
    observation_type observationtypeenum NOT NULL,
    severity observationseverityenum NOT NULL,
    status observationstatusenum,
    source_test_execution_id integer,
    source_sample_record_id character varying,
    source_attribute_id integer,
    detection_method character varying,
    detection_confidence double precision,
    impact_description text,
    impact_categories json,
    financial_impact_estimate double precision,
    regulatory_risk_level character varying,
    affected_processes json,
    affected_systems json,
    evidence_documents json,
    supporting_data json,
    screenshots json,
    related_observations json,
    detected_by integer,
    assigned_to integer,
    detected_at timestamp without time zone,
    assigned_at timestamp without time zone,
    auto_detection_rules json,
    auto_detection_score double precision,
    manual_validation_required boolean,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (observation_id)
);

-- Table: observation_resolutions
CREATE TABLE cycle_report_observation_mgmt_resolutions (
    resolution_id integer NOT NULL DEFAULT nextval('observation_resolutions_resolution_id_seq'::regclass),
    observation_id integer NOT NULL,
    resolution_strategy character varying NOT NULL,
    resolution_description text,
    resolution_steps json,
    success_criteria json,
    validation_requirements json,
    resolution_status resolutionstatusenum,
    progress_percentage double precision,
    current_step character varying,
    planned_start_date timestamp without time zone,
    planned_completion_date timestamp without time zone,
    actual_start_date timestamp without time zone,
    actual_completion_date timestamp without time zone,
    assigned_resources json,
    estimated_effort_hours integer,
    actual_effort_hours integer,
    budget_allocated double precision,
    budget_spent double precision,
    implemented_controls json,
    process_changes json,
    system_changes json,
    documentation_updates json,
    training_requirements json,
    validation_tests_planned json,
    validation_tests_completed json,
    validation_results json,
    effectiveness_metrics json,
    resolution_owner integer,
    created_by integer,
    created_at timestamp without time zone,
    validated_by integer,
    validated_at timestamp without time zone,
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (resolution_id)
);

-- Table: observation_versions
CREATE TABLE observation_versions (
    observation_version_id uuid NOT NULL DEFAULT gen_random_uuid(),
    observation_id uuid NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    observation_type character varying(50) NOT NULL,
    severity character varying(20) NOT NULL,
    title character varying(500) NOT NULL,
    description text NOT NULL,
    impact_description text,
    affected_attributes jsonb,
    affected_samples jsonb,
    affected_lobs jsonb,
    resolution_status character varying(50),
    resolution_description text,
    resolution_date timestamp with time zone,
    resolved_by character varying(255),
    group_id uuid,
    is_group_parent boolean,
    evidence_links jsonb,
    supporting_documents jsonb,
    tracking_metadata jsonb,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    version_number integer NOT NULL,
    is_latest_version boolean NOT NULL,
    version_created_at timestamp with time zone,
    version_created_by character varying(255),
    version_notes text,
    change_reason character varying(500),
    parent_version_id uuid,
    version_status character varying(50),
    approved_version_id uuid,
    approved_at timestamp with time zone,
    approved_by character varying(255),
    PRIMARY KEY (observation_version_id)
);

-- Table: observations
CREATE TABLE observations (
    observation_id integer NOT NULL DEFAULT nextval('observations_observation_id_seq'::regclass),
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    attribute_id integer,
    observation_type observation_type_enum NOT NULL,
    description text NOT NULL,
    impact_level impact_level_enum NOT NULL,
    samples_impacted integer NOT NULL,
    status observation_status_enum NOT NULL,
    tester_comments text,
    report_owner_comments text,
    resolution_rationale text,
    resolved_at timestamp with time zone,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (observation_id)
);

-- Table: permission_audit_log
CREATE TABLE permission_audit_log (
    audit_id integer NOT NULL DEFAULT nextval('permission_audit_log_audit_id_seq'::regclass),
    action_type character varying(50) NOT NULL,
    target_type character varying(50) NOT NULL,
    target_id integer NOT NULL,
    permission_id integer,
    role_id integer,
    performed_by integer,
    performed_at timestamp without time zone NOT NULL DEFAULT now(),
    reason text,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (audit_id)
);

-- Table: permissions
CREATE TABLE permissions (
    permission_id integer NOT NULL DEFAULT nextval('permissions_permission_id_seq'::regclass),
    resource character varying(100) NOT NULL,
    action character varying(50) NOT NULL,
    description text,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (permission_id),
    UNIQUE (resource, action)
);

-- Table: metrics_phases
CREATE TABLE metrics_phases (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    phase_name character varying(50) NOT NULL,
    lob_name character varying(100),
    total_attributes integer,
    approved_attributes integer,
    attributes_with_issues integer,
    primary_keys integer,
    non_pk_attributes integer,
    total_samples integer,
    approved_samples integer,
    failed_samples integer,
    total_test_cases integer,
    completed_test_cases integer,
    passed_test_cases integer,
    failed_test_cases integer,
    total_observations integer,
    approved_observations integer,
    completion_time_minutes double precision,
    on_time_completion boolean,
    submissions_for_approval integer,
    data_providers_assigned integer,
    changes_to_data_providers integer,
    rfi_sent integer,
    rfi_completed integer,
    rfi_pending integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    PRIMARY KEY (id)
);

-- Table: profiling_results
CREATE TABLE cycle_report_data_profiling_results (
    result_id integer NOT NULL DEFAULT nextval('profiling_results_result_id_seq'::regclass),
    phase_id integer NOT NULL,
    rule_id integer NOT NULL,
    attribute_id integer NOT NULL,
    execution_status character varying(50) NOT NULL,
    execution_time_ms integer,
    executed_at timestamp without time zone NOT NULL,
    passed_count integer,
    failed_count integer,
    total_count integer,
    pass_rate double precision,
    result_summary json,
    failed_records json,
    result_details text,
    quality_impact double precision,
    severity character varying(50),
    has_anomaly boolean,
    anomaly_description text,
    anomaly_marked_by integer,
    anomaly_marked_at timestamp without time zone,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (result_id)
);

-- Table: profiling_rules
CREATE TABLE cycle_report_data_profiling_rules (
    rule_id integer NOT NULL DEFAULT nextval('profiling_rules_rule_id_seq'::regclass),
    phase_id integer NOT NULL,
    attribute_id integer NOT NULL,
    rule_name character varying(255) NOT NULL,
    rule_type profilingruletype NOT NULL,
    rule_description text,
    rule_code text NOT NULL,
    rule_parameters json,
    llm_provider character varying(50),
    llm_rationale text,
    regulatory_reference text,
    status profilingrulestatus NOT NULL,
    approved_by integer,
    approved_at timestamp without time zone,
    approval_notes text,
    is_executable boolean,
    execution_order integer,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    version_number integer DEFAULT 1,
    is_current_version boolean DEFAULT true,
    business_key character varying(255) NOT NULL,
    version_created_at timestamp without time zone,
    version_created_by integer,
    effective_from timestamp without time zone,
    effective_to timestamp without time zone,
    rejected_by integer,
    rejected_at timestamp without time zone,
    rejection_reason text,
    rejection_notes text,
    revision_notes text,
    cycle_id integer,
    report_id integer,
    created_by integer,
    updated_by integer,
    rule_logic text,
    expected_result text,
    severity character varying(50),
    PRIMARY KEY (rule_id)
);

-- Table: regulatory_data_dictionary
CREATE TABLE regulatory_data_dictionary (
    dict_id integer NOT NULL DEFAULT nextval('regulatory_data_dictionary_dict_id_seq'::regclass),
    report_name character varying(255) NOT NULL,
    schedule_name character varying(255) NOT NULL,
    line_item_number character varying(50),
    line_item_name character varying(500) NOT NULL,
    technical_line_item_name character varying(500),
    mdrm character varying(50),
    description text,
    static_or_dynamic character varying(20),
    mandatory_or_optional character varying(20),
    format_specification character varying(200),
    num_reports_schedules_used character varying(50),
    other_schedule_reference text,
    is_active boolean NOT NULL,
    created_at timestamp without time zone NOT NULL DEFAULT now(),
    updated_at timestamp without time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (dict_id)
);

-- Table: report_attributes
CREATE TABLE report_attributes (
    attribute_id integer NOT NULL DEFAULT nextval('report_attributes_attribute_id_seq'::regclass),
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    attribute_name character varying(255) NOT NULL,
    description text,
    data_type data_type_enum,
    mandatory_flag mandatory_flag_enum NOT NULL,
    cde_flag boolean NOT NULL,
    historical_issues_flag boolean NOT NULL,
    is_scoped boolean NOT NULL,
    llm_generated boolean NOT NULL,
    llm_rationale text,
    tester_notes text,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    validation_rules text,
    typical_source_documents text,
    keywords_to_look_for text,
    testing_approach text,
    risk_score double precision,
    llm_risk_rationale text,
    is_primary_key boolean NOT NULL DEFAULT false,
    primary_key_order integer,
    approval_status character varying(20) NOT NULL DEFAULT 'pending'::character varying,
    master_attribute_id integer,
    version_number integer NOT NULL DEFAULT 1,
    is_latest_version boolean NOT NULL DEFAULT true,
    is_active boolean NOT NULL DEFAULT true,
    version_notes text,
    change_reason character varying(100),
    replaced_attribute_id integer,
    version_created_at timestamp without time zone NOT NULL DEFAULT now(),
    version_created_by integer NOT NULL DEFAULT 1,
    approved_at timestamp without time zone,
    approved_by integer,
    archived_at timestamp without time zone,
    archived_by integer,
    line_item_number character varying(20),
    technical_line_item_name character varying(255),
    mdrm character varying(50),
    PRIMARY KEY (attribute_id)
);

-- Table: report_owner_assignment_history
CREATE TABLE report_owner_assignment_history (
    history_id integer NOT NULL DEFAULT nextval('report_owner_assignment_history_history_id_seq'::regclass),
    assignment_id integer NOT NULL,
    changed_by integer NOT NULL,
    changed_at timestamp with time zone NOT NULL,
    field_changed character varying(100) NOT NULL,
    old_value text,
    new_value text,
    change_reason text,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (history_id)
);

-- Table: report_owner_assignments
CREATE TABLE report_owner_assignments (
    assignment_id integer NOT NULL DEFAULT nextval('report_owner_assignments_assignment_id_seq'::regclass),
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    phase_name character varying(50) NOT NULL,
    assignment_type assignment_type_enum NOT NULL,
    title character varying(255) NOT NULL,
    description text,
    assigned_to integer NOT NULL,
    assigned_by integer NOT NULL,
    assigned_at timestamp with time zone NOT NULL,
    due_date timestamp with time zone,
    started_at timestamp with time zone,
    completed_at timestamp with time zone,
    status assignment_status_enum NOT NULL,
    priority assignment_priority_enum NOT NULL,
    completed_by integer,
    completion_notes text,
    completion_attachments text,
    escalated boolean NOT NULL,
    escalated_at timestamp with time zone,
    escalation_reason text,
    assignment_metadata text,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    PRIMARY KEY (assignment_id)
);

-- Table: report_owner_executives
CREATE TABLE report_owner_executives (
    executive_id integer NOT NULL,
    report_owner_id integer NOT NULL,
    PRIMARY KEY (executive_id, report_owner_id)
);

-- Table: report_owner_scoping_reviews
CREATE TABLE cycle_report_scoping_report_owner_reviews (
    review_id integer NOT NULL DEFAULT nextval('report_owner_scoping_reviews_review_id_seq'::regclass),
    submission_id integer NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    approval_status approval_status_enum NOT NULL,
    review_comments text,
    requested_changes json,
    resource_impact_assessment text,
    risk_coverage_assessment text,
    reviewed_by integer NOT NULL,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (review_id)
);

-- Table: reports
CREATE TABLE reports (
    report_id integer NOT NULL DEFAULT nextval('reports_report_id_seq'::regclass),
    report_name character varying(255) NOT NULL,
    regulation character varying(255),
    description text,
    frequency character varying(100),
    report_owner_id integer NOT NULL,
    lob_id integer NOT NULL,
    is_active boolean NOT NULL,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (report_id)
);

-- Table: request_info_audit_log
CREATE TABLE request_info_audit_log (
    audit_id character varying(36) NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    phase_id character varying(36),
    action character varying(100) NOT NULL,
    entity_type character varying(50) NOT NULL,
    entity_id character varying(36),
    performed_by integer NOT NULL,
    performed_at timestamp with time zone NOT NULL,
    old_values jsonb,
    new_values jsonb,
    notes text,
    ip_address character varying(45),
    user_agent text,
    session_id character varying(100),
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (audit_id)
);

-- Table: request_info_audit_logs
CREATE TABLE cycle_report_request_info_audit_logs (
    log_id integer NOT NULL DEFAULT nextval('request_info_audit_logs_log_id_seq'::regclass),
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    phase_id character varying(36),
    action character varying(100) NOT NULL,
    entity_type character varying(50) NOT NULL,
    entity_id character varying(100),
    performed_by integer NOT NULL,
    performed_at timestamp with time zone NOT NULL,
    old_values jsonb,
    new_values jsonb,
    notes text,
    ip_address character varying(45),
    user_agent text,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (log_id)
);

-- Table: request_info_phases
CREATE TABLE request_info_phases (
    phase_id character varying(36) NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    phase_status character varying(50) NOT NULL,
    planned_start_date timestamp with time zone,
    planned_end_date timestamp with time zone,
    submission_deadline timestamp with time zone NOT NULL,
    reminder_schedule jsonb,
    instructions text,
    started_at timestamp with time zone,
    started_by integer,
    completed_at timestamp with time zone,
    completed_by integer,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    PRIMARY KEY (phase_id)
);

-- Table: resource_permissions
CREATE TABLE resource_permissions (
    resource_permission_id integer NOT NULL DEFAULT nextval('resource_permissions_resource_permission_id_seq'::regclass),
    user_id integer NOT NULL,
    resource_type character varying(50) NOT NULL,
    resource_id integer NOT NULL,
    permission_id integer NOT NULL,
    granted boolean NOT NULL,
    granted_by integer,
    granted_at timestamp without time zone NOT NULL DEFAULT now(),
    expires_at timestamp without time zone,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (resource_permission_id),
    UNIQUE (user_id, resource_type, resource_id, permission_id)
);

-- Table: resources
CREATE TABLE resources (
    resource_id integer NOT NULL DEFAULT nextval('resources_resource_id_seq'::regclass),
    resource_name character varying(100) NOT NULL,
    display_name character varying(200) NOT NULL,
    description text,
    resource_type character varying(50) NOT NULL,
    parent_resource_id integer,
    is_active boolean NOT NULL,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (resource_id)
);

-- Table: role_hierarchy
CREATE TABLE role_hierarchy (
    parent_role_id integer NOT NULL,
    child_role_id integer NOT NULL,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (parent_role_id, child_role_id)
);

-- Table: role_permissions
CREATE TABLE role_permissions (
    role_id integer NOT NULL,
    permission_id integer NOT NULL,
    granted_by integer,
    granted_at timestamp without time zone NOT NULL DEFAULT now(),
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (role_id, permission_id)
);

-- Table: roles
CREATE TABLE roles (
    role_id integer NOT NULL DEFAULT nextval('roles_role_id_seq'::regclass),
    role_name character varying(100) NOT NULL,
    description text,
    is_system boolean NOT NULL,
    is_active boolean NOT NULL,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (role_id)
);

-- Table: sample_approval_history
CREATE TABLE sample_approval_history (
    approval_id character varying(36) NOT NULL,
    set_id character varying(36) NOT NULL,
    approval_step character varying(100) NOT NULL,
    decision character varying(50) NOT NULL,
    approved_by integer NOT NULL,
    approved_at timestamp with time zone NOT NULL,
    feedback text,
    requested_changes jsonb,
    conditional_approval boolean NOT NULL,
    approval_conditions jsonb,
    previous_status sample_status_enum,
    new_status sample_status_enum NOT NULL,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (approval_id)
);

-- Table: sample_audit_logs
CREATE TABLE sample_audit_logs (
    id integer NOT NULL DEFAULT nextval('sample_audit_logs_id_seq'::regclass),
    sample_id integer,
    submission_id integer,
    action character varying NOT NULL,
    action_details json,
    user_id integer NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    PRIMARY KEY (id)
);

-- Table: sample_feedback
CREATE TABLE sample_feedback (
    id integer NOT NULL DEFAULT nextval('sample_feedback_id_seq'::regclass),
    sample_id integer NOT NULL,
    submission_id integer NOT NULL,
    feedback_type character varying NOT NULL,
    feedback_text text NOT NULL,
    severity character varying,
    is_blocking boolean,
    is_resolved boolean,
    resolved_at timestamp with time zone,
    resolved_by_user_id integer,
    resolution_notes text,
    created_by_user_id integer NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    PRIMARY KEY (id)
);

-- Table: sample_records
CREATE TABLE sample_records (
    record_id character varying(36) NOT NULL,
    set_id character varying(36) NOT NULL,
    sample_identifier character varying(255) NOT NULL,
    primary_key_value character varying(255) NOT NULL,
    sample_data jsonb NOT NULL,
    risk_score double precision,
    validation_status sample_validation_status_enum NOT NULL,
    validation_score double precision,
    selection_rationale text,
    data_source_info jsonb,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone,
    approval_status sample_approval_status_enum NOT NULL DEFAULT 'Pending'::sample_approval_status_enum,
    approved_by integer,
    approved_at timestamp with time zone,
    rejection_reason text,
    change_requests jsonb,
    PRIMARY KEY (record_id)
);

-- Table: sample_selection_audit_log
CREATE TABLE sample_selection_audit_log (
    audit_id character varying(36) NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    set_id character varying(36),
    action character varying(100) NOT NULL,
    entity_type character varying(50) NOT NULL,
    entity_id character varying(36),
    performed_by integer NOT NULL,
    performed_at timestamp with time zone NOT NULL,
    old_values jsonb,
    new_values jsonb,
    notes text,
    ip_address character varying(45),
    user_agent text,
    session_id character varying(100),
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (audit_id)
);

-- Table: sample_selection_phases
CREATE TABLE sample_selection_phases (
    phase_id integer NOT NULL DEFAULT nextval('sample_selection_phases_phase_id_seq'::regclass),
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    phase_status character varying(50),
    planned_start_date timestamp without time zone,
    planned_end_date timestamp without time zone,
    actual_start_date timestamp without time zone,
    actual_end_date timestamp without time zone,
    target_sample_size integer,
    sampling_methodology character varying(100),
    sampling_criteria json,
    llm_generation_enabled boolean,
    llm_provider character varying(50),
    llm_model character varying(100),
    llm_confidence_threshold double precision,
    manual_upload_enabled boolean,
    upload_template_url character varying(500),
    samples_generated integer,
    samples_validated integer,
    samples_approved integer,
    notes text,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    created_by integer,
    updated_by integer,
    id integer NOT NULL,
    PRIMARY KEY (phase_id, id)
);

-- Table: sample_sets
CREATE TABLE sample_sets (
    set_id character varying(36) NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    set_name character varying(255) NOT NULL,
    description text,
    generation_method sample_generation_method_enum NOT NULL,
    sample_type sample_type_enum NOT NULL,
    status sample_status_enum NOT NULL,
    target_sample_size integer,
    actual_sample_size integer NOT NULL,
    created_by integer NOT NULL,
    created_at timestamp with time zone NOT NULL,
    approved_by integer,
    approved_at timestamp with time zone,
    approval_notes text,
    generation_rationale text,
    selection_criteria jsonb,
    quality_score double precision,
    sample_metadata jsonb,
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    master_set_id character varying(36),
    version_number integer NOT NULL DEFAULT 1,
    is_latest_version boolean NOT NULL DEFAULT true,
    is_active boolean NOT NULL DEFAULT true,
    version_notes text,
    change_reason character varying(100),
    replaced_set_id character varying(36),
    version_created_at timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    version_created_by integer NOT NULL DEFAULT 1,
    archived_at timestamp without time zone,
    archived_by integer,
    PRIMARY KEY (set_id)
);

-- Table: sample_submission_items
CREATE TABLE sample_submission_items (
    id integer NOT NULL DEFAULT nextval('sample_submission_items_id_seq'::regclass),
    submission_id integer NOT NULL,
    sample_id integer NOT NULL,
    tester_decision testerdecision NOT NULL,
    primary_key_value character varying NOT NULL,
    sample_data_snapshot json NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    PRIMARY KEY (id)
);

-- Table: sample_submissions
CREATE TABLE sample_submissions (
    id integer NOT NULL DEFAULT nextval('sample_submissions_id_seq'::regclass),
    submission_id character varying,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    version_number integer NOT NULL,
    submitted_at timestamp with time zone DEFAULT now(),
    submitted_by_user_id integer,
    submission_notes text,
    status submissionstatus,
    reviewed_at timestamp with time zone,
    reviewed_by_user_id integer,
    review_decision reportownerdecision,
    review_feedback text,
    is_official_version boolean,
    total_samples integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    PRIMARY KEY (id)
);

-- Table: sample_upload_history
CREATE TABLE sample_upload_history (
    upload_id character varying(36) NOT NULL,
    set_id character varying(36) NOT NULL,
    upload_method character varying(50) NOT NULL,
    original_filename character varying(255),
    file_size_bytes integer,
    total_rows integer NOT NULL,
    valid_rows integer NOT NULL,
    invalid_rows integer NOT NULL,
    primary_key_column character varying(255) NOT NULL,
    data_mapping jsonb,
    validation_rules_applied jsonb,
    data_quality_score double precision NOT NULL,
    upload_summary jsonb,
    processing_time_ms integer NOT NULL,
    uploaded_by integer NOT NULL,
    uploaded_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (upload_id)
);

-- Table: sample_validation_issues
CREATE TABLE sample_validation_issues (
    issue_id character varying(36) NOT NULL,
    validation_id character varying(36) NOT NULL,
    record_id character varying(36) NOT NULL,
    issue_type character varying(100) NOT NULL,
    severity character varying(50) NOT NULL,
    field_name character varying(255),
    issue_description text NOT NULL,
    suggested_fix text,
    is_resolved boolean NOT NULL,
    resolved_at timestamp with time zone,
    resolved_by integer,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (issue_id)
);

-- Table: sample_validation_results
CREATE TABLE sample_validation_results (
    validation_id character varying(36) NOT NULL,
    set_id character varying(36) NOT NULL,
    validation_type character varying(100) NOT NULL,
    validation_rules jsonb NOT NULL,
    overall_status sample_validation_status_enum NOT NULL,
    total_samples integer NOT NULL,
    valid_samples integer NOT NULL,
    invalid_samples integer NOT NULL,
    warning_samples integer NOT NULL,
    overall_quality_score double precision NOT NULL,
    validation_summary jsonb,
    recommendations jsonb,
    validated_by integer NOT NULL,
    validated_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (validation_id)
);

-- Table: samples
CREATE TABLE cycle_report_sample_selection_samples (
    sample_id integer NOT NULL DEFAULT nextval('samples_sample_id_seq'::regclass),
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    primary_key_name character varying(100) NOT NULL,
    primary_key_value character varying(255) NOT NULL,
    sample_data jsonb NOT NULL,
    llm_rationale text,
    tester_rationale text,
    status sample_status_enum NOT NULL,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (sample_id)
);

-- Table: scoping_audit_log
CREATE TABLE scoping_audit_log (
    audit_id integer NOT NULL DEFAULT nextval('scoping_audit_log_audit_id_seq'::regclass),
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    action character varying(100) NOT NULL,
    performed_by integer NOT NULL,
    details json NOT NULL,
    previous_values json,
    new_values json,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (audit_id)
);

-- Table: scoping_decision_versions
CREATE TABLE cycle_report_scoping_decision_versions (
    decision_version_id uuid NOT NULL DEFAULT gen_random_uuid(),
    decision_id uuid NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    attribute_id integer NOT NULL,
    is_in_scope boolean NOT NULL,
    scope_reason text,
    testing_approach character varying(100),
    sample_size_override integer,
    special_instructions text,
    risk_level character varying(20),
    risk_factors jsonb,
    assigned_lobs jsonb,
    depends_on_attributes jsonb,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    version_number integer NOT NULL,
    is_latest_version boolean NOT NULL,
    version_created_at timestamp with time zone,
    version_created_by character varying(255),
    version_notes text,
    change_reason character varying(500),
    parent_version_id uuid,
    version_status character varying(50),
    approved_version_id uuid,
    approved_at timestamp with time zone,
    approved_by character varying(255),
    PRIMARY KEY (decision_version_id)
);

-- Table: scoping_submissions
CREATE TABLE cycle_report_scoping_submissions (
    submission_id integer NOT NULL DEFAULT nextval('scoping_submissions_submission_id_seq'::regclass),
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    submission_notes text,
    total_attributes integer NOT NULL,
    scoped_attributes integer NOT NULL,
    skipped_attributes integer NOT NULL,
    submitted_by integer NOT NULL,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    version integer NOT NULL DEFAULT 1,
    previous_version_id integer,
    changes_from_previous json,
    revision_reason text,
    PRIMARY KEY (submission_id)
);

-- Table: sla_configurations
CREATE TABLE sla_configurations (
    sla_config_id integer NOT NULL DEFAULT nextval('sla_configurations_sla_config_id_seq'::regclass),
    sla_type slatype NOT NULL,
    sla_hours integer NOT NULL,
    warning_hours integer,
    escalation_enabled boolean NOT NULL,
    is_active boolean NOT NULL,
    business_hours_only boolean NOT NULL,
    weekend_excluded boolean NOT NULL,
    auto_escalate_on_breach boolean NOT NULL,
    escalation_interval_hours integer NOT NULL,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (sla_config_id)
);

-- Table: sla_escalation_rules
CREATE TABLE sla_escalation_rules (
    escalation_rule_id integer NOT NULL DEFAULT nextval('sla_escalation_rules_escalation_rule_id_seq'::regclass),
    sla_config_id integer NOT NULL,
    escalation_level escalationlevel NOT NULL,
    escalation_order integer NOT NULL,
    escalate_to_role character varying(100) NOT NULL,
    escalate_to_user_id integer,
    hours_after_breach integer NOT NULL,
    email_template_subject character varying(255) NOT NULL,
    email_template_body text NOT NULL,
    include_managers boolean NOT NULL,
    is_active boolean NOT NULL,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (escalation_rule_id)
);

-- Table: sla_violation_tracking
CREATE TABLE sla_violation_tracking (
    violation_id integer NOT NULL DEFAULT nextval('sla_violation_tracking_violation_id_seq'::regclass),
    sla_config_id integer NOT NULL,
    report_id integer NOT NULL,
    cycle_id integer NOT NULL,
    started_at timestamp without time zone NOT NULL,
    due_date timestamp without time zone NOT NULL,
    warning_date timestamp without time zone,
    completed_at timestamp without time zone,
    is_violated boolean NOT NULL,
    violated_at timestamp without time zone,
    violation_hours integer,
    current_escalation_level escalationlevel,
    escalation_count integer NOT NULL,
    last_escalated_at timestamp without time zone,
    is_resolved boolean NOT NULL,
    resolved_at timestamp without time zone,
    resolution_notes text,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (violation_id)
);

-- Table: submission_documents
CREATE TABLE submission_documents (
    document_id integer NOT NULL DEFAULT nextval('submission_documents_document_id_seq'::regclass),
    phase_id character varying(36) NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    data_provider_id integer NOT NULL,
    document_type document_type_enum NOT NULL,
    original_filename character varying(255) NOT NULL,
    stored_filename character varying(255) NOT NULL,
    file_path character varying(500) NOT NULL,
    file_size integer NOT NULL,
    file_hash character varying(64) NOT NULL,
    mime_type character varying(100) NOT NULL,
    sample_records jsonb NOT NULL,
    attributes jsonb NOT NULL,
    description text NOT NULL,
    notes text,
    validation_status validation_status_enum NOT NULL,
    validation_messages jsonb,
    validation_score double precision,
    uploaded_at timestamp with time zone NOT NULL,
    validated_at timestamp with time zone,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (document_id)
);

-- Table: submission_reminders
CREATE TABLE submission_reminders (
    reminder_id character varying(36) NOT NULL,
    phase_id character varying(36) NOT NULL,
    data_provider_id integer NOT NULL,
    reminder_type character varying(50) NOT NULL,
    custom_message text,
    days_before_deadline integer,
    scheduled_at timestamp with time zone NOT NULL,
    sent_at timestamp with time zone,
    delivery_status character varying(50) NOT NULL,
    delivery_attempts integer NOT NULL,
    error_message text,
    viewed_at timestamp with time zone,
    responded_at timestamp with time zone,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (reminder_id)
);

-- Table: submission_validations
CREATE TABLE submission_validations (
    validation_id character varying(36) NOT NULL,
    submission_id integer NOT NULL,
    validation_type character varying(100) NOT NULL,
    status validation_status_enum NOT NULL,
    message text NOT NULL,
    severity character varying(20) NOT NULL,
    recommendation text,
    rule_applied character varying(200),
    validated_at timestamp with time zone NOT NULL,
    validated_by character varying(100) NOT NULL,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (validation_id)
);

-- Table: test_cases
CREATE TABLE test_cases (
    test_case_id character varying(36) NOT NULL,
    phase_id character varying(36) NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    attribute_id integer NOT NULL,
    sample_id character varying(36) NOT NULL,
    sample_identifier character varying(255) NOT NULL,
    data_owner_id integer NOT NULL,
    assigned_by integer NOT NULL,
    assigned_at timestamp with time zone NOT NULL,
    attribute_name character varying(255) NOT NULL,
    primary_key_attributes jsonb NOT NULL,
    expected_evidence_type character varying(100),
    special_instructions text,
    status test_case_status_enum NOT NULL,
    submission_deadline timestamp with time zone,
    submitted_at timestamp with time zone,
    acknowledged_at timestamp with time zone,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    PRIMARY KEY (test_case_id)
);

-- Table: test_comparisons
CREATE TABLE test_comparisons (
    comparison_id integer NOT NULL DEFAULT nextval('test_comparisons_comparison_id_seq'::regclass),
    execution_ids jsonb NOT NULL,
    comparison_criteria jsonb NOT NULL,
    comparison_results jsonb NOT NULL,
    consistency_score double precision NOT NULL,
    differences_found jsonb,
    recommendations jsonb,
    analysis_method_used character varying(100),
    statistical_metrics jsonb,
    compared_at timestamp with time zone NOT NULL,
    comparison_duration_ms integer NOT NULL,
    compared_by integer,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (comparison_id)
);

-- Table: test_cycles
CREATE TABLE test_cycles (
    cycle_id integer NOT NULL DEFAULT nextval('test_cycles_cycle_id_seq'::regclass),
    cycle_name character varying(255) NOT NULL,
    description text,
    test_manager_id integer NOT NULL,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    start_date date NOT NULL,
    end_date date,
    status character varying(50) NOT NULL,
    workflow_id character varying(255),
    PRIMARY KEY (cycle_id)
);

-- Table: test_execution_audit_logs
CREATE TABLE cycle_report_test_execution_audit_logss (
    log_id integer NOT NULL DEFAULT nextval('test_execution_audit_logs_log_id_seq'::regclass),
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    phase_id character varying(36),
    action character varying(100) NOT NULL,
    entity_type character varying(50) NOT NULL,
    entity_id character varying(100),
    performed_by integer NOT NULL,
    performed_at timestamp with time zone NOT NULL,
    old_values jsonb,
    new_values jsonb,
    notes text,
    ip_address character varying(45),
    user_agent text,
    execution_time_ms integer,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (log_id)
);

-- Table: test_execution_phases
CREATE TABLE test_execution_phases (
    phase_id character varying(36) NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    phase_status character varying(50) NOT NULL,
    planned_start_date timestamp with time zone,
    planned_end_date timestamp with time zone,
    testing_deadline timestamp with time zone NOT NULL,
    test_strategy text,
    instructions text,
    started_at timestamp with time zone,
    started_by integer,
    completed_at timestamp with time zone,
    completed_by integer,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    PRIMARY KEY (phase_id)
);

-- Table: test_execution_versions
CREATE TABLE test_execution_versions (
    execution_version_id uuid NOT NULL DEFAULT gen_random_uuid(),
    execution_id uuid NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    attribute_id integer NOT NULL,
    sample_id integer NOT NULL,
    test_results jsonb NOT NULL,
    document_results jsonb,
    database_results jsonb,
    overall_result character varying(20),
    confidence_score double precision,
    issues_identified jsonb,
    requires_resubmission boolean,
    resubmission_reason text,
    evidence_files jsonb,
    screenshots jsonb,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    version_number integer NOT NULL,
    is_latest_version boolean NOT NULL,
    version_created_at timestamp with time zone,
    version_created_by character varying(255),
    version_notes text,
    change_reason character varying(500),
    parent_version_id uuid,
    version_status character varying(50),
    approved_version_id uuid,
    approved_at timestamp with time zone,
    approved_by character varying(255),
    PRIMARY KEY (execution_version_id)
);

-- Table: test_executions
CREATE TABLE cycle_report_test_execution_test_executions (
    execution_id integer NOT NULL DEFAULT nextval('test_executions_execution_id_seq'::regclass),
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    sample_id integer,
    attribute_id integer,
    test_run_number integer NOT NULL,
    source_value text,
    expected_value text,
    test_result test_result_enum,
    discrepancy_details text,
    data_source_type data_source_type_enum,
    data_source_id integer,
    document_id integer,
    table_name character varying(255),
    column_name character varying(255),
    executed_at timestamp with time zone NOT NULL,
    executed_by integer NOT NULL,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (execution_id)
);

-- Table: test_report_phases
CREATE TABLE test_report_phases (
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    phase_id character varying NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    started_at timestamp without time zone,
    completed_at timestamp without time zone,
    include_executive_summary boolean,
    include_phase_artifacts boolean,
    include_detailed_observations boolean,
    include_metrics_dashboard boolean,
    report_title character varying,
    report_period character varying,
    regulatory_references json,
    final_report_document_id integer,
    report_generated_at timestamp without time zone,
    report_approved_by json,
    status character varying,
    PRIMARY KEY (phase_id)
);

-- Table: test_report_sections
CREATE TABLE cycle_report_test_report_sections (
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    section_id integer NOT NULL DEFAULT nextval('test_report_sections_section_id_seq'::regclass),
    phase_id character varying NOT NULL,
    section_name character varying NOT NULL,
    section_order integer NOT NULL,
    section_type character varying NOT NULL,
    content_text text,
    content_data json,
    artifacts json,
    metrics_summary json,
    PRIMARY KEY (section_id)
);

-- Table: test_result_reviews
CREATE TABLE test_result_reviews (
    review_id integer NOT NULL DEFAULT nextval('test_result_reviews_review_id_seq'::regclass),
    execution_id integer NOT NULL,
    reviewer_id integer NOT NULL,
    review_result review_status_enum NOT NULL,
    reviewer_comments text NOT NULL,
    recommended_action character varying(200),
    requires_retest boolean NOT NULL,
    accuracy_score double precision,
    completeness_score double precision,
    consistency_score double precision,
    overall_score double precision,
    review_criteria_used jsonb,
    supporting_evidence text,
    reviewed_at timestamp with time zone NOT NULL,
    review_duration_ms integer,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (review_id)
);

-- Table: tester_scoping_decisions
CREATE TABLE cycle_report_scoping_tester_decisions (
    decision_id integer NOT NULL DEFAULT nextval('tester_scoping_decisions_decision_id_seq'::regclass),
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    attribute_id integer NOT NULL,
    recommendation_id integer,
    decision scoping_decision_enum NOT NULL,
    final_scoping boolean NOT NULL,
    tester_rationale text,
    override_reason text,
    decided_by integer NOT NULL,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (decision_id)
);

-- Table: testing_execution_audit_logs
CREATE TABLE testing_execution_audit_logs (
    log_id integer NOT NULL DEFAULT nextval('testing_execution_audit_logs_log_id_seq'::regclass),
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    phase_id character varying(36),
    action character varying(100) NOT NULL,
    entity_type character varying(50) NOT NULL,
    entity_id character varying(100),
    performed_by integer NOT NULL,
    performed_at timestamp with time zone NOT NULL,
    old_values jsonb,
    new_values jsonb,
    notes text,
    ip_address character varying(45),
    user_agent text,
    execution_time_ms integer,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (log_id)
);

-- Table: testing_execution_phases
CREATE TABLE testing_execution_phases (
    phase_id character varying(36) NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    phase_status character varying(50) NOT NULL,
    planned_start_date timestamp with time zone,
    planned_end_date timestamp with time zone,
    testing_deadline timestamp with time zone NOT NULL,
    test_strategy text,
    instructions text,
    started_at timestamp with time zone,
    started_by integer,
    completed_at timestamp with time zone,
    completed_by integer,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    PRIMARY KEY (phase_id)
);

-- Table: testing_test_executions
CREATE TABLE testing_test_executions (
    execution_id integer NOT NULL DEFAULT nextval('testing_test_executions_execution_id_seq'::regclass),
    phase_id character varying(36) NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    sample_record_id character varying(100) NOT NULL,
    attribute_id integer NOT NULL,
    test_type test_type_enum NOT NULL,
    analysis_method analysis_method_enum NOT NULL,
    priority character varying(20) NOT NULL,
    custom_instructions text,
    status test_status_enum NOT NULL,
    result test_result_enum,
    confidence_score double precision,
    execution_summary text,
    error_message text,
    document_analysis_id integer,
    database_test_id integer,
    started_at timestamp with time zone,
    completed_at timestamp with time zone,
    processing_time_ms integer,
    assigned_tester_id integer,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    data_source_id integer,
    sample_id integer,
    executed_by integer,
    PRIMARY KEY (execution_id)
);

-- Table: universal_assignment_history
CREATE TABLE universal_assignment_history (
    history_id integer NOT NULL DEFAULT nextval('universal_assignment_history_history_id_seq'::regclass),
    assignment_id character varying(36) NOT NULL,
    changed_by_user_id integer NOT NULL,
    changed_at timestamp with time zone NOT NULL,
    action character varying(50) NOT NULL,
    field_changed character varying(100),
    old_value text,
    new_value text,
    change_reason text,
    change_metadata jsonb,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (history_id)
);

-- Table: universal_assignments
CREATE TABLE universal_assignments (
    assignment_id character varying(36) NOT NULL,
    assignment_type universal_assignment_type_enum NOT NULL,
    from_role character varying(50) NOT NULL,
    to_role character varying(50) NOT NULL,
    from_user_id integer NOT NULL,
    to_user_id integer,
    title character varying(255) NOT NULL,
    description text,
    task_instructions text,
    context_type universal_context_type_enum NOT NULL,
    context_data jsonb,
    status universal_assignment_status_enum NOT NULL,
    priority universal_assignment_priority_enum NOT NULL,
    assigned_at timestamp with time zone NOT NULL,
    due_date timestamp with time zone,
    acknowledged_at timestamp with time zone,
    started_at timestamp with time zone,
    completed_at timestamp with time zone,
    completed_by_user_id integer,
    completion_notes text,
    completion_data jsonb,
    completion_attachments jsonb,
    requires_approval boolean NOT NULL,
    approval_role character varying(50),
    approved_by_user_id integer,
    approved_at timestamp with time zone,
    approval_notes text,
    escalated boolean NOT NULL,
    escalated_at timestamp with time zone,
    escalated_to_user_id integer,
    escalation_reason text,
    delegated_to_user_id integer,
    delegated_at timestamp with time zone,
    delegation_reason text,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    assignment_metadata jsonb,
    workflow_step character varying(100),
    parent_assignment_id character varying(36),
    PRIMARY KEY (assignment_id)
);

-- Table: user_permissions
CREATE TABLE user_permissions (
    user_id integer NOT NULL,
    permission_id integer NOT NULL,
    granted boolean NOT NULL,
    granted_by integer,
    granted_at timestamp without time zone NOT NULL DEFAULT now(),
    expires_at timestamp without time zone,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, permission_id)
);

-- Table: user_roles
CREATE TABLE user_roles (
    user_id integer NOT NULL,
    role_id integer NOT NULL,
    assigned_by integer,
    assigned_at timestamp without time zone NOT NULL DEFAULT now(),
    expires_at timestamp without time zone,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, role_id)
);

-- Table: users
CREATE TABLE users (
    user_id integer NOT NULL DEFAULT nextval('users_user_id_seq'::regclass),
    first_name character varying(100) NOT NULL,
    last_name character varying(100) NOT NULL,
    email character varying(255) NOT NULL,
    phone character varying(20),
    role user_role_enum NOT NULL,
    lob_id integer,
    is_active boolean NOT NULL,
    hashed_password character varying(255) NOT NULL,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id)
);

-- Table: version_history
CREATE TABLE version_history (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    entity_type character varying(50) NOT NULL,
    entity_id uuid NOT NULL,
    entity_name character varying(255),
    version_number integer NOT NULL,
    change_type character varying(50) NOT NULL,
    change_reason text,
    changed_by character varying(255) NOT NULL,
    changed_at timestamp with time zone,
    change_details jsonb,
    cycle_id uuid,
    report_id uuid,
    phase_name character varying(50),
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (id)
);

-- Table: workflow_activities
CREATE TABLE workflow_activities (
    activity_id integer NOT NULL DEFAULT nextval('workflow_activities_activity_id_seq'::regclass),
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    phase_name character varying(100) NOT NULL,
    activity_name character varying(255) NOT NULL,
    activity_type activity_type_enum NOT NULL,
    activity_order integer NOT NULL,
    status activity_status_enum NOT NULL DEFAULT 'NOT_STARTED'::activity_status_enum,
    can_start boolean NOT NULL DEFAULT false,
    can_complete boolean NOT NULL DEFAULT false,
    is_manual boolean NOT NULL DEFAULT true,
    is_optional boolean NOT NULL DEFAULT false,
    started_at timestamp with time zone,
    started_by integer,
    completed_at timestamp with time zone,
    completed_by integer,
    revision_requested_at timestamp with time zone,
    revision_requested_by integer,
    revision_reason text,
    blocked_at timestamp with time zone,
    blocked_reason text,
    metadata jsonb,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    UNIQUE (cycle_id, report_id, phase_name, activity_name),
    PRIMARY KEY (activity_id)
);

-- Table: workflow_activity_dependencies
CREATE TABLE workflow_activity_dependencies (
    dependency_id integer NOT NULL DEFAULT nextval('workflow_activity_dependencies_dependency_id_seq'::regclass),
    phase_name character varying(100) NOT NULL,
    activity_name character varying(255) NOT NULL,
    depends_on_activity character varying(255) NOT NULL,
    dependency_type character varying(50) NOT NULL DEFAULT 'completion'::character varying,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    UNIQUE (phase_name, activity_name, depends_on_activity),
    PRIMARY KEY (dependency_id)
);

-- Table: workflow_activity_history
CREATE TABLE workflow_activity_history (
    history_id integer NOT NULL DEFAULT nextval('workflow_activity_history_history_id_seq'::regclass),
    activity_id integer NOT NULL,
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    phase_name character varying(100) NOT NULL,
    activity_name character varying(255) NOT NULL,
    from_status character varying(50),
    to_status character varying(50) NOT NULL,
    changed_by integer NOT NULL,
    changed_at timestamp with time zone NOT NULL DEFAULT now(),
    change_reason text,
    metadata jsonb,
    PRIMARY KEY (history_id)
);

-- Table: workflow_activity_templates
CREATE TABLE workflow_activity_templates (
    template_id integer NOT NULL DEFAULT nextval('workflow_activity_templates_template_id_seq'::regclass),
    phase_name character varying(100) NOT NULL,
    activity_name character varying(255) NOT NULL,
    activity_type activity_type_enum NOT NULL,
    activity_order integer NOT NULL,
    description text,
    is_manual boolean NOT NULL DEFAULT true,
    is_optional boolean NOT NULL DEFAULT false,
    required_role character varying(100),
    auto_complete_on_event character varying(100),
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    UNIQUE (phase_name, activity_name),
    PRIMARY KEY (template_id)
);

-- Table: workflow_alerts
CREATE TABLE workflow_alerts (
    alert_id integer NOT NULL DEFAULT nextval('workflow_alerts_alert_id_seq'::regclass),
    execution_id character varying(36),
    workflow_type character varying(100),
    phase_name character varying(50),
    alert_type character varying(50) NOT NULL,
    severity character varying(20) NOT NULL,
    threshold_value double precision,
    actual_value double precision,
    alert_message text,
    created_at timestamp with time zone,
    acknowledged boolean,
    acknowledged_by integer,
    acknowledged_at timestamp with time zone,
    resolved boolean,
    resolved_at timestamp with time zone,
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (alert_id)
);

-- Table: workflow_executions
CREATE TABLE workflow_executions (
    execution_id character varying(36) NOT NULL,
    workflow_id character varying(100) NOT NULL,
    workflow_run_id character varying(100) NOT NULL,
    workflow_type character varying(100) NOT NULL,
    workflow_version character varying(20),
    cycle_id integer NOT NULL,
    report_id integer,
    initiated_by integer NOT NULL,
    status workflowexecutionstatus,
    started_at timestamp with time zone,
    completed_at timestamp with time zone,
    duration_seconds double precision,
    input_data json,
    output_data json,
    error_details json,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (execution_id)
);

-- Table: workflow_metrics
CREATE TABLE workflow_metrics (
    metric_id integer NOT NULL DEFAULT nextval('workflow_metrics_metric_id_seq'::regclass),
    workflow_type character varying(100) NOT NULL,
    phase_name character varying(50),
    activity_name character varying(100),
    step_type steptype,
    period_start timestamp with time zone NOT NULL,
    period_end timestamp with time zone NOT NULL,
    execution_count integer,
    success_count integer,
    failure_count integer,
    avg_duration double precision,
    min_duration double precision,
    max_duration double precision,
    p50_duration double precision,
    p90_duration double precision,
    p95_duration double precision,
    p99_duration double precision,
    avg_retry_count double precision,
    timeout_count integer,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (metric_id),
    UNIQUE (workflow_type, phase_name, activity_name, step_type, period_start, period_end)
);

-- Table: workflow_phases
CREATE TABLE workflow_phases (
    phase_id integer NOT NULL DEFAULT nextval('workflow_phases_phase_id_seq'::regclass),
    cycle_id integer NOT NULL,
    report_id integer NOT NULL,
    phase_name workflow_phase_enum NOT NULL,
    status phase_status_enum NOT NULL,
    planned_start_date date,
    planned_end_date date,
    actual_start_date timestamp with time zone,
    actual_end_date timestamp with time zone,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    state workflow_phase_state_enum NOT NULL DEFAULT 'Not Started'::workflow_phase_state_enum,
    schedule_status workflow_phase_status_enum NOT NULL DEFAULT 'On Track'::workflow_phase_status_enum,
    state_override workflow_phase_state_enum,
    status_override workflow_phase_status_enum,
    override_reason text,
    override_by integer,
    override_at timestamp with time zone,
    started_by integer,
    completed_by integer,
    notes text,
    metadata jsonb,
    phase_data jsonb,
    PRIMARY KEY (phase_id)
);

-- Table: workflow_steps
CREATE TABLE workflow_steps (
    step_id character varying(36) NOT NULL,
    execution_id character varying(36) NOT NULL,
    parent_step_id character varying(36),
    step_name character varying(100) NOT NULL,
    step_type steptype NOT NULL,
    phase_name character varying(50),
    activity_name character varying(100),
    status workflowexecutionstatus,
    started_at timestamp with time zone,
    completed_at timestamp with time zone,
    duration_seconds double precision,
    attempt_number integer,
    max_attempts integer,
    retry_delay_seconds integer,
    input_data json,
    output_data json,
    error_details json,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (step_id)
);

-- Table: workflow_transitions
CREATE TABLE workflow_transitions (
    transition_id character varying(36) NOT NULL,
    execution_id character varying(36) NOT NULL,
    from_step_id character varying(36),
    to_step_id character varying(36),
    transition_type character varying(50),
    started_at timestamp with time zone NOT NULL,
    completed_at timestamp with time zone,
    duration_seconds double precision,
    condition_evaluated character varying(200),
    condition_result boolean,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (transition_id)
);

-- Add foreign key constraints
ALTER TABLE attribute_lob_assignments ADD CONSTRAINT attribute_lob_assignments_assigned_by_fkey FOREIGN KEY (assigned_by) REFERENCES users(user_id);
ALTER TABLE attribute_lob_assignments ADD CONSTRAINT attribute_lob_assignments_attribute_id_fkey FOREIGN KEY (attribute_id) REFERENCES report_attributes(attribute_id);
ALTER TABLE attribute_lob_assignments ADD CONSTRAINT attribute_lob_assignments_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE attribute_lob_assignments ADD CONSTRAINT attribute_lob_assignments_lob_id_fkey FOREIGN KEY (lob_id) REFERENCES lobs(lob_id);
ALTER TABLE attribute_lob_assignments ADD CONSTRAINT attribute_lob_assignments_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE cycle_report_data_profiling_attribute_scores ADD CONSTRAINT attribute_profiling_scores_attribute_id_fkey FOREIGN KEY (attribute_id) REFERENCES report_attributes(attribute_id);
ALTER TABLE cycle_report_data_profiling_attribute_scores ADD CONSTRAINT attribute_profiling_scores_phase_id_fkey FOREIGN KEY (phase_id) REFERENCES data_profiling_phases(phase_id);
ALTER TABLE cycle_report_scoping_attribute_recommendation_versions ADD CONSTRAINT attribute_scoping_recommendation_versions_attribute_id_fkey FOREIGN KEY (attribute_id) REFERENCES report_attributes(attribute_id);
ALTER TABLE cycle_report_scoping_attribute_recommendation_versions ADD CONSTRAINT attribute_scoping_recommendation_versions_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE cycle_report_scoping_attribute_recommendation_versions ADD CONSTRAINT attribute_scoping_recommendation_versions_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE cycle_report_scoping_attribute_recommendations ADD CONSTRAINT attribute_scoping_recommendations_attribute_id_fkey FOREIGN KEY (attribute_id) REFERENCES report_attributes(attribute_id);
ALTER TABLE cycle_report_scoping_attribute_recommendations ADD CONSTRAINT attribute_scoping_recommendations_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE cycle_report_scoping_attribute_recommendations ADD CONSTRAINT attribute_scoping_recommendations_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE attribute_version_change_logs ADD CONSTRAINT attribute_version_change_logs_attribute_id_fkey FOREIGN KEY (attribute_id) REFERENCES report_attributes(attribute_id);
ALTER TABLE attribute_version_change_logs ADD CONSTRAINT attribute_version_change_logs_changed_by_fkey FOREIGN KEY (changed_by) REFERENCES users(user_id);
ALTER TABLE attribute_version_comparisons ADD CONSTRAINT attribute_version_comparisons_compared_by_fkey FOREIGN KEY (compared_by) REFERENCES users(user_id);
ALTER TABLE attribute_version_comparisons ADD CONSTRAINT attribute_version_comparisons_version_a_id_fkey FOREIGN KEY (version_a_id) REFERENCES report_attributes(attribute_id);
ALTER TABLE attribute_version_comparisons ADD CONSTRAINT attribute_version_comparisons_version_b_id_fkey FOREIGN KEY (version_b_id) REFERENCES report_attributes(attribute_id);
ALTER TABLE audit_log ADD CONSTRAINT audit_log_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(user_id);
ALTER TABLE bulk_test_executions ADD CONSTRAINT bulk_test_executions_initiated_by_fkey FOREIGN KEY (initiated_by) REFERENCES users(user_id);
ALTER TABLE bulk_test_executions ADD CONSTRAINT bulk_test_executions_phase_id_fkey FOREIGN KEY (phase_id) REFERENCES testing_execution_phases(phase_id);
ALTER TABLE cdo_notifications ADD CONSTRAINT cdo_notifications_cdo_id_fkey FOREIGN KEY (cdo_id) REFERENCES users(user_id);
ALTER TABLE cdo_notifications ADD CONSTRAINT cdo_notifications_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE cdo_notifications ADD CONSTRAINT cdo_notifications_lob_id_fkey FOREIGN KEY (lob_id) REFERENCES lobs(lob_id);
ALTER TABLE cdo_notifications ADD CONSTRAINT cdo_notifications_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE cycle_reports ADD CONSTRAINT cycle_reports_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE cycle_reports ADD CONSTRAINT cycle_reports_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE cycle_reports ADD CONSTRAINT cycle_reports_tester_id_fkey FOREIGN KEY (tester_id) REFERENCES users(user_id);
ALTER TABLE data_owner_assignments ADD CONSTRAINT data_owner_assignments_assigned_by_fkey FOREIGN KEY (assigned_by) REFERENCES users(user_id);
ALTER TABLE data_owner_assignments ADD CONSTRAINT data_owner_assignments_attribute_id_fkey FOREIGN KEY (attribute_id) REFERENCES report_attributes(attribute_id);
ALTER TABLE data_owner_assignments ADD CONSTRAINT data_owner_assignments_cdo_id_fkey FOREIGN KEY (cdo_id) REFERENCES users(user_id);
ALTER TABLE data_owner_assignments ADD CONSTRAINT data_owner_assignments_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE data_owner_assignments ADD CONSTRAINT data_owner_assignments_data_owner_id_fkey FOREIGN KEY (data_owner_id) REFERENCES users(user_id);
ALTER TABLE data_owner_assignments ADD CONSTRAINT data_owner_assignments_lob_id_fkey FOREIGN KEY (lob_id) REFERENCES lobs(lob_id);
ALTER TABLE data_owner_assignments ADD CONSTRAINT data_owner_assignments_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE data_owner_escalation_log ADD CONSTRAINT data_owner_escalation_log_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE data_owner_escalation_log ADD CONSTRAINT data_owner_escalation_log_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE data_owner_escalation_log ADD CONSTRAINT data_owner_escalation_log_sent_by_fkey FOREIGN KEY (sent_by) REFERENCES users(user_id);
ALTER TABLE data_owner_notifications ADD CONSTRAINT data_owner_notifications_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE data_owner_notifications ADD CONSTRAINT data_owner_notifications_data_owner_id_fkey FOREIGN KEY (data_owner_id) REFERENCES users(user_id);
ALTER TABLE data_owner_notifications ADD CONSTRAINT data_owner_notifications_phase_id_fkey FOREIGN KEY (phase_id) REFERENCES request_info_phases(phase_id);
ALTER TABLE data_owner_notifications ADD CONSTRAINT data_owner_notifications_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE data_owner_phase_audit_log ADD CONSTRAINT data_owner_phase_audit_log_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE data_owner_phase_audit_log ADD CONSTRAINT data_owner_phase_audit_log_performed_by_fkey FOREIGN KEY (performed_by) REFERENCES users(user_id);
ALTER TABLE data_owner_phase_audit_log ADD CONSTRAINT data_owner_phase_audit_log_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE data_owner_sla_violations ADD CONSTRAINT data_owner_sla_violations_assignment_id_fkey FOREIGN KEY (assignment_id) REFERENCES data_owner_assignments(assignment_id);
ALTER TABLE data_owner_sla_violations ADD CONSTRAINT data_owner_sla_violations_attribute_id_fkey FOREIGN KEY (attribute_id) REFERENCES report_attributes(attribute_id);
ALTER TABLE data_owner_sla_violations ADD CONSTRAINT data_owner_sla_violations_cdo_id_fkey FOREIGN KEY (cdo_id) REFERENCES users(user_id);
ALTER TABLE data_owner_sla_violations ADD CONSTRAINT data_owner_sla_violations_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE data_owner_sla_violations ADD CONSTRAINT data_owner_sla_violations_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE cycle_report_data_profiling_files ADD CONSTRAINT data_profiling_files_phase_id_fkey FOREIGN KEY (phase_id) REFERENCES data_profiling_phases(phase_id);
ALTER TABLE cycle_report_data_profiling_files ADD CONSTRAINT data_profiling_files_uploaded_by_fkey FOREIGN KEY (uploaded_by) REFERENCES users(user_id);
ALTER TABLE data_profiling_phases ADD CONSTRAINT data_profiling_phases_completed_by_fkey FOREIGN KEY (completed_by) REFERENCES users(user_id);
ALTER TABLE data_profiling_phases ADD CONSTRAINT data_profiling_phases_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE data_profiling_phases ADD CONSTRAINT data_profiling_phases_data_requested_by_fkey FOREIGN KEY (data_requested_by) REFERENCES users(user_id);
ALTER TABLE data_profiling_phases ADD CONSTRAINT data_profiling_phases_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE data_profiling_phases ADD CONSTRAINT data_profiling_phases_started_by_fkey FOREIGN KEY (started_by) REFERENCES users(user_id);
ALTER TABLE cycle_report_data_profiling_rule_versions ADD CONSTRAINT data_profiling_rule_versions_attribute_id_fkey FOREIGN KEY (attribute_id) REFERENCES report_attributes(attribute_id);
ALTER TABLE cycle_report_data_profiling_rule_versions ADD CONSTRAINT data_profiling_rule_versions_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE cycle_report_data_profiling_rule_versions ADD CONSTRAINT data_profiling_rule_versions_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE data_provider_assignments ADD CONSTRAINT data_provider_assignments_assigned_by_fkey FOREIGN KEY (assigned_by) REFERENCES users(user_id);
ALTER TABLE data_provider_assignments ADD CONSTRAINT data_provider_assignments_attribute_id_fkey FOREIGN KEY (attribute_id) REFERENCES report_attributes(attribute_id);
ALTER TABLE data_provider_assignments ADD CONSTRAINT data_provider_assignments_cdo_id_fkey FOREIGN KEY (cdo_id) REFERENCES users(user_id);
ALTER TABLE data_provider_assignments ADD CONSTRAINT data_provider_assignments_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE data_provider_assignments ADD CONSTRAINT data_provider_assignments_data_provider_id_fkey FOREIGN KEY (data_provider_id) REFERENCES users(user_id);
ALTER TABLE data_provider_assignments ADD CONSTRAINT data_provider_assignments_lob_id_fkey FOREIGN KEY (lob_id) REFERENCES lobs(lob_id);
ALTER TABLE data_provider_assignments ADD CONSTRAINT data_provider_assignments_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE data_provider_escalation_log ADD CONSTRAINT data_provider_escalation_log_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE data_provider_escalation_log ADD CONSTRAINT data_provider_escalation_log_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE data_provider_escalation_log ADD CONSTRAINT data_provider_escalation_log_sent_by_fkey FOREIGN KEY (sent_by) REFERENCES users(user_id);
ALTER TABLE data_provider_notifications ADD CONSTRAINT data_provider_notifications_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE data_provider_notifications ADD CONSTRAINT data_provider_notifications_data_provider_id_fkey FOREIGN KEY (data_provider_id) REFERENCES users(user_id);
ALTER TABLE data_provider_notifications ADD CONSTRAINT data_provider_notifications_phase_id_fkey FOREIGN KEY (phase_id) REFERENCES request_info_phases(phase_id);
ALTER TABLE data_provider_notifications ADD CONSTRAINT data_provider_notifications_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE data_provider_phase_audit_log ADD CONSTRAINT data_provider_phase_audit_log_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE data_provider_phase_audit_log ADD CONSTRAINT data_provider_phase_audit_log_performed_by_fkey FOREIGN KEY (performed_by) REFERENCES users(user_id);
ALTER TABLE data_provider_phase_audit_log ADD CONSTRAINT data_provider_phase_audit_log_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE data_provider_sla_violations ADD CONSTRAINT data_provider_sla_violations_assignment_id_fkey FOREIGN KEY (assignment_id) REFERENCES data_provider_assignments(assignment_id);
ALTER TABLE data_provider_sla_violations ADD CONSTRAINT data_provider_sla_violations_attribute_id_fkey FOREIGN KEY (attribute_id) REFERENCES report_attributes(attribute_id);
ALTER TABLE data_provider_sla_violations ADD CONSTRAINT data_provider_sla_violations_cdo_id_fkey FOREIGN KEY (cdo_id) REFERENCES users(user_id);
ALTER TABLE data_provider_sla_violations ADD CONSTRAINT data_provider_sla_violations_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE data_provider_sla_violations ADD CONSTRAINT data_provider_sla_violations_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE data_provider_submissions ADD CONSTRAINT data_provider_submissions_attribute_id_fkey FOREIGN KEY (attribute_id) REFERENCES report_attributes(attribute_id);
ALTER TABLE data_provider_submissions ADD CONSTRAINT data_provider_submissions_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE data_provider_submissions ADD CONSTRAINT data_provider_submissions_data_provider_id_fkey FOREIGN KEY (data_provider_id) REFERENCES users(user_id);
ALTER TABLE data_provider_submissions ADD CONSTRAINT data_provider_submissions_database_submission_id_fkey FOREIGN KEY (database_submission_id) REFERENCES database_submissions(db_submission_id);
ALTER TABLE data_provider_submissions ADD CONSTRAINT data_provider_submissions_phase_id_fkey FOREIGN KEY (phase_id) REFERENCES request_info_phases(phase_id);
ALTER TABLE data_provider_submissions ADD CONSTRAINT data_provider_submissions_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE database_submissions ADD CONSTRAINT database_submissions_attribute_id_fkey FOREIGN KEY (attribute_id) REFERENCES report_attributes(attribute_id);
ALTER TABLE database_submissions ADD CONSTRAINT database_submissions_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE database_submissions ADD CONSTRAINT database_submissions_data_provider_id_fkey FOREIGN KEY (data_provider_id) REFERENCES users(user_id);
ALTER TABLE database_submissions ADD CONSTRAINT database_submissions_phase_id_fkey FOREIGN KEY (phase_id) REFERENCES request_info_phases(phase_id);
ALTER TABLE database_submissions ADD CONSTRAINT database_submissions_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE cycle_report_test_execution_database_tests ADD CONSTRAINT database_tests_attribute_id_fkey FOREIGN KEY (attribute_id) REFERENCES report_attributes(attribute_id);
ALTER TABLE cycle_report_test_execution_database_tests ADD CONSTRAINT database_tests_database_submission_id_fkey FOREIGN KEY (database_submission_id) REFERENCES database_submissions(db_submission_id);
ALTER TABLE cycle_report_test_execution_database_tests ADD CONSTRAINT database_tests_tested_by_fkey FOREIGN KEY (tested_by) REFERENCES users(user_id);
ALTER TABLE document_access_logs ADD CONSTRAINT document_access_logs_document_id_fkey FOREIGN KEY (document_id) REFERENCES documents(document_id);
ALTER TABLE document_access_logs ADD CONSTRAINT document_access_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(user_id);
ALTER TABLE cycle_report_test_execution_document_analyses ADD CONSTRAINT document_analyses_analyzed_by_fkey FOREIGN KEY (analyzed_by) REFERENCES users(user_id);
ALTER TABLE cycle_report_test_execution_document_analyses ADD CONSTRAINT document_analyses_attribute_id_fkey FOREIGN KEY (attribute_id) REFERENCES report_attributes(attribute_id);
ALTER TABLE cycle_report_test_execution_document_analyses ADD CONSTRAINT document_analyses_submission_document_id_fkey FOREIGN KEY (submission_document_id) REFERENCES submission_documents(document_id);
ALTER TABLE document_extractions ADD CONSTRAINT document_extractions_document_id_fkey FOREIGN KEY (document_id) REFERENCES documents(document_id);
ALTER TABLE document_extractions ADD CONSTRAINT document_extractions_validated_by_user_id_fkey FOREIGN KEY (validated_by_user_id) REFERENCES users(user_id);
ALTER TABLE document_revisions ADD CONSTRAINT document_revisions_document_id_fkey FOREIGN KEY (document_id) REFERENCES documents(document_id);
ALTER TABLE document_revisions ADD CONSTRAINT document_revisions_previous_document_id_fkey FOREIGN KEY (previous_document_id) REFERENCES documents(document_id);
ALTER TABLE document_revisions ADD CONSTRAINT document_revisions_requested_by_fkey FOREIGN KEY (requested_by) REFERENCES users(user_id);
ALTER TABLE document_revisions ADD CONSTRAINT document_revisions_reviewed_by_fkey FOREIGN KEY (reviewed_by) REFERENCES users(user_id);
ALTER TABLE document_revisions ADD CONSTRAINT document_revisions_test_case_id_fkey FOREIGN KEY (test_case_id) REFERENCES test_cases(test_case_id);
ALTER TABLE document_revisions ADD CONSTRAINT document_revisions_uploaded_by_fkey FOREIGN KEY (uploaded_by) REFERENCES users(user_id);
ALTER TABLE document_submissions ADD CONSTRAINT document_submissions_data_provider_id_fkey FOREIGN KEY (data_provider_id) REFERENCES users(user_id);
ALTER TABLE document_submissions ADD CONSTRAINT document_submissions_test_case_id_fkey FOREIGN KEY (test_case_id) REFERENCES test_cases(test_case_id);
ALTER TABLE document_submissions ADD CONSTRAINT document_submissions_validated_by_fkey FOREIGN KEY (validated_by) REFERENCES users(user_id);
ALTER TABLE document_submissions ADD CONSTRAINT fk_document_submissions_data_owner_id FOREIGN KEY (data_owner_id) REFERENCES users(user_id);
ALTER TABLE document_submissions ADD CONSTRAINT fk_document_submissions_parent FOREIGN KEY (parent_submission_id) REFERENCES document_submissions(submission_id);
ALTER TABLE documents ADD CONSTRAINT documents_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE documents ADD CONSTRAINT documents_parent_document_id_fkey FOREIGN KEY (parent_document_id) REFERENCES documents(document_id);
ALTER TABLE documents ADD CONSTRAINT documents_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE documents ADD CONSTRAINT documents_uploaded_by_user_id_fkey FOREIGN KEY (uploaded_by_user_id) REFERENCES users(user_id);
ALTER TABLE escalation_email_logs ADD CONSTRAINT escalation_email_logs_escalation_rule_id_fkey FOREIGN KEY (escalation_rule_id) REFERENCES sla_escalation_rules(escalation_rule_id);
ALTER TABLE escalation_email_logs ADD CONSTRAINT escalation_email_logs_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE escalation_email_logs ADD CONSTRAINT escalation_email_logs_sla_violation_id_fkey FOREIGN KEY (sla_violation_id) REFERENCES sla_violation_tracking(violation_id);
ALTER TABLE metrics_execution ADD CONSTRAINT metrics_execution_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE metrics_execution ADD CONSTRAINT metrics_execution_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE historical_data_owner_assignments ADD CONSTRAINT historical_data_owner_assignments_assigned_by_fkey FOREIGN KEY (assigned_by) REFERENCES users(user_id);
ALTER TABLE historical_data_owner_assignments ADD CONSTRAINT historical_data_owner_assignments_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE historical_data_owner_assignments ADD CONSTRAINT historical_data_owner_assignments_data_owner_id_fkey FOREIGN KEY (data_owner_id) REFERENCES users(user_id);
ALTER TABLE historical_data_provider_assignments ADD CONSTRAINT historical_data_provider_assignments_assigned_by_fkey FOREIGN KEY (assigned_by) REFERENCES users(user_id);
ALTER TABLE historical_data_provider_assignments ADD CONSTRAINT historical_data_provider_assignments_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE historical_data_provider_assignments ADD CONSTRAINT historical_data_provider_assignments_data_provider_id_fkey FOREIGN KEY (data_provider_id) REFERENCES users(user_id);
ALTER TABLE individual_samples ADD CONSTRAINT individual_samples_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE individual_samples ADD CONSTRAINT individual_samples_generated_by_user_id_fkey FOREIGN KEY (generated_by_user_id) REFERENCES users(user_id);
ALTER TABLE individual_samples ADD CONSTRAINT individual_samples_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE individual_samples ADD CONSTRAINT individual_samples_submission_id_fkey FOREIGN KEY (submission_id) REFERENCES sample_submissions(id);
ALTER TABLE individual_samples ADD CONSTRAINT individual_samples_tester_decision_by_user_id_fkey FOREIGN KEY (tester_decision_by_user_id) REFERENCES users(user_id);
ALTER TABLE llm_audit_log ADD CONSTRAINT llm_audit_log_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE llm_audit_log ADD CONSTRAINT llm_audit_log_executed_by_fkey FOREIGN KEY (executed_by) REFERENCES users(user_id);
ALTER TABLE llm_audit_log ADD CONSTRAINT llm_audit_log_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE llm_sample_generations ADD CONSTRAINT llm_sample_generations_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE llm_sample_generations ADD CONSTRAINT llm_sample_generations_generated_by_fkey FOREIGN KEY (generated_by) REFERENCES users(user_id);
ALTER TABLE llm_sample_generations ADD CONSTRAINT llm_sample_generations_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE llm_sample_generations ADD CONSTRAINT llm_sample_generations_set_id_fkey FOREIGN KEY (set_id) REFERENCES sample_sets(set_id);
ALTER TABLE cycle_report_observation_mgmt_approvals ADD CONSTRAINT observation_approvals_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES users(user_id);
ALTER TABLE cycle_report_observation_mgmt_approvals ADD CONSTRAINT observation_approvals_escalated_to_fkey FOREIGN KEY (escalated_to) REFERENCES users(user_id);
ALTER TABLE cycle_report_observation_mgmt_approvals ADD CONSTRAINT observation_approvals_observation_id_fkey FOREIGN KEY (observation_id) REFERENCES cycle_report_observation_mgmt_observation_records(observation_id);
ALTER TABLE observation_clarifications ADD CONSTRAINT observation_clarifications_group_id_fkey FOREIGN KEY (group_id) REFERENCES observation_groups(group_id);
ALTER TABLE observation_clarifications ADD CONSTRAINT observation_clarifications_requested_by_user_id_fkey FOREIGN KEY (requested_by_user_id) REFERENCES users(user_id);
ALTER TABLE observation_clarifications ADD CONSTRAINT observation_clarifications_responded_by_fkey FOREIGN KEY (responded_by) REFERENCES users(user_id);
ALTER TABLE observation_groups ADD CONSTRAINT observation_groups_attribute_id_fkey FOREIGN KEY (attribute_id) REFERENCES report_attributes(attribute_id);
ALTER TABLE observation_groups ADD CONSTRAINT observation_groups_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE observation_groups ADD CONSTRAINT observation_groups_data_executive_approved_by_fkey FOREIGN KEY (data_executive_approved_by) REFERENCES users(user_id);
ALTER TABLE observation_groups ADD CONSTRAINT observation_groups_finalized_by_fkey FOREIGN KEY (finalized_by) REFERENCES users(user_id);
ALTER TABLE observation_groups ADD CONSTRAINT observation_groups_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE observation_groups ADD CONSTRAINT observation_groups_report_owner_approved_by_fkey FOREIGN KEY (report_owner_approved_by) REFERENCES users(user_id);
ALTER TABLE cycle_report_observation_mgmt_impact_assessments ADD CONSTRAINT observation_impact_assessments_assessed_by_fkey FOREIGN KEY (assessed_by) REFERENCES users(user_id);
ALTER TABLE cycle_report_observation_mgmt_impact_assessments ADD CONSTRAINT observation_impact_assessments_observation_id_fkey FOREIGN KEY (observation_id) REFERENCES cycle_report_observation_mgmt_observation_records(observation_id);
ALTER TABLE cycle_report_observation_mgmt_impact_assessments ADD CONSTRAINT observation_impact_assessments_reviewed_by_fkey FOREIGN KEY (reviewed_by) REFERENCES users(user_id);
ALTER TABLE cycle_report_observation_mgmt_audit_logss ADD CONSTRAINT observation_management_audit_logs_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE cycle_report_observation_mgmt_audit_logss ADD CONSTRAINT observation_management_audit_logs_observation_id_fkey FOREIGN KEY (observation_id) REFERENCES cycle_report_observation_mgmt_observation_records(observation_id);
ALTER TABLE cycle_report_observation_mgmt_audit_logss ADD CONSTRAINT observation_management_audit_logs_performed_by_fkey FOREIGN KEY (performed_by) REFERENCES users(user_id);
ALTER TABLE cycle_report_observation_mgmt_audit_logss ADD CONSTRAINT observation_management_audit_logs_phase_id_fkey FOREIGN KEY (phase_id) REFERENCES observation_management_phases(phase_id);
ALTER TABLE cycle_report_observation_mgmt_audit_logss ADD CONSTRAINT observation_management_audit_logs_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE cycle_report_observation_mgmt_audit_logss ADD CONSTRAINT observation_management_audit_logs_source_test_execution_id_fkey FOREIGN KEY (source_test_execution_id) REFERENCES testing_test_executions(execution_id);
ALTER TABLE observation_management_phases ADD CONSTRAINT observation_management_phases_completed_by_fkey FOREIGN KEY (completed_by) REFERENCES users(user_id);
ALTER TABLE observation_management_phases ADD CONSTRAINT observation_management_phases_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE observation_management_phases ADD CONSTRAINT observation_management_phases_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE observation_management_phases ADD CONSTRAINT observation_management_phases_started_by_fkey FOREIGN KEY (started_by) REFERENCES users(user_id);
ALTER TABLE cycle_report_observation_mgmt_observation_records ADD CONSTRAINT observation_records_assigned_to_fkey FOREIGN KEY (assigned_to) REFERENCES users(user_id);
ALTER TABLE cycle_report_observation_mgmt_observation_records ADD CONSTRAINT observation_records_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE cycle_report_observation_mgmt_observation_records ADD CONSTRAINT observation_records_detected_by_fkey FOREIGN KEY (detected_by) REFERENCES users(user_id);
ALTER TABLE cycle_report_observation_mgmt_observation_records ADD CONSTRAINT observation_records_phase_id_fkey FOREIGN KEY (phase_id) REFERENCES observation_management_phases(phase_id);
ALTER TABLE cycle_report_observation_mgmt_observation_records ADD CONSTRAINT observation_records_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE cycle_report_observation_mgmt_observation_records ADD CONSTRAINT observation_records_source_attribute_id_fkey FOREIGN KEY (source_attribute_id) REFERENCES report_attributes(attribute_id);
ALTER TABLE cycle_report_observation_mgmt_observation_records ADD CONSTRAINT observation_records_source_test_execution_id_fkey FOREIGN KEY (source_test_execution_id) REFERENCES testing_test_executions(execution_id);
ALTER TABLE cycle_report_observation_mgmt_resolutions ADD CONSTRAINT observation_resolutions_created_by_fkey FOREIGN KEY (created_by) REFERENCES users(user_id);
ALTER TABLE cycle_report_observation_mgmt_resolutions ADD CONSTRAINT observation_resolutions_observation_id_fkey FOREIGN KEY (observation_id) REFERENCES cycle_report_observation_mgmt_observation_records(observation_id);
ALTER TABLE cycle_report_observation_mgmt_resolutions ADD CONSTRAINT observation_resolutions_resolution_owner_fkey FOREIGN KEY (resolution_owner) REFERENCES users(user_id);
ALTER TABLE cycle_report_observation_mgmt_resolutions ADD CONSTRAINT observation_resolutions_validated_by_fkey FOREIGN KEY (validated_by) REFERENCES users(user_id);
ALTER TABLE observation_versions ADD CONSTRAINT observation_versions_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE observation_versions ADD CONSTRAINT observation_versions_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE observations ADD CONSTRAINT observations_attribute_id_fkey FOREIGN KEY (attribute_id) REFERENCES report_attributes(attribute_id);
ALTER TABLE observations ADD CONSTRAINT observations_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE observations ADD CONSTRAINT observations_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE permission_audit_log ADD CONSTRAINT permission_audit_log_performed_by_fkey FOREIGN KEY (performed_by) REFERENCES users(user_id);
ALTER TABLE permission_audit_log ADD CONSTRAINT permission_audit_log_permission_id_fkey FOREIGN KEY (permission_id) REFERENCES permissions(permission_id);
ALTER TABLE permission_audit_log ADD CONSTRAINT permission_audit_log_role_id_fkey FOREIGN KEY (role_id) REFERENCES roles(role_id);
ALTER TABLE metrics_phases ADD CONSTRAINT metrics_phases_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE metrics_phases ADD CONSTRAINT metrics_phases_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE cycle_report_data_profiling_results ADD CONSTRAINT profiling_results_anomaly_marked_by_fkey FOREIGN KEY (anomaly_marked_by) REFERENCES users(user_id);
ALTER TABLE cycle_report_data_profiling_results ADD CONSTRAINT profiling_results_attribute_id_fkey FOREIGN KEY (attribute_id) REFERENCES report_attributes(attribute_id);
ALTER TABLE cycle_report_data_profiling_results ADD CONSTRAINT profiling_results_phase_id_fkey FOREIGN KEY (phase_id) REFERENCES data_profiling_phases(phase_id);
ALTER TABLE cycle_report_data_profiling_results ADD CONSTRAINT profiling_results_rule_id_fkey FOREIGN KEY (rule_id) REFERENCES cycle_report_data_profiling_rules(rule_id);
ALTER TABLE cycle_report_data_profiling_rules ADD CONSTRAINT profiling_rules_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES users(user_id);
ALTER TABLE cycle_report_data_profiling_rules ADD CONSTRAINT profiling_rules_attribute_id_fkey FOREIGN KEY (attribute_id) REFERENCES report_attributes(attribute_id);
ALTER TABLE cycle_report_data_profiling_rules ADD CONSTRAINT profiling_rules_phase_id_fkey FOREIGN KEY (phase_id) REFERENCES data_profiling_phases(phase_id);
ALTER TABLE report_attributes ADD CONSTRAINT fk_report_attributes_approved_by FOREIGN KEY (approved_by) REFERENCES users(user_id);
ALTER TABLE report_attributes ADD CONSTRAINT fk_report_attributes_archived_by FOREIGN KEY (archived_by) REFERENCES users(user_id);
ALTER TABLE report_attributes ADD CONSTRAINT fk_report_attributes_master_attribute FOREIGN KEY (master_attribute_id) REFERENCES report_attributes(attribute_id);
ALTER TABLE report_attributes ADD CONSTRAINT fk_report_attributes_replaced_attribute FOREIGN KEY (replaced_attribute_id) REFERENCES report_attributes(attribute_id);
ALTER TABLE report_attributes ADD CONSTRAINT fk_report_attributes_version_created_by FOREIGN KEY (version_created_by) REFERENCES users(user_id);
ALTER TABLE report_attributes ADD CONSTRAINT report_attributes_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE report_attributes ADD CONSTRAINT report_attributes_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE report_owner_assignment_history ADD CONSTRAINT report_owner_assignment_history_assignment_id_fkey FOREIGN KEY (assignment_id) REFERENCES report_owner_assignments(assignment_id);
ALTER TABLE report_owner_assignment_history ADD CONSTRAINT report_owner_assignment_history_changed_by_fkey FOREIGN KEY (changed_by) REFERENCES users(user_id);
ALTER TABLE report_owner_assignments ADD CONSTRAINT report_owner_assignments_assigned_by_fkey FOREIGN KEY (assigned_by) REFERENCES users(user_id);
ALTER TABLE report_owner_assignments ADD CONSTRAINT report_owner_assignments_assigned_to_fkey FOREIGN KEY (assigned_to) REFERENCES users(user_id);
ALTER TABLE report_owner_assignments ADD CONSTRAINT report_owner_assignments_completed_by_fkey FOREIGN KEY (completed_by) REFERENCES users(user_id);
ALTER TABLE report_owner_assignments ADD CONSTRAINT report_owner_assignments_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE report_owner_assignments ADD CONSTRAINT report_owner_assignments_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE report_owner_executives ADD CONSTRAINT report_owner_executives_executive_id_fkey FOREIGN KEY (executive_id) REFERENCES users(user_id);
ALTER TABLE report_owner_executives ADD CONSTRAINT report_owner_executives_report_owner_id_fkey FOREIGN KEY (report_owner_id) REFERENCES users(user_id);
ALTER TABLE cycle_report_scoping_report_owner_reviews ADD CONSTRAINT report_owner_scoping_reviews_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE cycle_report_scoping_report_owner_reviews ADD CONSTRAINT report_owner_scoping_reviews_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE cycle_report_scoping_report_owner_reviews ADD CONSTRAINT report_owner_scoping_reviews_reviewed_by_fkey FOREIGN KEY (reviewed_by) REFERENCES users(user_id);
ALTER TABLE cycle_report_scoping_report_owner_reviews ADD CONSTRAINT report_owner_scoping_reviews_submission_id_fkey FOREIGN KEY (submission_id) REFERENCES cycle_report_scoping_submissions(submission_id);
ALTER TABLE reports ADD CONSTRAINT reports_lob_id_fkey FOREIGN KEY (lob_id) REFERENCES lobs(lob_id);
ALTER TABLE reports ADD CONSTRAINT reports_report_owner_id_fkey FOREIGN KEY (report_owner_id) REFERENCES users(user_id);
ALTER TABLE request_info_audit_log ADD CONSTRAINT request_info_audit_log_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE request_info_audit_log ADD CONSTRAINT request_info_audit_log_performed_by_fkey FOREIGN KEY (performed_by) REFERENCES users(user_id);
ALTER TABLE request_info_audit_log ADD CONSTRAINT request_info_audit_log_phase_id_fkey FOREIGN KEY (phase_id) REFERENCES request_info_phases(phase_id);
ALTER TABLE request_info_audit_log ADD CONSTRAINT request_info_audit_log_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE cycle_report_request_info_audit_logs ADD CONSTRAINT request_info_audit_logs_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE cycle_report_request_info_audit_logs ADD CONSTRAINT request_info_audit_logs_performed_by_fkey FOREIGN KEY (performed_by) REFERENCES users(user_id);
ALTER TABLE cycle_report_request_info_audit_logs ADD CONSTRAINT request_info_audit_logs_phase_id_fkey FOREIGN KEY (phase_id) REFERENCES request_info_phases(phase_id);
ALTER TABLE cycle_report_request_info_audit_logs ADD CONSTRAINT request_info_audit_logs_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE request_info_phases ADD CONSTRAINT request_info_phases_completed_by_fkey FOREIGN KEY (completed_by) REFERENCES users(user_id);
ALTER TABLE request_info_phases ADD CONSTRAINT request_info_phases_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE request_info_phases ADD CONSTRAINT request_info_phases_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE request_info_phases ADD CONSTRAINT request_info_phases_started_by_fkey FOREIGN KEY (started_by) REFERENCES users(user_id);
ALTER TABLE resource_permissions ADD CONSTRAINT resource_permissions_granted_by_fkey FOREIGN KEY (granted_by) REFERENCES users(user_id);
ALTER TABLE resource_permissions ADD CONSTRAINT resource_permissions_permission_id_fkey FOREIGN KEY (permission_id) REFERENCES permissions(permission_id) ON DELETE CASCADE;
ALTER TABLE resource_permissions ADD CONSTRAINT resource_permissions_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE;
ALTER TABLE resources ADD CONSTRAINT resources_parent_resource_id_fkey FOREIGN KEY (parent_resource_id) REFERENCES resources(resource_id);
ALTER TABLE role_hierarchy ADD CONSTRAINT role_hierarchy_child_role_id_fkey FOREIGN KEY (child_role_id) REFERENCES roles(role_id) ON DELETE CASCADE;
ALTER TABLE role_hierarchy ADD CONSTRAINT role_hierarchy_parent_role_id_fkey FOREIGN KEY (parent_role_id) REFERENCES roles(role_id) ON DELETE CASCADE;
ALTER TABLE role_permissions ADD CONSTRAINT role_permissions_granted_by_fkey FOREIGN KEY (granted_by) REFERENCES users(user_id);
ALTER TABLE role_permissions ADD CONSTRAINT role_permissions_permission_id_fkey FOREIGN KEY (permission_id) REFERENCES permissions(permission_id) ON DELETE CASCADE;
ALTER TABLE role_permissions ADD CONSTRAINT role_permissions_role_id_fkey FOREIGN KEY (role_id) REFERENCES roles(role_id) ON DELETE CASCADE;
ALTER TABLE sample_approval_history ADD CONSTRAINT sample_approval_history_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES users(user_id);
ALTER TABLE sample_approval_history ADD CONSTRAINT sample_approval_history_set_id_fkey FOREIGN KEY (set_id) REFERENCES sample_sets(set_id);
ALTER TABLE sample_audit_logs ADD CONSTRAINT sample_audit_logs_sample_id_fkey FOREIGN KEY (sample_id) REFERENCES individual_samples(id);
ALTER TABLE sample_audit_logs ADD CONSTRAINT sample_audit_logs_submission_id_fkey FOREIGN KEY (submission_id) REFERENCES sample_submissions(id);
ALTER TABLE sample_audit_logs ADD CONSTRAINT sample_audit_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(user_id);
ALTER TABLE sample_feedback ADD CONSTRAINT sample_feedback_created_by_user_id_fkey FOREIGN KEY (created_by_user_id) REFERENCES users(user_id);
ALTER TABLE sample_feedback ADD CONSTRAINT sample_feedback_resolved_by_user_id_fkey FOREIGN KEY (resolved_by_user_id) REFERENCES users(user_id);
ALTER TABLE sample_feedback ADD CONSTRAINT sample_feedback_sample_id_fkey FOREIGN KEY (sample_id) REFERENCES individual_samples(id);
ALTER TABLE sample_feedback ADD CONSTRAINT sample_feedback_submission_id_fkey FOREIGN KEY (submission_id) REFERENCES sample_submissions(id);
ALTER TABLE sample_records ADD CONSTRAINT fk_sample_records_approved_by FOREIGN KEY (approved_by) REFERENCES users(user_id);
ALTER TABLE sample_records ADD CONSTRAINT sample_records_set_id_fkey FOREIGN KEY (set_id) REFERENCES sample_sets(set_id);
ALTER TABLE sample_selection_audit_log ADD CONSTRAINT sample_selection_audit_log_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE sample_selection_audit_log ADD CONSTRAINT sample_selection_audit_log_performed_by_fkey FOREIGN KEY (performed_by) REFERENCES users(user_id);
ALTER TABLE sample_selection_audit_log ADD CONSTRAINT sample_selection_audit_log_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE sample_selection_audit_log ADD CONSTRAINT sample_selection_audit_log_set_id_fkey FOREIGN KEY (set_id) REFERENCES sample_sets(set_id);
ALTER TABLE sample_selection_phases ADD CONSTRAINT sample_selection_phases_created_by_fkey FOREIGN KEY (created_by) REFERENCES users(user_id);
ALTER TABLE sample_selection_phases ADD CONSTRAINT sample_selection_phases_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE sample_selection_phases ADD CONSTRAINT sample_selection_phases_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE sample_selection_phases ADD CONSTRAINT sample_selection_phases_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES users(user_id);
ALTER TABLE sample_sets ADD CONSTRAINT sample_sets_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES users(user_id);
ALTER TABLE sample_sets ADD CONSTRAINT sample_sets_created_by_fkey FOREIGN KEY (created_by) REFERENCES users(user_id);
ALTER TABLE sample_sets ADD CONSTRAINT sample_sets_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE sample_sets ADD CONSTRAINT sample_sets_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE sample_submission_items ADD CONSTRAINT sample_submission_items_sample_id_fkey FOREIGN KEY (sample_id) REFERENCES individual_samples(id);
ALTER TABLE sample_submission_items ADD CONSTRAINT sample_submission_items_submission_id_fkey FOREIGN KEY (submission_id) REFERENCES sample_submissions(id);
ALTER TABLE sample_submissions ADD CONSTRAINT sample_submissions_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE sample_submissions ADD CONSTRAINT sample_submissions_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE sample_submissions ADD CONSTRAINT sample_submissions_reviewed_by_user_id_fkey FOREIGN KEY (reviewed_by_user_id) REFERENCES users(user_id);
ALTER TABLE sample_submissions ADD CONSTRAINT sample_submissions_submitted_by_user_id_fkey FOREIGN KEY (submitted_by_user_id) REFERENCES users(user_id);
ALTER TABLE sample_upload_history ADD CONSTRAINT sample_upload_history_set_id_fkey FOREIGN KEY (set_id) REFERENCES sample_sets(set_id);
ALTER TABLE sample_upload_history ADD CONSTRAINT sample_upload_history_uploaded_by_fkey FOREIGN KEY (uploaded_by) REFERENCES users(user_id);
ALTER TABLE sample_validation_issues ADD CONSTRAINT sample_validation_issues_record_id_fkey FOREIGN KEY (record_id) REFERENCES sample_records(record_id);
ALTER TABLE sample_validation_issues ADD CONSTRAINT sample_validation_issues_resolved_by_fkey FOREIGN KEY (resolved_by) REFERENCES users(user_id);
ALTER TABLE sample_validation_issues ADD CONSTRAINT sample_validation_issues_validation_id_fkey FOREIGN KEY (validation_id) REFERENCES sample_validation_results(validation_id);
ALTER TABLE sample_validation_results ADD CONSTRAINT sample_validation_results_set_id_fkey FOREIGN KEY (set_id) REFERENCES sample_sets(set_id);
ALTER TABLE sample_validation_results ADD CONSTRAINT sample_validation_results_validated_by_fkey FOREIGN KEY (validated_by) REFERENCES users(user_id);
ALTER TABLE cycle_report_sample_selection_samples ADD CONSTRAINT samples_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE cycle_report_sample_selection_samples ADD CONSTRAINT samples_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE scoping_audit_log ADD CONSTRAINT scoping_audit_log_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE scoping_audit_log ADD CONSTRAINT scoping_audit_log_performed_by_fkey FOREIGN KEY (performed_by) REFERENCES users(user_id);
ALTER TABLE scoping_audit_log ADD CONSTRAINT scoping_audit_log_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE cycle_report_scoping_decision_versions ADD CONSTRAINT scoping_decision_versions_attribute_id_fkey FOREIGN KEY (attribute_id) REFERENCES report_attributes(attribute_id);
ALTER TABLE cycle_report_scoping_decision_versions ADD CONSTRAINT scoping_decision_versions_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE cycle_report_scoping_decision_versions ADD CONSTRAINT scoping_decision_versions_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE cycle_report_scoping_submissions ADD CONSTRAINT fk_scoping_submissions_previous_version FOREIGN KEY (previous_version_id) REFERENCES cycle_report_scoping_submissions(submission_id);
ALTER TABLE cycle_report_scoping_submissions ADD CONSTRAINT scoping_submissions_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE cycle_report_scoping_submissions ADD CONSTRAINT scoping_submissions_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE cycle_report_scoping_submissions ADD CONSTRAINT scoping_submissions_submitted_by_fkey FOREIGN KEY (submitted_by) REFERENCES users(user_id);
ALTER TABLE sla_escalation_rules ADD CONSTRAINT sla_escalation_rules_escalate_to_user_id_fkey FOREIGN KEY (escalate_to_user_id) REFERENCES users(user_id);
ALTER TABLE sla_escalation_rules ADD CONSTRAINT sla_escalation_rules_sla_config_id_fkey FOREIGN KEY (sla_config_id) REFERENCES sla_configurations(sla_config_id);
ALTER TABLE sla_violation_tracking ADD CONSTRAINT sla_violation_tracking_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE sla_violation_tracking ADD CONSTRAINT sla_violation_tracking_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE sla_violation_tracking ADD CONSTRAINT sla_violation_tracking_sla_config_id_fkey FOREIGN KEY (sla_config_id) REFERENCES sla_configurations(sla_config_id);
ALTER TABLE submission_documents ADD CONSTRAINT submission_documents_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE submission_documents ADD CONSTRAINT submission_documents_data_provider_id_fkey FOREIGN KEY (data_provider_id) REFERENCES users(user_id);
ALTER TABLE submission_documents ADD CONSTRAINT submission_documents_phase_id_fkey FOREIGN KEY (phase_id) REFERENCES request_info_phases(phase_id);
ALTER TABLE submission_documents ADD CONSTRAINT submission_documents_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE submission_reminders ADD CONSTRAINT submission_reminders_data_provider_id_fkey FOREIGN KEY (data_provider_id) REFERENCES users(user_id);
ALTER TABLE submission_reminders ADD CONSTRAINT submission_reminders_phase_id_fkey FOREIGN KEY (phase_id) REFERENCES request_info_phases(phase_id);
ALTER TABLE submission_validations ADD CONSTRAINT submission_validations_submission_id_fkey FOREIGN KEY (submission_id) REFERENCES data_provider_submissions(submission_id);
ALTER TABLE test_cases ADD CONSTRAINT test_cases_assigned_by_fkey FOREIGN KEY (assigned_by) REFERENCES users(user_id);
ALTER TABLE test_cases ADD CONSTRAINT test_cases_attribute_id_fkey FOREIGN KEY (attribute_id) REFERENCES report_attributes(attribute_id);
ALTER TABLE test_cases ADD CONSTRAINT test_cases_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE test_cases ADD CONSTRAINT test_cases_data_provider_id_fkey FOREIGN KEY (data_owner_id) REFERENCES users(user_id);
ALTER TABLE test_cases ADD CONSTRAINT test_cases_phase_id_fkey FOREIGN KEY (phase_id) REFERENCES request_info_phases(phase_id);
ALTER TABLE test_cases ADD CONSTRAINT test_cases_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE test_comparisons ADD CONSTRAINT test_comparisons_compared_by_fkey FOREIGN KEY (compared_by) REFERENCES users(user_id);
ALTER TABLE test_cycles ADD CONSTRAINT test_cycles_test_manager_id_fkey FOREIGN KEY (test_manager_id) REFERENCES users(user_id);
ALTER TABLE cycle_report_test_execution_audit_logss ADD CONSTRAINT test_execution_audit_logs_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE cycle_report_test_execution_audit_logss ADD CONSTRAINT test_execution_audit_logs_performed_by_fkey FOREIGN KEY (performed_by) REFERENCES users(user_id);
ALTER TABLE cycle_report_test_execution_audit_logss ADD CONSTRAINT test_execution_audit_logs_phase_id_fkey FOREIGN KEY (phase_id) REFERENCES test_execution_phases(phase_id);
ALTER TABLE cycle_report_test_execution_audit_logss ADD CONSTRAINT test_execution_audit_logs_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE test_execution_phases ADD CONSTRAINT test_execution_phases_completed_by_fkey FOREIGN KEY (completed_by) REFERENCES users(user_id);
ALTER TABLE test_execution_phases ADD CONSTRAINT test_execution_phases_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE test_execution_phases ADD CONSTRAINT test_execution_phases_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE test_execution_phases ADD CONSTRAINT test_execution_phases_started_by_fkey FOREIGN KEY (started_by) REFERENCES users(user_id);
ALTER TABLE test_execution_versions ADD CONSTRAINT test_execution_versions_attribute_id_fkey FOREIGN KEY (attribute_id) REFERENCES report_attributes(attribute_id);
ALTER TABLE test_execution_versions ADD CONSTRAINT test_execution_versions_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE test_execution_versions ADD CONSTRAINT test_execution_versions_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE test_execution_versions ADD CONSTRAINT test_execution_versions_sample_id_fkey FOREIGN KEY (sample_id) REFERENCES cycle_report_sample_selection_samples(sample_id);
ALTER TABLE cycle_report_test_execution_test_executions ADD CONSTRAINT test_executions_attribute_id_fkey FOREIGN KEY (attribute_id) REFERENCES report_attributes(attribute_id);
ALTER TABLE cycle_report_test_execution_test_executions ADD CONSTRAINT test_executions_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE cycle_report_test_execution_test_executions ADD CONSTRAINT test_executions_data_source_id_fkey FOREIGN KEY (data_source_id) REFERENCES data_sources(data_source_id);
ALTER TABLE cycle_report_test_execution_test_executions ADD CONSTRAINT test_executions_document_id_fkey FOREIGN KEY (document_id) REFERENCES documents(document_id);
ALTER TABLE cycle_report_test_execution_test_executions ADD CONSTRAINT test_executions_executed_by_fkey FOREIGN KEY (executed_by) REFERENCES users(user_id);
ALTER TABLE cycle_report_test_execution_test_executions ADD CONSTRAINT test_executions_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE cycle_report_test_execution_test_executions ADD CONSTRAINT test_executions_sample_id_fkey FOREIGN KEY (sample_id) REFERENCES cycle_report_sample_selection_samples(sample_id);
ALTER TABLE test_report_phases ADD CONSTRAINT test_report_phases_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE test_report_phases ADD CONSTRAINT test_report_phases_final_report_document_id_fkey FOREIGN KEY (final_report_document_id) REFERENCES documents(document_id);
ALTER TABLE test_report_phases ADD CONSTRAINT test_report_phases_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE cycle_report_test_report_sections ADD CONSTRAINT test_report_sections_phase_id_fkey FOREIGN KEY (phase_id) REFERENCES test_report_phases(phase_id);
ALTER TABLE test_result_reviews ADD CONSTRAINT test_result_reviews_execution_id_fkey FOREIGN KEY (execution_id) REFERENCES testing_test_executions(execution_id);
ALTER TABLE test_result_reviews ADD CONSTRAINT test_result_reviews_reviewer_id_fkey FOREIGN KEY (reviewer_id) REFERENCES users(user_id);
ALTER TABLE cycle_report_scoping_tester_decisions ADD CONSTRAINT tester_scoping_decisions_attribute_id_fkey FOREIGN KEY (attribute_id) REFERENCES report_attributes(attribute_id);
ALTER TABLE cycle_report_scoping_tester_decisions ADD CONSTRAINT tester_scoping_decisions_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE cycle_report_scoping_tester_decisions ADD CONSTRAINT tester_scoping_decisions_decided_by_fkey FOREIGN KEY (decided_by) REFERENCES users(user_id);
ALTER TABLE cycle_report_scoping_tester_decisions ADD CONSTRAINT tester_scoping_decisions_recommendation_id_fkey FOREIGN KEY (recommendation_id) REFERENCES cycle_report_scoping_attribute_recommendations(recommendation_id);
ALTER TABLE cycle_report_scoping_tester_decisions ADD CONSTRAINT tester_scoping_decisions_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE testing_execution_audit_logs ADD CONSTRAINT testing_execution_audit_logs_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE testing_execution_audit_logs ADD CONSTRAINT testing_execution_audit_logs_performed_by_fkey FOREIGN KEY (performed_by) REFERENCES users(user_id);
ALTER TABLE testing_execution_audit_logs ADD CONSTRAINT testing_execution_audit_logs_phase_id_fkey FOREIGN KEY (phase_id) REFERENCES testing_execution_phases(phase_id);
ALTER TABLE testing_execution_audit_logs ADD CONSTRAINT testing_execution_audit_logs_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE testing_execution_phases ADD CONSTRAINT testing_execution_phases_completed_by_fkey FOREIGN KEY (completed_by) REFERENCES users(user_id);
ALTER TABLE testing_execution_phases ADD CONSTRAINT testing_execution_phases_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE testing_execution_phases ADD CONSTRAINT testing_execution_phases_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE testing_execution_phases ADD CONSTRAINT testing_execution_phases_started_by_fkey FOREIGN KEY (started_by) REFERENCES users(user_id);
ALTER TABLE testing_test_executions ADD CONSTRAINT fk_testing_test_executions_data_source FOREIGN KEY (data_source_id) REFERENCES data_sources(data_source_id);
ALTER TABLE testing_test_executions ADD CONSTRAINT fk_testing_test_executions_executed_by FOREIGN KEY (executed_by) REFERENCES users(user_id);
ALTER TABLE testing_test_executions ADD CONSTRAINT fk_testing_test_executions_sample FOREIGN KEY (sample_id) REFERENCES cycle_report_sample_selection_samples(sample_id);
ALTER TABLE testing_test_executions ADD CONSTRAINT testing_test_executions_assigned_tester_id_fkey FOREIGN KEY (assigned_tester_id) REFERENCES users(user_id);
ALTER TABLE testing_test_executions ADD CONSTRAINT testing_test_executions_attribute_id_fkey FOREIGN KEY (attribute_id) REFERENCES report_attributes(attribute_id);
ALTER TABLE testing_test_executions ADD CONSTRAINT testing_test_executions_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE testing_test_executions ADD CONSTRAINT testing_test_executions_database_test_id_fkey FOREIGN KEY (database_test_id) REFERENCES cycle_report_test_execution_database_tests(test_id);
ALTER TABLE testing_test_executions ADD CONSTRAINT testing_test_executions_document_analysis_id_fkey FOREIGN KEY (document_analysis_id) REFERENCES cycle_report_test_execution_document_analyses(analysis_id);
ALTER TABLE testing_test_executions ADD CONSTRAINT testing_test_executions_phase_id_fkey FOREIGN KEY (phase_id) REFERENCES test_execution_phases(phase_id);
ALTER TABLE testing_test_executions ADD CONSTRAINT testing_test_executions_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE universal_assignment_history ADD CONSTRAINT universal_assignment_history_assignment_id_fkey FOREIGN KEY (assignment_id) REFERENCES universal_assignments(assignment_id);
ALTER TABLE universal_assignment_history ADD CONSTRAINT universal_assignment_history_changed_by_user_id_fkey FOREIGN KEY (changed_by_user_id) REFERENCES users(user_id);
ALTER TABLE universal_assignments ADD CONSTRAINT universal_assignments_approved_by_user_id_fkey FOREIGN KEY (approved_by_user_id) REFERENCES users(user_id);
ALTER TABLE universal_assignments ADD CONSTRAINT universal_assignments_completed_by_user_id_fkey FOREIGN KEY (completed_by_user_id) REFERENCES users(user_id);
ALTER TABLE universal_assignments ADD CONSTRAINT universal_assignments_delegated_to_user_id_fkey FOREIGN KEY (delegated_to_user_id) REFERENCES users(user_id);
ALTER TABLE universal_assignments ADD CONSTRAINT universal_assignments_escalated_to_user_id_fkey FOREIGN KEY (escalated_to_user_id) REFERENCES users(user_id);
ALTER TABLE universal_assignments ADD CONSTRAINT universal_assignments_from_user_id_fkey FOREIGN KEY (from_user_id) REFERENCES users(user_id);
ALTER TABLE universal_assignments ADD CONSTRAINT universal_assignments_parent_assignment_id_fkey FOREIGN KEY (parent_assignment_id) REFERENCES universal_assignments(assignment_id);
ALTER TABLE universal_assignments ADD CONSTRAINT universal_assignments_to_user_id_fkey FOREIGN KEY (to_user_id) REFERENCES users(user_id);
ALTER TABLE user_permissions ADD CONSTRAINT user_permissions_granted_by_fkey FOREIGN KEY (granted_by) REFERENCES users(user_id);
ALTER TABLE user_permissions ADD CONSTRAINT user_permissions_permission_id_fkey FOREIGN KEY (permission_id) REFERENCES permissions(permission_id) ON DELETE CASCADE;
ALTER TABLE user_permissions ADD CONSTRAINT user_permissions_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE;
ALTER TABLE user_roles ADD CONSTRAINT user_roles_assigned_by_fkey FOREIGN KEY (assigned_by) REFERENCES users(user_id);
ALTER TABLE user_roles ADD CONSTRAINT user_roles_role_id_fkey FOREIGN KEY (role_id) REFERENCES roles(role_id) ON DELETE CASCADE;
ALTER TABLE user_roles ADD CONSTRAINT user_roles_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE;
ALTER TABLE users ADD CONSTRAINT users_lob_id_fkey FOREIGN KEY (lob_id) REFERENCES lobs(lob_id);
ALTER TABLE workflow_activities ADD CONSTRAINT workflow_activities_completed_by_fkey FOREIGN KEY (completed_by) REFERENCES users(user_id);
ALTER TABLE workflow_activities ADD CONSTRAINT workflow_activities_revision_requested_by_fkey FOREIGN KEY (revision_requested_by) REFERENCES users(user_id);
ALTER TABLE workflow_activities ADD CONSTRAINT workflow_activities_started_by_fkey FOREIGN KEY (started_by) REFERENCES users(user_id);
ALTER TABLE workflow_activity_history ADD CONSTRAINT workflow_activity_history_activity_id_fkey FOREIGN KEY (activity_id) REFERENCES workflow_activities(activity_id);
ALTER TABLE workflow_activity_history ADD CONSTRAINT workflow_activity_history_changed_by_fkey FOREIGN KEY (changed_by) REFERENCES users(user_id);
ALTER TABLE workflow_alerts ADD CONSTRAINT workflow_alerts_acknowledged_by_fkey FOREIGN KEY (acknowledged_by) REFERENCES users(user_id);
ALTER TABLE workflow_alerts ADD CONSTRAINT workflow_alerts_execution_id_fkey FOREIGN KEY (execution_id) REFERENCES workflow_executions(execution_id);
ALTER TABLE workflow_executions ADD CONSTRAINT workflow_executions_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE workflow_executions ADD CONSTRAINT workflow_executions_initiated_by_fkey FOREIGN KEY (initiated_by) REFERENCES users(user_id);
ALTER TABLE workflow_executions ADD CONSTRAINT workflow_executions_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE workflow_phases ADD CONSTRAINT fk_workflow_phases_completed_by FOREIGN KEY (completed_by) REFERENCES users(user_id);
ALTER TABLE workflow_phases ADD CONSTRAINT fk_workflow_phases_override_by FOREIGN KEY (override_by) REFERENCES users(user_id);
ALTER TABLE workflow_phases ADD CONSTRAINT fk_workflow_phases_started_by FOREIGN KEY (started_by) REFERENCES users(user_id);
ALTER TABLE workflow_phases ADD CONSTRAINT workflow_phases_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);
ALTER TABLE workflow_phases ADD CONSTRAINT workflow_phases_report_id_fkey FOREIGN KEY (report_id) REFERENCES reports(report_id);
ALTER TABLE workflow_steps ADD CONSTRAINT workflow_steps_execution_id_fkey FOREIGN KEY (execution_id) REFERENCES workflow_executions(execution_id);
ALTER TABLE workflow_steps ADD CONSTRAINT workflow_steps_parent_step_id_fkey FOREIGN KEY (parent_step_id) REFERENCES workflow_steps(step_id);
ALTER TABLE workflow_transitions ADD CONSTRAINT workflow_transitions_execution_id_fkey FOREIGN KEY (execution_id) REFERENCES workflow_executions(execution_id);
ALTER TABLE workflow_transitions ADD CONSTRAINT workflow_transitions_from_step_id_fkey FOREIGN KEY (from_step_id) REFERENCES workflow_steps(step_id);
ALTER TABLE workflow_transitions ADD CONSTRAINT workflow_transitions_to_step_id_fkey FOREIGN KEY (to_step_id) REFERENCES workflow_steps(step_id);

-- Create indexes
CREATE INDEX ix_assignment_templates_template_id ON assignment_templates USING btree (template_id);
CREATE INDEX ix_attribute_lob_assignments_assignment_id ON attribute_lob_assignments USING btree (assignment_id);
CREATE INDEX ix_attribute_profiling_scores_score_id ON attribute_profiling_scores USING btree (score_id);
CREATE INDEX ix_attribute_scoping_recommendations_recommendation_id ON attribute_scoping_recommendations USING btree (recommendation_id);
CREATE INDEX ix_attribute_version_change_logs_log_id ON attribute_version_change_logs USING btree (log_id);
CREATE INDEX ix_attribute_version_comparisons_comparison_id ON attribute_version_comparisons USING btree (comparison_id);
CREATE INDEX ix_audit_log_action ON audit_log USING btree (action);
CREATE INDEX ix_audit_log_audit_id ON audit_log USING btree (audit_id);
CREATE INDEX ix_bulk_test_executions_bulk_execution_id ON bulk_test_executions USING btree (bulk_execution_id);
CREATE INDEX ix_cdo_notifications_notification_id ON cdo_notifications USING btree (notification_id);
CREATE INDEX idx_cycle_reports_workflow_id ON cycle_reports USING btree (workflow_id);
CREATE INDEX ix_data_owner_assignments_assignment_id ON data_owner_assignments USING btree (assignment_id);
CREATE INDEX ix_data_owner_escalation_log_email_id ON data_owner_escalation_log USING btree (email_id);
CREATE INDEX ix_data_owner_notifications_notification_id ON data_owner_notifications USING btree (notification_id);
CREATE INDEX ix_data_owner_phase_audit_log_action ON data_owner_phase_audit_log USING btree (action);
CREATE INDEX ix_data_owner_phase_audit_log_audit_id ON data_owner_phase_audit_log USING btree (audit_id);
CREATE INDEX ix_data_owner_sla_violations_violation_id ON data_owner_sla_violations USING btree (violation_id);
CREATE INDEX ix_data_profiling_files_file_id ON data_profiling_files USING btree (file_id);
CREATE INDEX ix_data_profiling_phases_phase_id ON data_profiling_phases USING btree (phase_id);
CREATE INDEX ix_data_provider_assignments_assignment_id ON data_provider_assignments USING btree (assignment_id);
CREATE INDEX ix_data_provider_escalation_log_email_id ON data_provider_escalation_log USING btree (email_id);
CREATE INDEX ix_data_provider_notifications_notification_id ON data_provider_notifications USING btree (notification_id);
CREATE INDEX ix_data_provider_phase_audit_log_action ON data_provider_phase_audit_log USING btree (action);
CREATE INDEX ix_data_provider_phase_audit_log_audit_id ON data_provider_phase_audit_log USING btree (audit_id);
CREATE INDEX ix_data_provider_sla_violations_violation_id ON data_provider_sla_violations USING btree (violation_id);
CREATE INDEX ix_data_provider_submissions_submission_id ON data_provider_submissions USING btree (submission_id);
CREATE INDEX ix_data_sources_data_source_id ON data_sources USING btree (data_source_id);
CREATE INDEX ix_data_sources_data_source_name ON data_sources USING btree (data_source_name);
CREATE INDEX ix_database_submissions_db_submission_id ON database_submissions USING btree (db_submission_id);
CREATE INDEX ix_database_tests_test_id ON database_tests USING btree (test_id);
CREATE INDEX ix_document_access_logs_log_id ON document_access_logs USING btree (log_id);
CREATE INDEX ix_document_analyses_analysis_id ON document_analyses USING btree (analysis_id);
CREATE INDEX ix_document_extractions_extraction_id ON document_extractions USING btree (extraction_id);
CREATE INDEX ix_document_extractions_attribute_name ON document_extractions USING btree (attribute_name);
CREATE INDEX ix_document_submissions_submission_id ON document_submissions USING btree (submission_id);
CREATE INDEX idx_document_submissions_current ON document_submissions USING btree (test_case_id, is_current);
CREATE INDEX idx_document_submissions_parent ON document_submissions USING btree (parent_submission_id);
CREATE INDEX ix_document_submissions_data_owner_id ON document_submissions USING btree (data_owner_id);
CREATE INDEX ix_documents_document_type ON documents USING btree (document_type);
CREATE INDEX ix_documents_document_id ON documents USING btree (document_id);
CREATE INDEX ix_documents_file_hash ON documents USING btree (file_hash);
CREATE INDEX ix_documents_document_name ON documents USING btree (document_name);
CREATE INDEX ix_escalation_email_logs_log_id ON escalation_email_logs USING btree (log_id);
CREATE INDEX idx_metrics_execution_cycle_id ON metrics_execution USING btree (cycle_id);
CREATE INDEX idx_metrics_execution_report_id ON metrics_execution USING btree (report_id);
CREATE INDEX ix_historical_data_owner_assignments_report_name ON historical_data_owner_assignments USING btree (report_name);
CREATE INDEX ix_historical_data_owner_assignments_attribute_name ON historical_data_owner_assignments USING btree (attribute_name);
CREATE INDEX ix_historical_data_owner_assignments_history_id ON historical_data_owner_assignments USING btree (history_id);
CREATE INDEX ix_historical_data_provider_assignments_attribute_name ON historical_data_provider_assignments USING btree (attribute_name);
CREATE INDEX ix_historical_data_provider_assignments_history_id ON historical_data_provider_assignments USING btree (history_id);
CREATE INDEX ix_historical_data_provider_assignments_report_name ON historical_data_provider_assignments USING btree (report_name);
CREATE UNIQUE INDEX ix_individual_samples_sample_id ON individual_samples USING btree (sample_id);
CREATE INDEX ix_individual_samples_id ON individual_samples USING btree (id);
CREATE INDEX ix_individual_samples_cycle_report ON individual_samples USING btree (cycle_id, report_id);
CREATE INDEX ix_llm_audit_log_llm_provider ON llm_audit_log USING btree (llm_provider);
CREATE INDEX ix_llm_audit_log_log_id ON llm_audit_log USING btree (log_id);
CREATE INDEX idx_llm_generations_cycle_report ON llm_sample_generations USING btree (cycle_id, report_id);
CREATE INDEX ix_llm_sample_generations_generation_id ON llm_sample_generations USING btree (generation_id);
CREATE INDEX idx_llm_generations_generated_at ON llm_sample_generations USING btree (generated_at);
CREATE UNIQUE INDEX ix_lobs_lob_name ON lobs USING btree (lob_name);
CREATE INDEX ix_lobs_lob_id ON lobs USING btree (lob_id);
CREATE UNIQUE INDEX _observation_group_uc ON observation_groups USING btree (cycle_id, report_id, attribute_id, issue_type);
CREATE INDEX ix_observations_observation_id ON observations USING btree (observation_id);
CREATE INDEX ix_permission_audit_log_performed_at ON permission_audit_log USING btree (performed_at);
CREATE INDEX ix_permission_audit_log_target_type ON permission_audit_log USING btree (target_type);
CREATE INDEX ix_permission_audit_log_target_id ON permission_audit_log USING btree (target_id);
CREATE INDEX ix_permission_audit_log_audit_id ON permission_audit_log USING btree (audit_id);
CREATE UNIQUE INDEX uq_resource_action ON permissions USING btree (resource, action);
CREATE INDEX ix_permissions_action ON permissions USING btree (action);
CREATE INDEX ix_permissions_permission_id ON permissions USING btree (permission_id);
CREATE INDEX ix_permissions_resource ON permissions USING btree (resource);
CREATE INDEX idx_metrics_phases_cycle_id ON metrics_phases USING btree (cycle_id);
CREATE INDEX idx_metrics_phases_report_id ON metrics_phases USING btree (report_id);
CREATE INDEX idx_metrics_phases_phase_name ON metrics_phases USING btree (phase_name);
CREATE INDEX ix_profiling_results_result_id ON profiling_results USING btree (result_id);
CREATE INDEX ix_profiling_rules_rule_id ON profiling_rules USING btree (rule_id);
CREATE INDEX ix_profiling_rules_business_key ON profiling_rules USING btree (business_key);
CREATE INDEX ix_profiling_rules_current_version ON profiling_rules USING btree (is_current_version);
CREATE INDEX ix_profiling_rules_version_number ON profiling_rules USING btree (version_number);
CREATE INDEX ix_rdd_item_name_search ON regulatory_data_dictionary USING btree (line_item_name);
CREATE INDEX ix_regulatory_data_dictionary_schedule_name ON regulatory_data_dictionary USING btree (schedule_name);
CREATE INDEX ix_rdd_report_schedule ON regulatory_data_dictionary USING btree (report_name, schedule_name);
CREATE INDEX ix_regulatory_data_dictionary_mandatory_or_optional ON regulatory_data_dictionary USING btree (mandatory_or_optional);
CREATE INDEX ix_rdd_mandatory_search ON regulatory_data_dictionary USING btree (mandatory_or_optional);
CREATE INDEX ix_regulatory_data_dictionary_line_item_name ON regulatory_data_dictionary USING btree (line_item_name);
CREATE INDEX ix_regulatory_data_dictionary_report_name ON regulatory_data_dictionary USING btree (report_name);
CREATE INDEX ix_report_attributes_attribute_name ON report_attributes USING btree (attribute_name);
CREATE INDEX ix_report_attributes_attribute_id ON report_attributes USING btree (attribute_id);
CREATE INDEX ix_report_attributes_master_attribute_id ON report_attributes USING btree (master_attribute_id);
CREATE INDEX idx_ro_assignment_history_assignment ON report_owner_assignment_history USING btree (assignment_id);
CREATE INDEX ix_report_owner_assignment_history_history_id ON report_owner_assignment_history USING btree (history_id);
CREATE INDEX idx_ro_assignment_history_changed_at ON report_owner_assignment_history USING btree (changed_at);
CREATE INDEX idx_ro_assignments_phase ON report_owner_assignments USING btree (phase_name);
CREATE INDEX idx_ro_assignments_assigned_to ON report_owner_assignments USING btree (assigned_to);
CREATE INDEX ix_report_owner_assignments_assignment_id ON report_owner_assignments USING btree (assignment_id);
CREATE INDEX idx_ro_assignments_due_date ON report_owner_assignments USING btree (due_date);
CREATE INDEX idx_ro_assignments_cycle_report ON report_owner_assignments USING btree (cycle_id, report_id);
CREATE INDEX ix_report_owner_assignments_phase_name ON report_owner_assignments USING btree (phase_name);
CREATE INDEX idx_ro_assignments_status ON report_owner_assignments USING btree (status);
CREATE INDEX idx_ro_assignments_created_at ON report_owner_assignments USING btree (created_at);
CREATE INDEX ix_report_owner_scoping_reviews_review_id ON report_owner_scoping_reviews USING btree (review_id);
CREATE INDEX ix_reports_report_name ON reports USING btree (report_name);
CREATE INDEX ix_reports_report_id ON reports USING btree (report_id);
CREATE INDEX ix_request_info_audit_log_audit_id ON request_info_audit_log USING btree (audit_id);
CREATE INDEX ix_request_info_audit_log_action ON request_info_audit_log USING btree (action);
CREATE INDEX ix_request_info_audit_logs_log_id ON request_info_audit_logs USING btree (log_id);
CREATE INDEX ix_request_info_phases_phase_id ON request_info_phases USING btree (phase_id);
CREATE UNIQUE INDEX uq_user_resource_permission ON resource_permissions USING btree (user_id, resource_type, resource_id, permission_id);
CREATE INDEX ix_resource_permissions_resource_id ON resource_permissions USING btree (resource_id);
CREATE INDEX ix_resource_permissions_user_id ON resource_permissions USING btree (user_id);
CREATE INDEX ix_resource_permissions_resource_type ON resource_permissions USING btree (resource_type);
CREATE INDEX ix_resource_permissions_resource_permission_id ON resource_permissions USING btree (resource_permission_id);
CREATE UNIQUE INDEX ix_resources_resource_name ON resources USING btree (resource_name);
CREATE INDEX ix_resources_resource_id ON resources USING btree (resource_id);
CREATE INDEX ix_resources_resource_type ON resources USING btree (resource_type);
CREATE UNIQUE INDEX ix_roles_role_name ON roles USING btree (role_name);
CREATE INDEX ix_roles_role_id ON roles USING btree (role_id);
CREATE INDEX ix_sample_approval_history_approval_id ON sample_approval_history USING btree (approval_id);
CREATE INDEX idx_approval_history_approved_at ON sample_approval_history USING btree (approved_at);
CREATE INDEX idx_approval_history_set_id ON sample_approval_history USING btree (set_id);
CREATE INDEX idx_approval_history_decision ON sample_approval_history USING btree (decision);
CREATE INDEX ix_sample_audit_logs_id ON sample_audit_logs USING btree (id);
CREATE INDEX ix_sample_audit_logs_sample ON sample_audit_logs USING btree (sample_id);
CREATE INDEX ix_sample_feedback_id ON sample_feedback USING btree (id);
CREATE INDEX ix_sample_feedback_sample_submission ON sample_feedback USING btree (sample_id, submission_id);
CREATE INDEX idx_sample_records_identifier ON sample_records USING btree (sample_identifier);
CREATE INDEX ix_sample_records_record_id ON sample_records USING btree (record_id);
CREATE INDEX idx_sample_records_validation_status ON sample_records USING btree (validation_status);
CREATE INDEX ix_sample_records_sample_identifier ON sample_records USING btree (sample_identifier);
CREATE INDEX idx_sample_records_set_id ON sample_records USING btree (set_id);
CREATE INDEX ix_sample_selection_audit_log_audit_id ON sample_selection_audit_log USING btree (audit_id);
CREATE INDEX idx_sample_audit_entity ON sample_selection_audit_log USING btree (entity_type, entity_id);
CREATE INDEX idx_sample_audit_cycle_report ON sample_selection_audit_log USING btree (cycle_id, report_id);
CREATE INDEX ix_sample_selection_audit_log_action ON sample_selection_audit_log USING btree (action);
CREATE INDEX idx_sample_audit_action ON sample_selection_audit_log USING btree (action);
CREATE INDEX idx_sample_audit_performed_at ON sample_selection_audit_log USING btree (performed_at);
CREATE INDEX ix_sample_selection_phases_id ON sample_selection_phases USING btree (id);
CREATE INDEX idx_sample_sets_cycle_report ON sample_sets USING btree (cycle_id, report_id);
CREATE INDEX idx_sample_sets_status ON sample_sets USING btree (status);
CREATE INDEX idx_sample_sets_created_at ON sample_sets USING btree (created_at);
CREATE INDEX ix_sample_sets_set_name ON sample_sets USING btree (set_name);
CREATE INDEX ix_sample_sets_set_id ON sample_sets USING btree (set_id);
CREATE INDEX ix_sample_submission_items_id ON sample_submission_items USING btree (id);
CREATE UNIQUE INDEX ix_sample_submissions_submission_id ON sample_submissions USING btree (submission_id);
CREATE INDEX ix_sample_submissions_id ON sample_submissions USING btree (id);
CREATE INDEX ix_sample_submissions_cycle_report ON sample_submissions USING btree (cycle_id, report_id);
CREATE INDEX idx_upload_history_uploaded_at ON sample_upload_history USING btree (uploaded_at);
CREATE INDEX ix_sample_upload_history_upload_id ON sample_upload_history USING btree (upload_id);
CREATE INDEX idx_upload_history_method ON sample_upload_history USING btree (upload_method);
CREATE INDEX idx_validation_issues_severity ON sample_validation_issues USING btree (severity);
CREATE INDEX idx_validation_issues_resolved ON sample_validation_issues USING btree (is_resolved);
CREATE INDEX ix_sample_validation_issues_issue_id ON sample_validation_issues USING btree (issue_id);
CREATE INDEX ix_sample_validation_results_validation_id ON sample_validation_results USING btree (validation_id);
CREATE INDEX ix_samples_sample_id ON samples USING btree (sample_id);
CREATE INDEX ix_scoping_audit_log_audit_id ON scoping_audit_log USING btree (audit_id);
CREATE INDEX ix_scoping_submissions_submission_id ON scoping_submissions USING btree (submission_id);
CREATE INDEX ix_sla_configurations_sla_config_id ON sla_configurations USING btree (sla_config_id);
CREATE INDEX ix_sla_configurations_sla_type ON sla_configurations USING btree (sla_type);
CREATE INDEX ix_sla_escalation_rules_escalation_rule_id ON sla_escalation_rules USING btree (escalation_rule_id);
CREATE INDEX ix_sla_violation_tracking_violation_id ON sla_violation_tracking USING btree (violation_id);
CREATE INDEX ix_submission_documents_document_id ON submission_documents USING btree (document_id);
CREATE INDEX ix_submission_reminders_reminder_id ON submission_reminders USING btree (reminder_id);
CREATE INDEX ix_submission_validations_validation_id ON submission_validations USING btree (validation_id);
CREATE INDEX ix_test_cases_test_case_id ON test_cases USING btree (test_case_id);
CREATE INDEX ix_test_comparisons_comparison_id ON test_comparisons USING btree (comparison_id);
CREATE INDEX ix_test_cycles_cycle_name ON test_cycles USING btree (cycle_name);
CREATE INDEX ix_test_cycles_cycle_id ON test_cycles USING btree (cycle_id);
CREATE INDEX ix_test_cycles_workflow_id ON test_cycles USING btree (workflow_id);
CREATE INDEX ix_test_cycles_cycle_workflow ON test_cycles USING btree (cycle_id, workflow_id);
CREATE INDEX ix_test_execution_audit_logs_log_id ON test_execution_audit_logs USING btree (log_id);
CREATE INDEX ix_test_execution_phases_phase_id ON test_execution_phases USING btree (phase_id);
CREATE INDEX ix_test_executions_execution_id ON test_executions USING btree (execution_id);
CREATE INDEX ix_test_report_sections_section_id ON test_report_sections USING btree (section_id);
CREATE INDEX ix_test_result_reviews_review_id ON test_result_reviews USING btree (review_id);
CREATE INDEX ix_tester_scoping_decisions_decision_id ON tester_scoping_decisions USING btree (decision_id);
CREATE INDEX ix_testing_execution_audit_logs_log_id ON testing_execution_audit_logs USING btree (log_id);
CREATE INDEX ix_testing_execution_phases_phase_id ON testing_execution_phases USING btree (phase_id);
CREATE INDEX ix_testing_test_executions_execution_id ON testing_test_executions USING btree (execution_id);
CREATE INDEX ix_universal_assignment_history_history_id ON universal_assignment_history USING btree (history_id);
CREATE INDEX ix_universal_assignments_due_date ON universal_assignments USING btree (due_date);
CREATE INDEX ix_universal_assignments_status ON universal_assignments USING btree (status);
CREATE INDEX ix_universal_assignments_from_role ON universal_assignments USING btree (from_role);
CREATE INDEX ix_universal_assignments_assignment_id ON universal_assignments USING btree (assignment_id);
CREATE INDEX ix_universal_assignments_to_role ON universal_assignments USING btree (to_role);
CREATE INDEX ix_universal_assignments_assignment_type ON universal_assignments USING btree (assignment_type);
CREATE INDEX ix_universal_assignments_context_type ON universal_assignments USING btree (context_type);
CREATE INDEX ix_user_permissions_expires_at ON user_permissions USING btree (expires_at);
CREATE INDEX ix_user_permissions_user_id ON user_permissions USING btree (user_id);
CREATE INDEX ix_user_roles_user_id ON user_roles USING btree (user_id);
CREATE INDEX ix_user_roles_expires_at ON user_roles USING btree (expires_at);
CREATE INDEX ix_users_user_id ON users USING btree (user_id);
CREATE INDEX ix_users_role ON users USING btree (role);
CREATE UNIQUE INDEX ix_users_email ON users USING btree (email);
CREATE UNIQUE INDEX uq_workflow_activities_unique_activity ON workflow_activities USING btree (cycle_id, report_id, phase_name, activity_name);
CREATE INDEX ix_workflow_activities_cycle_report ON workflow_activities USING btree (cycle_id, report_id);
CREATE INDEX ix_workflow_activities_phase ON workflow_activities USING btree (cycle_id, report_id, phase_name);
CREATE INDEX ix_workflow_activities_status ON workflow_activities USING btree (status);
CREATE UNIQUE INDEX uq_activity_dependencies_unique ON workflow_activity_dependencies USING btree (phase_name, activity_name, depends_on_activity);
CREATE UNIQUE INDEX uq_activity_templates_unique ON workflow_activity_templates USING btree (phase_name, activity_name);
CREATE INDEX idx_workflow_alerts_unresolved ON workflow_alerts USING btree (resolved, created_at);
CREATE INDEX idx_workflow_alerts_severity ON workflow_alerts USING btree (severity, created_at);
CREATE INDEX idx_workflow_executions_cycle ON workflow_executions USING btree (cycle_id);
CREATE INDEX idx_workflow_executions_status ON workflow_executions USING btree (status);
CREATE INDEX idx_workflow_executions_started ON workflow_executions USING btree (started_at);
CREATE UNIQUE INDEX workflow_metrics_workflow_type_phase_name_activity_name_ste_key ON workflow_metrics USING btree (workflow_type, phase_name, activity_name, step_type, period_start, period_end);
CREATE INDEX idx_workflow_metrics_type_period ON workflow_metrics USING btree (workflow_type, period_start);
CREATE INDEX idx_workflow_metrics_phase_period ON workflow_metrics USING btree (phase_name, period_start);
CREATE INDEX ix_workflow_phases_phase_id ON workflow_phases USING btree (phase_id);
CREATE INDEX idx_workflow_steps_execution ON workflow_steps USING btree (execution_id);
CREATE INDEX idx_workflow_steps_status ON workflow_steps USING btree (status);
CREATE INDEX idx_workflow_steps_phase ON workflow_steps USING btree (phase_name);
CREATE INDEX idx_workflow_transitions_execution ON workflow_transitions USING btree (execution_id);
CREATE INDEX idx_workflow_transitions_timing ON workflow_transitions USING btree (started_at, completed_at);

-- Insert seed data

-- Seed data for lobs
INSERT INTO lobs (lob_id, lob_name, created_at, updated_at) VALUES (1, 'Consumer Banking', '2025-06-18T11:39:17.682028+00:00', '2025-06-18T11:39:17.682028+00:00');
INSERT INTO lobs (lob_id, lob_name, created_at, updated_at) VALUES (337, 'Retail Banking', '2025-06-01T21:50:26.886688+00:00', '2025-06-01T21:50:26.886688+00:00');
INSERT INTO lobs (lob_id, lob_name, created_at, updated_at) VALUES (338, 'GBM', '2025-06-07T17:50:45.684687+00:00', '2025-06-07T17:50:45.684687+00:00');
INSERT INTO lobs (lob_id, lob_name, created_at, updated_at) VALUES (344, 'Commercial Banking', '2025-06-15T19:44:46.956169+00:00', '2025-06-15T19:44:46.956169+00:00');
INSERT INTO lobs (lob_id, lob_name, created_at, updated_at) VALUES (345, 'Investment Banking', '2025-06-15T19:44:46.956169+00:00', '2025-06-15T19:44:46.956169+00:00');
INSERT INTO lobs (lob_id, lob_name, created_at, updated_at) VALUES (346, 'Risk Management', '2025-06-15T19:44:46.956169+00:00', '2025-06-15T19:44:46.956169+00:00');
INSERT INTO lobs (lob_id, lob_name, created_at, updated_at) VALUES (347, 'Compliance', '2025-06-15T19:44:46.956169+00:00', '2025-06-15T19:44:46.956169+00:00');
INSERT INTO lobs (lob_id, lob_name, created_at, updated_at) VALUES (348, 'Credit Cards', '2025-06-21T18:45:06.073215+00:00', '2025-06-21T18:45:06.073215+00:00');

-- Seed data for permissions
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (1, 'system', 'admin', 'admin access to System Administration', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (2, 'permissions', 'manage', 'manage access to Permissions Management', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (3, 'cycles', 'create', 'create access to Test Cycles', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (4, 'cycles', 'read', 'read access to Test Cycles', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (5, 'cycles', 'update', 'update access to Test Cycles', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (6, 'cycles', 'delete', 'delete access to Test Cycles', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (7, 'cycles', 'assign', 'assign access to Test Cycles', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (8, 'reports', 'create', 'create access to Reports', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (9, 'reports', 'read', 'read access to Reports', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (10, 'reports', 'update', 'update access to Reports', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (11, 'reports', 'delete', 'delete access to Reports', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (12, 'reports', 'assign', 'assign access to Reports', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (13, 'reports', 'approve', 'approve access to Reports', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (14, 'reports', 'override', 'override access to Reports', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (15, 'users', 'create', 'create access to Users', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (16, 'users', 'read', 'read access to Users', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (17, 'users', 'update', 'update access to Users', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (18, 'users', 'delete', 'delete access to Users', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (19, 'users', 'assign', 'assign access to Users', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (20, 'lobs', 'create', 'create access to Lines of Business', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (21, 'lobs', 'read', 'read access to Lines of Business', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (22, 'lobs', 'update', 'update access to Lines of Business', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (23, 'lobs', 'delete', 'delete access to Lines of Business', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (24, 'lobs', 'manage', 'manage access to Lines of Business', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (25, 'workflow', 'read', 'read access to Workflow', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (26, 'workflow', 'approve', 'approve access to Workflow', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (27, 'workflow', 'override', 'override access to Workflow', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (28, 'planning', 'execute', 'execute access to Planning Phase', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (29, 'planning', 'upload', 'upload access to Planning Phase', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (30, 'planning', 'create', 'create access to Planning Phase', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (31, 'planning', 'update', 'update access to Planning Phase', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (32, 'planning', 'delete', 'delete access to Planning Phase', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (33, 'planning', 'complete', 'complete access to Planning Phase', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (34, 'scoping', 'execute', 'execute access to Scoping Phase', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (35, 'scoping', 'generate', 'generate access to Scoping Phase', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (36, 'scoping', 'submit', 'submit access to Scoping Phase', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (37, 'scoping', 'approve', 'approve access to Scoping Phase', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (38, 'scoping', 'complete', 'complete access to Scoping Phase', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (39, 'data_owner', 'execute', 'execute access to Data Provider ID Phase', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (40, 'data_owner', 'identify', 'identify access to Data Provider ID Phase', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (41, 'data_owner', 'assign', 'assign access to Data Provider ID Phase', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (42, 'data_owner', 'upload', 'upload access to Data Provider ID Phase', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (43, 'data_owner', 'escalate', 'escalate access to Data Provider ID Phase', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (44, 'data_owner', 'complete', 'complete access to Data Provider ID Phase', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (45, 'sample_selection', 'execute', 'execute access to Sample Selection Phase', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (46, 'sample_selection', 'generate', 'generate access to Sample Selection Phase', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (47, 'sample_selection', 'upload', 'upload access to Sample Selection Phase', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (48, 'sample_selection', 'approve', 'approve access to Sample Selection Phase', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (49, 'sample_selection', 'complete', 'complete access to Sample Selection Phase', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (50, 'request_info', 'execute', 'execute access to Request Information Phase', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (51, 'request_info', 'upload', 'upload access to Request Information Phase', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (52, 'request_info', 'provide', 'provide access to Request Information Phase', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (53, 'request_info', 'complete', 'complete access to Request Information Phase', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (54, 'testing', 'execute', 'execute access to Testing Execution Phase', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (55, 'testing', 'submit', 'submit access to Testing Execution Phase', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (56, 'testing', 'review', 'review access to Testing Execution Phase', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (57, 'testing', 'approve', 'approve access to Testing Execution Phase', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (58, 'testing', 'complete', 'complete access to Testing Execution Phase', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (59, 'observations', 'create', 'create access to Observation Management Phase', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (60, 'observations', 'submit', 'submit access to Observation Management Phase', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (61, 'observations', 'review', 'review access to Observation Management Phase', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (62, 'observations', 'approve', 'approve access to Observation Management Phase', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (63, 'observations', 'override', 'override access to Observation Management Phase', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (64, 'observations', 'complete', 'complete access to Observation Management Phase', '2025-06-07T17:03:28.993444+00:00', '2025-06-07T17:03:28.993444+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (65, 'testing', 'read', 'View testing execution data and test cases', '2025-06-15T03:03:46.685855+00:00', '2025-06-15T03:03:46.685855+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (66, 'observations', 'read', 'View observations and observation reports', '2025-06-15T16:22:59.230804+00:00', '2025-06-15T16:22:59.230804+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (67, 'test-cycles', 'read', 'View test cycles', '2025-06-15T16:46:46.752147+00:00', '2025-06-15T16:46:46.752147+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (68, 'analytics', 'read', 'View analytics dashboard', '2025-06-15T16:46:46.752147+00:00', '2025-06-15T16:46:46.752147+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (70, 'data_owner', 'read', 'Read data owner information', '2025-06-15T18:29:47.639758+00:00', '2025-06-15T18:29:47.639758+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (71, 'sample_selection', 'read', 'Read sample selection data', '2025-06-16T00:49:46.355399+00:00', '2025-06-15T20:49:46.351102+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (72, 'request_info', 'read', 'Read request info data', '2025-06-16T01:41:47.849630+00:00', '2025-06-15T21:41:47.844914+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (73, 'metrics', 'read', 'Read metrics and analytics data', '2025-06-17T21:00:39.250842+00:00', '2025-06-17T21:00:39.250842+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (74, 'metrics', 'generate', 'Generate metrics reports', '2025-06-17T21:00:39.250842+00:00', '2025-06-17T21:00:39.250842+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (75, 'scoping', 'read', 'Read scoping data', '2025-06-17T21:02:52.856624+00:00', '2025-06-17T21:02:52.856624+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (76, 'data_profiling', 'assign', 'Create and assign tasks to report owners for data profiling', '2025-06-22T21:31:51.617522+00:00', '2025-06-22T21:31:51.617522+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (77, 'test_report', 'read', 'View test report content', '2025-06-25T02:13:41.917903+00:00', '2025-06-25T02:13:41.917903+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (78, 'test_report', 'write', 'Generate and configure test reports', '2025-06-25T02:13:41.917903+00:00', '2025-06-25T02:13:41.917903+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (79, 'test_report', 'approve', 'Approve test reports', '2025-06-25T02:13:41.917903+00:00', '2025-06-25T02:13:41.917903+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (80, 'observation_enhanced', 'read', 'View enhanced observation management', '2025-06-25T02:13:41.917903+00:00', '2025-06-25T02:13:41.917903+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (81, 'observation_enhanced', 'write', 'Create and manage enhanced observations', '2025-06-25T02:13:41.917903+00:00', '2025-06-25T02:13:41.917903+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (82, 'observation_enhanced', 'rate', 'Rate observation severity', '2025-06-25T02:13:41.917903+00:00', '2025-06-25T02:13:41.917903+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (83, 'observation_enhanced', 'approve', 'Approve or reject observations', '2025-06-25T02:13:41.917903+00:00', '2025-06-25T02:13:41.917903+00:00');
INSERT INTO permissions (permission_id, resource, action, description, created_at, updated_at) VALUES (84, 'observation_enhanced', 'finalize', 'Finalize observation groups', '2025-06-25T02:13:41.917903+00:00', '2025-06-25T02:13:41.917903+00:00');

-- Seed data for reports
INSERT INTO reports (report_id, report_name, regulation, description, frequency, report_owner_id, lob_id, is_active, created_at, updated_at) VALUES (156, 'FR Y-14M Schedule D.1', 'FR Y-14M Schedule D.1', 'FR Y-14M Schedule D.1', 'monthly', 4, 338, TRUE, '2025-06-07T17:51:22.018048+00:00', '2025-06-22T20:19:59.721577+00:00');
INSERT INTO reports (report_id, report_name, regulation, description, frequency, report_owner_id, lob_id, is_active, created_at, updated_at) VALUES (160, 'Demo Report for Data Provider Phase', 'Basel III', 'Demo report for testing Data Provider identification', 'Monthly', 4, 338, TRUE, '2025-06-11T20:52:27.999571+00:00', '2025-06-11T20:52:27.999571+00:00');
INSERT INTO reports (report_id, report_name, report_owner_id, lob_id, is_active, created_at, updated_at) VALUES (999, 'Test Report for Data Profiling', 1, 1, TRUE, '2025-06-22T19:02:18.953785+00:00', '2025-06-22T19:02:18.953785+00:00');
INSERT INTO reports (report_id, report_name, regulation, description, frequency, report_owner_id, lob_id, is_active, created_at, updated_at) VALUES (236092, 'E2E Debug Test Report 236092', 'Basel III', 'Test report for debug e2e testing', 'Quarterly', 1, 1, TRUE, '2025-06-18T13:03:37.816696+00:00', '2025-06-18T13:03:37.816696+00:00');
INSERT INTO reports (report_id, report_name, regulation, description, frequency, report_owner_id, lob_id, is_active, created_at, updated_at) VALUES (245822, 'E2E Complete Test Report 245822', 'Basel III', 'Test report for complete E2E testing', 'Quarterly', 1, 1, TRUE, '2025-06-18T12:16:04.529800+00:00', '2025-06-18T12:16:04.529800+00:00');
INSERT INTO reports (report_id, report_name, regulation, description, frequency, report_owner_id, lob_id, is_active, created_at, updated_at) VALUES (440728, 'E2E Test Report 440728', 'Basel III', 'Test report for E2E testing', 'Quarterly', 1, 1, TRUE, '2025-06-18T11:39:42.057066+00:00', '2025-06-18T11:39:42.057066+00:00');
INSERT INTO reports (report_id, report_name, regulation, description, frequency, report_owner_id, lob_id, is_active, created_at, updated_at) VALUES (506261, 'E2E Complete Test Report 506261', 'Basel III', 'Test report for complete E2E testing', 'Quarterly', 1, 1, TRUE, '2025-06-18T13:33:14.895130+00:00', '2025-06-18T13:33:14.895130+00:00');
INSERT INTO reports (report_id, report_name, regulation, description, frequency, report_owner_id, lob_id, is_active, created_at, updated_at) VALUES (507453, 'E2E Complete Test Report 507453', 'Basel III', 'Test report for complete E2E testing', 'Quarterly', 1, 1, TRUE, '2025-06-18T13:33:56.737248+00:00', '2025-06-18T13:33:56.737248+00:00');
INSERT INTO reports (report_id, report_name, regulation, description, frequency, report_owner_id, lob_id, is_active, created_at, updated_at) VALUES (570033, 'E2E Complete Test Report 570033', 'Basel III', 'Test report for complete E2E testing', 'Quarterly', 1, 1, TRUE, '2025-06-18T13:35:20.703635+00:00', '2025-06-18T13:35:20.703635+00:00');
INSERT INTO reports (report_id, report_name, regulation, description, frequency, report_owner_id, lob_id, is_active, created_at, updated_at) VALUES (573926, 'E2E Complete Test Report 573926', 'Basel III', 'Test report for complete E2E testing', 'Quarterly', 1, 1, TRUE, '2025-06-18T12:08:33.330681+00:00', '2025-06-18T12:08:33.330681+00:00');
INSERT INTO reports (report_id, report_name, regulation, description, frequency, report_owner_id, lob_id, is_active, created_at, updated_at) VALUES (591727, 'E2E Complete Test Report 591727', 'Basel III', 'Test report for complete E2E testing', 'Quarterly', 1, 1, TRUE, '2025-06-18T13:32:45.099630+00:00', '2025-06-18T13:32:45.099630+00:00');
INSERT INTO reports (report_id, report_name, regulation, description, frequency, report_owner_id, lob_id, is_active, created_at, updated_at) VALUES (592360, 'E2E Complete Test Report 592360', 'Basel III', 'Test report for complete E2E testing', 'Quarterly', 1, 1, TRUE, '2025-06-18T13:35:29.340089+00:00', '2025-06-18T13:35:29.340089+00:00');
INSERT INTO reports (report_id, report_name, regulation, description, frequency, report_owner_id, lob_id, is_active, created_at, updated_at) VALUES (596247, 'E2E Complete Test Report 596247', 'Basel III', 'Test report for complete E2E testing', 'Quarterly', 1, 1, TRUE, '2025-06-18T13:31:40.901550+00:00', '2025-06-18T13:31:40.901550+00:00');
INSERT INTO reports (report_id, report_name, regulation, description, frequency, report_owner_id, lob_id, is_active, created_at, updated_at) VALUES (608482, 'E2E Complete Test Report 608482', 'Basel III', 'Test report for complete E2E testing', 'Quarterly', 1, 1, TRUE, '2025-06-18T13:08:19.151780+00:00', '2025-06-18T13:08:19.151780+00:00');
INSERT INTO reports (report_id, report_name, regulation, description, frequency, report_owner_id, lob_id, is_active, created_at, updated_at) VALUES (654209, 'E2E Complete Test Report 654209', 'Basel III', 'Test report for complete E2E testing', 'Quarterly', 1, 1, TRUE, '2025-06-18T12:59:53.921509+00:00', '2025-06-18T12:59:53.921509+00:00');
INSERT INTO reports (report_id, report_name, regulation, description, frequency, report_owner_id, lob_id, is_active, created_at, updated_at) VALUES (668826, 'E2E Complete Test Report 668826', 'Basel III', 'Test report for complete E2E testing', 'Quarterly', 1, 1, TRUE, '2025-06-18T12:39:40.073926+00:00', '2025-06-18T12:39:40.073926+00:00');
INSERT INTO reports (report_id, report_name, regulation, description, frequency, report_owner_id, lob_id, is_active, created_at, updated_at) VALUES (812969, 'E2E Complete Test Report 812969', 'Basel III', 'Test report for complete E2E testing', 'Quarterly', 1, 1, TRUE, '2025-06-18T13:16:07.735103+00:00', '2025-06-18T13:16:07.735103+00:00');
INSERT INTO reports (report_id, report_name, regulation, description, frequency, report_owner_id, lob_id, is_active, created_at, updated_at) VALUES (900732, 'E2E Complete Test Report 900732', 'Basel III', 'Test report for complete E2E testing', 'Quarterly', 1, 1, TRUE, '2025-06-18T12:05:28.008138+00:00', '2025-06-18T12:05:28.008138+00:00');
INSERT INTO reports (report_id, report_name, regulation, description, frequency, report_owner_id, lob_id, is_active, created_at, updated_at) VALUES (919441, 'E2E Complete Test Report 919441', 'Basel III', 'Test report for complete E2E testing', 'Quarterly', 1, 1, TRUE, '2025-06-18T12:14:22.327960+00:00', '2025-06-18T12:14:22.327960+00:00');
INSERT INTO reports (report_id, report_name, regulation, description, frequency, report_owner_id, lob_id, is_active, created_at, updated_at) VALUES (927081, 'E2E Complete Test Report 927081', 'Basel III', 'Test report for complete E2E testing', 'Quarterly', 1, 1, TRUE, '2025-06-18T12:41:36.284353+00:00', '2025-06-18T12:41:36.284353+00:00');
INSERT INTO reports (report_id, report_name, regulation, description, frequency, report_owner_id, lob_id, is_active, created_at, updated_at) VALUES (986363, 'E2E Complete Test Report 986363', 'Basel III', 'Test report for complete E2E testing', 'Quarterly', 1, 1, TRUE, '2025-06-18T12:49:00.682871+00:00', '2025-06-18T12:49:00.682871+00:00');

-- Seed data for role_permissions
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 21, '2025-06-07T17:03:29.149042', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 23, '2025-06-07T17:03:29.149480', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 61, '2025-06-07T17:03:29.157990', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 62, '2025-06-07T17:03:29.158193', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 63, '2025-06-07T17:03:29.158395', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 64, '2025-06-07T17:03:29.158595', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 2, '2025-06-07T17:03:29.144543', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 3, '2025-06-07T17:03:29.144832', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 4, '2025-06-07T17:03:29.145134', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 5, '2025-06-07T17:03:29.145400', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 6, '2025-06-07T17:03:29.145698', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 7, '2025-06-07T17:03:29.145929', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 8, '2025-06-07T17:03:29.146153', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 9, '2025-06-07T17:03:29.146381', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 10, '2025-06-07T17:03:29.146611', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 11, '2025-06-07T17:03:29.146835', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 12, '2025-06-07T17:03:29.147055', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 13, '2025-06-07T17:03:29.147275', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 14, '2025-06-07T17:03:29.147493', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 15, '2025-06-07T17:03:29.147710', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 16, '2025-06-07T17:03:29.147948', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 17, '2025-06-07T17:03:29.148165', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 18, '2025-06-07T17:03:29.148383', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 19, '2025-06-07T17:03:29.148602', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 20, '2025-06-07T17:03:29.148824', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 22, '2025-06-07T17:03:29.149264', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_by, granted_at, created_at, updated_at) VALUES (1, 73, 1, '2025-06-24T22:40:55.020753', '2025-06-25T02:40:55.020753+00:00', '2025-06-25T02:40:55.020753+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 1, '2025-06-07T17:03:29.144075', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 70, '2025-06-15T18:24:11.895929', '2025-06-15T22:24:11.895929+00:00', '2025-06-15T22:24:11.895929+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 71, '2025-06-15T16:49:46.351102', '2025-06-16T00:49:46.359526+00:00', '2025-06-15T20:49:46.351102+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 67, '2025-06-15T12:46:46.752147', '2025-06-15T16:46:46.752147+00:00', '2025-06-15T16:46:46.752147+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 66, '2025-06-15T12:22:59.230804', '2025-06-15T16:22:59.230804+00:00', '2025-06-15T16:22:59.230804+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_by, granted_at, created_at, updated_at) VALUES (1, 65, 238, '2025-06-14T23:03:46.685855', '2025-06-15T03:03:46.685855+00:00', '2025-06-15T03:03:46.685855+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 24, '2025-06-07T17:03:29.149740', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 25, '2025-06-07T17:03:29.150052', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 26, '2025-06-07T17:03:29.150310', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 27, '2025-06-07T17:03:29.150548', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 28, '2025-06-07T17:03:29.150772', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 29, '2025-06-07T17:03:29.150993', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 30, '2025-06-07T17:03:29.151238', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 31, '2025-06-07T17:03:29.151573', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 32, '2025-06-07T17:03:29.151767', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 33, '2025-06-07T17:03:29.151952', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 34, '2025-06-07T17:03:29.152132', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 35, '2025-06-07T17:03:29.152305', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 36, '2025-06-07T17:03:29.152535', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 37, '2025-06-07T17:03:29.152732', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 38, '2025-06-07T17:03:29.152921', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 39, '2025-06-07T17:03:29.153127', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 40, '2025-06-07T17:03:29.153364', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 41, '2025-06-07T17:03:29.153587', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 42, '2025-06-07T17:03:29.153782', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 43, '2025-06-07T17:03:29.153970', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 44, '2025-06-07T17:03:29.154326', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 45, '2025-06-07T17:03:29.154582', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 46, '2025-06-07T17:03:29.154816', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 47, '2025-06-07T17:03:29.155048', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 48, '2025-06-07T17:03:29.155267', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 49, '2025-06-07T17:03:29.155482', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 50, '2025-06-07T17:03:29.155702', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 51, '2025-06-07T17:03:29.155923', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 52, '2025-06-07T17:03:29.156131', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 53, '2025-06-07T17:03:29.156338', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 54, '2025-06-07T17:03:29.156554', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 55, '2025-06-07T17:03:29.156769', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 56, '2025-06-07T17:03:29.156978', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 57, '2025-06-07T17:03:29.157180', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 58, '2025-06-07T17:03:29.157382', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 59, '2025-06-07T17:03:29.157591', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (1, 60, '2025-06-07T17:03:29.157791', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (2, 79, '2025-06-24T23:16:43.275202', '2025-06-25T03:16:43.275202+00:00', '2025-06-25T03:16:43.275202+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (2, 5, '2025-06-07T17:03:29.160311', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_by, granted_at, created_at, updated_at) VALUES (2, 78, 1, '2025-06-24T22:14:55.744177', '2025-06-25T02:14:55.744177+00:00', '2025-06-25T02:14:55.744177+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_by, granted_at, created_at, updated_at) VALUES (2, 77, 1, '2025-06-24T22:14:55.744177', '2025-06-25T02:14:55.744177+00:00', '2025-06-25T02:14:55.744177+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (2, 6, '2025-06-07T17:03:29.160692', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (2, 76, '2025-06-22T17:31:57.385299', '2025-06-22T21:31:57.385299+00:00', '2025-06-22T21:31:57.385299+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (2, 73, '2025-06-17T17:00:39.286703', '2025-06-17T21:00:39.286703+00:00', '2025-06-17T21:00:39.286703+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (2, 39, '2025-06-15T18:24:11.895929', '2025-06-15T22:24:11.895929+00:00', '2025-06-15T22:24:11.895929+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (2, 70, '2025-06-15T18:24:11.895929', '2025-06-15T22:24:11.895929+00:00', '2025-06-15T22:24:11.895929+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (2, 7, '2025-06-07T17:03:29.161101', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (2, 71, '2025-06-15T16:49:46.351102', '2025-06-16T00:49:46.359534+00:00', '2025-06-15T20:49:46.351102+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (2, 21, '2025-06-15T16:49:46.351102', '2025-06-16T00:49:46.359532+00:00', '2025-06-15T20:49:46.351102+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (2, 8, '2025-06-07T17:03:29.161498', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (2, 68, '2025-06-15T12:46:46.752147', '2025-06-15T16:46:46.752147+00:00', '2025-06-15T16:46:46.752147+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (2, 67, '2025-06-15T12:46:46.752147', '2025-06-15T16:46:46.752147+00:00', '2025-06-15T16:46:46.752147+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (2, 9, '2025-06-07T17:03:29.161862', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (2, 66, '2025-06-15T12:22:59.230804', '2025-06-15T16:22:59.230804+00:00', '2025-06-15T16:22:59.230804+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (2, 12, '2025-06-07T17:03:29.162216', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (2, 25, '2025-06-07T17:03:29.163296', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_by, granted_at, created_at, updated_at) VALUES (2, 65, 238, '2025-06-14T23:03:46.685855', '2025-06-15T03:03:46.685855+00:00', '2025-06-15T03:03:46.685855+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (2, 16, '2025-06-07T14:18:22.256929', '2025-06-07T18:18:22.256929+00:00', '2025-06-07T18:18:22.256929+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (2, 26, '2025-06-07T17:03:29.163675', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (2, 3, '2025-06-07T17:03:29.159490', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (2, 4, '2025-06-07T17:03:29.159958', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (3, 76, '2025-06-22T17:58:24.772414', '2025-06-22T21:58:24.772414+00:00', '2025-06-22T21:58:24.772414+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (3, 4, '2025-06-07T17:03:29.165090', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (3, 9, '2025-06-07T17:03:29.165499', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (3, 28, '2025-06-07T17:03:29.165973', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (3, 29, '2025-06-07T17:03:29.166309', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (3, 30, '2025-06-07T17:03:29.166680', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (3, 31, '2025-06-07T17:03:29.167055', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (3, 32, '2025-06-07T17:03:29.167425', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (3, 33, '2025-06-07T17:03:29.167826', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (3, 34, '2025-06-07T17:03:29.168213', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (3, 35, '2025-06-07T17:03:29.168583', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (3, 36, '2025-06-07T17:03:29.168920', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (3, 38, '2025-06-07T17:03:29.169300', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (3, 45, '2025-06-07T17:03:29.169833', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (3, 46, '2025-06-07T17:03:29.170255', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (3, 47, '2025-06-07T17:03:29.170652', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (3, 49, '2025-06-07T17:03:29.171019', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (3, 54, '2025-06-07T17:03:29.171371', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (3, 55, '2025-06-07T17:03:29.171718', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (3, 58, '2025-06-07T17:03:29.172069', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (3, 59, '2025-06-07T17:03:29.172406', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (3, 60, '2025-06-07T17:03:29.172747', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (3, 25, '2025-06-07T17:03:29.173168', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_by, granted_at, created_at, updated_at) VALUES (3, 65, 238, '2025-06-14T23:03:46.685855', '2025-06-15T03:03:46.685855+00:00', '2025-06-15T03:03:46.685855+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (3, 66, '2025-06-15T12:22:59.230804', '2025-06-15T16:22:59.230804+00:00', '2025-06-15T16:22:59.230804+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (3, 67, '2025-06-15T12:46:46.752147', '2025-06-15T16:46:46.752147+00:00', '2025-06-15T16:46:46.752147+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (3, 71, '2025-06-15T17:27:31.457380', '2025-06-16T01:27:31.461497+00:00', '2025-06-15T21:27:31.457380+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (3, 50, '2025-06-15T17:40:30.504454', '2025-06-16T01:40:30.510248+00:00', '2025-06-15T21:40:30.504454+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (3, 51, '2025-06-15T17:40:30.504454', '2025-06-16T01:40:30.510768+00:00', '2025-06-15T21:40:30.504454+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (3, 52, '2025-06-15T17:40:30.504454', '2025-06-16T01:40:30.511171+00:00', '2025-06-15T21:40:30.504454+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (3, 53, '2025-06-15T17:40:30.504454', '2025-06-16T01:40:30.511548+00:00', '2025-06-15T21:40:30.504454+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (3, 72, '2025-06-15T17:41:47.866500', '2025-06-16T01:41:47.867665+00:00', '2025-06-15T21:41:47.866500+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (3, 56, '2025-06-15T17:42:43.303822', '2025-06-16T01:42:43.310834+00:00', '2025-06-15T21:42:43.303822+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (3, 57, '2025-06-15T17:42:43.303822', '2025-06-16T01:42:43.311260+00:00', '2025-06-15T21:42:43.303822+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (3, 70, '2025-06-16T15:00:56.578834', '2025-06-16T19:00:56.578834+00:00', '2025-06-16T19:00:56.578834+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (3, 21, '2025-06-18T12:49:00.138817', '2025-06-18T16:49:00.138817+00:00', '2025-06-18T16:49:00.138817+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (3, 39, '2025-06-21T14:53:44.541074', '2025-06-21T18:53:44.541074+00:00', '2025-06-21T18:53:44.541074+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (3, 42, '2025-06-21T14:53:44.541074', '2025-06-21T18:53:44.541074+00:00', '2025-06-21T18:53:44.541074+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_by, granted_at, created_at, updated_at) VALUES (3, 44, 1, '2025-06-24T10:41:10.787965', '2025-06-24T14:41:10.787965+00:00', '2025-06-24T14:41:10.787965+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (3, 77, '2025-06-24T22:13:42.064765', '2025-06-25T02:13:42.064765+00:00', '2025-06-25T02:13:42.064765+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (3, 80, '2025-06-24T22:13:42.064765', '2025-06-25T02:13:42.064765+00:00', '2025-06-25T02:13:42.064765+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (3, 81, '2025-06-24T22:13:42.064765', '2025-06-25T02:13:42.064765+00:00', '2025-06-25T02:13:42.064765+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_by, granted_at, created_at, updated_at) VALUES (3, 78, 1, '2025-06-24T22:29:33.708612', '2025-06-25T02:29:33.708612+00:00', '2025-06-25T02:29:33.708612+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_by, granted_at, created_at, updated_at) VALUES (3, 73, 1, '2025-06-24T22:40:55.020753', '2025-06-25T02:40:55.020753+00:00', '2025-06-25T02:40:55.020753+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (3, 79, '2025-06-24T23:16:43.275202', '2025-06-25T03:16:43.275202+00:00', '2025-06-25T03:16:43.275202+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (4, 9, '2025-06-07T17:03:29.174093', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (4, 25, '2025-06-07T17:03:29.176973', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (4, 62, '2025-06-07T17:03:29.176615', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (4, 67, '2025-06-15T12:46:46.752147', '2025-06-15T16:46:46.752147+00:00', '2025-06-15T16:46:46.752147+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (4, 61, '2025-06-07T17:03:29.176290', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (4, 48, '2025-06-07T17:03:29.175272', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (4, 73, '2025-06-17T17:00:39.271102', '2025-06-17T21:00:39.271102+00:00', '2025-06-17T21:00:39.271102+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (4, 57, '2025-06-07T17:03:29.175965', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_by, granted_at, created_at, updated_at) VALUES (4, 65, 238, '2025-06-14T23:03:46.685855', '2025-06-15T03:03:46.685855+00:00', '2025-06-15T03:03:46.685855+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (4, 71, '2025-06-17T17:02:52.864453', '2025-06-17T21:02:52.864453+00:00', '2025-06-17T21:02:52.864453+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (4, 75, '2025-06-17T17:02:52.864453', '2025-06-17T21:02:52.864453+00:00', '2025-06-17T21:02:52.864453+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (4, 56, '2025-06-07T17:03:29.175629', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (4, 13, '2025-06-07T17:03:29.174461', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (4, 37, '2025-06-07T17:03:29.174885', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (4, 77, '2025-06-24T22:13:42.064765', '2025-06-25T02:13:42.064765+00:00', '2025-06-25T02:13:42.064765+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (4, 21, '2025-06-15T16:49:46.351102', '2025-06-16T00:49:46.359548+00:00', '2025-06-15T20:49:46.351102+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (4, 82, '2025-06-24T22:13:42.064765', '2025-06-25T02:13:42.064765+00:00', '2025-06-25T02:13:42.064765+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (4, 83, '2025-06-24T22:13:42.064765', '2025-06-25T02:13:42.064765+00:00', '2025-06-25T02:13:42.064765+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (4, 80, '2025-06-24T22:13:42.064765', '2025-06-25T02:13:42.064765+00:00', '2025-06-25T02:13:42.064765+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (4, 66, '2025-06-15T12:22:59.230804', '2025-06-15T16:22:59.230804+00:00', '2025-06-15T16:22:59.230804+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (4, 26, '2025-06-07T17:03:29.177356', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (4, 79, '2025-06-24T22:13:42.064765', '2025-06-25T02:13:42.064765+00:00', '2025-06-25T02:13:42.064765+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (4, 4, '2025-06-07T17:03:29.173679', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (5, 70, '2025-06-15T18:24:11.895929', '2025-06-15T22:24:11.895929+00:00', '2025-06-15T22:24:11.895929+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (5, 67, '2025-06-15T12:46:46.752147', '2025-06-15T16:46:46.752147+00:00', '2025-06-15T16:46:46.752147+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (5, 25, '2025-06-07T17:03:29.178630', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (5, 68, '2025-06-15T12:46:46.752147', '2025-06-15T16:46:46.752147+00:00', '2025-06-15T16:46:46.752147+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (5, 14, '2025-06-07T17:03:29.178287', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (5, 9, '2025-06-07T17:03:29.177936', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (5, 21, '2025-06-15T16:49:46.351102', '2025-06-16T00:49:46.359539+00:00', '2025-06-15T20:49:46.351102+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (5, 71, '2025-06-15T16:49:46.351102', '2025-06-16T00:49:46.359541+00:00', '2025-06-15T20:49:46.351102+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (5, 65, '2025-06-15T16:49:46.351102', '2025-06-16T00:49:46.359543+00:00', '2025-06-15T20:49:46.351102+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (5, 77, '2025-06-24T22:13:42.064765', '2025-06-25T02:13:42.064765+00:00', '2025-06-25T02:13:42.064765+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (5, 79, '2025-06-24T22:13:42.064765', '2025-06-25T02:13:42.064765+00:00', '2025-06-25T02:13:42.064765+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (5, 80, '2025-06-24T22:13:42.064765', '2025-06-25T02:13:42.064765+00:00', '2025-06-25T02:13:42.064765+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (5, 83, '2025-06-24T22:13:42.064765', '2025-06-25T02:13:42.064765+00:00', '2025-06-25T02:13:42.064765+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (5, 73, '2025-06-17T17:00:39.286703', '2025-06-17T21:00:39.286703+00:00', '2025-06-17T21:00:39.286703+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (5, 4, '2025-06-07T17:03:29.179744', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (5, 66, '2025-06-15T12:22:59.230804', '2025-06-15T16:22:59.230804+00:00', '2025-06-15T16:22:59.230804+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (5, 63, '2025-06-07T17:03:29.179332', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (5, 27, '2025-06-07T17:03:29.178995', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (6, 25, '2025-06-07T17:03:29.182096', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (6, 52, '2025-06-07T17:03:29.181420', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_by, granted_at, created_at, updated_at) VALUES (6, 77, 1, '2025-06-24T22:14:55.744177', '2025-06-25T02:14:55.744177+00:00', '2025-06-25T02:14:55.744177+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (6, 42, '2025-06-07T17:03:29.181055', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (6, 39, '2025-06-07T17:03:29.180699', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (6, 67, '2025-06-15T12:46:46.752147', '2025-06-15T16:46:46.752147+00:00', '2025-06-15T16:46:46.752147+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (6, 4, '2025-06-15T12:50:27.900604', '2025-06-15T16:50:27.900604+00:00', '2025-06-15T16:50:27.900604+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_by, granted_at, created_at, updated_at) VALUES (6, 73, 1, '2025-06-24T22:40:55.020753', '2025-06-25T02:40:55.020753+00:00', '2025-06-25T02:40:55.020753+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (6, 72, '2025-06-17T17:02:52.864453', '2025-06-17T21:02:52.864453+00:00', '2025-06-17T21:02:52.864453+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (6, 80, '2025-06-24T22:13:42.064765', '2025-06-25T02:13:42.064765+00:00', '2025-06-25T02:13:42.064765+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (6, 70, '2025-06-17T17:02:52.864453', '2025-06-17T21:02:52.864453+00:00', '2025-06-17T21:02:52.864453+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (6, 51, '2025-06-07T17:03:29.181747', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (7, 70, '2025-06-15T14:29:59.570967', '2025-06-15T18:29:59.570967+00:00', '2025-06-15T18:29:59.570967+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (7, 4, '2025-06-15T12:50:27.900604', '2025-06-15T16:50:27.900604+00:00', '2025-06-15T16:50:27.900604+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (7, 67, '2025-06-15T12:46:46.752147', '2025-06-15T16:46:46.752147+00:00', '2025-06-15T16:46:46.752147+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (7, 73, '2025-06-17T17:02:52.864453', '2025-06-17T21:02:52.864453+00:00', '2025-06-17T21:02:52.864453+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (7, 71, '2025-06-17T17:02:52.864453', '2025-06-17T21:02:52.864453+00:00', '2025-06-17T21:02:52.864453+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (7, 83, '2025-06-24T22:13:42.064765', '2025-06-25T02:13:42.064765+00:00', '2025-06-25T02:13:42.064765+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (7, 80, '2025-06-24T22:13:42.064765', '2025-06-25T02:13:42.064765+00:00', '2025-06-25T02:13:42.064765+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (7, 77, '2025-06-24T22:13:42.064765', '2025-06-25T02:13:42.064765+00:00', '2025-06-25T02:13:42.064765+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (7, 21, '2025-06-07T17:03:29.182597', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (7, 24, '2025-06-07T17:03:29.182934', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (7, 40, '2025-06-07T17:03:29.183413', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (7, 41, '2025-06-07T17:03:29.183966', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (7, 43, '2025-06-07T17:03:29.184387', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (7, 16, '2025-06-07T17:03:29.184804', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_at, created_at, updated_at) VALUES (7, 25, '2025-06-07T17:03:29.185164', '2025-06-07T17:03:29.139682+00:00', '2025-06-07T17:03:29.139682+00:00');
INSERT INTO role_permissions (role_id, permission_id, granted_by, granted_at, created_at, updated_at) VALUES (7, 1, 1, '2025-06-07T13:29:37.289076', '2025-06-07T17:29:37.289076+00:00', '2025-06-07T17:29:37.289076+00:00');

-- Seed data for roles
INSERT INTO roles (role_id, role_name, description, is_system, is_active, created_at, updated_at) VALUES (1, 'Admin', 'System Administrator - Full Access', TRUE, TRUE, '2025-06-07T17:03:29.121592+00:00', '2025-06-07T17:03:29.121592+00:00');
INSERT INTO roles (role_id, role_name, description, is_system, is_active, created_at, updated_at) VALUES (2, 'Test Executive', 'Test Manager - Manage testing cycles and assignments', TRUE, TRUE, '2025-06-07T17:03:29.121592+00:00', '2025-06-07T17:03:29.121592+00:00');
INSERT INTO roles (role_id, role_name, description, is_system, is_active, created_at, updated_at) VALUES (3, 'Tester', 'Tester - Execute testing workflows', TRUE, TRUE, '2025-06-07T17:03:29.121592+00:00', '2025-06-07T17:03:29.121592+00:00');
INSERT INTO roles (role_id, role_name, description, is_system, is_active, created_at, updated_at) VALUES (4, 'Report Owner', 'Report Owner - Review and approve reports', TRUE, TRUE, '2025-06-07T17:03:29.121592+00:00', '2025-06-07T17:03:29.121592+00:00');
INSERT INTO roles (role_id, role_name, description, is_system, is_active, created_at, updated_at) VALUES (5, 'Report Owner Executive', 'Report Owner Executive - Executive oversight', TRUE, TRUE, '2025-06-07T17:03:29.121592+00:00', '2025-06-07T17:03:29.121592+00:00');
INSERT INTO roles (role_id, role_name, description, is_system, is_active, created_at, updated_at) VALUES (6, 'Data Owner', 'Data Provider - Provide data for testing', TRUE, TRUE, '2025-06-07T17:03:29.121592+00:00', '2025-06-07T17:03:29.121592+00:00');
INSERT INTO roles (role_id, role_name, description, is_system, is_active, created_at, updated_at) VALUES (7, 'Data Executive', 'Chief Data Officer - Manage LOBs and data providers', TRUE, TRUE, '2025-06-07T17:03:29.121592+00:00', '2025-06-07T17:03:29.121592+00:00');

-- Seed data for users
INSERT INTO users (user_id, first_name, last_name, email, role, lob_id, is_active, hashed_password, created_at, updated_at) VALUES (1, 'Admin', 'User', 'admin@synapsedt.com', 'Admin', 337, TRUE, '$2b$12$Y9VaWwGF6MEV1UXQhzgbEetD3.i7q93Ndq78JiqFcQjk3fgNkRvo6', '2025-06-01T21:50:40.262461+00:00', '2025-06-17T19:55:54.150378+00:00');
INSERT INTO users (user_id, first_name, last_name, email, role, lob_id, is_active, hashed_password, created_at, updated_at) VALUES (2, 'Test', 'Manager', 'test.manager@example.com', 'Test Executive', 337, TRUE, '$2b$12$H5pY9NJJemeIpzBK.HAJ7.iu61HP7uE5Bso6b0vYEK9Bh3/BfugL6', '2025-06-01T21:50:47.758548+00:00', '2025-06-07T16:43:32.273177+00:00');
INSERT INTO users (user_id, first_name, last_name, email, role, lob_id, is_active, hashed_password, created_at, updated_at) VALUES (3, 'Jane', 'Doe', 'tester@example.com', 'Tester', 338, TRUE, '$2b$12$H5pY9NJJemeIpzBK.HAJ7.iu61HP7uE5Bso6b0vYEK9Bh3/BfugL6', '2025-06-01T21:50:53.868693+00:00', '2025-06-18T16:49:00.156586+00:00');
INSERT INTO users (user_id, first_name, last_name, email, role, lob_id, is_active, hashed_password, created_at, updated_at) VALUES (4, 'Mike', 'Johnson', 'report.owner@example.com', 'Report Owner', 337, TRUE, '$2b$12$H5pY9NJJemeIpzBK.HAJ7.iu61HP7uE5Bso6b0vYEK9Bh3/BfugL6', '2025-06-01T21:51:02.367197+00:00', '2025-06-07T16:43:32.273177+00:00');
INSERT INTO users (user_id, first_name, last_name, email, role, lob_id, is_active, hashed_password, created_at, updated_at) VALUES (5, 'David', 'Brown', 'cdo@example.com', 'Data Executive', 338, TRUE, '$2b$12$H5pY9NJJemeIpzBK.HAJ7.iu61HP7uE5Bso6b0vYEK9Bh3/BfugL6', '2025-06-01T21:51:02.546678+00:00', '2025-06-07T16:43:32.273177+00:00');
INSERT INTO users (user_id, first_name, last_name, email, role, lob_id, is_active, hashed_password, created_at, updated_at) VALUES (6, 'Lisa', 'Chen', 'data.provider@example.com', 'Data Owner', 338, TRUE, '$2b$12$H5pY9NJJemeIpzBK.HAJ7.iu61HP7uE5Bso6b0vYEK9Bh3/BfugL6', '2025-06-01T21:51:02.728714+00:00', '2025-06-07T16:43:32.273177+00:00');
INSERT INTO users (user_id, first_name, last_name, email, phone, role, is_active, hashed_password, created_at, updated_at) VALUES (238, 'System', 'Admin', 'admin@example.com', '1234567899', 'Admin', TRUE, '$2b$12$1v7F0S0VUx9XsaONmgcsxuyo7MTVtv7Q9nSWF3Cyzuy5864StdI6m', '2025-06-13T17:51:10.059128+00:00', '2025-06-15T01:59:51.037309+00:00');
INSERT INTO users (user_id, first_name, last_name, email, role, lob_id, is_active, hashed_password, created_at, updated_at) VALUES (244, 'Chief', 'DataOfficer', 'cdo@synapse.com', 'Data Executive', 337, TRUE, '$2b$12$EtiFUzkRVaKSySIBbVa1Qu1XzQfI/WCIHjxALZNpbIk8nL2I4w.am', '2025-06-15T16:04:56.724212+00:00', '2025-06-17T21:36:04.015082+00:00');
INSERT INTO users (user_id, first_name, last_name, email, role, lob_id, is_active, hashed_password, created_at, updated_at) VALUES (246, 'Test', 'Tester', 'test_tester@synapse.com', 'Tester', 337, TRUE, '$2b$12$onAbvKmzfICaOJC2sossUeK39wkQ3uSIvXBF8LLf7ryhhSj0kKjDi', '2025-06-15T16:06:02.720978+00:00', '2025-06-18T16:49:00.156586+00:00');
INSERT INTO users (user_id, first_name, last_name, email, role, lob_id, is_active, hashed_password, created_at, updated_at) VALUES (254, 'Test', 'Manager', 'testmgr@synapse.com', 'Test Executive', 337, TRUE, '$2b$12$EtiFUzkRVaKSySIBbVa1Qu1XzQfI/WCIHjxALZNpbIk8nL2I4w.am', '2025-06-15T16:48:18.999056+00:00', '2025-06-15T16:48:18.999056+00:00');
INSERT INTO users (user_id, first_name, last_name, email, role, lob_id, is_active, hashed_password, created_at, updated_at) VALUES (255, 'Test', 'Tester', 'tester@synapse.com', 'Tester', 337, TRUE, '$2b$12$EtiFUzkRVaKSySIBbVa1Qu1XzQfI/WCIHjxALZNpbIk8nL2I4w.am', '2025-06-15T16:48:18.999056+00:00', '2025-06-18T16:49:00.156586+00:00');
INSERT INTO users (user_id, first_name, last_name, email, role, lob_id, is_active, hashed_password, created_at, updated_at) VALUES (256, 'Report', 'Owner', 'owner@synapse.com', 'Report Owner', 337, TRUE, '$2b$12$EtiFUzkRVaKSySIBbVa1Qu1XzQfI/WCIHjxALZNpbIk8nL2I4w.am', '2025-06-15T16:48:18.999056+00:00', '2025-06-15T16:48:18.999056+00:00');
INSERT INTO users (user_id, first_name, last_name, email, role, lob_id, is_active, hashed_password, created_at, updated_at) VALUES (257, 'Executive', 'Owner', 'exec@synapse.com', 'Report Owner Executive', 337, TRUE, '$2b$12$EtiFUzkRVaKSySIBbVa1Qu1XzQfI/WCIHjxALZNpbIk8nL2I4w.am', '2025-06-15T16:48:18.999056+00:00', '2025-06-15T16:48:18.999056+00:00');
INSERT INTO users (user_id, first_name, last_name, email, role, lob_id, is_active, hashed_password, created_at, updated_at) VALUES (258, 'Data', 'Provider', 'provider@synapse.com', 'Data Owner', 337, TRUE, '$2b$12$EtiFUzkRVaKSySIBbVa1Qu1XzQfI/WCIHjxALZNpbIk8nL2I4w.am', '2025-06-15T16:48:18.999056+00:00', '2025-06-15T16:48:18.999056+00:00');
INSERT INTO users (user_id, first_name, last_name, email, role, lob_id, is_active, hashed_password, created_at, updated_at) VALUES (279, 'Test', 'Executive', 'test_executive@example.com', 'Test Executive', 337, TRUE, '$2b$12$2tufWYFAjxA3fTvcIzLblefzRwIh3j4RmvAoHSXir545fq542c0ay', '2025-06-16T02:17:48.076770+00:00', '2025-06-16T02:17:48.076770+00:00');
INSERT INTO users (user_id, first_name, last_name, email, role, lob_id, is_active, hashed_password, created_at, updated_at) VALUES (280, 'Report', 'Owner', 'report_owner@example.com', 'Report Owner', 337, TRUE, '$2b$12$c3zkD22YTw9zlaCuSLL3XOdxtpc3g3wFR3L1Wc08GY8meg8n0pAMa', '2025-06-16T02:17:48.076770+00:00', '2025-06-16T02:17:48.076770+00:00');
INSERT INTO users (user_id, first_name, last_name, email, role, lob_id, is_active, hashed_password, created_at, updated_at) VALUES (281, 'Report Owner', 'Executive', 'report_owner_executive@example.com', 'Report Owner Executive', 337, TRUE, '$2b$12$2JJ7A.08mxp.m2L.Dn38beHlOR4caP5wnFHSQzlM8EMw2kGERrjFi', '2025-06-16T02:17:48.076770+00:00', '2025-06-16T02:17:48.076770+00:00');
INSERT INTO users (user_id, first_name, last_name, email, role, lob_id, is_active, hashed_password, created_at, updated_at) VALUES (282, 'Data', 'Owner', 'data_owner@example.com', 'Data Owner', 337, TRUE, '$2b$12$b54FbBxqK2CGim6XwgXYaOwTRx5r60gHy71ieDdikV5gSM3vp.APy', '2025-06-16T02:17:48.076770+00:00', '2025-06-16T02:17:48.076770+00:00');
INSERT INTO users (user_id, first_name, last_name, email, role, lob_id, is_active, hashed_password, created_at, updated_at) VALUES (283, 'Data', 'Executive', 'data_executive@example.com', 'Data Executive', 337, TRUE, '$2b$12$WokYrrhTgHw61eL7upb4e.yN2/ak67YCfTfY5nLDMd5xRHV7.M1iu', '2025-06-16T02:17:48.076770+00:00', '2025-06-16T02:17:48.076770+00:00');
INSERT INTO users (user_id, first_name, last_name, email, role, is_active, hashed_password, created_at, updated_at) VALUES (345, 'Jane', 'Doe', 'jane.doe@example.com', 'Tester', TRUE, '$2b$12$X96ydl7JxZk6VoXEJYlWZOjsBh9kWrzMdbub.YRVllFCshhA/qzw6', '2025-06-21T17:51:18.186299+00:00', '2025-06-21T17:51:18.186299+00:00');

-- Seed data for workflow_activities
INSERT INTO workflow_activities (activity_id, cycle_id, report_id, phase_name, activity_name, activity_type, activity_order, status, can_start, can_complete, is_manual, is_optional, started_at, started_by, completed_at, completed_by, created_at, updated_at) VALUES (1, 21, 156, 'Planning', 'Start Planning Phase', 'START', 1, 'COMPLETED', FALSE, FALSE, TRUE, FALSE, '2025-06-22T20:27:31.589765+00:00', 3, '2025-06-23T00:37:27.688010+00:00', 3, '2025-06-25T18:07:54.960735+00:00', '2025-06-25T18:07:54.960735+00:00');
INSERT INTO workflow_activities (activity_id, cycle_id, report_id, phase_name, activity_name, activity_type, activity_order, status, can_start, can_complete, is_manual, is_optional, started_at, started_by, completed_at, completed_by, created_at, updated_at) VALUES (2, 21, 156, 'Planning', 'Generate Attributes', 'TASK', 2, 'COMPLETED', FALSE, FALSE, TRUE, FALSE, '2025-06-22T20:27:31.589765+00:00', 3, '2025-06-23T00:37:27.688010+00:00', 3, '2025-06-25T18:07:54.960735+00:00', '2025-06-25T18:07:54.960735+00:00');
INSERT INTO workflow_activities (activity_id, cycle_id, report_id, phase_name, activity_name, activity_type, activity_order, status, can_start, can_complete, is_manual, is_optional, started_at, started_by, completed_at, completed_by, created_at, updated_at) VALUES (3, 21, 156, 'Planning', 'Review Attributes', 'TASK', 3, 'COMPLETED', FALSE, FALSE, TRUE, FALSE, '2025-06-22T20:27:31.589765+00:00', 3, '2025-06-23T00:37:27.688010+00:00', 3, '2025-06-25T18:07:54.960735+00:00', '2025-06-25T18:07:54.960735+00:00');
INSERT INTO workflow_activities (activity_id, cycle_id, report_id, phase_name, activity_name, activity_type, activity_order, status, can_start, can_complete, is_manual, is_optional, started_at, started_by, completed_at, completed_by, created_at, updated_at) VALUES (4, 21, 156, 'Planning', 'Tester Review', 'REVIEW', 4, 'COMPLETED', FALSE, FALSE, TRUE, FALSE, '2025-06-22T20:27:31.589765+00:00', 3, '2025-06-23T00:37:27.688010+00:00', 3, '2025-06-25T18:07:54.960735+00:00', '2025-06-25T18:07:54.960735+00:00');
INSERT INTO workflow_activities (activity_id, cycle_id, report_id, phase_name, activity_name, activity_type, activity_order, status, can_start, can_complete, is_manual, is_optional, started_at, started_by, completed_at, completed_by, created_at, updated_at) VALUES (5, 21, 156, 'Planning', 'Report Owner Approval', 'APPROVAL', 5, 'COMPLETED', FALSE, FALSE, TRUE, FALSE, '2025-06-22T20:27:31.589765+00:00', 3, '2025-06-23T00:37:27.688010+00:00', 3, '2025-06-25T18:07:54.960735+00:00', '2025-06-25T18:07:54.960735+00:00');
INSERT INTO workflow_activities (activity_id, cycle_id, report_id, phase_name, activity_name, activity_type, activity_order, status, can_start, can_complete, is_manual, is_optional, started_at, started_by, completed_at, completed_by, created_at, updated_at) VALUES (6, 21, 156, 'Planning', 'Complete Planning Phase', 'COMPLETE', 6, 'COMPLETED', FALSE, FALSE, TRUE, FALSE, '2025-06-22T20:27:31.589765+00:00', 3, '2025-06-23T00:37:27.688010+00:00', 3, '2025-06-25T18:07:54.960735+00:00', '2025-06-25T18:07:54.960735+00:00');
INSERT INTO workflow_activities (activity_id, cycle_id, report_id, phase_name, activity_name, activity_type, activity_order, status, can_start, can_complete, is_manual, is_optional, started_at, completed_at, completed_by, created_at, updated_at) VALUES (7, 21, 156, 'Request for Information', 'Start Request Info', 'START', 1, 'COMPLETED', FALSE, FALSE, TRUE, FALSE, '2025-06-24T19:00:00+00:00', '2025-06-24T23:59:01.522050+00:00', 3, '2025-06-25T18:08:55.780205+00:00', '2025-06-25T18:08:55.780205+00:00');
INSERT INTO workflow_activities (activity_id, cycle_id, report_id, phase_name, activity_name, activity_type, activity_order, status, can_start, can_complete, is_manual, is_optional, started_at, completed_at, completed_by, created_at, updated_at) VALUES (8, 21, 156, 'Request for Information', 'Generate Test Cases', 'TASK', 2, 'COMPLETED', FALSE, FALSE, TRUE, FALSE, '2025-06-24T19:00:00+00:00', '2025-06-24T23:59:01.522050+00:00', 3, '2025-06-25T18:08:55.780205+00:00', '2025-06-25T18:08:55.780205+00:00');
INSERT INTO workflow_activities (activity_id, cycle_id, report_id, phase_name, activity_name, activity_type, activity_order, status, can_start, can_complete, is_manual, is_optional, started_at, completed_at, completed_by, created_at, updated_at) VALUES (9, 21, 156, 'Request for Information', 'Data Provider Upload', 'TASK', 3, 'COMPLETED', FALSE, FALSE, TRUE, FALSE, '2025-06-24T19:00:00+00:00', '2025-06-24T23:59:01.522050+00:00', 3, '2025-06-25T18:08:55.780205+00:00', '2025-06-25T18:08:55.780205+00:00');
INSERT INTO workflow_activities (activity_id, cycle_id, report_id, phase_name, activity_name, activity_type, activity_order, status, can_start, can_complete, is_manual, is_optional, started_at, completed_at, completed_by, created_at, updated_at) VALUES (10, 21, 156, 'Request for Information', 'Complete Request Info', 'COMPLETE', 4, 'COMPLETED', FALSE, FALSE, TRUE, FALSE, '2025-06-24T19:00:00+00:00', '2025-06-24T23:59:01.522050+00:00', 3, '2025-06-25T18:08:55.780205+00:00', '2025-06-25T18:08:55.780205+00:00');
INSERT INTO workflow_activities (activity_id, cycle_id, report_id, phase_name, activity_name, activity_type, activity_order, status, can_start, can_complete, is_manual, is_optional, started_at, started_by, completed_by, created_at, updated_at) VALUES (11, 21, 156, 'Data Provider Identification', 'Start Data Provider ID', 'START', 1, 'COMPLETED', FALSE, FALSE, TRUE, FALSE, '2025-06-24T17:36:49.275861+00:00', 3, 3, '2025-06-25T18:08:55.780205+00:00', '2025-06-25T18:08:55.780205+00:00');
INSERT INTO workflow_activities (activity_id, cycle_id, report_id, phase_name, activity_name, activity_type, activity_order, status, can_start, can_complete, is_manual, is_optional, started_at, started_by, created_at, updated_at) VALUES (12, 21, 156, 'Data Provider Identification', 'LOB Executive Assignment', 'TASK', 2, 'IN_PROGRESS', FALSE, TRUE, TRUE, FALSE, '2025-06-24T17:36:49.275861+00:00', 3, '2025-06-25T18:08:55.780205+00:00', '2025-06-25T18:08:55.780205+00:00');
INSERT INTO workflow_activities (activity_id, cycle_id, report_id, phase_name, activity_name, activity_type, activity_order, status, can_start, can_complete, is_manual, is_optional, created_at, updated_at) VALUES (13, 21, 156, 'Data Provider Identification', 'Data Owner Assignment', 'TASK', 3, 'NOT_STARTED', FALSE, FALSE, TRUE, FALSE, '2025-06-25T18:08:55.780205+00:00', '2025-06-25T18:08:55.780205+00:00');
INSERT INTO workflow_activities (activity_id, cycle_id, report_id, phase_name, activity_name, activity_type, activity_order, status, can_start, can_complete, is_manual, is_optional, created_at, updated_at) VALUES (14, 21, 156, 'Data Provider Identification', 'Data Provider Assignment', 'TASK', 4, 'NOT_STARTED', FALSE, FALSE, TRUE, FALSE, '2025-06-25T18:08:55.780205+00:00', '2025-06-25T18:08:55.780205+00:00');
INSERT INTO workflow_activities (activity_id, cycle_id, report_id, phase_name, activity_name, activity_type, activity_order, status, can_start, can_complete, is_manual, is_optional, created_at, updated_at) VALUES (15, 21, 156, 'Data Provider Identification', 'Complete Provider ID', 'COMPLETE', 5, 'NOT_STARTED', FALSE, FALSE, TRUE, FALSE, '2025-06-25T18:08:55.780205+00:00', '2025-06-25T18:08:55.780205+00:00');
INSERT INTO workflow_activities (activity_id, cycle_id, report_id, phase_name, activity_name, activity_type, activity_order, status, can_start, can_complete, is_manual, is_optional, started_at, started_by, completed_by, created_at, updated_at) VALUES (16, 21, 156, 'Data Profiling', 'Start Data Profiling', 'START', 1, 'COMPLETED', FALSE, FALSE, TRUE, FALSE, '2025-06-23T04:09:03.308164+00:00', 3, 3, '2025-06-25T18:08:55.780205+00:00', '2025-06-25T18:08:55.780205+00:00');
INSERT INTO workflow_activities (activity_id, cycle_id, report_id, phase_name, activity_name, activity_type, activity_order, status, can_start, can_complete, is_manual, is_optional, started_at, started_by, completed_at, created_at, updated_at) VALUES (17, 21, 156, 'Data Profiling', 'Profile Data Sources', 'TASK', 2, 'COMPLETED', FALSE, TRUE, TRUE, FALSE, '2025-06-23T04:09:03.308164+00:00', 3, '2025-06-24T19:32:11.601260+00:00', '2025-06-25T18:08:55.780205+00:00', '2025-06-25T18:08:55.780205+00:00');
INSERT INTO workflow_activities (activity_id, cycle_id, report_id, phase_name, activity_name, activity_type, activity_order, status, can_start, can_complete, is_manual, is_optional, completed_at, created_at, updated_at) VALUES (18, 21, 156, 'Data Profiling', 'Document Findings', 'TASK', 3, 'COMPLETED', FALSE, FALSE, TRUE, FALSE, '2025-06-24T19:32:11.601260+00:00', '2025-06-25T18:08:55.780205+00:00', '2025-06-25T18:08:55.780205+00:00');
INSERT INTO workflow_activities (activity_id, cycle_id, report_id, phase_name, activity_name, activity_type, activity_order, status, can_start, can_complete, is_manual, is_optional, completed_at, created_at, updated_at) VALUES (19, 21, 156, 'Data Profiling', 'Complete Data Profiling', 'COMPLETE', 4, 'COMPLETED', FALSE, FALSE, TRUE, FALSE, '2025-06-24T19:32:11.601260+00:00', '2025-06-25T18:08:55.780205+00:00', '2025-06-25T18:08:55.780205+00:00');
INSERT INTO workflow_activities (activity_id, cycle_id, report_id, phase_name, activity_name, activity_type, activity_order, status, can_start, can_complete, is_manual, is_optional, started_at, started_by, completed_at, completed_by, created_at, updated_at) VALUES (20, 21, 156, 'Scoping', 'Start Scoping Phase', 'START', 1, 'COMPLETED', FALSE, FALSE, TRUE, FALSE, '2025-06-23T00:37:27.688458+00:00', 3, '2025-06-24T07:48:27.795565+00:00', 3, '2025-06-25T18:08:55.780205+00:00', '2025-06-25T18:08:55.780205+00:00');
INSERT INTO workflow_activities (activity_id, cycle_id, report_id, phase_name, activity_name, activity_type, activity_order, status, can_start, can_complete, is_manual, is_optional, started_at, started_by, completed_at, completed_by, created_at, updated_at) VALUES (21, 21, 156, 'Scoping', 'Define Scope', 'TASK', 2, 'COMPLETED', FALSE, FALSE, TRUE, FALSE, '2025-06-23T00:37:27.688458+00:00', 3, '2025-06-24T07:48:27.795565+00:00', 3, '2025-06-25T18:08:55.780205+00:00', '2025-06-25T18:08:55.780205+00:00');
INSERT INTO workflow_activities (activity_id, cycle_id, report_id, phase_name, activity_name, activity_type, activity_order, status, can_start, can_complete, is_manual, is_optional, started_at, started_by, completed_at, completed_by, created_at, updated_at) VALUES (22, 21, 156, 'Scoping', 'Tester Review', 'REVIEW', 3, 'COMPLETED', FALSE, FALSE, TRUE, FALSE, '2025-06-23T00:37:27.688458+00:00', 3, '2025-06-24T07:48:27.795565+00:00', 3, '2025-06-25T18:08:55.780205+00:00', '2025-06-25T18:08:55.780205+00:00');
INSERT INTO workflow_activities (activity_id, cycle_id, report_id, phase_name, activity_name, activity_type, activity_order, status, can_start, can_complete, is_manual, is_optional, started_at, started_by, completed_at, completed_by, created_at, updated_at) VALUES (23, 21, 156, 'Scoping', 'Report Owner Approval', 'APPROVAL', 4, 'COMPLETED', FALSE, FALSE, TRUE, FALSE, '2025-06-23T00:37:27.688458+00:00', 3, '2025-06-24T07:48:27.795565+00:00', 3, '2025-06-25T18:08:55.780205+00:00', '2025-06-25T18:08:55.780205+00:00');
INSERT INTO workflow_activities (activity_id, cycle_id, report_id, phase_name, activity_name, activity_type, activity_order, status, can_start, can_complete, is_manual, is_optional, started_at, started_by, completed_at, completed_by, created_at, updated_at) VALUES (24, 21, 156, 'Scoping', 'Complete Scoping Phase', 'COMPLETE', 5, 'COMPLETED', FALSE, FALSE, TRUE, FALSE, '2025-06-23T00:37:27.688458+00:00', 3, '2025-06-24T07:48:27.795565+00:00', 3, '2025-06-25T18:08:55.780205+00:00', '2025-06-25T18:08:55.780205+00:00');
INSERT INTO workflow_activities (activity_id, cycle_id, report_id, phase_name, activity_name, activity_type, activity_order, status, can_start, can_complete, is_manual, is_optional, completed_at, created_at, updated_at) VALUES (25, 21, 156, 'Sample Selection', 'Start Sample Selection', 'START', 1, 'COMPLETED', TRUE, FALSE, TRUE, FALSE, '2025-06-24T19:05:42.778201+00:00', '2025-06-25T18:08:55.780205+00:00', '2025-06-25T18:08:55.780205+00:00');
INSERT INTO workflow_activities (activity_id, cycle_id, report_id, phase_name, activity_name, activity_type, activity_order, status, can_start, can_complete, is_manual, is_optional, completed_at, created_at, updated_at) VALUES (26, 21, 156, 'Sample Selection', 'Generate Samples', 'TASK', 2, 'COMPLETED', FALSE, FALSE, TRUE, FALSE, '2025-06-24T19:05:42.778201+00:00', '2025-06-25T18:08:55.780205+00:00', '2025-06-25T18:08:55.780205+00:00');
INSERT INTO workflow_activities (activity_id, cycle_id, report_id, phase_name, activity_name, activity_type, activity_order, status, can_start, can_complete, is_manual, is_optional, completed_at, created_at, updated_at) VALUES (27, 21, 156, 'Sample Selection', 'Review Samples', 'TASK', 3, 'COMPLETED', FALSE, FALSE, TRUE, FALSE, '2025-06-24T19:05:42.778201+00:00', '2025-06-25T18:08:55.780205+00:00', '2025-06-25T18:08:55.780205+00:00');
INSERT INTO workflow_activities (activity_id, cycle_id, report_id, phase_name, activity_name, activity_type, activity_order, status, can_start, can_complete, is_manual, is_optional, completed_at, created_at, updated_at) VALUES (28, 21, 156, 'Sample Selection', 'Complete Sample Selection', 'COMPLETE', 4, 'COMPLETED', FALSE, FALSE, TRUE, FALSE, '2025-06-24T19:05:42.778201+00:00', '2025-06-25T18:08:55.780205+00:00', '2025-06-25T18:08:55.780205+00:00');
INSERT INTO workflow_activities (activity_id, cycle_id, report_id, phase_name, activity_name, activity_type, activity_order, status, can_start, can_complete, is_manual, is_optional, started_by, completed_at, completed_by, created_at, updated_at) VALUES (29, 21, 156, 'Test Execution', 'Start Test Execution', 'START', 1, 'COMPLETED', FALSE, FALSE, TRUE, FALSE, 1, '2025-06-25T19:14:57.261760+00:00', 1, '2025-06-25T18:08:55.780205+00:00', '2025-06-25T18:08:55.780205+00:00');
INSERT INTO workflow_activities (activity_id, cycle_id, report_id, phase_name, activity_name, activity_type, activity_order, status, can_start, can_complete, is_manual, is_optional, started_by, completed_at, created_at, updated_at) VALUES (30, 21, 156, 'Test Execution', 'Execute Tests', 'TASK', 2, 'COMPLETED', FALSE, TRUE, TRUE, FALSE, 1, '2025-06-25T19:14:57.261760+00:00', '2025-06-25T18:08:55.780205+00:00', '2025-06-25T18:08:55.780205+00:00');
INSERT INTO workflow_activities (activity_id, cycle_id, report_id, phase_name, activity_name, activity_type, activity_order, status, can_start, can_complete, is_manual, is_optional, completed_at, created_at, updated_at) VALUES (31, 21, 156, 'Test Execution', 'Document Results', 'TASK', 3, 'COMPLETED', FALSE, FALSE, TRUE, FALSE, '2025-06-25T19:14:57.261760+00:00', '2025-06-25T18:08:55.780205+00:00', '2025-06-25T18:08:55.780205+00:00');
INSERT INTO workflow_activities (activity_id, cycle_id, report_id, phase_name, activity_name, activity_type, activity_order, status, can_start, can_complete, is_manual, is_optional, completed_at, created_at, updated_at) VALUES (32, 21, 156, 'Test Execution', 'Complete Test Execution', 'COMPLETE', 4, 'COMPLETED', FALSE, FALSE, TRUE, FALSE, '2025-06-25T19:14:57.261760+00:00', '2025-06-25T18:08:55.780205+00:00', '2025-06-25T18:08:55.780205+00:00');
INSERT INTO workflow_activities (activity_id, cycle_id, report_id, phase_name, activity_name, activity_type, activity_order, status, can_start, can_complete, is_manual, is_optional, started_at, completed_at, created_at, updated_at) VALUES (33, 21, 156, 'Observation Management', 'Start Observation Management Phase', 'START', 1, 'COMPLETED', TRUE, TRUE, TRUE, FALSE, '2025-06-23T19:21:14.115383+00:00', '2025-06-23T19:21:14.115383+00:00', '2025-06-25T19:21:14.115383+00:00', '2025-06-25T19:21:14.115383+00:00');
INSERT INTO workflow_activities (activity_id, cycle_id, report_id, phase_name, activity_name, activity_type, activity_order, status, can_start, can_complete, is_manual, is_optional, started_at, completed_at, created_at, updated_at) VALUES (34, 21, 156, 'Observation Management', 'Create Observations', 'TASK', 2, 'COMPLETED', TRUE, TRUE, TRUE, FALSE, '2025-06-23T19:21:14.115383+00:00', '2025-06-24T19:21:14.115383+00:00', '2025-06-25T19:21:14.115383+00:00', '2025-06-25T19:21:14.115383+00:00');
INSERT INTO workflow_activities (activity_id, cycle_id, report_id, phase_name, activity_name, activity_type, activity_order, status, can_start, can_complete, is_manual, is_optional, started_at, completed_at, created_at, updated_at) VALUES (35, 21, 156, 'Observation Management', 'Group Observations', 'TASK', 3, 'COMPLETED', TRUE, TRUE, TRUE, FALSE, '2025-06-24T19:21:14.115383+00:00', '2025-06-24T19:21:14.115383+00:00', '2025-06-25T19:21:14.115383+00:00', '2025-06-25T19:21:14.115383+00:00');
INSERT INTO workflow_activities (activity_id, cycle_id, report_id, phase_name, activity_name, activity_type, activity_order, status, can_start, can_complete, is_manual, is_optional, started_at, completed_at, created_at, updated_at) VALUES (36, 21, 156, 'Observation Management', 'Rate Severity', 'TASK', 4, 'COMPLETED', TRUE, TRUE, TRUE, FALSE, '2025-06-24T19:21:14.115383+00:00', '2025-06-25T07:21:14.115383+00:00', '2025-06-25T19:21:14.115383+00:00', '2025-06-25T19:21:14.115383+00:00');
INSERT INTO workflow_activities (activity_id, cycle_id, report_id, phase_name, activity_name, activity_type, activity_order, status, can_start, can_complete, is_manual, is_optional, started_at, completed_at, created_at, updated_at) VALUES (37, 21, 156, 'Observation Management', 'Tester Review', 'REVIEW', 5, 'COMPLETED', TRUE, TRUE, TRUE, FALSE, '2025-06-25T07:21:14.115383+00:00', '2025-06-25T13:21:14.115383+00:00', '2025-06-25T19:21:14.115383+00:00', '2025-06-25T19:21:14.115383+00:00');
INSERT INTO workflow_activities (activity_id, cycle_id, report_id, phase_name, activity_name, activity_type, activity_order, status, can_start, can_complete, is_manual, is_optional, started_at, completed_at, created_at, updated_at) VALUES (38, 21, 156, 'Observation Management', 'Report Owner Approval', 'APPROVAL', 6, 'COMPLETED', TRUE, TRUE, TRUE, FALSE, '2025-06-25T13:21:14.115383+00:00', '2025-06-25T17:21:14.115383+00:00', '2025-06-25T19:21:14.115383+00:00', '2025-06-25T19:21:14.115383+00:00');
INSERT INTO workflow_activities (activity_id, cycle_id, report_id, phase_name, activity_name, activity_type, activity_order, status, can_start, can_complete, is_manual, is_optional, started_at, completed_at, created_at, updated_at) VALUES (39, 21, 156, 'Observation Management', 'Complete Observation Management Phase', 'COMPLETE', 7, 'COMPLETED', TRUE, TRUE, TRUE, FALSE, '2025-06-25T17:21:14.115383+00:00', '2025-06-25T17:21:14.115383+00:00', '2025-06-25T19:21:14.115383+00:00', '2025-06-25T19:21:14.115383+00:00');
INSERT INTO workflow_activities (activity_id, cycle_id, report_id, phase_name, activity_name, activity_type, activity_order, status, can_start, can_complete, is_manual, is_optional, created_at, updated_at) VALUES (40, 21, 156, 'Finalize Test Report', 'Start Finalize Test Report Phase', 'START', 1, 'NOT_STARTED', TRUE, FALSE, TRUE, FALSE, '2025-06-25T19:21:14.118066+00:00', '2025-06-25T19:21:14.118066+00:00');
INSERT INTO workflow_activities (activity_id, cycle_id, report_id, phase_name, activity_name, activity_type, activity_order, status, can_start, can_complete, is_manual, is_optional, created_at, updated_at) VALUES (41, 21, 156, 'Finalize Test Report', 'Generate Report', 'TASK', 2, 'NOT_STARTED', FALSE, FALSE, TRUE, FALSE, '2025-06-25T19:21:14.118066+00:00', '2025-06-25T19:21:14.118066+00:00');
INSERT INTO workflow_activities (activity_id, cycle_id, report_id, phase_name, activity_name, activity_type, activity_order, status, can_start, can_complete, is_manual, is_optional, created_at, updated_at) VALUES (42, 21, 156, 'Finalize Test Report', 'Review Report', 'REVIEW', 3, 'NOT_STARTED', FALSE, FALSE, TRUE, FALSE, '2025-06-25T19:21:14.118066+00:00', '2025-06-25T19:21:14.118066+00:00');
INSERT INTO workflow_activities (activity_id, cycle_id, report_id, phase_name, activity_name, activity_type, activity_order, status, can_start, can_complete, is_manual, is_optional, created_at, updated_at) VALUES (43, 21, 156, 'Finalize Test Report', 'Approve Report', 'APPROVAL', 4, 'NOT_STARTED', FALSE, FALSE, TRUE, FALSE, '2025-06-25T19:21:14.118066+00:00', '2025-06-25T19:21:14.118066+00:00');
INSERT INTO workflow_activities (activity_id, cycle_id, report_id, phase_name, activity_name, activity_type, activity_order, status, can_start, can_complete, is_manual, is_optional, created_at, updated_at) VALUES (44, 21, 156, 'Finalize Test Report', 'Complete Finalize Test Report Phase', 'COMPLETE', 5, 'NOT_STARTED', FALSE, FALSE, TRUE, FALSE, '2025-06-25T19:21:14.118066+00:00', '2025-06-25T19:21:14.118066+00:00');

-- Seed data for workflow_activity_dependencies
INSERT INTO workflow_activity_dependencies (dependency_id, phase_name, activity_name, depends_on_activity, dependency_type, is_active, created_at) VALUES (1, 'Planning', 'Generate Attributes', 'Start Planning Phase', 'completion', TRUE, '2025-06-25T17:32:05.484218+00:00');
INSERT INTO workflow_activity_dependencies (dependency_id, phase_name, activity_name, depends_on_activity, dependency_type, is_active, created_at) VALUES (2, 'Planning', 'Review Attributes', 'Generate Attributes', 'completion', TRUE, '2025-06-25T17:32:05.484218+00:00');
INSERT INTO workflow_activity_dependencies (dependency_id, phase_name, activity_name, depends_on_activity, dependency_type, is_active, created_at) VALUES (3, 'Planning', 'Tester Review', 'Review Attributes', 'completion', TRUE, '2025-06-25T17:32:05.484218+00:00');
INSERT INTO workflow_activity_dependencies (dependency_id, phase_name, activity_name, depends_on_activity, dependency_type, is_active, created_at) VALUES (4, 'Planning', 'Report Owner Approval', 'Tester Review', 'completion', TRUE, '2025-06-25T17:32:05.484218+00:00');
INSERT INTO workflow_activity_dependencies (dependency_id, phase_name, activity_name, depends_on_activity, dependency_type, is_active, created_at) VALUES (5, 'Planning', 'Complete Planning Phase', 'Report Owner Approval', 'approval', TRUE, '2025-06-25T17:32:05.484218+00:00');
INSERT INTO workflow_activity_dependencies (dependency_id, phase_name, activity_name, depends_on_activity, dependency_type, is_active, created_at) VALUES (6, 'Data Profiling', 'Profile Data Sources', 'Start Data Profiling', 'completion', TRUE, '2025-06-25T17:32:05.484218+00:00');
INSERT INTO workflow_activity_dependencies (dependency_id, phase_name, activity_name, depends_on_activity, dependency_type, is_active, created_at) VALUES (7, 'Data Profiling', 'Document Findings', 'Profile Data Sources', 'completion', TRUE, '2025-06-25T17:32:05.484218+00:00');
INSERT INTO workflow_activity_dependencies (dependency_id, phase_name, activity_name, depends_on_activity, dependency_type, is_active, created_at) VALUES (8, 'Data Profiling', 'Complete Data Profiling', 'Document Findings', 'completion', TRUE, '2025-06-25T17:32:05.484218+00:00');
INSERT INTO workflow_activity_dependencies (dependency_id, phase_name, activity_name, depends_on_activity, dependency_type, is_active, created_at) VALUES (9, 'Scoping', 'Define Scope', 'Start Scoping Phase', 'completion', TRUE, '2025-06-25T17:32:05.484218+00:00');
INSERT INTO workflow_activity_dependencies (dependency_id, phase_name, activity_name, depends_on_activity, dependency_type, is_active, created_at) VALUES (10, 'Scoping', 'Tester Review', 'Define Scope', 'completion', TRUE, '2025-06-25T17:32:05.484218+00:00');
INSERT INTO workflow_activity_dependencies (dependency_id, phase_name, activity_name, depends_on_activity, dependency_type, is_active, created_at) VALUES (11, 'Scoping', 'Report Owner Approval', 'Tester Review', 'completion', TRUE, '2025-06-25T17:32:05.484218+00:00');
INSERT INTO workflow_activity_dependencies (dependency_id, phase_name, activity_name, depends_on_activity, dependency_type, is_active, created_at) VALUES (12, 'Scoping', 'Complete Scoping Phase', 'Report Owner Approval', 'approval', TRUE, '2025-06-25T17:32:05.484218+00:00');
INSERT INTO workflow_activity_dependencies (dependency_id, phase_name, activity_name, depends_on_activity, dependency_type, is_active, created_at) VALUES (13, 'Sample Selection', 'Generate Samples', 'Start Sample Selection', 'completion', TRUE, '2025-06-25T17:32:05.484218+00:00');
INSERT INTO workflow_activity_dependencies (dependency_id, phase_name, activity_name, depends_on_activity, dependency_type, is_active, created_at) VALUES (14, 'Sample Selection', 'Review Samples', 'Generate Samples', 'completion', TRUE, '2025-06-25T17:32:05.484218+00:00');
INSERT INTO workflow_activity_dependencies (dependency_id, phase_name, activity_name, depends_on_activity, dependency_type, is_active, created_at) VALUES (15, 'Sample Selection', 'Complete Sample Selection', 'Review Samples', 'completion', TRUE, '2025-06-25T17:32:05.484218+00:00');
INSERT INTO workflow_activity_dependencies (dependency_id, phase_name, activity_name, depends_on_activity, dependency_type, is_active, created_at) VALUES (16, 'Data Provider ID', 'LOB Executive Assignment', 'Start Data Provider ID', 'completion', TRUE, '2025-06-25T17:32:05.484218+00:00');
INSERT INTO workflow_activity_dependencies (dependency_id, phase_name, activity_name, depends_on_activity, dependency_type, is_active, created_at) VALUES (17, 'Data Provider ID', 'Data Owner Assignment', 'LOB Executive Assignment', 'completion', TRUE, '2025-06-25T17:32:05.484218+00:00');
INSERT INTO workflow_activity_dependencies (dependency_id, phase_name, activity_name, depends_on_activity, dependency_type, is_active, created_at) VALUES (18, 'Data Provider ID', 'Data Provider Assignment', 'Data Owner Assignment', 'completion', TRUE, '2025-06-25T17:32:05.484218+00:00');
INSERT INTO workflow_activity_dependencies (dependency_id, phase_name, activity_name, depends_on_activity, dependency_type, is_active, created_at) VALUES (19, 'Data Provider ID', 'Complete Provider ID', 'Data Provider Assignment', 'completion', TRUE, '2025-06-25T17:32:05.484218+00:00');
INSERT INTO workflow_activity_dependencies (dependency_id, phase_name, activity_name, depends_on_activity, dependency_type, is_active, created_at) VALUES (20, 'Data Owner ID', 'Assign LOB Executives', 'Start Data Owner ID', 'completion', TRUE, '2025-06-25T17:32:05.484218+00:00');
INSERT INTO workflow_activity_dependencies (dependency_id, phase_name, activity_name, depends_on_activity, dependency_type, is_active, created_at) VALUES (21, 'Data Owner ID', 'Assign Data Owners', 'Assign LOB Executives', 'completion', TRUE, '2025-06-25T17:32:05.484218+00:00');
INSERT INTO workflow_activity_dependencies (dependency_id, phase_name, activity_name, depends_on_activity, dependency_type, is_active, created_at) VALUES (22, 'Data Owner ID', 'Complete Data Owner ID', 'Assign Data Owners', 'completion', TRUE, '2025-06-25T17:32:05.484218+00:00');
INSERT INTO workflow_activity_dependencies (dependency_id, phase_name, activity_name, depends_on_activity, dependency_type, is_active, created_at) VALUES (23, 'Request Info', 'Generate Test Cases', 'Start Request Info', 'completion', TRUE, '2025-06-25T17:32:05.484218+00:00');
INSERT INTO workflow_activity_dependencies (dependency_id, phase_name, activity_name, depends_on_activity, dependency_type, is_active, created_at) VALUES (24, 'Request Info', 'Data Provider Upload', 'Generate Test Cases', 'completion', TRUE, '2025-06-25T17:32:05.484218+00:00');
INSERT INTO workflow_activity_dependencies (dependency_id, phase_name, activity_name, depends_on_activity, dependency_type, is_active, created_at) VALUES (25, 'Request Info', 'Complete Request Info', 'Data Provider Upload', 'any', TRUE, '2025-06-25T17:32:05.484218+00:00');
INSERT INTO workflow_activity_dependencies (dependency_id, phase_name, activity_name, depends_on_activity, dependency_type, is_active, created_at) VALUES (26, 'Test Execution', 'Execute Tests', 'Start Test Execution', 'completion', TRUE, '2025-06-25T17:32:05.484218+00:00');
INSERT INTO workflow_activity_dependencies (dependency_id, phase_name, activity_name, depends_on_activity, dependency_type, is_active, created_at) VALUES (27, 'Test Execution', 'Document Results', 'Execute Tests', 'any', TRUE, '2025-06-25T17:32:05.484218+00:00');
INSERT INTO workflow_activity_dependencies (dependency_id, phase_name, activity_name, depends_on_activity, dependency_type, is_active, created_at) VALUES (28, 'Test Execution', 'Complete Test Execution', 'Document Results', 'completion', TRUE, '2025-06-25T17:32:05.484218+00:00');
INSERT INTO workflow_activity_dependencies (dependency_id, phase_name, activity_name, depends_on_activity, dependency_type, is_active, created_at) VALUES (29, 'Observation Management', 'Create Observations', 'Start Observations', 'completion', TRUE, '2025-06-25T17:32:05.484218+00:00');
INSERT INTO workflow_activity_dependencies (dependency_id, phase_name, activity_name, depends_on_activity, dependency_type, is_active, created_at) VALUES (30, 'Observation Management', 'Data Provider Response', 'Create Observations', 'any', TRUE, '2025-06-25T17:32:05.484218+00:00');
INSERT INTO workflow_activity_dependencies (dependency_id, phase_name, activity_name, depends_on_activity, dependency_type, is_active, created_at) VALUES (31, 'Observation Management', 'Finalize Observations', 'Create Observations', 'any', TRUE, '2025-06-25T17:32:05.484218+00:00');
INSERT INTO workflow_activity_dependencies (dependency_id, phase_name, activity_name, depends_on_activity, dependency_type, is_active, created_at) VALUES (32, 'Observation Management', 'Complete Observations', 'Finalize Observations', 'completion', TRUE, '2025-06-25T17:32:05.484218+00:00');
INSERT INTO workflow_activity_dependencies (dependency_id, phase_name, activity_name, depends_on_activity, dependency_type, is_active, created_at) VALUES (33, 'Test Report', 'Generate Report', 'Start Test Report', 'completion', TRUE, '2025-06-25T17:32:05.484218+00:00');
INSERT INTO workflow_activity_dependencies (dependency_id, phase_name, activity_name, depends_on_activity, dependency_type, is_active, created_at) VALUES (34, 'Test Report', 'Review Report', 'Generate Report', 'completion', TRUE, '2025-06-25T17:32:05.484218+00:00');
INSERT INTO workflow_activity_dependencies (dependency_id, phase_name, activity_name, depends_on_activity, dependency_type, is_active, created_at) VALUES (35, 'Test Report', 'Approve Report', 'Review Report', 'completion', TRUE, '2025-06-25T17:32:05.484218+00:00');
INSERT INTO workflow_activity_dependencies (dependency_id, phase_name, activity_name, depends_on_activity, dependency_type, is_active, created_at) VALUES (36, 'Test Report', 'Complete Test Report', 'Approve Report', 'approval', TRUE, '2025-06-25T17:32:05.484218+00:00');

-- Seed data for workflow_activity_templates
INSERT INTO workflow_activity_templates (template_id, phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, required_role, is_active, created_at, updated_at) VALUES (1, 'Planning', 'Start Planning Phase', 'START', 1, 'Initialize planning phase', TRUE, FALSE, 'Tester', TRUE, '2025-06-25T17:32:05.470352+00:00', '2025-06-25T17:32:05.470352+00:00');
INSERT INTO workflow_activity_templates (template_id, phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, required_role, is_active, created_at, updated_at) VALUES (2, 'Planning', 'Generate Attributes', 'TASK', 2, 'Generate test attributes using LLM', FALSE, FALSE, 'Tester', TRUE, '2025-06-25T17:32:05.470352+00:00', '2025-06-25T17:32:05.470352+00:00');
INSERT INTO workflow_activity_templates (template_id, phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, required_role, is_active, created_at, updated_at) VALUES (3, 'Planning', 'Review Attributes', 'TASK', 3, 'Review and edit generated attributes', TRUE, FALSE, 'Tester', TRUE, '2025-06-25T17:32:05.470352+00:00', '2025-06-25T17:32:05.470352+00:00');
INSERT INTO workflow_activity_templates (template_id, phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, required_role, is_active, created_at, updated_at) VALUES (4, 'Planning', 'Tester Review', 'REVIEW', 4, 'Submit for report owner review', TRUE, FALSE, 'Tester', TRUE, '2025-06-25T17:32:05.470352+00:00', '2025-06-25T17:32:05.470352+00:00');
INSERT INTO workflow_activity_templates (template_id, phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, required_role, is_active, created_at, updated_at) VALUES (5, 'Planning', 'Report Owner Approval', 'APPROVAL', 5, 'Report owner approves attributes', TRUE, FALSE, 'Report Owner', TRUE, '2025-06-25T17:32:05.470352+00:00', '2025-06-25T17:32:05.470352+00:00');
INSERT INTO workflow_activity_templates (template_id, phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, is_active, created_at, updated_at) VALUES (6, 'Planning', 'Complete Planning Phase', 'COMPLETE', 6, 'Finalize planning phase', FALSE, FALSE, TRUE, '2025-06-25T17:32:05.470352+00:00', '2025-06-25T17:32:05.470352+00:00');
INSERT INTO workflow_activity_templates (template_id, phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, required_role, is_active, created_at, updated_at) VALUES (7, 'Data Profiling', 'Start Data Profiling', 'START', 1, 'Initialize data profiling', TRUE, FALSE, 'Tester', TRUE, '2025-06-25T17:32:05.470352+00:00', '2025-06-25T17:32:05.470352+00:00');
INSERT INTO workflow_activity_templates (template_id, phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, required_role, is_active, created_at, updated_at) VALUES (8, 'Data Profiling', 'Profile Data Sources', 'TASK', 2, 'Analyze data sources and patterns', TRUE, FALSE, 'Tester', TRUE, '2025-06-25T17:32:05.470352+00:00', '2025-06-25T17:32:05.470352+00:00');
INSERT INTO workflow_activity_templates (template_id, phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, required_role, is_active, created_at, updated_at) VALUES (9, 'Data Profiling', 'Document Findings', 'TASK', 3, 'Document profiling results', TRUE, FALSE, 'Tester', TRUE, '2025-06-25T17:32:05.470352+00:00', '2025-06-25T17:32:05.470352+00:00');
INSERT INTO workflow_activity_templates (template_id, phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, required_role, is_active, created_at, updated_at) VALUES (10, 'Data Profiling', 'Complete Data Profiling', 'COMPLETE', 4, 'Finalize data profiling', TRUE, FALSE, 'Tester', TRUE, '2025-06-25T17:32:05.470352+00:00', '2025-06-25T17:32:05.470352+00:00');
INSERT INTO workflow_activity_templates (template_id, phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, required_role, is_active, created_at, updated_at) VALUES (11, 'Scoping', 'Start Scoping Phase', 'START', 1, 'Initialize scoping phase', TRUE, FALSE, 'Tester', TRUE, '2025-06-25T17:32:05.470352+00:00', '2025-06-25T17:32:05.470352+00:00');
INSERT INTO workflow_activity_templates (template_id, phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, required_role, is_active, created_at, updated_at) VALUES (12, 'Scoping', 'Define Scope', 'TASK', 2, 'Define testing scope and boundaries', TRUE, FALSE, 'Tester', TRUE, '2025-06-25T17:32:05.470352+00:00', '2025-06-25T17:32:05.470352+00:00');
INSERT INTO workflow_activity_templates (template_id, phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, required_role, is_active, created_at, updated_at) VALUES (13, 'Scoping', 'Tester Review', 'REVIEW', 3, 'Submit scope for approval', TRUE, FALSE, 'Tester', TRUE, '2025-06-25T17:32:05.470352+00:00', '2025-06-25T17:32:05.470352+00:00');
INSERT INTO workflow_activity_templates (template_id, phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, required_role, is_active, created_at, updated_at) VALUES (14, 'Scoping', 'Report Owner Approval', 'APPROVAL', 4, 'Report owner approves scope', TRUE, FALSE, 'Report Owner', TRUE, '2025-06-25T17:32:05.470352+00:00', '2025-06-25T17:32:05.470352+00:00');
INSERT INTO workflow_activity_templates (template_id, phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, is_active, created_at, updated_at) VALUES (15, 'Scoping', 'Complete Scoping Phase', 'COMPLETE', 5, 'Finalize scoping phase', FALSE, FALSE, TRUE, '2025-06-25T17:32:05.470352+00:00', '2025-06-25T17:32:05.470352+00:00');
INSERT INTO workflow_activity_templates (template_id, phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, required_role, is_active, created_at, updated_at) VALUES (16, 'Sample Selection', 'Start Sample Selection', 'START', 1, 'Initialize sample selection', TRUE, FALSE, 'Tester', TRUE, '2025-06-25T17:32:05.470352+00:00', '2025-06-25T17:32:05.470352+00:00');
INSERT INTO workflow_activity_templates (template_id, phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, required_role, is_active, created_at, updated_at) VALUES (17, 'Sample Selection', 'Generate Samples', 'TASK', 2, 'Generate test samples', TRUE, FALSE, 'Tester', TRUE, '2025-06-25T17:32:05.470352+00:00', '2025-06-25T17:32:05.470352+00:00');
INSERT INTO workflow_activity_templates (template_id, phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, required_role, is_active, created_at, updated_at) VALUES (18, 'Sample Selection', 'Review Samples', 'TASK', 3, 'Review and adjust samples', TRUE, FALSE, 'Tester', TRUE, '2025-06-25T17:32:05.470352+00:00', '2025-06-25T17:32:05.470352+00:00');
INSERT INTO workflow_activity_templates (template_id, phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, required_role, is_active, created_at, updated_at) VALUES (19, 'Sample Selection', 'Complete Sample Selection', 'COMPLETE', 4, 'Finalize sample selection', TRUE, FALSE, 'Tester', TRUE, '2025-06-25T17:32:05.470352+00:00', '2025-06-25T17:32:05.470352+00:00');
INSERT INTO workflow_activity_templates (template_id, phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, required_role, is_active, created_at, updated_at) VALUES (20, 'Data Provider ID', 'Start Data Provider ID', 'START', 1, 'Initialize data provider identification', TRUE, FALSE, 'CDO', TRUE, '2025-06-25T17:32:05.470352+00:00', '2025-06-25T17:32:05.470352+00:00');
INSERT INTO workflow_activity_templates (template_id, phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, required_role, is_active, created_at, updated_at) VALUES (21, 'Data Provider ID', 'LOB Executive Assignment', 'TASK', 2, 'Assign LOB executives', TRUE, FALSE, 'CDO', TRUE, '2025-06-25T17:32:05.470352+00:00', '2025-06-25T17:32:05.470352+00:00');
INSERT INTO workflow_activity_templates (template_id, phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, required_role, is_active, created_at, updated_at) VALUES (22, 'Data Provider ID', 'Data Owner Assignment', 'TASK', 3, 'Assign data owners', TRUE, FALSE, 'Report Owner Executive', TRUE, '2025-06-25T17:32:05.470352+00:00', '2025-06-25T17:32:05.470352+00:00');
INSERT INTO workflow_activity_templates (template_id, phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, required_role, is_active, created_at, updated_at) VALUES (23, 'Data Provider ID', 'Data Provider Assignment', 'TASK', 4, 'Assign data providers', TRUE, FALSE, 'Data Owner', TRUE, '2025-06-25T17:32:05.470352+00:00', '2025-06-25T17:32:05.470352+00:00');
INSERT INTO workflow_activity_templates (template_id, phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, is_active, created_at, updated_at) VALUES (24, 'Data Provider ID', 'Complete Provider ID', 'COMPLETE', 5, 'Complete provider identification', FALSE, FALSE, TRUE, '2025-06-25T17:32:05.470352+00:00', '2025-06-25T17:32:05.470352+00:00');
INSERT INTO workflow_activity_templates (template_id, phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, required_role, is_active, created_at, updated_at) VALUES (25, 'Data Owner ID', 'Start Data Owner ID', 'START', 1, 'Initialize data owner identification', TRUE, FALSE, 'CDO', TRUE, '2025-06-25T17:32:05.470352+00:00', '2025-06-25T17:32:05.470352+00:00');
INSERT INTO workflow_activity_templates (template_id, phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, required_role, is_active, created_at, updated_at) VALUES (26, 'Data Owner ID', 'Assign LOB Executives', 'TASK', 2, 'CDO assigns LOB executives', TRUE, FALSE, 'CDO', TRUE, '2025-06-25T17:32:05.470352+00:00', '2025-06-25T17:32:05.470352+00:00');
INSERT INTO workflow_activity_templates (template_id, phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, required_role, is_active, created_at, updated_at) VALUES (27, 'Data Owner ID', 'Assign Data Owners', 'TASK', 3, 'Executives assign data owners', TRUE, FALSE, 'Report Owner Executive', TRUE, '2025-06-25T17:32:05.470352+00:00', '2025-06-25T17:32:05.470352+00:00');
INSERT INTO workflow_activity_templates (template_id, phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, is_active, created_at, updated_at) VALUES (28, 'Data Owner ID', 'Complete Data Owner ID', 'COMPLETE', 4, 'Complete data owner identification', FALSE, FALSE, TRUE, '2025-06-25T17:32:05.470352+00:00', '2025-06-25T17:32:05.470352+00:00');
INSERT INTO workflow_activity_templates (template_id, phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, auto_complete_on_event, is_active, created_at, updated_at) VALUES (29, 'Request Info', 'Start Request Info', 'START', 1, 'Initialize request info phase', FALSE, FALSE, 'sample_selection_complete', TRUE, '2025-06-25T17:32:05.470352+00:00', '2025-06-25T17:32:05.470352+00:00');
INSERT INTO workflow_activity_templates (template_id, phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, is_active, created_at, updated_at) VALUES (30, 'Request Info', 'Generate Test Cases', 'TASK', 2, 'Generate test cases FROM cycle_report_sample_selection_samples', FALSE, FALSE, TRUE, '2025-06-25T17:32:05.470352+00:00', '2025-06-25T17:32:05.470352+00:00');
INSERT INTO workflow_activity_templates (template_id, phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, required_role, is_active, created_at, updated_at) VALUES (31, 'Request Info', 'Data Provider Upload', 'TASK', 3, 'Data providers upload documents', TRUE, FALSE, 'Data Provider', TRUE, '2025-06-25T17:32:05.470352+00:00', '2025-06-25T17:32:05.470352+00:00');
INSERT INTO workflow_activity_templates (template_id, phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, is_active, created_at, updated_at) VALUES (32, 'Request Info', 'Complete Request Info', 'COMPLETE', 4, 'Complete request info phase', FALSE, FALSE, TRUE, '2025-06-25T17:32:05.470352+00:00', '2025-06-25T17:32:05.470352+00:00');
INSERT INTO workflow_activity_templates (template_id, phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, required_role, is_active, created_at, updated_at) VALUES (33, 'Test Execution', 'Start Test Execution', 'START', 1, 'Initialize test execution', TRUE, FALSE, 'Tester', TRUE, '2025-06-25T17:32:05.470352+00:00', '2025-06-25T17:32:05.470352+00:00');
INSERT INTO workflow_activity_templates (template_id, phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, required_role, is_active, created_at, updated_at) VALUES (34, 'Test Execution', 'Execute Tests', 'TASK', 2, 'Execute test cases', TRUE, FALSE, 'Tester', TRUE, '2025-06-25T17:32:05.470352+00:00', '2025-06-25T17:32:05.470352+00:00');
INSERT INTO workflow_activity_templates (template_id, phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, required_role, is_active, created_at, updated_at) VALUES (35, 'Test Execution', 'Document Results', 'TASK', 3, 'Document test results', TRUE, FALSE, 'Tester', TRUE, '2025-06-25T17:32:05.470352+00:00', '2025-06-25T17:32:05.470352+00:00');
INSERT INTO workflow_activity_templates (template_id, phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, required_role, is_active, created_at, updated_at) VALUES (36, 'Test Execution', 'Complete Test Execution', 'COMPLETE', 4, 'Complete test execution', TRUE, FALSE, 'Tester', TRUE, '2025-06-25T17:32:05.470352+00:00', '2025-06-25T17:32:05.470352+00:00');
INSERT INTO workflow_activity_templates (template_id, phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, required_role, is_active, created_at, updated_at) VALUES (37, 'Observation Management', 'Start Observations', 'START', 1, 'Initialize observation management', TRUE, FALSE, 'Tester', TRUE, '2025-06-25T17:32:05.470352+00:00', '2025-06-25T17:32:05.470352+00:00');
INSERT INTO workflow_activity_templates (template_id, phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, required_role, is_active, created_at, updated_at) VALUES (38, 'Observation Management', 'Create Observations', 'TASK', 2, 'Create and document observations', TRUE, FALSE, 'Tester', TRUE, '2025-06-25T17:32:05.470352+00:00', '2025-06-25T17:32:05.470352+00:00');
INSERT INTO workflow_activity_templates (template_id, phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, required_role, is_active, created_at, updated_at) VALUES (39, 'Observation Management', 'Data Provider Response', 'TASK', 3, 'Data providers respond to observations', TRUE, TRUE, 'Data Provider', TRUE, '2025-06-25T17:32:05.470352+00:00', '2025-06-25T17:32:05.470352+00:00');
INSERT INTO workflow_activity_templates (template_id, phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, required_role, is_active, created_at, updated_at) VALUES (40, 'Observation Management', 'Finalize Observations', 'TASK', 4, 'Finalize all observations', TRUE, FALSE, 'Tester', TRUE, '2025-06-25T17:32:05.470352+00:00', '2025-06-25T17:32:05.470352+00:00');
INSERT INTO workflow_activity_templates (template_id, phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, required_role, is_active, created_at, updated_at) VALUES (41, 'Observation Management', 'Complete Observations', 'COMPLETE', 5, 'Complete observation management', TRUE, FALSE, 'Tester', TRUE, '2025-06-25T17:32:05.470352+00:00', '2025-06-25T17:32:05.470352+00:00');
INSERT INTO workflow_activity_templates (template_id, phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, required_role, is_active, created_at, updated_at) VALUES (42, 'Test Report', 'Start Test Report', 'START', 1, 'Initialize test report generation', TRUE, FALSE, 'Tester', TRUE, '2025-06-25T17:32:05.470352+00:00', '2025-06-25T17:32:05.470352+00:00');
INSERT INTO workflow_activity_templates (template_id, phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, required_role, is_active, created_at, updated_at) VALUES (43, 'Test Report', 'Generate Report', 'TASK', 2, 'Generate test report', TRUE, FALSE, 'Tester', TRUE, '2025-06-25T17:32:05.470352+00:00', '2025-06-25T17:32:05.470352+00:00');
INSERT INTO workflow_activity_templates (template_id, phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, required_role, is_active, created_at, updated_at) VALUES (44, 'Test Report', 'Review Report', 'REVIEW', 3, 'Review generated report', TRUE, FALSE, 'Test Manager', TRUE, '2025-06-25T17:32:05.470352+00:00', '2025-06-25T17:32:05.470352+00:00');
INSERT INTO workflow_activity_templates (template_id, phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, required_role, is_active, created_at, updated_at) VALUES (45, 'Test Report', 'Approve Report', 'APPROVAL', 4, 'Approve final report', TRUE, FALSE, 'Report Owner', TRUE, '2025-06-25T17:32:05.470352+00:00', '2025-06-25T17:32:05.470352+00:00');
INSERT INTO workflow_activity_templates (template_id, phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, is_active, created_at, updated_at) VALUES (46, 'Test Report', 'Complete Test Report', 'COMPLETE', 5, 'Complete test report phase', FALSE, FALSE, TRUE, '2025-06-25T17:32:05.470352+00:00', '2025-06-25T17:32:05.470352+00:00');

-- Seed data for workflow_phases
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, planned_start_date, planned_end_date, actual_start_date, actual_end_date, created_at, updated_at, state, schedule_status, completed_by, notes) VALUES (48, 21, 156, 'Planning', 'Complete', 2025-06-22, 2025-06-29, '2025-06-22T20:27:31.589765+00:00', '2025-06-23T00:37:27.688010+00:00', '2025-06-22T23:34:32.984331+00:00', '2025-06-22T20:37:27.664505+00:00', 'Complete', 'On Track', 3, 'Planning phase completed via simplified interface');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, planned_start_date, planned_end_date, actual_start_date, created_at, updated_at, state, schedule_status, started_by) VALUES (49, 21, 156, 'Data Profiling', 'In Progress', 2025-06-26, 2025-06-29, '2025-06-23T04:09:03.308164+00:00', '2025-06-22T23:34:32.984395+00:00', '2025-06-23T00:09:03.292640+00:00', 'In Progress', 'On Track', 3);
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, planned_start_date, planned_end_date, actual_start_date, actual_end_date, created_at, updated_at, state, schedule_status, started_by, completed_by, notes) VALUES (50, 21, 156, 'Scoping', 'Complete', 2025-06-30, 2025-07-04, '2025-06-23T00:37:27.688458+00:00', '2025-06-24T07:48:27.795565+00:00', '2025-06-22T23:34:32.984419+00:00', '2025-06-24T03:48:27.811696+00:00', 'Complete', 'On Track', 3, 3, 'Scoping phase completed');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, planned_start_date, planned_end_date, actual_start_date, created_at, updated_at, state, schedule_status, phase_data) VALUES (51, 21, 156, 'Sample Selection', 'Complete', 2025-06-24, 2025-07-01, '2025-06-24T15:05:42.778201+00:00', '2025-06-22T23:34:32.984436+00:00', '2025-06-24T11:40:20.414757+00:00', 'Not Started', 'On Track', '{"cycle_report_sample_selection_samples": [{"cycle_id": 21, "report_id": 156, "sample_id": "C21_R156_S001", "created_at": "2025-06-24T11:35:38.038947", "updated_at": "2025-06-24T11:37:18.673662", "sample_data": {"Bank ID": "2347891", "Period ID": "2024-01-31", "Customer ID": "CUS789234561", "Reference Number": "4538291076453", "Current Credit limit": "25000"}, "generated_at": "2025-06-24T11:35:38.038939", "generated_by": "Jane Doe", "is_submitted": true, "lob_assignment": "GBM", "lob_updated_at": "2025-06-24T11:37:23.142368", "lob_updated_by": "Jane Doe", "version_number": 1, "tester_decision": "include", "version_reviewed": 1, "generation_method": "LLM Generated", "primary_key_value": "4538291076453", "tester_decision_at": "2025-06-24T11:37:18.673658", "tester_decision_by": "Jane Doe", "generated_by_user_id": 3, "latest_submission_id": "f8b00ad1-d8cb-401a-951b-dda1607cde6b", "report_owner_decision": "approved", "report_owner_feedback": null, "tester_decision_by_id": 3, "report_owner_reviewed_at": "2025-06-24T11:40:20.432699", "report_owner_reviewed_by": "Mike Johnson", "latest_submission_version": 1}, {"cycle_id": 21, "report_id": 156, "sample_id": "C21_R156_S003", "created_at": "2025-06-24T11:35:38.038959", "updated_at": "2025-06-24T11:37:20.589131", "sample_data": {"Bank ID": "2347891", "Period ID": "2024-01-31", "Customer ID": "CUS789234789", "Reference Number": "4538291076999", "Current Credit limit": "12500"}, "generated_at": "2025-06-24T11:35:38.038956", "generated_by": "Jane Doe", "is_submitted": true, "lob_assignment": "GBM", "lob_updated_at": "2025-06-24T11:37:26.151536", "lob_updated_by": "Jane Doe", "version_number": 1, "tester_decision": "include", "version_reviewed": 1, "generation_method": "LLM Generated", "primary_key_value": "4538291076999", "tester_decision_at": "2025-06-24T11:37:20.589118", "tester_decision_by": "Jane Doe", "generated_by_user_id": 3, "latest_submission_id": "f8b00ad1-d8cb-401a-951b-dda1607cde6b", "report_owner_decision": "approved", "report_owner_feedback": null, "tester_decision_by_id": 3, "report_owner_reviewed_at": "2025-06-24T11:40:20.432703", "report_owner_reviewed_by": "Mike Johnson", "latest_submission_version": 1}], "submissions": [{"notes": "", "status": "approved", "reviewed_at": "2025-06-24T11:40:20.432676", "reviewed_by": "Mike Johnson", "submitted_at": "2025-06-24T11:37:30.923372", "submitted_by": "Jane Doe", "submission_id": "f8b00ad1-d8cb-401a-951b-dda1607cde6b", "total_samples": 2, "reviewed_by_id": 4, "version_number": 1, "pending_samples": 0, "review_feedback": "APPROVED", "submitted_by_id": 3, "excluded_samples": 0, "included_samples": 2, "samples_snapshot": [{"cycle_id": 21, "report_id": 156, "sample_id": "C21_R156_S001", "created_at": "2025-06-24T11:35:38.038947", "updated_at": "2025-06-24T11:37:18.673662", "sample_data": {"Bank ID": "2347891", "Period ID": "2024-01-31", "Customer ID": "CUS789234561", "Reference Number": "4538291076453", "Current Credit limit": "25000"}, "generated_at": "2025-06-24T11:35:38.038939", "generated_by": "Jane Doe", "is_submitted": false, "submitted_at": "2025-06-24T11:37:30.923352", "submitted_by": "Jane Doe", "submission_id": "f8b00ad1-d8cb-401a-951b-dda1607cde6b", "lob_assignment": "GBM", "lob_updated_at": "2025-06-24T11:37:23.142368", "lob_updated_by": "Jane Doe", "version_number": 1, "submitted_by_id": 3, "tester_decision": "include", "generation_method": "LLM Generated", "primary_key_value": "4538291076453", "tester_decision_at": "2025-06-24T11:37:18.673658", "tester_decision_by": "Jane Doe", "generated_by_user_id": 3, "report_owner_decision": "approved", "report_owner_feedback": null, "tester_decision_by_id": 3, "report_owner_reviewed_at": "2025-06-24T11:40:20.432681", "report_owner_reviewed_by": "Mike Johnson"}, {"cycle_id": 21, "report_id": 156, "sample_id": "C21_R156_S003", "created_at": "2025-06-24T11:35:38.038959", "updated_at": "2025-06-24T11:37:20.589131", "sample_data": {"Bank ID": "2347891", "Period ID": "2024-01-31", "Customer ID": "CUS789234789", "Reference Number": "4538291076999", "Current Credit limit": "12500"}, "generated_at": "2025-06-24T11:35:38.038956", "generated_by": "Jane Doe", "is_submitted": false, "submitted_at": "2025-06-24T11:37:30.923366", "submitted_by": "Jane Doe", "submission_id": "f8b00ad1-d8cb-401a-951b-dda1607cde6b", "lob_assignment": "GBM", "lob_updated_at": "2025-06-24T11:37:26.151536", "lob_updated_by": "Jane Doe", "version_number": 1, "submitted_by_id": 3, "tester_decision": "include", "generation_method": "LLM Generated", "primary_key_value": "4538291076999", "tester_decision_at": "2025-06-24T11:37:20.589118", "tester_decision_by": "Jane Doe", "generated_by_user_id": 3, "report_owner_decision": "approved", "report_owner_feedback": null, "tester_decision_by_id": 3, "report_owner_reviewed_at": "2025-06-24T11:40:20.432685", "report_owner_reviewed_by": "Mike Johnson"}]}], "last_updated": "2025-06-24T11:37:30.923384"}');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, planned_start_date, planned_end_date, actual_start_date, created_at, updated_at, state, schedule_status, started_by, completed_by, notes) VALUES (52, 21, 156, 'Data Provider ID', 'Complete', 2025-07-09, 2025-07-12, '2025-06-24T17:36:49.275861+00:00', '2025-06-22T23:34:32.984452+00:00', '2025-06-24T14:41:29.057022+00:00', 'In Progress', 'On Track', 3, 3, 'Final test with proper workflow orchestrator state transition');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, planned_start_date, planned_end_date, actual_start_date, actual_end_date, created_at, updated_at, state, schedule_status, completed_by, notes) VALUES (53, 21, 156, 'Request Info', 'In Progress', 2025-07-13, 2025-07-17, '2025-06-24T19:00:00+00:00', '2025-06-24T23:59:01.522050+00:00', '2025-06-22T23:34:32.984467+00:00', '2025-06-24T19:59:01.489620+00:00', 'Complete', 'On Track', 3, 'All test cases have been submitted successfully');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, planned_start_date, planned_end_date, created_at, updated_at, state, schedule_status) VALUES (55, 21, 156, 'Observations', 'Complete', 2025-07-28, 2025-08-01, '2025-06-22T23:34:32.984494+00:00', '2025-06-25T02:50:45.597880+00:00', 'Complete', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (57, 21, 160, 'Sample Selection', 'Not Started', '2025-06-22T21:53:56.651682+00:00', '2025-06-22T21:53:56.651682+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (58, 21, 160, 'Data Provider ID', 'Not Started', '2025-06-22T21:53:56.651682+00:00', '2025-06-22T21:53:56.651682+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (59, 21, 160, 'Request Info', 'Not Started', '2025-06-22T21:53:56.651682+00:00', '2025-06-22T21:53:56.651682+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (61, 21, 160, 'Observations', 'Not Started', '2025-06-22T21:53:56.651682+00:00', '2025-06-22T21:53:56.651682+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (62, 21, 160, 'Testing', 'Not Started', '2025-06-22T21:53:56.651682+00:00', '2025-06-22T21:53:56.651682+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (63, 21, 160, 'Planning', 'Not Started', '2025-06-22T21:53:56.651682+00:00', '2025-06-22T21:53:56.651682+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (64, 21, 160, 'Scoping', 'Not Started', '2025-06-22T21:53:56.651682+00:00', '2025-06-22T21:53:56.651682+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (65, 21, 160, 'Data Profiling', 'Not Started', '2025-06-22T21:53:56.651682+00:00', '2025-06-22T21:53:56.651682+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (75, 29, 156, 'Planning', 'Not Started', '2025-06-24T09:07:23.474935+00:00', '2025-06-24T09:07:23.474937+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (76, 29, 156, 'Data Profiling', 'Not Started', '2025-06-24T09:07:23.475051+00:00', '2025-06-24T09:07:23.475052+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (77, 29, 156, 'Scoping', 'Not Started', '2025-06-24T09:07:23.475070+00:00', '2025-06-24T09:07:23.475071+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (78, 29, 156, 'Sample Selection', 'Not Started', '2025-06-24T09:07:23.475085+00:00', '2025-06-24T09:07:23.475086+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (79, 29, 156, 'Data Provider ID', 'Not Started', '2025-06-24T09:07:23.475099+00:00', '2025-06-24T09:07:23.475100+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (80, 29, 156, 'Request Info', 'Not Started', '2025-06-24T09:07:23.475113+00:00', '2025-06-24T09:07:23.475114+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (82, 29, 156, 'Observations', 'Not Started', '2025-06-24T09:07:23.475140+00:00', '2025-06-24T09:07:23.475141+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (83, 29, 156, 'Testing', 'Not Started', '2025-06-24T09:07:23.475153+00:00', '2025-06-24T09:07:23.475154+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (93, 30, 156, 'Planning', 'Not Started', '2025-06-24T09:07:40.825480+00:00', '2025-06-24T09:07:40.825481+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (94, 30, 156, 'Data Profiling', 'Not Started', '2025-06-24T09:07:40.825536+00:00', '2025-06-24T09:07:40.825537+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (95, 30, 156, 'Scoping', 'Not Started', '2025-06-24T09:07:40.825554+00:00', '2025-06-24T09:07:40.825556+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (96, 30, 156, 'Sample Selection', 'Not Started', '2025-06-24T09:07:40.825569+00:00', '2025-06-24T09:07:40.825570+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (97, 30, 156, 'Data Provider ID', 'Not Started', '2025-06-24T09:07:40.825581+00:00', '2025-06-24T09:07:40.825582+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (98, 30, 156, 'Request Info', 'Not Started', '2025-06-24T09:07:40.825593+00:00', '2025-06-24T09:07:40.825594+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (100, 30, 156, 'Observations', 'Not Started', '2025-06-24T09:07:40.825617+00:00', '2025-06-24T09:07:40.825618+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (101, 30, 156, 'Testing', 'Not Started', '2025-06-24T09:07:40.825628+00:00', '2025-06-24T09:07:40.825629+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (111, 31, 156, 'Planning', 'Not Started', '2025-06-24T09:08:11.955172+00:00', '2025-06-24T09:08:11.955174+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (112, 31, 156, 'Data Profiling', 'Not Started', '2025-06-24T09:08:11.955335+00:00', '2025-06-24T09:08:11.955341+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (113, 31, 156, 'Scoping', 'Not Started', '2025-06-24T09:08:11.955426+00:00', '2025-06-24T09:08:11.955431+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (114, 31, 156, 'Sample Selection', 'Not Started', '2025-06-24T09:08:11.955506+00:00', '2025-06-24T09:08:11.955512+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (115, 31, 156, 'Data Provider ID', 'Not Started', '2025-06-24T09:08:11.955584+00:00', '2025-06-24T09:08:11.955590+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (116, 31, 156, 'Request Info', 'Not Started', '2025-06-24T09:08:11.955677+00:00', '2025-06-24T09:08:11.955682+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (118, 31, 156, 'Observations', 'Not Started', '2025-06-24T09:08:11.955830+00:00', '2025-06-24T09:08:11.955836+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (119, 31, 156, 'Testing', 'Not Started', '2025-06-24T09:08:11.955910+00:00', '2025-06-24T09:08:11.955916+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (129, 32, 156, 'Planning', 'Not Started', '2025-06-24T15:05:07.361249+00:00', '2025-06-24T15:05:07.361250+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (130, 32, 156, 'Data Profiling', 'Not Started', '2025-06-24T15:05:07.361304+00:00', '2025-06-24T15:05:07.361305+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (131, 32, 156, 'Scoping', 'Not Started', '2025-06-24T15:05:07.361322+00:00', '2025-06-24T15:05:07.361324+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (132, 32, 156, 'Sample Selection', 'Not Started', '2025-06-24T15:05:07.361337+00:00', '2025-06-24T15:05:07.361338+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (133, 32, 156, 'Data Provider ID', 'Not Started', '2025-06-24T15:05:07.361352+00:00', '2025-06-24T15:05:07.361353+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (134, 32, 156, 'Request Info', 'Not Started', '2025-06-24T15:05:07.361366+00:00', '2025-06-24T15:05:07.361367+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (136, 32, 156, 'Observations', 'Not Started', '2025-06-24T15:05:07.361395+00:00', '2025-06-24T15:05:07.361396+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (137, 32, 156, 'Testing', 'Not Started', '2025-06-24T15:05:07.361408+00:00', '2025-06-24T15:05:07.361409+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (147, 33, 156, 'Planning', 'Not Started', '2025-06-24T15:05:26.548657+00:00', '2025-06-24T15:05:26.548662+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (148, 33, 156, 'Data Profiling', 'Not Started', '2025-06-24T15:05:26.548840+00:00', '2025-06-24T15:05:26.548844+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (149, 33, 156, 'Scoping', 'Not Started', '2025-06-24T15:05:26.548909+00:00', '2025-06-24T15:05:26.548913+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (150, 33, 156, 'Sample Selection', 'Not Started', '2025-06-24T15:05:26.548969+00:00', '2025-06-24T15:05:26.548973+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (151, 33, 156, 'Data Provider ID', 'Not Started', '2025-06-24T15:05:26.549030+00:00', '2025-06-24T15:05:26.549034+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (152, 33, 156, 'Request Info', 'Not Started', '2025-06-24T15:05:26.549087+00:00', '2025-06-24T15:05:26.549091+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (154, 33, 156, 'Observations', 'Not Started', '2025-06-24T15:05:26.549168+00:00', '2025-06-24T15:05:26.549171+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (155, 33, 156, 'Testing', 'Not Started', '2025-06-24T15:05:26.549206+00:00', '2025-06-24T15:05:26.549209+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (165, 34, 156, 'Planning', 'Not Started', '2025-06-24T15:05:48.676254+00:00', '2025-06-24T15:05:48.676257+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (166, 34, 156, 'Data Profiling', 'Not Started', '2025-06-24T15:05:48.676349+00:00', '2025-06-24T15:05:48.676351+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (167, 34, 156, 'Scoping', 'Not Started', '2025-06-24T15:05:48.676386+00:00', '2025-06-24T15:05:48.676389+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (168, 34, 156, 'Sample Selection', 'Not Started', '2025-06-24T15:05:48.676418+00:00', '2025-06-24T15:05:48.676421+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (169, 34, 156, 'Data Provider ID', 'Not Started', '2025-06-24T15:05:48.676514+00:00', '2025-06-24T15:05:48.676516+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (170, 34, 156, 'Request Info', 'Not Started', '2025-06-24T15:05:48.676549+00:00', '2025-06-24T15:05:48.676552+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (172, 34, 156, 'Observations', 'Not Started', '2025-06-24T15:05:48.676618+00:00', '2025-06-24T15:05:48.676620+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (173, 34, 156, 'Testing', 'Not Started', '2025-06-24T15:05:48.676651+00:00', '2025-06-24T15:05:48.676654+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (183, 35, 156, 'Planning', 'Not Started', '2025-06-24T15:06:29.053801+00:00', '2025-06-24T15:06:29.053803+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (184, 35, 156, 'Data Profiling', 'Not Started', '2025-06-24T15:06:29.053902+00:00', '2025-06-24T15:06:29.053904+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (185, 35, 156, 'Scoping', 'Not Started', '2025-06-24T15:06:29.053938+00:00', '2025-06-24T15:06:29.053940+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (186, 35, 156, 'Sample Selection', 'Not Started', '2025-06-24T15:06:29.053969+00:00', '2025-06-24T15:06:29.053971+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (187, 35, 156, 'Data Provider ID', 'Not Started', '2025-06-24T15:06:29.054000+00:00', '2025-06-24T15:06:29.054002+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (188, 35, 156, 'Request Info', 'Not Started', '2025-06-24T15:06:29.054029+00:00', '2025-06-24T15:06:29.054032+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (190, 35, 156, 'Observations', 'Not Started', '2025-06-24T15:06:29.054090+00:00', '2025-06-24T15:06:29.054092+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (191, 35, 156, 'Testing', 'Not Started', '2025-06-24T15:06:29.054120+00:00', '2025-06-24T15:06:29.054122+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (201, 36, 156, 'Planning', 'Not Started', '2025-06-24T15:07:48.604819+00:00', '2025-06-24T15:07:48.604820+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (202, 36, 156, 'Data Profiling', 'Not Started', '2025-06-24T15:07:48.604869+00:00', '2025-06-24T15:07:48.604870+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (203, 36, 156, 'Scoping', 'Not Started', '2025-06-24T15:07:48.604887+00:00', '2025-06-24T15:07:48.604888+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (204, 36, 156, 'Sample Selection', 'Not Started', '2025-06-24T15:07:48.604901+00:00', '2025-06-24T15:07:48.604902+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (205, 36, 156, 'Data Provider ID', 'Not Started', '2025-06-24T15:07:48.604914+00:00', '2025-06-24T15:07:48.604915+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (206, 36, 156, 'Request Info', 'Not Started', '2025-06-24T15:07:48.604927+00:00', '2025-06-24T15:07:48.604928+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (208, 36, 156, 'Observations', 'Not Started', '2025-06-24T15:07:48.604954+00:00', '2025-06-24T15:07:48.604955+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (209, 36, 156, 'Testing', 'Not Started', '2025-06-24T15:07:48.604966+00:00', '2025-06-24T15:07:48.604967+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (219, 37, 156, 'Planning', 'Not Started', '2025-06-24T15:08:26.951681+00:00', '2025-06-24T15:08:26.951683+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (220, 37, 156, 'Data Profiling', 'Not Started', '2025-06-24T15:08:26.951747+00:00', '2025-06-24T15:08:26.951749+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (221, 37, 156, 'Scoping', 'Not Started', '2025-06-24T15:08:26.951766+00:00', '2025-06-24T15:08:26.951767+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (222, 37, 156, 'Sample Selection', 'Not Started', '2025-06-24T15:08:26.951782+00:00', '2025-06-24T15:08:26.951783+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (223, 37, 156, 'Data Provider ID', 'Not Started', '2025-06-24T15:08:26.951798+00:00', '2025-06-24T15:08:26.951800+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (224, 37, 156, 'Request Info', 'Not Started', '2025-06-24T15:08:26.951813+00:00', '2025-06-24T15:08:26.951814+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (226, 37, 156, 'Observations', 'Not Started', '2025-06-24T15:08:26.951839+00:00', '2025-06-24T15:08:26.951840+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (227, 37, 156, 'Testing', 'Not Started', '2025-06-24T15:08:26.951852+00:00', '2025-06-24T15:08:26.951853+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (237, 38, 156, 'Planning', 'Not Started', '2025-06-24T15:09:02.005464+00:00', '2025-06-24T15:09:02.005466+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (238, 38, 156, 'Data Profiling', 'Not Started', '2025-06-24T15:09:02.005517+00:00', '2025-06-24T15:09:02.005518+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (239, 38, 156, 'Scoping', 'Not Started', '2025-06-24T15:09:02.005535+00:00', '2025-06-24T15:09:02.005536+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (240, 38, 156, 'Sample Selection', 'Not Started', '2025-06-24T15:09:02.005548+00:00', '2025-06-24T15:09:02.005549+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (241, 38, 156, 'Data Provider ID', 'Not Started', '2025-06-24T15:09:02.005560+00:00', '2025-06-24T15:09:02.005561+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (242, 38, 156, 'Request Info', 'Not Started', '2025-06-24T15:09:02.005573+00:00', '2025-06-24T15:09:02.005573+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (244, 38, 156, 'Observations', 'Not Started', '2025-06-24T15:09:02.005596+00:00', '2025-06-24T15:09:02.005597+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (245, 38, 156, 'Testing', 'Not Started', '2025-06-24T15:09:02.005607+00:00', '2025-06-24T15:09:02.005608+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (255, 39, 156, 'Planning', 'Not Started', '2025-06-24T15:17:13.312066+00:00', '2025-06-24T15:17:13.312067+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (256, 39, 156, 'Data Profiling', 'Not Started', '2025-06-24T15:17:13.312128+00:00', '2025-06-24T15:17:13.312129+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (257, 39, 156, 'Scoping', 'Not Started', '2025-06-24T15:17:13.312145+00:00', '2025-06-24T15:17:13.312146+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (258, 39, 156, 'Sample Selection', 'Not Started', '2025-06-24T15:17:13.312158+00:00', '2025-06-24T15:17:13.312159+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (259, 39, 156, 'Data Provider ID', 'Not Started', '2025-06-24T15:17:13.312171+00:00', '2025-06-24T15:17:13.312172+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (260, 39, 156, 'Request Info', 'Not Started', '2025-06-24T15:17:13.312183+00:00', '2025-06-24T15:17:13.312184+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (262, 39, 156, 'Observations', 'Not Started', '2025-06-24T15:17:13.312207+00:00', '2025-06-24T15:17:13.312208+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (263, 39, 156, 'Testing', 'Not Started', '2025-06-24T15:17:13.312219+00:00', '2025-06-24T15:17:13.312220+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (273, 40, 156, 'Planning', 'Not Started', '2025-06-24T15:17:40.446712+00:00', '2025-06-24T15:17:40.446714+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (274, 40, 156, 'Data Profiling', 'Not Started', '2025-06-24T15:17:40.446762+00:00', '2025-06-24T15:17:40.446763+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (275, 40, 156, 'Scoping', 'Not Started', '2025-06-24T15:17:40.446778+00:00', '2025-06-24T15:17:40.446779+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (276, 40, 156, 'Sample Selection', 'Not Started', '2025-06-24T15:17:40.446791+00:00', '2025-06-24T15:17:40.446792+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (277, 40, 156, 'Data Provider ID', 'Not Started', '2025-06-24T15:17:40.446803+00:00', '2025-06-24T15:17:40.446804+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (278, 40, 156, 'Request Info', 'Not Started', '2025-06-24T15:17:40.446815+00:00', '2025-06-24T15:17:40.446816+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (280, 40, 156, 'Observations', 'Not Started', '2025-06-24T15:17:40.446838+00:00', '2025-06-24T15:17:40.446839+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (281, 40, 156, 'Testing', 'Not Started', '2025-06-24T15:17:40.446850+00:00', '2025-06-24T15:17:40.446851+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (291, 41, 156, 'Planning', 'Not Started', '2025-06-24T15:18:26.422440+00:00', '2025-06-24T15:18:26.422442+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (292, 41, 156, 'Data Profiling', 'Not Started', '2025-06-24T15:18:26.422539+00:00', '2025-06-24T15:18:26.422542+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (293, 41, 156, 'Scoping', 'Not Started', '2025-06-24T15:18:26.422578+00:00', '2025-06-24T15:18:26.422581+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (294, 41, 156, 'Sample Selection', 'Not Started', '2025-06-24T15:18:26.422613+00:00', '2025-06-24T15:18:26.422616+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (295, 41, 156, 'Data Provider ID', 'Not Started', '2025-06-24T15:18:26.422647+00:00', '2025-06-24T15:18:26.422649+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (296, 41, 156, 'Request Info', 'Not Started', '2025-06-24T15:18:26.422680+00:00', '2025-06-24T15:18:26.422683+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (298, 41, 156, 'Observations', 'Not Started', '2025-06-24T15:18:26.422746+00:00', '2025-06-24T15:18:26.422749+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (299, 41, 156, 'Testing', 'Not Started', '2025-06-24T15:18:26.422779+00:00', '2025-06-24T15:18:26.422781+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (309, 42, 156, 'Planning', 'Not Started', '2025-06-24T15:23:10.288111+00:00', '2025-06-24T15:23:10.288113+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (310, 42, 156, 'Data Profiling', 'Not Started', '2025-06-24T15:23:10.288202+00:00', '2025-06-24T15:23:10.288205+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (311, 42, 156, 'Scoping', 'Not Started', '2025-06-24T15:23:10.288238+00:00', '2025-06-24T15:23:10.288241+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (312, 42, 156, 'Sample Selection', 'Not Started', '2025-06-24T15:23:10.288271+00:00', '2025-06-24T15:23:10.288273+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (313, 42, 156, 'Data Provider ID', 'Not Started', '2025-06-24T15:23:10.288301+00:00', '2025-06-24T15:23:10.288304+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (314, 42, 156, 'Request Info', 'Not Started', '2025-06-24T15:23:10.288332+00:00', '2025-06-24T15:23:10.288334+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (316, 42, 156, 'Observations', 'Not Started', '2025-06-24T15:23:10.288393+00:00', '2025-06-24T15:23:10.288395+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (317, 42, 156, 'Testing', 'Not Started', '2025-06-24T15:23:10.288423+00:00', '2025-06-24T15:23:10.288425+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (327, 43, 156, 'Planning', 'Not Started', '2025-06-24T15:24:06.298931+00:00', '2025-06-24T15:24:06.298934+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (328, 43, 156, 'Data Profiling', 'Not Started', '2025-06-24T15:24:06.299066+00:00', '2025-06-24T15:24:06.299068+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (329, 43, 156, 'Scoping', 'Not Started', '2025-06-24T15:24:06.299102+00:00', '2025-06-24T15:24:06.299105+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (330, 43, 156, 'Sample Selection', 'Not Started', '2025-06-24T15:24:06.299134+00:00', '2025-06-24T15:24:06.299137+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (331, 43, 156, 'Data Provider ID', 'Not Started', '2025-06-24T15:24:06.299165+00:00', '2025-06-24T15:24:06.299167+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (332, 43, 156, 'Request Info', 'Not Started', '2025-06-24T15:24:06.299195+00:00', '2025-06-24T15:24:06.299198+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (334, 43, 156, 'Observations', 'Not Started', '2025-06-24T15:24:06.299257+00:00', '2025-06-24T15:24:06.299259+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (335, 43, 156, 'Testing', 'Not Started', '2025-06-24T15:24:06.299286+00:00', '2025-06-24T15:24:06.299288+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (345, 44, 156, 'Planning', 'Not Started', '2025-06-24T15:24:36.080251+00:00', '2025-06-24T15:24:36.080254+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (346, 44, 156, 'Data Profiling', 'Not Started', '2025-06-24T15:24:36.080358+00:00', '2025-06-24T15:24:36.080362+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (347, 44, 156, 'Scoping', 'Not Started', '2025-06-24T15:24:36.080401+00:00', '2025-06-24T15:24:36.080403+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (348, 44, 156, 'Sample Selection', 'Not Started', '2025-06-24T15:24:36.080467+00:00', '2025-06-24T15:24:36.080471+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (349, 44, 156, 'Data Provider ID', 'Not Started', '2025-06-24T15:24:36.080514+00:00', '2025-06-24T15:24:36.080517+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (350, 44, 156, 'Request Info', 'Not Started', '2025-06-24T15:24:36.080549+00:00', '2025-06-24T15:24:36.080551+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (352, 44, 156, 'Observations', 'Not Started', '2025-06-24T15:24:36.080612+00:00', '2025-06-24T15:24:36.080615+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (353, 44, 156, 'Testing', 'Not Started', '2025-06-24T15:24:36.080671+00:00', '2025-06-24T15:24:36.080674+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (363, 45, 156, 'Planning', 'Not Started', '2025-06-24T15:25:30.999804+00:00', '2025-06-24T15:25:30.999807+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (364, 45, 156, 'Data Profiling', 'Not Started', '2025-06-24T15:25:30.999898+00:00', '2025-06-24T15:25:30.999901+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (365, 45, 156, 'Scoping', 'Not Started', '2025-06-24T15:25:30.999938+00:00', '2025-06-24T15:25:30.999941+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (366, 45, 156, 'Sample Selection', 'Not Started', '2025-06-24T15:25:30.999972+00:00', '2025-06-24T15:25:30.999974+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (367, 45, 156, 'Data Provider ID', 'Not Started', '2025-06-24T15:25:31.000004+00:00', '2025-06-24T15:25:31.000006+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (368, 45, 156, 'Request Info', 'Not Started', '2025-06-24T15:25:31.000035+00:00', '2025-06-24T15:25:31.000037+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (370, 45, 156, 'Observations', 'Not Started', '2025-06-24T15:25:31.000097+00:00', '2025-06-24T15:25:31.000100+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (371, 45, 156, 'Testing', 'Not Started', '2025-06-24T15:25:31.000128+00:00', '2025-06-24T15:25:31.000130+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (381, 46, 156, 'Planning', 'Not Started', '2025-06-24T15:25:51.531826+00:00', '2025-06-24T15:25:51.531829+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (382, 46, 156, 'Data Profiling', 'Not Started', '2025-06-24T15:25:51.531941+00:00', '2025-06-24T15:25:51.531944+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (383, 46, 156, 'Scoping', 'Not Started', '2025-06-24T15:25:51.531985+00:00', '2025-06-24T15:25:51.531988+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (384, 46, 156, 'Sample Selection', 'Not Started', '2025-06-24T15:25:51.532024+00:00', '2025-06-24T15:25:51.532027+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (385, 46, 156, 'Data Provider ID', 'Not Started', '2025-06-24T15:25:51.532062+00:00', '2025-06-24T15:25:51.532065+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (386, 46, 156, 'Request Info', 'Not Started', '2025-06-24T15:25:51.532099+00:00', '2025-06-24T15:25:51.532101+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (388, 46, 156, 'Observations', 'Not Started', '2025-06-24T15:25:51.532173+00:00', '2025-06-24T15:25:51.532176+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (389, 46, 156, 'Testing', 'Not Started', '2025-06-24T15:25:51.532210+00:00', '2025-06-24T15:25:51.532212+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, actual_end_date, created_at, updated_at, state, schedule_status, started_by, phase_data) VALUES (390, 21, 156, 'Test Execution', 'Complete', '2025-06-25T06:57:44.913067+00:00', '2025-06-24T19:21:55.724299+00:00', '2025-06-25T06:57:44.914637+00:00', 'In Progress', 'On Track', 1, '{"pass_rate": 0, "total_tests": 0, "completed_by": 3, "tests_failed": 0, "tests_passed": 0}');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, actual_start_date, created_at, updated_at, state, schedule_status, started_by, notes) VALUES (391, 21, 156, 'Finalize Test Report', 'Not Started', '2025-06-25T18:27:07.060773+00:00', '2025-06-25T01:50:41.750785+00:00', '2025-06-25T14:27:07.046567+00:00', 'In Progress', 'On Track', 255, 'Test report phase started');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (392, 21, 160, 'Finalize Test Report', 'Not Started', '2025-06-25T01:50:41.750785+00:00', '2025-06-25T01:50:41.750785+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (393, 29, 156, 'Finalize Test Report', 'Not Started', '2025-06-25T01:50:41.750785+00:00', '2025-06-25T01:50:41.750785+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (394, 30, 156, 'Finalize Test Report', 'Not Started', '2025-06-25T01:50:41.750785+00:00', '2025-06-25T01:50:41.750785+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (395, 31, 156, 'Finalize Test Report', 'Not Started', '2025-06-25T01:50:41.750785+00:00', '2025-06-25T01:50:41.750785+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (396, 32, 156, 'Finalize Test Report', 'Not Started', '2025-06-25T01:50:41.750785+00:00', '2025-06-25T01:50:41.750785+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (397, 33, 156, 'Finalize Test Report', 'Not Started', '2025-06-25T01:50:41.750785+00:00', '2025-06-25T01:50:41.750785+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (398, 34, 156, 'Finalize Test Report', 'Not Started', '2025-06-25T01:50:41.750785+00:00', '2025-06-25T01:50:41.750785+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (399, 35, 156, 'Finalize Test Report', 'Not Started', '2025-06-25T01:50:41.750785+00:00', '2025-06-25T01:50:41.750785+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (400, 36, 156, 'Finalize Test Report', 'Not Started', '2025-06-25T01:50:41.750785+00:00', '2025-06-25T01:50:41.750785+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (401, 37, 156, 'Finalize Test Report', 'Not Started', '2025-06-25T01:50:41.750785+00:00', '2025-06-25T01:50:41.750785+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (402, 38, 156, 'Finalize Test Report', 'Not Started', '2025-06-25T01:50:41.750785+00:00', '2025-06-25T01:50:41.750785+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (403, 39, 156, 'Finalize Test Report', 'Not Started', '2025-06-25T01:50:41.750785+00:00', '2025-06-25T01:50:41.750785+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (404, 40, 156, 'Finalize Test Report', 'Not Started', '2025-06-25T01:50:41.750785+00:00', '2025-06-25T01:50:41.750785+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (405, 41, 156, 'Finalize Test Report', 'Not Started', '2025-06-25T01:50:41.750785+00:00', '2025-06-25T01:50:41.750785+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (406, 42, 156, 'Finalize Test Report', 'Not Started', '2025-06-25T01:50:41.750785+00:00', '2025-06-25T01:50:41.750785+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (407, 43, 156, 'Finalize Test Report', 'Not Started', '2025-06-25T01:50:41.750785+00:00', '2025-06-25T01:50:41.750785+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (408, 44, 156, 'Finalize Test Report', 'Not Started', '2025-06-25T01:50:41.750785+00:00', '2025-06-25T01:50:41.750785+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (409, 45, 156, 'Finalize Test Report', 'Not Started', '2025-06-25T01:50:41.750785+00:00', '2025-06-25T01:50:41.750785+00:00', 'Not Started', 'On Track');
INSERT INTO workflow_phases (phase_id, cycle_id, report_id, phase_name, status, created_at, updated_at, state, schedule_status) VALUES (410, 46, 156, 'Finalize Test Report', 'Not Started', '2025-06-25T01:50:41.750785+00:00', '2025-06-25T01:50:41.750785+00:00', 'Not Started', 'On Track');

-- Reset sequences
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'attribute_lob_assignments_assignment_id_seq') THEN
        PERFORM setval('attribute_lob_assignments_assignment_id_seq', COALESCE((SELECT MAX(assignment_id) FROM attribute_lob_assignments), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'attribute_profiling_scores_score_id_seq') THEN
        PERFORM setval('attribute_profiling_scores_score_id_seq', COALESCE((SELECT MAX(score_id) FROM cycle_report_data_profiling_attribute_scores), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'attribute_scoping_recommendations_recommendation_id_seq') THEN
        PERFORM setval('attribute_scoping_recommendations_recommendation_id_seq', COALESCE((SELECT MAX(recommendation_id) FROM cycle_report_scoping_attribute_recommendations), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'attribute_version_change_logs_log_id_seq') THEN
        PERFORM setval('attribute_version_change_logs_log_id_seq', COALESCE((SELECT MAX(log_id) FROM attribute_version_change_logs), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'attribute_version_comparisons_comparison_id_seq') THEN
        PERFORM setval('attribute_version_comparisons_comparison_id_seq', COALESCE((SELECT MAX(comparison_id) FROM attribute_version_comparisons), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'audit_log_audit_id_seq') THEN
        PERFORM setval('audit_log_audit_id_seq', COALESCE((SELECT MAX(audit_id) FROM audit_log), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'bulk_test_executions_bulk_execution_id_seq') THEN
        PERFORM setval('bulk_test_executions_bulk_execution_id_seq', COALESCE((SELECT MAX(bulk_execution_id) FROM bulk_test_executions), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'cdo_notifications_notification_id_seq') THEN
        PERFORM setval('cdo_notifications_notification_id_seq', COALESCE((SELECT MAX(notification_id) FROM cdo_notifications), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'data_owner_assignments_assignment_id_seq') THEN
        PERFORM setval('data_owner_assignments_assignment_id_seq', COALESCE((SELECT MAX(assignment_id) FROM data_owner_assignments), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'data_owner_escalation_log_email_id_seq') THEN
        PERFORM setval('data_owner_escalation_log_email_id_seq', COALESCE((SELECT MAX(email_id) FROM data_owner_escalation_log), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'data_owner_phase_audit_log_audit_id_seq') THEN
        PERFORM setval('data_owner_phase_audit_log_audit_id_seq', COALESCE((SELECT MAX(audit_id) FROM data_owner_phase_audit_log), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'data_owner_sla_violations_violation_id_seq') THEN
        PERFORM setval('data_owner_sla_violations_violation_id_seq', COALESCE((SELECT MAX(violation_id) FROM data_owner_sla_violations), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'data_profiling_files_file_id_seq') THEN
        PERFORM setval('data_profiling_files_file_id_seq', COALESCE((SELECT MAX(file_id) FROM cycle_report_data_profiling_files), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'data_profiling_phases_phase_id_seq') THEN
        PERFORM setval('data_profiling_phases_phase_id_seq', COALESCE((SELECT MAX(phase_id) FROM data_profiling_phases), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'data_provider_assignments_assignment_id_seq') THEN
        PERFORM setval('data_provider_assignments_assignment_id_seq', COALESCE((SELECT MAX(assignment_id) FROM data_provider_assignments), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'data_provider_escalation_log_email_id_seq') THEN
        PERFORM setval('data_provider_escalation_log_email_id_seq', COALESCE((SELECT MAX(email_id) FROM data_provider_escalation_log), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'data_provider_phase_audit_log_audit_id_seq') THEN
        PERFORM setval('data_provider_phase_audit_log_audit_id_seq', COALESCE((SELECT MAX(audit_id) FROM data_provider_phase_audit_log), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'data_provider_sla_violations_violation_id_seq') THEN
        PERFORM setval('data_provider_sla_violations_violation_id_seq', COALESCE((SELECT MAX(violation_id) FROM data_provider_sla_violations), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'data_provider_submissions_submission_id_seq') THEN
        PERFORM setval('data_provider_submissions_submission_id_seq', COALESCE((SELECT MAX(submission_id) FROM data_provider_submissions), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'data_sources_data_source_id_seq') THEN
        PERFORM setval('data_sources_data_source_id_seq', COALESCE((SELECT MAX(data_source_id) FROM data_sources), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'database_tests_test_id_seq') THEN
        PERFORM setval('database_tests_test_id_seq', COALESCE((SELECT MAX(test_id) FROM cycle_report_test_execution_database_tests), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'document_access_logs_log_id_seq') THEN
        PERFORM setval('document_access_logs_log_id_seq', COALESCE((SELECT MAX(log_id) FROM document_access_logs), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'document_analyses_analysis_id_seq') THEN
        PERFORM setval('document_analyses_analysis_id_seq', COALESCE((SELECT MAX(analysis_id) FROM cycle_report_test_execution_document_analyses), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'document_extractions_extraction_id_seq') THEN
        PERFORM setval('document_extractions_extraction_id_seq', COALESCE((SELECT MAX(extraction_id) FROM document_extractions), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'document_revisions_revision_id_seq') THEN
        PERFORM setval('document_revisions_revision_id_seq', COALESCE((SELECT MAX(revision_id) FROM document_revisions), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'documents_document_id_seq') THEN
        PERFORM setval('documents_document_id_seq', COALESCE((SELECT MAX(document_id) FROM documents), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'escalation_email_logs_log_id_seq') THEN
        PERFORM setval('escalation_email_logs_log_id_seq', COALESCE((SELECT MAX(log_id) FROM escalation_email_logs), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'historical_data_owner_assignments_history_id_seq') THEN
        PERFORM setval('historical_data_owner_assignments_history_id_seq', COALESCE((SELECT MAX(history_id) FROM historical_data_owner_assignments), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'historical_data_provider_assignments_history_id_seq') THEN
        PERFORM setval('historical_data_provider_assignments_history_id_seq', COALESCE((SELECT MAX(history_id) FROM historical_data_provider_assignments), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'individual_samples_id_seq') THEN
        PERFORM setval('individual_samples_id_seq', COALESCE((SELECT MAX(id) FROM individual_samples), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'llm_audit_log_log_id_seq') THEN
        PERFORM setval('llm_audit_log_log_id_seq', COALESCE((SELECT MAX(log_id) FROM llm_audit_log), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'lobs_lob_id_seq') THEN
        PERFORM setval('lobs_lob_id_seq', COALESCE((SELECT MAX(lob_id) FROM lobs), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'observation_approvals_approval_id_seq') THEN
        PERFORM setval('observation_approvals_approval_id_seq', COALESCE((SELECT MAX(approval_id) FROM cycle_report_observation_mgmt_approvals), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'observation_clarifications_clarification_id_seq') THEN
        PERFORM setval('observation_clarifications_clarification_id_seq', COALESCE((SELECT MAX(clarification_id) FROM observation_clarifications), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'observation_groups_group_id_seq') THEN
        PERFORM setval('observation_groups_group_id_seq', COALESCE((SELECT MAX(group_id) FROM observation_groups), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'observation_impact_assessments_assessment_id_seq') THEN
        PERFORM setval('observation_impact_assessments_assessment_id_seq', COALESCE((SELECT MAX(assessment_id) FROM cycle_report_observation_mgmt_impact_assessments), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'observation_management_audit_logs_log_id_seq') THEN
        PERFORM setval('observation_management_audit_logs_log_id_seq', COALESCE((SELECT MAX(log_id) FROM cycle_report_observation_mgmt_audit_logss), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'observation_records_observation_id_seq') THEN
        PERFORM setval('observation_records_observation_id_seq', COALESCE((SELECT MAX(observation_id) FROM cycle_report_observation_mgmt_observation_records), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'observation_resolutions_resolution_id_seq') THEN
        PERFORM setval('observation_resolutions_resolution_id_seq', COALESCE((SELECT MAX(resolution_id) FROM cycle_report_observation_mgmt_resolutions), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'observations_observation_id_seq') THEN
        PERFORM setval('observations_observation_id_seq', COALESCE((SELECT MAX(observation_id) FROM observations), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'permission_audit_log_audit_id_seq') THEN
        PERFORM setval('permission_audit_log_audit_id_seq', COALESCE((SELECT MAX(audit_id) FROM permission_audit_log), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'permissions_permission_id_seq') THEN
        PERFORM setval('permissions_permission_id_seq', COALESCE((SELECT MAX(permission_id) FROM permissions), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'profiling_results_result_id_seq') THEN
        PERFORM setval('profiling_results_result_id_seq', COALESCE((SELECT MAX(result_id) FROM cycle_report_data_profiling_results), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'profiling_rules_rule_id_seq') THEN
        PERFORM setval('profiling_rules_rule_id_seq', COALESCE((SELECT MAX(rule_id) FROM cycle_report_data_profiling_rules), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'regulatory_data_dictionary_dict_id_seq') THEN
        PERFORM setval('regulatory_data_dictionary_dict_id_seq', COALESCE((SELECT MAX(dict_id) FROM regulatory_data_dictionary), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'report_attributes_attribute_id_seq') THEN
        PERFORM setval('report_attributes_attribute_id_seq', COALESCE((SELECT MAX(attribute_id) FROM report_attributes), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'report_owner_assignment_history_history_id_seq') THEN
        PERFORM setval('report_owner_assignment_history_history_id_seq', COALESCE((SELECT MAX(history_id) FROM report_owner_assignment_history), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'report_owner_assignments_assignment_id_seq') THEN
        PERFORM setval('report_owner_assignments_assignment_id_seq', COALESCE((SELECT MAX(assignment_id) FROM report_owner_assignments), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'report_owner_scoping_reviews_review_id_seq') THEN
        PERFORM setval('report_owner_scoping_reviews_review_id_seq', COALESCE((SELECT MAX(review_id) FROM cycle_report_scoping_report_owner_reviews), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'reports_report_id_seq') THEN
        PERFORM setval('reports_report_id_seq', COALESCE((SELECT MAX(report_id) FROM reports), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'request_info_audit_logs_log_id_seq') THEN
        PERFORM setval('request_info_audit_logs_log_id_seq', COALESCE((SELECT MAX(log_id) FROM cycle_report_request_info_audit_logs), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'resource_permissions_resource_permission_id_seq') THEN
        PERFORM setval('resource_permissions_resource_permission_id_seq', COALESCE((SELECT MAX(resource_permission_id) FROM resource_permissions), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'resources_resource_id_seq') THEN
        PERFORM setval('resources_resource_id_seq', COALESCE((SELECT MAX(resource_id) FROM resources), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'roles_role_id_seq') THEN
        PERFORM setval('roles_role_id_seq', COALESCE((SELECT MAX(role_id) FROM roles), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'sample_audit_logs_id_seq') THEN
        PERFORM setval('sample_audit_logs_id_seq', COALESCE((SELECT MAX(id) FROM sample_audit_logs), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'sample_feedback_id_seq') THEN
        PERFORM setval('sample_feedback_id_seq', COALESCE((SELECT MAX(id) FROM sample_feedback), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'sample_selection_phases_phase_id_seq') THEN
        PERFORM setval('sample_selection_phases_phase_id_seq', COALESCE((SELECT MAX(phase_id) FROM sample_selection_phases), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'sample_submission_items_id_seq') THEN
        PERFORM setval('sample_submission_items_id_seq', COALESCE((SELECT MAX(id) FROM sample_submission_items), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'sample_submissions_id_seq') THEN
        PERFORM setval('sample_submissions_id_seq', COALESCE((SELECT MAX(id) FROM sample_submissions), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'samples_sample_id_seq') THEN
        PERFORM setval('samples_sample_id_seq', COALESCE((SELECT MAX(sample_id) FROM cycle_report_sample_selection_samples), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'scoping_audit_log_audit_id_seq') THEN
        PERFORM setval('scoping_audit_log_audit_id_seq', COALESCE((SELECT MAX(audit_id) FROM scoping_audit_log), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'scoping_submissions_submission_id_seq') THEN
        PERFORM setval('scoping_submissions_submission_id_seq', COALESCE((SELECT MAX(submission_id) FROM cycle_report_scoping_submissions), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'sla_configurations_sla_config_id_seq') THEN
        PERFORM setval('sla_configurations_sla_config_id_seq', COALESCE((SELECT MAX(sla_config_id) FROM sla_configurations), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'sla_escalation_rules_escalation_rule_id_seq') THEN
        PERFORM setval('sla_escalation_rules_escalation_rule_id_seq', COALESCE((SELECT MAX(escalation_rule_id) FROM sla_escalation_rules), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'sla_violation_tracking_violation_id_seq') THEN
        PERFORM setval('sla_violation_tracking_violation_id_seq', COALESCE((SELECT MAX(violation_id) FROM sla_violation_tracking), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'submission_documents_document_id_seq') THEN
        PERFORM setval('submission_documents_document_id_seq', COALESCE((SELECT MAX(document_id) FROM submission_documents), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'test_comparisons_comparison_id_seq') THEN
        PERFORM setval('test_comparisons_comparison_id_seq', COALESCE((SELECT MAX(comparison_id) FROM test_comparisons), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'test_cycles_cycle_id_seq') THEN
        PERFORM setval('test_cycles_cycle_id_seq', COALESCE((SELECT MAX(cycle_id) FROM test_cycles), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'test_execution_audit_logs_log_id_seq') THEN
        PERFORM setval('test_execution_audit_logs_log_id_seq', COALESCE((SELECT MAX(log_id) FROM cycle_report_test_execution_audit_logss), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'test_executions_execution_id_seq') THEN
        PERFORM setval('test_executions_execution_id_seq', COALESCE((SELECT MAX(execution_id) FROM cycle_report_test_execution_test_executions), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'test_report_sections_section_id_seq') THEN
        PERFORM setval('test_report_sections_section_id_seq', COALESCE((SELECT MAX(section_id) FROM cycle_report_test_report_sections), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'test_result_reviews_review_id_seq') THEN
        PERFORM setval('test_result_reviews_review_id_seq', COALESCE((SELECT MAX(review_id) FROM test_result_reviews), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'tester_scoping_decisions_decision_id_seq') THEN
        PERFORM setval('tester_scoping_decisions_decision_id_seq', COALESCE((SELECT MAX(decision_id) FROM cycle_report_scoping_tester_decisions), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'testing_execution_audit_logs_log_id_seq') THEN
        PERFORM setval('testing_execution_audit_logs_log_id_seq', COALESCE((SELECT MAX(log_id) FROM testing_execution_audit_logs), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'testing_test_executions_execution_id_seq') THEN
        PERFORM setval('testing_test_executions_execution_id_seq', COALESCE((SELECT MAX(execution_id) FROM testing_test_executions), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'universal_assignment_history_history_id_seq') THEN
        PERFORM setval('universal_assignment_history_history_id_seq', COALESCE((SELECT MAX(history_id) FROM universal_assignment_history), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'users_user_id_seq') THEN
        PERFORM setval('users_user_id_seq', COALESCE((SELECT MAX(user_id) FROM users), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'workflow_activities_activity_id_seq') THEN
        PERFORM setval('workflow_activities_activity_id_seq', COALESCE((SELECT MAX(activity_id) FROM workflow_activities), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'workflow_activity_dependencies_dependency_id_seq') THEN
        PERFORM setval('workflow_activity_dependencies_dependency_id_seq', COALESCE((SELECT MAX(dependency_id) FROM workflow_activity_dependencies), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'workflow_activity_history_history_id_seq') THEN
        PERFORM setval('workflow_activity_history_history_id_seq', COALESCE((SELECT MAX(history_id) FROM workflow_activity_history), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'workflow_activity_templates_template_id_seq') THEN
        PERFORM setval('workflow_activity_templates_template_id_seq', COALESCE((SELECT MAX(template_id) FROM workflow_activity_templates), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'workflow_alerts_alert_id_seq') THEN
        PERFORM setval('workflow_alerts_alert_id_seq', COALESCE((SELECT MAX(alert_id) FROM workflow_alerts), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'workflow_metrics_metric_id_seq') THEN
        PERFORM setval('workflow_metrics_metric_id_seq', COALESCE((SELECT MAX(metric_id) FROM workflow_metrics), 1));
    END IF;
END $$;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'workflow_phases_phase_id_seq') THEN
        PERFORM setval('workflow_phases_phase_id_seq', COALESCE((SELECT MAX(phase_id) FROM workflow_phases), 1));
    END IF;
END $$;