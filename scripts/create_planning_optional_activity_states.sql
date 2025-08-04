-- Create activity states for the new optional Planning activities for cycle 50, report 156

-- Get the activity definition IDs for the new activities
WITH new_activities AS (
    SELECT id, activity_code, sequence_order, depends_on_activity_codes
    FROM activity_definitions
    WHERE phase_name = 'Planning'
    AND activity_code IN ('add_data_source', 'map_pdes', 'classify_pdes')
)
-- Insert activity states for these activities
INSERT INTO activity_states (
    activity_definition_id,
    cycle_id,
    report_id,
    phase_name,
    status,
    is_blocked,
    blocking_reason,
    blocked_by_activities,
    created_at,
    updated_at
)
SELECT 
    na.id,
    50 as cycle_id,
    156 as report_id,
    'Planning' as phase_name,
    'pending' as status,
    -- These activities depend on load_attributes being completed
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM activity_states as2
            JOIN activity_definitions ad ON ad.id = as2.activity_definition_id
            WHERE as2.cycle_id = 50 
            AND as2.report_id = 156
            AND ad.activity_code = 'load_attributes'
            AND as2.status = 'completed'
        ) THEN false
        ELSE true
    END as is_blocked,
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM activity_states as2
            JOIN activity_definitions ad ON ad.id = as2.activity_definition_id
            WHERE as2.cycle_id = 50 
            AND as2.report_id = 156
            AND ad.activity_code = 'load_attributes'
            AND as2.status = 'completed'
        ) THEN NULL
        ELSE 'Waiting for Load Attributes to complete'
    END as blocking_reason,
    na.depends_on_activity_codes as blocked_by_activities,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
FROM new_activities na
WHERE NOT EXISTS (
    -- Don't create duplicates
    SELECT 1 FROM activity_states
    WHERE activity_definition_id = na.id
    AND cycle_id = 50
    AND report_id = 156
);

-- Check the results
SELECT 
    ad.activity_code,
    ad.activity_name,
    ad.sequence_order,
    as2.status,
    as2.is_blocked,
    as2.blocking_reason
FROM activity_states as2
JOIN activity_definitions ad ON ad.id = as2.activity_definition_id
WHERE as2.cycle_id = 50 
AND as2.report_id = 156
AND ad.phase_name = 'Planning'
ORDER BY ad.sequence_order;