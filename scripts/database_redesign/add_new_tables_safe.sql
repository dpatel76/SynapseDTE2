-- Safe addition of new redesigned tables alongside existing ones
-- This preserves the current working system

-- Create new enums if they don't exist
DO $$ BEGIN
    CREATE TYPE report_status_enum AS ENUM ('Active', 'Inactive', 'Under Review', 'Archived');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE cycle_status_enum AS ENUM ('Draft', 'Planning', 'In Progress', 'Review', 'Completed', 'Cancelled');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE security_classification_enum AS ENUM ('Public', 'Internal', 'Confidential', 'Restricted', 'HRCI');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE assignment_type_enum AS ENUM ('report_owner', 'tester', 'data_owner', 'reviewer', 'approver', 'observer', 'data_provider');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE assignment_status_enum AS ENUM ('pending', 'accepted', 'declined', 'completed', 'reassigned', 'expired');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create report_inventory table (new name for reports)
CREATE TABLE IF NOT EXISTS report_inventory (
    id SERIAL PRIMARY KEY,
    report_number VARCHAR(50) UNIQUE NOT NULL,
    report_name VARCHAR(255) NOT NULL,
    description TEXT,
    frequency VARCHAR(50),
    business_unit VARCHAR(100),
    regulatory_requirement BOOLEAN DEFAULT false,
    status report_status_enum DEFAULT 'Active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id)
);

-- Create new phase tables with cycle_report_* naming
CREATE TABLE IF NOT EXISTS cycle_report_attributes_planning (
    id SERIAL PRIMARY KEY,
    cycle_report_id INTEGER NOT NULL REFERENCES cycle_reports(id),
    attribute_name VARCHAR(255) NOT NULL,
    description TEXT,
    data_type data_type_enum NOT NULL,
    is_mandatory BOOLEAN DEFAULT false,
    is_cde BOOLEAN DEFAULT false,
    has_issues BOOLEAN DEFAULT false,
    is_primary_key BOOLEAN DEFAULT false,
    information_security_classification security_classification_enum DEFAULT 'Internal',
    data_source_id INTEGER REFERENCES data_sources(data_source_id),
    source_table VARCHAR(255),
    source_column VARCHAR(255),
    version INTEGER DEFAULT 1,
    status phase_status_enum DEFAULT 'Not Started',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id),
    approved_by INTEGER REFERENCES users(id),
    approved_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(cycle_report_id, attribute_name, version)
);

-- Version history table
CREATE TABLE IF NOT EXISTS cycle_report_attributes_planning_version_history (
    id SERIAL PRIMARY KEY,
    planning_attribute_id INTEGER NOT NULL,
    cycle_report_id INTEGER NOT NULL,
    attribute_name VARCHAR(255) NOT NULL,
    description TEXT,
    data_type data_type_enum NOT NULL,
    is_mandatory BOOLEAN,
    is_cde BOOLEAN,
    has_issues BOOLEAN,
    is_primary_key BOOLEAN,
    information_security_classification security_classification_enum,
    data_source_id INTEGER,
    source_table VARCHAR(255),
    source_column VARCHAR(255),
    version INTEGER NOT NULL,
    change_reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id)
);

-- Universal assignments table
CREATE TABLE IF NOT EXISTS universal_assignments (
    id SERIAL PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL,
    entity_id INTEGER NOT NULL,
    assignee_id INTEGER NOT NULL REFERENCES users(id),
    assignment_type assignment_type_enum NOT NULL,
    cycle_id INTEGER REFERENCES test_cycles(id),
    phase VARCHAR(50),
    assignment_reason TEXT,
    due_date DATE,
    priority VARCHAR(20) DEFAULT 'normal',
    status assignment_status_enum DEFAULT 'pending',
    accepted_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by INTEGER REFERENCES users(id),
    CONSTRAINT unique_active_assignment UNIQUE (entity_type, entity_id, assignee_id, assignment_type, status)
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_report_inventory_number ON report_inventory(report_number);
CREATE INDEX IF NOT EXISTS idx_planning_cycle_report ON cycle_report_attributes_planning(cycle_report_id);
CREATE INDEX IF NOT EXISTS idx_planning_status ON cycle_report_attributes_planning(status);
CREATE INDEX IF NOT EXISTS idx_universal_assignments_entity ON universal_assignments(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_universal_assignments_assignee ON universal_assignments(assignee_id);
CREATE INDEX IF NOT EXISTS idx_universal_assignments_status ON universal_assignments(status);

-- Comments
COMMENT ON TABLE report_inventory IS 'Master list of all reports in the organization';
COMMENT ON TABLE cycle_report_attributes_planning IS 'Phase 1: Define and classify report attributes';
COMMENT ON TABLE universal_assignments IS 'Flexible assignment system for any entity to any user';

\echo 'New tables added successfully alongside existing system'