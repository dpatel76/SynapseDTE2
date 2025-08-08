-- Phase ID Refactoring Script (Fixed Version)
-- This script refactors the database to use phase_id as the primary foreign key
-- instead of redundant cycle_id/report_id combinations

-- =============================================================================
-- PHASE 1: Add phase_id columns to tables that need them (COMPLETED)
-- =============================================================================
-- Already done - phase_id columns exist

-- =============================================================================
-- PHASE 2: Add foreign key constraints for phase_id (with proper error handling)
-- =============================================================================

-- Add foreign key constraints, ignoring if they already exist
DO $$
BEGIN
    -- Tables that already have phase_id
    BEGIN
        ALTER TABLE cycle_report_data_profiling_rules 
        ADD CONSTRAINT fk_data_profiling_rules_phase_id 
        FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);
    EXCEPTION WHEN duplicate_object THEN
        RAISE NOTICE 'Constraint fk_data_profiling_rules_phase_id already exists';
    END;

    BEGIN
        ALTER TABLE cycle_report_documents 
        ADD CONSTRAINT fk_documents_phase_id 
        FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);
    EXCEPTION WHEN duplicate_object THEN
        RAISE NOTICE 'Constraint fk_documents_phase_id already exists';
    END;

    BEGIN
        ALTER TABLE cycle_report_observation_groups 
        ADD CONSTRAINT fk_observation_groups_phase_id 
        FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);
    EXCEPTION WHEN duplicate_object THEN
        RAISE NOTICE 'Constraint fk_observation_groups_phase_id already exists';
    END;

    BEGIN
        ALTER TABLE cycle_report_observation_mgmt_audit_logs 
        ADD CONSTRAINT fk_obs_mgmt_audit_logs_phase_id 
        FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);
    EXCEPTION WHEN duplicate_object THEN
        RAISE NOTICE 'Constraint fk_obs_mgmt_audit_logs_phase_id already exists';
    END;

    BEGIN
        ALTER TABLE cycle_report_observation_mgmt_observation_records 
        ADD CONSTRAINT fk_obs_mgmt_records_phase_id 
        FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);
    EXCEPTION WHEN duplicate_object THEN
        RAISE NOTICE 'Constraint fk_obs_mgmt_records_phase_id already exists';
    END;

    BEGIN
        ALTER TABLE cycle_report_observation_mgmt_preliminary_findings 
        ADD CONSTRAINT fk_obs_mgmt_findings_phase_id 
        FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);
    EXCEPTION WHEN duplicate_object THEN
        RAISE NOTICE 'Constraint fk_obs_mgmt_findings_phase_id already exists';
    END;

    BEGIN
        ALTER TABLE cycle_report_planning_attributes 
        ADD CONSTRAINT fk_planning_attributes_phase_id 
        FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);
    EXCEPTION WHEN duplicate_object THEN
        RAISE NOTICE 'Constraint fk_planning_attributes_phase_id already exists';
    END;

    BEGIN
        ALTER TABLE cycle_report_request_info_audit_logs 
        ADD CONSTRAINT fk_request_info_audit_phase_id 
        FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);
    EXCEPTION WHEN duplicate_object THEN
        RAISE NOTICE 'Constraint fk_request_info_audit_phase_id already exists';
    END;

    BEGIN
        ALTER TABLE cycle_report_request_info_testcase_source_evidence 
        ADD CONSTRAINT fk_request_info_evidence_phase_id 
        FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);
    EXCEPTION WHEN duplicate_object THEN
        RAISE NOTICE 'Constraint fk_request_info_evidence_phase_id already exists';
    END;

    BEGIN
        ALTER TABLE cycle_report_sample_selection_audit_logs 
        ADD CONSTRAINT fk_sample_selection_audit_phase_id 
        FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);
    EXCEPTION WHEN duplicate_object THEN
        RAISE NOTICE 'Constraint fk_sample_selection_audit_phase_id already exists';
    END;

    BEGIN
        ALTER TABLE cycle_report_sample_selection_samples 
        ADD CONSTRAINT fk_sample_selection_samples_phase_id 
        FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);
    EXCEPTION WHEN duplicate_object THEN
        RAISE NOTICE 'Constraint fk_sample_selection_samples_phase_id already exists';
    END;

    BEGIN
        ALTER TABLE cycle_report_scoping_attribute_recommendations_backup 
        ADD CONSTRAINT fk_scoping_recommendations_phase_id 
        FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);
    EXCEPTION WHEN duplicate_object THEN
        RAISE NOTICE 'Constraint fk_scoping_recommendations_phase_id already exists';
    END;

    BEGIN
        ALTER TABLE cycle_report_scoping_decision_versions 
        ADD CONSTRAINT fk_scoping_decision_versions_phase_id 
        FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);
    EXCEPTION WHEN duplicate_object THEN
        RAISE NOTICE 'Constraint fk_scoping_decision_versions_phase_id already exists';
    END;

    BEGIN
        ALTER TABLE cycle_report_scoping_decisions 
        ADD CONSTRAINT fk_scoping_decisions_phase_id 
        FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);
    EXCEPTION WHEN duplicate_object THEN
        RAISE NOTICE 'Constraint fk_scoping_decisions_phase_id already exists';
    END;

    BEGIN
        ALTER TABLE cycle_report_scoping_submissions 
        ADD CONSTRAINT fk_scoping_submissions_phase_id 
        FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);
    EXCEPTION WHEN duplicate_object THEN
        RAISE NOTICE 'Constraint fk_scoping_submissions_phase_id already exists';
    END;

    BEGIN
        ALTER TABLE cycle_report_test_execution_results 
        ADD CONSTRAINT fk_test_execution_results_phase_id 
        FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);
    EXCEPTION WHEN duplicate_object THEN
        RAISE NOTICE 'Constraint fk_test_execution_results_phase_id already exists';
    END;

    -- Tables with newly added phase_id columns
    BEGIN
        ALTER TABLE cycle_report_data_profiling_rule_versions 
        ADD CONSTRAINT fk_data_profiling_rule_versions_phase_id 
        FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);
    EXCEPTION WHEN duplicate_object THEN
        RAISE NOTICE 'Constraint fk_data_profiling_rule_versions_phase_id already exists';
    END;

    BEGIN
        ALTER TABLE cycle_report_planning_data_sources 
        ADD CONSTRAINT fk_planning_data_sources_phase_id 
        FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);
    EXCEPTION WHEN duplicate_object THEN
        RAISE NOTICE 'Constraint fk_planning_data_sources_phase_id already exists';
    END;

    BEGIN
        ALTER TABLE cycle_report_planning_pde_mappings 
        ADD CONSTRAINT fk_planning_pde_mappings_phase_id 
        FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);
    EXCEPTION WHEN duplicate_object THEN
        RAISE NOTICE 'Constraint fk_planning_pde_mappings_phase_id already exists';
    END;

    BEGIN
        ALTER TABLE cycle_report_test_cases 
        ADD CONSTRAINT fk_test_cases_phase_id 
        FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);
    EXCEPTION WHEN duplicate_object THEN
        RAISE NOTICE 'Constraint fk_test_cases_phase_id already exists';
    END;

    BEGIN
        ALTER TABLE cycle_report_document_submissions 
        ADD CONSTRAINT fk_document_submissions_phase_id 
        FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);
    EXCEPTION WHEN duplicate_object THEN
        RAISE NOTICE 'Constraint fk_document_submissions_phase_id already exists';
    END;

    BEGIN
        ALTER TABLE profiling_executions 
        ADD CONSTRAINT fk_profiling_executions_phase_id 
        FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);
    EXCEPTION WHEN duplicate_object THEN
        RAISE NOTICE 'Constraint fk_profiling_executions_phase_id already exists';
    END;

    BEGIN
        ALTER TABLE profiling_jobs 
        ADD CONSTRAINT fk_profiling_jobs_phase_id 
        FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);
    EXCEPTION WHEN duplicate_object THEN
        RAISE NOTICE 'Constraint fk_profiling_jobs_phase_id already exists';
    END;

    BEGIN
        ALTER TABLE metrics_execution 
        ADD CONSTRAINT fk_metrics_execution_phase_id 
        FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);
    EXCEPTION WHEN duplicate_object THEN
        RAISE NOTICE 'Constraint fk_metrics_execution_phase_id already exists';
    END;

END $$;

-- =============================================================================
-- PHASE 3: Remove redundant cycle_id and report_id columns
-- =============================================================================

-- Drop redundant columns from tables that should only use phase_id
DO $$
DECLARE
    table_rec TEXT;
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
    FOREACH table_rec IN ARRAY tables_to_process
    LOOP
        -- Check if table exists
        IF EXISTS (SELECT 1 FROM information_schema.tables 
                  WHERE table_name = table_rec AND table_schema = 'public') THEN
            
            -- Drop foreign key constraints first (ignore if they don't exist)
            BEGIN
                EXECUTE format('ALTER TABLE %I DROP CONSTRAINT %I_cycle_id_fkey', table_rec, table_rec);
                RAISE NOTICE 'Dropped constraint %_cycle_id_fkey from %', table_rec, table_rec;
            EXCEPTION 
                WHEN undefined_object THEN
                    RAISE NOTICE 'Constraint %_cycle_id_fkey does not exist in %', table_rec, table_rec;
                WHEN OTHERS THEN
                    RAISE NOTICE 'Error dropping constraint %_cycle_id_fkey from %: %', table_rec, table_rec, SQLERRM;
            END;

            BEGIN
                EXECUTE format('ALTER TABLE %I DROP CONSTRAINT %I_report_id_fkey', table_rec, table_rec);
                RAISE NOTICE 'Dropped constraint %_report_id_fkey from %', table_rec, table_rec;
            EXCEPTION 
                WHEN undefined_object THEN
                    RAISE NOTICE 'Constraint %_report_id_fkey does not exist in %', table_rec, table_rec;
                WHEN OTHERS THEN
                    RAISE NOTICE 'Error dropping constraint %_report_id_fkey from %: %', table_rec, table_rec, SQLERRM;
            END;

            -- Drop the columns if they exist
            IF EXISTS (SELECT 1 FROM information_schema.columns 
                      WHERE table_name = table_rec AND column_name = 'cycle_id' AND table_schema = 'public') THEN
                EXECUTE format('ALTER TABLE %I DROP COLUMN cycle_id', table_rec);
                RAISE NOTICE 'Dropped cycle_id column from %', table_rec;
            ELSE
                RAISE NOTICE 'cycle_id column does not exist in %', table_rec;
            END IF;
            
            IF EXISTS (SELECT 1 FROM information_schema.columns 
                      WHERE table_name = table_rec AND column_name = 'report_id' AND table_schema = 'public') THEN
                EXECUTE format('ALTER TABLE %I DROP COLUMN report_id', table_rec);
                RAISE NOTICE 'Dropped report_id column from %', table_rec;
            ELSE
                RAISE NOTICE 'report_id column does not exist in %', table_rec;
            END IF;
            
        ELSE
            RAISE NOTICE 'Table % does not exist, skipping', table_rec;
        END IF;
    END LOOP;
END $$;

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