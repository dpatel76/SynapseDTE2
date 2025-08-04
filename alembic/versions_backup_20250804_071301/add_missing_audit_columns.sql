-- Migration: Add missing audit columns to tables using AuditMixin
-- This script adds created_by_id and updated_by_id columns to tables that should have them
-- based on their model definitions but might be missing them in the database

-- Start transaction
BEGIN;

-- Function to safely add audit columns
CREATE OR REPLACE FUNCTION add_audit_columns_if_missing(p_table_name TEXT) 
RETURNS VOID AS $$
DECLARE
    v_created_by_exists BOOLEAN;
    v_updated_by_exists BOOLEAN;
BEGIN
    -- Check if created_by_id exists
    SELECT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = p_table_name 
        AND column_name = 'created_by_id'
    ) INTO v_created_by_exists;
    
    -- Check if updated_by_id exists
    SELECT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = p_table_name 
        AND column_name = 'updated_by_id'
    ) INTO v_updated_by_exists;
    
    -- Add created_by_id if missing
    IF NOT v_created_by_exists THEN
        EXECUTE format('ALTER TABLE %I ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL', p_table_name);
        EXECUTE format('COMMENT ON COLUMN %I.created_by_id IS ''ID of user who created this record''', p_table_name);
        EXECUTE format('CREATE INDEX idx_%s_created_by ON %I(created_by_id)', p_table_name, p_table_name);
        RAISE NOTICE 'Added created_by_id to table %', p_table_name;
    END IF;
    
    -- Add updated_by_id if missing
    IF NOT v_updated_by_exists THEN
        EXECUTE format('ALTER TABLE %I ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL', p_table_name);
        EXECUTE format('COMMENT ON COLUMN %I.updated_by_id IS ''ID of user who last updated this record''', p_table_name);
        EXECUTE format('CREATE INDEX idx_%s_updated_by ON %I(updated_by_id)', p_table_name, p_table_name);
        RAISE NOTICE 'Added updated_by_id to table %', p_table_name;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Apply to all tables that use AuditMixin (based on model analysis)
-- Core models inheriting from CustomPKModel + AuditMixin
SELECT add_audit_columns_if_missing('reports');
SELECT add_audit_columns_if_missing('test_cycles');
SELECT add_audit_columns_if_missing('cycle_reports');
SELECT add_audit_columns_if_missing('documents');
SELECT add_audit_columns_if_missing('audit_logs');
SELECT add_audit_columns_if_missing('llm_audit_logs');

-- LOB model (inherits from AuditableCustomPKModel)
SELECT add_audit_columns_if_missing('lobs');

-- Data Owner phase models
SELECT add_audit_columns_if_missing('attribute_lob_assignments');
SELECT add_audit_columns_if_missing('historical_data_owner_assignments');
SELECT add_audit_columns_if_missing('data_owner_sla_violations');
SELECT add_audit_columns_if_missing('data_owner_escalation_logs');
SELECT add_audit_columns_if_missing('data_owner_phase_audit_logs');

-- Data Profiling models
SELECT add_audit_columns_if_missing('data_profiling_phases');
SELECT add_audit_columns_if_missing('data_profiling_files');
SELECT add_audit_columns_if_missing('profiling_rules');
SELECT add_audit_columns_if_missing('profiling_results');
SELECT add_audit_columns_if_missing('attribute_profiling_scores');
SELECT add_audit_columns_if_missing('profiling_jobs');
SELECT add_audit_columns_if_missing('profiling_rule_sets');
SELECT add_audit_columns_if_missing('profiling_anomaly_patterns');

-- Data Source models
SELECT add_audit_columns_if_missing('data_sources');
SELECT add_audit_columns_if_missing('attribute_mappings');
SELECT add_audit_columns_if_missing('data_queries');
SELECT add_audit_columns_if_missing('profiling_executions');
SELECT add_audit_columns_if_missing('secure_data_access');

-- Document models
SELECT add_audit_columns_if_missing('document_access_logs');
SELECT add_audit_columns_if_missing('document_extractions');

-- Metrics models
SELECT add_audit_columns_if_missing('metrics_phases');
SELECT add_audit_columns_if_missing('metrics_execution');

-- Observation models
SELECT add_audit_columns_if_missing('document_revisions');
SELECT add_audit_columns_if_missing('observation_groups');
SELECT add_audit_columns_if_missing('observations');
SELECT add_audit_columns_if_missing('observation_clarifications');
SELECT add_audit_columns_if_missing('test_report_phases');
SELECT add_audit_columns_if_missing('test_report_sections');
SELECT add_audit_columns_if_missing('observation_management_phases');
SELECT add_audit_columns_if_missing('observation_records');
SELECT add_audit_columns_if_missing('observation_impact_assessments');
SELECT add_audit_columns_if_missing('observation_approvals');
SELECT add_audit_columns_if_missing('observation_resolutions');
SELECT add_audit_columns_if_missing('observation_management_audit_logs');

-- RBAC models
SELECT add_audit_columns_if_missing('resources');
SELECT add_audit_columns_if_missing('permissions');
SELECT add_audit_columns_if_missing('roles');
SELECT add_audit_columns_if_missing('role_permissions');
SELECT add_audit_columns_if_missing('user_roles');
SELECT add_audit_columns_if_missing('user_permissions');
SELECT add_audit_columns_if_missing('resource_permissions');

-- Report models
SELECT add_audit_columns_if_missing('report_attributes');
SELECT add_audit_columns_if_missing('report_owner_assignments');
SELECT add_audit_columns_if_missing('report_owner_assignment_history');
SELECT add_audit_columns_if_missing('cycle_report_attributes_planning');

-- Request Info models
SELECT add_audit_columns_if_missing('request_info_phases');
SELECT add_audit_columns_if_missing('request_info_attributes');
SELECT add_audit_columns_if_missing('request_info_attachments');
SELECT add_audit_columns_if_missing('request_info_responses');
SELECT add_audit_columns_if_missing('request_info_response_attachments');
SELECT add_audit_columns_if_missing('request_info_templates');
SELECT add_audit_columns_if_missing('request_info_audit_logs');

-- Sample Selection models
SELECT add_audit_columns_if_missing('sample_sets');
SELECT add_audit_columns_if_missing('sample_records');
SELECT add_audit_columns_if_missing('sample_validation_results');
SELECT add_audit_columns_if_missing('sample_validation_issues');
SELECT add_audit_columns_if_missing('sample_approval_history');
SELECT add_audit_columns_if_missing('llm_sample_generations');
SELECT add_audit_columns_if_missing('sample_upload_history');
SELECT add_audit_columns_if_missing('sample_selection_phases');
SELECT add_audit_columns_if_missing('sample_selection_audit_logs');

-- Scoping models
SELECT add_audit_columns_if_missing('attribute_scoping_recommendations');
SELECT add_audit_columns_if_missing('tester_scoping_decisions');
SELECT add_audit_columns_if_missing('scoping_submissions');
SELECT add_audit_columns_if_missing('report_owner_scoping_reviews');
SELECT add_audit_columns_if_missing('scoping_audit_logs');

-- SLA models
SELECT add_audit_columns_if_missing('sla_configurations');
SELECT add_audit_columns_if_missing('sla_violations');

-- Test Execution models
SELECT add_audit_columns_if_missing('test_execution_phases');
SELECT add_audit_columns_if_missing('test_parameters');
SELECT add_audit_columns_if_missing('test_scripts');
SELECT add_audit_columns_if_missing('test_executions');
SELECT add_audit_columns_if_missing('test_results');
SELECT add_audit_columns_if_missing('test_result_details');
SELECT add_audit_columns_if_missing('test_exceptions');
SELECT add_audit_columns_if_missing('test_execution_audit_logs');
SELECT add_audit_columns_if_missing('samples');

-- Universal Assignment models
SELECT add_audit_columns_if_missing('universal_assignments');
SELECT add_audit_columns_if_missing('universal_assignment_history');

-- Versioned models
SELECT add_audit_columns_if_missing('data_profiling_rule_versions');
SELECT add_audit_columns_if_missing('test_execution_versions');
SELECT add_audit_columns_if_missing('observation_versions');
SELECT add_audit_columns_if_missing('scoping_decision_versions');
SELECT add_audit_columns_if_missing('versioned_attribute_scoping_recommendations');

-- Workflow models
SELECT add_audit_columns_if_missing('workflows');
SELECT add_audit_columns_if_missing('workflow_activities');
SELECT add_audit_columns_if_missing('workflow_phases');
SELECT add_audit_columns_if_missing('workflow_phase_transitions');
SELECT add_audit_columns_if_missing('workflow_tracking_events');

-- Clean up the function
DROP FUNCTION add_audit_columns_if_missing(TEXT);

-- Verify the migration
SELECT 
    t.table_name,
    CASE WHEN c1.column_name IS NOT NULL THEN '✓' ELSE '✗' END as has_created_by,
    CASE WHEN c2.column_name IS NOT NULL THEN '✓' ELSE '✗' END as has_updated_by
FROM information_schema.tables t
LEFT JOIN information_schema.columns c1 
    ON t.table_name = c1.table_name 
    AND t.table_schema = c1.table_schema 
    AND c1.column_name = 'created_by_id'
LEFT JOIN information_schema.columns c2 
    ON t.table_name = c2.table_name 
    AND t.table_schema = c2.table_schema 
    AND c2.column_name = 'updated_by_id'
WHERE t.table_schema = 'public'
AND t.table_type = 'BASE TABLE'
AND t.table_name NOT IN ('alembic_version', 'users')
AND t.table_name IN (
    'reports', 'test_cycles', 'cycle_reports', 'lobs', 'documents',
    'audit_logs', 'llm_audit_logs', 'attribute_lob_assignments',
    'historical_data_owner_assignments', 'data_owner_sla_violations',
    'data_owner_escalation_logs', 'data_owner_phase_audit_logs'
)
ORDER BY t.table_name;

COMMIT;