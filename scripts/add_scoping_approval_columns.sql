-- Add approval columns to cycle_report_scoping_tester_decisions table
-- to mirror the data profiling approach

ALTER TABLE cycle_report_scoping_tester_decisions
ADD COLUMN IF NOT EXISTS approval_status VARCHAR(50) DEFAULT 'Pending',
ADD COLUMN IF NOT EXISTS approved_by INTEGER REFERENCES users(user_id),
ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS approval_notes TEXT,
ADD COLUMN IF NOT EXISTS rejected_by INTEGER REFERENCES users(user_id),
ADD COLUMN IF NOT EXISTS rejected_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS rejection_reason TEXT;

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_scoping_decisions_approval_status 
ON cycle_report_scoping_tester_decisions(approval_status);

CREATE INDEX IF NOT EXISTS idx_scoping_decisions_approved_by 
ON cycle_report_scoping_tester_decisions(approved_by);

-- Add similar columns to version history table if they don't exist
ALTER TABLE cycle_report_scoping_decision_versions
ADD COLUMN IF NOT EXISTS approval_status VARCHAR(50),
ADD COLUMN IF NOT EXISTS approved_by INTEGER REFERENCES users(user_id),
ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS approval_notes TEXT,
ADD COLUMN IF NOT EXISTS rejected_by INTEGER REFERENCES users(user_id),
ADD COLUMN IF NOT EXISTS rejected_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS rejection_reason TEXT;

-- Update any existing scoped decisions to have 'Pending' status
UPDATE cycle_report_scoping_tester_decisions 
SET approval_status = 'Pending' 
WHERE approval_status IS NULL AND final_scoping = true;

COMMENT ON COLUMN cycle_report_scoping_tester_decisions.approval_status IS 'Report Owner approval status: Pending, Approved, Rejected';
COMMENT ON COLUMN cycle_report_scoping_tester_decisions.approved_by IS 'User ID of the Report Owner who approved';
COMMENT ON COLUMN cycle_report_scoping_tester_decisions.approved_at IS 'Timestamp when approved';
COMMENT ON COLUMN cycle_report_scoping_tester_decisions.approval_notes IS 'Notes from Report Owner on approval';
COMMENT ON COLUMN cycle_report_scoping_tester_decisions.rejected_by IS 'User ID of the Report Owner who rejected';
COMMENT ON COLUMN cycle_report_scoping_tester_decisions.rejected_at IS 'Timestamp when rejected';
COMMENT ON COLUMN cycle_report_scoping_tester_decisions.rejection_reason IS 'Reason for rejection by Report Owner';