-- Unblock the first activity of each phase so it can be started
UPDATE activity_states AS as1
SET is_blocked = false,
    blocking_reason = NULL,
    blocked_by_activities = '[]'::json
FROM activity_definitions ad
WHERE as1.activity_definition_id = ad.id
AND as1.cycle_id = 50
AND as1.report_id = 156
AND ad.sequence_order = 1
AND as1.status = 'pending';

-- Check the results
SELECT 
    ad.phase_name,
    ad.activity_name,
    ad.sequence_order,
    as2.status,
    as2.is_blocked,
    as2.blocking_reason
FROM activity_states as2
JOIN activity_definitions ad ON ad.id = as2.activity_definition_id
WHERE as2.cycle_id = 50 
AND as2.report_id = 156
AND ad.sequence_order = 1
ORDER BY ad.phase_name;