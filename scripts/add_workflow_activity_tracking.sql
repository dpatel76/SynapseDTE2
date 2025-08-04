-- Add workflow_activity_id to data profiling tables
ALTER TABLE cycle_report_data_profiling_files 
ADD COLUMN IF NOT EXISTS workflow_activity_id INTEGER REFERENCES workflow_activities(activity_id);

ALTER TABLE cycle_report_data_profiling_rules 
ADD COLUMN IF NOT EXISTS workflow_activity_id INTEGER REFERENCES workflow_activities(activity_id);

ALTER TABLE cycle_report_data_profiling_results 
ADD COLUMN IF NOT EXISTS workflow_activity_id INTEGER REFERENCES workflow_activities(activity_id);

ALTER TABLE cycle_report_data_profiling_attribute_scores 
ADD COLUMN IF NOT EXISTS workflow_activity_id INTEGER REFERENCES workflow_activities(activity_id);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_profiling_files_workflow ON cycle_report_data_profiling_files(workflow_activity_id);
CREATE INDEX IF NOT EXISTS idx_profiling_rules_workflow ON cycle_report_data_profiling_rules(workflow_activity_id);
CREATE INDEX IF NOT EXISTS idx_profiling_results_workflow ON cycle_report_data_profiling_results(workflow_activity_id);
CREATE INDEX IF NOT EXISTS idx_profiling_scores_workflow ON cycle_report_data_profiling_attribute_scores(workflow_activity_id);

-- Migrate data from phase_id to workflow_activity_id
-- This assumes workflow_activities has been populated with phase data
UPDATE cycle_report_data_profiling_files f
SET workflow_activity_id = (
    SELECT activity_id FROM workflow_activities wa
    WHERE wa.cycle_id = (SELECT cycle_id FROM data_profiling_phases WHERE phase_id = f.phase_id)
    AND wa.report_id = (SELECT report_id FROM data_profiling_phases WHERE phase_id = f.phase_id)
    AND wa.phase_name = 'data_profiling'
    AND wa.activity_name = 'Upload Data Files'
    LIMIT 1
)
WHERE phase_id IS NOT NULL AND workflow_activity_id IS NULL;

UPDATE cycle_report_data_profiling_rules r
SET workflow_activity_id = (
    SELECT activity_id FROM workflow_activities wa
    WHERE wa.cycle_id = (SELECT cycle_id FROM data_profiling_phases WHERE phase_id = r.phase_id)
    AND wa.report_id = (SELECT report_id FROM data_profiling_phases WHERE phase_id = r.phase_id)
    AND wa.phase_name = 'data_profiling'
    AND wa.activity_name = 'Generate Profiling Rules'
    LIMIT 1
)
WHERE phase_id IS NOT NULL AND workflow_activity_id IS NULL;

UPDATE cycle_report_data_profiling_results res
SET workflow_activity_id = (
    SELECT activity_id FROM workflow_activities wa
    WHERE wa.cycle_id = (SELECT cycle_id FROM data_profiling_phases WHERE phase_id = res.phase_id)
    AND wa.report_id = (SELECT report_id FROM data_profiling_phases WHERE phase_id = res.phase_id)
    AND wa.phase_name = 'data_profiling'
    AND wa.activity_name = 'Execute Profiling'
    LIMIT 1
)
WHERE phase_id IS NOT NULL AND workflow_activity_id IS NULL;

UPDATE cycle_report_data_profiling_attribute_scores s
SET workflow_activity_id = (
    SELECT activity_id FROM workflow_activities wa
    WHERE wa.cycle_id = (SELECT cycle_id FROM data_profiling_phases WHERE phase_id = s.phase_id)
    AND wa.report_id = (SELECT report_id FROM data_profiling_phases WHERE phase_id = s.phase_id)
    AND wa.phase_name = 'data_profiling'
    AND wa.activity_name = 'Calculate Attribute Scores'
    LIMIT 1
)
WHERE phase_id IS NOT NULL AND workflow_activity_id IS NULL;

-- Now we can safely drop the phase_id columns
ALTER TABLE cycle_report_data_profiling_files DROP COLUMN IF EXISTS phase_id;
ALTER TABLE cycle_report_data_profiling_rules DROP COLUMN IF EXISTS phase_id;
ALTER TABLE cycle_report_data_profiling_results DROP COLUMN IF EXISTS phase_id;
ALTER TABLE cycle_report_data_profiling_attribute_scores DROP COLUMN IF EXISTS phase_id;