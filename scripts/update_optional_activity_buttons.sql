-- Update button text for optional Planning activities to be consistent

-- Update Add Data Source button
UPDATE activity_definitions
SET button_text = 'Configure Data Source',
    updated_at = CURRENT_TIMESTAMP
WHERE activity_code = 'add_data_source';

-- Update Map PDEs button
UPDATE activity_definitions
SET button_text = 'Map Process Elements',
    updated_at = CURRENT_TIMESTAMP
WHERE activity_code = 'map_pdes';

-- Update Classify PDEs button
UPDATE activity_definitions
SET button_text = 'Classify Elements',
    updated_at = CURRENT_TIMESTAMP
WHERE activity_code = 'classify_pdes';

-- Show the updated activities
SELECT 
    activity_code,
    activity_name,
    button_text,
    can_skip
FROM activity_definitions
WHERE phase_name = 'Planning'
AND activity_code IN ('add_data_source', 'map_pdes', 'classify_pdes')
ORDER BY sequence_order;