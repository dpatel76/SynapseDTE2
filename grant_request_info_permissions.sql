-- Grant permissions on Request Info Evidence tables to the application user

-- Grant permissions on the versions table
GRANT ALL PRIVILEGES ON TABLE cycle_report_request_info_evidence_versions TO synapse_user;

-- Grant permissions on the evidence table
GRANT ALL PRIVILEGES ON TABLE cycle_report_request_info_evidence TO synapse_user;

-- Grant permissions on the view (if it exists)
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM pg_views WHERE viewname = 'cycle_report_request_info_latest_versions') THEN
        EXECUTE 'GRANT SELECT ON cycle_report_request_info_latest_versions TO synapse_user';
    END IF;
END $$;

-- Verify permissions
SELECT 
    tablename,
    tableowner,
    has_table_privilege('synapse_user', schemaname||'.'||tablename, 'SELECT') as select_perm,
    has_table_privilege('synapse_user', schemaname||'.'||tablename, 'INSERT') as insert_perm,
    has_table_privilege('synapse_user', schemaname||'.'||tablename, 'UPDATE') as update_perm,
    has_table_privilege('synapse_user', schemaname||'.'||tablename, 'DELETE') as delete_perm
FROM pg_tables 
WHERE tablename LIKE 'cycle_report_request_info%'
ORDER BY tablename;