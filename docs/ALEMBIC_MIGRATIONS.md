# Alembic Database Migrations Guide

## Overview

This project uses Alembic for database schema version control and migrations. The initial migration has been set up to mark the current database state as the baseline.

## Current Status

- **Initial Migration ID**: `3be61ad5f00f`
- **Created**: 2025-08-04 07:13:48
- **Description**: Baseline migration marking the current 126-table schema

## Setup for New Machines

### Quick Setup

Run the provided setup script:

```bash
./scripts/setup_new_machine_with_alembic.sh
```

This script will:
1. Check PostgreSQL connection
2. Create the database (if needed)
3. Run SQL initialization scripts
4. Apply Alembic migrations
5. Verify the setup

### Manual Setup

If you prefer manual setup:

```bash
# 1. Create database
psql -h localhost -p 5433 -U synapse_user -d postgres -c "CREATE DATABASE synapse_dt;"

# 2. Run SQL scripts
for script in scripts/database/08032025/*.sql; do
    psql -h localhost -p 5433 -U synapse_user -d synapse_dt -f "$script"
done

# 3. Set database URL
export DATABASE_URL="postgresql://synapse_user:synapse_password@localhost:5433/synapse_dt"

# 4. Run Alembic migrations
alembic upgrade head
```

## Making Database Changes

### 1. Modify SQLAlchemy Models

Edit the models in `app/models/` to reflect your desired changes.

### 2. Generate Migration

```bash
# Set database URL
export DATABASE_URL="postgresql://synapse_user:synapse_password@localhost:5433/synapse_dt"

# Generate migration
alembic revision --autogenerate -m "describe_your_changes"
```

### 3. Review Generated Migration

Always review the generated migration file in `alembic/versions/`:
- Check that all intended changes are captured
- Verify no unintended changes are included
- Add any custom migration logic if needed

### 4. Apply Migration

```bash
# Apply to database
alembic upgrade head

# Or test first with --sql flag
alembic upgrade head --sql
```

### 5. Rollback (if needed)

```bash
# Rollback one revision
alembic downgrade -1

# Rollback to specific revision
alembic downgrade 3be61ad5f00f
```

## Common Tasks

### Check Current Version

```bash
alembic current
```

### View Migration History

```bash
alembic history
```

### Create Empty Migration

For complex migrations that can't be auto-generated:

```bash
alembic revision -m "complex_migration"
```

### Test Migration Without Applying

```bash
alembic upgrade head --sql > migration_preview.sql
```

## Best Practices

1. **Always Review Auto-generated Migrations**
   - Alembic may not detect all changes correctly
   - Complex changes may need manual adjustment

2. **Test Migrations**
   - Test on a copy of the database first
   - Have a rollback plan

3. **Descriptive Messages**
   - Use clear, descriptive migration messages
   - Include ticket numbers if applicable

4. **Data Migrations**
   - Be careful with data migrations
   - Consider performance for large tables
   - Always backup before data migrations

5. **Team Coordination**
   - Communicate database changes to the team
   - Avoid conflicting migrations

## Troubleshooting

### "Can't locate revision" Error

```bash
# Check alembic_version table
psql -d synapse_dt -c "SELECT * FROM alembic_version;"

# Reset if needed (CAUTION: only on dev)
psql -d synapse_dt -c "DELETE FROM alembic_version;"
alembic stamp head
```

### Migration Conflicts

If multiple developers create migrations:
1. Merge the latest changes
2. Delete your local migration
3. Regenerate after merge

### Failed Migration

1. Check error message
2. Fix the issue in the migration file
3. If partially applied, may need manual cleanup
4. Rerun migration

## Container-Specific Notes

When using Docker containers:

```bash
# Run migrations in backend container
docker-compose -f docker-compose.container.yml exec backend alembic upgrade head

# Or during container startup (add to entrypoint)
alembic upgrade head && python main.py
```

## Important Files

- `alembic.ini` - Alembic configuration
- `alembic/env.py` - Migration environment setup
- `alembic/versions/` - Migration files
- `scripts/generate_initial_migration.py` - Helper for generating migrations
- `scripts/setup_new_machine_with_alembic.sh` - Setup script for new machines

## Migration Naming Convention

Use descriptive names that indicate what changed:
- `add_user_preferences_table`
- `update_report_status_enum`
- `add_index_to_test_cycles`
- `remove_deprecated_columns`

## Contact

For questions about database migrations, contact the development team.