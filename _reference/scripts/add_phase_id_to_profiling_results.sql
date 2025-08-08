-- Add phase_id column to cycle_report_data_profiling_results table
-- This column is referenced in the ProfilingResult model but was missing from the database

-- Check if the column already exists before adding it
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'cycle_report_data_profiling_results' 
        AND column_name = 'phase_id'
    ) THEN
        -- Add the phase_id column
        ALTER TABLE cycle_report_data_profiling_results 
        ADD COLUMN phase_id INTEGER;
        
        -- Add foreign key constraint to workflow_phases table
        ALTER TABLE cycle_report_data_profiling_results
        ADD CONSTRAINT fk_profiling_results_phase_id 
        FOREIGN KEY (phase_id) 
        REFERENCES workflow_phases(phase_id)
        ON DELETE CASCADE;
        
        -- Create index for better query performance
        CREATE INDEX idx_profiling_results_phase_id 
        ON cycle_report_data_profiling_results(phase_id);
        
        RAISE NOTICE 'Successfully added phase_id column to cycle_report_data_profiling_results table';
    ELSE
        RAISE NOTICE 'Column phase_id already exists in cycle_report_data_profiling_results table';
    END IF;
END $$;

-- Also check and add phase_id to other related tables if missing
DO $$
BEGIN
    -- Check cycle_report_data_profiling_files
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'cycle_report_data_profiling_files' 
        AND column_name = 'phase_id'
    ) THEN
        ALTER TABLE cycle_report_data_profiling_files 
        ADD COLUMN phase_id INTEGER;
        
        ALTER TABLE cycle_report_data_profiling_files
        ADD CONSTRAINT fk_profiling_files_phase_id 
        FOREIGN KEY (phase_id) 
        REFERENCES workflow_phases(phase_id)
        ON DELETE CASCADE;
        
        CREATE INDEX idx_profiling_files_phase_id 
        ON cycle_report_data_profiling_files(phase_id);
        
        RAISE NOTICE 'Successfully added phase_id column to cycle_report_data_profiling_files table';
    END IF;
    
    -- Check cycle_report_data_profiling_rules
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'cycle_report_data_profiling_rules' 
        AND column_name = 'phase_id'
    ) THEN
        ALTER TABLE cycle_report_data_profiling_rules 
        ADD COLUMN phase_id INTEGER;
        
        ALTER TABLE cycle_report_data_profiling_rules
        ADD CONSTRAINT fk_profiling_rules_phase_id 
        FOREIGN KEY (phase_id) 
        REFERENCES workflow_phases(phase_id)
        ON DELETE CASCADE;
        
        CREATE INDEX idx_profiling_rules_phase_id 
        ON cycle_report_data_profiling_rules(phase_id);
        
        RAISE NOTICE 'Successfully added phase_id column to cycle_report_data_profiling_rules table';
    END IF;
    
    -- Check cycle_report_data_profiling_attribute_scores
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'cycle_report_data_profiling_attribute_scores' 
        AND column_name = 'phase_id'
    ) THEN
        ALTER TABLE cycle_report_data_profiling_attribute_scores 
        ADD COLUMN phase_id INTEGER;
        
        ALTER TABLE cycle_report_data_profiling_attribute_scores
        ADD CONSTRAINT fk_profiling_scores_phase_id 
        FOREIGN KEY (phase_id) 
        REFERENCES workflow_phases(phase_id)
        ON DELETE CASCADE;
        
        CREATE INDEX idx_profiling_scores_phase_id 
        ON cycle_report_data_profiling_attribute_scores(phase_id);
        
        RAISE NOTICE 'Successfully added phase_id column to cycle_report_data_profiling_attribute_scores table';
    END IF;
END $$;

-- Update existing records to link them to their corresponding workflow phases
-- This will set phase_id based on matching cycle_id and report_id
UPDATE cycle_report_data_profiling_results pr
SET phase_id = wp.phase_id
FROM workflow_phases wp
JOIN cycle_report_planning_attributes ra ON ra.cycle_id = wp.cycle_id AND ra.report_id = wp.report_id
WHERE pr.attribute_id = ra.id
AND wp.phase_name = 'Data Profiling'
AND pr.phase_id IS NULL;

-- Make phase_id NOT NULL after populating existing records
-- Only do this if all records have been updated
DO $$
DECLARE
    null_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO null_count
    FROM cycle_report_data_profiling_results
    WHERE phase_id IS NULL;
    
    IF null_count = 0 THEN
        ALTER TABLE cycle_report_data_profiling_results
        ALTER COLUMN phase_id SET NOT NULL;
        RAISE NOTICE 'Made phase_id NOT NULL in cycle_report_data_profiling_results';
    ELSE
        RAISE NOTICE 'Cannot make phase_id NOT NULL - % records still have NULL values', null_count;
    END IF;
END $$;