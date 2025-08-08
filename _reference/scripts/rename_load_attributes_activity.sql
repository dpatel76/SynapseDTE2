-- Script to rename "Load Attributes" activity to "Generate LLM Recommendations" in Scoping phase
-- This better reflects what the activity actually does - generating AI recommendations for testing

-- Update the activity definition
UPDATE activity_definitions
SET 
    activity_name = 'Generate LLM Recommendations',
    description = 'AI analyzes attributes and provides testing recommendations',
    button_text = 'Generate Recommendations',
    success_message = 'LLM recommendations generated successfully',
    instructions = 'Click to generate AI-powered testing recommendations for all attributes'
WHERE 
    phase_name = 'Scoping' 
    AND activity_code = 'load_scoping_attributes';

-- Update any existing activity states that reference the old name
UPDATE activity_states
SET activity_metadata = jsonb_set(
    COALESCE(activity_metadata, '{}'::jsonb),
    '{display_name}',
    '"Generate LLM Recommendations"'::jsonb
)
WHERE activity_definition_id IN (
    SELECT id 
    FROM activity_definitions 
    WHERE phase_name = 'Scoping' 
    AND activity_code = 'load_scoping_attributes'
);

-- Log the change
SELECT 
    id,
    phase_name,
    activity_name as new_name,
    activity_code,
    description
FROM activity_definitions
WHERE phase_name = 'Scoping' 
AND activity_code = 'load_scoping_attributes';