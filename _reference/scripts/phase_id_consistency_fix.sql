-- Phase ID Consistency Fix Script
-- This script ensures consistent use of phase_id across all tables
-- and removes remaining redundant cycle_id/report_id columns

-- =============================================================================
-- PHASE 1: Fix data type inconsistencies
-- =============================================================================

-- First, let's standardize all phase_id columns to integer to match workflow_phases.phase_id
BEGIN;

-- Fix varchar phase_id columns to integer
ALTER TABLE cycle_report_test_report_sections 
ALTER COLUMN phase_id TYPE integer USING CASE 
    WHEN phase_id ~ '^[0-9]+$' THEN phase_id::integer 
    ELSE NULL 
END;

ALTER TABLE cycle_report_observation_mgmt_audit_logs 
ALTER COLUMN phase_id TYPE integer USING CASE 
    WHEN phase_id ~ '^[0-9]+$' THEN phase_id::integer 
    ELSE NULL 
END;

ALTER TABLE cycle_report_observation_mgmt_observation_records 
ALTER COLUMN phase_id TYPE integer USING CASE 
    WHEN phase_id ~ '^[0-9]+$' THEN phase_id::integer 
    ELSE NULL 
END;

ALTER TABLE cycle_report_request_info_audit_logs 
ALTER COLUMN phase_id TYPE integer USING CASE 
    WHEN phase_id ~ '^[0-9]+$' THEN phase_id::integer 
    ELSE NULL 
END;

-- Fix UUID phase_id columns to integer (these will be NULL since no data exists)
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

COMMIT;

-- =============================================================================
-- PHASE 2: Add foreign key constraints for standardized phase_id columns
-- =============================================================================

-- Add foreign key constraints, ignoring if they already exist
DO $$
DECLARE
    table_names TEXT[] := ARRAY[
        'cycle_report_data_profiling_rule_versions',
        'cycle_report_document_submissions',
        'cycle_report_planning_data_sources',
        'cycle_report_planning_pde_mappings',
        'cycle_report_test_cases',
        'cycle_report_test_report_sections',
        'cycle_report_observation_mgmt_audit_logs',
        'cycle_report_observation_mgmt_observation_records',
        'cycle_report_request_info_audit_logs'
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

-- =============================================================================
-- PHASE 3: Drop dependent views temporarily to remove cycle_id/report_id
-- =============================================================================

-- Drop dependent views
DROP VIEW IF EXISTS cycle_report_documents_by_test_case CASCADE;
DROP VIEW IF EXISTS cycle_report_documents_latest CASCADE;
DROP VIEW IF EXISTS cycle_report_required_documents CASCADE;

-- =============================================================================
-- PHASE 4: Remove remaining redundant cycle_id and report_id columns
-- =============================================================================

DO $$
DECLARE
    table_rec TEXT;
    tables_to_process TEXT[] := ARRAY[
        'cycle_report_data_profiling_rule_versions',
        'cycle_report_data_profiling_rules',
        'cycle_report_document_submissions',
        'cycle_report_documents',
        'cycle_report_observation_groups',
        'cycle_report_observation_mgmt_audit_logs',
        'cycle_report_observation_mgmt_observation_records',
        'cycle_report_observation_mgmt_preliminary_findings',
        'cycle_report_planning_attributes',
        'cycle_report_planning_data_sources',
        'cycle_report_planning_pde_mappings',
        'cycle_report_request_info_audit_logs',
        'cycle_report_request_info_testcase_source_evidence',
        'cycle_report_sample_selection_audit_logs',
        'cycle_report_sample_selection_samples',
        'cycle_report_scoping_attribute_recommendations_backup',
        'cycle_report_scoping_decision_versions',
        'cycle_report_scoping_decisions',
        'cycle_report_scoping_submissions',
        'cycle_report_test_cases',
        'cycle_report_test_execution_results'
    ];
BEGIN
    FOREACH table_rec IN ARRAY tables_to_process
    LOOP
        -- Check if table exists
        IF EXISTS (SELECT 1 FROM information_schema.tables 
                  WHERE table_name = table_rec AND table_schema = 'public') THEN
            
            -- Drop foreign key constraints first
            BEGIN
                EXECUTE format('ALTER TABLE %I DROP CONSTRAINT IF EXISTS %I_cycle_id_fkey', table_rec, table_rec);
            EXCEPTION WHEN OTHERS THEN
                -- Ignore errors
            END;

            BEGIN
                EXECUTE format('ALTER TABLE %I DROP CONSTRAINT IF EXISTS %I_report_id_fkey', table_rec, table_rec);
            EXCEPTION WHEN OTHERS THEN
                -- Ignore errors
            END;

            -- Drop the columns if they exist
            IF EXISTS (SELECT 1 FROM information_schema.columns 
                      WHERE table_name = table_rec AND column_name = 'cycle_id' AND table_schema = 'public') THEN
                EXECUTE format('ALTER TABLE %I DROP COLUMN cycle_id', table_rec);
                RAISE NOTICE 'Dropped cycle_id column from %', table_rec;
            END IF;
            
            IF EXISTS (SELECT 1 FROM information_schema.columns 
                      WHERE table_name = table_rec AND column_name = 'report_id' AND table_schema = 'public') THEN
                EXECUTE format('ALTER TABLE %I DROP COLUMN report_id', table_rec);
                RAISE NOTICE 'Dropped report_id column from %', table_rec;
            END IF;
            
        ELSE
            RAISE NOTICE 'Table % does not exist, skipping', table_rec;
        END IF;
    END LOOP;
END $$;

-- =============================================================================
-- PHASE 5: Recreate views using only phase_id
-- =============================================================================

-- Recreate cycle_report_documents_latest view (phase_id only)
CREATE VIEW cycle_report_documents_latest AS
SELECT 
    id,
    phase_id,
    document_type,
    document_category,
    original_filename,
    stored_filename,
    file_path,
    file_size,
    file_format,
    mime_type,
    file_hash,
    document_title,
    document_description,
    document_version,
    is_latest_version,
    parent_document_id,
    access_level,
    allowed_roles,
    allowed_users,
    upload_status,
    processing_status,
    validation_status,
    content_preview,
    content_summary,
    extracted_metadata,
    search_keywords,
    validation_errors,
    validation_warnings,
    quality_score,
    download_count,
    last_downloaded_at,
    last_downloaded_by,
    view_count,
    last_viewed_at,
    last_viewed_by,
    workflow_stage,
    required_for_completion,
    approval_required,
    approved_by,
    approved_at,
    approval_notes,
    retention_period_days,
    archive_date,
    delete_date,
    is_archived,
    archived_at,
    archived_by,
    uploaded_by,
    uploaded_at,
    created_at,
    updated_at,
    created_by,
    updated_by
FROM cycle_report_documents 
WHERE is_latest_version = true AND is_archived = false;

-- Recreate cycle_report_documents_by_test_case view (phase_id only)
CREATE VIEW cycle_report_documents_by_test_case AS
SELECT 
    phase_id,
    test_case_id,
    document_type,
    COUNT(*) AS document_count,
    SUM(file_size) AS total_size_bytes,
    COUNT(CASE 
        WHEN upload_status IN ('uploaded', 'processed') THEN 1 
        ELSE NULL 
    END) AS uploaded_count,
    COUNT(CASE 
        WHEN is_latest_version = true THEN 1 
        ELSE NULL 
    END) AS latest_version_count
FROM cycle_report_documents 
WHERE test_case_id IS NOT NULL AND is_archived = false
GROUP BY phase_id, test_case_id, document_type;

-- Recreate cycle_report_required_documents view (phase_id only)
CREATE VIEW cycle_report_required_documents AS
SELECT 
    phase_id,
    document_type,
    COUNT(*) AS document_count,
    COUNT(CASE 
        WHEN upload_status IN ('uploaded', 'processed') THEN 1 
        ELSE NULL 
    END) AS uploaded_count,
    COUNT(CASE 
        WHEN validation_status = 'valid' THEN 1 
        ELSE NULL 
    END) AS valid_count,
    CASE 
        WHEN COUNT(*) = COUNT(CASE WHEN upload_status IN ('uploaded', 'processed') THEN 1 ELSE NULL END) 
        THEN 'complete'
        ELSE 'incomplete'
    END AS completion_status
FROM cycle_report_documents 
WHERE required_for_completion = true 
    AND is_latest_version = true 
    AND is_archived = false
GROUP BY phase_id, document_type;

-- =============================================================================
-- VERIFICATION
-- =============================================================================

-- Final verification of consistency
SELECT 
    'Phase ID Consistency Check' as status,
    COUNT(*) as total_cycle_report_tables,
    COUNT(CASE WHEN has_phase_id = '✓' AND has_cycle_id = '✗' AND has_report_id = '✗' THEN 1 END) as phase_id_only_tables,
    COUNT(CASE WHEN has_phase_id = '✓' AND (has_cycle_id = '✓' OR has_report_id = '✓') THEN 1 END) as mixed_tables,
    COUNT(CASE WHEN has_phase_id = '✗' THEN 1 END) as no_phase_id_tables
FROM (
    SELECT 
        t.table_name,
        CASE WHEN c1.column_name IS NOT NULL THEN '✓' ELSE '✗' END as has_phase_id,
        CASE WHEN c2.column_name IS NOT NULL THEN '✓' ELSE '✗' END as has_cycle_id,
        CASE WHEN c3.column_name IS NOT NULL THEN '✓' ELSE '✗' END as has_report_id
    FROM information_schema.tables t
    LEFT JOIN information_schema.columns c1 ON t.table_name = c1.table_name 
        AND c1.column_name = 'phase_id' AND c1.table_schema = 'public'
    LEFT JOIN information_schema.columns c2 ON t.table_name = c2.table_name 
        AND c2.column_name = 'cycle_id' AND c2.table_schema = 'public'
    LEFT JOIN information_schema.columns c3 ON t.table_name = c3.table_name 
        AND c3.column_name = 'report_id' AND c3.table_schema = 'public'
    WHERE t.table_schema = 'public' 
        AND t.table_type = 'BASE TABLE'
        AND t.table_name LIKE 'cycle_report_%'
) subquery;

-- Show remaining inconsistencies
SELECT 
    t.table_name,
    CASE WHEN c1.column_name IS NOT NULL THEN '✓' ELSE '✗' END as has_phase_id,
    CASE WHEN c2.column_name IS NOT NULL THEN '✓' ELSE '✗' END as has_cycle_id,
    CASE WHEN c3.column_name IS NOT NULL THEN '✓' ELSE '✗' END as has_report_id,
    c1.data_type as phase_id_type
FROM information_schema.tables t
LEFT JOIN information_schema.columns c1 ON t.table_name = c1.table_name 
    AND c1.column_name = 'phase_id' AND c1.table_schema = 'public'
LEFT JOIN information_schema.columns c2 ON t.table_name = c2.table_name 
    AND c2.column_name = 'cycle_id' AND c2.table_schema = 'public'
LEFT JOIN information_schema.columns c3 ON t.table_name = c3.table_name 
    AND c3.column_name = 'report_id' AND c3.table_schema = 'public'
WHERE t.table_schema = 'public' 
    AND t.table_type = 'BASE TABLE'
    AND t.table_name LIKE 'cycle_report_%'
    AND (c1.column_name IS NOT NULL OR c2.column_name IS NOT NULL OR c3.column_name IS NOT NULL)
ORDER BY 
    CASE WHEN c1.column_name IS NOT NULL AND c2.column_name IS NULL AND c3.column_name IS NULL THEN 1
         WHEN c1.column_name IS NOT NULL AND (c2.column_name IS NOT NULL OR c3.column_name IS NOT NULL) THEN 2
         ELSE 3
    END,
    t.table_name;

SELECT 'Phase ID consistency fix completed!' as message;