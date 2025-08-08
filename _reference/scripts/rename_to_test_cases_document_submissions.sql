-- Rename table to use plural "cases" for consistency
ALTER TABLE cycle_report_test_case_document_submissions 
RENAME TO cycle_report_test_cases_document_submissions;

-- Update the sequence name if it exists
ALTER SEQUENCE IF EXISTS cycle_report_document_submissions_id_seq 
RENAME TO cycle_report_test_cases_document_submissions_id_seq;

-- Show the renamed table
\d cycle_report_test_cases_document_submissions