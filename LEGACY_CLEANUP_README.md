# Legacy Table Cleanup Instructions

This directory contains scripts to safely clean up legacy database tables that have been replaced by the new unified architecture.

## 🎯 Overview

The SynapseDTE application has been migrated to a unified planning architecture. This cleanup removes old tables that are no longer needed, freeing up database space and improving performance.

## 📋 What Will Be Cleaned Up

### Tables to be REMOVED:
- **Sample Selection Legacy Tables** (~15 tables)
  - `sample_sets`, `sample_records`, `sample_submissions`
  - `individual_samples`, `sample_validation_results`
  - `sample_approval_history`, `sample_upload_history`
  - `llm_sample_generations`, `sample_feedback`
  - And more...

- **Versioning Legacy Tables** (~8 tables)
  - `version_history`, `workflow_version_operations`
  - `planning_phase_versions`, `*_versions_old`
  - And more...

- **Phase Tracking Legacy Tables** (~6 tables)
  - `data_profiling_phases`, `scoping_phases`
  - `test_execution_phases`, `observation_management_phases`
  - And more...

- **Decision Tracking Legacy Tables** (~5 tables)
  - `attribute_decisions_old`, `sample_decisions_old`
  - `scoping_decisions_old`, `observation_decisions_old`
  - And more...

- **Migration Tracking Tables** (~4 tables)
  - `sample_selection_migration_tracking`
  - `scoping_migration_tracking`
  - And more...

- **Associated Objects**
  - Legacy sequences (15+ sequences)
  - Legacy enums (15+ enums)
  - Orphaned indexes and constraints
  - Legacy functions and triggers

### Tables to be KEPT:
- ✅ **New Unified Planning Tables**
  - `cycle_report_planning_versions`
  - `cycle_report_planning_attributes`
  - `cycle_report_planning_data_sources`
  - `cycle_report_planning_pde_mappings`

- ✅ **Core Application Tables**
  - `users`, `reports`, `test_cycles`, `workflow_phases`
  - All RBAC and permission tables
  - All current workflow and activity tables

## 🚀 Quick Start

### Option 1: Automated Script (Recommended)
```bash
# Run the interactive cleanup script
./run_legacy_cleanup.sh
```

### Option 2: Manual Execution
```bash
# Step 1: Check what will be cleaned up
psql -h localhost -U your_user -d your_database -f check_tables_before_cleanup.sql

# Step 2: Execute the cleanup
psql -h localhost -U your_user -d your_database -f cleanup_legacy_tables_safe.sql
```

## ⚠️ Important Prerequisites

### 1. **Create a Full Database Backup**
```bash
# Create a complete backup before running cleanup
pg_dump -h localhost -U your_user -d your_database > backup_$(date +%Y%m%d_%H%M%S).sql
```

### 2. **Stop Application Services**
```bash
# Stop all application processes that might be using the database
sudo systemctl stop synapsdte
# Or however you manage your application services
```

### 3. **Verify New Tables Exist**
The cleanup script will automatically verify that new unified planning tables exist before proceeding.

## 📁 Files Included

| File | Description |
|------|-------------|
| `run_legacy_cleanup.sh` | Interactive cleanup script (recommended) |
| `check_tables_before_cleanup.sql` | Verification script to see what will be cleaned |
| `cleanup_legacy_tables_safe.sql` | Main cleanup script with safety checks |
| `cleanup_legacy_tables.sql` | Original comprehensive cleanup script |
| `LEGACY_CLEANUP_README.md` | This documentation file |

## 🔒 Safety Features

- **Transaction-based**: All changes are wrapped in a transaction
- **Rollback capability**: If something goes wrong, changes can be rolled back
- **Pre-verification**: Checks that new tables exist before cleanup
- **Post-verification**: Confirms cleanup was successful
- **Detailed logging**: Shows progress and results of each cleanup phase

## 🏁 After Cleanup

1. **Restart Application Services**
   ```bash
   sudo systemctl start synapsdte
   ```

2. **Verify Application Functions**
   - Test key application features
   - Check that planning phase works correctly
   - Verify that unified architecture is functioning

3. **Monitor Performance**
   - Database should be faster due to reduced table count
   - Query performance should improve
   - Storage usage should decrease

## 🆘 Troubleshooting

### If Cleanup Fails
1. Check error messages in the script output
2. Verify database connection and permissions
3. Ensure new unified planning tables exist
4. If needed, restore from backup

### If Application Issues After Cleanup
1. Check application logs for missing table errors
2. Verify that all new unified tables exist
3. Restart application services
4. If problems persist, restore from backup

## 📊 Expected Results

After successful cleanup:
- **Database size reduction**: 20-30% smaller database
- **Improved performance**: Faster queries and operations
- **Cleaner schema**: Only active tables remain
- **Better maintenance**: Easier to understand and maintain

## 🎯 Support

If you encounter issues:
1. Check the error messages in the script output
2. Verify your database backup is complete
3. Ensure you have proper database permissions
4. Review the verification output before cleanup

The cleanup process is designed to be safe and reversible, but always maintain proper backups!