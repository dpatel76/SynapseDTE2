-- Migration to create new scoping version tables
-- These tables support the version-based scoping workflow

-- Create scoping versions table
CREATE TABLE IF NOT EXISTS cycle_report_scoping_versions (
    version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phase_id INTEGER NOT NULL REFERENCES workflow_phases(phase_id),
    workflow_activity_id INTEGER REFERENCES workflow_activities(activity_id),
    version_number INTEGER NOT NULL DEFAULT 1,
    version_status VARCHAR(50) NOT NULL DEFAULT 'draft',
    parent_version_id UUID REFERENCES cycle_report_scoping_versions(version_id),
    
    -- Workflow tracking
    workflow_execution_id VARCHAR(255),
    workflow_run_id VARCHAR(255),
    activity_name VARCHAR(255),
    
    -- Statistics
    total_attributes INTEGER DEFAULT 0,
    scoped_attributes INTEGER DEFAULT 0,
    declined_attributes INTEGER DEFAULT 0,
    override_count INTEGER DEFAULT 0,
    cde_count INTEGER DEFAULT 0,
    recommendation_accuracy DECIMAL(5,2),
    
    -- Submission tracking
    submission_notes TEXT,
    submitted_by_id INTEGER REFERENCES users(user_id),
    submitted_at TIMESTAMP WITH TIME ZONE,
    
    -- Approval tracking
    approval_notes TEXT,
    approved_by_id INTEGER REFERENCES users(user_id),
    approved_at TIMESTAMP WITH TIME ZONE,
    
    -- Rejection tracking
    rejection_reason TEXT,
    requested_changes TEXT,
    
    -- Assessments
    resource_impact_assessment TEXT,
    risk_coverage_assessment TEXT,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by_id INTEGER REFERENCES users(user_id),
    updated_by_id INTEGER REFERENCES users(user_id),
    
    -- Constraints
    UNIQUE(phase_id, version_number),
    CHECK (version_status IN ('draft', 'pending', 'approved', 'rejected', 'superseded'))
);

-- Create scoping attributes table
CREATE TABLE IF NOT EXISTS cycle_report_scoping_attributes (
    attribute_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version_id UUID NOT NULL REFERENCES cycle_report_scoping_versions(version_id) ON DELETE CASCADE,
    phase_id INTEGER NOT NULL REFERENCES workflow_phases(phase_id),
    planning_attribute_id INTEGER NOT NULL REFERENCES cycle_report_planning_attributes(id),
    
    -- LLM recommendations
    llm_recommendation VARCHAR(50),
    llm_provider VARCHAR(50),
    llm_confidence_score DECIMAL(3,2),
    llm_rationale TEXT,
    llm_processing_time_ms INTEGER,
    
    -- Tester decisions
    tester_decision VARCHAR(50),
    tester_rationale TEXT,
    tester_decided_by_id INTEGER REFERENCES users(user_id),
    tester_decided_at TIMESTAMP WITH TIME ZONE,
    
    -- Report owner decisions
    report_owner_decision VARCHAR(50),
    report_owner_notes TEXT,
    report_owner_decided_by_id INTEGER REFERENCES users(user_id),
    report_owner_decided_at TIMESTAMP WITH TIME ZONE,
    
    -- Final status
    final_status VARCHAR(50) NOT NULL DEFAULT 'pending',
    override_reason TEXT,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by_id INTEGER REFERENCES users(user_id),
    updated_by_id INTEGER REFERENCES users(user_id),
    
    -- Constraints
    UNIQUE(version_id, planning_attribute_id),
    CHECK (llm_recommendation IN ('include', 'exclude', 'review', NULL)),
    CHECK (tester_decision IN ('include', 'exclude', NULL)),
    CHECK (report_owner_decision IN ('approve', 'override', NULL)),
    CHECK (final_status IN ('pending', 'included', 'excluded'))
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_scoping_versions_phase_id ON cycle_report_scoping_versions(phase_id);
CREATE INDEX IF NOT EXISTS idx_scoping_versions_status ON cycle_report_scoping_versions(version_status);
CREATE INDEX IF NOT EXISTS idx_scoping_versions_created_at ON cycle_report_scoping_versions(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_scoping_attributes_version_id ON cycle_report_scoping_attributes(version_id);
CREATE INDEX IF NOT EXISTS idx_scoping_attributes_planning_id ON cycle_report_scoping_attributes(planning_attribute_id);
CREATE INDEX IF NOT EXISTS idx_scoping_attributes_final_status ON cycle_report_scoping_attributes(final_status);

-- Create scoping audit log table if it doesn't exist
CREATE TABLE IF NOT EXISTS scoping_audit_log (
    audit_id SERIAL PRIMARY KEY,
    cycle_id INTEGER NOT NULL REFERENCES test_cycles(cycle_id),
    report_id INTEGER NOT NULL REFERENCES reports(id),
    phase_id INTEGER NOT NULL REFERENCES workflow_phases(phase_id),
    action VARCHAR(100) NOT NULL,
    performed_by INTEGER NOT NULL REFERENCES users(user_id),
    performed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    details JSONB,
    
    -- Index for faster queries
    INDEX idx_scoping_audit_phase_id (phase_id),
    INDEX idx_scoping_audit_performed_at (performed_at DESC)
);

-- Add comments
COMMENT ON TABLE cycle_report_scoping_versions IS 'Version management for scoping decisions';
COMMENT ON TABLE cycle_report_scoping_attributes IS 'Attribute-level scoping decisions within a version';
COMMENT ON TABLE scoping_audit_log IS 'Audit trail for scoping phase activities';