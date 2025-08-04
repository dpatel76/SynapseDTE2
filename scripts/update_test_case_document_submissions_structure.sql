-- Update cycle_report_test_case_document_submissions table structure to match the model

-- Add missing columns
ALTER TABLE cycle_report_test_case_document_submissions
ADD COLUMN IF NOT EXISTS submission_id VARCHAR(36),
ADD COLUMN IF NOT EXISTS test_case_id INTEGER,
ADD COLUMN IF NOT EXISTS data_provider_id INTEGER,
ADD COLUMN IF NOT EXISTS original_filename VARCHAR(255),
ADD COLUMN IF NOT EXISTS stored_filename VARCHAR(255),
ADD COLUMN IF NOT EXISTS file_size_bytes INTEGER,
ADD COLUMN IF NOT EXISTS mime_type VARCHAR(100),
ADD COLUMN IF NOT EXISTS submission_notes TEXT,
ADD COLUMN IF NOT EXISTS submitted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS revision_number INTEGER DEFAULT 1,
ADD COLUMN IF NOT EXISTS parent_submission_id VARCHAR(36),
ADD COLUMN IF NOT EXISTS is_current BOOLEAN DEFAULT TRUE,
ADD COLUMN IF NOT EXISTS notes TEXT,
ADD COLUMN IF NOT EXISTS is_valid BOOLEAN DEFAULT TRUE,
ADD COLUMN IF NOT EXISTS validation_notes TEXT,
ADD COLUMN IF NOT EXISTS validated_by INTEGER,
ADD COLUMN IF NOT EXISTS validated_at TIMESTAMP WITH TIME ZONE;

-- Add foreign key constraints
ALTER TABLE cycle_report_test_case_document_submissions
ADD CONSTRAINT IF NOT EXISTS fk_test_case_id 
    FOREIGN KEY (test_case_id) REFERENCES cycle_report_test_cases(id),
ADD CONSTRAINT IF NOT EXISTS fk_data_provider_id 
    FOREIGN KEY (data_provider_id) REFERENCES users(user_id),
ADD CONSTRAINT IF NOT EXISTS fk_parent_submission_id 
    FOREIGN KEY (parent_submission_id) REFERENCES cycle_report_test_case_document_submissions(submission_id),
ADD CONSTRAINT IF NOT EXISTS fk_validated_by 
    FOREIGN KEY (validated_by) REFERENCES users(user_id);

-- Create unique index on submission_id
CREATE UNIQUE INDEX IF NOT EXISTS idx_submission_id 
    ON cycle_report_test_case_document_submissions(submission_id);

-- Make submission_id the primary key instead of id
-- First, drop the existing primary key
ALTER TABLE cycle_report_test_case_document_submissions 
    DROP CONSTRAINT IF EXISTS cycle_report_document_submissions_pkey;

-- Set submission_id as NOT NULL
UPDATE cycle_report_test_case_document_submissions 
    SET submission_id = gen_random_uuid()::text 
    WHERE submission_id IS NULL;

ALTER TABLE cycle_report_test_case_document_submissions
    ALTER COLUMN submission_id SET NOT NULL;

-- Add new primary key
ALTER TABLE cycle_report_test_case_document_submissions
    ADD PRIMARY KEY (submission_id);

-- Show the updated table structure
\d cycle_report_test_case_document_submissions