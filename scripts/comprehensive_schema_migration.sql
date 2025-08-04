-- Comprehensive Schema Migration Script
-- This script consolidates all pending database schema updates

-- 1. Ensure all tables have audit columns
-- Check and add missing audit columns to any tables that don't have them
DO $$
DECLARE
    r RECORD;
    column_exists BOOLEAN;
BEGIN
    -- List of tables that should have audit columns
    FOR r IN 
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        AND table_name NOT IN ('alembic_version', 'spatial_ref_sys')
    LOOP
        -- Check and add created_at
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = r.table_name 
            AND column_name = 'created_at'
        ) INTO column_exists;
        
        IF NOT column_exists THEN
            EXECUTE format('ALTER TABLE %I ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP', r.table_name);
            RAISE NOTICE 'Added created_at to %', r.table_name;
        END IF;
        
        -- Check and add updated_at
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = r.table_name 
            AND column_name = 'updated_at'
        ) INTO column_exists;
        
        IF NOT column_exists THEN
            EXECUTE format('ALTER TABLE %I ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP', r.table_name);
            RAISE NOTICE 'Added updated_at to %', r.table_name;
        END IF;
        
        -- Check and add created_by_id
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = r.table_name 
            AND column_name = 'created_by_id'
        ) INTO column_exists;
        
        IF NOT column_exists THEN
            EXECUTE format('ALTER TABLE %I ADD COLUMN created_by_id INTEGER REFERENCES users(user_id)', r.table_name);
            RAISE NOTICE 'Added created_by_id to %', r.table_name;
        END IF;
        
        -- Check and add updated_by_id
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = r.table_name 
            AND column_name = 'updated_by_id'
        ) INTO column_exists;
        
        IF NOT column_exists THEN
            EXECUTE format('ALTER TABLE %I ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id)', r.table_name);
            RAISE NOTICE 'Added updated_by_id to %', r.table_name;
        END IF;
    END LOOP;
END $$;

-- 2. Create update triggers for updated_at columns
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update trigger to all tables with updated_at column
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN 
        SELECT table_name 
        FROM information_schema.columns 
        WHERE column_name = 'updated_at' 
        AND table_schema = 'public'
    LOOP
        EXECUTE format('
            CREATE TRIGGER update_%I_updated_at 
            BEFORE UPDATE ON %I 
            FOR EACH ROW 
            EXECUTE FUNCTION update_updated_at_column()',
            r.table_name, r.table_name
        );
    END LOOP;
EXCEPTION
    WHEN duplicate_object THEN
        -- Trigger already exists, skip
        NULL;
END $$;

-- 3. Add indexes for foreign keys and frequently queried columns
CREATE INDEX IF NOT EXISTS idx_activity_states_cycle_report 
ON activity_states(cycle_id, report_id);

CREATE INDEX IF NOT EXISTS idx_activity_states_definition 
ON activity_states(activity_definition_id);

CREATE INDEX IF NOT EXISTS idx_activity_states_status 
ON activity_states(status);

CREATE INDEX IF NOT EXISTS idx_activity_definitions_phase_active 
ON activity_definitions(phase_name, is_active);

CREATE INDEX IF NOT EXISTS idx_workflow_phases_cycle_report_phase 
ON workflow_phases(cycle_id, report_id, phase_name);

-- 4. Ensure enum types exist
DO $$ BEGIN
    CREATE TYPE activity_status_enum AS ENUM ('pending', 'active', 'completed', 'skipped');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE activity_type_enum AS ENUM ('phase_start', 'phase_complete', 'manual', 'automated');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 5. Add missing columns to activity tables if they don't exist
ALTER TABLE activity_definitions 
ADD COLUMN IF NOT EXISTS auto_complete_on_condition JSONB;

ALTER TABLE activity_states 
ADD COLUMN IF NOT EXISTS completion_percentage INTEGER DEFAULT 0 CHECK (completion_percentage >= 0 AND completion_percentage <= 100);

-- 6. Create versioning support tables if they don't exist
CREATE TABLE IF NOT EXISTS attribute_version_change_logs (
    log_id SERIAL PRIMARY KEY,
    attribute_id INTEGER NOT NULL REFERENCES cycle_report_planning_attributes(id),
    change_type version_change_type_enum NOT NULL,
    version_number INTEGER NOT NULL,
    change_notes TEXT,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    changed_by INTEGER NOT NULL REFERENCES users(user_id),
    field_changes TEXT,
    impact_assessment TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by_id INTEGER REFERENCES users(user_id),
    updated_by_id INTEGER REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS attribute_version_comparisons (
    comparison_id SERIAL PRIMARY KEY,
    version_a_id INTEGER NOT NULL REFERENCES cycle_report_planning_attributes(id),
    version_b_id INTEGER NOT NULL REFERENCES cycle_report_planning_attributes(id),
    differences_found INTEGER NOT NULL DEFAULT 0,
    comparison_summary TEXT,
    impact_score FLOAT,
    compared_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    compared_by INTEGER NOT NULL REFERENCES users(user_id),
    comparison_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by_id INTEGER REFERENCES users(user_id),
    updated_by_id INTEGER REFERENCES users(user_id)
);

-- 7. Add performance indexes
CREATE INDEX IF NOT EXISTS idx_universal_assignments_context 
ON universal_assignments(context_type, status);

CREATE INDEX IF NOT EXISTS idx_universal_assignments_user 
ON universal_assignments(to_user_id, status);

CREATE INDEX IF NOT EXISTS idx_test_executions_cycle_report 
ON cycle_report_test_executions(cycle_id, report_id);

CREATE INDEX IF NOT EXISTS idx_observations_cycle_report 
ON observations(cycle_id, report_id);

-- 8. Clean up any orphaned records
DELETE FROM activity_states 
WHERE activity_definition_id NOT IN (SELECT id FROM activity_definitions);

-- 9. Update statistics for query optimization
ANALYZE activity_definitions;
ANALYZE activity_states;
ANALYZE workflow_phases;
ANALYZE cycle_report_attributes_planning;
ANALYZE universal_assignments;

-- Display summary
DO $$
BEGIN
    RAISE NOTICE 'Schema migration completed successfully';
    RAISE NOTICE 'All tables now have audit columns';
    RAISE NOTICE 'Update triggers have been created';
    RAISE NOTICE 'Performance indexes have been added';
    RAISE NOTICE 'Statistics have been updated';
END $$;