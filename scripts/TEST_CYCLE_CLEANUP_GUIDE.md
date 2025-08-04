# Test Cycle Cleanup Guide

This guide explains how to safely remove test cycles and all their dependent data from the SynapseDTE database.

## Overview

The database has a complex hierarchy of test cycle-related data:

1. **test_cycles** - Main table containing cycle information
2. **cycle_reports** - Junction table linking cycles to reports
3. **workflow_phases** - 9 workflow phases per cycle-report combination
4. **workflow_activities** - Individual activities within each phase
5. **cycle_report_\*** tables - Phase-specific data (planning, scoping, data profiling, etc.)
6. **Assignment tables** - Data owner and attribute assignments
7. **Metrics and audit tables** - Performance and audit tracking

## Database Schema Hierarchy

```
test_cycles (cycle_id)
├── cycle_reports (cycle_id, report_id)
│   ├── workflow_phases (phase_id, cycle_id, report_id)
│   │   ├── workflow_activities (activity_id, cycle_id, report_id, phase_id)
│   │   │   └── workflow_activity_history (activity_id)
│   │   ├── cycle_report_planning_* (phase_id, cycle_id)
│   │   ├── cycle_report_scoping_* (phase_id, cycle_id)
│   │   ├── cycle_report_data_profiling_* (phase_id, cycle_id)
│   │   ├── cycle_report_sample_selection_* (phase_id, cycle_id)
│   │   ├── cycle_report_test_execution_* (phase_id, cycle_id)
│   │   └── cycle_report_test_report_* (phase_id, cycle_id)
│   ├── test_executions (cycle_id, report_id)
│   └── observations (cycle_id, report_id)
├── attribute_lob_assignments (cycle_id)
├── data_owner_assignments (cycle_id)
├── phase_metrics (cycle_id)
├── execution_metrics (cycle_id)
└── llm_audit_logs (cycle_id)
```

## Available Cleanup Scripts

### 1. Python Script (`comprehensive_test_cycle_cleanup.py`)

**Features:**
- Comprehensive error handling
- Dry-run capability
- Detailed logging and reporting
- Orphaned record cleanup
- Progress tracking

**Usage Examples:**

```bash
# Dry run for a specific cycle
python scripts/comprehensive_test_cycle_cleanup.py --cycle-id 123 --dry-run

# Delete a specific test cycle
python scripts/comprehensive_test_cycle_cleanup.py --cycle-id 123

# Delete all test cycles (with confirmation)
python scripts/comprehensive_test_cycle_cleanup.py --all-cycles --confirm

# Clean up orphaned records only
python scripts/comprehensive_test_cycle_cleanup.py --orphaned-only --confirm

# Custom database connection
python scripts/comprehensive_test_cycle_cleanup.py --cycle-id 123 \
    --db-host localhost --db-port 5432 --db-name synapse_dt --db-user postgres
```

### 2. SQL Script (`test_cycle_cleanup.sql`)

**Features:**
- Direct SQL execution
- Manual control over each step
- Verification queries
- Bulk cleanup options

**Usage:**

1. Open the SQL file in your database client
2. Replace `:cycle_id` with the actual cycle ID
3. Execute the sections in order:
   - Part 1: Delete dependent data
   - Part 2: Delete workflow structure
   - Part 3: Delete core relationships
   - Part 4: Delete main table
   - Verification: Check deletion success

## Pre-Cleanup Checklist

Before running any cleanup:

1. **Create a backup:**
   ```bash
   pg_dump -h localhost -U postgres synapse_dt > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

2. **Identify the cycle to delete:**
   ```sql
   SELECT cycle_id, cycle_name, status, start_date, end_date 
   FROM test_cycles 
   ORDER BY cycle_id;
   ```

3. **Check related data count:**
   ```sql
   SELECT 
       tc.cycle_id,
       tc.cycle_name,
       COUNT(cr.report_id) as report_count,
       COUNT(wp.phase_id) as phase_count,
       COUNT(wa.activity_id) as activity_count
   FROM test_cycles tc
   LEFT JOIN cycle_reports cr ON tc.cycle_id = cr.cycle_id
   LEFT JOIN workflow_phases wp ON tc.cycle_id = wp.cycle_id
   LEFT JOIN workflow_activities wa ON tc.cycle_id = wa.cycle_id
   WHERE tc.cycle_id = YOUR_CYCLE_ID
   GROUP BY tc.cycle_id;
   ```

4. **Verify no active processes:**
   - Check that no Temporal workflows are running for the cycle
   - Ensure no users are actively working on the cycle

## Foreign Key Relationships

The following cascade delete relationships are configured in the models:

- `TestCycle` → `CycleReport` (cascade="all, delete-orphan")
- `TestCycle` → `WorkflowPhase` (cascade="all, delete-orphan")
- `WorkflowPhase` → `WorkflowActivity` (cascade="all, delete-orphan")
- `WorkflowActivity` → `WorkflowActivityHistory` (cascade="all, delete-orphan")

However, many `cycle_report_*` tables may not have cascade deletes configured at the database level, so manual deletion is required.

## Deletion Order

The scripts follow this deletion order to avoid foreign key constraint violations:

1. **Most dependent data** (activity history, audit logs)
2. **Phase-specific data** (test execution results, reviews)
3. **Phase data** (planning, scoping, data profiling, etc.)
4. **Assignment data** (data owner assignments, LOB assignments)
5. **Workflow structure** (activities, phases)
6. **Core relationships** (cycle_reports)
7. **Main table** (test_cycles)

## Common Issues and Solutions

### Issue: Foreign Key Constraint Violations

**Solution:** Ensure you're following the correct deletion order. The scripts are designed to handle this automatically.

### Issue: Orphaned Records

**Solution:** Use the orphaned record cleanup:
```bash
python scripts/comprehensive_test_cycle_cleanup.py --orphaned-only --confirm
```

### Issue: Table Doesn't Exist

**Solution:** The scripts check for table existence. If a table doesn't exist, it's skipped automatically.

### Issue: Permission Denied

**Solution:** Ensure your database user has DELETE permissions on all tables:
```sql
GRANT DELETE ON ALL TABLES IN SCHEMA public TO your_user;
```

## Verification After Cleanup

After running the cleanup, verify the deletion was successful:

```sql
-- Check main table
SELECT COUNT(*) FROM test_cycles WHERE cycle_id = YOUR_CYCLE_ID;

-- Check for orphaned records
SELECT 'cycle_reports' as table_name, COUNT(*) as count
FROM cycle_reports WHERE cycle_id = YOUR_CYCLE_ID
UNION ALL
SELECT 'workflow_phases', COUNT(*)
FROM workflow_phases WHERE cycle_id = YOUR_CYCLE_ID
UNION ALL
SELECT 'workflow_activities', COUNT(*)
FROM workflow_activities WHERE cycle_id = YOUR_CYCLE_ID;
```

All counts should return 0.

## Recovery

If you need to recover from a mistake:

1. **Stop any ongoing operations**
2. **Restore from backup:**
   ```bash
   psql -h localhost -U postgres -d synapse_dt < backup_file.sql
   ```
3. **Verify data integrity**
4. **Re-run cleanup with correct parameters**

## Best Practices

1. **Always use dry-run first** to understand the impact
2. **Create backups** before any destructive operations
3. **Test on non-production** environments first
4. **Monitor logs** during cleanup operations
5. **Verify results** after cleanup completion
6. **Clean up orphaned records** periodically

## Support

If you encounter issues:

1. Check the log files generated by the Python script
2. Review the database error messages
3. Verify your database permissions
4. Ensure all required tables exist
5. Check for any running transactions that might be blocking the cleanup

## Example Cleanup Session

```bash
# 1. Check what will be deleted
python scripts/comprehensive_test_cycle_cleanup.py --cycle-id 123 --dry-run

# 2. Create backup
pg_dump -h localhost -U postgres synapse_dt > backup_before_cycle_123_cleanup.sql

# 3. Perform cleanup
python scripts/comprehensive_test_cycle_cleanup.py --cycle-id 123

# 4. Verify cleanup
python scripts/comprehensive_test_cycle_cleanup.py --cycle-id 123 --dry-run

# 5. Clean up any orphaned records
python scripts/comprehensive_test_cycle_cleanup.py --orphaned-only --confirm
```

This should result in a clean deletion of test cycle 123 and all its dependent data.