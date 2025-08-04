-- Add optional activities for Planning phase that become available after Load Attributes is complete
-- These activities are for data source management and PDE mapping

-- Add Data Source activity
INSERT INTO activity_definitions (
    phase_name,
    activity_name,
    activity_code,
    description,
    activity_type,
    requires_backend_action,
    sequence_order,
    depends_on_activity_codes,
    button_text,
    success_message,
    instructions,
    can_skip,
    can_reset,
    is_active,
    created_at,
    updated_at
) VALUES (
    'Planning',
    'Add Data Source',
    'add_data_source',
    'Configure data source connections for the report',
    'manual',
    true,
    3,  -- After load_attributes which is order 2
    '["load_attributes"]'::json,
    'Add Data Source',
    'Data source configured successfully',
    'Configure the data source connection details including database type, connection string, and authentication. This will be used for automated data profiling and testing.',
    true,  -- Can skip
    true,  -- Can reset
    true,  -- Is active
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- Map PDEs activity
INSERT INTO activity_definitions (
    phase_name,
    activity_name,
    activity_code,
    description,
    activity_type,
    requires_backend_action,
    sequence_order,
    depends_on_activity_codes,
    button_text,
    success_message,
    instructions,
    can_skip,
    can_reset,
    is_active,
    created_at,
    updated_at
) VALUES (
    'Planning',
    'Map PDEs',
    'map_pdes',
    'Map Process Data Elements to report attributes',
    'manual',
    true,
    4,  -- After add_data_source
    '["load_attributes"]'::json,  -- Only depends on load_attributes, not add_data_source
    'Map PDEs',
    'PDEs mapped successfully',
    'Map Process Data Elements (PDEs) to the loaded report attributes. This helps establish the relationship between business processes and data attributes for better testing coverage.',
    true,  -- Can skip
    true,  -- Can reset
    true,  -- Is active
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- Classify PDEs activity
INSERT INTO activity_definitions (
    phase_name,
    activity_name,
    activity_code,
    description,
    activity_type,
    requires_backend_action,
    sequence_order,
    depends_on_activity_codes,
    button_text,
    success_message,
    instructions,
    can_skip,
    can_reset,
    is_active,
    created_at,
    updated_at
) VALUES (
    'Planning',
    'Classify PDEs',
    'classify_pdes',
    'Classify Process Data Elements by criticality and risk',
    'manual',
    true,
    5,  -- After map_pdes
    '["load_attributes", "map_pdes"]'::json,  -- Depends on both load_attributes and map_pdes
    'Classify PDEs',
    'PDEs classified successfully',
    'Classify the mapped Process Data Elements based on criticality, risk level, and regulatory requirements. This classification helps prioritize testing efforts.',
    true,  -- Can skip
    true,  -- Can reset
    true,  -- Is active
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- Update the sequence order of existing activities that come after these new ones
UPDATE activity_definitions 
SET sequence_order = sequence_order + 3
WHERE phase_name = 'Planning' 
AND sequence_order >= 3;

-- Fix the sequence order for our new activities (they got shifted too)
UPDATE activity_definitions 
SET sequence_order = 3
WHERE activity_code = 'add_data_source';

UPDATE activity_definitions 
SET sequence_order = 4
WHERE activity_code = 'map_pdes';

UPDATE activity_definitions 
SET sequence_order = 5
WHERE activity_code = 'classify_pdes';

-- Show the final order
SELECT 
    activity_code,
    activity_name,
    sequence_order,
    depends_on_activity_codes,
    can_skip
FROM activity_definitions
WHERE phase_name = 'Planning'
ORDER BY sequence_order;