-- Temporary SQL script to update user_role_enum
-- This should be run manually or converted to an Alembic migration

-- First, update existing data to use new role names
UPDATE users SET role = 'Test Executive' WHERE role = 'Test Manager';
UPDATE users SET role = 'Data Executive' WHERE role = 'CDO';
UPDATE users SET role = 'Report Executive' WHERE role = 'Report Owner Executive';
UPDATE users SET role = 'Data Owner' WHERE role = 'Data Provider';

-- Update role names in roles table
UPDATE roles SET role_name = 'Test Executive' WHERE role_name = 'Test Manager';
UPDATE roles SET role_name = 'Data Executive' WHERE role_name = 'CDO';
UPDATE roles SET role_name = 'Report Executive' WHERE role_name = 'Report Owner Executive';
UPDATE roles SET role_name = 'Data Owner' WHERE role_name = 'Data Provider';

-- Update workflow activity templates
UPDATE workflow_activity_templates SET required_role = 'Test Executive' WHERE required_role = 'Test Manager';
UPDATE workflow_activity_templates SET required_role = 'Data Executive' WHERE required_role = 'CDO';

-- Now we need to recreate the enum type with new values
-- This is complex in PostgreSQL, so we'll use a workaround

-- Step 1: Create a new enum type with correct values
CREATE TYPE user_role_enum_new AS ENUM (
    'Tester',
    'Test Executive',
    'Report Owner',
    'Report Executive',
    'Data Owner',
    'Data Executive',
    'Admin'
);

-- Step 2: Update columns to use new enum
ALTER TABLE users ALTER COLUMN role TYPE user_role_enum_new USING role::text::user_role_enum_new;

-- Step 3: Drop old enum and rename new one
DROP TYPE user_role_enum;
ALTER TYPE user_role_enum_new RENAME TO user_role_enum;