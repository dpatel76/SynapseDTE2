-- Migration: Rename cycle_report_rfi_evidence to cycle_report_test_cases_evidence
-- Description: Unifies document and data source evidence into a single table
-- Date: 2025-07-30
-- Author: System Migration

-- IMPORTANT: Run this migration with database owner/admin privileges

BEGIN;

-- Step 1: Check if migration has already been applied
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'cycle_report_test_cases_evidence') THEN
        RAISE NOTICE 'Table cycle_report_test_cases_evidence already exists. Migration may have been applied.';
        -- You may want to stop here or handle this case differently
    END IF;
END $$;

-- Step 2: Rename the table
ALTER TABLE cycle_report_rfi_evidence RENAME TO cycle_report_test_cases_evidence;

-- Step 3: Add new columns from document submissions if they don't exist
ALTER TABLE cycle_report_test_cases_evidence 
ADD COLUMN IF NOT EXISTS submission_number INTEGER DEFAULT 1,
ADD COLUMN IF NOT EXISTS is_revision BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS revision_requested_by INTEGER REFERENCES users(user_id),
ADD COLUMN IF NOT EXISTS revision_requested_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS revision_reason TEXT,
ADD COLUMN IF NOT EXISTS revision_deadline TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS document_type document_type_enum;

-- Step 4: Rename submitted_by to data_owner_id if it exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name = 'cycle_report_test_cases_evidence' 
               AND column_name = 'submitted_by') THEN
        ALTER TABLE cycle_report_test_cases_evidence 
        RENAME COLUMN submitted_by TO data_owner_id;
    END IF;
END $$;

-- Step 5: Add unique constraint for test_case_id and submission_number
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints 
                   WHERE table_name = 'cycle_report_test_cases_evidence' 
                   AND constraint_name = 'uq_test_case_evidence_submission_number') THEN
        ALTER TABLE cycle_report_test_cases_evidence
        ADD CONSTRAINT uq_test_case_evidence_submission_number 
        UNIQUE (test_case_id, submission_number);
    END IF;
END $$;

-- Step 6: Add index for current evidence
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_indexes 
                   WHERE tablename = 'cycle_report_test_cases_evidence' 
                   AND indexname = 'idx_unique_current_evidence') THEN
        CREATE UNIQUE INDEX idx_unique_current_evidence 
        ON cycle_report_test_cases_evidence(test_case_id, is_current)
        WHERE is_current = true;
    END IF;
END $$;

-- Step 7: Rename constraints
DO $$
BEGIN
    -- Rename primary key constraint
    IF EXISTS (SELECT 1 FROM information_schema.table_constraints 
               WHERE table_name = 'cycle_report_test_cases_evidence' 
               AND constraint_name = 'cycle_report_rfi_evidence_pkey') THEN
        ALTER TABLE cycle_report_test_cases_evidence 
        RENAME CONSTRAINT cycle_report_rfi_evidence_pkey TO cycle_report_test_cases_evidence_pkey;
    END IF;
    
    -- Rename foreign key constraints
    IF EXISTS (SELECT 1 FROM information_schema.table_constraints 
               WHERE table_name = 'cycle_report_test_cases_evidence' 
               AND constraint_name = 'cycle_report_rfi_evidence_parent_evidence_id_fkey') THEN
        ALTER TABLE cycle_report_test_cases_evidence
        RENAME CONSTRAINT cycle_report_rfi_evidence_parent_evidence_id_fkey 
        TO cycle_report_test_cases_evidence_parent_evidence_id_fkey;
    END IF;
    
    -- Update foreign key references from other tables
    IF EXISTS (SELECT 1 FROM information_schema.table_constraints 
               WHERE constraint_name LIKE '%cycle_report_rfi_evidence%' 
               AND table_name != 'cycle_report_test_cases_evidence') THEN
        RAISE NOTICE 'There may be foreign key references to the old table name that need updating';
    END IF;
END $$;

-- Step 8: Rename sequence
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.sequences 
               WHERE sequence_name = 'cycle_report_rfi_evidence_id_seq') THEN
        ALTER SEQUENCE cycle_report_rfi_evidence_id_seq 
        RENAME TO cycle_report_test_cases_evidence_id_seq;
    END IF;
END $$;

-- Step 9: Update sequence ownership if needed
DO $$
BEGIN
    -- Ensure the sequence is owned by the correct column
    ALTER SEQUENCE cycle_report_test_cases_evidence_id_seq 
    OWNED BY cycle_report_test_cases_evidence.id;
EXCEPTION
    WHEN undefined_object THEN
        NULL; -- Sequence might not exist or already be correctly owned
END $$;

-- Step 10: Add table comment
COMMENT ON TABLE cycle_report_test_cases_evidence IS 
'Unified evidence table for test cases - stores both document and data source evidence';

-- Step 11: Migrate any existing document submissions to the unified table
-- Only run if TestCaseDocumentSubmission table exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables 
               WHERE table_name = 'cycle_report_test_cases_document_submissions') THEN
        
        -- Insert document submissions that don't already exist in evidence table
        INSERT INTO cycle_report_test_cases_evidence (
            test_case_id, phase_id, cycle_id, report_id, sample_id,
            evidence_type, version_number, is_current,
            data_owner_id, submitted_at, submission_notes,
            submission_number, is_revision, 
            revision_requested_by, revision_requested_at,
            revision_reason, revision_deadline,
            validation_status, validation_notes,
            original_filename, stored_filename, file_path,
            file_size_bytes, file_hash, mime_type, document_type,
            created_at, updated_at, created_by, updated_by
        )
        SELECT 
            ds.test_case_id,
            tc.phase_id,
            tc.cycle_id,
            tc.report_id,
            tc.sample_id,
            'document' as evidence_type,
            ds.submission_number as version_number,
            true as is_current,
            ds.submitted_by as data_owner_id,
            ds.submitted_at,
            ds.submission_notes,
            ds.submission_number,
            ds.is_revision,
            ds.revision_requested_by,
            ds.revision_requested_at,
            ds.revision_reason,
            ds.revision_deadline,
            'pending' as validation_status,
            NULL as validation_notes,
            ds.original_filename,
            ds.stored_filename,
            ds.file_path,
            ds.file_size_bytes,
            ds.file_hash,
            ds.mime_type,
            ds.document_type,
            ds.created_at,
            ds.updated_at,
            ds.created_by,
            ds.updated_by
        FROM cycle_report_test_cases_document_submissions ds
        JOIN cycle_report_test_cases tc ON ds.test_case_id = tc.id
        WHERE NOT EXISTS (
            SELECT 1 FROM cycle_report_test_cases_evidence e
            WHERE e.test_case_id = ds.test_case_id
            AND e.evidence_type = 'document'
            AND e.original_filename = ds.original_filename
        );
        
        RAISE NOTICE 'Migrated document submissions to unified evidence table';
    END IF;
END $$;

-- Step 12: Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_evidence_test_case_id 
ON cycle_report_test_cases_evidence(test_case_id);

CREATE INDEX IF NOT EXISTS idx_evidence_phase_id 
ON cycle_report_test_cases_evidence(phase_id);

CREATE INDEX IF NOT EXISTS idx_evidence_data_owner_id 
ON cycle_report_test_cases_evidence(data_owner_id);

CREATE INDEX IF NOT EXISTS idx_evidence_evidence_type 
ON cycle_report_test_cases_evidence(evidence_type);

CREATE INDEX IF NOT EXISTS idx_evidence_created_at 
ON cycle_report_test_cases_evidence(created_at DESC);

-- Step 13: Grant appropriate permissions (adjust as needed)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON cycle_report_test_cases_evidence TO your_app_user;
-- GRANT USAGE, SELECT ON SEQUENCE cycle_report_test_cases_evidence_id_seq TO your_app_user;

COMMIT;

-- Verification queries (run these after migration)
/*
-- Check if table was renamed
SELECT table_name 
FROM information_schema.tables 
WHERE table_name IN ('cycle_report_rfi_evidence', 'cycle_report_test_cases_evidence');

-- Check column structure
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'cycle_report_test_cases_evidence'
ORDER BY ordinal_position;

-- Check constraints
SELECT constraint_name, constraint_type
FROM information_schema.table_constraints
WHERE table_name = 'cycle_report_test_cases_evidence';

-- Check indexes
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'cycle_report_test_cases_evidence';

-- Check data
SELECT evidence_type, COUNT(*) 
FROM cycle_report_test_cases_evidence 
GROUP BY evidence_type;
*/