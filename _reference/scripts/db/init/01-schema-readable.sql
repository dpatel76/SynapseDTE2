-- SynapseDTE Complete Database Schema (Readable Column Order)
-- This schema includes all tables, mixins, and seed data for containerized testing
-- Columns are ordered for better readability: PKs, business fields, FKs, metadata, timestamps

-- Ensure we're using the correct database
\c synapse_dt;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =================================================================
-- CORE TABLES
-- =================================================================

-- Users table (CustomPKModel + TimestampMixin)
CREATE TABLE IF NOT EXISTS users (
    -- Primary Key
    user_id SERIAL PRIMARY KEY,
    
    -- Core Identity Fields
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    
    -- User Information
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    role VARCHAR(50) NOT NULL CHECK (role IN ('Tester', 'Test Executive', 'Report Owner', 'Report Executive', 'Data Owner', 'Data Executive', 'Admin')),
    is_active BOOLEAN DEFAULT true NOT NULL,
    
    -- Foreign Keys
    lob_id INTEGER,
    
    -- Timestamps (TimestampMixin)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

-- LOBs table (AuditableCustomPKModel = CustomPKModel + TimestampMixin + AuditMixin)
CREATE TABLE IF NOT EXISTS lobs (
    -- Primary Key
    lob_id SERIAL PRIMARY KEY,
    
    -- Business Fields
    lob_name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true NOT NULL,
    
    -- Audit Fields (AuditMixin)
    created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    
    -- Timestamps (TimestampMixin)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Add foreign key constraint for users.lob_id after lobs table exists
ALTER TABLE users ADD CONSTRAINT fk_users_lob_id FOREIGN KEY (lob_id) REFERENCES lobs(lob_id);

-- =================================================================
-- RBAC TABLES (Role-Based Access Control)
-- =================================================================

-- RBAC Permissions (CustomPKModel + TimestampMixin + AuditMixin)
CREATE TABLE IF NOT EXISTS rbac_permissions (
    -- Primary Key
    permission_id SERIAL PRIMARY KEY,
    
    -- Permission Definition
    resource VARCHAR(100) NOT NULL,
    action VARCHAR(50) NOT NULL,
    description TEXT,
    
    -- Audit Fields (AuditMixin)
    created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    
    -- Timestamps (TimestampMixin)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Constraints
    CONSTRAINT uq_resource_action UNIQUE (resource, action)
);

CREATE INDEX idx_rbac_permissions_resource ON rbac_permissions(resource);
CREATE INDEX idx_rbac_permissions_action ON rbac_permissions(action);

-- RBAC Roles (CustomPKModel + TimestampMixin + AuditMixin)
CREATE TABLE IF NOT EXISTS rbac_roles (
    -- Primary Key
    role_id SERIAL PRIMARY KEY,
    
    -- Role Definition
    role_name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    is_system BOOLEAN DEFAULT false NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    
    -- Audit Fields (AuditMixin)
    created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    
    -- Timestamps (TimestampMixin)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX idx_rbac_roles_role_name ON rbac_roles(role_name);

-- RBAC Role Permissions (Junction table with audit)
CREATE TABLE IF NOT EXISTS rbac_role_permissions (
    -- Composite Primary Key
    role_id INTEGER REFERENCES rbac_roles(role_id) ON DELETE CASCADE,
    permission_id INTEGER REFERENCES rbac_permissions(permission_id) ON DELETE CASCADE,
    
    -- Assignment Metadata
    granted_by INTEGER REFERENCES users(user_id),
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Audit Fields (AuditMixin)
    created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    
    -- Timestamps (TimestampMixin)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Constraints
    PRIMARY KEY (role_id, permission_id)
);

-- RBAC User Roles (Junction table with expiration)
CREATE TABLE IF NOT EXISTS rbac_user_roles (
    -- Composite Primary Key
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    role_id INTEGER REFERENCES rbac_roles(role_id) ON DELETE CASCADE,
    
    -- Assignment Metadata
    assigned_by INTEGER REFERENCES users(user_id),
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Audit Fields (AuditMixin)
    created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    
    -- Timestamps (TimestampMixin)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Constraints
    PRIMARY KEY (user_id, role_id)
);

CREATE INDEX idx_rbac_user_roles_user_id ON rbac_user_roles(user_id);
CREATE INDEX idx_rbac_user_roles_expires_at ON rbac_user_roles(expires_at);

-- RBAC User Permissions (Direct permissions, can override roles)
CREATE TABLE IF NOT EXISTS rbac_user_permissions (
    -- Composite Primary Key
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    permission_id INTEGER REFERENCES rbac_permissions(permission_id) ON DELETE CASCADE,
    
    -- Permission Control
    granted BOOLEAN DEFAULT true NOT NULL,  -- Can be false to explicitly deny
    
    -- Assignment Metadata
    granted_by INTEGER REFERENCES users(user_id),
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Audit Fields (AuditMixin)
    created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    
    -- Timestamps (TimestampMixin)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Constraints
    PRIMARY KEY (user_id, permission_id)
);

CREATE INDEX idx_rbac_user_permissions_user_id ON rbac_user_permissions(user_id);
CREATE INDEX idx_rbac_user_permissions_expires_at ON rbac_user_permissions(expires_at);

-- RBAC Resource Permissions (Fine-grained access to specific resources)
CREATE TABLE IF NOT EXISTS rbac_resource_permissions (
    -- Primary Key
    resource_permission_id SERIAL PRIMARY KEY,
    
    -- Resource Identification
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE NOT NULL,
    resource_type VARCHAR(50) NOT NULL,  -- e.g., 'report', 'cycle', 'lob'
    resource_id INTEGER NOT NULL,        -- ID of the specific resource
    permission_id INTEGER REFERENCES rbac_permissions(permission_id) ON DELETE CASCADE NOT NULL,
    
    -- Permission Control
    granted BOOLEAN DEFAULT true NOT NULL,
    
    -- Assignment Metadata
    granted_by INTEGER REFERENCES users(user_id),
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Audit Fields (AuditMixin)
    created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    
    -- Timestamps (TimestampMixin)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Constraints
    CONSTRAINT uq_user_resource_permission UNIQUE (user_id, resource_type, resource_id, permission_id)
);

CREATE INDEX idx_rbac_resource_permissions_user_id ON rbac_resource_permissions(user_id);
CREATE INDEX idx_rbac_resource_permissions_resource_type ON rbac_resource_permissions(resource_type);
CREATE INDEX idx_rbac_resource_permissions_resource_id ON rbac_resource_permissions(resource_id);

-- RBAC Role Hierarchy (For role inheritance)
CREATE TABLE IF NOT EXISTS rbac_role_hierarchy (
    -- Composite Primary Key
    parent_role_id INTEGER REFERENCES rbac_roles(role_id) ON DELETE CASCADE,
    child_role_id INTEGER REFERENCES rbac_roles(role_id) ON DELETE CASCADE,
    
    -- Audit Fields (AuditMixin)
    created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    
    -- Timestamps (TimestampMixin)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Constraints
    PRIMARY KEY (parent_role_id, child_role_id)
);

-- RBAC Permission Audit Logs (Track all permission changes)
CREATE TABLE IF NOT EXISTS rbac_permission_audit_logs (
    -- Primary Key
    audit_id SERIAL PRIMARY KEY,
    
    -- Audit Information
    action_type VARCHAR(50) NOT NULL,    -- 'grant', 'revoke', 'expire'
    target_type VARCHAR(50) NOT NULL,    -- 'user', 'role'
    target_id INTEGER NOT NULL,
    
    -- What Changed
    permission_id INTEGER REFERENCES rbac_permissions(permission_id),
    role_id INTEGER REFERENCES rbac_roles(role_id),
    
    -- Who and When
    performed_by INTEGER REFERENCES users(user_id),
    performed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    reason TEXT,
    
    -- Audit Fields (AuditMixin)
    created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    
    -- Timestamps (TimestampMixin)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX idx_rbac_permission_audit_logs_target_type ON rbac_permission_audit_logs(target_type);
CREATE INDEX idx_rbac_permission_audit_logs_target_id ON rbac_permission_audit_logs(target_id);
CREATE INDEX idx_rbac_permission_audit_logs_performed_at ON rbac_permission_audit_logs(performed_at);

-- =================================================================
-- WORKFLOW AND TESTING TABLES
-- =================================================================

-- Test Cycles (BaseModel = Base + TimestampMixin, has id not custom PK)
CREATE TABLE IF NOT EXISTS test_cycles (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- Business Fields
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'planning',
    
    -- Scheduling
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    
    -- Foreign Keys
    created_by_id INTEGER REFERENCES users(user_id),
    
    -- Timestamps (TimestampMixin)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Workflow Phases (CustomPKModel + TimestampMixin)
CREATE TABLE IF NOT EXISTS workflow_phases (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- Business Identifier
    phase_id VARCHAR(255) UNIQUE NOT NULL,
    
    -- Phase Information
    phase_name VARCHAR(100) NOT NULL,
    phase_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    
    -- Foreign Keys
    cycle_id INTEGER REFERENCES test_cycles(id),
    
    -- Timing
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- Additional Data
    metadata JSONB,
    
    -- Timestamps (TimestampMixin)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Request Info / RFI (CustomPKModel + TimestampMixin)
CREATE TABLE IF NOT EXISTS request_info (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- Business Identifier
    rfi_id VARCHAR(255) UNIQUE NOT NULL,
    
    -- RFI Information
    title VARCHAR(255) NOT NULL,
    description TEXT,
    priority VARCHAR(20) DEFAULT 'medium',
    status VARCHAR(50) DEFAULT 'open',
    
    -- Assignment
    requester_id INTEGER REFERENCES users(user_id),
    assignee_id INTEGER REFERENCES users(user_id),
    
    -- Scheduling
    due_date DATE,
    resolved_at TIMESTAMP,
    
    -- Resolution
    resolution TEXT,
    
    -- Additional Data
    metadata JSONB,
    
    -- Timestamps (TimestampMixin)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Jobs table (CustomPKModel + TimestampMixin)
CREATE TABLE IF NOT EXISTS jobs (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- Business Identifier
    job_id VARCHAR(255) UNIQUE NOT NULL,
    
    -- Job Information
    job_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    
    -- Results
    result JSONB,
    error TEXT,
    
    -- Foreign Keys
    created_by_id INTEGER REFERENCES users(user_id),
    
    -- Timing
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- Timestamps (TimestampMixin)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Data Sources (CustomPKModel + TimestampMixin)
CREATE TABLE IF NOT EXISTS data_sources (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- Data Source Information
    name VARCHAR(255) UNIQUE NOT NULL,
    type VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    
    -- Configuration
    connection_details JSONB NOT NULL,
    
    -- Foreign Keys
    created_by_id INTEGER REFERENCES users(user_id),
    
    -- Timestamps (TimestampMixin)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Reports (for User model relationships)
CREATE TABLE IF NOT EXISTS reports (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- Report Information
    report_name VARCHAR(255) NOT NULL,
    
    -- Foreign Keys
    report_owner_id INTEGER REFERENCES users(user_id),
    
    -- Timestamps (TimestampMixin)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Cycle Reports (for User model relationships)
CREATE TABLE IF NOT EXISTS cycle_reports (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- Foreign Keys
    cycle_id INTEGER REFERENCES test_cycles(id),
    tester_id INTEGER REFERENCES users(user_id),
    
    -- Timestamps (TimestampMixin)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Test Execution (BaseModel = Base + TimestampMixin)
CREATE TABLE IF NOT EXISTS test_execution (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- Foreign Keys
    executed_by INTEGER REFERENCES users(user_id),
    
    -- Timestamps (TimestampMixin)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Audit Logs (for User model relationships)
CREATE TABLE IF NOT EXISTS audit_logs (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- Audit Information
    action VARCHAR(100) NOT NULL,
    details JSONB,
    
    -- Foreign Keys
    user_id INTEGER REFERENCES users(user_id),
    
    -- Timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- LLM Audit Logs (for User model relationships)
CREATE TABLE IF NOT EXISTS llm_audit_logs (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- LLM Interaction
    prompt TEXT,
    response TEXT,
    
    -- Foreign Keys
    executed_by INTEGER REFERENCES users(user_id),
    
    -- Timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Universal Assignments (referenced in User model)
CREATE TABLE IF NOT EXISTS universal_assignments (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- Assignment Flow
    from_user_id INTEGER REFERENCES users(user_id),
    to_user_id INTEGER REFERENCES users(user_id),
    
    -- Assignment Status
    completed_by_user_id INTEGER REFERENCES users(user_id),
    approved_by_user_id INTEGER REFERENCES users(user_id),
    
    -- Escalation/Delegation
    escalated_to_user_id INTEGER REFERENCES users(user_id),
    delegated_to_user_id INTEGER REFERENCES users(user_id),
    
    -- Timestamps (TimestampMixin)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Universal Assignment History
CREATE TABLE IF NOT EXISTS universal_assignment_history (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- History Information
    assignment_id INTEGER REFERENCES universal_assignments(id),
    change_type VARCHAR(50),
    
    -- Foreign Keys
    changed_by_user_id INTEGER REFERENCES users(user_id),
    
    -- Timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- =================================================================
-- ALEMBIC VERSION TABLE
-- =================================================================

CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Mark as manually created to prevent migration conflicts
INSERT INTO alembic_version (version_num) VALUES ('containerized_schema_v1') ON CONFLICT DO NOTHING;

-- =================================================================
-- TRIGGERS FOR TIMESTAMP UPDATES
-- =================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update trigger to all tables with updated_at column
DO $$
DECLARE
    t text;
BEGIN
    FOR t IN 
        SELECT table_name 
        FROM information_schema.columns 
        WHERE column_name = 'updated_at' 
        AND table_schema = 'public'
    LOOP
        EXECUTE format('DROP TRIGGER IF EXISTS update_%I_updated_at ON %I', t, t);
        EXECUTE format('CREATE TRIGGER update_%I_updated_at BEFORE UPDATE ON %I 
                       FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column()', t, t);
    END LOOP;
END;
$$ language 'plpgsql';

-- =================================================================
-- SEED DATA - CRITICAL FOR SYSTEM OPERATION
-- =================================================================

-- Insert default RBAC roles (system roles that cannot be deleted)
INSERT INTO rbac_roles (role_name, description, is_system) VALUES
    ('Administrator', 'Full system access', true),
    ('Test Executive', 'Manages test cycles and assignments', true),
    ('Tester', 'Executes test procedures', true),
    ('Report Owner', 'Owns and approves reports', true),
    ('Report Owner Executive', 'Executive oversight of reports', true),
    ('Data Owner', 'Provides data for testing', true),
    ('Chief Data Officer', 'Oversees data governance', true)
ON CONFLICT (role_name) DO NOTHING;

-- Insert core permissions (based on rbac_config.py patterns)
-- Note: This is a subset. Full permissions should be loaded via seed_rbac_permissions.py
INSERT INTO rbac_permissions (resource, action, description) VALUES
    -- User management
    ('users', 'view', 'View users'),
    ('users', 'create', 'Create users'),
    ('users', 'update', 'Update users'),
    ('users', 'delete', 'Delete users'),
    ('users', 'manage_roles', 'Manage user roles'),
    
    -- Test cycles
    ('test_cycles', 'view', 'View test cycles'),
    ('test_cycles', 'create', 'Create test cycles'),
    ('test_cycles', 'update', 'Update test cycles'),
    ('test_cycles', 'delete', 'Delete test cycles'),
    ('test_cycles', 'assign', 'Assign test cycles'),
    
    -- Reports
    ('reports', 'view', 'View reports'),
    ('reports', 'create', 'Create reports'),
    ('reports', 'update', 'Update reports'),
    ('reports', 'delete', 'Delete reports'),
    ('reports', 'approve', 'Approve reports'),
    
    -- Data sources
    ('data_sources', 'view', 'View data sources'),
    ('data_sources', 'create', 'Create data sources'),
    ('data_sources', 'update', 'Update data sources'),
    ('data_sources', 'delete', 'Delete data sources'),
    ('data_sources', 'execute', 'Execute queries on data sources'),
    
    -- RFI
    ('rfi', 'view', 'View RFIs'),
    ('rfi', 'create', 'Create RFIs'),
    ('rfi', 'update', 'Update RFIs'),
    ('rfi', 'delete', 'Delete RFIs'),
    ('rfi', 'assign', 'Assign RFIs'),
    
    -- System
    ('system', 'view_logs', 'View system logs'),
    ('system', 'manage_config', 'Manage system configuration'),
    ('system', 'view_metrics', 'View system metrics')
ON CONFLICT (resource, action) DO NOTHING;

-- Assign all permissions to Administrator role
INSERT INTO rbac_role_permissions (role_id, permission_id)
SELECT r.role_id, p.permission_id
FROM rbac_roles r
CROSS JOIN rbac_permissions p
WHERE r.role_name = 'Administrator'
ON CONFLICT (role_id, permission_id) DO NOTHING;

-- Insert test users (password: 'password123')
-- Password hash is bcrypt with 12 rounds
INSERT INTO users (email, hashed_password, first_name, last_name, role, is_active) VALUES
    ('admin@test.local', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiGH5MbKNr92', 'Admin', 'User', 'Admin', true),
    ('test.executive@test.local', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiGH5MbKNr92', 'Test', 'Executive', 'Test Executive', true),
    ('tester@test.local', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiGH5MbKNr92', 'Test', 'Tester', 'Tester', true),
    ('report.owner@test.local', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiGH5MbKNr92', 'Report', 'Owner', 'Report Owner', true),
    ('data.owner@test.local', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiGH5MbKNr92', 'Data', 'Owner', 'Data Owner', true)
ON CONFLICT (email) DO NOTHING;

-- Assign RBAC roles to test users
INSERT INTO rbac_user_roles (user_id, role_id)
SELECT u.user_id, r.role_id
FROM users u
JOIN rbac_roles r ON 
    (u.role = 'Admin' AND r.role_name = 'Administrator') OR
    (u.role = 'Test Executive' AND r.role_name = 'Test Executive') OR
    (u.role = 'Tester' AND r.role_name = 'Tester') OR
    (u.role = 'Report Owner' AND r.role_name = 'Report Owner') OR
    (u.role = 'Data Owner' AND r.role_name = 'Data Owner')
ON CONFLICT (user_id, role_id) DO NOTHING;

-- Insert test LOBs
INSERT INTO lobs (lob_name, description, is_active) VALUES
    ('Corporate Banking', 'Corporate banking line of business', true),
    ('Retail Banking', 'Retail banking line of business', true),
    ('Investment Banking', 'Investment banking line of business', true)
ON CONFLICT (lob_name) DO NOTHING;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO synapse_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO synapse_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO synapse_user;

-- Ensure sequences are properly set
SELECT setval(pg_get_serial_sequence('users', 'user_id'), COALESCE((SELECT MAX(user_id) FROM users), 0) + 1, false);
SELECT setval(pg_get_serial_sequence('rbac_roles', 'role_id'), COALESCE((SELECT MAX(role_id) FROM rbac_roles), 0) + 1, false);
SELECT setval(pg_get_serial_sequence('rbac_permissions', 'permission_id'), COALESCE((SELECT MAX(permission_id) FROM rbac_permissions), 0) + 1, false);
SELECT setval(pg_get_serial_sequence('lobs', 'lob_id'), COALESCE((SELECT MAX(lob_id) FROM lobs), 0) + 1, false);