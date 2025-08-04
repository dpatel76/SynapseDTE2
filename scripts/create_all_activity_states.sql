-- Create activity states for all phases for cycle 50, report 156
-- First, delete any existing activity states to avoid duplicates
DELETE FROM activity_states 
WHERE cycle_id = 50 
AND report_id = 156;

-- Insert activity states for each phase
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
    ad.phase_name,
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
            ad.depends_on_activity_codes
        ELSE '[]'::json
    END as blocked_by_activities,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
FROM activity_definitions ad
WHERE ad.is_active = true
ORDER BY ad.phase_name, ad.sequence_order;

-- Update any phases that might already be in progress
-- Mark Planning phase activities as completed if attributes exist
UPDATE activity_states as2
SET status = 'completed',
    completed_at = CURRENT_TIMESTAMP,
    is_blocked = false,
    blocking_reason = NULL
FROM activity_definitions ad
WHERE as2.activity_definition_id = ad.id
AND as2.cycle_id = 50
AND as2.report_id = 156
AND ad.phase_name = 'Planning'
AND ad.activity_code IN ('start_planning', 'load_attributes')
AND EXISTS (
    SELECT 1 FROM cycle_report_planning_attributes 
    WHERE cycle_id = 50 AND report_id = 156
);

-- Show results by phase
SELECT 
    ad.phase_name,
    COUNT(*) as total_activities,
    SUM(CASE WHEN as2.status = 'completed' THEN 1 ELSE 0 END) as completed,
    SUM(CASE WHEN as2.status = 'active' THEN 1 ELSE 0 END) as active,
    SUM(CASE WHEN as2.status = 'pending' THEN 1 ELSE 0 END) as pending
FROM activity_states as2
JOIN activity_definitions ad ON ad.id = as2.activity_definition_id
WHERE as2.cycle_id = 50 
AND as2.report_id = 156
GROUP BY ad.phase_name
ORDER BY ad.phase_name;