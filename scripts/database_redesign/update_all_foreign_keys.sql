-- Update all foreign key constraints to point to report_inventory

-- List all tables that reference reports
SELECT DISTINCT
    tc.table_name,
    kcu.column_name,
    tc.constraint_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu 
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.referential_constraints rc 
    ON tc.constraint_name = rc.constraint_name
JOIN information_schema.key_column_usage rcu 
    ON rc.unique_constraint_name = rcu.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY' 
    AND rcu.table_name = 'reports'
    AND rcu.column_name = 'report_id'
ORDER BY tc.table_name;

-- Now update each one
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN 
        SELECT DISTINCT
            tc.table_name,
            tc.constraint_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu 
            ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.referential_constraints rc 
            ON tc.constraint_name = rc.constraint_name
        JOIN information_schema.key_column_usage rcu 
            ON rc.unique_constraint_name = rcu.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY' 
            AND rcu.table_name = 'reports'
            AND rcu.column_name = 'report_id'
    LOOP
        -- Drop old constraint
        EXECUTE format('ALTER TABLE %I DROP CONSTRAINT IF EXISTS %I', r.table_name, r.constraint_name);
        
        -- Add new constraint
        EXECUTE format('ALTER TABLE %I ADD CONSTRAINT %I FOREIGN KEY (report_id) REFERENCES report_inventory(id)', 
                       r.table_name, r.constraint_name);
                       
        RAISE NOTICE 'Updated constraint % on table %', r.constraint_name, r.table_name;
    END LOOP;
END $$;

\echo 'All foreign key constraints updated'