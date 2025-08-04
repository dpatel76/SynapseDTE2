-- Create simplified observation management tables (CORRECTED VERSION)
-- This implements the 2-table architecture from the implementation plan

-- Drop existing tables if they exist (cleanup)
DROP TABLE IF EXISTS cycle_report_observations_unified CASCADE;
DROP TABLE IF EXISTS cycle_report_observation_groups CASCADE;

-- Create main observation groups table with built-in approval workflow
CREATE TABLE cycle_report_observation_groups (
    id SERIAL PRIMARY KEY,
    phase_id INTEGER NOT NULL REFERENCES workflow_phases(phase_id),
    cycle_id INTEGER NOT NULL REFERENCES test_cycles(cycle_id),
    report_id INTEGER NOT NULL REFERENCES reports(id),
    
    -- Group identification (grouped by attribute + LOB)
    group_name VARCHAR(255) NOT NULL,
    group_description TEXT,
    attribute_id INTEGER NOT NULL REFERENCES cycle_report_planning_attributes(id),
    lob_id INTEGER NOT NULL REFERENCES lobs(lob_id),
    
    -- Group metadata
    observation_count INTEGER DEFAULT 0,
    severity_level VARCHAR(50) DEFAULT 'medium' CHECK (severity_level IN ('high', 'medium', 'low')),
    issue_type VARCHAR(100) NOT NULL CHECK (issue_type IN ('data_quality', 'process_failure', 'system_error', 'compliance_gap')),
    
    -- Group summary
    issue_summary TEXT NOT NULL,
    impact_description TEXT,
    proposed_resolution TEXT,
    
    -- Status and workflow (embedded approval workflow)
    status VARCHAR(50) DEFAULT 'draft' CHECK (status IN ('draft', 'pending_tester_review', 'tester_approved', 'pending_report_owner_approval', 'report_owner_approved', 'rejected', 'resolved', 'closed')),
    
    -- Tester Review (built-in)
    tester_review_status VARCHAR(50) CHECK (tester_review_status IN ('approved', 'rejected', 'needs_clarification')),
    tester_review_notes TEXT,
    tester_review_score INTEGER CHECK (tester_review_score BETWEEN 1 AND 100),
    tester_reviewed_by INTEGER REFERENCES users(user_id),
    tester_reviewed_at TIMESTAMP WITH TIME ZONE,
    
    -- Report Owner Approval (built-in)
    report_owner_approval_status VARCHAR(50) CHECK (report_owner_approval_status IN ('approved', 'rejected', 'needs_clarification')),
    report_owner_approval_notes TEXT,
    report_owner_approved_by INTEGER REFERENCES users(user_id),
    report_owner_approved_at TIMESTAMP WITH TIME ZONE,
    
    -- Clarification handling (built-in)
    clarification_requested BOOLEAN DEFAULT FALSE,
    clarification_request_text TEXT,
    clarification_response TEXT,
    clarification_due_date TIMESTAMP WITH TIME ZONE,
    
    -- Resolution tracking (built-in)
    resolution_status VARCHAR(50) DEFAULT 'pending' CHECK (resolution_status IN ('pending', 'in_progress', 'completed', 'deferred')),
    resolution_approach TEXT,
    resolution_timeline TEXT,
    resolution_owner INTEGER REFERENCES users(user_id),
    resolution_notes TEXT,
    resolved_by INTEGER REFERENCES users(user_id),
    resolved_at TIMESTAMP WITH TIME ZONE,
    
    -- Detection information
    detection_method VARCHAR(50) NOT NULL CHECK (detection_method IN ('auto_detected', 'manual_review', 'escalation')),
    detected_by INTEGER NOT NULL REFERENCES users(user_id),
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL REFERENCES users(user_id),
    updated_by INTEGER NOT NULL REFERENCES users(user_id),
    
    -- Constraints
    UNIQUE(attribute_id, lob_id, phase_id) -- One group per attribute+LOB combination
);

-- Create individual observations table (one per test case failure)
CREATE TABLE cycle_report_observations_unified (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES cycle_report_observation_groups(id) ON DELETE CASCADE,
    
    -- Link to test execution that generated this observation (one-to-one relationship)
    test_execution_id INTEGER NOT NULL REFERENCES cycle_report_test_execution_results(id),
    test_case_id VARCHAR(255) NOT NULL,
    
    -- Test context (tied to specific sample and attribute for LOB)
    attribute_id INTEGER NOT NULL REFERENCES cycle_report_planning_attributes(id),
    sample_id VARCHAR(255) NOT NULL,
    lob_id INTEGER NOT NULL REFERENCES lobs(lob_id),
    
    -- Observation details
    observation_title VARCHAR(255) NOT NULL,
    observation_description TEXT NOT NULL,
    
    -- Test failure details
    expected_value TEXT,
    actual_value TEXT,
    variance_details JSONB,
    test_result VARCHAR(50) CHECK (test_result IN ('fail', 'inconclusive')),
    
    -- Evidence and documentation
    evidence_files JSONB, -- List of file paths, screenshots, etc.
    supporting_documentation TEXT,
    
    -- Individual observation metadata
    confidence_level FLOAT CHECK (confidence_level BETWEEN 0.0 AND 1.0),
    reproducible BOOLEAN DEFAULT FALSE,
    frequency_estimate VARCHAR(50) CHECK (frequency_estimate IN ('isolated', 'occasional', 'frequent', 'systematic')),
    
    -- Impact assessment
    business_impact TEXT,
    technical_impact TEXT,
    regulatory_impact TEXT,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL REFERENCES users(user_id),
    updated_by INTEGER NOT NULL REFERENCES users(user_id),
    
    -- Constraints
    UNIQUE(test_execution_id), -- One observation per test execution
    UNIQUE(test_case_id, sample_id, attribute_id) -- One observation per test case failure
);

-- Create indexes for performance
CREATE INDEX idx_observation_groups_phase_id ON cycle_report_observation_groups(phase_id);
CREATE INDEX idx_observation_groups_cycle_id ON cycle_report_observation_groups(cycle_id);
CREATE INDEX idx_observation_groups_report_id ON cycle_report_observation_groups(report_id);
CREATE INDEX idx_observation_groups_attribute_lob ON cycle_report_observation_groups(attribute_id, lob_id);
CREATE INDEX idx_observation_groups_status ON cycle_report_observation_groups(status);
CREATE INDEX idx_observation_groups_detected_by ON cycle_report_observation_groups(detected_by);

CREATE INDEX idx_observations_unified_group_id ON cycle_report_observations_unified(group_id);
CREATE INDEX idx_observations_unified_test_execution_id ON cycle_report_observations_unified(test_execution_id);
CREATE INDEX idx_observations_unified_test_case_id ON cycle_report_observations_unified(test_case_id);
CREATE INDEX idx_observations_unified_attribute_id ON cycle_report_observations_unified(attribute_id);
CREATE INDEX idx_observations_unified_lob_id ON cycle_report_observations_unified(lob_id);
CREATE INDEX idx_observations_unified_sample_id ON cycle_report_observations_unified(sample_id);

-- Create function to update observation counts
CREATE OR REPLACE FUNCTION update_observation_group_count_unified()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE cycle_report_observation_groups 
        SET observation_count = observation_count + 1
        WHERE id = NEW.group_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE cycle_report_observation_groups 
        SET observation_count = observation_count - 1
        WHERE id = OLD.group_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update observation counts
CREATE TRIGGER trg_update_observation_count_unified
    AFTER INSERT OR DELETE ON cycle_report_observations_unified
    FOR EACH ROW EXECUTE FUNCTION update_observation_group_count_unified();

-- Create function to update updated_at timestamps (if it doesn't exist)
CREATE OR REPLACE FUNCTION update_updated_at_column_unified()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updated_at columns
CREATE TRIGGER trg_observation_groups_updated_at_unified
    BEFORE UPDATE ON cycle_report_observation_groups
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column_unified();

CREATE TRIGGER trg_observations_unified_updated_at
    BEFORE UPDATE ON cycle_report_observations_unified
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column_unified();

-- Add comments for documentation
COMMENT ON TABLE cycle_report_observation_groups IS 'Observation groups with built-in approval workflow, grouped by attribute and LOB';
COMMENT ON TABLE cycle_report_observations_unified IS 'Individual observations, one per test case failure, linked to test execution results';

COMMENT ON COLUMN cycle_report_observation_groups.observation_count IS 'Automatically maintained count of observations in this group';
COMMENT ON COLUMN cycle_report_observation_groups.status IS 'Main workflow status for the group';
COMMENT ON COLUMN cycle_report_observation_groups.tester_review_status IS 'Tester review decision (built-in approval)';
COMMENT ON COLUMN cycle_report_observation_groups.report_owner_approval_status IS 'Report owner approval decision (built-in approval)';
COMMENT ON COLUMN cycle_report_observation_groups.clarification_requested IS 'Whether clarification has been requested';
COMMENT ON COLUMN cycle_report_observation_groups.resolution_status IS 'Resolution tracking status';

COMMENT ON COLUMN cycle_report_observations_unified.test_execution_id IS 'Links to the test execution that generated this observation';
COMMENT ON COLUMN cycle_report_observations_unified.confidence_level IS 'Confidence level (0.0-1.0) that this is a real issue';
COMMENT ON COLUMN cycle_report_observations_unified.evidence_files IS 'JSON array of evidence file paths and metadata';
COMMENT ON COLUMN cycle_report_observations_unified.variance_details IS 'JSON object with detailed variance information';