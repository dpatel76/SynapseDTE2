-- Rename cycle_report_rfi_evidence to cycle_report_test_cases_evidence
-- and add missing fields from TestCaseDocumentSubmission

BEGIN;

-- 1. Rename the table
ALTER TABLE cycle_report_rfi_evidence RENAME TO cycle_report_test_cases_evidence;

-- 2. Add missing fields from TestCaseDocumentSubmission that aren't already in the evidence table
-- Most fields already exist, but we need to add these:

-- Submission tracking fields
ALTER TABLE cycle_report_test_cases_evidence 
ADD COLUMN IF NOT EXISTS submission_number INTEGER DEFAULT 1,
ADD COLUMN IF NOT EXISTS is_revision BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS revision_requested_by INTEGER REFERENCES users(user_id),
ADD COLUMN IF NOT EXISTS revision_requested_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS revision_reason TEXT,
ADD COLUMN IF NOT EXISTS revision_deadline TIMESTAMP WITH TIME ZONE;

-- Document type field (for document classification)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'cycle_report_test_cases_evidence' 
        AND column_name = 'document_type'
    ) THEN
        ALTER TABLE cycle_report_test_cases_evidence 
        ADD COLUMN document_type document_type_enum;
    END IF;
END $$;

-- Data owner field (rename submitted_by to data_owner_id for consistency)
ALTER TABLE cycle_report_test_cases_evidence 
RENAME COLUMN submitted_by TO data_owner_id;

-- Add unique constraint for submission number per test case
ALTER TABLE cycle_report_test_cases_evidence
ADD CONSTRAINT uq_test_case_evidence_submission_number 
UNIQUE (test_case_id, submission_number);

-- Add index for current evidence per test case
CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_current_evidence 
ON cycle_report_test_cases_evidence(test_case_id, is_current)
WHERE is_current = true;

-- 3. Rename constraints and indexes to match new table name
ALTER TABLE cycle_report_test_cases_evidence 
RENAME CONSTRAINT cycle_report_rfi_evidence_pkey TO cycle_report_test_cases_evidence_pkey;

-- Update foreign key constraints referencing this table
ALTER TABLE cycle_report_test_cases_evidence
RENAME CONSTRAINT cycle_report_rfi_evidence_parent_evidence_id_fkey 
TO cycle_report_test_cases_evidence_parent_evidence_id_fkey;

-- 4. Update sequences if any
-- The table uses Integer primary key with autoincrement, so update the sequence name
ALTER SEQUENCE IF EXISTS cycle_report_rfi_evidence_id_seq 
RENAME TO cycle_report_test_cases_evidence_id_seq;

-- 5. Add comment to table
COMMENT ON TABLE cycle_report_test_cases_evidence IS 
'Unified evidence table for test cases - stores both document and data source evidence';

COMMIT;