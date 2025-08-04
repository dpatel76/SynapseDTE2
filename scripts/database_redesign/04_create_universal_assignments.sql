-- Complete Database Redesign: Universal Assignment System
-- Flexible assignment mechanism for any entity to any user with any role

-- =====================================================
-- UNIVERSAL ASSIGNMENT SYSTEM
-- =====================================================

-- Assignment types enum
CREATE TYPE assignment_type_enum AS ENUM (
    'report_owner',
    'tester',
    'data_owner',
    'reviewer',
    'approver',
    'observer',
    'data_provider'
);

-- Assignment status enum
CREATE TYPE assignment_status_enum AS ENUM (
    'pending',
    'accepted',
    'declined',
    'completed',
    'reassigned',
    'expired'
);

-- Universal assignments table
CREATE TABLE universal_assignments (
    id SERIAL PRIMARY KEY,
    
    -- What is being assigned
    entity_type VARCHAR(50) NOT NULL, -- cycle_report, test_case, observation, etc.
    entity_id INTEGER NOT NULL,
    
    -- Who is assigned
    assignee_id INTEGER NOT NULL REFERENCES users(id),
    assignment_type assignment_type_enum NOT NULL,
    
    -- Assignment context
    cycle_id INTEGER REFERENCES test_cycles(id),
    phase VARCHAR(50),
    
    -- Assignment details
    assignment_reason TEXT,
    due_date DATE,
    priority VARCHAR(20) DEFAULT 'normal', -- urgent, high, normal, low
    
    -- Status tracking
    status assignment_status_enum DEFAULT 'pending',
    accepted_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by INTEGER REFERENCES users(id),
    
    -- Ensure unique active assignments
    CONSTRAINT unique_active_assignment UNIQUE (entity_type, entity_id, assignee_id, assignment_type, status)
);

-- Assignment history (track all changes)
CREATE TABLE assignment_history (
    id SERIAL PRIMARY KEY,
    assignment_id INTEGER NOT NULL REFERENCES universal_assignments(id),
    action VARCHAR(50) NOT NULL, -- created, accepted, declined, completed, reassigned
    from_assignee_id INTEGER REFERENCES users(id),
    to_assignee_id INTEGER REFERENCES users(id),
    comments TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id)
);

-- Assignment delegations
CREATE TABLE assignment_delegations (
    id SERIAL PRIMARY KEY,
    assignment_id INTEGER NOT NULL REFERENCES universal_assignments(id),
    delegated_to_id INTEGER NOT NULL REFERENCES users(id),
    delegation_reason TEXT,
    delegation_start DATE,
    delegation_end DATE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id)
);

-- Assignment notifications preferences
CREATE TABLE assignment_notification_preferences (
    user_id INTEGER NOT NULL REFERENCES users(id),
    assignment_type assignment_type_enum NOT NULL,
    email_enabled BOOLEAN DEFAULT true,
    in_app_enabled BOOLEAN DEFAULT true,
    sms_enabled BOOLEAN DEFAULT false,
    notification_lead_time INTEGER DEFAULT 1, -- days before due date
    PRIMARY KEY (user_id, assignment_type)
);

-- =====================================================
-- LOB ASSIGNMENT SYSTEM
-- =====================================================

-- LOB assignments for users
CREATE TABLE user_lob_assignments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    lob_id INTEGER NOT NULL REFERENCES lobs(id),
    role user_role_enum NOT NULL,
    is_primary BOOLEAN DEFAULT false,
    effective_date DATE DEFAULT CURRENT_DATE,
    expiry_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    UNIQUE(user_id, lob_id, role)
);

-- Report LOB associations
CREATE TABLE report_lob_associations (
    id SERIAL PRIMARY KEY,
    report_id INTEGER NOT NULL REFERENCES report_inventory(id),
    lob_id INTEGER NOT NULL REFERENCES lobs(id),
    association_type VARCHAR(50), -- primary, secondary, reference
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    UNIQUE(report_id, lob_id)
);

-- =====================================================
-- ROLE-BASED ACCESS CONTROL (RBAC)
-- =====================================================

-- Permissions
CREATE TABLE permissions (
    id SERIAL PRIMARY KEY,
    permission_code VARCHAR(100) UNIQUE NOT NULL,
    permission_name VARCHAR(255) NOT NULL,
    description TEXT,
    resource_type VARCHAR(50), -- report, cycle, user, etc.
    action VARCHAR(50), -- view, create, update, delete, approve
    is_active BOOLEAN DEFAULT true
);

-- Role permissions mapping
CREATE TABLE role_permissions (
    role user_role_enum NOT NULL,
    permission_id INTEGER NOT NULL REFERENCES permissions(id),
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    granted_by INTEGER REFERENCES users(id),
    PRIMARY KEY (role, permission_id)
);

-- User-specific permissions (overrides)
CREATE TABLE user_permissions (
    user_id INTEGER NOT NULL REFERENCES users(id),
    permission_id INTEGER NOT NULL REFERENCES permissions(id),
    is_granted BOOLEAN DEFAULT true, -- can be used to explicitly deny
    reason TEXT,
    expires_at TIMESTAMP WITH TIME ZONE,
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    granted_by INTEGER REFERENCES users(id),
    PRIMARY KEY (user_id, permission_id)
);

-- =====================================================
-- TEAM MANAGEMENT
-- =====================================================

-- Teams for grouping users
CREATE TABLE teams (
    id SERIAL PRIMARY KEY,
    team_name VARCHAR(255) NOT NULL,
    description TEXT,
    team_lead_id INTEGER REFERENCES users(id),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id)
);

-- Team members
CREATE TABLE team_members (
    team_id INTEGER NOT NULL REFERENCES teams(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    role_in_team VARCHAR(50), -- lead, member, observer
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (team_id, user_id)
);

-- Team assignments (assign work to teams)
CREATE TABLE team_assignments (
    id SERIAL PRIMARY KEY,
    team_id INTEGER NOT NULL REFERENCES teams(id),
    entity_type VARCHAR(50) NOT NULL,
    entity_id INTEGER NOT NULL,
    assignment_type VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id)
);

-- Indexes
CREATE INDEX idx_universal_assignments_entity ON universal_assignments(entity_type, entity_id);
CREATE INDEX idx_universal_assignments_assignee ON universal_assignments(assignee_id);
CREATE INDEX idx_universal_assignments_status ON universal_assignments(status);
CREATE INDEX idx_universal_assignments_due_date ON universal_assignments(due_date);
CREATE INDEX idx_assignment_history_assignment ON assignment_history(assignment_id);
CREATE INDEX idx_user_lob_assignments_user ON user_lob_assignments(user_id);
CREATE INDEX idx_user_lob_assignments_lob ON user_lob_assignments(lob_id);
CREATE INDEX idx_report_lob_associations_report ON report_lob_associations(report_id);
CREATE INDEX idx_team_members_user ON team_members(user_id);

-- Comments
COMMENT ON TABLE universal_assignments IS 'Flexible assignment system for any entity to any user';
COMMENT ON TABLE user_lob_assignments IS 'Associates users with LOBs for specific roles';
COMMENT ON TABLE report_lob_associations IS 'Links reports to relevant LOBs';
COMMENT ON TABLE permissions IS 'Granular permissions for role-based access control';
COMMENT ON TABLE teams IS 'Group users into teams for bulk assignments';