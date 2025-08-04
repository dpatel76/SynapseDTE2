-- Rollback Migration: Revert cycle_report_test_cases_evidence to cycle_report_rfi_evidence
-- Description: Reverts the unified evidence table back to original structure
-- Date: 2025-07-30
-- Author: System Migration

-- IMPORTANT: Run this rollback with database owner/admin privileges

BEGIN;

-- Step 1: Check if rollback is needed
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'cycle_report_test_cases_evidence') THEN
        RAISE NOTICE 'Table cycle_report_test_cases_evidence does not exist. Rollback not needed.';
        -- You may want to stop here
    END IF;
END $$;

-- Step 2: Rename the table back
ALTER TABLE cycle_report_test_cases_evidence RENAME TO cycle_report_rfi_evidence;

-- Step 3: Rename data_owner_id back to submitted_by if it was changed
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name = 'cycle_report_rfi_evidence' 
               AND column_name = 'data_owner_id') THEN
        ALTER TABLE cycle_report_rfi_evidence 
        RENAME COLUMN data_owner_id TO submitted_by;
    END IF;
END $$;

-- Step 4: Drop the new columns that were added
ALTER TABLE cycle_report_rfi_evidence 
DROP COLUMN IF EXISTS submission_number,
DROP COLUMN IF EXISTS is_revision,
DROP COLUMN IF EXISTS revision_requested_by,
DROP COLUMN IF EXISTS revision_requested_at,
DROP COLUMN IF EXISTS revision_reason,
DROP COLUMN IF EXISTS revision_deadline,
DROP COLUMN IF EXISTS document_type;

-- Step 5: Drop the unique constraint
ALTER TABLE cycle_report_rfi_evidence
DROP CONSTRAINT IF EXISTS uq_test_case_evidence_submission_number;

-- Step 6: Drop the index
DROP INDEX IF EXISTS idx_unique_current_evidence;

-- Step 7: Rename constraints back
DO $$
BEGIN
    -- Rename primary key constraint
    IF EXISTS (SELECT 1 FROM information_schema.table_constraints 
               WHERE table_name = 'cycle_report_rfi_evidence' 
               AND constraint_name = 'cycle_report_test_cases_evidence_pkey') THEN
        ALTER TABLE cycle_report_rfi_evidence 
        RENAME CONSTRAINT cycle_report_test_cases_evidence_pkey TO cycle_report_rfi_evidence_pkey;
    END IF;
    
    -- Rename foreign key constraints
    IF EXISTS (SELECT 1 FROM information_schema.table_constraints 
               WHERE table_name = 'cycle_report_rfi_evidence' 
               AND constraint_name = 'cycle_report_test_cases_evidence_parent_evidence_id_fkey') THEN
        ALTER TABLE cycle_report_rfi_evidence
        RENAME CONSTRAINT cycle_report_test_cases_evidence_parent_evidence_id_fkey 
        TO cycle_report_rfi_evidence_parent_evidence_id_fkey;
    END IF;
END $$;

-- Step 8: Rename sequence back
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.sequences 
               WHERE sequence_name = 'cycle_report_test_cases_evidence_id_seq') THEN
        ALTER SEQUENCE cycle_report_test_cases_evidence_id_seq 
        RENAME TO cycle_report_rfi_evidence_id_seq;
    END IF;
END $$;

-- Step 9: Update sequence ownership
DO $$
BEGIN
    ALTER SEQUENCE cycle_report_rfi_evidence_id_seq 
    OWNED BY cycle_report_rfi_evidence.id;
EXCEPTION
    WHEN undefined_object THEN
        NULL; -- Sequence might not exist
END $$;

-- Step 10: Remove table comment
COMMENT ON TABLE cycle_report_rfi_evidence IS NULL;

-- Step 11: Drop the additional indexes
DROP INDEX IF EXISTS idx_evidence_test_case_id;
DROP INDEX IF EXISTS idx_evidence_phase_id;
DROP INDEX IF EXISTS idx_evidence_data_owner_id;
DROP INDEX IF EXISTS idx_evidence_evidence_type;
DROP INDEX IF EXISTS idx_evidence_created_at;

COMMIT;

-- Verification queries (run these after rollback)
/*
-- Check if table was renamed back
SELECT table_name 
FROM information_schema.tables 
WHERE table_name IN ('cycle_report_rfi_evidence', 'cycle_report_test_cases_evidence');

-- Check column structure
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'cycle_report_rfi_evidence'
ORDER BY ordinal_position;

-- Check constraints
SELECT constraint_name, constraint_type
FROM information_schema.table_constraints
WHERE table_name = 'cycle_report_rfi_evidence';
*/