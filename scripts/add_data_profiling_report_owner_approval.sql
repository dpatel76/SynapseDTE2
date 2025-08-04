-- Add Report Owner Review & Approval activity to Data Profiling phase
-- This activity should be triggered after Tester reviews and approves rules

-- First, check current Data Profiling activities
SELECT activity_name, activity_type, activity_order 
FROM workflow_activity_templates 
WHERE phase_name = 'Data Profiling' 
ORDER BY activity_order;

-- Insert the new Report Owner Review & Approval activity
-- It should come after "Review Profiling Results" and before "Complete Data Profiling"
INSERT INTO workflow_activity_templates (
    phase_name,
    activity_name,
    activity_type,
    activity_order,
    description,
    is_manual,
    is_optional,
    required_role,
    auto_complete_on_event,
    is_active,
    handler_name,
    timeout_seconds,
    retry_policy,
    execution_mode
) VALUES (
    'Data Profiling',
    'Report Owner Rule Approval',
    'APPROVAL',
    4, -- After "Review Profiling Results" (order 3)
    'Report Owner reviews and approves/rejects data profiling rules submitted by Tester. Each rule can be individually approved or rejected with feedback.',
    false,
    false,
    'Report Owner',
    NULL,
    true,
    'ReportOwnerRuleApprovalHandler',
    86400, -- 24 hours timeout
    '{"max_retries": 3, "retry_delay": 300}',
    'sequential'
);

-- Update the order of "Complete Data Profiling" to come after Report Owner approval
UPDATE workflow_activity_templates 
SET activity_order = 5 
WHERE phase_name = 'Data Profiling' 
AND activity_name = 'Complete Data Profiling';

-- Add activity dependency configuration
-- This ensures Report Owner approval starts automatically when Tester completes review
UPDATE workflow_activity_templates
SET auto_complete_on_event = 'tester_rules_sent_for_approval'
WHERE phase_name = 'Data Profiling'
AND activity_name = 'Review Profiling Results';

-- Verify the updated activities
SELECT activity_name, activity_type, activity_order, required_role
FROM workflow_activity_templates 
WHERE phase_name = 'Data Profiling' 
ORDER BY activity_order;