-- Fix button text for optional Planning activities to use standard Start/Complete pattern

-- Update all optional activities to use standard "Start" button text
UPDATE activity_definitions
SET button_text = 'Start',
    updated_at = CURRENT_TIMESTAMP
WHERE phase_name = 'Planning'
AND activity_code IN ('add_data_source', 'map_pdes', 'classify_pdes');

-- Show the updated activities
SELECT 
    activity_code,
    activity_name,
    button_text,
    activity_type,
    can_skip
FROM activity_definitions
WHERE phase_name = 'Planning'
ORDER BY sequence_order;