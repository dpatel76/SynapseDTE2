-- Comprehensive fix for all audit columns
-- This script uses a PL/pgSQL function to dynamically add audit columns to ALL tables

BEGIN;

-- Create a function to add audit columns if they don't exist
CREATE OR REPLACE FUNCTION add_audit_columns_to_table(p_table_name TEXT)
RETURNS VOID AS $$
DECLARE
    has_created_by BOOLEAN;
    has_updated_by BOOLEAN;
BEGIN
    -- Check if columns exist
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns c
        WHERE c.table_schema = 'public' 
        AND c.table_name = p_table_name 
        AND c.column_name = 'created_by_id'
    ) INTO has_created_by;
    
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns c
        WHERE c.table_schema = 'public' 
        AND c.table_name = p_table_name 
        AND c.column_name = 'updated_by_id'
    ) INTO has_updated_by;
    
    -- Add created_by_id if missing
    IF NOT has_created_by THEN
        EXECUTE format('ALTER TABLE %I ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL', p_table_name);
        EXECUTE format('CREATE INDEX idx_%s_created_by ON %I(created_by_id)', p_table_name, p_table_name);
        RAISE NOTICE 'Added created_by_id to %', p_table_name;
    END IF;
    
    -- Add updated_by_id if missing
    IF NOT has_updated_by THEN
        EXECUTE format('ALTER TABLE %I ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL', p_table_name);
        EXECUTE format('CREATE INDEX idx_%s_updated_by ON %I(updated_by_id)', p_table_name, p_table_name);
        RAISE NOTICE 'Added updated_by_id to %', p_table_name;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Apply to all tables that should have audit columns based on the models
DO $$
DECLARE
    tbl TEXT;
    tables_to_update TEXT[] := ARRAY[
        'roles', 'permissions', 'role_permissions', 'user_roles', 'user_permissions',
        'resource_permissions', 'resources', 'lobs', 'test_cycles', 'cycle_reports',
        'documents', 'reports', 'workflow_phases', 'workflow_activities', 
        'workflow_activity_dependencies', 'workflow_transitions', 'workflow_executions',
        'workflow_metrics', 'workflow_alerts', 'workflow_steps', 'workflow_activity_templates',
        'test_execution_phases', 'test_executions', 'test_report_phases', 'test_report_sections',
        'test_result_reviews', 'test_comparisons', 'sample_selection_phases', 'sample_sets',
        'sample_records', 'sample_validation_results', 'sample_validation_issues', 'samples',
        'observation_management_phases', 'observation_groups', 'observations', 
        'observation_records', 'observation_clarifications', 'observation_approvals',
        'observation_resolutions', 'observation_impact_assessments', 'data_profiling_phases',
        'data_profiling_files', 'profiling_rules', 'profiling_results', 'profiling_jobs',
        'profiling_executions', 'profiling_rule_sets', 'profiling_anomaly_patterns',
        'data_queries', 'data_sources', 'attribute_mappings', 'secure_data_access_logs',
        'document_access_logs', 'document_extractions', 'document_revisions', 
        'document_analyses', 'request_info_phases', 'scoping_submissions', 
        'tester_scoping_decisions', 'report_owner_scoping_reviews', 
        'attribute_scoping_recommendations', 'cycle_report_attributes_planning',
        'attribute_version_change_logs', 'attribute_version_comparisons',
        'attribute_profiling_scores', 'universal_assignments', 'sla_configurations',
        'sla_escalation_rules', 'data_owner_sla_violations', 'metrics_phases',
        'metrics_execution', 'llm_sample_generations', 'intelligent_samples',
        'intelligent_sampling_jobs', 'database_tests', 'bulk_test_executions',
        'historical_data_owner_assignments', 'escalation_email_logs', 'sampling_rules'
    ];
BEGIN
    FOREACH tbl IN ARRAY tables_to_update
    LOOP
        -- Check if table exists before trying to add columns
        IF EXISTS (
            SELECT 1 FROM information_schema.tables t
            WHERE t.table_schema = 'public' 
            AND t.table_name = tbl
        ) THEN
            PERFORM add_audit_columns_to_table(tbl);
        ELSE
            RAISE NOTICE 'Table % does not exist, skipping', tbl;
        END IF;
    END LOOP;
END $$;

-- Drop the function
DROP FUNCTION add_audit_columns_to_table(TEXT);

-- Verify the results
SELECT 
    'Tables with audit columns' as status,
    COUNT(*) as count
FROM information_schema.columns 
WHERE table_schema = 'public' 
AND column_name = 'created_by_id'
AND table_name NOT IN ('users', 'alembic_version');

COMMIT;