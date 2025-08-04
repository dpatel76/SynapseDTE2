#!/bin/bash

echo "=== Full Reset and Test Script ==="
echo

# Reset database
echo "1. Resetting database..."
psql -U synapse_user -d synapse_dt << 'EOF'
-- Full reset of Request Info
UPDATE workflow_phases
SET state = 'Not Started',
    status = 'Not Started',
    actual_start_date = NULL,
    actual_end_date = NULL,
    started_by = NULL,
    completed_by = NULL,
    updated_at = CURRENT_TIMESTAMP
WHERE cycle_id = 58 
  AND report_id = 156 
  AND phase_name = 'Request Info';

UPDATE activity_states
SET status = 'pending',
    started_at = NULL,
    completed_at = NULL,
    completed_by = NULL,
    started_by = NULL,
    completion_percentage = 0,
    completion_notes = NULL,
    completion_data = NULL,
    updated_at = CURRENT_TIMESTAMP
WHERE cycle_id = 58
  AND report_id = 156
  AND phase_name = 'Request Info';

DELETE FROM cycle_report_test_cases 
WHERE phase_id = (
    SELECT phase_id FROM workflow_phases 
    WHERE cycle_id = 58 AND report_id = 156 AND phase_name = 'Request Info'
);

SELECT 'Database reset complete' as status;
EOF

echo
echo "2. Running workflow test..."
python test_rfi_complete_flow.py

echo
echo "3. Checking final database state..."
psql -U synapse_user -d synapse_dt -t -c "
SELECT COUNT(*) || ' test cases created' as result
FROM cycle_report_test_cases 
WHERE phase_id = (
    SELECT phase_id FROM workflow_phases 
    WHERE cycle_id = 58 AND report_id = 156 AND phase_name = 'Request Info'
);"

echo
echo "=== Test Complete ==="