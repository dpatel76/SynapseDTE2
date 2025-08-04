# SynapseDTE Migration Guide

## Quick Start

### Creating a Test Database

The fastest way to set up a test database with complete schema and data:

```bash
# Ensure DATABASE_URL points to your source database
export DATABASE_URL=postgresql://synapse_user:synapse_password@localhost:5432/synapse_dt

# Run the migration script
python migrations/scripts/create_test_database.py

# Update your .env to use the test database
export DATABASE_URL=postgresql://synapse_user:synapse_password@localhost:5432/synapse_dt_test
```

## Migration Overview

### What Gets Migrated

1. **Complete Schema** (126 tables)
   - All table structures
   - All indexes and constraints
   - All PostgreSQL ENUM types
   - All foreign key relationships

2. **Essential Data**
   - RBAC: Roles, Permissions, Mappings
   - Business: LOBs, Workflow Templates
   - Users: 10 test users with known passwords
   - Reference: Data Dictionary entries

3. **Test Data**
   - Sample test cycles
   - Sample reports
   - User-role assignments

### What Doesn't Get Migrated

- Production user data (except structure)
- Audit logs and history
- Test execution results
- Document uploads
- Observations and findings

## Step-by-Step Instructions

### 1. Prerequisites

Ensure you have:
- PostgreSQL client tools (`pg_dump`, `psql`)
- Python environment with project dependencies
- Database user with CREATEDB privilege
- Read access to source database

### 2. Run Migration

```bash
cd /path/to/SynapseDTE
python migrations/scripts/create_test_database.py
```

### 3. Verify Migration

Check the reconciliation report output:

```
====================================================================================================
COMPLETE RECONCILIATION REPORT
====================================================================================================
Table                                              Source       Test       Diff                 Status
---------------------------------------------------------------------------------------------------------
alembic_version                                         1          1          -        ✅ PERFECT MATCH
lobs                                                    8          8          -        ✅ PERFECT MATCH
permissions                                            83         83          -        ✅ PERFECT MATCH
...
---------------------------------------------------------------------------------------------------------

✅ SUCCESS: All 126 source tables exist in test database!
```

### 4. Connect to Test Database

```bash
# Verify connection
psql postgresql://synapse_user:synapse_password@localhost:5432/synapse_dt_test

# In psql
\dt                    # List all tables
\du                    # List users
SELECT * FROM users;   # Check test users
\q                     # Quit
```

### 5. Update Application Configuration

Update your `.env` file:

```env
# Old (source database)
# DATABASE_URL=postgresql://synapse_user:synapse_password@localhost:5432/synapse_dt

# New (test database)
DATABASE_URL=postgresql://synapse_user:synapse_password@localhost:5432/synapse_dt_test
```

### 6. Test the Application

```bash
# Start backend
uvicorn app.main:app --reload

# In another terminal, start frontend
cd frontend
npm start
```

Login with any test user:
- Email: `admin@example.com`
- Password: `password123`

## Test Users Reference

| Email | Role | Use Case |
|-------|------|----------|
| admin@example.com | Admin | System administration |
| tester1@example.com | Tester | Execute testing workflow |
| test.manager@example.com | Test Executive | Manage test cycles |
| report.owner1@example.com | Report Owner | Approve test results |
| data.owner1@example.com | Data Owner | Provide test data |

All passwords: `password123`

## Troubleshooting

### Common Issues

1. **pg_dump: command not found**
   ```bash
   # macOS
   brew install postgresql
   
   # Add to PATH
   export PATH="/usr/local/opt/postgresql/bin:$PATH"
   ```

2. **Permission denied creating database**
   ```sql
   -- Grant createdb permission
   ALTER USER synapse_user CREATEDB;
   ```

3. **Database already exists**
   ```bash
   # Drop and recreate
   psql -U postgres -c "DROP DATABASE synapse_dt_test"
   python migrations/scripts/create_test_database.py
   ```

4. **Foreign key constraint errors**
   - This is handled automatically by the script
   - Check logs for specific table issues

### Validation Checks

After migration, verify:

1. **Table Count**: Should be 126 tables
   ```sql
   SELECT COUNT(*) FROM information_schema.tables 
   WHERE table_schema = 'public';
   ```

2. **User Count**: Should have 10 test users
   ```sql
   SELECT COUNT(*) FROM users;
   ```

3. **RBAC Setup**: Roles and permissions
   ```sql
   SELECT COUNT(*) FROM roles;        -- Should be 7
   SELECT COUNT(*) FROM permissions;  -- Should be 83
   ```

## Advanced Usage

### Custom Database Name

Modify the script to use a different test database name:

```python
# In create_test_database.py
migration = CompleteDatabaseMigrationV2(test_db_name="my_test_db")
```

### Selective Data Copy

To copy specific production data:

```python
# Add tables to copy data from
production_tables_to_copy = [
    'workflow_definitions',
    'sla_configurations',
    # Add more tables as needed
]
```

### Exclude Sensitive Data

The script already excludes sensitive data like:
- Real user passwords
- Audit logs
- PII information
- Document contents

## Rollback

To remove the test database:

```bash
psql -U postgres -c "DROP DATABASE IF EXISTS synapse_dt_test"
```

## Next Steps

1. Run application tests against test database
2. Develop new features using test database
3. Use test database for training/demos
4. Create additional test data as needed

## Questions?

- Check reconciliation report for data discrepancies
- Review migration script logs for errors
- Ensure all prerequisites are met
- Verify database permissions