# Deployment Without Source Database Access

This guide explains how to deploy SynapseDTE database on a machine that does NOT have access to the source database.

## Overview

The deployment uses a two-step process:
1. **Export** (on machine WITH source database)
2. **Import** (on target machine WITHOUT source database)

## Step 1: Export (One-time, on source machine)

On a machine with access to the source database:

```bash
# Navigate to project directory
cd /path/to/SynapseDTE

# Export schema and seed data
python migrations/scripts/export_schema.py
```

This creates three files in `migrations/schema/`:
- `complete_schema.sql` (465KB) - Complete database structure
- `seed_data.sql` (361KB) - Essential data (roles, permissions, etc.)
- `README.md` - Deployment instructions

### Files Created

The export includes:
- ✅ All 126 tables with complete structure
- ✅ All PostgreSQL ENUM types (50+)
- ✅ All indexes and constraints
- ✅ All foreign key relationships
- ✅ Essential seed data:
  - 7 system roles
  - 83 permissions
  - 208 role-permission mappings
  - 8 LOBs (Lines of Business)
  - 46 workflow activity templates
  - 36 workflow dependencies
  - 407 regulatory data dictionary entries
  - 6 test users

## Step 2: Deploy (On target machine)

### Option A: Automated Deployment (Recommended)

1. **Copy files to target machine**:
   ```bash
   # Copy the entire schema directory
   scp -r migrations/schema/ user@target-machine:/path/to/deployment/
   
   # Also copy the deployment script
   scp migrations/scripts/create_database_from_schema.py user@target-machine:/path/to/deployment/
   ```

2. **On target machine, run**:
   ```bash
   # Set database connection parameters (optional, defaults to localhost)
   export DB_HOST=localhost
   export DB_PORT=5432
   export DB_USER=postgres
   export DB_PASSWORD=postgres
   
   # Run deployment
   python create_database_from_schema.py
   ```

### Option B: Manual Deployment

1. **Create database**:
   ```bash
   createdb -U postgres synapse_dt
   ```

2. **Load schema**:
   ```bash
   psql -U postgres -d synapse_dt -f schema/complete_schema.sql
   ```

3. **Load seed data**:
   ```bash
   psql -U postgres -d synapse_dt -f schema/seed_data.sql
   ```

## Test Users

After deployment, these users are available:

| Email | Password | Role |
|-------|----------|------|
| admin@example.com | password123 | Admin |
| tester1@example.com | password123 | Tester |
| tester2@example.com | password123 | Tester |
| test.manager@example.com | password123 | Test Executive |
| report.owner@example.com | password123 | Report Owner |
| data.owner@example.com | password123 | Data Owner |

## Verification

After deployment, verify the database:

```sql
-- Connect to database
psql -U postgres -d synapse_dt

-- Check table count (should be 126)
SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';

-- Check users
SELECT email, role FROM users;

-- Check roles
SELECT COUNT(*) as role_count FROM roles;
-- Should return 7

-- Check permissions
SELECT COUNT(*) as permission_count FROM permissions;
-- Should return 83
```

## What's Included vs Not Included

### ✅ Included (Everything needed for system to function):
- Complete database schema (all 126 tables)
- All ENUM types and constraints
- System roles and permissions
- Role-permission mappings
- Test users with known passwords
- Workflow configurations
- Regulatory data dictionary
- Lines of Business (LOBs)

### ❌ Not Included (Production/test data):
- Production user accounts
- Test execution history
- Audit logs
- Document uploads
- Observations and findings
- Test cycles and results

## Troubleshooting

### Common Issues

1. **psql: command not found**
   ```bash
   # Install PostgreSQL client
   # Ubuntu/Debian
   sudo apt-get install postgresql-client
   
   # macOS
   brew install postgresql
   ```

2. **Permission denied**
   ```bash
   # Ensure user has createdb privilege
   psql -U postgres -c "ALTER USER youruser CREATEDB;"
   ```

3. **Database already exists**
   ```bash
   dropdb synapse_dt
   # Then retry creation
   ```

4. **Foreign key constraint errors**
   - The seed_data.sql file disables constraints during import
   - If issues persist, check PostgreSQL version (requires 12+)

## File Structure After Deployment

```
migrations/
├── schema/
│   ├── complete_schema.sql    # Database structure
│   ├── seed_data.sql          # Essential data
│   └── README.md              # Deployment guide
└── scripts/
    ├── create_database_from_schema.py  # Automated deployment
    └── export_schema.py               # Export script (not needed on target)
```

## Next Steps

1. **Update application configuration**:
   ```bash
   # In .env file
   DATABASE_URL=postgresql://username:password@localhost:5432/synapse_dt
   ```

2. **Start application**:
   ```bash
   # Backend
   uvicorn app.main:app --reload
   
   # Frontend
   cd frontend && npm start
   ```

3. **Login** with test user credentials above

## Summary

This deployment method allows you to:
- ✅ Deploy without source database access
- ✅ Create identical database structure
- ✅ Include all necessary seed data
- ✅ Have working test users immediately
- ✅ Start using the system right away

The exported files are portable and can be:
- Stored in version control
- Used for multiple deployments
- Shared with deployment teams
- Used for disaster recovery