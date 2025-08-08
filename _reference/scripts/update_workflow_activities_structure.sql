-- Update workflow_activities table structure to properly reference cycle, report, and phase
-- First, let's see the current structure and update it

-- Add cycle_id and report_id if they don't exist (they likely do)
ALTER TABLE workflow_activities 
    ADD COLUMN IF NOT EXISTS cycle_id INTEGER NOT NULL,
    ADD COLUMN IF NOT EXISTS report_id INTEGER NOT NULL;

-- Add phase_id if not exists (we added this earlier)
ALTER TABLE workflow_activities 
    ADD COLUMN IF NOT EXISTS phase_id INTEGER;

-- Drop the old composite foreign key constraint if it exists
ALTER TABLE workflow_activities 
    DROP CONSTRAINT IF EXISTS workflow_activities_cycle_id_report_id_phase_name_fkey;

-- Now add proper foreign key constraints
ALTER TABLE workflow_activities 
    ADD CONSTRAINT fk_workflow_activities_cycle 
        FOREIGN KEY (cycle_id) REFERENCES test_cycles(cycle_id),
    ADD CONSTRAINT fk_workflow_activities_report 
        FOREIGN KEY (report_id) REFERENCES reports(id),
    ADD CONSTRAINT fk_workflow_activities_phase 
        FOREIGN KEY (phase_id) REFERENCES workflow_phases(phase_id);

-- Create a composite foreign key for cycle_id, report_id, phase_id to ensure consistency
ALTER TABLE workflow_activities 
    ADD CONSTRAINT fk_workflow_activities_phase_composite 
        FOREIGN KEY (cycle_id, report_id, phase_id) 
        REFERENCES workflow_phases(cycle_id, report_id, phase_id);

-- But wait, we need to add phase_id to the unique constraint in workflow_phases first
ALTER TABLE workflow_phases 
    DROP CONSTRAINT IF EXISTS workflow_phases_cycle_id_report_id_phase_name_key;

ALTER TABLE workflow_phases 
    ADD CONSTRAINT workflow_phases_unique_phase 
        UNIQUE (cycle_id, report_id, phase_id);

-- Keep the phase_name unique constraint as well
ALTER TABLE workflow_phases 
    ADD CONSTRAINT workflow_phases_unique_phase_name 
        UNIQUE (cycle_id, report_id, phase_name);

-- Update the workflow_activities unique constraint to include phase_id
ALTER TABLE workflow_activities 
    DROP CONSTRAINT IF EXISTS uq_workflow_activities_unique_activity;

ALTER TABLE workflow_activities 
    ADD CONSTRAINT uq_workflow_activities_unique_activity 
        UNIQUE (cycle_id, report_id, phase_id, activity_name);

-- Create comprehensive indexes for performance
CREATE INDEX IF NOT EXISTS idx_workflow_activities_cycle_report_phase 
    ON workflow_activities(cycle_id, report_id, phase_id);

-- This gives us a clean structure where:
-- 1. workflow_phases tracks the 9 phases for each cycle/report
-- 2. workflow_activities tracks granular activities within each phase
-- 3. All cycle_report_* tables reference phase_id to know which phase they belong to
-- 4. Clear referential integrity throughout the system