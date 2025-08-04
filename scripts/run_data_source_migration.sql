-- Create enum type for data source types (skip if exists)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'datasourcetype') THEN
        CREATE TYPE datasourcetype AS ENUM (
            'postgresql', 'mysql', 'oracle', 'sqlserver', 'mongodb',
            'csv', 'excel', 'api', 'sftp', 's3'
        );
    END IF;
END$$;

-- Create cycle_report_data_sources table
CREATE TABLE cycle_report_data_sources (
    id SERIAL PRIMARY KEY,
    cycle_id INTEGER NOT NULL REFERENCES test_cycles(cycle_id),
    report_id INTEGER NOT NULL REFERENCES reports(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    source_type datasourcetype NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    connection_config JSON,
    auth_type VARCHAR(50),
    auth_config JSON,
    refresh_schedule VARCHAR(100),
    last_sync_at TIMESTAMP,
    last_sync_status VARCHAR(50),
    last_sync_message TEXT,
    validation_rules JSON,
    
    -- Audit columns
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by_id INTEGER REFERENCES users(user_id),
    updated_by_id INTEGER REFERENCES users(user_id)
);

-- Create cycle_report_pde_mappings table
CREATE TABLE cycle_report_pde_mappings (
    id SERIAL PRIMARY KEY,
    cycle_id INTEGER NOT NULL REFERENCES test_cycles(cycle_id),
    report_id INTEGER NOT NULL REFERENCES reports(id),
    attribute_id INTEGER NOT NULL REFERENCES cycle_report_planning_attributes(id),
    data_source_id INTEGER REFERENCES cycle_report_data_sources(id),
    
    -- PDE information
    pde_name VARCHAR(255) NOT NULL,
    pde_code VARCHAR(100) UNIQUE NOT NULL,
    pde_description TEXT,
    
    -- Mapping details
    source_field VARCHAR(255),
    transformation_rule JSON,
    mapping_type VARCHAR(50),
    
    -- LLM-assisted mapping
    llm_suggested_mapping JSON,
    llm_confidence_score INTEGER,
    llm_mapping_rationale TEXT,
    llm_alternative_mappings JSON,
    mapping_confirmed_by_user BOOLEAN DEFAULT FALSE,
    
    -- Business metadata
    business_process VARCHAR(255),
    business_owner VARCHAR(255),
    data_steward VARCHAR(255),
    
    -- Classification
    criticality VARCHAR(50),
    risk_level VARCHAR(50),
    regulatory_flag BOOLEAN DEFAULT FALSE,
    pii_flag BOOLEAN DEFAULT FALSE,
    
    -- LLM-assisted classification
    llm_suggested_criticality VARCHAR(50),
    llm_suggested_risk_level VARCHAR(50),
    llm_classification_rationale TEXT,
    llm_regulatory_references JSON,
    
    -- Validation
    is_validated BOOLEAN DEFAULT FALSE,
    validation_message TEXT,
    
    -- Audit columns
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by_id INTEGER REFERENCES users(user_id),
    updated_by_id INTEGER REFERENCES users(user_id)
);

-- Create cycle_report_pde_classifications table
CREATE TABLE cycle_report_pde_classifications (
    id SERIAL PRIMARY KEY,
    pde_mapping_id INTEGER NOT NULL REFERENCES cycle_report_pde_mappings(id),
    
    -- Classification details
    classification_type VARCHAR(100) NOT NULL,
    classification_value VARCHAR(100) NOT NULL,
    classification_reason TEXT,
    
    -- Supporting evidence
    evidence_type VARCHAR(100),
    evidence_reference VARCHAR(500),
    evidence_details JSON,
    
    -- Review and approval
    classified_by INTEGER REFERENCES users(user_id),
    reviewed_by INTEGER REFERENCES users(user_id),
    approved_by INTEGER REFERENCES users(user_id),
    review_status VARCHAR(50),
    review_notes TEXT,
    
    -- Audit columns
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by_id INTEGER REFERENCES users(user_id),
    updated_by_id INTEGER REFERENCES users(user_id)
);

-- Create indexes
CREATE INDEX idx_data_sources_cycle_report ON cycle_report_data_sources(cycle_id, report_id);
CREATE INDEX idx_pde_mappings_cycle_report ON cycle_report_pde_mappings(cycle_id, report_id);
CREATE INDEX idx_pde_mappings_attribute ON cycle_report_pde_mappings(attribute_id);
CREATE INDEX idx_pde_classifications_mapping ON cycle_report_pde_classifications(pde_mapping_id);

-- Update activity definitions to require backend action
UPDATE activity_definitions
SET 
    requires_backend_action = true,
    instructions = CASE 
        WHEN activity_code = 'add_data_source' THEN 
            'Configure the data source connection for this report. You can set up database connections, file locations, or API endpoints that will be used for data validation and testing.'
        WHEN activity_code = 'map_pdes' THEN 
            'Map Process Data Elements (PDEs) to report attributes. The system will use AI to suggest mappings based on attribute names and descriptions.'
        WHEN activity_code = 'classify_pdes' THEN 
            'Classify Process Data Elements by criticality, risk level, and regulatory requirements. AI will assist in identifying high-risk and compliance-critical elements.'
    END,
    updated_at = CURRENT_TIMESTAMP
WHERE activity_code IN ('add_data_source', 'map_pdes', 'classify_pdes');