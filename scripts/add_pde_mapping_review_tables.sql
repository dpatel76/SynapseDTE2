-- Create enum types for review status and action types
CREATE TYPE review_status_enum AS ENUM ('pending', 'approved', 'rejected', 'needs_revision');
CREATE TYPE review_action_type_enum AS ENUM ('submit_for_review', 'approve', 'reject', 'request_revision', 'revise', 'auto_approve');

-- Create PDE Mapping Reviews table
CREATE TABLE cycle_report_planning_pde_mapping_reviews (
    id SERIAL PRIMARY KEY,
    pde_mapping_id INTEGER NOT NULL REFERENCES cycle_report_pde_mappings(id),
    
    -- Review status
    review_status review_status_enum DEFAULT 'pending' NOT NULL,
    
    -- Reviewer information
    submitted_by_id INTEGER NOT NULL REFERENCES users(user_id),
    submitted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reviewed_by_id INTEGER REFERENCES users(user_id),
    reviewed_at TIMESTAMP,
    
    -- Review details
    review_notes TEXT,
    revision_requested TEXT,
    
    -- Auto-approval settings
    llm_confidence_threshold INTEGER DEFAULT 85,
    auto_approved BOOLEAN DEFAULT FALSE,
    
    -- Version tracking
    version_number INTEGER DEFAULT 1,
    is_latest BOOLEAN DEFAULT TRUE,
    
    -- Audit columns
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by_id INTEGER REFERENCES users(user_id),
    updated_by_id INTEGER REFERENCES users(user_id)
);

-- Create Review History table
CREATE TABLE cycle_report_planning_pde_mapping_review_history (
    id SERIAL PRIMARY KEY,
    pde_mapping_id INTEGER NOT NULL REFERENCES cycle_report_pde_mappings(id),
    review_id INTEGER NOT NULL REFERENCES cycle_report_planning_pde_mapping_reviews(id),
    
    -- Action details
    action_type review_action_type_enum NOT NULL,
    action_by_id INTEGER NOT NULL REFERENCES users(user_id),
    action_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- State tracking
    previous_status review_status_enum,
    new_status review_status_enum,
    
    -- Action metadata
    action_notes TEXT,
    changes_made JSON,
    
    -- Audit columns
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by_id INTEGER REFERENCES users(user_id),
    updated_by_id INTEGER REFERENCES users(user_id)
);

-- Create Approval Rules table
CREATE TABLE cycle_report_planning_pde_mapping_approval_rules (
    id SERIAL PRIMARY KEY,
    cycle_id INTEGER REFERENCES test_cycles(cycle_id),
    report_id INTEGER REFERENCES reports(id),
    
    -- Rule configuration
    rule_name VARCHAR(255) NOT NULL,
    rule_description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Conditions for auto-approval
    min_llm_confidence INTEGER DEFAULT 85,
    require_data_source BOOLEAN DEFAULT FALSE,
    require_business_metadata BOOLEAN DEFAULT FALSE,
    
    -- Attribute-based conditions
    auto_approve_cde BOOLEAN DEFAULT FALSE,
    auto_approve_primary_key BOOLEAN DEFAULT TRUE,
    auto_approve_public_classification BOOLEAN DEFAULT TRUE,
    
    -- Risk-based conditions
    max_risk_score_for_auto_approval INTEGER DEFAULT 5,
    
    -- Priority and ordering
    priority INTEGER DEFAULT 100,
    
    -- Audit columns
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by_id INTEGER REFERENCES users(user_id),
    updated_by_id INTEGER REFERENCES users(user_id)
);

-- Create indexes for performance
CREATE INDEX idx_pde_mapping_reviews_mapping_id ON pde_mapping_reviews(pde_mapping_id);
CREATE INDEX idx_pde_mapping_reviews_status ON pde_mapping_reviews(review_status) WHERE is_latest = TRUE;
CREATE INDEX idx_pde_mapping_reviews_submitted_by ON pde_mapping_reviews(submitted_by_id);
CREATE INDEX idx_pde_mapping_reviews_reviewed_by ON pde_mapping_reviews(reviewed_by_id);

CREATE INDEX idx_pde_mapping_review_history_mapping_id ON pde_mapping_review_history(pde_mapping_id);
CREATE INDEX idx_pde_mapping_review_history_review_id ON pde_mapping_review_history(review_id);
CREATE INDEX idx_pde_mapping_review_history_action_by ON pde_mapping_review_history(action_by_id);

CREATE INDEX idx_pde_mapping_approval_rules_cycle_report ON pde_mapping_approval_rules(cycle_id, report_id) WHERE is_active = TRUE;

-- Add default global approval rule
INSERT INTO cycle_report_planning_pde_mapping_approval_rules (
    rule_name,
    rule_description,
    is_active,
    min_llm_confidence,
    auto_approve_primary_key,
    auto_approve_public_classification,
    priority
) VALUES (
    'Default Auto-Approval Rule',
    'Auto-approve mappings with high LLM confidence for primary keys and public data',
    true,
    85,
    true,
    true,
    1000
);

-- Add review status column to PDEMapping if needed for quick lookup
ALTER TABLE cycle_report_pde_mappings
ADD COLUMN IF NOT EXISTS latest_review_status review_status_enum,
ADD COLUMN IF NOT EXISTS latest_review_id INTEGER REFERENCES cycle_report_planning_pde_mapping_reviews(id);

-- Create trigger to update latest review status on PDEMapping
CREATE OR REPLACE FUNCTION update_pde_mapping_review_status()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_latest = TRUE THEN
        UPDATE cycle_report_pde_mappings
        SET latest_review_status = NEW.review_status,
            latest_review_id = NEW.id
        WHERE id = NEW.pde_mapping_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_pde_mapping_review_status_trigger
AFTER INSERT OR UPDATE ON pde_mapping_reviews
FOR EACH ROW
EXECUTE FUNCTION update_pde_mapping_review_status();