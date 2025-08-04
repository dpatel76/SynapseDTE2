-- Emergency fix for missing audit columns
-- This script adds audit columns to tables that are causing 500 errors

BEGIN;

-- Add audit columns to permissions table
ALTER TABLE permissions 
ADD COLUMN IF NOT EXISTS created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_permissions_created_by ON permissions(created_by_id);
CREATE INDEX IF NOT EXISTS idx_permissions_updated_by ON permissions(updated_by_id);

-- Add audit columns to roles table
ALTER TABLE roles 
ADD COLUMN IF NOT EXISTS created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_roles_created_by ON roles(created_by_id);
CREATE INDEX IF NOT EXISTS idx_roles_updated_by ON roles(updated_by_id);

-- Add audit columns to test_cycles table
ALTER TABLE test_cycles 
ADD COLUMN IF NOT EXISTS created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_test_cycles_created_by ON test_cycles(created_by_id);
CREATE INDEX IF NOT EXISTS idx_test_cycles_updated_by ON test_cycles(updated_by_id);

-- Verify the changes
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
AND column_name IN ('created_by_id', 'updated_by_id')
AND table_name IN ('permissions', 'roles', 'test_cycles', 'lobs')
ORDER BY table_name, column_name;

COMMIT;