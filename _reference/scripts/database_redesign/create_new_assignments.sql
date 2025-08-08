-- Create our new assignment system with a different name to avoid conflicts

-- Create assignment tables
CREATE TABLE IF NOT EXISTS entity_assignments (
    id SERIAL PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL,
    entity_id INTEGER NOT NULL,
    assignee_id INTEGER NOT NULL REFERENCES users(user_id),
    assignment_type assignment_type_enum NOT NULL,
    cycle_id INTEGER REFERENCES test_cycles(cycle_id),
    phase VARCHAR(50),
    assignment_reason TEXT,
    due_date DATE,
    priority VARCHAR(20) DEFAULT 'normal',
    status assignment_status_enum DEFAULT 'pending',
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