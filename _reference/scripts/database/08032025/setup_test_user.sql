-- Setup test user with proper role structure
-- Date: 2025-08-03

-- Insert roles if they don't exist
INSERT INTO roles (role_name, description, is_system, is_active) VALUES
('Tester', 'Test execution role', true, true),
('Test Executive', 'Test executive role', true, true),
('Report Owner', 'Report owner role', true, true),
('Report Executive', 'Report executive role', true, true),
('Data Owner', 'Data owner role', true, true),
('Data Executive', 'Data executive role', true, true),
('Admin', 'System administrator role', true, true)
ON CONFLICT (role_name) DO NOTHING;

-- Insert test user
INSERT INTO users (email, hashed_password, first_name, last_name, is_active) VALUES
('tester@example.com', '$2b$12$D/8avO4TQoqLTPI5jVzooOHlgQgaVHdm4pGp303CkmjXcn/vMQpie', 'Test', 'User', true)
ON CONFLICT (email) DO UPDATE SET
    hashed_password = EXCLUDED.hashed_password,
    first_name = EXCLUDED.first_name,
    last_name = EXCLUDED.last_name,
    is_active = EXCLUDED.is_active
RETURNING user_id;

-- Assign Tester role to the test user
WITH test_user AS (
    SELECT user_id FROM users WHERE email = 'tester@example.com'
),
tester_role AS (
    SELECT role_id FROM roles WHERE role_name = 'Tester'
)
INSERT INTO user_roles (user_id, role_id)
SELECT test_user.user_id, tester_role.role_id
FROM test_user, tester_role
ON CONFLICT (user_id, role_id) DO NOTHING;

-- Verify the setup
SELECT 
    u.user_id,
    u.email,
    u.first_name,
    u.last_name,
    r.role_name
FROM users u
JOIN user_roles ur ON u.user_id = ur.user_id
JOIN roles r ON ur.role_id = r.role_id
WHERE u.email = 'tester@example.com';