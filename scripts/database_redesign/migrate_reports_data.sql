-- Migrate all data from reports to report_inventory

-- First, disable foreign key checks temporarily
SET session_replication_role = 'replica';

-- Copy all reports data
INSERT INTO report_inventory (id, report_number, report_name, description, frequency, report_owner_id, lob_id, is_active, regulation, created_at, updated_at, created_by, updated_by)
SELECT 
    report_id as id,
    COALESCE('RPT-' || LPAD(report_id::text, 4, '0'), 'RPT-UNKNOWN') as report_number,
    report_name,
    description,
    frequency,
    report_owner_id,
    lob_id,
    is_active,
    regulation,
    created_at,
    updated_at,
    created_by_id as created_by,
    updated_by_id as updated_by
FROM reports
ON CONFLICT (id) DO UPDATE SET
    report_name = EXCLUDED.report_name,
    description = EXCLUDED.description,
    frequency = EXCLUDED.frequency,
    report_owner_id = EXCLUDED.report_owner_id,
    lob_id = EXCLUDED.lob_id,
    is_active = EXCLUDED.is_active,
    regulation = EXCLUDED.regulation,
    updated_at = CURRENT_TIMESTAMP;

-- Also handle the case where report_number might conflict
UPDATE report_inventory ri1
SET report_number = 'RPT-' || LPAD(ri1.id::text, 4, '0') || '-DUP'
WHERE EXISTS (
    SELECT 1 FROM report_inventory ri2 
    WHERE ri2.report_number = ri1.report_number 
    AND ri2.id < ri1.id
);

-- Update the sequence
SELECT setval('report_inventory_id_seq', COALESCE((SELECT MAX(id) FROM report_inventory), 1) + 1);

-- Re-enable foreign key checks
SET session_replication_role = 'origin';

-- Now update foreign key constraints
ALTER TABLE cycle_reports 
DROP CONSTRAINT IF EXISTS cycle_reports_report_id_fkey;

ALTER TABLE cycle_reports 
ADD CONSTRAINT cycle_reports_report_id_fkey 
FOREIGN KEY (report_id) REFERENCES report_inventory(id);

-- Report attributes
ALTER TABLE report_attributes 
DROP CONSTRAINT IF EXISTS report_attributes_report_id_fkey;

ALTER TABLE report_attributes 
ADD CONSTRAINT report_attributes_report_id_fkey 
FOREIGN KEY (report_id) REFERENCES report_inventory(id);

-- Documents
ALTER TABLE documents 
DROP CONSTRAINT IF EXISTS documents_report_id_fkey;

ALTER TABLE documents 
ADD CONSTRAINT documents_report_id_fkey 
FOREIGN KEY (report_id) REFERENCES report_inventory(id);

-- Sample sets
ALTER TABLE sample_sets 
DROP CONSTRAINT IF EXISTS sample_sets_report_id_fkey;

ALTER TABLE sample_sets 
ADD CONSTRAINT sample_sets_report_id_fkey 
FOREIGN KEY (report_id) REFERENCES report_inventory(id);

-- Test cases
ALTER TABLE test_cases 
DROP CONSTRAINT IF EXISTS test_cases_report_id_fkey;

ALTER TABLE test_cases 
ADD CONSTRAINT test_cases_report_id_fkey 
FOREIGN KEY (report_id) REFERENCES report_inventory(id);

\echo 'Data migration completed successfully'