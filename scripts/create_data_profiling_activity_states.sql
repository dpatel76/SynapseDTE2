-- Create activity states for Data Profiling phase for cycle 50, report 156
-- First, delete any existing activity states for this phase to avoid duplicates
DELETE FROM activity_states 
WHERE cycle_id = 50 
AND report_id = 156 
AND activity_definition_id IN (
    SELECT id FROM activity_definitions WHERE phase_name = 'Data Profiling'
);

-- Insert activity states for each activity definition
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
    ad.id,
    50 as cycle_id,
    156 as report_id,
    'Data Profiling' as phase_name,
    'pending' as status,
    CASE 
        WHEN ad.sequence_order > 1 THEN true
        ELSE false
    END as is_blocked,
    CASE 
        WHEN ad.sequence_order > 1 THEN 'Waiting for previous activity to complete'
        ELSE NULL
    END as blocking_reason,
    CASE 
        WHEN ad.sequence_order > 1 THEN 
            (SELECT json_agg(ad2.activity_code) 
             FROM activity_definitions ad2 
             WHERE ad2.phase_name = 'Data Profiling' 
             AND ad2.sequence_order < ad.sequence_order)::json
        ELSE '[]'::json
    END as blocked_by_activities,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
FROM activity_definitions ad
WHERE ad.phase_name = 'Data Profiling'
AND ad.is_active = true
ORDER BY ad.sequence_order;

-- Check the results
SELECT 
    as2.id,
    ad.activity_name,
    ad.activity_code,
    ad.sequence_order,
    as2.status,
    as2.is_blocked,
    as2.blocking_reason
FROM activity_states as2
JOIN activity_definitions ad ON ad.id = as2.activity_definition_id
WHERE as2.cycle_id = 50 
AND as2.report_id = 156
AND ad.phase_name = 'Data Profiling'
ORDER BY ad.sequence_order;