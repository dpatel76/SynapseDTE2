-- Fix Primary Key attribute decisions for cycle 55, report 156
-- This script manually approves all PK attributes that don't have decisions

-- First, check which PK attributes need decisions
SELECT 
    sa.attribute_id,
    pa.attribute_name,
    pa.is_primary_key,
    sa.tester_decision,
    sa.final_scoping
FROM cycle_report_scoping_attributes sa
JOIN cycle_report_planning_attributes pa ON sa.planning_attribute_id = pa.id
JOIN cycle_report_scoping_versions sv ON sa.version_id = sv.version_id
JOIN workflow_phases wp ON sv.phase_id = wp.phase_id
WHERE wp.cycle_id = 55
    AND wp.report_id = 156
    AND pa.is_primary_key = true
    AND sa.tester_decision IS NULL
    AND sv.version_number = (
        SELECT MAX(sv2.version_number)
        FROM cycle_report_scoping_versions sv2
        WHERE sv2.phase_id = sv.phase_id
    );

-- Update PK attributes to have 'accept' decision
UPDATE cycle_report_scoping_attributes sa
SET 
    tester_decision = 'accept',
    final_scoping = true,
    tester_rationale = 'Primary Key attribute - automatically included for testing',
    tester_decided_at = NOW(),
    tester_decided_by_id = 1, -- Replace with actual user ID
    updated_at = NOW(),
    status = 'submitted'
FROM cycle_report_planning_attributes pa,
     cycle_report_scoping_versions sv,
     workflow_phases wp
WHERE sa.planning_attribute_id = pa.id
    AND sa.version_id = sv.version_id
    AND sv.phase_id = wp.phase_id
    AND wp.cycle_id = 55
    AND wp.report_id = 156
    AND pa.is_primary_key = true
    AND sa.tester_decision IS NULL
    AND sv.version_number = (
        SELECT MAX(sv2.version_number)
        FROM cycle_report_scoping_versions sv2
        WHERE sv2.phase_id = sv.phase_id
    );

-- Verify the update
SELECT COUNT(*) as pk_without_decisions
FROM cycle_report_scoping_attributes sa
JOIN cycle_report_planning_attributes pa ON sa.planning_attribute_id = pa.id
JOIN cycle_report_scoping_versions sv ON sa.version_id = sv.version_id
JOIN workflow_phases wp ON sv.phase_id = wp.phase_id
WHERE wp.cycle_id = 55
    AND wp.report_id = 156
    AND pa.is_primary_key = true
    AND sa.tester_decision IS NULL
    AND sv.version_number = (
        SELECT MAX(sv2.version_number)
        FROM cycle_report_scoping_versions sv2
        WHERE sv2.phase_id = sv.phase_id
    );