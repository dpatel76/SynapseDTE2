-- Create entity assignments table with string status

CREATE TABLE IF NOT EXISTS entity_assignments (
    id SERIAL PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL,
    entity_id INTEGER NOT NULL,
    assignee_id INTEGER NOT NULL REFERENCES users(user_id),
    assignment_type VARCHAR(50) NOT NULL, -- report_owner, tester, data_owner, reviewer, approver, observer, data_provider
    cycle_id INTEGER REFERENCES test_cycles(cycle_id),
    phase VARCHAR(50),
    assignment_reason TEXT,
    due_date DATE,
    priority VARCHAR(20) DEFAULT 'normal',
    status VARCHAR(20) DEFAULT 'pending', -- pending, accepted, declined, completed, reassigned, expired
    accepted_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(user_id),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by INTEGER REFERENCES users(user_id),
    CONSTRAINT unique_active_entity_assignment UNIQUE (entity_type, entity_id, assignee_id, assignment_type, status)
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_entity_assignments_entity ON entity_assignments(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_entity_assignments_assignee ON entity_assignments(assignee_id);
CREATE INDEX IF NOT EXISTS idx_entity_assignments_status ON entity_assignments(status);

COMMENT ON TABLE entity_assignments IS 'Flexible assignment system for any entity to any user';

\echo 'Entity assignments table created successfully'