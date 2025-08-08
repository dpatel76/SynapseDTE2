-- Simple migration from reports to report_inventory

-- First check what we're migrating
SELECT COUNT(*) as total_reports FROM reports;

-- Insert all reports preserving the IDs
INSERT INTO report_inventory (id, report_number, report_name, description, frequency, report_owner_id, lob_id, is_active, regulation)
SELECT 
    report_id as id,
    'RPT-' || LPAD(report_id::text, 6, '0') as report_number,
    report_name,
    description,
    frequency,
    report_owner_id,
    lob_id,
    is_active,
    regulation
FROM reports
ON CONFLICT (id) DO NOTHING;

-- Update sequence to avoid ID conflicts
SELECT setval('report_inventory_id_seq', COALESCE((SELECT MAX(id) FROM report_inventory), 1) + 1);

-- Check migration results
SELECT COUNT(*) as migrated_reports FROM report_inventory;

\echo 'Migration completed'