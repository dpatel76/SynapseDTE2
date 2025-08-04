-- Fix All Issues Script
-- This script addresses all the issues mentioned in the requirements

-- 1. Fix Data Profiling Activities
-- ================================

-- First, update the activity name and code
UPDATE workflow_activity_templates
SET 
    name = 'Generate Data Profiling Rules',
    activity_code = 'generate_profiling_rules',
    description = 'Generate data profiling rules based on uploaded files or configured data sources'
WHERE activity_code = 'generate_profile' AND phase_code = 'data_profiling';

-- Update activity dependencies
UPDATE workflow_activity_dependencies
SET prerequisite_activity_code = 'generate_profiling_rules'
WHERE prerequisite_activity_code = 'generate_profile';

UPDATE workflow_activity_dependencies  
SET dependent_activity_code = 'generate_profiling_rules'
WHERE dependent_activity_code = 'generate_profile';

-- Make Upload Data Files optional with skip conditions
UPDATE workflow_activity_templates
SET 
    can_skip = true,
    skip_conditions = jsonb_build_object(
        'condition_type', 'data_source_configured',
        'description', 'Skip if data source is configured during planning',
        'auto_skip', true
    )
WHERE activity_code = 'upload_data_files' AND phase_code = 'data_profiling';

-- Update existing activity states that might be stuck
UPDATE workflow_activity_states
SET activity_code = 'generate_profiling_rules'
WHERE activity_code = 'generate_profile';

-- Create a helper view to check data source availability
CREATE OR REPLACE VIEW v_cycle_report_data_source_status AS
SELECT DISTINCT
    cr.cycle_id,
    cr.report_id,
    CASE 
        WHEN COUNT(dsc.id) > 0 THEN true
        ELSE false
    END as has_data_source,
    COUNT(dsc.id) as data_source_count,
    array_agg(dsc.name) as data_source_names
FROM cycle_reports cr
LEFT JOIN data_source_configs dsc ON 
    dsc.cycle_id = cr.cycle_id AND 
    dsc.report_id = cr.report_id AND
    dsc.is_active = true
GROUP BY cr.cycle_id, cr.report_id;

-- 2. Add Information Security Classification to PDE Classification
-- ==============================================================

-- Add information_security_classification column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'pde_classifications' 
        AND column_name = 'information_security_classification'
    ) THEN
        ALTER TABLE pde_classifications 
        ADD COLUMN information_security_classification VARCHAR(50);
    END IF;
END $$;

-- Add security_controls column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'pde_classifications' 
        AND column_name = 'security_controls'
    ) THEN
        ALTER TABLE pde_classifications 
        ADD COLUMN security_controls JSONB;
    END IF;
END $$;

-- 3. Update workflow activity templates to ensure proper ordering
-- =============================================================

-- Ensure proper display order for data profiling activities
UPDATE workflow_activity_templates 
SET display_order = CASE activity_code
    WHEN 'data_source_review' THEN 1
    WHEN 'upload_data_files' THEN 2
    WHEN 'generate_profiling_rules' THEN 3
    WHEN 'execute_profiling' THEN 4
    WHEN 'review_profiling_results' THEN 5
    WHEN 'define_dq_thresholds' THEN 6
    WHEN 'validate_dq_rules' THEN 7
    WHEN 'finalize_profiling' THEN 8
END
WHERE phase_code = 'data_profiling';

-- 4. Create indexes for better performance on classification queries
-- ================================================================

CREATE INDEX IF NOT EXISTS idx_pde_classifications_mapping_id 
ON pde_classifications(pde_mapping_id);

CREATE INDEX IF NOT EXISTS idx_pde_classifications_info_sec_class 
ON pde_classifications(information_security_classification);

CREATE INDEX IF NOT EXISTS idx_pde_mappings_cycle_report 
ON pde_mappings(cycle_id, report_id);

-- 5. Add audit trail for classification changes
-- ============================================

CREATE TABLE IF NOT EXISTS pde_classification_audit (
    id SERIAL PRIMARY KEY,
    classification_id INTEGER NOT NULL REFERENCES pde_classifications(id),
    field_name VARCHAR(100) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    changed_by_id INTEGER NOT NULL REFERENCES users(user_id),
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    change_reason TEXT
);

-- 6. Add function to auto-skip upload files activity when data source exists
-- =========================================================================

CREATE OR REPLACE FUNCTION auto_skip_upload_files_activity()
RETURNS TRIGGER AS $$
BEGIN
    -- Check if data source exists for this cycle/report
    IF EXISTS (
        SELECT 1 FROM data_source_configs 
        WHERE cycle_id = NEW.cycle_id 
        AND report_id = NEW.report_id 
        AND is_active = true
    ) AND NEW.activity_code = 'upload_data_files' AND NEW.status = 'pending' THEN
        -- Auto-skip the activity
        NEW.status = 'skipped';
        NEW.completed_at = CURRENT_TIMESTAMP;
        NEW.completed_by_id = NEW.assigned_to_id;
        NEW.notes = 'Auto-skipped: Data source is configured';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for auto-skipping
DROP TRIGGER IF EXISTS trg_auto_skip_upload_files ON workflow_activity_states;
CREATE TRIGGER trg_auto_skip_upload_files
    BEFORE INSERT OR UPDATE ON workflow_activity_states
    FOR EACH ROW
    EXECUTE FUNCTION auto_skip_upload_files_activity();

-- 7. Cleanup any duplicate or stuck activities
-- ===========================================

-- Remove duplicate activity states (keep the latest)
DELETE FROM workflow_activity_states a
USING workflow_activity_states b
WHERE a.id < b.id
AND a.cycle_id = b.cycle_id
AND a.report_id = b.report_id
AND a.phase_code = b.phase_code
AND a.activity_code = b.activity_code;

-- Reset any stuck 'active' states that should be 'in_progress'
UPDATE workflow_activity_states
SET status = 'in_progress'
WHERE status = 'active'
AND phase_code = 'data_profiling';

-- 8. Grant necessary permissions
-- =============================

-- Ensure testers can classify PDEs but not approve mappings
-- (This is already handled in the application logic, but we can add a permission check)

-- Add permission flags if they don't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'roles' 
        AND column_name = 'can_classify_pdes'
    ) THEN
        ALTER TABLE roles 
        ADD COLUMN can_classify_pdes BOOLEAN DEFAULT true;
    END IF;
END $$;

-- Update role permissions
UPDATE roles SET can_classify_pdes = true WHERE role_name IN ('TESTER', 'TEST_EXECUTIVE', 'ADMIN');
UPDATE roles SET can_classify_pdes = false WHERE role_name IN ('DATA_PROVIDER', 'DATA_EXECUTIVE');

-- Final message
DO $$
BEGIN
    RAISE NOTICE 'All fixes applied successfully!';
    RAISE NOTICE '1. Data Profiling activities updated and made conditional';
    RAISE NOTICE '2. Information security classification added to PDE classifications';
    RAISE NOTICE '3. Activity ordering fixed';
    RAISE NOTICE '4. Performance indexes created';
    RAISE NOTICE '5. Audit trail table created';
    RAISE NOTICE '6. Auto-skip functionality added for upload files activity';
    RAISE NOTICE '7. Cleaned up duplicate/stuck activities';
    RAISE NOTICE '8. Role permissions updated';
END $$;