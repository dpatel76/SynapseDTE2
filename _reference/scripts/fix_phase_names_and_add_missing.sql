-- Fix phase names to match frontend expectations
UPDATE activity_definitions SET phase_name = 'Planning' WHERE phase_name = 'planning';
UPDATE activity_definitions SET phase_name = 'Scoping' WHERE phase_name = 'scoping';
UPDATE activity_definitions SET phase_name = 'Sample Selection' WHERE phase_name = 'sample_selection';
UPDATE activity_definitions SET phase_name = 'Test Execution' WHERE phase_name = 'test_execution';
UPDATE activity_definitions SET phase_name = 'Observations' WHERE phase_name = 'observations';
UPDATE activity_definitions SET phase_name = 'Finalize Test Report' WHERE phase_name = 'finalize_test_report';

-- Check which phases are still missing
SELECT 'Missing: Data Provider ID' WHERE NOT EXISTS (SELECT 1 FROM activity_definitions WHERE phase_name = 'Data Provider ID');
SELECT 'Missing: Request Info' WHERE NOT EXISTS (SELECT 1 FROM activity_definitions WHERE phase_name = 'Request Info');

-- Insert Data Provider ID activities
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
) 
SELECT * FROM (VALUES
    ('Data Provider ID', 'Start Data Provider ID Phase', 'start_data_provider_id', 'Initiate the data provider identification phase', 'phase_start', true, 1, '[]'::json, 'Start Phase', 'Data Provider ID phase started successfully', 'Click to begin identifying data providers', false, false, true),
    ('Data Provider ID', 'Load Attributes', 'load_attributes', 'Load attributes from planning phase', 'manual', false, 2, '["start_data_provider_id"]'::json, 'Mark Complete', 'Attributes loaded successfully', 'Load attributes that need data provider assignments', false, true, true),
    ('Data Provider ID', 'Assign Data Providers', 'assign_data_providers', 'Assign data providers to attributes', 'manual', false, 3, '["load_attributes"]'::json, 'Mark Complete', 'Data providers assigned successfully', 'Assign a data provider to each attribute', false, true, true),
    ('Data Provider ID', 'Review Assignments', 'review_assignments', 'Review all data provider assignments', 'manual', false, 4, '["assign_data_providers"]'::json, 'Mark Complete', 'Assignments reviewed successfully', 'Review and confirm all data provider assignments', false, true, true),
    ('Data Provider ID', 'Complete Data Provider ID Phase', 'complete_data_provider_id', 'Complete the data provider identification phase', 'phase_complete', true, 5, '["review_assignments"]'::json, 'Complete Phase', 'Data Provider ID phase completed successfully', 'Complete the data provider identification phase', false, false, true)
) AS t(phase_name, activity_name, activity_code, description, activity_type, requires_backend_action, sequence_order, depends_on_activity_codes, button_text, success_message, instructions, can_skip, can_reset, is_active)
WHERE NOT EXISTS (SELECT 1 FROM activity_definitions WHERE phase_name = 'Data Provider ID');

-- Insert Request Info activities
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
) 
SELECT * FROM (VALUES
    ('Request Info', 'Start Request Info Phase', 'start_request_info', 'Initiate the request for information phase', 'phase_start', true, 1, '[]'::json, 'Start Phase', 'Request Info phase started successfully', 'Click to begin the request for information phase', false, false, true),
    ('Request Info', 'Create Test Cases', 'create_test_cases', 'Create test cases for data collection', 'manual', false, 2, '["start_request_info"]'::json, 'Mark Complete', 'Test cases created successfully', 'Create test cases for data providers to submit evidence', false, true, true),
    ('Request Info', 'Notify Data Providers', 'notify_data_providers', 'Send notifications to data providers', 'manual', true, 3, '["create_test_cases"]'::json, 'Send Notifications', 'Notifications sent successfully', 'Send email notifications to data providers', false, true, true),
    ('Request Info', 'Collect Documents', 'collect_documents', 'Collect supporting documents from data providers', 'manual', false, 4, '["notify_data_providers"]'::json, 'Mark Complete', 'Documents collected successfully', 'Monitor and collect documents submitted by data providers', false, true, true),
    ('Request Info', 'Review Submissions', 'review_submissions', 'Review all submitted documents', 'manual', false, 5, '["collect_documents"]'::json, 'Mark Complete', 'Submissions reviewed successfully', 'Review completeness of submitted documents', false, true, true),
    ('Request Info', 'Complete Request Info Phase', 'complete_request_info', 'Complete the request for information phase', 'phase_complete', true, 6, '["review_submissions"]'::json, 'Complete Phase', 'Request Info phase completed successfully', 'Complete the request for information phase', false, false, true)
) AS t(phase_name, activity_name, activity_code, description, activity_type, requires_backend_action, sequence_order, depends_on_activity_codes, button_text, success_message, instructions, can_skip, can_reset, is_active)
WHERE NOT EXISTS (SELECT 1 FROM activity_definitions WHERE phase_name = 'Request Info');

-- Show final count
SELECT phase_name, COUNT(*) as activity_count 
FROM activity_definitions 
WHERE is_active = true
GROUP BY phase_name 
ORDER BY phase_name;