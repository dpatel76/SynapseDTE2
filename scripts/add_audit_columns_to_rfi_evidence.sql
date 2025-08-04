-- Add missing audit columns to cycle_report_rfi_evidence table

-- Add created_by_id column if it doesn't exist
ALTER TABLE cycle_report_rfi_evidence 
ADD COLUMN IF NOT EXISTS created_by_id INTEGER REFERENCES users(user_id);

-- Add updated_by_id column if it doesn't exist
ALTER TABLE cycle_report_rfi_evidence 
ADD COLUMN IF NOT EXISTS updated_by_id INTEGER REFERENCES users(user_id);

-- Update the new columns with values from the old columns if they exist
UPDATE cycle_report_rfi_evidence 
SET created_by_id = created_by 
WHERE created_by_id IS NULL AND created_by IS NOT NULL;

UPDATE cycle_report_rfi_evidence 
SET updated_by_id = updated_by 
WHERE updated_by_id IS NULL AND updated_by IS NOT NULL;