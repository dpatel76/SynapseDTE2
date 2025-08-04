-- Add 'Submitted' to the phase_status_enum type

-- First, check if the enum type exists and what values it has
DO $$
BEGIN
    -- Check if 'Submitted' is already in the enum
    IF NOT EXISTS (
        SELECT 1 
        FROM pg_enum 
        WHERE enumtypid = 'phase_status_enum'::regtype 
        AND enumlabel = 'Submitted'
    ) THEN
        -- Add 'Submitted' to the enum type
        ALTER TYPE phase_status_enum ADD VALUE IF NOT EXISTS 'Submitted' AFTER 'In Progress';
    END IF;
END $$;

-- Verify the enum values
SELECT enumlabel 
FROM pg_enum 
WHERE enumtypid = 'phase_status_enum'::regtype 
ORDER BY enumsortorder;