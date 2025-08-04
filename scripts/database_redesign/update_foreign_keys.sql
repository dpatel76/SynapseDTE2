-- Update foreign key constraints to point to report_inventory

-- First, we need to migrate data to ensure referential integrity
-- Copy all report IDs from reports to report_inventory if not already there
INSERT INTO report_inventory (id, report_number, report_name, description, frequency, report_owner_id, lob_id, is_active, regulation, created_at, updated_at, created_by_id, updated_by_id)
SELECT 
    report_id as id,
    COALESCE('RPT-' || report_id::text, 'RPT-UNKNOWN') as report_number,
    report_name,
    description,
    frequency,
    report_owner_id,
    lob_id,
    is_active,
    regulation,
    created_at,
    updated_at,
    created_by_id,
    updated_by_id
FROM reports
ON CONFLICT (id) DO NOTHING;

-- Update the sequence to avoid conflicts
SELECT setval('report_inventory_id_seq', COALESCE((SELECT MAX(id) FROM report_inventory), 1) + 1);

-- Now update foreign key constraints
-- For cycle_reports
ALTER TABLE cycle_reports 
DROP CONSTRAINT IF EXISTS cycle_reports_report_id_fkey;

ALTER TABLE cycle_reports 
ADD CONSTRAINT cycle_reports_report_id_fkey 
FOREIGN KEY (report_id) REFERENCES report_inventory(id);

-- For report_attributes
ALTER TABLE report_attributes 
DROP CONSTRAINT IF EXISTS report_attributes_report_id_fkey;

ALTER TABLE report_attributes 
ADD CONSTRAINT report_attributes_report_id_fkey 
FOREIGN KEY (report_id) REFERENCES report_inventory(id);

-- For documents
ALTER TABLE documents 
DROP CONSTRAINT IF EXISTS documents_report_id_fkey;

ALTER TABLE documents 
ADD CONSTRAINT documents_report_id_fkey 
FOREIGN KEY (report_id) REFERENCES report_inventory(id);

-- For attribute_lob_assignments
ALTER TABLE attribute_lob_assignments 
DROP CONSTRAINT IF EXISTS attribute_lob_assignments_report_id_fkey;

ALTER TABLE attribute_lob_assignments 
ADD CONSTRAINT attribute_lob_assignments_report_id_fkey 
FOREIGN KEY (report_id) REFERENCES report_inventory(id);

-- For data_owner_sla_violations
ALTER TABLE data_owner_sla_violations 
DROP CONSTRAINT IF EXISTS data_owner_sla_violations_report_id_fkey;

ALTER TABLE data_owner_sla_violations 
ADD CONSTRAINT data_owner_sla_violations_report_id_fkey 
FOREIGN KEY (report_id) REFERENCES report_inventory(id);

-- Continue for other tables...
\echo 'Foreign key constraints updated successfully'