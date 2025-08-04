-- Create workflow activities for cycle 54, report 156 by copying from cycle 21
INSERT INTO workflow_activities (
    cycle_id, 
    report_id, 
    phase_name, 
    activity_name, 
    activity_order, 
    activity_type, 
    status,
    can_start,
    can_complete,
    is_manual,
    is_optional
)
SELECT 
    54 as cycle_id,
    156 as report_id,
    phase_name,
    activity_name,
    activity_order,
    activity_type,
    CASE 
        WHEN phase_name = 'Scoping' AND activity_name IN ('Start Scoping Phase', 'Define Scope', 'Tester Review', 'Report Owner Approval')
        THEN 'COMPLETED'::activity_status_enum
        ELSE 'NOT_STARTED'::activity_status_enum
    END as status,
    can_start,
    can_complete,
    is_manual,
    is_optional
FROM workflow_activities
WHERE cycle_id = 21 
  AND report_id = 156
ON CONFLICT DO NOTHING;