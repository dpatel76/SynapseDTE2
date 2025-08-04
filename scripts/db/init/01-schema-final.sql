-- SynapseDTE Complete Database Schema (Final Version)
-- Foreign keys are placed right after primary keys for better readability
-- Column order: PKs, FKs, business fields, metadata, audit fields, timestamps

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
    
    -- Foreign Keys
    lob_id INTEGER,  -- Added after LOBs table is created
    
    -- Core Identity Fields
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    
    -- User Information
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    role VARCHAR(50) NOT NULL CHECK (role IN ('Tester', 'Test Executive', 'Report Owner', 'Report Executive', 'Data Owner', 'Data Executive', 'Admin')),
    is_active BOOLEAN DEFAULT true NOT NULL,
    
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
    
    -- Foreign Keys (Audit)
    created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    
    -- Business Fields
    lob_name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true NOT NULL,
    
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
    
    -- Foreign Keys (Audit)
    created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    
    -- Permission Definition
    resource VARCHAR(100) NOT NULL,
    action VARCHAR(50) NOT NULL,
    description TEXT,
    
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
    
    -- Foreign Keys (Audit)
    created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    
    -- Role Definition
    role_name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    is_system BOOLEAN DEFAULT false NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    
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
    
    -- Foreign Keys
    granted_by INTEGER REFERENCES users(user_id),
    created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    
    -- Assignment Metadata
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
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
    
    -- Foreign Keys
    assigned_by INTEGER REFERENCES users(user_id),
    created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    
    -- Assignment Metadata
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE,
    
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
    
    -- Foreign Keys
    granted_by INTEGER REFERENCES users(user_id),
    created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    
    -- Permission Control
    granted BOOLEAN DEFAULT true NOT NULL,  -- Can be false to explicitly deny
    
    -- Assignment Metadata
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE,
    
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
    
    -- Foreign Keys
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE NOT NULL,
    permission_id INTEGER REFERENCES rbac_permissions(permission_id) ON DELETE CASCADE NOT NULL,
    granted_by INTEGER REFERENCES users(user_id),
    created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    
    -- Resource Identification
    resource_type VARCHAR(50) NOT NULL,  -- e.g., 'report', 'cycle', 'lob'
    resource_id INTEGER NOT NULL,        -- ID of the specific resource
    
    -- Permission Control
    granted BOOLEAN DEFAULT true NOT NULL,
    
    -- Assignment Metadata
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE,
    
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
    
    -- Foreign Keys (Audit)
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
    
    -- Foreign Keys
    permission_id INTEGER REFERENCES rbac_permissions(permission_id),
    role_id INTEGER REFERENCES rbac_roles(role_id),
    performed_by INTEGER REFERENCES users(user_id),
    created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    
    -- Audit Information
    action_type VARCHAR(50) NOT NULL,    -- 'grant', 'revoke', 'expire'
    target_type VARCHAR(50) NOT NULL,    -- 'user', 'role'
    target_id INTEGER NOT NULL,
    
    -- Who and When
    performed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    reason TEXT,
    
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
    
    -- Foreign Keys
    created_by_id INTEGER REFERENCES users(user_id),
    
    -- Business Fields
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'planning',
    
    -- Scheduling
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    
    -- Timestamps (TimestampMixin)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Workflow Phases (CustomPKModel + TimestampMixin)
CREATE TABLE IF NOT EXISTS workflow_phases (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- Foreign Keys
    cycle_id INTEGER REFERENCES test_cycles(id),
    
    -- Business Identifier
    phase_id VARCHAR(255) UNIQUE NOT NULL,
    
    -- Phase Information
    phase_name VARCHAR(100) NOT NULL,
    phase_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    
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
    
    -- Foreign Keys
    requester_id INTEGER REFERENCES users(user_id),
    assignee_id INTEGER REFERENCES users(user_id),
    
    -- Business Identifier
    rfi_id VARCHAR(255) UNIQUE NOT NULL,
    
    -- RFI Information
    title VARCHAR(255) NOT NULL,
    description TEXT,
    priority VARCHAR(20) DEFAULT 'medium',
    status VARCHAR(50) DEFAULT 'open',
    
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
    
    -- Foreign Keys
    created_by_id INTEGER REFERENCES users(user_id),
    
    -- Business Identifier
    job_id VARCHAR(255) UNIQUE NOT NULL,
    
    -- Job Information
    job_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    
    -- Results
    result JSONB,
    error TEXT,
    
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
    
    -- Foreign Keys
    created_by_id INTEGER REFERENCES users(user_id),
    
    -- Data Source Information
    name VARCHAR(255) UNIQUE NOT NULL,
    type VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    
    -- Configuration
    connection_details JSONB NOT NULL,
    
    -- Timestamps (TimestampMixin)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Reports (for User model relationships)
CREATE TABLE IF NOT EXISTS reports (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- Foreign Keys
    report_owner_id INTEGER REFERENCES users(user_id),
    
    -- Report Information
    report_name VARCHAR(255) NOT NULL,
    
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
    
    -- Foreign Keys
    user_id INTEGER REFERENCES users(user_id),
    
    -- Audit Information
    action VARCHAR(100) NOT NULL,
    details JSONB,
    
    -- Timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- LLM Audit Logs (for User model relationships)
CREATE TABLE IF NOT EXISTS llm_audit_logs (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- Foreign Keys
    executed_by INTEGER REFERENCES users(user_id),
    
    -- LLM Interaction
    prompt TEXT,
    response TEXT,
    
    -- Timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Universal Assignments (referenced in User model)
CREATE TABLE IF NOT EXISTS universal_assignments (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- Foreign Keys
    from_user_id INTEGER REFERENCES users(user_id),
    to_user_id INTEGER REFERENCES users(user_id),
    completed_by_user_id INTEGER REFERENCES users(user_id),
    approved_by_user_id INTEGER REFERENCES users(user_id),
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
    
    -- Foreign Keys
    assignment_id INTEGER REFERENCES universal_assignments(id),
    changed_by_user_id INTEGER REFERENCES users(user_id),
    
    -- History Information
    change_type VARCHAR(50),
    
    -- Timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- =================================================================
-- ATTRIBUTE-RELATED TABLES FOR DATA OWNER PHASE
-- =================================================================

-- Attribute LOB Assignments (for Data Owner phase)
CREATE TABLE IF NOT EXISTS attribute_lob_assignments (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- Foreign Keys
    assigned_by INTEGER REFERENCES users(user_id),
    
    -- Assignment Information
    attribute_id INTEGER NOT NULL,
    lob_id INTEGER REFERENCES lobs(lob_id),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Historical Data Owner Assignments (for audit trail)
CREATE TABLE IF NOT EXISTS historical_data_owner_assignments (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- Foreign Keys
    data_owner_id INTEGER REFERENCES users(user_id),
    assigned_by INTEGER REFERENCES users(user_id),
    
    -- Assignment Information
    entity_type VARCHAR(50) NOT NULL,
    entity_id INTEGER NOT NULL,
    
    -- Timestamps
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    unassigned_at TIMESTAMP WITH TIME ZONE
);

-- Data Owner Phase Audit Logs
CREATE TABLE IF NOT EXISTS data_owner_phase_audit_logs (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- Foreign Keys
    performed_by INTEGER REFERENCES users(user_id),
    
    -- Audit Information
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id INTEGER,
    details JSONB,
    
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