-- Create phase tables with correct references to existing schema

-- Create the planning attributes table
CREATE TABLE IF NOT EXISTS cycle_report_attributes_planning (
    id SERIAL PRIMARY KEY,
    cycle_id INTEGER NOT NULL,
    report_id INTEGER NOT NULL,
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
    FOREIGN KEY (cycle_id, report_id) REFERENCES cycle_reports(cycle_id, report_id),
    UNIQUE(cycle_id, report_id, attribute_name, version)
);

-- Create test cases table
CREATE TABLE IF NOT EXISTS cycle_report_test_cases (
    id SERIAL PRIMARY KEY,
    cycle_id INTEGER NOT NULL,
    report_id INTEGER NOT NULL,
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
    FOREIGN KEY (cycle_id, report_id) REFERENCES cycle_reports(cycle_id, report_id),
    UNIQUE(cycle_id, report_id, test_case_number, version)
);

-- Create document submissions table
CREATE TABLE IF NOT EXISTS cycle_report_document_submissions (
    id SERIAL PRIMARY KEY,
    cycle_id INTEGER NOT NULL,
    report_id INTEGER NOT NULL,
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
    updated_by INTEGER REFERENCES users(user_id),
    FOREIGN KEY (cycle_id, report_id) REFERENCES cycle_reports(cycle_id, report_id)
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_planning_cycle_report ON cycle_report_attributes_planning(cycle_id, report_id);
CREATE INDEX IF NOT EXISTS idx_planning_status ON cycle_report_attributes_planning(status);
CREATE INDEX IF NOT EXISTS idx_test_cases_cycle_report ON cycle_report_test_cases(cycle_id, report_id);
CREATE INDEX IF NOT EXISTS idx_document_submissions_cycle_report ON cycle_report_document_submissions(cycle_id, report_id);

\echo 'Phase tables created successfully'