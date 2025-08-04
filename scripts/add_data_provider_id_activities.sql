-- Insert Data Provider ID activities with unique activity codes
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
    ('Data Provider ID', 'Start Data Provider ID Phase', 'start_data_provider_id', 'Initiate the data provider identification phase', 'phase_start', true, 1, '[]'::json, 'Start Phase', 'Data Provider ID phase started successfully', 'Click to begin identifying data providers', false, false, true),
    ('Data Provider ID', 'Load Report Attributes', 'load_report_attributes', 'Load attributes from planning phase', 'manual', false, 2, '["start_data_provider_id"]'::json, 'Mark Complete', 'Attributes loaded successfully', 'Load attributes that need data provider assignments', false, true, true),
    ('Data Provider ID', 'Assign Data Providers', 'assign_data_providers', 'Assign data providers to attributes', 'manual', false, 3, '["load_report_attributes"]'::json, 'Mark Complete', 'Data providers assigned successfully', 'Assign a data provider to each attribute', false, true, true),
    ('Data Provider ID', 'Review Provider Assignments', 'review_provider_assignments', 'Review all data provider assignments', 'manual', false, 4, '["assign_data_providers"]'::json, 'Mark Complete', 'Assignments reviewed successfully', 'Review and confirm all data provider assignments', false, true, true),
    ('Data Provider ID', 'Complete Data Provider ID Phase', 'complete_data_provider_id', 'Complete the data provider identification phase', 'phase_complete', true, 5, '["review_provider_assignments"]'::json, 'Complete Phase', 'Data Provider ID phase completed successfully', 'Complete the data provider identification phase', false, false, true);

-- Check result
SELECT phase_name, COUNT(*) as activity_count 
FROM activity_definitions 
WHERE phase_name = 'Data Provider ID'
GROUP BY phase_name;