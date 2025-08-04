-- Phase ID Refactoring Script
-- This script refactors the database to use phase_id as the primary foreign key
-- instead of redundant cycle_id/report_id combinations

-- =============================================================================
-- PHASE 1: Add phase_id columns to tables that need them
-- =============================================================================

-- Tables that currently have cycle_id + report_id but need phase_id
BEGIN;

-- Add phase_id columns (nullable initially)
ALTER TABLE activity_states ADD COLUMN phase_id UUID;
ALTER TABLE cycle_report_data_profiling_rule_versions ADD COLUMN phase_id UUID;
ALTER TABLE cycle_report_document_submissions ADD COLUMN phase_id UUID;
ALTER TABLE cycle_report_planning_data_sources ADD COLUMN phase_id UUID;
ALTER TABLE cycle_report_planning_pde_mappings ADD COLUMN phase_id UUID;
ALTER TABLE cycle_report_test_cases ADD COLUMN phase_id UUID;
ALTER TABLE data_owner_phase_audit_logs_legacy ADD COLUMN phase_id UUID;
ALTER TABLE llm_audit_logs ADD COLUMN phase_id UUID;
ALTER TABLE metrics_execution ADD COLUMN phase_id UUID;
ALTER TABLE metrics_phases ADD COLUMN phase_id UUID;
ALTER TABLE profiling_executions ADD COLUMN phase_id UUID;
ALTER TABLE profiling_jobs ADD COLUMN phase_id UUID;
ALTER TABLE universal_sla_violation_trackings ADD COLUMN phase_id UUID;
ALTER TABLE universal_version_histories ADD COLUMN phase_id UUID;
ALTER TABLE workflow_activity_histories ADD COLUMN phase_id UUID;
ALTER TABLE workflow_executions ADD COLUMN phase_id UUID;

COMMIT;

-- =============================================================================
-- PHASE 2: Populate phase_id from existing cycle_id/report_id relationships
-- =============================================================================

-- For tables that will only use phase_id (removing cycle_id/report_id)
BEGIN;

-- Data Profiling Rules -> Data Profiling phase
UPDATE cycle_report_data_profiling_rules 
SET phase_id = wp.phase_id
FROM workflow_phases wp
WHERE wp.cycle_id = cycle_report_data_profiling_rules.cycle_id 
    AND wp.report_id = cycle_report_data_profiling_rules.report_id
    AND wp.phase_name = 'Data Profiling';

-- Documents -> Request for Information phase (most documents are RFI related)
UPDATE cycle_report_documents 
SET phase_id = wp.phase_id
FROM workflow_phases wp
WHERE wp.cycle_id = cycle_report_documents.cycle_id 
    AND wp.report_id = cycle_report_documents.report_id
    AND wp.phase_name = 'Request for Information';

-- Observation tables -> Observation Management phase
UPDATE cycle_report_observation_groups 
SET phase_id = wp.phase_id
FROM workflow_phases wp
WHERE wp.cycle_id = cycle_report_observation_groups.cycle_id 
    AND wp.report_id = cycle_report_observation_groups.report_id
    AND wp.phase_name = 'Observation Management';

UPDATE cycle_report_observation_mgmt_audit_logs 
SET phase_id = wp.phase_id
FROM workflow_phases wp
WHERE wp.cycle_id = cycle_report_observation_mgmt_audit_logs.cycle_id 
    AND wp.report_id = cycle_report_observation_mgmt_audit_logs.report_id
    AND wp.phase_name = 'Observation Management';

UPDATE cycle_report_observation_mgmt_observation_records 
SET phase_id = wp.phase_id
FROM workflow_phases wp
WHERE wp.cycle_id = cycle_report_observation_mgmt_observation_records.cycle_id 
    AND wp.report_id = cycle_report_observation_mgmt_observation_records.report_id
    AND wp.phase_name = 'Observation Management';

UPDATE cycle_report_observation_mgmt_preliminary_findings 
SET phase_id = wp.phase_id
FROM workflow_phases wp
WHERE wp.cycle_id = cycle_report_observation_mgmt_preliminary_findings.cycle_id 
    AND wp.report_id = cycle_report_observation_mgmt_preliminary_findings.report_id
    AND wp.phase_name = 'Observation Management';

-- Planning Attributes -> Planning phase
UPDATE cycle_report_planning_attributes 
SET phase_id = wp.phase_id
FROM workflow_phases wp
WHERE wp.cycle_id = cycle_report_planning_attributes.cycle_id 
    AND wp.report_id = cycle_report_planning_attributes.report_id
    AND wp.phase_name = 'Planning';

-- Request Info tables -> Request for Information phase
UPDATE cycle_report_request_info_audit_logs 
SET phase_id = wp.phase_id
FROM workflow_phases wp
WHERE wp.cycle_id = cycle_report_request_info_audit_logs.cycle_id 
    AND wp.report_id = cycle_report_request_info_audit_logs.report_id
    AND wp.phase_name = 'Request for Information';

UPDATE cycle_report_request_info_testcase_source_evidence 
SET phase_id = wp.phase_id
FROM workflow_phases wp
WHERE wp.cycle_id = cycle_report_request_info_testcase_source_evidence.cycle_id 
    AND wp.report_id = cycle_report_request_info_testcase_source_evidence.report_id
    AND wp.phase_name = 'Request for Information';

-- Sample Selection tables -> Sample Selection phase
UPDATE cycle_report_sample_selection_audit_logs 
SET phase_id = wp.phase_id
FROM workflow_phases wp
WHERE wp.cycle_id = cycle_report_sample_selection_audit_logs.cycle_id 
    AND wp.report_id = cycle_report_sample_selection_audit_logs.report_id
    AND wp.phase_name = 'Sample Selection';

UPDATE cycle_report_sample_selection_samples 
SET phase_id = wp.phase_id
FROM workflow_phases wp
WHERE wp.cycle_id = cycle_report_sample_selection_samples.cycle_id 
    AND wp.report_id = cycle_report_sample_selection_samples.report_id
    AND wp.phase_name = 'Sample Selection';

-- Scoping tables -> Scoping phase
UPDATE cycle_report_scoping_attribute_recommendations_backup 
SET phase_id = wp.phase_id
FROM workflow_phases wp
WHERE wp.cycle_id = cycle_report_scoping_attribute_recommendations_backup.cycle_id 
    AND wp.report_id = cycle_report_scoping_attribute_recommendations_backup.report_id
    AND wp.phase_name = 'Scoping';

UPDATE cycle_report_scoping_decision_versions 
SET phase_id = wp.phase_id
FROM workflow_phases wp
WHERE wp.cycle_id = cycle_report_scoping_decision_versions.cycle_id 
    AND wp.report_id = cycle_report_scoping_decision_versions.report_id
    AND wp.phase_name = 'Scoping';

UPDATE cycle_report_scoping_decisions 
SET phase_id = wp.phase_id
FROM workflow_phases wp
WHERE wp.cycle_id = cycle_report_scoping_decisions.cycle_id 
    AND wp.report_id = cycle_report_scoping_decisions.report_id
    AND wp.phase_name = 'Scoping';

UPDATE cycle_report_scoping_submissions 
SET phase_id = wp.phase_id
FROM workflow_phases wp
WHERE wp.cycle_id = cycle_report_scoping_submissions.cycle_id 
    AND wp.report_id = cycle_report_scoping_submissions.report_id
    AND wp.phase_name = 'Scoping';

-- Test Execution tables -> Test Execution phase
UPDATE cycle_report_test_execution_results 
SET phase_id = wp.phase_id
FROM workflow_phases wp
WHERE wp.cycle_id = cycle_report_test_execution_results.cycle_id 
    AND wp.report_id = cycle_report_test_execution_results.report_id
    AND wp.phase_name = 'Test Execution';

COMMIT;

-- =============================================================================
-- PHASE 3: Populate phase_id for tables getting phase_id added
-- =============================================================================

BEGIN;

-- Data Profiling related tables
UPDATE cycle_report_data_profiling_rule_versions 
SET phase_id = wp.phase_id
FROM workflow_phases wp
WHERE wp.cycle_id = cycle_report_data_profiling_rule_versions.cycle_id 
    AND wp.report_id = cycle_report_data_profiling_rule_versions.report_id
    AND wp.phase_name = 'Data Profiling';

UPDATE profiling_executions 
SET phase_id = wp.phase_id
FROM workflow_phases wp
WHERE wp.cycle_id = profiling_executions.cycle_id 
    AND wp.report_id = profiling_executions.report_id
    AND wp.phase_name = 'Data Profiling';

UPDATE profiling_jobs 
SET phase_id = wp.phase_id
FROM workflow_phases wp
WHERE wp.cycle_id = profiling_jobs.cycle_id 
    AND wp.report_id = profiling_jobs.report_id
    AND wp.phase_name = 'Data Profiling';

-- Planning related tables
UPDATE cycle_report_planning_data_sources 
SET phase_id = wp.phase_id
FROM workflow_phases wp
WHERE wp.cycle_id = cycle_report_planning_data_sources.cycle_id 
    AND wp.report_id = cycle_report_planning_data_sources.report_id
    AND wp.phase_name = 'Planning';

UPDATE cycle_report_planning_pde_mappings 
SET phase_id = wp.phase_id
FROM workflow_phases wp
WHERE wp.cycle_id = cycle_report_planning_pde_mappings.cycle_id 
    AND wp.report_id = cycle_report_planning_pde_mappings.report_id
    AND wp.phase_name = 'Planning';

-- Test Execution related tables
UPDATE cycle_report_test_cases 
SET phase_id = wp.phase_id
FROM workflow_phases wp
WHERE wp.cycle_id = cycle_report_test_cases.cycle_id 
    AND wp.report_id = cycle_report_test_cases.report_id
    AND wp.phase_name = 'Test Execution';

UPDATE metrics_execution 
SET phase_id = wp.phase_id
FROM workflow_phases wp
WHERE wp.cycle_id = metrics_execution.cycle_id 
    AND wp.report_id = metrics_execution.report_id
    AND wp.phase_name = 'Test Execution';

-- Document related tables
UPDATE cycle_report_document_submissions 
SET phase_id = wp.phase_id
FROM workflow_phases wp
WHERE wp.cycle_id = cycle_report_document_submissions.cycle_id 
    AND wp.report_id = cycle_report_document_submissions.report_id
    AND wp.phase_name = 'Request for Information';

COMMIT;

-- =============================================================================
-- PHASE 4: Add foreign key constraints for phase_id
-- =============================================================================

BEGIN;

-- Add foreign key constraints for all tables with phase_id
ALTER TABLE cycle_report_data_profiling_rules 
ADD CONSTRAINT fk_data_profiling_rules_phase_id 
FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);

ALTER TABLE cycle_report_documents 
ADD CONSTRAINT fk_documents_phase_id 
FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);

ALTER TABLE cycle_report_observation_groups 
ADD CONSTRAINT fk_observation_groups_phase_id 
FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);

ALTER TABLE cycle_report_observation_mgmt_audit_logs 
ADD CONSTRAINT fk_obs_mgmt_audit_logs_phase_id 
FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);

ALTER TABLE cycle_report_observation_mgmt_observation_records 
ADD CONSTRAINT fk_obs_mgmt_records_phase_id 
FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);

ALTER TABLE cycle_report_observation_mgmt_preliminary_findings 
ADD CONSTRAINT fk_obs_mgmt_findings_phase_id 
FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);

ALTER TABLE cycle_report_planning_attributes 
ADD CONSTRAINT fk_planning_attributes_phase_id 
FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);

ALTER TABLE cycle_report_request_info_audit_logs 
ADD CONSTRAINT fk_request_info_audit_phase_id 
FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);

ALTER TABLE cycle_report_request_info_testcase_source_evidence 
ADD CONSTRAINT fk_request_info_evidence_phase_id 
FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);

ALTER TABLE cycle_report_sample_selection_audit_logs 
ADD CONSTRAINT fk_sample_selection_audit_phase_id 
FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);

ALTER TABLE cycle_report_sample_selection_samples 
ADD CONSTRAINT fk_sample_selection_samples_phase_id 
FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);

ALTER TABLE cycle_report_scoping_attribute_recommendations_backup 
ADD CONSTRAINT fk_scoping_recommendations_phase_id 
FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);

ALTER TABLE cycle_report_scoping_decision_versions 
ADD CONSTRAINT fk_scoping_decision_versions_phase_id 
FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);

ALTER TABLE cycle_report_scoping_decisions 
ADD CONSTRAINT fk_scoping_decisions_phase_id 
FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);

ALTER TABLE cycle_report_scoping_submissions 
ADD CONSTRAINT fk_scoping_submissions_phase_id 
FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);

ALTER TABLE cycle_report_test_execution_results 
ADD CONSTRAINT fk_test_execution_results_phase_id 
FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);

-- Add constraints for newly added phase_id columns
ALTER TABLE cycle_report_data_profiling_rule_versions 
ADD CONSTRAINT fk_data_profiling_rule_versions_phase_id 
FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);

ALTER TABLE cycle_report_planning_data_sources 
ADD CONSTRAINT fk_planning_data_sources_phase_id 
FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);

ALTER TABLE cycle_report_planning_pde_mappings 
ADD CONSTRAINT fk_planning_pde_mappings_phase_id 
FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);

ALTER TABLE cycle_report_test_cases 
ADD CONSTRAINT fk_test_cases_phase_id 
FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);

ALTER TABLE cycle_report_document_submissions 
ADD CONSTRAINT fk_document_submissions_phase_id 
FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);

ALTER TABLE profiling_executions 
ADD CONSTRAINT fk_profiling_executions_phase_id 
FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);

ALTER TABLE profiling_jobs 
ADD CONSTRAINT fk_profiling_jobs_phase_id 
FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);

ALTER TABLE metrics_execution 
ADD CONSTRAINT fk_metrics_execution_phase_id 
FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);

COMMIT;

-- =============================================================================
-- PHASE 5: Remove redundant cycle_id and report_id columns
-- =============================================================================

BEGIN;

-- Drop foreign key constraints first, then columns
-- Note: Some constraint names may vary, using IF EXISTS for safety

-- Data Profiling Rules
ALTER TABLE cycle_report_data_profiling_rules 
DROP CONSTRAINT IF EXISTS cycle_report_data_profiling_rules_cycle_id_fkey,
DROP CONSTRAINT IF EXISTS cycle_report_data_profiling_rules_report_id_fkey,
DROP CONSTRAINT IF EXISTS fk_data_profiling_rules_cycle,
DROP CONSTRAINT IF EXISTS fk_data_profiling_rules_report;

ALTER TABLE cycle_report_data_profiling_rules 
DROP COLUMN cycle_id,
DROP COLUMN report_id;

-- Documents
ALTER TABLE cycle_report_documents 
DROP CONSTRAINT IF EXISTS cycle_report_documents_cycle_id_fkey,
DROP CONSTRAINT IF EXISTS cycle_report_documents_report_id_fkey;

ALTER TABLE cycle_report_documents 
DROP COLUMN cycle_id,
DROP COLUMN report_id;

-- Observation tables
ALTER TABLE cycle_report_observation_groups 
DROP CONSTRAINT IF EXISTS cycle_report_observation_groups_cycle_id_fkey,
DROP CONSTRAINT IF EXISTS cycle_report_observation_groups_report_id_fkey;

ALTER TABLE cycle_report_observation_groups 
DROP COLUMN cycle_id,
DROP COLUMN report_id;

ALTER TABLE cycle_report_observation_mgmt_audit_logs 
DROP CONSTRAINT IF EXISTS cycle_report_observation_mgmt_audit_logs_cycle_id_fkey,
DROP CONSTRAINT IF EXISTS cycle_report_observation_mgmt_audit_logs_report_id_fkey;

ALTER TABLE cycle_report_observation_mgmt_audit_logs 
DROP COLUMN cycle_id,
DROP COLUMN report_id;

ALTER TABLE cycle_report_observation_mgmt_observation_records 
DROP CONSTRAINT IF EXISTS cycle_report_observation_mgmt_observation_records_cycle_id_fkey,
DROP CONSTRAINT IF EXISTS cycle_report_observation_mgmt_observation_records_report_id_fkey;

ALTER TABLE cycle_report_observation_mgmt_observation_records 
DROP COLUMN cycle_id,
DROP COLUMN report_id;

ALTER TABLE cycle_report_observation_mgmt_preliminary_findings 
DROP CONSTRAINT IF EXISTS cycle_report_observation_mgmt_preliminary_findings_cycle_id_fkey,
DROP CONSTRAINT IF EXISTS cycle_report_observation_mgmt_preliminary_findings_report_id_fkey;

ALTER TABLE cycle_report_observation_mgmt_preliminary_findings 
DROP COLUMN cycle_id,
DROP COLUMN report_id;

-- Planning Attributes
ALTER TABLE cycle_report_planning_attributes 
DROP CONSTRAINT IF EXISTS cycle_report_planning_attributes_cycle_id_fkey,
DROP CONSTRAINT IF EXISTS cycle_report_planning_attributes_report_id_fkey;

ALTER TABLE cycle_report_planning_attributes 
DROP COLUMN cycle_id,
DROP COLUMN report_id;

-- Request Info tables
ALTER TABLE cycle_report_request_info_audit_logs 
DROP CONSTRAINT IF EXISTS cycle_report_request_info_audit_logs_cycle_id_fkey,
DROP CONSTRAINT IF EXISTS cycle_report_request_info_audit_logs_report_id_fkey;

ALTER TABLE cycle_report_request_info_audit_logs 
DROP COLUMN cycle_id,
DROP COLUMN report_id;

ALTER TABLE cycle_report_request_info_testcase_source_evidence 
DROP CONSTRAINT IF EXISTS cycle_report_request_info_testcase_source_evidence_cycle_id_fkey,
DROP CONSTRAINT IF EXISTS cycle_report_request_info_testcase_source_evidence_report_id_fkey;

ALTER TABLE cycle_report_request_info_testcase_source_evidence 
DROP COLUMN cycle_id,
DROP COLUMN report_id;

-- Sample Selection tables
ALTER TABLE cycle_report_sample_selection_audit_logs 
DROP CONSTRAINT IF EXISTS cycle_report_sample_selection_audit_logs_cycle_id_fkey,
DROP CONSTRAINT IF EXISTS cycle_report_sample_selection_audit_logs_report_id_fkey;

ALTER TABLE cycle_report_sample_selection_audit_logs 
DROP COLUMN cycle_id,
DROP COLUMN report_id;

ALTER TABLE cycle_report_sample_selection_samples 
DROP CONSTRAINT IF EXISTS cycle_report_sample_selection_samples_cycle_id_fkey,
DROP CONSTRAINT IF EXISTS cycle_report_sample_selection_samples_report_id_fkey;

ALTER TABLE cycle_report_sample_selection_samples 
DROP COLUMN cycle_id,
DROP COLUMN report_id;

-- Scoping tables
ALTER TABLE cycle_report_scoping_attribute_recommendations_backup 
DROP CONSTRAINT IF EXISTS cycle_report_scoping_attribute_recommendations_backup_cycle_id_fkey,
DROP CONSTRAINT IF EXISTS cycle_report_scoping_attribute_recommendations_backup_report_id_fkey;

ALTER TABLE cycle_report_scoping_attribute_recommendations_backup 
DROP COLUMN cycle_id,
DROP COLUMN report_id;

ALTER TABLE cycle_report_scoping_decision_versions 
DROP CONSTRAINT IF EXISTS cycle_report_scoping_decision_versions_cycle_id_fkey,
DROP CONSTRAINT IF EXISTS cycle_report_scoping_decision_versions_report_id_fkey;

ALTER TABLE cycle_report_scoping_decision_versions 
DROP COLUMN cycle_id,
DROP COLUMN report_id;

ALTER TABLE cycle_report_scoping_decisions 
DROP CONSTRAINT IF EXISTS cycle_report_scoping_decisions_cycle_id_fkey,
DROP CONSTRAINT IF EXISTS cycle_report_scoping_decisions_report_id_fkey;

ALTER TABLE cycle_report_scoping_decisions 
DROP COLUMN cycle_id,
DROP COLUMN report_id;

ALTER TABLE cycle_report_scoping_submissions 
DROP CONSTRAINT IF EXISTS cycle_report_scoping_submissions_cycle_id_fkey,
DROP CONSTRAINT IF EXISTS cycle_report_scoping_submissions_report_id_fkey;

ALTER TABLE cycle_report_scoping_submissions 
DROP COLUMN cycle_id,
DROP COLUMN report_id;

-- Test Execution tables
ALTER TABLE cycle_report_test_execution_results 
DROP CONSTRAINT IF EXISTS cycle_report_test_execution_results_cycle_id_fkey,
DROP CONSTRAINT IF EXISTS cycle_report_test_execution_results_report_id_fkey;

ALTER TABLE cycle_report_test_execution_results 
DROP COLUMN cycle_id,
DROP COLUMN report_id;

COMMIT;

-- =============================================================================
-- VERIFICATION QUERIES
-- =============================================================================

-- Check the refactoring results
SELECT 
    'Phase ID Refactoring Complete' as status,
    COUNT(*) as tables_with_phase_id_only
FROM information_schema.tables t
JOIN information_schema.columns c1 ON t.table_name = c1.table_name 
    AND c1.column_name = 'phase_id'
LEFT JOIN information_schema.columns c2 ON t.table_name = c2.table_name 
    AND c2.column_name = 'cycle_id'
LEFT JOIN information_schema.columns c3 ON t.table_name = c3.table_name 
    AND c3.column_name = 'report_id'
WHERE t.table_schema = 'public' 
    AND t.table_type = 'BASE TABLE'
    AND c1.column_name IS NOT NULL  -- Has phase_id
    AND c2.column_name IS NULL      -- No cycle_id
    AND c3.column_name IS NULL      -- No report_id
    AND t.table_name LIKE 'cycle_report_%';

-- List remaining tables with multiple ID columns
SELECT 
    t.table_name,
    CASE WHEN c1.column_name IS NOT NULL THEN '✓' ELSE '✗' END as has_phase_id,
    CASE WHEN c2.column_name IS NOT NULL THEN '✓' ELSE '✗' END as has_cycle_id,
    CASE WHEN c3.column_name IS NOT NULL THEN '✓' ELSE '✗' END as has_report_id
FROM information_schema.tables t
LEFT JOIN information_schema.columns c1 ON t.table_name = c1.table_name 
    AND c1.column_name = 'phase_id'
LEFT JOIN information_schema.columns c2 ON t.table_name = c2.table_name 
    AND c2.column_name = 'cycle_id'
LEFT JOIN information_schema.columns c3 ON t.table_name = c3.table_name 
    AND c3.column_name = 'report_id'
WHERE t.table_schema = 'public' 
    AND t.table_type = 'BASE TABLE'
    AND (c1.column_name IS NOT NULL OR c2.column_name IS NOT NULL OR c3.column_name IS NOT NULL)
    AND t.table_name LIKE 'cycle_report_%'
ORDER BY t.table_name;