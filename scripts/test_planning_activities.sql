-- Test that the Planning activities are set up correctly

-- Show all Planning activities with their states for cycle 50, report 156
SELECT 
    ad.sequence_order,
    ad.activity_code,
    ad.activity_name,
    ad.activity_type,
    ad.can_skip as is_optional,
    as2.status,
    as2.is_blocked,
    as2.blocking_reason,
    ad.depends_on_activity_codes
FROM activity_definitions ad
LEFT JOIN activity_states as2 ON as2.activity_definition_id = ad.id 
    AND as2.cycle_id = 50 
    AND as2.report_id = 156
WHERE ad.phase_name = 'Planning'
AND ad.is_active = true
ORDER BY ad.sequence_order;

-- Check which activities are ready to start
SELECT 
    ad.activity_code,
    ad.activity_name,
    'Ready to start' as status
FROM activity_definitions ad
JOIN activity_states as2 ON as2.activity_definition_id = ad.id
WHERE ad.phase_name = 'Planning'
AND as2.cycle_id = 50
AND as2.report_id = 156
AND as2.status = 'pending'
AND as2.is_blocked = false;