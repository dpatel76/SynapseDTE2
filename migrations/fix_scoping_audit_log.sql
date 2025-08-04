-- Fix scoping audit log table creation
CREATE TABLE IF NOT EXISTS scoping_audit_log (
    audit_id SERIAL PRIMARY KEY,
    cycle_id INTEGER NOT NULL REFERENCES test_cycles(cycle_id),
    report_id INTEGER NOT NULL REFERENCES reports(id),
    phase_id INTEGER NOT NULL REFERENCES workflow_phases(phase_id),
    action VARCHAR(100) NOT NULL,
    performed_by INTEGER NOT NULL REFERENCES users(user_id),
    performed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    details JSONB
);

-- Create indexes separately
CREATE INDEX IF NOT EXISTS idx_scoping_audit_phase_id ON scoping_audit_log(phase_id);
CREATE INDEX IF NOT EXISTS idx_scoping_audit_performed_at ON scoping_audit_log(performed_at DESC);

-- Add comment
COMMENT ON TABLE scoping_audit_log IS 'Audit trail for scoping phase activities';