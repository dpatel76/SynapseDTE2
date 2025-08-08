-- Add Information Security Classification to ReportAttribute table

-- Create enum type if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'information_security_classification_enum') THEN
        CREATE TYPE information_security_classification_enum AS ENUM (
            'HRCI',
            'Confidential',
            'Proprietary',
            'Public'
        );
    END IF;
END$$;

-- Add column to cycle_report_attributes_planning table
ALTER TABLE cycle_report_planning_attributes
ADD COLUMN IF NOT EXISTS information_security_classification information_security_classification_enum;

-- Add comment
COMMENT ON COLUMN cycle_report_attributes_planning.information_security_classification 
IS 'Security classification: HRCI, Confidential, Proprietary, Public';

-- Update existing PDEMapping to use consistent enum if needed
DO $$
BEGIN
    -- Check if the column exists and is using string type
    IF EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'cycle_report_pde_mappings' 
        AND column_name = 'information_security_classification'
        AND data_type = 'character varying'
    ) THEN
        -- Drop the old column
        ALTER TABLE cycle_report_pde_mappings 
        DROP COLUMN information_security_classification;
        
        -- Add new column with enum type
        ALTER TABLE cycle_report_pde_mappings
        ADD COLUMN information_security_classification information_security_classification_enum;
        
        COMMENT ON COLUMN cycle_report_pde_mappings.information_security_classification 
        IS 'Security classification: HRCI, Confidential, Proprietary, Public';
    END IF;
END$$;