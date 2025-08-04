# Unified Test Execution Database Migration

This directory contains scripts and SQL files to migrate from the legacy test execution system to the unified test execution architecture.

## Files

- `create_unified_test_execution_tables.sql` - SQL commands to create unified test execution tables
- `apply_database_changes.sh` - Shell script to apply database changes
- `verify_database_changes.sh` - Shell script to verify migration was successful
- `execute_database_changes.py` - Python script for advanced database operations

## Quick Start

### 1. Apply Database Changes

```bash
# Using shell script (recommended)
./apply_database_changes.sh

# Or using Python script
python3 execute_database_changes.py
```

### 2. Verify Migration

```bash
./verify_database_changes.sh
```

## Database Configuration

Set environment variables to override default database connection settings:

```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=synapse_dt
export DB_USER=synapse_user
export DB_PASSWORD=synapse_password
```

## What Gets Created

### New Tables

1. **cycle_report_test_execution_results** - Main test execution results table
2. **cycle_report_test_execution_reviews** - Tester review workflow table
3. **cycle_report_test_execution_audit** - Comprehensive audit trail table

### Key Features

- **Evidence Integration**: Direct integration with Request for Information phase evidence
- **Execution Versioning**: Support for test execution retries and versioning
- **Comprehensive Analysis**: Support for LLM analysis and database query execution
- **Tester Workflow**: Built-in tester approval workflow with quality scoring
- **Audit Trail**: Complete audit log of all test execution activities

### Constraints and Indexes

- Primary keys and foreign key relationships
- Unique constraints for execution versioning
- Performance indexes for common queries
- Check constraints for data integrity
- Triggers for automatic timestamp updates

## Migration Process

1. **Backup**: Legacy tables are automatically backed up with timestamp
2. **Create**: New unified tables are created with proper structure
3. **Indexes**: Performance indexes and constraints are added
4. **Triggers**: Update triggers for timestamp management
5. **Verify**: Installation verification and constraint checking

## Legacy Tables

The following legacy tables are backed up but not removed:

- `cycle_report_test_executions`
- `cycle_report_test_execution_document_analyses`
- `cycle_report_test_execution_database_tests`
- `test_result_reviews`
- `bulk_test_executions`
- `test_comparisons`
- `test_execution_audit_logs`

## Post-Migration Steps

1. **Update Application**: Use new unified models in your application
2. **Test APIs**: Verify new API endpoints work correctly
3. **Frontend**: Update frontend components to use new backend
4. **End-to-End Testing**: Run comprehensive tests
5. **Remove Legacy**: After confirming migration success, remove legacy tables

## Troubleshooting

### Connection Issues

```bash
# Test database connection
psql -h localhost -p 5432 -U synapse_user -d synapse_dt -c "SELECT version();"
```

### Check Migration Status

```bash
# Verify tables exist
psql -h localhost -p 5432 -U synapse_user -d synapse_dt -c "
SELECT table_name FROM information_schema.tables 
WHERE table_name LIKE '%test_execution%' 
ORDER BY table_name;
"
```

### Rollback

If you need to rollback:

1. Drop the unified tables:
```sql
DROP TABLE IF EXISTS cycle_report_test_execution_audit;
DROP TABLE IF EXISTS cycle_report_test_execution_reviews;
DROP TABLE IF EXISTS cycle_report_test_execution_results;
```

2. Restore from backup tables (if needed):
```sql
-- Example for restoring a backup table
ALTER TABLE cycle_report_test_executions_backup_20250718 RENAME TO cycle_report_test_executions;
```

## Support

For issues or questions:

1. Check the verification script output
2. Review the database logs
3. Ensure all foreign key dependencies exist
4. Verify database user permissions

## Architecture Benefits

The unified test execution architecture provides:

- **Simplified Data Model**: 3 tables instead of 7+ legacy tables
- **Better Performance**: Optimized indexes and query patterns
- **Evidence Integration**: Direct link to Request for Information evidence
- **Audit Trail**: Complete audit log of all activities
- **Scalability**: Designed for high-volume test execution
- **Maintainability**: Clean, well-documented table structure
- **Flexibility**: JSONB columns for extensible data storage