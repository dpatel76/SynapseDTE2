-- Insert activity definitions for Test Execution phase
INSERT INTO activity_definitions (
    phase_name, activity_name, activity_code, description, 
    activity_type, requires_backend_action, backend_endpoint,
    sequence_order, depends_on_activity_codes, button_text, success_message, 
    instructions, can_skip, can_reset, is_active
) VALUES
    -- Test Execution Phase
    ('test_execution', 'Start Test Execution Phase', 'start_test_execution', 'Initialize test execution phase', 
     'phase_start', true, '/test-execution/cycles/{cycle_id}/reports/{report_id}/start',
     1, '[]', 'Start Phase', 'Test Execution Phase Started', NULL, false, true, true),
    
    ('test_execution', 'Load Test Cases', 'load_test_cases', 'Load test cases from Request Info phase', 
     'manual', false, NULL,
     2, '["start_test_execution"]', 'Load Test Cases', 'Test cases loaded successfully', 
     'Test cases are automatically loaded from Request Info phase', false, true, true),
    
    ('test_execution', 'Execute Tests', 'execute_tests', 'Execute document and database tests', 
     'manual', false, NULL,
     3, '["load_test_cases"]', 'Execute Tests', 'Tests executed successfully',
     'Use the test execution interface to run tests', false, true, true),
    
    ('test_execution', 'Complete Test Execution', 'complete_test_execution', 'Complete test execution phase', 
     'phase_complete', true, '/test-execution/cycles/{cycle_id}/reports/{report_id}/complete',
     4, '["execute_tests"]', 'Complete Phase', 'Test Execution Phase Completed', NULL, false, false, true),

    -- Observations Phase
    ('observations', 'Start Observations Phase', 'start_observations', 'Initialize observations phase', 
     'phase_start', true, '/observations/cycles/{cycle_id}/reports/{report_id}/start',
     1, '[]', 'Start Phase', 'Observations Phase Started', NULL, false, true, true),
    
    ('observations', 'Review Test Results', 'review_test_results', 'Review failed test cases and create observations', 
     'manual', false, NULL,
     2, '["start_observations"]', 'Review Results', 'Test results reviewed',
     'Review failed test cases and create observations as needed', false, true, true),
    
    ('observations', 'Manage Observations', 'manage_observations', 'Create, update, and approve observations', 
     'manual', false, NULL,
     3, '["review_test_results"]', 'Manage Observations', 'Observations managed successfully',
     'Use the observations interface to manage observations', false, true, true),
    
    ('observations', 'Complete Observations', 'complete_observations', 'Complete observations phase', 
     'phase_complete', true, '/observations/cycles/{cycle_id}/reports/{report_id}/complete',
     4, '["manage_observations"]', 'Complete Phase', 'Observations Phase Completed', NULL, false, false, true),

    -- Finalize Test Report Phase
    ('finalize_test_report', 'Start Finalize Phase', 'start_finalize', 'Initialize report finalization phase', 
     'phase_start', true, '/test-report/cycles/{cycle_id}/reports/{report_id}/start',
     1, '[]', 'Start Phase', 'Finalize Phase Started', NULL, false, true, true),
    
    ('finalize_test_report', 'Generate Report', 'generate_report', 'Generate final test report', 
     'manual', true, '/test-report/cycles/{cycle_id}/reports/{report_id}/generate',
     2, '["start_finalize"]', 'Generate Report', 'Report generated successfully',
     'Click to generate the final test report', false, true, true),
    
    ('finalize_test_report', 'Review Report', 'review_report', 'Review the generated test report', 
     'manual', false, NULL,
     3, '["generate_report"]', 'Review Report', 'Report reviewed',
     'Review the generated report for completeness and accuracy', false, true, true),
    
    ('finalize_test_report', 'Approve Report', 'approve_report', 'Approve the final test report', 
     'manual', true, '/test-report/cycles/{cycle_id}/reports/{report_id}/approve',
     4, '["review_report"]', 'Approve Report', 'Report approved successfully',
     'Approve the final test report', false, false, true),
    
    ('finalize_test_report', 'Complete Report', 'complete_report', 'Complete the test report phase', 
     'phase_complete', true, '/test-report/cycles/{cycle_id}/reports/{report_id}/complete',
     5, '["approve_report"]', 'Complete Phase', 'Test Report Finalized', NULL, false, false, true);