-- Update optional activities to not require backend action since they don't have implementations yet
-- This will allow them to be started and completed without errors

UPDATE activity_definitions
SET 
    requires_backend_action = false,
    instructions = CASE 
        WHEN activity_code = 'add_data_source' THEN 
            'This activity is for future implementation. For now, data source configuration can be managed through the admin panel. Click "Start" and then "Mark as Complete" to proceed.'
        WHEN activity_code = 'map_pdes' THEN 
            'This activity is for future implementation. Process Data Element mapping will be available in a future release. Click "Start" and then "Mark as Complete" to proceed.'
        WHEN activity_code = 'classify_pdes' THEN 
            'This activity is for future implementation. PDE classification features will be available in a future release. Click "Start" and then "Mark as Complete" to proceed.'
    END,
    updated_at = CURRENT_TIMESTAMP
WHERE activity_code IN ('add_data_source', 'map_pdes', 'classify_pdes');

-- Show the updated activities
SELECT 
    activity_code,
    activity_name,
    requires_backend_action,
    can_skip,
    instructions
FROM activity_definitions
WHERE activity_code IN ('add_data_source', 'map_pdes', 'classify_pdes');