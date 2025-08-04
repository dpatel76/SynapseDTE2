# Database Redesign Implementation

This directory contains the complete database redesign following business-oriented naming conventions.

## Overview

The redesign implements a cleaner, more intuitive database structure with the following key improvements:

1. **Business-oriented naming**: `report_inventory` instead of `reports`, `cycle_reports` for instances
2. **Consistent phase naming**: All phase tables follow `cycle_report_*` pattern
3. **Separate version history**: Each versioned entity has a `_version_history` table
4. **Universal assignments**: Flexible system for assigning any entity to any user
5. **Comprehensive audit**: Separate audit tables from version history

## Database Structure

### Core Tables
- `users` - System users with roles
- `lobs` - Lines of Business
- `report_inventory` - Master list of all reports
- `test_cycles` - Testing periods
- `cycle_reports` - Report instances for specific test cycles
- `data_sources` - External data source configurations

### Phase Tables (Following `cycle_report_*` pattern)
1. **Planning**: `cycle_report_attributes_planning` (with security classification)
2. **Data Profiling**: `cycle_report_data_profiling`, `cycle_report_profiling_results`
3. **Scoping**: `cycle_report_attributes_scoping`
4. **Sample Selection**: `cycle_report_sample_selection`, `cycle_report_samples`
5. **Data Owners**: `cycle_report_data_owners`
6. **Source Evidence**: `cycle_report_test_cases`, `cycle_report_document_submissions`
7. **Test Execution**: `cycle_report_test_execution`, `cycle_report_test_failures`
8. **Observations**: `cycle_report_observations`, `cycle_report_observation_failures`
9. **Final Report**: `cycle_report_final`

### Version History Tables
- `cycle_report_attributes_planning_version_history`
- `cycle_report_attributes_scoping_version_history`
- Additional version history tables for other versioned entities

### Supporting Tables
- `universal_assignments` - Flexible assignment system
- `audit_log` - Universal audit trail
- `permissions` - Granular RBAC permissions
- `teams` - Group users for bulk assignments
- `workflow_configuration` - Phase workflow settings

## Implementation Steps

### 1. Clean Database Start
```bash
# Connect to PostgreSQL
psql -U postgres

# Create fresh database
DROP DATABASE IF EXISTS synapse_dt;
CREATE DATABASE synapse_dt;

# Connect to new database
\c synapse_dt

# Run the master script
\i /path/to/scripts/database_redesign/05_apply_redesign.sql

# Load reference data
\i /path/to/scripts/database_redesign/06_load_reference_data.sql
```

### 2. Verify Installation
```sql
-- Check all tables created
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- Check phase tables
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name LIKE 'cycle_report_%'
ORDER BY table_name;

-- Check enums
SELECT typname 
FROM pg_type 
WHERE typtype = 'e'
ORDER BY typname;
```

## Key Features

### 1. Enhanced Planning Phase
- Added `information_security_classification` field
- Includes data source and table mapping for PDE
- Tracks CDE, issues, and primary key flags

### 2. Universal Assignment System
- Assign any entity to any user with any role
- Track assignment history and delegations
- Support team-based assignments

### 3. Comprehensive Audit
- Separate audit tables from version history
- Track data access for sensitive information
- Phase transition audit trail

### 4. Flexible LOB Assignment
- Users can have multiple LOB assignments
- Reports can be associated with multiple LOBs
- Role-specific LOB assignments

## Migration Notes

Since this is a clean start:
1. No data migration scripts needed
2. Existing test cycles and reports will be removed
3. Users and reference data need to be re-created
4. All historical data will be lost

## Next Steps

1. Update application models to match new schema
2. Update API endpoints for new table structure  
3. Update UI components to use new naming
4. Create seed data for testing
5. Implement new business logic for phases

## Benefits

1. **Clarity**: Table names clearly indicate their purpose
2. **Consistency**: All phase tables follow same pattern
3. **Flexibility**: Universal assignments support any workflow
4. **Auditability**: Comprehensive audit without duplication
5. **Security**: Built-in support for data classification