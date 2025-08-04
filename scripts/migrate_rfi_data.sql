-- Migrate existing RFI data to unified evidence table
-- This script migrates data from redundant tables to the new unified structure

BEGIN;

-- 1. Check if old tables exist and have data
DO $$
DECLARE
    doc_count INTEGER;
    evidence_count INTEGER;
    unified_count INTEGER;
BEGIN
    -- Check existing data counts
    SELECT COUNT(*) INTO doc_count FROM cycle_report_test_cases_document_submissions;
    SELECT COUNT(*) INTO evidence_count FROM cycle_report_request_info_testcase_source_evidence;
    SELECT COUNT(*) INTO unified_count FROM cycle_report_rfi_evidence;
    
    RAISE NOTICE 'Found % document submissions, % source evidence records, % unified evidence records', 
        doc_count, evidence_count, unified_count;
    
    -- Only proceed if we have data to migrate and unified table is empty or has less data
    IF (doc_count > 0 OR evidence_count > 0) AND unified_count < (doc_count + evidence_count) THEN
        RAISE NOTICE 'Proceeding with data migration...';
        
        -- 2. Migrate document submissions to unified table
        INSERT INTO cycle_report_rfi_evidence (
            test_case_id,
            phase_id,
            cycle_id,
            report_id,
            sample_id,
            evidence_type,
            version_number,
            is_current,
            submitted_by,
            submitted_at,
            submission_notes,
            validation_status,
            validation_notes,
            validated_by,
            validated_at,
            original_filename,
            stored_filename,
            file_path,
            file_size_bytes,
            file_hash,
            mime_type,
            created_at,
            updated_at,
            created_by,
            updated_by
        )
        SELECT 
            ds.test_case_id,
            ds.phase_id,
            wp.cycle_id,
            wp.report_id,
            tc.sample_id,
            'document' as evidence_type,
            ds.submission_number as version_number,
            ds.is_current,
            ds.data_owner_id as submitted_by,
            ds.submitted_at,
            ds.submission_notes,
            ds.validation_status,
            ds.validation_notes,
            ds.validated_by,
            ds.validated_at,
            ds.original_filename,
            ds.stored_filename,
            ds.file_path,
            ds.file_size_bytes,
            ds.file_hash,
            ds.mime_type,
            ds.created_at,
            ds.updated_at,
            COALESCE(ds.created_by, ds.data_owner_id),
            COALESCE(ds.updated_by, ds.data_owner_id)
        FROM cycle_report_test_cases_document_submissions ds
        JOIN cycle_report_test_cases tc ON ds.test_case_id = tc.id
        JOIN workflow_phases wp ON ds.phase_id = wp.phase_id
        WHERE NOT EXISTS (
            SELECT 1 FROM cycle_report_rfi_evidence e 
            WHERE e.test_case_id = ds.test_case_id 
            AND e.version_number = ds.submission_number
            AND e.evidence_type = 'document'
        );
        
        RAISE NOTICE 'Migrated document submissions';
        
        -- 3. Migrate source evidence to unified table
        INSERT INTO cycle_report_rfi_evidence (
            test_case_id,
            phase_id,
            cycle_id,
            report_id,
            sample_id,
            evidence_type,
            version_number,
            is_current,
            submitted_by,
            submitted_at,
            submission_notes,
            validation_status,
            validation_notes,
            validated_by,
            validated_at,
            original_filename,
            file_path,
            planning_data_source_id,
            query_text,
            query_parameters,
            created_at,
            updated_at,
            created_by,
            updated_by
        )
        SELECT 
            se.test_case_id,
            se.phase_id,
            wp.cycle_id,
            wp.report_id,
            se.sample_id,
            se.evidence_type,
            se.version_number,
            se.is_current,
            se.submitted_by,
            se.submitted_at,
            se.submission_notes,
            se.validation_status,
            se.validation_notes,
            se.validated_by,
            se.validated_at,
            se.document_name,
            se.document_path,
            se.data_source_id,
            se.query_text,
            se.query_parameters,
            se.created_at,
            se.updated_at,
            se.created_by,
            se.updated_by
        FROM cycle_report_request_info_testcase_source_evidence se
        JOIN workflow_phases wp ON se.phase_id = wp.phase_id
        WHERE NOT EXISTS (
            SELECT 1 FROM cycle_report_rfi_evidence e 
            WHERE e.test_case_id = se.test_case_id 
            AND e.evidence_type = se.evidence_type
            AND e.version_number = se.version_number
        );
        
        RAISE NOTICE 'Migrated source evidence';
        
        -- 4. Update parent evidence relationships
        UPDATE cycle_report_rfi_evidence e1
        SET parent_evidence_id = e2.id
        FROM cycle_report_rfi_evidence e2
        WHERE e1.test_case_id = e2.test_case_id
        AND e1.version_number = e2.version_number + 1
        AND e1.evidence_type = e2.evidence_type
        AND e1.parent_evidence_id IS NULL;
        
        RAISE NOTICE 'Updated parent evidence relationships';
        
    ELSE
        RAISE NOTICE 'No migration needed - either no source data or unified table already populated';
    END IF;
    
END $$;

COMMIT;