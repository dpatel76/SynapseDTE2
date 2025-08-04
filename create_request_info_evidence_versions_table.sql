-- Create Request Info Evidence Versions table
-- This replaces the cycle_report_rfi_versions table with a more descriptive name

-- Create enum types if they don't exist
DO $$ BEGIN
    CREATE TYPE version_status_enum AS ENUM ('draft', 'pending_approval', 'approved', 'rejected', 'superseded');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE evidence_status_enum AS ENUM ('pending', 'approved', 'rejected', 'request_changes');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create the main versions table
CREATE TABLE IF NOT EXISTS cycle_report_request_info_evidence_versions (
    -- Primary key
    version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Phase Integration
    phase_id INTEGER NOT NULL REFERENCES workflow_phases(phase_id),
    
    -- Version Management
    version_number INTEGER NOT NULL,
    version_status version_status_enum NOT NULL DEFAULT 'draft',
    parent_version_id UUID REFERENCES cycle_report_request_info_evidence_versions(version_id),
    
    -- Summary statistics
    total_test_cases INTEGER NOT NULL DEFAULT 0,
    submitted_count INTEGER NOT NULL DEFAULT 0,
    approved_count INTEGER NOT NULL DEFAULT 0,
    rejected_count INTEGER NOT NULL DEFAULT 0,
    pending_count INTEGER NOT NULL DEFAULT 0,
    
    -- Evidence type breakdown
    document_evidence_count INTEGER NOT NULL DEFAULT 0,
    data_source_evidence_count INTEGER NOT NULL DEFAULT 0,
    
    -- Submission tracking
    submission_deadline TIMESTAMP WITH TIME ZONE,
    reminder_schedule JSONB,
    instructions TEXT,
    
    -- Approval workflow
    submitted_by_id INTEGER REFERENCES users(user_id),
    submitted_at TIMESTAMP WITH TIME ZONE,
    approved_by_id INTEGER REFERENCES users(user_id),
    approved_at TIMESTAMP WITH TIME ZONE,
    rejection_reason TEXT,
    
    -- Report owner review metadata
    report_owner_review_requested_at TIMESTAMP WITH TIME ZONE,
    report_owner_review_completed_at TIMESTAMP WITH TIME ZONE,
    report_owner_feedback_summary JSONB,
    
    -- Workflow tracking
    workflow_execution_id VARCHAR(255),
    workflow_run_id VARCHAR(255),
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by_id INTEGER REFERENCES users(user_id),
    updated_by_id INTEGER REFERENCES users(user_id),
    
    -- Constraints
    CONSTRAINT uq_request_info_version_phase_number UNIQUE (phase_id, version_number)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_request_info_versions_phase_id ON cycle_report_request_info_evidence_versions(phase_id);
CREATE INDEX IF NOT EXISTS idx_request_info_versions_status ON cycle_report_request_info_evidence_versions(version_status);
CREATE INDEX IF NOT EXISTS idx_request_info_versions_parent ON cycle_report_request_info_evidence_versions(parent_version_id);

-- Create the evidence table (if it doesn't exist)
CREATE TABLE IF NOT EXISTS cycle_report_request_info_evidence (
    -- Primary key
    evidence_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Version Reference
    version_id UUID NOT NULL REFERENCES cycle_report_request_info_evidence_versions(version_id) ON DELETE CASCADE,
    
    -- Phase Integration
    phase_id INTEGER NOT NULL REFERENCES workflow_phases(phase_id),
    
    -- Test case reference
    test_case_id INTEGER NOT NULL REFERENCES cycle_report_test_cases(id),
    sample_id VARCHAR(255) NOT NULL,
    attribute_id INTEGER NOT NULL REFERENCES cycle_report_planning_attributes(id),
    attribute_name VARCHAR(255) NOT NULL,
    
    -- Evidence type and details
    evidence_type VARCHAR(20) NOT NULL CHECK (evidence_type IN ('document', 'data_source')),
    evidence_status evidence_status_enum NOT NULL DEFAULT 'pending',
    
    -- Document evidence fields
    document_name VARCHAR(255),
    document_path TEXT,
    document_size_bytes BIGINT,
    document_mime_type VARCHAR(100),
    
    -- Data source evidence fields
    data_source_name VARCHAR(255),
    data_source_type VARCHAR(50),
    query_text TEXT,
    query_result JSONB,
    query_row_count INTEGER,
    
    -- Submission details
    submitted_by_id INTEGER REFERENCES users(user_id),
    submitted_at TIMESTAMP WITH TIME ZONE,
    submission_notes TEXT,
    
    -- Tester review
    tester_decision VARCHAR(50),
    tester_notes TEXT,
    tester_decided_by_id INTEGER REFERENCES users(user_id),
    tester_decided_at TIMESTAMP WITH TIME ZONE,
    
    -- Report owner review
    report_owner_decision VARCHAR(50),
    report_owner_notes TEXT,
    report_owner_decided_by_id INTEGER REFERENCES users(user_id),
    report_owner_decided_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    rejection_reason TEXT,
    requires_resubmission BOOLEAN DEFAULT FALSE,
    resubmission_deadline TIMESTAMP WITH TIME ZONE,
    is_resubmission BOOLEAN DEFAULT FALSE,
    parent_evidence_id UUID REFERENCES cycle_report_request_info_evidence(evidence_id),
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by_id INTEGER REFERENCES users(user_id),
    updated_by_id INTEGER REFERENCES users(user_id)
);

-- Create indexes for evidence table
CREATE INDEX IF NOT EXISTS idx_request_info_evidence_version_id ON cycle_report_request_info_evidence(version_id);
CREATE INDEX IF NOT EXISTS idx_request_info_evidence_test_case ON cycle_report_request_info_evidence(test_case_id);
CREATE INDEX IF NOT EXISTS idx_request_info_evidence_sample ON cycle_report_request_info_evidence(sample_id);
CREATE INDEX IF NOT EXISTS idx_request_info_evidence_status ON cycle_report_request_info_evidence(evidence_status);

-- Add comments for documentation
COMMENT ON TABLE cycle_report_request_info_evidence_versions IS 'Version management for Request Info evidence submissions';
COMMENT ON COLUMN cycle_report_request_info_evidence_versions.version_id IS 'Unique identifier for this version';
COMMENT ON COLUMN cycle_report_request_info_evidence_versions.phase_id IS 'Reference to the workflow phase';
COMMENT ON COLUMN cycle_report_request_info_evidence_versions.version_number IS 'Sequential version number within the phase';
COMMENT ON COLUMN cycle_report_request_info_evidence_versions.version_status IS 'Current status of this version';

COMMENT ON TABLE cycle_report_request_info_evidence IS 'Individual evidence submissions for test cases';
COMMENT ON COLUMN cycle_report_request_info_evidence.evidence_id IS 'Unique identifier for this evidence';
COMMENT ON COLUMN cycle_report_request_info_evidence.version_id IS 'Reference to the version this evidence belongs to';
COMMENT ON COLUMN cycle_report_request_info_evidence.test_case_id IS 'Reference to the test case this evidence supports';