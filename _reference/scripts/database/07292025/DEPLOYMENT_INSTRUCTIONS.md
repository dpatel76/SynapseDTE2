# SynapseDTE Database Deployment Instructions

Generated: 2025-07-29

## Overview

This directory contains a complete database export of the SynapseDTE application database. This export includes ALL schema changes up to July 29, 2025, including workflow metadata tables.

**IMPORTANT**: This export is for the **main application database only**. Temporal Server uses a separate database (see Temporal Database section below).

## Files in This Export

| File | Size | Description |
|------|------|-------------|
| `01_complete_schema.sql` | 542KB | Complete database schema (108 tables, 84 ENUMs, 521 indexes) |
| `02_complete_data.sql` | 13MB | ALL data from ALL tables (complete backup) |
| `03_seed_data_only.sql` | 51KB | Essential seed data only (for development) |
| `deploy.sh` | 4.9KB | Automated deployment script |
| `verify_deployment.py` | 3KB | Python verification script |
| `README.md` | 5.6KB | Quick reference guide |
| `database_stats.json` | 353B | Database statistics |

## Quick Start Deployment

### Option 1: Automated Deployment (Recommended)

```bash
# Full deployment with all data
./deploy.sh

# Minimal deployment with seed data only
./deploy.sh --seed-only
```

### Option 2: Manual Deployment

```bash
# 1. Create database
createdb -U postgres synapse_dt

# 2. Load schema
psql -U postgres -d synapse_dt -f 01_complete_schema.sql

# 3. Load data (choose one):
# For complete data:
psql -U postgres -d synapse_dt -f 02_complete_data.sql

# For seed data only:
psql -U postgres -d synapse_dt -f 03_seed_data_only.sql

# 4. Verify deployment
python verify_deployment.py
```

## Database Architecture

### Main Application Database (`synapse_dt`)

The main database contains 108 tables including:

#### Core Tables
- User management (`users`, `rbac_roles`, `rbac_permissions`)
- Test cycles and reports (`test_cycles`, `reports`)
- Lines of Business (`lobs`)
- Audit trails (`audit_logs`, `llm_audit_logs`)

#### Workflow Metadata Tables (10 tables)
These tables store application-specific workflow information:
- `workflow_activities` - Activity tracking
- `workflow_activity_dependencies` - Activity relationships
- `workflow_activity_histories` - Activity audit trail
- `workflow_activity_templates` - Predefined activities
- `workflow_alerts` - Workflow notifications
- `workflow_executions` - Execution tracking
- `workflow_metrics` - Performance metrics
- `workflow_phases` - Phase management
- `workflow_steps` - Step definitions
- `workflow_transitions` - State transitions

### Temporal Server Database (SEPARATE)

**IMPORTANT**: Temporal uses a completely separate PostgreSQL database:

```yaml
Database Name: temporal
Database User: temporal
Database Password: temporal
Database Port: 5434 (not 5432!)
```

To set up Temporal database:
```bash
# Temporal is managed via Docker Compose
docker-compose -f docker-compose.temporal.yml up -d
```

This creates:
- PostgreSQL for Temporal on port 5434
- Temporal Server on port 7233
- Temporal UI on port 8088

## Deployment Steps for New Machine

### 1. Copy Export Files

```bash
# From source machine
scp -r /path/to/07292025/ user@target-machine:/deployment/

# Or via Git (if checked in)
git pull
cd scripts/database/07292025/
```

### 2. Install Prerequisites

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install postgresql postgresql-client

# macOS
brew install postgresql

# Verify installation
psql --version  # Should be 12+
```

### 3. Deploy Main Database

```bash
cd /deployment/07292025/

# Run automated deployment
./deploy.sh

# Follow prompts:
# - Choose deployment mode (full or seed-only)
# - Handle existing database if present
```

### 4. Deploy Temporal (if needed)

```bash
# From project root
docker-compose -f docker-compose.temporal.yml up -d

# Verify Temporal is running
docker-compose -f docker-compose.temporal.yml ps

# Access Temporal UI
open http://localhost:8088
```

### 5. Update Application Configuration

```bash
# Edit .env file in project root
DATABASE_URL=postgresql://postgres:password@localhost:5432/synapse_dt
TEMPORAL_HOST=localhost:7233
TEMPORAL_NAMESPACE=default
```

### 6. Verify Deployment

```bash
# Run verification script
python verify_deployment.py

# Expected output:
# ✓ Tables: 108 (expected: 108)
# ✓ Workflow tables: 10
# ✓ Test tables: XX
# ✓ Users: XX
# ✓ Test users available
```

## Test Users After Deployment

| Email | Password | Role |
|-------|----------|------|
| admin@example.com | password123 | Admin |
| tester1@example.com | password123 | Tester |
| tester2@example.com | password123 | Tester |
| test.manager@example.com | password123 | Test Executive |
| report.owner@example.com | password123 | Report Owner |
| data.owner@example.com | password123 | Data Owner |

## Troubleshooting

### Common Issues

1. **Permission Denied**
   ```bash
   # Grant createdb permission
   sudo -u postgres psql -c "ALTER USER youruser CREATEDB;"
   ```

2. **Port Conflicts**
   - Main DB uses port 5432
   - Temporal DB uses port 5434
   - Ensure both ports are available

3. **Docker Not Running**
   ```bash
   # Start Docker daemon
   sudo systemctl start docker  # Linux
   open -a Docker  # macOS
   ```

4. **Temporal Connection Failed**
   ```bash
   # Check Temporal is running
   docker-compose -f docker-compose.temporal.yml logs temporal-server
   ```

### Verification Queries

```sql
-- Check main database tables
psql -U postgres -d synapse_dt -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';"

-- Check workflow tables specifically
psql -U postgres -d synapse_dt -c "SELECT table_name FROM information_schema.tables WHERE table_name LIKE 'workflow%' ORDER BY table_name;"

-- Check Temporal database (separate)
psql -U temporal -h localhost -p 5434 -d temporal -c "\dt"
```

## What's Included vs Not Included

### ✅ Included in This Export
- Complete schema for main application database
- All workflow metadata tables
- All data (in full export mode)
- Essential seed data (in seed-only mode)
- Test users with known passwords
- All ENUMs, indexes, constraints

### ❌ NOT Included
- Temporal Server database (managed separately)
- Docker containers
- Application code
- Environment variables
- SSL certificates
- File uploads/attachments

## Next Steps After Deployment

1. **Start Temporal Services**
   ```bash
   docker-compose -f docker-compose.temporal.yml up -d
   ```

2. **Start Application**
   ```bash
   # Backend
   uvicorn app.main:app --reload --port 8000
   
   # Frontend
   cd frontend && npm install && npm start
   ```

3. **Access Services**
   - Application: http://localhost:8000
   - Frontend: http://localhost:3000
   - Temporal UI: http://localhost:8088

4. **Run Initial Tests**
   ```bash
   # Test database connection
   python -c "from app.core.database import engine; print('DB connected!')"
   
   # Test Temporal connection
   python -c "from app.core.temporal import get_temporal_client; print('Temporal connected!')"
   ```

## Migration Notes

### From Broken Alembic Setup
Since the Alembic migration system is broken, this export provides a clean way to set up the database:
1. The schema includes all migrations applied up to July 29, 2025
2. No need to run any Alembic migrations
3. Future migrations can be applied manually or Alembic can be reset

### Resetting Alembic (Optional)
After deployment, to reset Alembic:
```sql
-- Clear alembic version
TRUNCATE TABLE alembic_version;

-- Set to latest version
INSERT INTO alembic_version (version_num) VALUES ('latest_migration_id');
```

## Support Files

- `export_full_database.py` - Script used to generate this export
- `database_stats.json` - Statistics about the exported database
- `README.md` - Quick reference guide
- `verify_deployment.py` - Verification script

## Important Security Notes

1. **Change default passwords** immediately after deployment
2. **Restrict database access** in production
3. **Use SSL/TLS** for database connections in production
4. **Backup regularly** using pg_dump or similar

## Contact

For issues with deployment:
1. Check logs in deployment directory
2. Verify PostgreSQL version (12+ required)
3. Ensure sufficient disk space (minimum 2GB)
4. Check network connectivity for Docker services