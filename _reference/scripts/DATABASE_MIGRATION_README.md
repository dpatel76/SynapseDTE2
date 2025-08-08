# Database Migration and Reconciliation Tools

This directory contains tools for safely extracting database schema, migrating to a test database, and reconciling differences between databases.

## Overview

The migration tools provide:
- **Read-only** access to the production database
- Complete schema extraction including tables, columns, constraints, and indexes
- Seed data extraction for essential reference tables
- Test database creation and validation
- Comprehensive reconciliation reporting
- No impact on the production database

## Tools

### 1. `database_migration_reconciler.py`
Main Python script that handles:
- Schema extraction from source database (READ-ONLY)
- SQL migration script generation
- Test database schema creation
- Schema and data reconciliation
- Detailed reporting

### 2. `setup_test_database.sh`
Shell script to create the test database before running migrations.

## Usage

### Step 1: Setup Test Database

```bash
# Make the script executable
chmod +x scripts/setup_test_database.sh

# Run the setup script
./scripts/setup_test_database.sh
```

This will:
- Create a new test database (`synapse_dt_test`)
- Set up proper permissions
- Generate `.env.test` configuration file

### Step 2: Run Migration and Reconciliation

```bash
# Install required Python packages if needed
pip install asyncpg

# Run the migration reconciler
python scripts/database_migration_reconciler.py
```

You can also run without confirmation prompt:
```bash
python scripts/database_migration_reconciler.py --no-confirm
```

### Step 3: Review Output

The script generates several files:

1. **Migration SQL Script**: `migration_YYYYMMDD_HHMMSS.sql`
   - Complete DDL for all tables
   - Seed data INSERT statements
   - Can be used to recreate the database

2. **Reconciliation Report**: `reconciliation_report_YYYYMMDD_HHMMSS.json`
   - Detailed comparison results
   - Schema differences
   - Data differences
   - Validation errors

3. **Log File**: `migration_reconciliation_YYYYMMDD_HHMMSS.log`
   - Complete execution log
   - Useful for debugging

## Configuration

### Environment Variables

You can configure database connections using environment variables:

```bash
export SOURCE_DATABASE_URL="postgresql://user:pass@host:port/source_db"
export TEST_DATABASE_URL="postgresql://user:pass@host:port/test_db"
```

Or use the generated `.env.test` file.

### Seed Tables

The following tables are considered "seed tables" and their data is extracted:
- users
- roles
- permissions
- role_permissions
- lobs
- testing_cycles
- reports
- workflow_phases
- workflow_activities
- workflow_activity_templates
- workflow_activity_dependencies
- report_types
- regulatory_bodies
- sla_configurations
- notification_templates

## Safety Features

1. **Read-Only Connection**: The source database is accessed with `default_transaction_read_only = 'on'`
2. **No Production Modifications**: All operations on production are SELECT only
3. **Test Database Isolation**: All modifications happen only in the test database
4. **Confirmation Prompt**: Requires explicit confirmation before proceeding
5. **Comprehensive Logging**: All operations are logged for audit trail

## Reconciliation Report

The reconciliation report includes:

### Summary Section
- Total tables processed
- Number of seed tables
- Count of schema differences
- Count of data differences
- Validation errors

### Schema Differences
- Missing tables
- Extra tables
- Column mismatches
- Data type differences
- Constraint differences

### Data Differences
- Row count mismatches
- Missing records
- Extra records
- Data content mismatches

## Example Output

```
=== Database Migration and Reconciliation Tool ===
Source Database: localhost:5432/synapse_dt
Test Database: localhost:5432/synapse_dt_test
==================================================

=== Extracting Schema from Source Database ===
✓ Connected to source database in READ-ONLY mode
Found 45 tables to process

Processing table: users
  - Extracted 10 seed records
  ✓ 10 columns, 3 constraints, 2 indexes, 10 rows

=== Generating Migration SQL ===
✓ Migration SQL saved to: migration_20240315_143022.sql

=== Creating Test Database Schema ===
✓ Test database schema created successfully

=== Reconciling Schemas ===
✓ Schema reconciliation complete. Found 0 differences

=== Reconciling Data ===
Reconciling data for: users
  ✓ Row count matches: 10
  ✓ Data content matches

=== Reconciliation Summary ===
Total tables processed: 45
Seed tables with data: 14
Schema differences: 0
Data differences: 0
Validation errors: 0

✓ Migration and reconciliation completed successfully!
```

## Troubleshooting

### Common Issues

1. **Permission Denied**
   - Ensure database user has appropriate permissions
   - Check PostgreSQL pg_hba.conf settings

2. **Connection Refused**
   - Verify database is running
   - Check host and port settings
   - Ensure PostgreSQL is listening on the correct interface

3. **Module Not Found**
   - Install required dependencies: `pip install asyncpg`

4. **Test Database Already Exists**
   - The setup script will prompt to drop and recreate
   - Or manually drop: `DROP DATABASE synapse_dt_test;`

## Advanced Usage

### Custom Seed Tables

Edit the `SEED_TABLES` list in `database_migration_reconciler.py` to include additional tables:

```python
SEED_TABLES = [
    'users',
    'roles',
    # Add your custom tables here
    'my_reference_table',
]
```

### Exclude Tables

Add tables to `EXCLUDE_TABLES` to skip them during migration:

```python
EXCLUDE_TABLES = [
    'alembic_version',
    'pg_stat_statements',
    'temporary_table',
]
```

## Security Notes

- Never commit `.env.test` files with real credentials
- Use read-only database users when possible
- Ensure test databases are properly isolated
- Regularly clean up test databases after use