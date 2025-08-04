-- Complete Database Redesign: Phase-Specific Tables
-- Following cycle_report_* naming pattern

-- =====================================================
-- PHASE 1: PLANNING (ATTRIBUTES)
-- =====================================================

-- Planning phase attributes for each cycle report
CREATE TABLE cycle_report_planning_attributes (
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
    data_source_id INTEGER REFERENCES data_sources(id),
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

-- Version history for planning attributes
CREATE TABLE cycle_report_planning_attributes_version_history (
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

-- =====================================================
-- PHASE 2: DATA PROFILING
-- =====================================================

-- Data profiling configuration for cycle reports
CREATE TABLE cycle_report_data_profiling (
    id SERIAL PRIMARY KEY,
    cycle_report_id INTEGER NOT NULL REFERENCES cycle_reports(id),
    profiling_start_date DATE,
    profiling_end_date DATE,
    record_count BIGINT,
    execution_time_seconds INTEGER,
    status phase_status_enum DEFAULT 'Not Started',
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id),
    approved_by INTEGER REFERENCES users(id),
    approved_at TIMESTAMP WITH TIME ZONE
);

-- Profiling results per attribute
CREATE TABLE cycle_report_profiling_results (
    id SERIAL PRIMARY KEY,
    profiling_id INTEGER NOT NULL REFERENCES cycle_report_data_profiling(id),
    attribute_id INTEGER NOT NULL REFERENCES cycle_report_planning_attributes(id),
    total_count BIGINT,
    null_count BIGINT,
    distinct_count BIGINT,
    min_value TEXT,
    max_value TEXT,
    avg_length INTEGER,
    pattern_detected TEXT,
    anomaly_score DECIMAL(5,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- PHASE 3: SCOPING
-- =====================================================

-- Scoping decisions for attributes
CREATE TABLE cycle_report_attributes_scoping (
    id SERIAL PRIMARY KEY,
    cycle_report_id INTEGER NOT NULL REFERENCES cycle_reports(id),
    attribute_id INTEGER NOT NULL REFERENCES cycle_report_planning_attributes(id),
    in_scope BOOLEAN NOT NULL,
    scope_reason TEXT,
    risk_rating VARCHAR(20), -- High, Medium, Low
    testing_required BOOLEAN DEFAULT true,
    version INTEGER DEFAULT 1,
    status phase_status_enum DEFAULT 'Not Started',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id),
    approved_by INTEGER REFERENCES users(id),
    approved_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(cycle_report_id, attribute_id, version)
);

-- Version history for scoping
CREATE TABLE cycle_report_attributes_scoping_version_history (
    id SERIAL PRIMARY KEY,
    scoping_id INTEGER NOT NULL,
    cycle_report_id INTEGER NOT NULL,
    attribute_id INTEGER NOT NULL,
    in_scope BOOLEAN,
    scope_reason TEXT,
    risk_rating VARCHAR(20),
    testing_required BOOLEAN,
    version INTEGER NOT NULL,
    change_reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id)
);

-- =====================================================
-- PHASE 4: SAMPLE SELECTION
-- =====================================================

-- Sample selection configuration
CREATE TABLE cycle_report_sample_selection (
    id SERIAL PRIMARY KEY,
    cycle_report_id INTEGER NOT NULL REFERENCES cycle_reports(id),
    lob_id INTEGER NOT NULL REFERENCES lobs(id),
    sample_size INTEGER NOT NULL,
    selection_method VARCHAR(50), -- Random, Stratified, Risk-based
    selection_criteria TEXT,
    version INTEGER DEFAULT 1,
    status phase_status_enum DEFAULT 'Not Started',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id),
    approved_by INTEGER REFERENCES users(id),
    approved_at TIMESTAMP WITH TIME ZONE
);

-- Individual samples selected
CREATE TABLE cycle_report_samples (
    id SERIAL PRIMARY KEY,
    selection_id INTEGER NOT NULL REFERENCES cycle_report_sample_selection(id),
    sample_identifier VARCHAR(255) NOT NULL,
    sample_data JSONB,
    risk_score DECIMAL(5,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- PHASE 5: DATA OWNER IDENTIFICATION
-- =====================================================

-- Data owner assignments for attribute/LOB combinations
CREATE TABLE cycle_report_data_owners (
    id SERIAL PRIMARY KEY,
    cycle_report_id INTEGER NOT NULL REFERENCES cycle_reports(id),
    attribute_id INTEGER NOT NULL REFERENCES cycle_report_planning_attributes(id),
    lob_id INTEGER NOT NULL REFERENCES lobs(id),
    data_owner_id INTEGER REFERENCES users(id),
    assignment_date DATE,
    version INTEGER DEFAULT 1,
    status phase_status_enum DEFAULT 'Not Started',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id),
    UNIQUE(cycle_report_id, attribute_id, lob_id, version)
);

-- =====================================================
-- PHASE 6: SOURCE EVIDENCE (REQUEST INFO)
-- =====================================================

-- Test cases for cycle reports
CREATE TABLE cycle_report_test_cases (
    id SERIAL PRIMARY KEY,
    cycle_report_id INTEGER NOT NULL REFERENCES cycle_reports(id),
    test_case_number VARCHAR(50) NOT NULL,
    test_case_name VARCHAR(255) NOT NULL,
    description TEXT,
    expected_outcome TEXT,
    test_type VARCHAR(50), -- Manual, Automated, Query
    query_text TEXT,
    version INTEGER DEFAULT 1,
    status phase_status_enum DEFAULT 'Not Started',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id),
    UNIQUE(cycle_report_id, test_case_number, version)
);

-- Document submissions for evidence
CREATE TABLE cycle_report_document_submissions (
    id SERIAL PRIMARY KEY,
    cycle_report_id INTEGER NOT NULL REFERENCES cycle_reports(id),
    data_owner_id INTEGER REFERENCES users(id),
    document_type VARCHAR(50), -- Screenshot, Report, Query Result
    file_name VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_size BIGINT,
    submission_date DATE,
    version INTEGER DEFAULT 1,
    status phase_status_enum DEFAULT 'Not Started',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id)
);

-- =====================================================
-- PHASE 7: TEST EXECUTION
-- =====================================================

-- Test execution results
CREATE TABLE cycle_report_test_execution (
    id SERIAL PRIMARY KEY,
    cycle_report_id INTEGER NOT NULL REFERENCES cycle_reports(id),
    test_case_id INTEGER NOT NULL REFERENCES cycle_report_test_cases(id),
    sample_id INTEGER REFERENCES cycle_report_samples(id),
    execution_date DATE,
    result VARCHAR(20), -- Pass, Fail, N/A, Blocked
    actual_outcome TEXT,
    evidence_path TEXT,
    version INTEGER DEFAULT 1,
    status phase_status_enum DEFAULT 'Not Started',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    executed_by INTEGER REFERENCES users(id),
    reviewed_by INTEGER REFERENCES users(id),
    approved_by INTEGER REFERENCES users(id),
    approved_at TIMESTAMP WITH TIME ZONE
);

-- Test failures for investigation
CREATE TABLE cycle_report_test_failures (
    id SERIAL PRIMARY KEY,
    execution_id INTEGER NOT NULL REFERENCES cycle_report_test_execution(id),
    failure_reason TEXT,
    root_cause TEXT,
    impact_assessment TEXT,
    remediation_plan TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id)
);

-- =====================================================
-- PHASE 8: OBSERVATIONS
-- =====================================================

-- Grouped observations from test failures
CREATE TABLE cycle_report_observations (
    id SERIAL PRIMARY KEY,
    cycle_report_id INTEGER NOT NULL REFERENCES cycle_reports(id),
    observation_number VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    impact_level VARCHAR(20), -- High, Medium, Low
    recommendation TEXT,
    management_response TEXT,
    target_date DATE,
    version INTEGER DEFAULT 1,
    status phase_status_enum DEFAULT 'Not Started',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id),
    approved_by INTEGER REFERENCES users(id),
    approved_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(cycle_report_id, observation_number, version)
);

-- Link test failures to observations
CREATE TABLE cycle_report_observation_failures (
    observation_id INTEGER NOT NULL REFERENCES cycle_report_observations(id),
    test_failure_id INTEGER NOT NULL REFERENCES cycle_report_test_failures(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (observation_id, test_failure_id)
);

-- =====================================================
-- PHASE 9: FINAL REPORT
-- =====================================================

-- Final test report
CREATE TABLE cycle_report_final (
    id SERIAL PRIMARY KEY,
    cycle_report_id INTEGER NOT NULL REFERENCES cycle_reports(id),
    executive_summary TEXT,
    test_approach TEXT,
    test_results_summary TEXT,
    key_findings TEXT,
    recommendations TEXT,
    conclusion TEXT,
    version INTEGER DEFAULT 1,
    status phase_status_enum DEFAULT 'Not Started',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id),
    approved_by INTEGER REFERENCES users(id),
    approved_at TIMESTAMP WITH TIME ZONE,
    finalized_by INTEGER REFERENCES users(id),
    finalized_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for phase tables
CREATE INDEX idx_planning_cycle_report ON cycle_report_attributes_planning(cycle_report_id);
CREATE INDEX idx_planning_status ON cycle_report_attributes_planning(status);
CREATE INDEX idx_scoping_cycle_report ON cycle_report_attributes_scoping(cycle_report_id);
CREATE INDEX idx_sample_selection_cycle ON cycle_report_sample_selection(cycle_report_id);
CREATE INDEX idx_data_owners_cycle ON cycle_report_data_owners(cycle_report_id);
CREATE INDEX idx_test_cases_cycle ON cycle_report_test_cases(cycle_report_id);
CREATE INDEX idx_test_execution_cycle ON cycle_report_test_execution(cycle_report_id);
CREATE INDEX idx_observations_cycle ON cycle_report_observations(cycle_report_id);
CREATE INDEX idx_final_report_cycle ON cycle_report_final(cycle_report_id);

-- Comments
COMMENT ON TABLE cycle_report_attributes_planning IS 'Phase 1: Define and classify report attributes';
COMMENT ON TABLE cycle_report_data_profiling IS 'Phase 2: Profile data to understand patterns';
COMMENT ON TABLE cycle_report_attributes_scoping IS 'Phase 3: Determine which attributes to test';
COMMENT ON TABLE cycle_report_sample_selection IS 'Phase 4: Select samples for testing';
COMMENT ON TABLE cycle_report_data_owners IS 'Phase 5: Assign data owners to attribute/LOB combinations';
COMMENT ON TABLE cycle_report_test_cases IS 'Phase 6: Define test cases and gather evidence';
COMMENT ON TABLE cycle_report_test_execution IS 'Phase 7: Execute tests and record results';
COMMENT ON TABLE cycle_report_observations IS 'Phase 8: Group test failures into observations';
COMMENT ON TABLE cycle_report_final IS 'Phase 9: Create final test report';