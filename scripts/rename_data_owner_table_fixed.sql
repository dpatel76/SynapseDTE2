-- Rename the data owner assignments table to better reflect its purpose as a mapping table

-- 1. Check if table was already renamed
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'cycle_report_data_owner_lob_mapping') THEN
        RAISE NOTICE 'Table already renamed to cycle_report_data_owner_lob_mapping';
    ELSE
        -- Table still has old name, proceed with rename
        
        -- 1. Rename the main table
        ALTER TABLE cycle_report_data_owner_lob_attribute_assignments 
        RENAME TO cycle_report_data_owner_lob_mapping;
        
        -- 2. Since assignment_id is UUID, there's no sequence to rename
        
        -- 3. Rename the primary key constraint if it exists
        ALTER TABLE cycle_report_data_owner_lob_mapping 
        RENAME CONSTRAINT cycle_report_data_owner_lob_attribute_assignments_pkey 
        TO cycle_report_data_owner_lob_mapping_pkey;
        
        -- 4. Rename the assignment_id column to mapping_id
        ALTER TABLE cycle_report_data_owner_lob_mapping 
        RENAME COLUMN assignment_id TO mapping_id;
        
        RAISE NOTICE 'Table successfully renamed to cycle_report_data_owner_lob_mapping';
    END IF;
END $$;

-- 5. Check for foreign key constraints that reference the old table
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

-- 6. Rename versions table if it exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'cycle_report_data_owner_lob_attribute_versions') THEN
        ALTER TABLE cycle_report_data_owner_lob_attribute_versions 
        RENAME TO cycle_report_data_owner_lob_mapping_versions;
        RAISE NOTICE 'Versions table renamed to cycle_report_data_owner_lob_mapping_versions';
    END IF;
END $$;

-- 7. Update the unique index we just created
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_unique_phase_attribute_lob') THEN
        -- Index exists on the renamed table, no action needed
        RAISE NOTICE 'Unique index already exists on renamed table';
    END IF;
END $$;