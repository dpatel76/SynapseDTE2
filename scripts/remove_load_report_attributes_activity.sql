-- Remove 'Load Report Attributes' activity from Data Provider ID phase
-- This activity is unnecessary as attributes are automatically loaded when the phase starts

-- First, get the ID of the activity we want to remove
DO $$
DECLARE
    load_attr_id INTEGER;
BEGIN
    SELECT id INTO load_attr_id
    FROM activity_definitions 
    WHERE activity_code = 'load_report_attributes' 
    AND phase_name = 'Data Provider ID';
    
    -- Delete any activity states that reference this activity
    DELETE FROM activity_states 
    WHERE activity_definition_id = load_attr_id;
    
    -- Update any dependencies that reference this activity
    UPDATE activity_definitions 
    SET depends_on_activity_codes = '["start_data_provider_id"]'::json
    WHERE activity_code = 'assign_data_providers' 
    AND phase_name = 'Data Provider ID';
    
    -- Update sequence orders to fill the gap
    UPDATE activity_definitions 
    SET sequence_order = sequence_order - 1
    WHERE phase_name = 'Data Provider ID' 
    AND sequence_order > 2;
    
    -- Delete the 'Load Report Attributes' activity
    DELETE FROM activity_definitions 
    WHERE id = load_attr_id;
    
    RAISE NOTICE 'Successfully removed Load Report Attributes activity';
END $$;

-- Verify the changes
SELECT 
    phase_name, 
    activity_name, 
    activity_code, 
    sequence_order, 
    depends_on_activity_codes
FROM activity_definitions 
WHERE phase_name = 'Data Provider ID'
ORDER BY sequence_order;