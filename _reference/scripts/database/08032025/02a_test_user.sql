-- Insert test LOB first
INSERT INTO lobs (name, description, is_active) VALUES
('Test LOB', 'Test Line of Business', true)
ON CONFLICT DO NOTHING;

-- Insert test user with bcrypt hash for password123
INSERT INTO users (email, hashed_password, first_name, last_name, role, is_active) VALUES
('tester@example.com', '$2b$12$D/8avO4TQoqLTPI5jVzooOHlgQgaVHdm4pGp303CkmjXcn/vMQpie', 'Test', 'User', 'Tester', true)
ON CONFLICT (email) DO UPDATE SET
    hashed_password = '$2b$12$D/8avO4TQoqLTPI5jVzooOHlgQgaVHdm4pGp303CkmjXcn/vMQpie',
    first_name = 'Test',
    last_name = 'User',
    role = 'Tester',
    is_active = true;