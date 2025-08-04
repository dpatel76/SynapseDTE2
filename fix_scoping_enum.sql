-- Check current enum values
SELECT enumlabel FROM pg_enum 
WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'scoping_version_status_enum')
ORDER BY enumsortorder;

-- If pending_approval is missing, we need to add it
-- First, check if the type exists
DO $$
BEGIN
    -- Check if pending_approval exists in the enum
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum 
        WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'scoping_version_status_enum')
        AND enumlabel = 'pending_approval'
    ) THEN
        -- Add the missing value
        ALTER TYPE scoping_version_status_enum ADD VALUE IF NOT EXISTS 'pending_approval' AFTER 'draft';
    END IF;
END $$;