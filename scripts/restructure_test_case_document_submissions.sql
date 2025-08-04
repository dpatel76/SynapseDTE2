-- Restructure cycle_report_test_cases_document_submissions table
-- This script normalizes the table and removes data_provider_id

-- First, add new columns if they don't exist
ALTER TABLE cycle_report_test_cases_document_submissions
ADD COLUMN IF NOT EXISTS submission_number INTEGER DEFAULT 1,
ADD COLUMN IF NOT EXISTS is_revision BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS revision_requested_by INTEGER REFERENCES users(user_id),
ADD COLUMN IF NOT EXISTS revision_requested_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS revision_reason TEXT,
ADD COLUMN IF NOT EXISTS revision_deadline TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS file_hash VARCHAR(64),
ADD COLUMN IF NOT EXISTS validation_status VARCHAR(50) DEFAULT 'pending';

-- Update column names for consistency
ALTER TABLE cycle_report_test_cases_document_submissions
RENAME COLUMN IF EXISTS is_valid TO validation_status_old;

-- Convert old is_valid boolean to new validation_status
UPDATE cycle_report_test_cases_document_submissions
SET validation_status = CASE 
    WHEN validation_status_old = true THEN 'passed'
    WHEN validation_status_old = false THEN 'failed'
    ELSE 'pending'
END
WHERE validation_status IS NULL OR validation_status = 'pending';

-- Drop the old column
ALTER TABLE cycle_report_test_cases_document_submissions
DROP COLUMN IF EXISTS validation_status_old;

-- Drop data_provider_id and its constraint as it's redundant with data_owner_id
ALTER TABLE cycle_report_test_cases_document_submissions
DROP CONSTRAINT IF EXISTS fk_data_provider_id;

ALTER TABLE cycle_report_test_cases_document_submissions
DROP COLUMN IF EXISTS data_provider_id;

-- Drop revision_number column (replaced by submission_number)
ALTER TABLE cycle_report_test_cases_document_submissions
DROP COLUMN IF EXISTS revision_number;

-- Drop notes column (replaced by submission_notes)
ALTER TABLE cycle_report_test_cases_document_submissions
DROP COLUMN IF EXISTS notes;

-- Add new foreign key for revision_requested_by if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'fk_revision_requested_by'
    ) THEN
        ALTER TABLE cycle_report_test_cases_document_submissions
        ADD CONSTRAINT fk_revision_requested_by 
        FOREIGN KEY (revision_requested_by) REFERENCES users(user_id);
    END IF;
END $$;

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_test_case_submissions_phase_id 
ON cycle_report_test_cases_document_submissions(phase_id);

CREATE INDEX IF NOT EXISTS idx_test_case_submissions_test_case_id 
ON cycle_report_test_cases_document_submissions(test_case_id);

CREATE INDEX IF NOT EXISTS idx_test_case_submissions_data_owner_id 
ON cycle_report_test_cases_document_submissions(data_owner_id);

CREATE INDEX IF NOT EXISTS idx_test_case_submissions_is_current 
ON cycle_report_test_cases_document_submissions(is_current);

-- Add unique constraint for stored_filename
ALTER TABLE cycle_report_test_cases_document_submissions
ADD CONSTRAINT uq_stored_filename UNIQUE (stored_filename);

-- Add the partial unique index for current submissions
CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_current_submission 
ON cycle_report_test_cases_document_submissions(test_case_id, is_current) 
WHERE is_current = true;

-- Add unique constraint for test_case_id and submission_number
ALTER TABLE cycle_report_test_cases_document_submissions
ADD CONSTRAINT uq_test_case_submission_number 
UNIQUE (test_case_id, submission_number);

-- Update submission_number for existing records based on their order
WITH numbered_submissions AS (
    SELECT submission_id,
           ROW_NUMBER() OVER (PARTITION BY test_case_id ORDER BY submitted_at) as new_submission_number
    FROM cycle_report_test_cases_document_submissions
)
UPDATE cycle_report_test_cases_document_submissions s
SET submission_number = ns.new_submission_number
FROM numbered_submissions ns
WHERE s.submission_id = ns.submission_id;

-- Set is_revision = true for submissions where submission_number > 1
UPDATE cycle_report_test_cases_document_submissions
SET is_revision = true
WHERE submission_number > 1;

-- Clean up duplicate columns
ALTER TABLE cycle_report_test_cases_document_submissions
DROP COLUMN IF EXISTS file_name,
DROP COLUMN IF EXISTS file_size,
DROP COLUMN IF EXISTS submission_date,
DROP COLUMN IF EXISTS version,
DROP COLUMN IF EXISTS status,
DROP COLUMN IF EXISTS document_type;

-- Show the final table structure
\d cycle_report_test_cases_document_submissions