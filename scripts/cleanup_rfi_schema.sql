-- RFI Schema Cleanup and Consolidation
-- This script consolidates redundant tables and fixes type mismatches

BEGIN;

-- 1. First, backup existing data
CREATE TABLE IF NOT EXISTS backup_document_submissions AS 
SELECT * FROM cycle_report_test_cases_document_submissions;

CREATE TABLE IF NOT EXISTS backup_source_evidence AS 
SELECT * FROM cycle_report_request_info_testcase_source_evidence;

-- 2. Create unified evidence table with proper structure
CREATE TABLE IF NOT EXISTS cycle_report_rfi_evidence (
    id SERIAL PRIMARY KEY,
    test_case_id INTEGER NOT NULL REFERENCES cycle_report_test_cases(id),
    phase_id INTEGER NOT NULL REFERENCES workflow_phases(phase_id),
    cycle_id INTEGER NOT NULL REFERENCES test_cycles(cycle_id),
    report_id INTEGER NOT NULL REFERENCES reports(id),
    sample_id VARCHAR(255) NOT NULL,
    
    -- Evidence type and version
    evidence_type VARCHAR(20) NOT NULL CHECK (evidence_type IN ('document', 'data_source')),
    version_number INTEGER DEFAULT 1 NOT NULL,
    is_current BOOLEAN DEFAULT TRUE NOT NULL,
    parent_evidence_id INTEGER REFERENCES cycle_report_rfi_evidence(id),
    
    -- Common submission fields
    submitted_by INTEGER NOT NULL REFERENCES users(user_id),
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    submission_notes TEXT,
    
    -- Validation and review
    validation_status VARCHAR(50) DEFAULT 'pending' NOT NULL,
    validation_notes TEXT,
    validated_by INTEGER REFERENCES users(user_id),
    validated_at TIMESTAMP WITH TIME ZONE,
    
    -- Tester decision fields
    tester_decision VARCHAR(50) CHECK (tester_decision IN ('approved', 'rejected', 'requires_revision')),
    tester_notes TEXT,
    decided_by INTEGER REFERENCES users(user_id),
    decided_at TIMESTAMP WITH TIME ZONE,
    requires_resubmission BOOLEAN DEFAULT FALSE,
    resubmission_deadline TIMESTAMP WITH TIME ZONE,
    
    -- Document specific fields (nullable)
    original_filename VARCHAR(255),
    stored_filename VARCHAR(255),
    file_path VARCHAR(500),
    file_size_bytes INTEGER,
    file_hash VARCHAR(64),
    mime_type VARCHAR(100),
    
    -- Data source specific fields (nullable)
    rfi_data_source_id UUID REFERENCES cycle_report_rfi_data_sources(data_source_id),
    planning_data_source_id INTEGER REFERENCES cycle_report_planning_data_sources(id),
    query_text TEXT,
    query_parameters JSONB,
    query_validation_id UUID REFERENCES cycle_report_rfi_query_validations(validation_id),
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by INTEGER NOT NULL REFERENCES users(user_id),
    updated_by INTEGER NOT NULL REFERENCES users(user_id),
    
    -- Constraints
    CONSTRAINT uq_test_case_version UNIQUE(test_case_id, version_number),
    CONSTRAINT check_evidence_type_fields CHECK (
        (evidence_type = 'document' AND original_filename IS NOT NULL AND file_path IS NOT NULL) OR
        (evidence_type = 'data_source' AND query_text IS NOT NULL)
    )
);

-- Create indexes
CREATE INDEX idx_rfi_evidence_test_case ON cycle_report_rfi_evidence(test_case_id);
CREATE INDEX idx_rfi_evidence_phase ON cycle_report_rfi_evidence(phase_id);
CREATE INDEX idx_rfi_evidence_current ON cycle_report_rfi_evidence(is_current) WHERE is_current = true;
CREATE INDEX idx_rfi_evidence_type ON cycle_report_rfi_evidence(evidence_type);
CREATE INDEX idx_rfi_evidence_status ON cycle_report_rfi_evidence(validation_status);

-- 3. Migrate document submissions to unified table
INSERT INTO cycle_report_rfi_evidence (
    test_case_id,
    phase_id,
    cycle_id,
    report_id,
    sample_id,
    evidence_type,
    version_number,
    is_current,
    parent_evidence_id,
    submitted_by,
    submitted_at,
    submission_notes,
    validation_status,
    validation_notes,
    validated_by,
    validated_at,
    original_filename,
    stored_filename,
    file_path,
    file_size_bytes,
    file_hash,
    mime_type,
    created_at,
    updated_at,
    created_by,
    updated_by
)
SELECT 
    ds.test_case_id,
    ds.phase_id,
    tc.phase_id as cycle_id,  -- Get from test case
    tc.phase_id as report_id, -- Get from test case
    tc.sample_id,
    'document' as evidence_type,
    ds.submission_number as version_number,
    ds.is_current,
    NULL as parent_evidence_id, -- Will update later
    ds.data_owner_id as submitted_by,
    ds.submitted_at,
    ds.submission_notes,
    ds.validation_status,
    ds.validation_notes,
    ds.validated_by,
    ds.validated_at,
    ds.original_filename,
    ds.stored_filename,
    ds.file_path,
    ds.file_size_bytes,
    ds.file_hash,
    ds.mime_type,
    ds.created_at,
    ds.updated_at,
    COALESCE(ds.created_by, ds.data_owner_id),
    COALESCE(ds.updated_by, ds.data_owner_id)
FROM cycle_report_test_cases_document_submissions ds
JOIN cycle_report_test_cases tc ON ds.test_case_id = tc.id
WHERE NOT EXISTS (
    SELECT 1 FROM cycle_report_rfi_evidence e 
    WHERE e.test_case_id = ds.test_case_id 
    AND e.version_number = ds.submission_number
);

-- 4. Migrate source evidence to unified table (get cycle_id and report_id from test case)
INSERT INTO cycle_report_rfi_evidence (
    test_case_id,
    phase_id,
    cycle_id,
    report_id,
    sample_id,
    evidence_type,
    version_number,
    is_current,
    submitted_by,
    submitted_at,
    submission_notes,
    validation_status,
    validation_notes,
    validated_by,
    validated_at,
    original_filename,
    file_path,
    planning_data_source_id,
    query_text,
    query_parameters,
    created_at,
    updated_at,
    created_by,
    updated_by
)
SELECT 
    se.test_case_id,
    se.phase_id,
    wp.cycle_id,
    wp.report_id,
    se.sample_id,
    se.evidence_type,
    se.version_number,
    se.is_current,
    se.submitted_by,
    se.submitted_at,
    se.submission_notes,
    se.validation_status,
    se.validation_notes,
    se.validated_by,
    se.validated_at,
    se.document_name,
    se.document_path,
    se.data_source_id,
    se.query_text,
    se.query_parameters,
    se.created_at,
    se.updated_at,
    se.created_by,
    se.updated_by
FROM cycle_report_request_info_testcase_source_evidence se
JOIN workflow_phases wp ON se.phase_id = wp.phase_id
WHERE NOT EXISTS (
    SELECT 1 FROM cycle_report_rfi_evidence e 
    WHERE e.test_case_id = se.test_case_id 
    AND e.evidence_type = se.evidence_type
    AND e.version_number = se.version_number
);

-- 5. Update parent evidence relationships
UPDATE cycle_report_rfi_evidence e1
SET parent_evidence_id = e2.id
FROM cycle_report_rfi_evidence e2
WHERE e1.test_case_id = e2.test_case_id
AND e1.version_number = e2.version_number + 1
AND e1.evidence_type = e2.evidence_type;

-- 6. Create simplified views for easy access
CREATE OR REPLACE VIEW vw_rfi_current_evidence AS
SELECT 
    e.*,
    tc.test_case_name,
    tc.attribute_name,
    tc.data_owner_id,
    u.first_name || ' ' || u.last_name as data_owner_name,
    ds.source_name as data_source_name
FROM cycle_report_rfi_evidence e
JOIN cycle_report_test_cases tc ON e.test_case_id = tc.id
JOIN users u ON tc.data_owner_id = u.user_id
LEFT JOIN cycle_report_rfi_data_sources ds ON e.rfi_data_source_id = ds.data_source_id
WHERE e.is_current = true;

-- 7. Drop redundant columns from test cases table
ALTER TABLE cycle_report_test_cases 
DROP COLUMN IF EXISTS submission_deadline CASCADE,
DROP COLUMN IF EXISTS submitted_at CASCADE,
DROP COLUMN IF EXISTS acknowledged_at CASCADE;

-- 8. Create function to handle evidence versioning
CREATE OR REPLACE FUNCTION create_evidence_revision(
    p_test_case_id INTEGER,
    p_revision_reason TEXT,
    p_revision_deadline TIMESTAMP WITH TIME ZONE,
    p_requested_by INTEGER
) RETURNS INTEGER AS $$
DECLARE
    v_new_evidence_id INTEGER;
    v_current_evidence RECORD;
BEGIN
    -- Get current evidence
    SELECT * INTO v_current_evidence
    FROM cycle_report_rfi_evidence
    WHERE test_case_id = p_test_case_id
    AND is_current = true
    LIMIT 1;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'No current evidence found for test case %', p_test_case_id;
    END IF;
    
    -- Mark current as not current
    UPDATE cycle_report_rfi_evidence
    SET is_current = false,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = v_current_evidence.id;
    
    -- Create revision request in current record
    UPDATE cycle_report_rfi_evidence
    SET tester_decision = 'requires_revision',
        tester_notes = p_revision_reason,
        decided_by = p_requested_by,
        decided_at = CURRENT_TIMESTAMP,
        requires_resubmission = true,
        resubmission_deadline = p_revision_deadline
    WHERE id = v_current_evidence.id;
    
    RETURN v_current_evidence.id;
END;
$$ LANGUAGE plpgsql;

-- 9. Grant permissions
GRANT SELECT, INSERT, UPDATE ON cycle_report_rfi_evidence TO synapse_app;
GRANT SELECT ON vw_rfi_current_evidence TO synapse_app;
GRANT EXECUTE ON FUNCTION create_evidence_revision TO synapse_app;

-- 10. Add comments for documentation
COMMENT ON TABLE cycle_report_rfi_evidence IS 'Unified evidence table for RFI phase - combines documents and data sources';
COMMENT ON VIEW vw_rfi_current_evidence IS 'View of current evidence versions only';
COMMENT ON FUNCTION create_evidence_revision IS 'Creates a revision request for evidence resubmission';

COMMIT;

-- After verification, drop old tables (run separately after testing)
-- DROP TABLE IF EXISTS cycle_report_test_cases_document_submissions CASCADE;
-- DROP TABLE IF EXISTS cycle_report_request_info_testcase_source_evidence CASCADE;
-- DROP TABLE IF EXISTS cycle_report_request_info_evidence_validation CASCADE;
-- DROP TABLE IF EXISTS cycle_report_request_info_tester_decisions CASCADE;