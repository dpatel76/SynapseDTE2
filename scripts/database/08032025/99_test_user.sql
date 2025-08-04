-- Test user with bcrypt hash for password123
-- Generated: 2025-08-03
-- Use these credentials for API testing:
-- Email: tester@example.com
-- Password: password123

INSERT INTO users (email, hashed_password, first_name, last_name, role, is_active) VALUES
('tester@example.com', '$2b$12$D/8avO4TQoqLTPI5jVzooOHlgQgaVHdm4pGp303CkmjXcn/vMQpie', 'Test', 'User', 'Tester', true)
ON CONFLICT (email) DO UPDATE SET
    hashed_password = EXCLUDED.hashed_password,
    first_name = EXCLUDED.first_name,
    last_name = EXCLUDED.last_name,
    role = EXCLUDED.role,
    is_active = EXCLUDED.is_active;
