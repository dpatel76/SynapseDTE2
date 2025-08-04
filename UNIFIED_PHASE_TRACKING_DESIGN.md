# Unified Phase Tracking Design

## Overview
Instead of having separate phase tables for each workflow phase (data_profiling_phases, sample_selection_phases, etc.), we'll have a single unified phase tracking table that tracks all phases for a cycle/report combination.

## Architecture

### 1. Single Phase Tracking Table: `workflow_phases`
```sql
CREATE TABLE workflow_phases (
    phase_id SERIAL PRIMARY KEY,
    cycle_id INTEGER NOT NULL REFERENCES test_cycles(cycle_id),
    report_id INTEGER NOT NULL REFERENCES reports(id),
    phase_name VARCHAR(100) NOT NULL,  -- 'planning', 'scoping', 'data_profiling', etc.
    phase_order INTEGER NOT NULL,       -- 1-9 for the 9 phases
    
    -- Status tracking
    status VARCHAR(50) NOT NULL DEFAULT 'NOT_STARTED',
    started_at TIMESTAMP,
    started_by INTEGER REFERENCES users(user_id),
    completed_at TIMESTAMP,
    completed_by INTEGER REFERENCES users(user_id),
    
    -- Risk and metadata
    risk_level VARCHAR(20),  -- 'low', 'medium', 'high'
    phase_metadata JSON,     -- Phase-specific data
    
    -- Audit fields
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(user_id),
    updated_by INTEGER REFERENCES users(user_id),
    
    -- Unique constraint
    UNIQUE(cycle_id, report_id, phase_name)
);
```

### 2. Workflow Activities (granular tracking within phases)
```sql
-- Keep existing workflow_activities table
-- Activities belong to phases and provide granular tracking
CREATE TABLE workflow_activities (
    activity_id SERIAL PRIMARY KEY,
    phase_id INTEGER NOT NULL REFERENCES workflow_phases(phase_id),
    activity_name VARCHAR(255) NOT NULL,
    activity_type VARCHAR(50) NOT NULL,
    activity_order INTEGER NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'NOT_STARTED',
    -- ... rest of existing fields
);
```

### 3. All cycle_report_* tables keep phase_id
```sql
-- Example: Data profiling tables
ALTER TABLE cycle_report_data_profiling_files 
    ADD COLUMN phase_id INTEGER REFERENCES workflow_phases(phase_id);
    
ALTER TABLE cycle_report_data_profiling_rules 
    ADD COLUMN phase_id INTEGER REFERENCES workflow_phases(phase_id);
    
-- Same pattern for all other cycle_report_* tables
```

## Benefits

1. **Single source of truth** for phase status across all workflow phases
2. **Maintains referential integrity** - all data knows which phase it belongs to
3. **Supports both phase-level and activity-level tracking**
4. **Simpler than maintaining 9 separate phase tables**
5. **Easier to query** - can get all phase statuses for a report in one query

## Workflow

1. When a test cycle starts for a report:
   - Create all 9 phase records in `workflow_phases` with status 'NOT_STARTED'
   - Create all activities for each phase in `workflow_activities`

2. As work progresses:
   - Update phase status in `workflow_phases`
   - Update activity status in `workflow_activities`
   - All data created references the appropriate phase_id

3. Phase transitions:
   - When all required activities in a phase are complete, mark phase as complete
   - Next phase can start based on business rules

## Phase Names (Standardized)
1. `planning` - Report Planning & Attribute Definition
2. `scoping` - Scoping & Risk Assessment  
3. `data_request` - Data Request to CDOs
4. `data_profiling` - Data Profiling & Quality Assessment
5. `sample_selection` - Sample Selection
6. `request_info` - Request for Information
7. `test_execution` - Test Execution
8. `observation_mgmt` - Observation Management
9. `test_report` - Test Report Generation

## Migration Strategy

1. Create the unified `workflow_phases` table
2. Migrate data from existing phase tables to the new unified table
3. Add phase_id to cycle_report_* tables that don't have it
4. Update foreign keys to reference the new workflow_phases table
5. Drop the old phase-specific tables

This approach gives us the best of both worlds - unified phase tracking while maintaining the context of which phase each piece of data belongs to.