-- Drop obsolete document revision tables
-- Since we've consolidated all submission and revision tracking into cycle_report_test_cases_document_submissions

-- Drop cycle_report_document_revisions table
DROP TABLE IF EXISTS cycle_report_document_revisions CASCADE;

-- Also check and drop any other potential revision-related tables
DROP TABLE IF EXISTS cycle_report_test_case_document_revisions CASCADE;
DROP TABLE IF EXISTS cycle_report_test_case_document_revision_requests CASCADE;
DROP TABLE IF EXISTS cycle_report_test_case_document_revision_history CASCADE;
DROP TABLE IF EXISTS document_revisions CASCADE;
DROP TABLE IF EXISTS document_revision_history CASCADE;

-- List remaining document-related tables to confirm cleanup
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND (table_name LIKE '%document%' OR table_name LIKE '%revision%')
ORDER BY table_name;