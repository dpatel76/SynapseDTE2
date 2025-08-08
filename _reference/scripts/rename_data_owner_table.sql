-- Rename the data owner assignments table to better reflect its purpose as a mapping table

-- 1. Rename the main table
ALTER TABLE cycle_report_data_owner_lob_attribute_assignments 
RENAME TO cycle_report_data_owner_lob_mapping;

-- 2. Rename the sequence
ALTER SEQUENCE cycle_report_data_owner_lob_attribute_assignments_assignment_id_seq 
RENAME TO cycle_report_data_owner_lob_mapping_mapping_id_seq;

-- 3. Rename the primary key constraint
ALTER TABLE cycle_report_data_owner_lob_mapping 
RENAME CONSTRAINT cycle_report_data_owner_lob_attribute_assignments_pkey 
TO cycle_report_data_owner_lob_mapping_pkey;

-- 4. Rename the assignment_id column to mapping_id
ALTER TABLE cycle_report_data_owner_lob_mapping 
RENAME COLUMN assignment_id TO mapping_id;

-- 5. Update any foreign key constraints that reference this table
-- (Check if any exist first)
SELECT 
    tc.constraint_name, 
    tc.table_name, 
    kcu.column_name, 
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name 
FROM 
    information_schema.table_constraints AS tc 
    JOIN information_schema.key_column_usage AS kcu
      ON tc.constraint_name = kcu.constraint_name
      AND tc.table_schema = kcu.table_schema
    JOIN information_schema.constraint_column_usage AS ccu
      ON ccu.constraint_name = tc.constraint_name
      AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY' 
  AND ccu.table_name='cycle_report_data_owner_lob_attribute_assignments';

-- Note: The versions table should also be renamed for consistency
ALTER TABLE cycle_report_data_owner_lob_attribute_versions 
RENAME TO cycle_report_data_owner_lob_mapping_versions;