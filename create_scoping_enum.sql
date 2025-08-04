-- Create the scoping version status enum if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'scoping_version_status_enum') THEN
        CREATE TYPE scoping_version_status_enum AS ENUM ('draft', 'pending', 'approved', 'rejected', 'superseded');
    END IF;
END$$;