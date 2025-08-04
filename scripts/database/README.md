# Database Migrations

This directory contains database migration scripts and utilities for SynapseDTE.

## Directory Structure

```
migrations/
├── README.md                    # This file
├── alembic/                    # Alembic migration files (auto-generated)
│   └── versions/               # Individual migration versions
└── scripts/                    # Manual migration and utility scripts
    └── create_test_database.py # Complete test database creation script
```

## Database Deployment Options

### Option 1: With Source Database Access

Use `create_test_database.py` when you have access to an existing database:

- **Complete Schema Copy**: Copies all 126 tables from the source database
- **Preserves Structure**: Maintains all constraints, indexes, and PostgreSQL ENUM types
- **Seed Data**: Includes essential data for system operation (RBAC, users, etc.)
- **Non-Destructive**: Only reads from source database, never modifies it
- **Reconciliation Report**: Provides detailed comparison between source and test databases

### Option 2: Without Source Database (Deployment on New Machine)

Use the two-step process for machines without source database access:

#### Step 1: Export Schema (on machine with source database)
```bash
python migrations/scripts/export_schema.py
```

This creates:
- `migrations/schema/complete_schema.sql` - Full database schema
- `migrations/schema/seed_data.sql` - Essential seed data
- `migrations/schema/README.md` - Deployment instructions

#### Step 2: Create Database (on target machine)
```bash
python migrations/scripts/create_database_from_schema.py
```

Or manually:
```bash
createdb synapse_dt
psql -d synapse_dt -f migrations/schema/complete_schema.sql
psql -d synapse_dt -f migrations/schema/seed_data.sql
```

### Prerequisites

1. **PostgreSQL Client Tools**: Ensure `pg_dump` and `psql` are installed
   ```bash
   # macOS
   brew install postgresql
   
   # Ubuntu/Debian
   sudo apt-get install postgresql-client
   
   # RHEL/CentOS
   sudo yum install postgresql
   ```

2. **Python Dependencies**: All required packages from requirements.txt

3. **Database Access**: 
   - Read access to source database
   - Create database privileges on PostgreSQL server

### Usage

#### Basic Usage

```bash
# Run from project root
python migrations/scripts/create_test_database.py
```

This will:
1. Create a test database named `synapse_dt_test`
2. Copy complete schema from source database
3. Seed essential data (roles, permissions, test users)
4. Generate a reconciliation report

#### Environment Configuration

The script uses the `DATABASE_URL` environment variable:

```bash
# Set source database URL
export DATABASE_URL=postgresql://username:password@localhost:5432/source_db

# Run migration
python migrations/scripts/create_test_database.py
```

#### Custom Test Database Name

To use a different test database name, modify the script:

```python
# In create_test_database.py
migration = CompleteDatabaseMigrationV2(test_db_name="my_custom_test_db")
```

### What Gets Created

#### 1. Complete Schema (126 tables)
- All tables with original structure
- All indexes and constraints
- All PostgreSQL ENUM types (50+ enums)
- All foreign key relationships

#### 2. Essential Seed Data
- **Roles**: 7 system roles (Admin, Tester, Test Executive, etc.)
- **Permissions**: 83 system permissions
- **Role-Permission Mappings**: 208 mappings
- **LOBs**: 8 Lines of Business
- **Users**: 10 test users (see below)
- **Workflow Templates**: 46 activity templates
- **Data Dictionary**: 407 regulatory data dictionary entries

#### 3. Test Users Created

| Email | Role | Password |
|-------|------|----------|
| admin@example.com | Admin | password123 |
| tester1@example.com | Tester | password123 |
| tester2@example.com | Tester | password123 |
| test.manager@example.com | Test Executive | password123 |
| report.owner1@example.com | Report Owner | password123 |
| report.owner2@example.com | Report Owner | password123 |
| data.owner1@example.com | Data Owner | password123 |
| data.owner2@example.com | Data Owner | password123 |
| report.executive@example.com | Report Owner Executive | password123 |
| data.executive@example.com | Data Executive | password123 |

#### 4. Sample Test Data
- 3 Test Cycles (Q1, Q2, Q3 2024)
- 3 Test Reports (FR Y-14M, FFIEC 031, FR Y-9C)

### Reconciliation Report

The script generates a detailed reconciliation report showing:
- Table counts in source vs test database
- Record counts for each table
- Status indicators:
  - ✅ PERFECT MATCH - Same record count in both
  - 📊 DATA PRESENT - Table has data (may differ from source)
  - ✓ BOTH EMPTY - No data in either database
  - ○ NO DATA - Source has data, test is empty
  - ❌ MISSING IN TEST - Table exists in source but not test

### After Migration

1. **Update .env file**:
   ```bash
   DATABASE_URL=postgresql://username:password@localhost:5432/synapse_dt_test
   ```

2. **Verify connection**:
   ```bash
   psql postgresql://username:password@localhost:5432/synapse_dt_test -c "\dt"
   ```

3. **Run application**:
   ```bash
   uvicorn app.main:app --reload
   ```

### Troubleshooting

#### pg_dump not found
```bash
# Add PostgreSQL bin to PATH
export PATH=/usr/local/pgsql/bin:$PATH
```

#### Permission denied
Ensure your database user has:
- `CREATEDB` privilege for creating test database
- `SELECT` privilege on all source tables

#### Foreign key errors
The script handles dependencies automatically, but if issues persist:
1. Check source database integrity
2. Ensure all ENUM types are created first
3. Verify table creation order

### Advanced Options

#### Copy Specific Data

To copy data from specific tables, modify the `seed_essential_data` method:

```python
# Add to base_tables list
base_tables = [
    'your_table_name',
    # ... other tables
]
```

#### Exclude Tables

To exclude certain tables from migration:

```python
# In dump_and_restore_schema method
dump_cmd.extend(['--exclude-table=public.table_to_exclude'])
```

### Clean Up

To remove the test database:

```bash
psql -U postgres -c "DROP DATABASE IF EXISTS synapse_dt_test"
```

## Alembic Migrations

For incremental schema changes, use Alembic:

```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

See Alembic documentation for more details.

## Best Practices

1. **Always backup** before running migrations
2. **Test migrations** on test database first
3. **Review reconciliation report** to ensure data integrity
4. **Document** any custom modifications to migration scripts
5. **Version control** all migration files

## Support

For issues or questions:
1. Check the reconciliation report for missing data
2. Verify PostgreSQL client tools are installed
3. Ensure database permissions are correct
4. Review script logs for detailed error messages