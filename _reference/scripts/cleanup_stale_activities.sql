-- Clean up stale activity states and ensure proper state tracking
-- This script removes duplicate activity states and ensures consistency

-- 1. First, let's see what duplicate activity states exist
WITH duplicate_activities AS (
    SELECT 
        cycle_id,
        report_id,
        phase_name,
        activity_name,
        COUNT(*) as count,
        MAX(id) as latest_id
    FROM workflow_activities
    WHERE status NOT IN ('completed', 'skipped')
    GROUP BY cycle_id, report_id, phase_name, activity_name
    HAVING COUNT(*) > 1
)
SELECT * FROM duplicate_activities;

-- 2. Remove duplicate activity states (keep only the latest)
DELETE FROM workflow_activities a
USING workflow_activities b
WHERE a.id < b.id
AND a.cycle_id = b.cycle_id
AND a.report_id = b.report_id
AND a.phase_name = b.phase_name
AND a.activity_name = b.activity_name;

-- 3. Reset any stuck 'active' states
UPDATE workflow_activities
SET status = 'pending'
WHERE status = 'active';

-- 4. Clean up orphaned activity states (activities for phases that are already completed)
DELETE FROM workflow_activities wa
WHERE EXISTS (
    SELECT 1 
    FROM workflow_phases wp
    WHERE wp.cycle_id = wa.cycle_id
    AND wp.report_id = wa.report_id
    AND wp.phase_name = wa.phase_name
    AND wp.status = 'completed'
    AND wa.status NOT IN ('completed', 'skipped')
);

-- 5. Ensure activity templates have correct activity codes
UPDATE workflow_activity_templates
SET activity_name = CASE 
    WHEN activity_name = 'Generate Data Profile' THEN 'Generate Data Profiling Rules'
    ELSE activity_name
END
WHERE phase_name = 'Data Profiling';

-- 6. Create a function to reset activities for a specific phase
CREATE OR REPLACE FUNCTION reset_phase_activities(
    p_cycle_id INTEGER,
    p_report_id INTEGER,
    p_phase_name VARCHAR
) RETURNS void AS $$
BEGIN
    -- Delete existing activities for the phase
    DELETE FROM workflow_activities
    WHERE cycle_id = p_cycle_id
    AND report_id = p_report_id
    AND phase_name = p_phase_name;
    
    -- Re-create activities from templates
    INSERT INTO workflow_activities (
        cycle_id,
        report_id,
        phase_name,
        activity_name,
        activity_type,
        status,
        display_order,
        is_optional,
        created_at,
        updated_at
    )
    SELECT 
        p_cycle_id,
        p_report_id,
        wat.phase_name,
        wat.activity_name,
        wat.activity_type,
        'pending',
        wat.activity_order,
        wat.is_optional,
        NOW(),
        NOW()
    FROM workflow_activity_templates wat
    WHERE wat.phase_name = p_phase_name
    AND wat.is_active = true
    ORDER BY wat.activity_order;
END;
$$ LANGUAGE plpgsql;

-- 7. Add a trigger to prevent duplicate activities
CREATE OR REPLACE FUNCTION prevent_duplicate_activities()
RETURNS TRIGGER AS $$
BEGIN
    -- Check if an activity already exists
    IF EXISTS (
        SELECT 1 FROM workflow_activities
        WHERE cycle_id = NEW.cycle_id
        AND report_id = NEW.report_id
        AND phase_name = NEW.phase_name
        AND activity_name = NEW.activity_name
        AND id != COALESCE(NEW.id, -1)
    ) THEN
        RAISE EXCEPTION 'Duplicate activity state already exists for cycle_id=%, report_id=%, phase=%, activity=%',
            NEW.cycle_id, NEW.report_id, NEW.phase_name, NEW.activity_name;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_prevent_duplicate_activities ON workflow_activities;
CREATE TRIGGER trg_prevent_duplicate_activities
    BEFORE INSERT OR UPDATE ON workflow_activities
    FOR EACH ROW
    EXECUTE FUNCTION prevent_duplicate_activities();

-- 8. Add index for better performance
CREATE INDEX IF NOT EXISTS idx_workflow_activities_lookup 
ON workflow_activities(cycle_id, report_id, phase_name, activity_name);

-- 9. Update any completed phases to ensure their activities are marked correctly
UPDATE workflow_activities wa
SET status = 'completed',
    completed_at = NOW()
WHERE EXISTS (
    SELECT 1 
    FROM workflow_phases wp
    WHERE wp.cycle_id = wa.cycle_id
    AND wp.report_id = wa.report_id
    AND wp.phase_name = wa.phase_name
    AND wp.status = 'completed'
)
AND wa.status = 'pending';

-- Final message
DO $$
BEGIN
    RAISE NOTICE 'Cleanup completed successfully!';
    RAISE NOTICE '1. Removed duplicate activity states';
    RAISE NOTICE '2. Reset stuck active states';
    RAISE NOTICE '3. Cleaned up orphaned activities';
    RAISE NOTICE '4. Updated activity template names';
    RAISE NOTICE '5. Created reset function for phases';
    RAISE NOTICE '6. Added trigger to prevent duplicates';
    RAISE NOTICE '7. Added performance index';
    RAISE NOTICE '8. Synchronized completed phase activities';
END $$;