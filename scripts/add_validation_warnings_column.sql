-- Add validation_warnings column to cycle_report_rfi_query_validations table
-- This column stores helpful warnings about query validation (e.g., suggestions for column aliases)

ALTER TABLE cycle_report_rfi_query_validations 
ADD COLUMN IF NOT EXISTS validation_warnings JSONB;

-- Add comment for documentation
COMMENT ON COLUMN cycle_report_rfi_query_validations.validation_warnings IS 
'Array of validation warnings to help users improve their queries (e.g., column alias suggestions)';