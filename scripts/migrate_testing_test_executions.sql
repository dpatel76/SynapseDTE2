-- Migration script to remove testing_test_executions table
-- and update all references to use test_executions

-- Step 1: Check current data
SELECT 'Data in testing_test_executions:' as info, COUNT(*) as count FROM testing_test_executions;
SELECT 'Data in test_executions:' as info, COUNT(*) as count FROM cycle_report_test_execution_test_executions;

-- Step 2: Backup the testing_test_executions table
CREATE TABLE IF NOT EXISTS testing_test_executions_backup AS 
SELECT * FROM testing_test_executions;

-- Step 3: Drop the existing test_executions table (it seems to have different structure)
DROP TABLE IF EXISTS test_executions CASCADE;

-- Step 4: Rename testing_test_executions to test_executions
ALTER TABLE testing_test_executions RENAME TO test_executions;

-- Step 5: Update all foreign key constraints
-- 5.1 Drop old constraints
ALTER TABLE test_result_reviews 
DROP CONSTRAINT IF EXISTS test_result_reviews_execution_id_fkey;

ALTER TABLE cycle_report_observation_mgmt_observation_records_backup 
DROP CONSTRAINT IF EXISTS observation_records_source_test_execution_id_fkey;

ALTER TABLE cycle_report_observation_mgmt_audit_logs 
DROP CONSTRAINT IF EXISTS observation_management_audit_logs_source_test_execution_id_fkey;

ALTER TABLE cycle_report_observation_mgmt_observation_records 
DROP CONSTRAINT IF EXISTS observation_records_source_test_execution_id_fkey1;

-- 5.2 Recreate constraints with new table name
ALTER TABLE test_result_reviews 
ADD CONSTRAINT test_result_reviews_execution_id_fkey 
FOREIGN KEY (execution_id) REFERENCES cycle_report_test_execution_test_executions(execution_id);

ALTER TABLE cycle_report_observation_mgmt_observation_records_backup 
ADD CONSTRAINT observation_records_source_test_execution_id_fkey 
FOREIGN KEY (source_test_execution_id) REFERENCES cycle_report_test_execution_test_executions(execution_id);

ALTER TABLE cycle_report_observation_mgmt_audit_logs 
ADD CONSTRAINT observation_management_audit_logs_source_test_execution_id_fkey 
FOREIGN KEY (source_test_execution_id) REFERENCES cycle_report_test_execution_test_executions(execution_id);

ALTER TABLE cycle_report_observation_mgmt_observation_records 
ADD CONSTRAINT observation_records_source_test_execution_id_fkey1 
FOREIGN KEY (source_test_execution_id) REFERENCES cycle_report_test_execution_test_executions(execution_id);

-- Step 6: Update any indexes that might exist
-- Check for indexes on the old table name
SELECT 'Indexes on test_executions:' as info;
SELECT indexname FROM pg_indexes WHERE tablename = 'test_executions';

-- Step 7: Verify the migration
SELECT 'Tables after migration:' as info;
SELECT tablename FROM pg_tables 
WHERE schemaname = 'public' 
AND tablename LIKE '%test_execution%' 
ORDER BY tablename;

-- Step 8: Verify foreign keys are working
SELECT 
    tc.table_name, 
    tc.constraint_name,
    ccu.table_name AS foreign_table_name
FROM 
    information_schema.table_constraints AS tc 
    JOIN information_schema.constraint_column_usage AS ccu
      ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY' 
AND ccu.table_name = 'test_executions';