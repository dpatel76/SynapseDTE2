-- Fix Data Profiling Activities Configuration
-- 1. Rename "Generate Data Profile" to "Generate Data Profiling Rules"
-- 2. Make "Upload Data Files" optional based on data source presence
-- 3. Update dependencies and configuration

BEGIN;

-- First, update the activity name and code for "Generate Data Profile"
UPDATE activity_definitions
SET 
    activity_name = 'Generate Data Profiling Rules',
    activity_code = 'generate_profiling_rules',
    description = 'Generate profiling rules from uploaded data or configured data source',
    button_text = 'Generate Rules',
    success_message = 'Data profiling rules generated successfully',
    instructions = 'Use the Generate Rules button to analyze the data and create profiling rules'
WHERE 
    activity_code = 'generate_profile'
    AND phase_name = 'Data Profiling';

-- Update dependencies for activities that depended on the old code
UPDATE activity_definitions
SET depends_on_activity_codes = '["upload_data_files", "generate_profiling_rules"]'::json
WHERE 
    activity_code = 'review_rules'
    AND phase_name = 'Data Profiling';

-- Make "Upload Data Files" optional by setting can_skip = true
UPDATE activity_definitions
SET 
    can_skip = true,
    description = 'Upload data files for profiling (optional if data source is configured)',
    instructions = 'Upload the data files that need to be profiled. This step is optional if a data source was configured during planning.'
WHERE 
    activity_code = 'upload_data_files'
    AND phase_name = 'Data Profiling';

-- Update the generate rules activity to not strictly depend on upload_data_files
-- It should depend only on the phase start
UPDATE activity_definitions
SET 
    depends_on_activity_codes = '["start_data_profiling"]'::json,
    instructions = 'Generate profiling rules from uploaded files or configured data source'
WHERE 
    activity_code = 'generate_profiling_rules'
    AND phase_name = 'Data Profiling';

-- Update review rules to depend on generate_profiling_rules (with new code)
UPDATE activity_definitions
SET depends_on_activity_codes = '["generate_profiling_rules"]'::json
WHERE 
    activity_code = 'review_rules'
    AND phase_name = 'Data Profiling';

-- Fix any existing activity states that might have the old activity code
UPDATE activity_states
SET status = 'pending'
WHERE activity_definition_id IN (
    SELECT id FROM activity_definitions 
    WHERE activity_code IN ('generate_profile', 'generate_profiling_rules')
    AND phase_name = 'Data Profiling'
)
AND status = 'active';

-- Add a configuration field to track if data source is available
-- This will be used to determine if Upload Data Files should be auto-skipped
ALTER TABLE activity_definitions 
ADD COLUMN IF NOT EXISTS conditional_skip_rules JSON;

-- Set conditional skip rules for Upload Data Files
UPDATE activity_definitions
SET conditional_skip_rules = '{
    "skip_if_data_source_configured": true,
    "check_planning_attributes": true
}'::json
WHERE 
    activity_code = 'upload_data_files'
    AND phase_name = 'Data Profiling';

-- Create a helper view to check if data source is configured for a cycle/report
CREATE OR REPLACE VIEW v_cycle_report_data_source_status AS
SELECT 
    ra.cycle_id,
    ra.report_id,
    COUNT(DISTINCT ra.attribute_id) as total_attributes,
    COUNT(DISTINCT CASE 
        WHEN ra.data_source_id IS NOT NULL 
        OR ra.source_table IS NOT NULL 
        OR ra.source_column IS NOT NULL 
        THEN ra.attribute_id 
    END) as attributes_with_data_source,
    CASE 
        WHEN COUNT(DISTINCT CASE 
            WHEN ra.data_source_id IS NOT NULL 
            OR ra.source_table IS NOT NULL 
            OR ra.source_column IS NOT NULL 
            THEN ra.attribute_id 
        END) > 0 
        THEN true 
        ELSE false 
    END as has_data_source_configured
FROM cycle_report_planning_attributes ra
WHERE ra.is_active = true
GROUP BY ra.cycle_id, ra.report_id;

-- Add comment to explain the view
COMMENT ON VIEW v_cycle_report_data_source_status IS 
'Helper view to determine if a cycle/report has data sources configured during planning phase';

COMMIT;

-- Query to verify the changes
SELECT 
    activity_code,
    activity_name,
    description,
    can_skip,
    depends_on_activity_codes,
    conditional_skip_rules
FROM activity_definitions
WHERE phase_name = 'Data Profiling'
ORDER BY sequence_order;