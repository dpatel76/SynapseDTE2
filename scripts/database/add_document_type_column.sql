-- Add document_type column to cycle_report_test_cases_document_submissions table

-- First check if the enum type exists
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'document_type_enum') THEN
        CREATE TYPE document_type_enum AS ENUM (
            'Source Document',
            'Supporting Evidence',
            'Data Extract',
            'Query Result',
            'Other'
        );
    END IF;
END $$;

-- Add the column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'cycle_report_test_cases_document_submissions' 
        AND column_name = 'document_type'
    ) THEN
        ALTER TABLE cycle_report_test_cases_document_submissions 
        ADD COLUMN document_type document_type_enum NOT NULL DEFAULT 'Source Document';
        
        -- Remove the default after adding the column
        ALTER TABLE cycle_report_test_cases_document_submissions 
        ALTER COLUMN document_type DROP DEFAULT;
    END IF;
END $$;

-- Optional: Update existing records based on file extension or other criteria
-- UPDATE cycle_report_test_cases_document_submissions 
-- SET document_type = 'Data Extract' 
-- WHERE mime_type LIKE '%spreadsheet%' OR mime_type LIKE '%csv%';