-- Create unified evidence table (without permissions)
BEGIN;

-- Create unified evidence table with proper structure
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
CREATE INDEX IF NOT EXISTS idx_rfi_evidence_test_case ON cycle_report_rfi_evidence(test_case_id);
CREATE INDEX IF NOT EXISTS idx_rfi_evidence_phase ON cycle_report_rfi_evidence(phase_id);
CREATE INDEX IF NOT EXISTS idx_rfi_evidence_current ON cycle_report_rfi_evidence(is_current) WHERE is_current = true;
CREATE INDEX IF NOT EXISTS idx_rfi_evidence_type ON cycle_report_rfi_evidence(evidence_type);
CREATE INDEX IF NOT EXISTS idx_rfi_evidence_status ON cycle_report_rfi_evidence(validation_status);

-- Create simplified view for easy access
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

-- Create function to handle evidence versioning
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

COMMIT;