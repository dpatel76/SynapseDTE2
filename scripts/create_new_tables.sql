-- Create new required tables for refactoring

-- Create document versions table
CREATE TABLE IF NOT EXISTS cycle_report_request_info_document_versions (
    id SERIAL PRIMARY KEY,
    document_submission_id INTEGER NOT NULL,
    version_number INTEGER NOT NULL DEFAULT 1,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500),
    file_size INTEGER,
    mime_type VARCHAR(100),
    checksum VARCHAR(64),
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    uploaded_by_id INTEGER REFERENCES users(user_id),
    change_reason TEXT,
    is_current BOOLEAN DEFAULT true,
    created_by_id INTEGER REFERENCES users(user_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by_id INTEGER REFERENCES users(user_id),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_submission_version UNIQUE (document_submission_id, version_number)
);

CREATE INDEX IF NOT EXISTS idx_doc_versions_is_current 
    ON cycle_report_request_info_document_versions(is_current) 
    WHERE is_current = true;
    
CREATE INDEX IF NOT EXISTS idx_doc_versions_submission_id 
    ON cycle_report_request_info_document_versions(document_submission_id);

-- Create preliminary findings table
CREATE TABLE IF NOT EXISTS cycle_report_observation_mgmt_preliminary_findings (
    id SERIAL PRIMARY KEY,
    cycle_id INTEGER NOT NULL REFERENCES test_cycles(cycle_id),
    report_id INTEGER NOT NULL REFERENCES reports(id),
    finding_title VARCHAR(500) NOT NULL,
    finding_description TEXT NOT NULL,
    finding_type VARCHAR(50) CHECK (finding_type IN ('potential_issue', 'anomaly', 'clarification_needed', 'noteworthy')),
    source_type VARCHAR(50) CHECK (source_type IN ('test_execution', 'data_analysis', 'document_review', 'llm_analysis')),
    source_reference VARCHAR(255),
    category VARCHAR(100),
    severity_estimate VARCHAR(20) CHECK (severity_estimate IN ('low', 'medium', 'high', 'critical', 'unknown')),
    evidence_summary TEXT,
    supporting_data JSONB,
    status VARCHAR(50) DEFAULT 'draft' CHECK (status IN ('draft', 'under_review', 'converted_to_observation', 'dismissed', 'merged')),
    review_notes TEXT,
    conversion_date TIMESTAMP WITH TIME ZONE,
    dismissed_reason TEXT,
    dismissed_date TIMESTAMP WITH TIME ZONE,
    assigned_to_id INTEGER REFERENCES users(user_id),
    tags TEXT[],
    created_by_id INTEGER REFERENCES users(user_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by_id INTEGER REFERENCES users(user_id),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_prelim_findings_cycle_report 
    ON cycle_report_observation_mgmt_preliminary_findings(cycle_id, report_id);
    
CREATE INDEX IF NOT EXISTS idx_prelim_findings_status 
    ON cycle_report_observation_mgmt_preliminary_findings(status);
    
CREATE INDEX IF NOT EXISTS idx_prelim_findings_assigned 
    ON cycle_report_observation_mgmt_preliminary_findings(assigned_to_id);
    
CREATE INDEX IF NOT EXISTS idx_prelim_findings_tags 
    ON cycle_report_observation_mgmt_preliminary_findings USING gin(tags);
EOF < /dev/null