-- Create RFI Query Validation Tables
-- Run this script to add support for query-based evidence in the Request for Information phase

-- 1. Data Source table for reusable connections
CREATE TABLE IF NOT EXISTS cycle_report_rfi_data_sources (
    data_source_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phase_id INTEGER REFERENCES workflow_phases(phase_id),
    data_owner_id INTEGER NOT NULL REFERENCES users(user_id),
    source_name VARCHAR(255) NOT NULL,
    connection_type VARCHAR(50) NOT NULL CHECK (connection_type IN ('postgresql', 'mysql', 'oracle', 'csv', 'api')),
    connection_details JSONB NOT NULL, -- Encrypted connection info
    is_active BOOLEAN DEFAULT TRUE,
    test_query TEXT,
    
    -- Validation tracking
    last_validated_at TIMESTAMP WITH TIME ZONE,
    validation_status VARCHAR(50) CHECK (validation_status IN ('valid', 'invalid', 'pending')),
    validation_error TEXT,
    usage_count INTEGER DEFAULT 0,
    
    -- Audit fields
    created_by INTEGER NOT NULL REFERENCES users(user_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by INTEGER REFERENCES users(user_id),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    CONSTRAINT uq_data_source_name_owner UNIQUE (data_owner_id, source_name)
);

CREATE INDEX idx_rfi_data_sources_owner ON cycle_report_rfi_data_sources(data_owner_id);
CREATE INDEX idx_rfi_data_sources_phase ON cycle_report_rfi_data_sources(phase_id);
CREATE INDEX idx_rfi_data_sources_active ON cycle_report_rfi_data_sources(is_active);

-- 2. Query Validation Results table
CREATE TABLE IF NOT EXISTS cycle_report_rfi_query_validations (
    validation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    test_case_id INTEGER NOT NULL REFERENCES cycle_report_test_cases(id),
    data_source_id UUID NOT NULL REFERENCES cycle_report_rfi_data_sources(data_source_id),
    
    -- Query details
    query_text TEXT NOT NULL,
    query_parameters JSONB,
    
    -- Validation results
    validation_status VARCHAR(50) NOT NULL CHECK (validation_status IN ('success', 'failed', 'timeout')),
    validation_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    execution_time_ms INTEGER,
    
    -- Results
    row_count INTEGER,
    column_names JSONB, -- Array of column names
    sample_rows JSONB, -- First N rows as preview
    error_message TEXT,
    
    -- Column validation
    has_primary_keys BOOLEAN,
    has_target_attribute BOOLEAN,
    missing_columns JSONB, -- Array of missing column names
    
    -- User tracking
    validated_by INTEGER NOT NULL REFERENCES users(user_id),
    
    -- Indexes
    CONSTRAINT fk_validation_test_case FOREIGN KEY (test_case_id) REFERENCES cycle_report_test_cases(id) ON DELETE CASCADE
);

CREATE INDEX idx_rfi_query_validations_test_case ON cycle_report_rfi_query_validations(test_case_id);
CREATE INDEX idx_rfi_query_validations_data_source ON cycle_report_rfi_query_validations(data_source_id);
CREATE INDEX idx_rfi_query_validations_timestamp ON cycle_report_rfi_query_validations(validation_timestamp);
CREATE INDEX idx_rfi_query_validations_status ON cycle_report_rfi_query_validations(validation_status);

-- 3. Update the evidence table to properly reference data sources
-- Add foreign key constraint if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_evidence_data_source'
        AND table_name = 'cycle_report_request_info_testcase_source_evidence'
    ) THEN
        ALTER TABLE cycle_report_request_info_testcase_source_evidence
        ADD CONSTRAINT fk_evidence_data_source 
        FOREIGN KEY (data_source_id) 
        REFERENCES cycle_report_rfi_data_sources(data_source_id);
    END IF;
END $$;

-- 4. Add query validation tracking to evidence
ALTER TABLE cycle_report_request_info_testcase_source_evidence
ADD COLUMN IF NOT EXISTS query_validation_id UUID REFERENCES cycle_report_rfi_query_validations(validation_id);

-- 5. Create view for easy query evidence tracking
CREATE OR REPLACE VIEW vw_rfi_query_evidence AS
SELECT 
    e.id as evidence_id,
    e.test_case_id,
    e.phase_id,
    e.evidence_type,
    e.validation_status as evidence_status,
    e.submitted_by,
    e.submitted_at,
    tc.test_case_name,
    tc.attribute_name,
    tc.sample_id,
    ds.source_name,
    ds.connection_type,
    e.query_text,
    qv.validation_status as query_validation_status,
    qv.row_count,
    qv.has_primary_keys,
    qv.has_target_attribute,
    qv.validation_timestamp
FROM cycle_report_request_info_testcase_source_evidence e
JOIN cycle_report_test_cases tc ON e.test_case_id = tc.id
LEFT JOIN cycle_report_rfi_data_sources ds ON e.data_source_id = ds.data_source_id
LEFT JOIN cycle_report_rfi_query_validations qv ON e.query_validation_id = qv.validation_id
WHERE e.evidence_type = 'data_source';

-- Grant permissions (adjust roles as needed)
GRANT SELECT, INSERT, UPDATE ON cycle_report_rfi_data_sources TO synapse_app;
GRANT SELECT, INSERT ON cycle_report_rfi_query_validations TO synapse_app;
GRANT SELECT ON vw_rfi_query_evidence TO synapse_app;

-- Add comments for documentation
COMMENT ON TABLE cycle_report_rfi_data_sources IS 'Reusable data source configurations for query-based evidence in RFI phase';
COMMENT ON TABLE cycle_report_rfi_query_validations IS 'Query validation results before evidence submission';
COMMENT ON VIEW vw_rfi_query_evidence IS 'Consolidated view of query-based evidence with validation status';