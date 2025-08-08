# SynapseDTE Database Export - 2025-07-29

## Overview

This directory contains a complete database export of SynapseDTE, including all schema changes up to July 29, 2025.

### Database Statistics
- **Total Tables**: 108 (including workflow/temporal tables)
- **Total Views**: 5
- **Total Sequences**: 70
- **Total ENUM Types**: 84
- **Total Indexes**: 521
- **Total Constraints**: 1424
- **Workflow/Temporal Tables**: 10

### Key Table Row Counts
- **users**: 26 rows
- **workflow_activities**: 0 rows
- **workflow_phases**: 18 rows
- **workflow_executions**: 0 rows
- **test_cycles**: 4 rows
- **reports**: 21 rows
- **lobs**: 8 rows

## Files in This Export

1. **01_complete_schema.sql** - Complete database schema
   - All table definitions
   - All ENUM types
   - All indexes and constraints
   - All sequences and views
   - Workflow/temporal table structures

2. **02_complete_data.sql** - Complete database data
   - ALL data from ALL tables
   - Includes test data, configurations, and transactional data
   - Foreign key constraints disabled during import

3. **03_seed_data_only.sql** - Essential seed data only
   - System roles and permissions
   - Test users
   - Workflow templates
   - Configuration data
   - Minimal data needed to run the system

4. **deploy.sh** - Automated deployment script
   - Handles database creation
   - Manages existing database scenarios
   - Provides verification
   - Two modes: full or seed-only

## Deployment Instructions

### Quick Start (Recommended)

```bash
# For complete database with all data:
./deploy.sh

# For minimal setup with seed data only:
./deploy.sh --seed-only
```

### Manual Deployment

1. **Create the database**:
   ```bash
   createdb -U postgres synapse_dt
   ```

2. **Load schema**:
   ```bash
   psql -U postgres -d synapse_dt -f 01_complete_schema.sql
   ```

3. **Load data** (choose one):
   ```bash
   # Option A: Complete data
   psql -U postgres -d synapse_dt -f 02_complete_data.sql
   
   # Option B: Seed data only
   psql -U postgres -d synapse_dt -f 03_seed_data_only.sql
   ```

### Using Different Database Credentials

```bash
# Set environment variables
export DB_USER=myuser
export DB_HOST=myhost
export DB_PORT=5432
export DB_NAME=mydatabase

# Run deployment
./deploy.sh
```

## Test Users

After deployment, these test users are available (password for all: `password123`):

| Email | Role | Purpose |
|-------|------|---------|
| admin@example.com | Admin | Full system access |
| tester1@example.com | Tester | Execute tests |
| tester2@example.com | Tester | Execute tests |
| test.manager@example.com | Test Executive | Manage test cycles |
| report.owner@example.com | Report Owner | Review reports |
| data.owner@example.com | Data Owner | Provide data |

## Important Notes

### Temporal/Workflow Tables
This export includes all temporal workflow tables:
- workflow_activities
- workflow_activity_dependencies
- workflow_activity_histories
- workflow_activity_templates
- workflow_alerts
- workflow_executions
- workflow_metrics
- workflow_phases
- workflow_steps
- workflow_transitions

### Schema Changes Since Previous Export
- Added RFI (Request for Information) version tables
- Enhanced evidence collection tables
- Added validation warning columns
- Updated query validation tables
- Added data owner permissions
- Enhanced audit trail functionality

### Data Considerations
- **Complete data export** includes ALL transactional data
- **Seed data export** includes only essential configuration
- Choose based on your needs:
  - Development/Testing: Use seed data only
  - Migration/Backup: Use complete data

## Troubleshooting

### Common Issues

1. **Permission Denied**
   ```bash
   # Ensure PostgreSQL user has proper permissions
   sudo -u postgres createuser --createdb yourusername
   ```

2. **Database Already Exists**
   - The deploy.sh script will prompt you for action
   - Choose to drop and recreate or load data only

3. **Foreign Key Violations**
   - Data exports disable triggers during import
   - If issues persist, check PostgreSQL version (12+ required)

4. **Large File Issues**
   - Complete data file may be large
   - Ensure sufficient disk space
   - Consider using seed data for development

### Verification Queries

```sql
-- Check if all tables loaded
SELECT COUNT(*) FROM information_schema.tables 
WHERE table_schema = 'public';
-- Should return 108

-- Check workflow tables
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name LIKE 'workflow%';

-- Check user access
SELECT u.email, r.role_name 
FROM users u 
JOIN user_roles ur ON u.user_id = ur.user_id 
JOIN roles r ON ur.role_id = r.role_id;
```

## Next Steps After Deployment

1. **Update application configuration**:
   ```bash
   # In project root .env file
   DATABASE_URL=postgresql://username:password@localhost:5432/synapse_dt
   ```

2. **Start the application**:
   ```bash
   # Backend (from project root)
   uvicorn app.main:app --reload
   
   # Frontend (from frontend directory)
   npm start
   ```

3. **Verify temporal workflows**:
   - Check that workflow tables are populated
   - Test workflow execution functionality
   - Verify activity templates are loaded

## Support

If you encounter issues:
1. Check the log files created during deployment
2. Verify PostgreSQL version (12+ required)
3. Ensure sufficient permissions and disk space
4. Review error messages in deployment output

## Export Metadata

- **Export Date**: 2025-07-29 22:24:28
- **Source Database**: synapse_dt
- **PostgreSQL Version**: Check with `psql --version`
- **Export Method**: pg_dump with comprehensive options
- **Includes**: Complete schema, all data, temporal tables
