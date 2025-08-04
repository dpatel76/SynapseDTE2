-- Create universal_assignment_history table for tracking assignment changes
-- This is important for metrics on how many revisions before report owner approves rules

CREATE TABLE IF NOT EXISTS universal_assignment_history (
    history_id SERIAL PRIMARY KEY,
    assignment_id VARCHAR(36) NOT NULL,
    changed_by_user_id INTEGER NOT NULL,
    changed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    action VARCHAR(50) NOT NULL,
    field_changed VARCHAR(100),
    old_value TEXT,
    new_value TEXT,
    change_reason TEXT,
    change_metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by_id INTEGER,
    updated_by_id INTEGER,
    
    -- Foreign keys
    CONSTRAINT fk_history_assignment FOREIGN KEY (assignment_id) 
        REFERENCES universal_assignments(assignment_id) ON DELETE CASCADE,
    CONSTRAINT fk_history_changed_by FOREIGN KEY (changed_by_user_id) 
        REFERENCES users(user_id),
    CONSTRAINT fk_history_created_by FOREIGN KEY (created_by_id) 
        REFERENCES users(user_id),
    CONSTRAINT fk_history_updated_by FOREIGN KEY (updated_by_id) 
        REFERENCES users(user_id)
);

-- Create indexes for better query performance
CREATE INDEX idx_assignment_history_assignment_id ON universal_assignment_history(assignment_id);
CREATE INDEX idx_assignment_history_changed_by ON universal_assignment_history(changed_by_user_id);
CREATE INDEX idx_assignment_history_changed_at ON universal_assignment_history(changed_at);
CREATE INDEX idx_assignment_history_action ON universal_assignment_history(action);

-- Create a view to easily track revision iterations for rule approvals
CREATE OR REPLACE VIEW v_rule_approval_iterations AS
SELECT 
    ua.assignment_id,
    ua.context_data->>'cycle_id' as cycle_id,
    ua.context_data->>'report_id' as report_id,
    ua.context_data->>'report_name' as report_name,
    COUNT(DISTINCT uah.history_id) FILTER (WHERE uah.action = 'completed' AND uah.new_value LIKE '%rejected%') as rejection_count,
    COUNT(DISTINCT uah.history_id) FILTER (WHERE uah.action = 'completed' AND uah.new_value LIKE '%approved%') as approval_count,
    COUNT(DISTINCT uah.history_id) FILTER (WHERE uah.action IN ('created', 'assigned', 'started', 'completed')) as total_state_changes,
    MIN(uah.changed_at) FILTER (WHERE uah.action = 'created') as first_created_at,
    MAX(uah.changed_at) FILTER (WHERE uah.action = 'completed') as final_completed_at,
    ua.status as current_status
FROM universal_assignments ua
LEFT JOIN universal_assignment_history uah ON ua.assignment_id = uah.assignment_id
WHERE ua.assignment_type = 'Rule Approval'
GROUP BY ua.assignment_id, ua.context_data, ua.status;

-- Add comment explaining the table's purpose
COMMENT ON TABLE universal_assignment_history IS 'Tracks all changes to universal assignments for audit trail and metrics. Essential for tracking rule approval iterations between Tester and Report Owner.';
COMMENT ON COLUMN universal_assignment_history.change_metadata IS 'JSONB field containing structured data about the change, including old and new values in their original format';