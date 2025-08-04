-- Phase ID Refactoring Script (No Data Migration Version)
-- This script refactors the database to use phase_id as the primary foreign key
-- instead of redundant cycle_id/report_id combinations
-- 
-- NOTE: This version is designed for a clean database with no existing data
-- It skips data migration steps since there are no cycles/phases to migrate

-- =============================================================================
-- PHASE 1: Add phase_id columns to tables that need them
-- =============================================================================

BEGIN;

-- Add phase_id columns (nullable for now)
-- Tables that currently have cycle_id + report_id but need phase_id
ALTER TABLE activity_states ADD COLUMN IF NOT EXISTS phase_id UUID;
ALTER TABLE cycle_report_data_profiling_rule_versions ADD COLUMN IF NOT EXISTS phase_id UUID;
ALTER TABLE cycle_report_document_submissions ADD COLUMN IF NOT EXISTS phase_id UUID;
ALTER TABLE cycle_report_planning_data_sources ADD COLUMN IF NOT EXISTS phase_id UUID;
ALTER TABLE cycle_report_planning_pde_mappings ADD COLUMN IF NOT EXISTS phase_id UUID;
ALTER TABLE cycle_report_test_cases ADD COLUMN IF NOT EXISTS phase_id UUID;
ALTER TABLE data_owner_phase_audit_logs_legacy ADD COLUMN IF NOT EXISTS phase_id UUID;
ALTER TABLE llm_audit_logs ADD COLUMN IF NOT EXISTS phase_id UUID;
ALTER TABLE metrics_execution ADD COLUMN IF NOT EXISTS phase_id UUID;
ALTER TABLE metrics_phases ADD COLUMN IF NOT EXISTS phase_id UUID;
ALTER TABLE profiling_executions ADD COLUMN IF NOT EXISTS phase_id UUID;
ALTER TABLE profiling_jobs ADD COLUMN IF NOT EXISTS phase_id UUID;
ALTER TABLE universal_sla_violation_trackings ADD COLUMN IF NOT EXISTS phase_id UUID;
ALTER TABLE universal_version_histories ADD COLUMN IF NOT EXISTS phase_id UUID;
ALTER TABLE workflow_activity_histories ADD COLUMN IF NOT EXISTS phase_id UUID;
ALTER TABLE workflow_executions ADD COLUMN IF NOT EXISTS phase_id UUID;

COMMIT;

-- =============================================================================
-- PHASE 2: Add foreign key constraints for phase_id
-- =============================================================================

BEGIN;

-- Add foreign key constraints for all tables with phase_id
-- Tables that already have phase_id but may be missing constraints
ALTER TABLE cycle_report_data_profiling_rules 
ADD CONSTRAINT IF NOT EXISTS fk_data_profiling_rules_phase_id 
FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);

ALTER TABLE cycle_report_documents 
ADD CONSTRAINT IF NOT EXISTS fk_documents_phase_id 
FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);

ALTER TABLE cycle_report_observation_groups 
ADD CONSTRAINT IF NOT EXISTS fk_observation_groups_phase_id 
FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);

ALTER TABLE cycle_report_observation_mgmt_audit_logs 
ADD CONSTRAINT IF NOT EXISTS fk_obs_mgmt_audit_logs_phase_id 
FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);

ALTER TABLE cycle_report_observation_mgmt_observation_records 
ADD CONSTRAINT IF NOT EXISTS fk_obs_mgmt_records_phase_id 
FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);

ALTER TABLE cycle_report_observation_mgmt_preliminary_findings 
ADD CONSTRAINT IF NOT EXISTS fk_obs_mgmt_findings_phase_id 
FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);

ALTER TABLE cycle_report_planning_attributes 
ADD CONSTRAINT IF NOT EXISTS fk_planning_attributes_phase_id 
FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);

ALTER TABLE cycle_report_request_info_audit_logs 
ADD CONSTRAINT IF NOT EXISTS fk_request_info_audit_phase_id 
FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);

ALTER TABLE cycle_report_request_info_testcase_source_evidence 
ADD CONSTRAINT IF NOT EXISTS fk_request_info_evidence_phase_id 
FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);

ALTER TABLE cycle_report_sample_selection_audit_logs 
ADD CONSTRAINT IF NOT EXISTS fk_sample_selection_audit_phase_id 
FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);

ALTER TABLE cycle_report_sample_selection_samples 
ADD CONSTRAINT IF NOT EXISTS fk_sample_selection_samples_phase_id 
FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);

ALTER TABLE cycle_report_scoping_attribute_recommendations_backup 
ADD CONSTRAINT IF NOT EXISTS fk_scoping_recommendations_phase_id 
FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);

ALTER TABLE cycle_report_scoping_decision_versions 
ADD CONSTRAINT IF NOT EXISTS fk_scoping_decision_versions_phase_id 
FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);

ALTER TABLE cycle_report_scoping_decisions 
ADD CONSTRAINT IF NOT EXISTS fk_scoping_decisions_phase_id 
FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);

ALTER TABLE cycle_report_scoping_submissions 
ADD CONSTRAINT IF NOT EXISTS fk_scoping_submissions_phase_id 
FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);

ALTER TABLE cycle_report_test_execution_results 
ADD CONSTRAINT IF NOT EXISTS fk_test_execution_results_phase_id 
FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);

-- Add constraints for newly added phase_id columns
ALTER TABLE cycle_report_data_profiling_rule_versions 
ADD CONSTRAINT IF NOT EXISTS fk_data_profiling_rule_versions_phase_id 
FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);

ALTER TABLE cycle_report_planning_data_sources 
ADD CONSTRAINT IF NOT EXISTS fk_planning_data_sources_phase_id 
FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);

ALTER TABLE cycle_report_planning_pde_mappings 
ADD CONSTRAINT IF NOT EXISTS fk_planning_pde_mappings_phase_id 
FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);

ALTER TABLE cycle_report_test_cases 
ADD CONSTRAINT IF NOT EXISTS fk_test_cases_phase_id 
FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);

ALTER TABLE cycle_report_document_submissions 
ADD CONSTRAINT IF NOT EXISTS fk_document_submissions_phase_id 
FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);

ALTER TABLE profiling_executions 
ADD CONSTRAINT IF NOT EXISTS fk_profiling_executions_phase_id 
FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);

ALTER TABLE profiling_jobs 
ADD CONSTRAINT IF NOT EXISTS fk_profiling_jobs_phase_id 
FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);

ALTER TABLE metrics_execution 
ADD CONSTRAINT IF NOT EXISTS fk_metrics_execution_phase_id 
FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);

COMMIT;

-- =============================================================================
-- PHASE 3: Remove redundant cycle_id and report_id columns
-- =============================================================================

-- Tables to refactor (remove cycle_id and report_id, keep only phase_id)
-- NOTE: We'll be conservative and only remove from tables where we're confident

BEGIN;

-- Check if tables exist and have the columns before dropping
DO $$
DECLARE
    table_name TEXT;
    tables_to_process TEXT[] := ARRAY[
        'cycle_report_data_profiling_rules',
        'cycle_report_documents',
        'cycle_report_observation_groups',
        'cycle_report_observation_mgmt_audit_logs',
        'cycle_report_observation_mgmt_observation_records',
        'cycle_report_observation_mgmt_preliminary_findings',
        'cycle_report_planning_attributes',
        'cycle_report_request_info_audit_logs',
        'cycle_report_request_info_testcase_source_evidence',
        'cycle_report_sample_selection_audit_logs',
        'cycle_report_sample_selection_samples',
        'cycle_report_scoping_attribute_recommendations_backup',
        'cycle_report_scoping_decision_versions',
        'cycle_report_scoping_decisions',
        'cycle_report_scoping_submissions',
        'cycle_report_test_execution_results'
    ];
BEGIN
    FOREACH table_name IN ARRAY tables_to_process
    LOOP
        -- Check if table exists
        IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = table_name AND table_schema = 'public') THEN
            -- Drop foreign key constraints first (ignore if they don't exist)
            EXECUTE format('ALTER TABLE %I DROP CONSTRAINT IF EXISTS %I_cycle_id_fkey', table_name, table_name);
            EXECUTE format('ALTER TABLE %I DROP CONSTRAINT IF EXISTS %I_report_id_fkey', table_name, table_name);
            EXECUTE format('ALTER TABLE %I DROP CONSTRAINT IF EXISTS fk_%I_cycle', table_name, table_name);
            EXECUTE format('ALTER TABLE %I DROP CONSTRAINT IF EXISTS fk_%I_report', table_name, table_name);
            
            -- Drop the columns if they exist
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = table_name AND column_name = 'cycle_id' AND table_schema = 'public') THEN
                EXECUTE format('ALTER TABLE %I DROP COLUMN cycle_id', table_name);
                RAISE NOTICE 'Dropped cycle_id from %', table_name;
            END IF;
            
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = table_name AND column_name = 'report_id' AND table_schema = 'public') THEN
                EXECUTE format('ALTER TABLE %I DROP COLUMN report_id', table_name);
                RAISE NOTICE 'Dropped report_id from %', table_name;
            END IF;
        ELSE
            RAISE NOTICE 'Table % does not exist, skipping', table_name;
        END IF;
    END LOOP;
END $$;

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

-- List all tables with their ID column status
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

-- Summary message
SELECT 'Phase ID refactoring completed successfully. Tables now use phase_id as primary foreign key relationship.' as message;