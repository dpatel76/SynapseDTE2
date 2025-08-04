-- Unified Test Execution Architecture
-- Direct SQL implementation (bypassing Alembic)
-- Execute this script to create the unified test execution tables

-- =============================================================================
-- 1. CREATE UNIFIED TEST EXECUTION TABLES
-- =============================================================================

-- Create the main test execution results table
CREATE TABLE IF NOT EXISTS cycle_report_test_execution_results (
    id SERIAL PRIMARY KEY,
    
    -- Context and relationships
    phase_id INTEGER NOT NULL REFERENCES workflow_phases(phase_id),
    cycle_id INTEGER NOT NULL REFERENCES test_cycles(cycle_id),
    report_id INTEGER NOT NULL REFERENCES reports(id),
    test_case_id VARCHAR(100) NOT NULL,
    
    -- Evidence integration (from Request for Information phase)
    evidence_id INTEGER NOT NULL REFERENCES cycle_report_request_info_testcase_source_evidence(id),
    
    -- Execution versioning
    execution_number INTEGER NOT NULL,
    is_latest_execution BOOLEAN DEFAULT FALSE,
    execution_reason VARCHAR(100), -- 'initial', 'retry', 'evidence_updated', 'manual_rerun'
    
    -- Test execution configuration
    test_type VARCHAR(50) NOT NULL, -- 'document_analysis', 'database_test', 'manual_test', 'hybrid'
    analysis_method VARCHAR(50) NOT NULL, -- 'llm_analysis', 'database_query', 'manual_review'
    
    -- Core test data
    sample_value TEXT,
    extracted_value TEXT,
    expected_value TEXT,
    
    -- Test results
    test_result VARCHAR(50), -- 'pass', 'fail', 'inconclusive', 'pending_review'
    comparison_result BOOLEAN,
    variance_details JSONB,
    
    -- LLM Analysis Results
    llm_confidence_score FLOAT,
    llm_analysis_rationale TEXT,
    llm_model_used VARCHAR(100),
    llm_tokens_used INTEGER,
    llm_response_raw JSONB,
    llm_processing_time_ms INTEGER,
    
    -- Database Test Results
    database_query_executed TEXT,
    database_result_count INTEGER,
    database_execution_time_ms INTEGER,
    database_result_sample JSONB,
    
    -- Execution status and timing
    execution_status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed', 'cancelled'
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    processing_time_ms INTEGER,
    
    -- Error handling
    error_message TEXT,
    error_details JSONB,
    retry_count INTEGER DEFAULT 0,
    
    -- Comprehensive analysis results
    analysis_results JSONB NOT NULL,
    
    -- Evidence context
    evidence_validation_status VARCHAR(50),
    evidence_version_number INTEGER,
    
    -- Test execution summary
    execution_summary TEXT,
    processing_notes TEXT,
    
    -- Execution metadata
    executed_by INTEGER NOT NULL REFERENCES users(user_id),
    execution_method VARCHAR(50) NOT NULL, -- 'automatic', 'manual', 'scheduled'
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL REFERENCES users(user_id),
    updated_by INTEGER NOT NULL REFERENCES users(user_id)
);

-- Create test execution reviews table
CREATE TABLE IF NOT EXISTS cycle_report_test_execution_reviews (
    id SERIAL PRIMARY KEY,
    execution_id INTEGER NOT NULL REFERENCES cycle_report_test_execution_results(id),
    phase_id INTEGER NOT NULL REFERENCES workflow_phases(phase_id),
    
    -- Review details
    review_status VARCHAR(50) NOT NULL, -- 'approved', 'rejected', 'requires_revision'
    review_notes TEXT,
    reviewer_comments TEXT,
    recommended_action VARCHAR(100), -- 'approve', 'retest', 'escalate', 'manual_review'
    
    -- Quality scoring
    accuracy_score FLOAT,
    completeness_score FLOAT,
    consistency_score FLOAT,
    overall_score FLOAT,
    
    -- Review metadata
    review_criteria_used JSONB,
    supporting_evidence TEXT,
    requires_retest BOOLEAN DEFAULT FALSE,
    
    -- Escalation handling
    escalation_required BOOLEAN DEFAULT FALSE,
    escalation_reason TEXT,
    escalation_level VARCHAR(50), -- 'supervisor', 'manager', 'director'
    
    -- Tester-only workflow
    reviewed_by INTEGER NOT NULL REFERENCES users(user_id),
    reviewed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    review_duration_ms INTEGER,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL REFERENCES users(user_id),
    updated_by INTEGER NOT NULL REFERENCES users(user_id)
);

-- Create test execution audit table
CREATE TABLE IF NOT EXISTS cycle_report_test_execution_audit (
    id SERIAL PRIMARY KEY,
    execution_id INTEGER NOT NULL REFERENCES cycle_report_test_execution_results(id),
    
    -- Audit details
    action VARCHAR(100) NOT NULL, -- 'created', 'updated', 'reviewed', 'approved', 'rejected', 'retested'
    previous_status VARCHAR(50),
    new_status VARCHAR(50),
    change_reason TEXT,
    
    -- Action metadata
    action_details JSONB,
    system_info JSONB,
    
    -- Audit trail
    performed_by INTEGER NOT NULL REFERENCES users(user_id),
    performed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Request context
    ip_address VARCHAR(45),
    user_agent TEXT,
    session_id VARCHAR(100),
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- 2. CREATE CONSTRAINTS AND INDEXES
-- =============================================================================

-- Unique constraints
ALTER TABLE cycle_report_test_execution_results 
ADD CONSTRAINT uq_test_execution_results_test_case_execution 
UNIQUE (test_case_id, execution_number);

-- Create conditional unique constraint for latest execution
CREATE UNIQUE INDEX IF NOT EXISTS uq_test_execution_results_latest_execution
ON cycle_report_test_execution_results(test_case_id, is_latest_execution)
WHERE is_latest_execution = TRUE;

-- Check constraint for evidence validation
ALTER TABLE cycle_report_test_execution_results 
ADD CONSTRAINT ck_test_execution_evidence_approved 
CHECK (evidence_validation_status IN ('valid', 'approved'));

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_test_execution_results_phase_cycle_report 
ON cycle_report_test_execution_results(phase_id, cycle_id, report_id);

CREATE INDEX IF NOT EXISTS idx_test_execution_results_evidence_id 
ON cycle_report_test_execution_results(evidence_id);

CREATE INDEX IF NOT EXISTS idx_test_execution_results_execution_status 
ON cycle_report_test_execution_results(execution_status);

CREATE INDEX IF NOT EXISTS idx_test_execution_results_created_at 
ON cycle_report_test_execution_results(created_at);

CREATE INDEX IF NOT EXISTS idx_test_execution_results_test_case_id 
ON cycle_report_test_execution_results(test_case_id);

-- Review table indexes
CREATE INDEX IF NOT EXISTS idx_test_execution_reviews_execution_id 
ON cycle_report_test_execution_reviews(execution_id);

CREATE INDEX IF NOT EXISTS idx_test_execution_reviews_status 
ON cycle_report_test_execution_reviews(review_status);

CREATE INDEX IF NOT EXISTS idx_test_execution_reviews_reviewed_by 
ON cycle_report_test_execution_reviews(reviewed_by);

-- Audit table indexes
CREATE INDEX IF NOT EXISTS idx_test_execution_audit_execution_id 
ON cycle_report_test_execution_audit(execution_id);

CREATE INDEX IF NOT EXISTS idx_test_execution_audit_performed_at 
ON cycle_report_test_execution_audit(performed_at);

CREATE INDEX IF NOT EXISTS idx_test_execution_audit_action 
ON cycle_report_test_execution_audit(action);

-- =============================================================================
-- 3. CREATE UPDATE TRIGGER FOR TIMESTAMP
-- =============================================================================

-- Create or replace the update trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add update triggers to tables
DROP TRIGGER IF EXISTS update_test_execution_results_updated_at ON cycle_report_test_execution_results;
CREATE TRIGGER update_test_execution_results_updated_at
    BEFORE UPDATE ON cycle_report_test_execution_results
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_test_execution_reviews_updated_at ON cycle_report_test_execution_reviews;
CREATE TRIGGER update_test_execution_reviews_updated_at
    BEFORE UPDATE ON cycle_report_test_execution_reviews
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- 4. CLEANUP LEGACY TABLES (Optional - run after data migration)
-- =============================================================================

-- Uncomment these lines after ensuring data migration is complete
-- DROP TABLE IF EXISTS test_execution_audit_logs;
-- DROP TABLE IF EXISTS test_comparisons;
-- DROP TABLE IF EXISTS bulk_test_executions;
-- DROP TABLE IF EXISTS test_result_reviews;
-- DROP TABLE IF EXISTS cycle_report_test_execution_database_tests;
-- DROP TABLE IF EXISTS cycle_report_test_execution_document_analyses;
-- DROP TABLE IF EXISTS cycle_report_test_executions;

-- Drop legacy ENUMs
-- DROP TYPE IF EXISTS test_type_enum;
-- DROP TYPE IF EXISTS test_status_enum;
-- DROP TYPE IF EXISTS test_result_enum;
-- DROP TYPE IF EXISTS analysis_method_enum;
-- DROP TYPE IF EXISTS review_status_enum;

-- =============================================================================
-- 5. GRANT PERMISSIONS (Adjust based on your security model)
-- =============================================================================

-- Grant permissions to application role (adjust role name as needed)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON cycle_report_test_execution_results TO synapse_app;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON cycle_report_test_execution_reviews TO synapse_app;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON cycle_report_test_execution_audit TO synapse_app;

-- Grant sequence permissions
-- GRANT USAGE, SELECT ON SEQUENCE cycle_report_test_execution_results_id_seq TO synapse_app;
-- GRANT USAGE, SELECT ON SEQUENCE cycle_report_test_execution_reviews_id_seq TO synapse_app;
-- GRANT USAGE, SELECT ON SEQUENCE cycle_report_test_execution_audit_id_seq TO synapse_app;

-- =============================================================================
-- VERIFICATION QUERIES
-- =============================================================================

-- Verify tables were created
SELECT table_name, table_type 
FROM information_schema.tables 
WHERE table_name IN (
    'cycle_report_test_execution_results',
    'cycle_report_test_execution_reviews', 
    'cycle_report_test_execution_audit'
)
ORDER BY table_name;

-- Verify constraints
SELECT conname, contype, conkey 
FROM pg_constraint 
WHERE conrelid IN (
    'cycle_report_test_execution_results'::regclass,
    'cycle_report_test_execution_reviews'::regclass,
    'cycle_report_test_execution_audit'::regclass
);

-- Verify indexes
SELECT indexname, tablename, indexdef 
FROM pg_indexes 
WHERE tablename IN (
    'cycle_report_test_execution_results',
    'cycle_report_test_execution_reviews',
    'cycle_report_test_execution_audit'
)
ORDER BY tablename, indexname;

COMMIT;