-- Comprehensive SQL script to verify and add missing audit columns
-- This script checks all tables that use AuditMixin in the models and ensures they have the audit columns

-- First, let's check which tables are missing the audit columns
WITH audit_tables AS (
    SELECT DISTINCT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_type = 'BASE TABLE'
    AND table_name NOT IN ('alembic_version', 'users') -- Exclude system and users table
),
existing_audit_columns AS (
    SELECT 
        table_name,
        MAX(CASE WHEN column_name = 'created_by_id' THEN 1 ELSE 0 END) as has_created_by,
        MAX(CASE WHEN column_name = 'updated_by_id' THEN 1 ELSE 0 END) as has_updated_by
    FROM information_schema.columns
    WHERE table_schema = 'public'
    AND column_name IN ('created_by_id', 'updated_by_id')
    GROUP BY table_name
)
SELECT 
    a.table_name,
    COALESCE(e.has_created_by, 0) as has_created_by,
    COALESCE(e.has_updated_by, 0) as has_updated_by,
    CASE 
        WHEN COALESCE(e.has_created_by, 0) = 0 OR COALESCE(e.has_updated_by, 0) = 0 
        THEN 'MISSING AUDIT COLUMNS'
        ELSE 'OK'
    END as status
FROM audit_tables a
LEFT JOIN existing_audit_columns e ON a.table_name = e.table_name
WHERE a.table_name IN (
    -- Core tables that use AuditMixin based on the models
    'reports',
    'test_cycles',
    'cycle_reports',
    'lobs',
    'documents',
    'audit_logs',
    'llm_audit_logs',
    'attribute_lob_assignments',
    'historical_data_owner_assignments',
    'data_owner_sla_violations',
    'data_owner_escalation_logs',
    'data_owner_phase_audit_logs',
    'data_profiling_phases',
    'data_profiling_files',
    'profiling_rules',
    'profiling_results',
    'attribute_profiling_scores',
    'data_sources',
    'attribute_mappings',
    'data_queries',
    'profiling_executions',
    'secure_data_access',
    'document_access_logs',
    'document_extractions',
    'metrics_phases',
    'metrics_execution',
    'document_revisions',
    'observation_groups',
    'observations',
    'observation_clarifications',
    'test_report_phases',
    'test_report_sections',
    'observation_management_phases',
    'observation_records',
    'observation_impact_assessments',
    'observation_approvals',
    'observation_resolutions',
    'observation_management_audit_logs',
    'profiling_jobs',
    'profiling_rule_sets',
    'profiling_anomaly_patterns',
    'resources',
    'permissions',
    'roles',
    'role_permissions',
    'user_roles',
    'user_permissions',
    'resource_permissions',
    'report_attributes',
    'report_owner_assignments',
    'report_owner_assignment_history',
    'request_info_phases',
    'request_info_attributes',
    'request_info_attachments',
    'request_info_responses',
    'request_info_response_attachments',
    'request_info_templates',
    'request_info_audit_logs',
    'sample_sets',
    'sample_records',
    'sample_validation_results',
    'sample_validation_issues',
    'sample_approval_history',
    'llm_sample_generations',
    'sample_upload_history',
    'sample_selection_phases',
    'sample_selection_audit_logs',
    'attribute_scoping_recommendations',
    'tester_scoping_decisions',
    'scoping_submissions',
    'report_owner_scoping_reviews',
    'scoping_audit_logs',
    'sla_configurations',
    'sla_violations',
    'test_execution_phases',
    'test_parameters',
    'test_scripts',
    'test_executions',
    'test_results',
    'test_result_details',
    'test_exceptions',
    'test_execution_audit_logs',
    'universal_assignments',
    'universal_assignment_history',
    'data_profiling_rule_versions',
    'test_execution_versions',
    'observation_versions',
    'scoping_decision_versions',
    'versioned_attribute_scoping_recommendations',
    'workflows',
    'workflow_activities',
    'workflow_phases',
    'workflow_phase_transitions',
    'workflow_tracking_events',
    'cycle_report_attributes_planning'
)
ORDER BY 
    CASE 
        WHEN COALESCE(e.has_created_by, 0) = 0 OR COALESCE(e.has_updated_by, 0) = 0 
        THEN 0 
        ELSE 1 
    END,
    a.table_name;

-- Now generate the ALTER TABLE statements for tables missing audit columns
-- This will create the SQL commands needed to add the missing columns

SELECT 
    '-- Adding audit columns to table: ' || table_name || E'\n' ||
    CASE 
        WHEN has_created_by = 0 THEN 
            'ALTER TABLE ' || table_name || ' ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;' || E'\n' ||
            'CREATE INDEX idx_' || table_name || '_created_by ON ' || table_name || '(created_by_id);' || E'\n'
        ELSE ''
    END ||
    CASE 
        WHEN has_updated_by = 0 THEN 
            'ALTER TABLE ' || table_name || ' ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;' || E'\n' ||
            'CREATE INDEX idx_' || table_name || '_updated_by ON ' || table_name || '(updated_by_id);' || E'\n'
        ELSE ''
    END as sql_commands
FROM (
    SELECT 
        a.table_name,
        COALESCE(e.has_created_by, 0) as has_created_by,
        COALESCE(e.has_updated_by, 0) as has_updated_by
    FROM (
        SELECT DISTINCT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_type = 'BASE TABLE'
        AND table_name NOT IN ('alembic_version', 'users')
    ) a
    LEFT JOIN (
        SELECT 
            table_name,
            MAX(CASE WHEN column_name = 'created_by_id' THEN 1 ELSE 0 END) as has_created_by,
            MAX(CASE WHEN column_name = 'updated_by_id' THEN 1 ELSE 0 END) as has_updated_by
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND column_name IN ('created_by_id', 'updated_by_id')
        GROUP BY table_name
    ) e ON a.table_name = e.table_name
) audit_check
WHERE (has_created_by = 0 OR has_updated_by = 0)
AND table_name IN (
    -- Same list of core tables as above
    'reports',
    'test_cycles',
    'cycle_reports',
    'lobs',
    'documents',
    'audit_logs',
    'llm_audit_logs',
    'attribute_lob_assignments',
    'historical_data_owner_assignments',
    'data_owner_sla_violations',
    'data_owner_escalation_logs',
    'data_owner_phase_audit_logs',
    'data_profiling_phases',
    'data_profiling_files',
    'profiling_rules',
    'profiling_results',
    'attribute_profiling_scores',
    'data_sources',
    'attribute_mappings',
    'data_queries',
    'profiling_executions',
    'secure_data_access',
    'document_access_logs',
    'document_extractions',
    'metrics_phases',
    'metrics_execution',
    'document_revisions',
    'observation_groups',
    'observations',
    'observation_clarifications',
    'test_report_phases',
    'test_report_sections',
    'observation_management_phases',
    'observation_records',
    'observation_impact_assessments',
    'observation_approvals',
    'observation_resolutions',
    'observation_management_audit_logs',
    'profiling_jobs',
    'profiling_rule_sets',
    'profiling_anomaly_patterns',
    'resources',
    'permissions',
    'roles',
    'role_permissions',
    'user_roles',
    'user_permissions',
    'resource_permissions',
    'report_attributes',
    'report_owner_assignments',
    'report_owner_assignment_history',
    'request_info_phases',
    'request_info_attributes',
    'request_info_attachments',
    'request_info_responses',
    'request_info_response_attachments',
    'request_info_templates',
    'request_info_audit_logs',
    'sample_sets',
    'sample_records',
    'sample_validation_results',
    'sample_validation_issues',
    'sample_approval_history',
    'llm_sample_generations',
    'sample_upload_history',
    'sample_selection_phases',
    'sample_selection_audit_logs',
    'attribute_scoping_recommendations',
    'tester_scoping_decisions',
    'scoping_submissions',
    'report_owner_scoping_reviews',
    'scoping_audit_logs',
    'sla_configurations',
    'sla_violations',
    'test_execution_phases',
    'test_parameters',
    'test_scripts',
    'test_executions',
    'test_results',
    'test_result_details',
    'test_exceptions',
    'test_execution_audit_logs',
    'universal_assignments',
    'universal_assignment_history',
    'data_profiling_rule_versions',
    'test_execution_versions',
    'observation_versions',
    'scoping_decision_versions',
    'versioned_attribute_scoping_recommendations',
    'workflows',
    'workflow_activities',
    'workflow_phases',
    'workflow_phase_transitions',
    'workflow_tracking_events',
    'cycle_report_attributes_planning'
)
ORDER BY table_name;

-- Additionally, let's create a single transaction script to add all missing columns
-- This can be executed as a single operation

BEGIN;

DO $$
DECLARE
    r RECORD;
    v_sql TEXT;
BEGIN
    FOR r IN 
        SELECT 
            a.table_name,
            COALESCE(e.has_created_by, 0) as has_created_by,
            COALESCE(e.has_updated_by, 0) as has_updated_by
        FROM (
            SELECT DISTINCT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            AND table_name NOT IN ('alembic_version', 'users')
            AND table_name IN (
                'reports', 'test_cycles', 'cycle_reports', 'lobs', 'documents',
                'audit_logs', 'llm_audit_logs', 'attribute_lob_assignments',
                'historical_data_owner_assignments', 'data_owner_sla_violations',
                'data_owner_escalation_logs', 'data_owner_phase_audit_logs',
                'data_profiling_phases', 'data_profiling_files', 'profiling_rules',
                'profiling_results', 'attribute_profiling_scores', 'data_sources',
                'attribute_mappings', 'data_queries', 'profiling_executions',
                'secure_data_access', 'document_access_logs', 'document_extractions',
                'metrics_phases', 'metrics_execution', 'document_revisions',
                'observation_groups', 'observations', 'observation_clarifications',
                'test_report_phases', 'test_report_sections',
                'observation_management_phases', 'observation_records',
                'observation_impact_assessments', 'observation_approvals',
                'observation_resolutions', 'observation_management_audit_logs',
                'profiling_jobs', 'profiling_rule_sets', 'profiling_anomaly_patterns',
                'resources', 'permissions', 'roles', 'role_permissions',
                'user_roles', 'user_permissions', 'resource_permissions',
                'report_attributes', 'report_owner_assignments',
                'report_owner_assignment_history', 'request_info_phases',
                'request_info_attributes', 'request_info_attachments',
                'request_info_responses', 'request_info_response_attachments',
                'request_info_templates', 'request_info_audit_logs',
                'sample_sets', 'sample_records', 'sample_validation_results',
                'sample_validation_issues', 'sample_approval_history',
                'llm_sample_generations', 'sample_upload_history',
                'sample_selection_phases', 'sample_selection_audit_logs',
                'attribute_scoping_recommendations', 'tester_scoping_decisions',
                'scoping_submissions', 'report_owner_scoping_reviews',
                'scoping_audit_logs', 'sla_configurations', 'sla_violations',
                'test_execution_phases', 'test_parameters', 'test_scripts',
                'test_executions', 'test_results', 'test_result_details',
                'test_exceptions', 'test_execution_audit_logs',
                'universal_assignments', 'universal_assignment_history',
                'data_profiling_rule_versions', 'test_execution_versions',
                'observation_versions', 'scoping_decision_versions',
                'versioned_attribute_scoping_recommendations', 'workflows',
                'workflow_activities', 'workflow_phases', 'workflow_phase_transitions',
                'workflow_tracking_events', 'cycle_report_attributes_planning'
            )
        ) a
        LEFT JOIN (
            SELECT 
                table_name,
                MAX(CASE WHEN column_name = 'created_by_id' THEN 1 ELSE 0 END) as has_created_by,
                MAX(CASE WHEN column_name = 'updated_by_id' THEN 1 ELSE 0 END) as has_updated_by
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND column_name IN ('created_by_id', 'updated_by_id')
            GROUP BY table_name
        ) e ON a.table_name = e.table_name
        WHERE (COALESCE(e.has_created_by, 0) = 0 OR COALESCE(e.has_updated_by, 0) = 0)
    LOOP
        -- Add created_by_id if missing
        IF r.has_created_by = 0 THEN
            v_sql := 'ALTER TABLE ' || r.table_name || ' ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL';
            EXECUTE v_sql;
            
            v_sql := 'CREATE INDEX idx_' || r.table_name || '_created_by ON ' || r.table_name || '(created_by_id)';
            EXECUTE v_sql;
            
            RAISE NOTICE 'Added created_by_id to table %', r.table_name;
        END IF;
        
        -- Add updated_by_id if missing
        IF r.has_updated_by = 0 THEN
            v_sql := 'ALTER TABLE ' || r.table_name || ' ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL';
            EXECUTE v_sql;
            
            v_sql := 'CREATE INDEX idx_' || r.table_name || '_updated_by ON ' || r.table_name || '(updated_by_id)';
            EXECUTE v_sql;
            
            RAISE NOTICE 'Added updated_by_id to table %', r.table_name;
        END IF;
    END LOOP;
END;
$$;

COMMIT;

-- Verify the results
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
AND column_name IN ('created_by_id', 'updated_by_id')
AND table_name IN (
    'reports', 'test_cycles', 'cycle_reports', 'lobs', 'documents'
)
ORDER BY table_name, column_name;