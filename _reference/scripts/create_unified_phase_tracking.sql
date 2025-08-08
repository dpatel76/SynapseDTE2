-- Create unified workflow_phases table
CREATE TABLE IF NOT EXISTS workflow_phases (
    phase_id SERIAL PRIMARY KEY,
    cycle_id INTEGER NOT NULL,
    report_id INTEGER NOT NULL,
    phase_name VARCHAR(100) NOT NULL,
    phase_order INTEGER NOT NULL,
    
    -- Status tracking
    status VARCHAR(50) NOT NULL DEFAULT 'NOT_STARTED',
    started_at TIMESTAMP WITH TIME ZONE,
    started_by INTEGER REFERENCES users(user_id),
    completed_at TIMESTAMP WITH TIME ZONE,
    completed_by INTEGER REFERENCES users(user_id),
    
    -- Phase-specific tracking that was in individual phase tables
    data_requested_at TIMESTAMP WITH TIME ZONE,
    data_requested_by INTEGER REFERENCES users(user_id),
    data_received_at TIMESTAMP WITH TIME ZONE,
    rules_generated_at TIMESTAMP WITH TIME ZONE,
    profiling_executed_at TIMESTAMP WITH TIME ZONE,
    
    -- Risk and metadata
    risk_level VARCHAR(20), -- 'low', 'medium', 'high'
    phase_metadata JSON,    -- Phase-specific flexible data
    
    -- Progress tracking
    progress_percentage INTEGER DEFAULT 0,
    estimated_completion_date DATE,
    
    -- SLA tracking
    sla_deadline TIMESTAMP WITH TIME ZONE,
    is_sla_breached BOOLEAN DEFAULT FALSE,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(user_id),
    updated_by INTEGER REFERENCES users(user_id),
    
    -- Constraints
    FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id),
    FOREIGN KEY (report_id) REFERENCES reports(id),
    UNIQUE(cycle_id, report_id, phase_name),
    CHECK (phase_order >= 1 AND phase_order <= 9),
    CHECK (risk_level IN ('low', 'medium', 'high') OR risk_level IS NULL)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_workflow_phases_cycle_report ON workflow_phases(cycle_id, report_id);
CREATE INDEX IF NOT EXISTS idx_workflow_phases_status ON workflow_phases(status);
CREATE INDEX IF NOT EXISTS idx_workflow_phases_phase_name ON workflow_phases(phase_name);

-- Update workflow_activities to reference phase_id
ALTER TABLE workflow_activities DROP CONSTRAINT IF EXISTS workflow_activities_cycle_id_report_id_phase_name_fkey;
ALTER TABLE workflow_activities ADD COLUMN IF NOT EXISTS phase_id INTEGER REFERENCES workflow_phases(phase_id);

-- Create index on workflow_activities.phase_id
CREATE INDEX IF NOT EXISTS idx_workflow_activities_phase_id ON workflow_activities(phase_id);

-- Ensure all cycle_report_* tables have phase_id column
-- Planning phase tables
ALTER TABLE cycle_report_planning_attributes 
    ADD COLUMN IF NOT EXISTS phase_id INTEGER REFERENCES workflow_phases(phase_id);
ALTER TABLE cycle_report_planning_attribute_version_history 
    ADD COLUMN IF NOT EXISTS phase_id INTEGER REFERENCES workflow_phases(phase_id);
ALTER TABLE cycle_report_planning_pde_mapping_approval_rules 
    ADD COLUMN IF NOT EXISTS phase_id INTEGER REFERENCES workflow_phases(phase_id);
ALTER TABLE cycle_report_planning_pde_mapping_reviews 
    ADD COLUMN IF NOT EXISTS phase_id INTEGER REFERENCES workflow_phases(phase_id);
ALTER TABLE cycle_report_planning_pde_mapping_review_history 
    ADD COLUMN IF NOT EXISTS phase_id INTEGER REFERENCES workflow_phases(phase_id);

-- Scoping phase tables  
ALTER TABLE cycle_report_scoping_attribute_recommendations 
    ADD COLUMN IF NOT EXISTS phase_id INTEGER REFERENCES workflow_phases(phase_id);
ALTER TABLE cycle_report_scoping_attribute_recommendation_versions 
    ADD COLUMN IF NOT EXISTS phase_id INTEGER REFERENCES workflow_phases(phase_id);
ALTER TABLE cycle_report_scoping_tester_decisions 
    ADD COLUMN IF NOT EXISTS phase_id INTEGER REFERENCES workflow_phases(phase_id);
ALTER TABLE cycle_report_scoping_submissions 
    ADD COLUMN IF NOT EXISTS phase_id INTEGER REFERENCES workflow_phases(phase_id);
ALTER TABLE cycle_report_scoping_report_owner_reviews 
    ADD COLUMN IF NOT EXISTS phase_id INTEGER REFERENCES workflow_phases(phase_id);
ALTER TABLE cycle_report_scoping_audit_logs 
    ADD COLUMN IF NOT EXISTS phase_id INTEGER REFERENCES workflow_phases(phase_id);
ALTER TABLE cycle_report_scoping_decision_versions 
    ADD COLUMN IF NOT EXISTS phase_id INTEGER REFERENCES workflow_phases(phase_id);

-- Request Info phase tables
ALTER TABLE cycle_report_request_info_audit_logs 
    ADD COLUMN IF NOT EXISTS phase_id INTEGER REFERENCES workflow_phases(phase_id);
ALTER TABLE cycle_report_request_info_document_versions
    ADD COLUMN IF NOT EXISTS phase_id INTEGER REFERENCES workflow_phases(phase_id);

-- Data Profiling phase tables (keeping existing phase_id)
-- Already have phase_id from before

-- Sample Selection phase tables
ALTER TABLE cycle_report_sample_selection_samples 
    ADD COLUMN IF NOT EXISTS phase_id INTEGER REFERENCES workflow_phases(phase_id);
ALTER TABLE cycle_report_sample_selection_audit_logs 
    ADD COLUMN IF NOT EXISTS phase_id INTEGER REFERENCES workflow_phases(phase_id);

-- Test Execution phase tables
ALTER TABLE cycle_report_test_execution_test_executions 
    ADD COLUMN IF NOT EXISTS phase_id INTEGER REFERENCES workflow_phases(phase_id);
ALTER TABLE cycle_report_test_execution_document_analyses 
    ADD COLUMN IF NOT EXISTS phase_id INTEGER REFERENCES workflow_phases(phase_id);
ALTER TABLE cycle_report_test_execution_database_tests 
    ADD COLUMN IF NOT EXISTS phase_id INTEGER REFERENCES workflow_phases(phase_id);
ALTER TABLE cycle_report_test_execution_audit_logs 
    ADD COLUMN IF NOT EXISTS phase_id INTEGER REFERENCES workflow_phases(phase_id);

-- Observation Management phase tables
ALTER TABLE cycle_report_observation_mgmt_observation_records 
    ADD COLUMN IF NOT EXISTS phase_id INTEGER REFERENCES workflow_phases(phase_id);
ALTER TABLE cycle_report_observation_mgmt_impact_assessments 
    ADD COLUMN IF NOT EXISTS phase_id INTEGER REFERENCES workflow_phases(phase_id);
ALTER TABLE cycle_report_observation_mgmt_approvals 
    ADD COLUMN IF NOT EXISTS phase_id INTEGER REFERENCES workflow_phases(phase_id);
ALTER TABLE cycle_report_observation_mgmt_resolutions 
    ADD COLUMN IF NOT EXISTS phase_id INTEGER REFERENCES workflow_phases(phase_id);
ALTER TABLE cycle_report_observation_mgmt_audit_logs 
    ADD COLUMN IF NOT EXISTS phase_id INTEGER REFERENCES workflow_phases(phase_id);
ALTER TABLE cycle_report_observation_mgmt_preliminary_findings
    ADD COLUMN IF NOT EXISTS phase_id INTEGER REFERENCES workflow_phases(phase_id);

-- Test Report phase tables
ALTER TABLE cycle_report_test_report_sections 
    ADD COLUMN IF NOT EXISTS phase_id INTEGER REFERENCES workflow_phases(phase_id);

-- Create indexes on all phase_id columns for performance
CREATE INDEX IF NOT EXISTS idx_planning_attributes_phase ON cycle_report_planning_attributes(phase_id);
CREATE INDEX IF NOT EXISTS idx_scoping_recommendations_phase ON cycle_report_scoping_attribute_recommendations(phase_id);
CREATE INDEX IF NOT EXISTS idx_profiling_files_phase ON cycle_report_data_profiling_files(phase_id);
CREATE INDEX IF NOT EXISTS idx_samples_phase ON cycle_report_sample_selection_samples(phase_id);
CREATE INDEX IF NOT EXISTS idx_test_executions_phase ON cycle_report_test_execution_test_executions(phase_id);
CREATE INDEX IF NOT EXISTS idx_observations_phase ON cycle_report_observation_mgmt_observation_records(phase_id);
CREATE INDEX IF NOT EXISTS idx_test_report_sections_phase ON cycle_report_test_report_sections(phase_id);