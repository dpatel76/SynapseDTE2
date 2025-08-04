-- Script to rename "Submit for Approval" activity to "Report Owner Approval"

-- First, let's check what activities contain "Submit" or "Approval"
SELECT 
    activity_name,
    activity_code,
    phase_name,
    description,
    button_text
FROM activity_definitions 
WHERE 
    activity_name ILIKE '%submit%approval%' 
    OR activity_name = 'Submit for Approval'
    OR (activity_name ILIKE '%submit%' AND activity_name ILIKE '%approval%');

-- Update the activity name and related text
UPDATE activity_definitions
SET 
    activity_name = 'Report Owner Approval',
    description = 'Report Owner reviews and approves the scoping decisions',
    button_text = 'Submit to Report Owner',
    success_message = 'Submitted to Report Owner for approval',
    instructions = 'Click to submit the scoping decisions to the Report Owner for review and approval'
WHERE 
    activity_name = 'Submit for Approval' 
    OR (activity_name ILIKE '%submit%' AND activity_name ILIKE '%approval%' AND phase_name = 'Scoping');

-- Verify the update
SELECT 
    activity_name,
    activity_code,
    phase_name,
    description,
    button_text,
    success_message,
    instructions
FROM activity_definitions 
WHERE 
    activity_name = 'Report Owner Approval'
    OR activity_code LIKE '%submit%approval%';