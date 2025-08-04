-- Add Test Report tables

-- Test Report Sections table
CREATE TABLE IF NOT EXISTS cycle_report_test_report_sections (
    id SERIAL PRIMARY KEY,
    phase_id INTEGER NOT NULL REFERENCES workflow_phases(phase_id),
    cycle_id INTEGER NOT NULL REFERENCES test_cycles(cycle_id),
    report_id INTEGER NOT NULL REFERENCES reports(id),
    
    -- Section identification
    section_name VARCHAR(100) NOT NULL,
    section_title VARCHAR(255) NOT NULL,
    section_order INTEGER NOT NULL,
    
    -- Section content
    section_content JSONB NOT NULL,
    markdown_content TEXT,
    html_content TEXT,
    
    -- Status tracking
    status VARCHAR(50) DEFAULT 'draft' NOT NULL,
    last_generated_at TIMESTAMP WITH TIME ZONE,
    requires_refresh BOOLEAN DEFAULT FALSE NOT NULL,
    data_sources TEXT[],
    
    -- Approval workflow
    approval_status VARCHAR(50) DEFAULT 'draft' NOT NULL,
    tester_approved BOOLEAN DEFAULT FALSE NOT NULL,
    tester_approved_by INTEGER REFERENCES users(user_id),
    tester_approved_at TIMESTAMP WITH TIME ZONE,
    tester_notes TEXT,
    
    report_owner_approved BOOLEAN DEFAULT FALSE NOT NULL,
    report_owner_approved_by INTEGER REFERENCES users(user_id),
    report_owner_approved_at TIMESTAMP WITH TIME ZONE,
    report_owner_notes TEXT,
    
    executive_approved BOOLEAN DEFAULT FALSE NOT NULL,
    executive_approved_by INTEGER REFERENCES users(user_id),
    executive_approved_at TIMESTAMP WITH TIME ZONE,
    executive_notes TEXT,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by INTEGER REFERENCES users(user_id),
    updated_by INTEGER REFERENCES users(user_id),
    
    -- Constraints
    UNIQUE(phase_id, section_name),
    CHECK (approval_status IN ('draft', 'pending_tester', 'pending_report_owner', 'pending_executive', 'approved', 'rejected', 'revision_requested'))
);

-- Test Report Generation table
CREATE TABLE IF NOT EXISTS cycle_report_test_report_generation (
    id SERIAL PRIMARY KEY,
    phase_id INTEGER NOT NULL REFERENCES workflow_phases(phase_id),
    cycle_id INTEGER NOT NULL REFERENCES test_cycles(cycle_id),
    report_id INTEGER NOT NULL REFERENCES reports(id),
    
    -- Generation metadata
    generation_started_at TIMESTAMP WITH TIME ZONE,
    generation_completed_at TIMESTAMP WITH TIME ZONE,
    generation_duration_ms INTEGER,
    phase_data_collected JSONB,
    
    -- Status tracking
    status VARCHAR(50) DEFAULT 'not_started' NOT NULL,
    error_message TEXT,
    total_sections INTEGER DEFAULT 0 NOT NULL,
    sections_completed INTEGER DEFAULT 0 NOT NULL,
    output_formats_generated TEXT[],
    
    -- Approval tracking
    all_approvals_received BOOLEAN DEFAULT FALSE NOT NULL,
    phase_completion_ready BOOLEAN DEFAULT FALSE NOT NULL,
    phase_completed_at TIMESTAMP WITH TIME ZONE,
    phase_completed_by INTEGER REFERENCES users(user_id),
    
    -- Audit fields
    generated_by INTEGER REFERENCES users(user_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by_id INTEGER REFERENCES users(user_id),
    updated_by_id INTEGER REFERENCES users(user_id),
    
    -- Constraints
    UNIQUE(phase_id),
    CHECK (status IN ('not_started', 'in_progress', 'completed', 'failed'))
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_test_report_sections_phase_id ON cycle_report_test_report_sections(phase_id);
CREATE INDEX IF NOT EXISTS idx_test_report_sections_cycle_report ON cycle_report_test_report_sections(cycle_id, report_id);
CREATE INDEX IF NOT EXISTS idx_test_report_sections_status ON cycle_report_test_report_sections(status);
CREATE INDEX IF NOT EXISTS idx_test_report_sections_approval_status ON cycle_report_test_report_sections(approval_status);

CREATE INDEX IF NOT EXISTS idx_test_report_generation_phase_id ON cycle_report_test_report_generation(phase_id);
CREATE INDEX IF NOT EXISTS idx_test_report_generation_cycle_report ON cycle_report_test_report_generation(cycle_id, report_id);
CREATE INDEX IF NOT EXISTS idx_test_report_generation_status ON cycle_report_test_report_generation(status);