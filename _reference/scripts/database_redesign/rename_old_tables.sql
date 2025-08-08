-- Rename old tables with _backup suffix

-- 1. Reports table (already migrated to report_inventory)
ALTER TABLE IF EXISTS reports RENAME TO reports_backup;

-- 2. Report attributes (will be replaced by cycle_report_attributes_planning)
ALTER TABLE IF EXISTS report_attributes RENAME TO report_attributes_backup;

-- 3. Test cases (will be replaced by cycle_report_test_cases)
ALTER TABLE IF EXISTS test_cases RENAME TO test_cases_backup;

-- 4. Document submissions (will be replaced by cycle_report_document_submissions)
ALTER TABLE IF EXISTS document_submissions RENAME TO document_submissions_backup;

-- 5. Data provider submissions (similar to document submissions)
ALTER TABLE IF EXISTS data_provider_submissions RENAME TO data_provider_submissions_backup;

-- 6. Database submissions
ALTER TABLE IF EXISTS database_submissions RENAME TO database_submissions_backup;

-- 7. Sample submissions
ALTER TABLE IF EXISTS sample_submissions RENAME TO sample_submissions_backup;

-- List the renamed tables
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name LIKE '%_backup'
ORDER BY table_name;

\echo 'Old tables renamed with _backup suffix'