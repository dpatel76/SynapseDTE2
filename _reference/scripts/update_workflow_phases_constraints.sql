-- Add phase_order column if it doesn't exist
ALTER TABLE workflow_phases 
ADD COLUMN IF NOT EXISTS phase_order INTEGER;

-- Update phase_order based on phase_name
UPDATE workflow_phases
SET phase_order = CASE 
    WHEN phase_name = 'Planning' THEN 1
    WHEN phase_name = 'Scoping' THEN 2
    WHEN phase_name = 'Data Provider ID' THEN 3
    WHEN phase_name = 'Data Profiling' THEN 4
    WHEN phase_name = 'Sample Selection' THEN 5
    WHEN phase_name = 'Request Info' THEN 6
    WHEN phase_name = 'Test Execution' THEN 7
    WHEN phase_name = 'Observations' THEN 8
    WHEN phase_name = 'Finalize Test Report' THEN 9
    ELSE 0
END
WHERE phase_order IS NULL;

-- Add new columns for unified phase tracking
ALTER TABLE workflow_phases
ADD COLUMN IF NOT EXISTS data_requested_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS data_requested_by INTEGER REFERENCES users(user_id),
ADD COLUMN IF NOT EXISTS data_received_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS rules_generated_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS profiling_executed_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS risk_level VARCHAR(20),
ADD COLUMN IF NOT EXISTS progress_percentage INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS estimated_completion_date DATE,
ADD COLUMN IF NOT EXISTS sla_deadline TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS is_sla_breached BOOLEAN DEFAULT FALSE;

-- Add constraints
ALTER TABLE workflow_phases
DROP CONSTRAINT IF EXISTS workflow_phases_phase_order_check;

ALTER TABLE workflow_phases
ADD CONSTRAINT workflow_phases_phase_order_check CHECK (phase_order >= 1 AND phase_order <= 9);

ALTER TABLE workflow_phases
DROP CONSTRAINT IF EXISTS workflow_phases_risk_level_check;

ALTER TABLE workflow_phases
ADD CONSTRAINT workflow_phases_risk_level_check CHECK (risk_level IN ('low', 'medium', 'high') OR risk_level IS NULL);

-- Update workflow_activities structure
ALTER TABLE workflow_activities 
DROP CONSTRAINT IF EXISTS workflow_activities_cycle_id_report_id_phase_name_fkey;

-- Ensure workflow_activities has all necessary columns
ALTER TABLE workflow_activities
ALTER COLUMN cycle_id SET NOT NULL,
ALTER COLUMN report_id SET NOT NULL;

-- Add foreign key constraints to workflow_activities
ALTER TABLE workflow_activities
DROP CONSTRAINT IF EXISTS fk_workflow_activities_cycle;
ALTER TABLE workflow_activities
ADD CONSTRAINT fk_workflow_activities_cycle FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id);

ALTER TABLE workflow_activities
DROP CONSTRAINT IF EXISTS fk_workflow_activities_report;
ALTER TABLE workflow_activities
ADD CONSTRAINT fk_workflow_activities_report FOREIGN KEY (report_id) REFERENCES reports(id);

ALTER TABLE workflow_activities
DROP CONSTRAINT IF EXISTS fk_workflow_activities_phase;
ALTER TABLE workflow_activities
ADD CONSTRAINT fk_workflow_activities_phase FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);

-- Add unique constraint on workflow_activities
ALTER TABLE workflow_activities
DROP CONSTRAINT IF EXISTS uq_workflow_activities_unique_activity;
ALTER TABLE workflow_activities
ADD CONSTRAINT uq_workflow_activities_unique_activity 
    UNIQUE (cycle_id, report_id, phase_id, activity_name);

-- Create comprehensive indexes
CREATE INDEX IF NOT EXISTS idx_workflow_activities_cycle_report_phase 
    ON workflow_activities(cycle_id, report_id, phase_id);

-- Add unique constraints to workflow_phases
ALTER TABLE workflow_phases
DROP CONSTRAINT IF EXISTS workflow_phases_unique_phase_name;
ALTER TABLE workflow_phases
ADD CONSTRAINT workflow_phases_unique_phase_name 
    UNIQUE (cycle_id, report_id, phase_name);

-- Create indexes on all phase_id columns that exist
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN 
        SELECT tablename, 'CREATE INDEX IF NOT EXISTS idx_' || tablename || '_phase_id ON ' || tablename || '(phase_id);' as create_index_sql
        FROM pg_tables t
        WHERE t.schemaname = 'public'
        AND t.tablename LIKE 'cycle_report_%'
        AND EXISTS (
            SELECT 1
            FROM information_schema.columns c
            WHERE c.table_schema = 'public'
            AND c.table_name = t.tablename
            AND c.column_name = 'phase_id'
        )
    LOOP
        EXECUTE r.create_index_sql;
    END LOOP;
END $$;