-- Fix users table to match application model expectations
-- Date: 2025-08-03

-- Add role column to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS role user_role_enum;

-- Update existing users to have a role based on user_roles table
UPDATE users u
SET role = 'Tester'
WHERE EXISTS (
    SELECT 1 FROM user_roles ur
    JOIN roles r ON ur.role_id = r.role_id
    WHERE ur.user_id = u.user_id
    AND r.role_name = 'Tester'
)
AND role IS NULL;

-- Make role NOT NULL after setting values
ALTER TABLE users ALTER COLUMN role SET NOT NULL;

-- Create index on role
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- Verify the change
SELECT 
    u.user_id,
    u.email,
    u.first_name,
    u.last_name,
    u.role as user_table_role,
    r.role_name as roles_table_role
FROM users u
LEFT JOIN user_roles ur ON u.user_id = ur.user_id
LEFT JOIN roles r ON ur.role_id = r.role_id
WHERE u.email = 'tester@example.com';