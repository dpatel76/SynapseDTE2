-- Insert Data Profiling phase activities
INSERT INTO activity_definitions (
    phase_name,
    activity_name,
    activity_code,
    description,
    activity_type,
    requires_backend_action,
    sequence_order,
    depends_on_activity_codes,
    button_text,
    success_message,
    instructions,
    can_skip,
    can_reset,
    is_active
) VALUES
-- Phase start activity
(
    'Data Profiling',
    'Start Data Profiling Phase',
    'start_data_profiling',
    'Initiate the data profiling phase',
    'phase_start',
    true,
    1,
    '[]'::json,
    'Start Phase',
    'Data Profiling phase started successfully',
    'Click to begin the data profiling phase',
    false,
    false,
    true
),
-- File upload activity
(
    'Data Profiling',
    'Upload Data Files',
    'upload_data_files',
    'Upload data files for profiling',
    'manual',
    false,
    2,
    '["start_data_profiling"]'::json,
    'Mark Complete',
    'Data files uploaded successfully',
    'Upload the data files that need to be profiled',
    false,
    true,
    true
),
-- Generate profile activity
(
    'Data Profiling',
    'Generate Data Profile',
    'generate_profile',
    'Generate profiling rules from uploaded data',
    'manual',
    true,
    3,
    '["upload_data_files"]'::json,
    'Generate Profile',
    'Data profile generated successfully',
    'Use the Generate Profile button to analyze the uploaded data',
    false,
    true,
    true
),
-- Review rules activity
(
    'Data Profiling',
    'Review Profiling Rules',
    'review_rules',
    'Review and approve generated profiling rules',
    'manual',
    false,
    4,
    '["generate_profile"]'::json,
    'Mark Complete',
    'Profiling rules reviewed',
    'Review the generated profiling rules and approve them',
    false,
    true,
    true
),
-- Execute profiling activity
(
    'Data Profiling',
    'Execute Data Profiling',
    'execute_profiling',
    'Execute the approved profiling rules',
    'manual',
    true,
    5,
    '["review_rules"]'::json,
    'Execute Profiling',
    'Data profiling executed successfully',
    'Run the profiling rules against the data',
    false,
    true,
    true
),
-- Phase complete activity
(
    'Data Profiling',
    'Complete Data Profiling Phase',
    'complete_data_profiling',
    'Complete the data profiling phase',
    'phase_complete',
    true,
    6,
    '["execute_profiling"]'::json,
    'Complete Phase',
    'Data Profiling phase completed successfully',
    'Complete the data profiling phase',
    false,
    false,
    true
);

-- Update any existing activity states for this phase to match new definitions
UPDATE activity_states 
SET status = 'pending' 
WHERE cycle_id IN (
    SELECT DISTINCT cycle_id 
    FROM activity_states 
    WHERE phase_name = 'Data Profiling'
);