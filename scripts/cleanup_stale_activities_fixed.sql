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
        MAX(activity_id) as latest_id
    FROM workflow_activities
    WHERE status NOT IN ('COMPLETED', 'SKIPPED')
    GROUP BY cycle_id, report_id, phase_name, activity_name
    HAVING COUNT(*) > 1
)
SELECT * FROM duplicate_activities;

-- 2. Remove duplicate activity states (keep only the latest)
DELETE FROM workflow_activities a
USING workflow_activities b
WHERE a.activity_id < b.activity_id
AND a.cycle_id = b.cycle_id
AND a.report_id = b.report_id
AND a.phase_name = b.phase_name
AND a.activity_name = b.activity_name;

-- 3. Clean up any activities in invalid states
UPDATE workflow_activities
SET status = 'NOT_STARTED'
WHERE status NOT IN ('NOT_STARTED', 'IN_PROGRESS', 'COMPLETED', 'REVISION_REQUESTED', 'BLOCKED', 'SKIPPED');

-- 4. Clean up orphaned activity states (activities for phases that are already completed)
DELETE FROM workflow_activities wa
WHERE EXISTS (
    SELECT 1 
    FROM workflow_phases wp
    WHERE wp.cycle_id = wa.cycle_id
    AND wp.report_id = wa.report_id
    AND wp.phase_name::text = wa.phase_name
    AND wp.status = 'COMPLETED'
    AND wa.status NOT IN ('COMPLETED', 'SKIPPED')
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
        activity_order,
        is_optional,
        is_manual,
        created_at,
        updated_at
    )
    SELECT 
        p_cycle_id,
        p_report_id,
        wat.phase_name,
        wat.activity_name,
        wat.activity_type,
        'NOT_STARTED',
        wat.activity_order,
        wat.is_optional,
        wat.is_manual,
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
        AND activity_id != COALESCE(NEW.activity_id, -1)
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
SET status = 'COMPLETED',
    completed_at = NOW()
WHERE EXISTS (
    SELECT 1 
    FROM workflow_phases wp
    WHERE wp.cycle_id = wa.cycle_id
    AND wp.report_id = wa.report_id
    AND wp.phase_name::text = wa.phase_name
    AND wp.status = 'COMPLETED'
)
AND wa.status = 'NOT_STARTED';

-- 10. Fix any activities that should auto-skip when data source is configured
UPDATE workflow_activities wa
SET status = 'SKIPPED',
    completed_at = NOW(),
    metadata = jsonb_build_object('skip_reason', 'Data source configured')
WHERE wa.activity_name = 'Upload Data Files'
AND wa.phase_name = 'Data Profiling'
AND wa.status = 'NOT_STARTED'
AND EXISTS (
    SELECT 1 FROM data_source_configs dsc
    WHERE dsc.cycle_id = wa.cycle_id
    AND dsc.report_id = wa.report_id
    AND dsc.is_active = true
);

-- Final message
DO $$
BEGIN
    RAISE NOTICE 'Cleanup completed successfully!';
    RAISE NOTICE '1. Removed duplicate activity states';
    RAISE NOTICE '2. Reset invalid activity states';
    RAISE NOTICE '3. Cleaned up orphaned activities';
    RAISE NOTICE '4. Updated activity template names';
    RAISE NOTICE '5. Created reset function for phases';
    RAISE NOTICE '6. Added trigger to prevent duplicates';
    RAISE NOTICE '7. Added performance index';
    RAISE NOTICE '8. Synchronized completed phase activities';
    RAISE NOTICE '9. Auto-skipped upload files when data source exists';
END $$;