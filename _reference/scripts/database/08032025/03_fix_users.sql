-- Fix users table to match application model
-- This runs after the initial schema but before test user creation

-- Drop the old users table and recreate with correct structure
DROP TABLE IF EXISTS users CASCADE;

-- User role enum
DROP TYPE IF EXISTS user_role_enum CASCADE;
CREATE TYPE user_role_enum AS ENUM (
    'Tester',
    'Test Executive', 
    'Report Owner',
    'Report Executive',
    'Data Owner',
    'Data Executive',
    'Admin'
);

-- LOBs table (if not exists)
CREATE TABLE IF NOT EXISTS lobs (
    lob_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Insert default LOB if not exists
INSERT INTO lobs (name, description, is_active) 
SELECT 'Default LOB', 'Default Line of Business', true
WHERE NOT EXISTS (SELECT 1 FROM lobs WHERE name = 'Default LOB');

-- Users table with correct structure
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    role user_role_enum NOT NULL,
    lob_id INTEGER REFERENCES lobs(lob_id),
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_cdo BOOLEAN DEFAULT FALSE
);

-- Create indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

-- Insert test user with bcrypt hash for password123
INSERT INTO users (email, hashed_password, first_name, last_name, role, is_active) VALUES
('tester@example.com', '$2b$12$D/8avO4TQoqLTPI5jVzooOHlgQgaVHdm4pGp303CkmjXcn/vMQpie', 'Test', 'User', 'Tester', true),
('admin@example.com', '$2b$12$D/8avO4TQoqLTPI5jVzooOHlgQgaVHdm4pGp303CkmjXcn/vMQpie', 'System', 'Administrator', 'Admin', true),
('report.owner@example.com', '$2b$12$D/8avO4TQoqLTPI5jVzooOHlgQgaVHdm4pGp303CkmjXcn/vMQpie', 'Report', 'Owner', 'Report Owner', true),
('data.owner@example.com', '$2b$12$D/8avO4TQoqLTPI5jVzooOHlgQgaVHdm4pGp303CkmjXcn/vMQpie', 'Data', 'Owner', 'Data Owner', true),
('data.executive@example.com', '$2b$12$D/8avO4TQoqLTPI5jVzooOHlgQgaVHdm4pGp303CkmjXcn/vMQpie', 'Data', 'Executive', 'Data Executive', true)
ON CONFLICT (email) DO NOTHING;