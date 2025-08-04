-- Rename test case document tables to be more descriptive
-- This script renames tables to clearly indicate they are for test case documents

-- 1. Rename cycle_report_document_submissions to cycle_report_test_case_document_submissions
ALTER TABLE IF EXISTS cycle_report_document_submissions 
RENAME TO cycle_report_test_case_document_submissions;

-- 2. Rename document_revisions to cycle_report_test_case_document_revisions
ALTER TABLE IF EXISTS document_revisions 
RENAME TO cycle_report_test_case_document_revisions;

-- 3. Rename document_revision_history to cycle_report_test_case_document_revision_history
ALTER TABLE IF EXISTS document_revision_history 
RENAME TO cycle_report_test_case_document_revision_history;

-- Update any indexes, constraints, etc. that might have the old table names
-- PostgreSQL should handle most of these automatically, but let's check

-- Show the renamed tables
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name LIKE '%test_case_document%'
ORDER BY table_name;