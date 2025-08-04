-- Create redesign tables with correct column references

-- First, create report_inventory
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
    created_by INTEGER REFERENCES users(user_id),
    updated_by INTEGER REFERENCES users(user_id)
);

-- Create the planning attributes table
CREATE TABLE IF NOT EXISTS cycle_report_attributes_planning (
    id SERIAL PRIMARY KEY,
    cycle_report_id INTEGER NOT NULL REFERENCES cycle_reports(cycle_report_id),
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
    created_by INTEGER REFERENCES users(user_id),
    updated_by INTEGER REFERENCES users(user_id),
    approved_by INTEGER REFERENCES users(user_id),
    approved_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(cycle_report_id, attribute_name, version)
);

-- Create version history table
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
    created_by INTEGER REFERENCES users(user_id)
);

-- Create test cases table
CREATE TABLE IF NOT EXISTS cycle_report_test_cases (
    id SERIAL PRIMARY KEY,
    cycle_report_id INTEGER NOT NULL REFERENCES cycle_reports(cycle_report_id),
    test_case_number VARCHAR(50) NOT NULL,
    test_case_name VARCHAR(255) NOT NULL,
    description TEXT,
    expected_outcome TEXT,
    test_type VARCHAR(50),
    query_text TEXT,
    version INTEGER DEFAULT 1,
    status phase_status_enum DEFAULT 'Not Started',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(user_id),
    updated_by INTEGER REFERENCES users(user_id),
    UNIQUE(cycle_report_id, test_case_number, version)
);

-- Create document submissions table
CREATE TABLE IF NOT EXISTS cycle_report_document_submissions (
    id SERIAL PRIMARY KEY,
    cycle_report_id INTEGER NOT NULL REFERENCES cycle_reports(cycle_report_id),
    data_owner_id INTEGER REFERENCES users(user_id),
    document_type VARCHAR(50),
    file_name VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_size BIGINT,
    submission_date DATE,
    version INTEGER DEFAULT 1,
    status phase_status_enum DEFAULT 'Not Started',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(user_id),
    updated_by INTEGER REFERENCES users(user_id)
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_report_inventory_number ON report_inventory(report_number);
CREATE INDEX IF NOT EXISTS idx_planning_cycle_report ON cycle_report_attributes_planning(cycle_report_id);
CREATE INDEX IF NOT EXISTS idx_planning_status ON cycle_report_attributes_planning(status);
CREATE INDEX IF NOT EXISTS idx_test_cases_cycle ON cycle_report_test_cases(cycle_report_id);
CREATE INDEX IF NOT EXISTS idx_document_submissions_cycle ON cycle_report_document_submissions(cycle_report_id);

\echo 'Core redesign tables created successfully'