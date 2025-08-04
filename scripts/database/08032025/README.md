# Database Containerization Scripts

This directory contains scripts and files needed to set up the SynapseDTE database for containerized deployment.

## Overview

The database setup process consists of:
1. Extracting complete schema from existing database
2. Extracting seed data from existing database (read-only)
3. Creating test database to validate setup
4. Generating Docker deployment files

## Files

### Scripts

- `extract_schema_from_db.py` - Extracts database schema directly from PostgreSQL
- `extract_ddl_from_db.py` - Alternative DDL extraction with SERIAL type conversion
- `extract_data.py` - Extracts seed data from existing database (READ-ONLY access)
- `setup_test_db.py` - Creates and validates test database
- `create_minimal_seeds.py` - Creates minimal seed data for quick setup

### Generated Files

- `01_schema.sql` - Original schema export
- `01_schema_complete.sql` - Complete schema with sequences
- `01_schema_simple.sql` - Simplified schema using SERIAL types
- `03_minimal_seeds.sql` - Minimal seed data SQL
- `02_seed_data.sql` - Combined seed data for Docker deployment
- `seed_data/` - Individual JSON files with extracted data (45 tables)
- `sql_seeds/` - Individual SQL insert scripts
- `minimal_seeds/` - Minimal seed data JSON files
- `docker-compose.yml` - Docker compose configuration

## Column Organization

Tables are created with columns organized in this order:
1. **Primary Keys** - ID columns and composite keys
2. **Foreign Keys** - References to other tables
3. **Business Attributes** - Core business data
4. **Audit Fields** - created_by_id, updated_by_id
5. **Timestamp Fields** - created_at, updated_at, etc.

## Usage

### Step 1: Extract Schema

```bash
cd /Users/dineshpatel/code/projects/SynapseDTE/scripts/database/08032025

# Extract complete DDL from database
python extract_ddl_from_db.py
```

This generates:
- `00_drop_all.sql` - Script to drop all tables (use with caution!)
- `01_schema_complete.sql` - Complete schema with sequences
- `01_schema_simple.sql` - Simplified schema using SERIAL types

### Step 2: Extract Seed Data

```bash
python extract_data.py
```

This extracts data from the existing database in READ-ONLY mode and generates:
- `seed_data/*.json` - Extracted data in JSON format
- `sql_seeds/*.sql` - SQL INSERT statements
- `_extraction_summary.json` - Summary of extraction process

### Step 3: Test Database Setup

```bash
python setup_test_db.py
```

This:
- Creates a test database `synapse_dte_test`
- Applies the schema
- Loads seed data
- Validates the setup
- Generates Docker deployment files

### Step 4: Docker Deployment

```bash
# Start PostgreSQL container with initialized database
docker-compose up -d

# Check logs
docker-compose logs -f postgres

# Connect to database
docker exec -it synapse_dte_db psql -U synapse_user -d synapse_dte_test
```

## Seed Data Strategy

The extraction process uses different strategies for different tables:

### Full Extract Tables
These tables have all data extracted:
- `roles` - All user roles
- `permissions` - All permissions
- `role_permissions` - All role-permission mappings
- `lobs` - All Lines of Business
- `reports` - All report definitions
- `report_attributes` - All report attributes
- `workflow_phases` - All workflow phase definitions

### Sample Extract Tables
These tables have limited data extracted:
- `users` - 10 most recent users
- `test_cycles` - 5 most recent test cycles
- `cycle_reports` - 20 most recent cycle reports

### Skipped Tables
Large tables (>1000 rows) are skipped by default unless explicitly configured.

## Creating Minimal Seeds

For quick development setup, use the minimal seeds script:

```bash
python create_minimal_seeds.py
```

This creates essential data:
- Admin user (admin@example.com / admin123)
- Basic roles (Admin, Tester, Report Owner, Data Owner)
- Essential permissions
- Sample LOBs and reports
- One test cycle with reports

## Environment Variables

For containerized deployment, set these environment variables:

```env
# Database Configuration
DB_HOST=postgres
DB_PORT=5432
DB_NAME=synapse_dte
DB_USER=synapse_user
DB_PASSWORD=synapse_password

# Application Configuration
SECRET_KEY=your-secret-key-here
ENVIRONMENT=development
```

## Current Issues & Solutions

### Schema Issues
1. **Custom Types**: The schema contains custom types (e.g., `securityclassification`)
   - Solution: Add type definitions at the beginning of schema files
   ```sql
   CREATE TYPE securityclassification AS ENUM ('Public', 'Internal', 'Confidential', 'Restricted');
   ```

2. **Table Dependencies**: Foreign keys require specific creation order
   - Solution: Create tables in dependency order or use the simplified schema

3. **Sequences**: Some tables reference sequences that need pre-creation
   - Solution: Use `01_schema_simple.sql` which uses SERIAL types

## Migration Notes

Since Alembic migrations are broken, follow this process for schema changes:

1. Extract current schema using `extract_ddl_from_db.py`
2. Compare with previous schema version
3. Create migration SQL manually
4. Apply changes to test database first
5. Update Docker deployment files

## Troubleshooting

### Connection Issues
- Ensure PostgreSQL is running
- Check credentials in scripts match your setup
- Verify database names don't conflict

### Schema Issues
- Ensure custom types are defined before tables
- Check table creation order for foreign key dependencies
- Use `01_schema_simple.sql` if sequence issues occur
- Verify all required extensions are installed

### Data Issues
- Check `_extraction_summary.json` for errors
- Verify JSON files in `seed_data/` are valid
- Check SQL files in `sql_seeds/` for syntax

## Security Notes

1. **Never commit real production data** - Use anonymized/sample data only
2. **Change default passwords** before deployment
3. **Use environment variables** for sensitive configuration
4. **Restrict database access** in production

## Extracted Data Summary

- **Total Tables**: 100
- **Tables with Data**: 45
- **Skipped Tables**: 3 (too many rows)
- **Empty Tables**: 52

### Key Extracted Tables
- Users, roles, permissions (with mappings)
- Reports and report attributes
- Test cycles and cycle reports
- Workflow phases and activities
- Planning, scoping, and test execution data

## Next Steps

1. Fix schema issues (add custom types)
2. Test with `setup_test_db.py`
3. Verify application connectivity
4. Build Docker image with fixed schema
5. Deploy to container orchestration platform