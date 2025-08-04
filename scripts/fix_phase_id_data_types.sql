-- Fix remaining phase_id data type inconsistencies
-- Convert all phase_id columns to integer to match workflow_phases.phase_id

-- First, check if these tables have any actual data
SELECT 'cycle_report_data_profiling_rule_versions' as table_name, COUNT(*) as row_count FROM cycle_report_data_profiling_rule_versions
UNION ALL
SELECT 'cycle_report_document_submissions', COUNT(*) FROM cycle_report_document_submissions
UNION ALL
SELECT 'cycle_report_observation_mgmt_audit_logs', COUNT(*) FROM cycle_report_observation_mgmt_audit_logs
UNION ALL
SELECT 'cycle_report_observation_mgmt_observation_records', COUNT(*) FROM cycle_report_observation_mgmt_observation_records
UNION ALL
SELECT 'cycle_report_planning_data_sources', COUNT(*) FROM cycle_report_planning_data_sources
UNION ALL
SELECT 'cycle_report_planning_pde_mappings', COUNT(*) FROM cycle_report_planning_pde_mappings
UNION ALL
SELECT 'cycle_report_request_info_audit_logs', COUNT(*) FROM cycle_report_request_info_audit_logs
UNION ALL
SELECT 'cycle_report_test_cases', COUNT(*) FROM cycle_report_test_cases
UNION ALL
SELECT 'cycle_report_test_report_sections', COUNT(*) FROM cycle_report_test_report_sections;

-- Convert UUID phase_id columns to integer
ALTER TABLE cycle_report_data_profiling_rule_versions 
ALTER COLUMN phase_id TYPE integer USING NULL;

ALTER TABLE cycle_report_document_submissions 
ALTER COLUMN phase_id TYPE integer USING NULL;

ALTER TABLE cycle_report_planning_data_sources 
ALTER COLUMN phase_id TYPE integer USING NULL;

ALTER TABLE cycle_report_planning_pde_mappings 
ALTER COLUMN phase_id TYPE integer USING NULL;

ALTER TABLE cycle_report_test_cases 
ALTER COLUMN phase_id TYPE integer USING NULL;

-- Convert VARCHAR phase_id columns to integer
-- For non-nullable columns, we need to handle differently
ALTER TABLE cycle_report_observation_mgmt_observation_records 
ALTER COLUMN phase_id TYPE integer USING CASE 
    WHEN phase_id ~ '^[0-9]+$' THEN phase_id::integer 
    ELSE 0  -- Default value since it's NOT NULL
END;

ALTER TABLE cycle_report_test_report_sections 
ALTER COLUMN phase_id TYPE integer USING CASE 
    WHEN phase_id ~ '^[0-9]+$' THEN phase_id::integer 
    ELSE 0  -- Default value since it's NOT NULL
END;

-- For nullable VARCHAR columns
ALTER TABLE cycle_report_observation_mgmt_audit_logs 
ALTER COLUMN phase_id TYPE integer USING CASE 
    WHEN phase_id ~ '^[0-9]+$' THEN phase_id::integer 
    ELSE NULL 
END;

ALTER TABLE cycle_report_request_info_audit_logs 
ALTER COLUMN phase_id TYPE integer USING CASE 
    WHEN phase_id ~ '^[0-9]+$' THEN phase_id::integer 
    ELSE NULL 
END;

-- Now add foreign key constraints for the corrected tables
DO $$
DECLARE
    table_names TEXT[] := ARRAY[
        'cycle_report_data_profiling_rule_versions',
        'cycle_report_document_submissions',
        'cycle_report_planning_data_sources',
        'cycle_report_planning_pde_mappings',
        'cycle_report_test_cases',
        'cycle_report_observation_mgmt_audit_logs',
        'cycle_report_observation_mgmt_observation_records',
        'cycle_report_request_info_audit_logs',
        'cycle_report_test_report_sections'
    ];
    table_name TEXT;
    constraint_name TEXT;
BEGIN
    FOREACH table_name IN ARRAY table_names
    LOOP
        constraint_name := 'fk_' || table_name || '_phase_id';
        
        BEGIN
            EXECUTE format('ALTER TABLE %I ADD CONSTRAINT %I FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id)', 
                          table_name, constraint_name);
            RAISE NOTICE 'Added constraint % to %', constraint_name, table_name;
        EXCEPTION 
            WHEN duplicate_object THEN
                RAISE NOTICE 'Constraint % already exists on %', constraint_name, table_name;
            WHEN OTHERS THEN
                RAISE NOTICE 'Error adding constraint % to %: %', constraint_name, table_name, SQLERRM;
        END;
    END LOOP;
END $$;

-- Final verification
SELECT 
    'Data Type Consistency Check' as status,
    COUNT(*) as total_phase_id_columns,
    COUNT(CASE WHEN data_type = 'integer' THEN 1 END) as integer_columns,
    COUNT(CASE WHEN data_type != 'integer' THEN 1 END) as non_integer_columns
FROM information_schema.columns 
WHERE column_name = 'phase_id' 
    AND table_schema = 'public' 
    AND table_name LIKE 'cycle_report_%';

-- Show any remaining inconsistencies
SELECT 
    table_name,
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE column_name = 'phase_id' 
    AND table_schema = 'public' 
    AND table_name LIKE 'cycle_report_%'
    AND data_type != 'integer'
ORDER BY table_name;

SELECT 'Phase ID data type consistency fix completed!' as message;