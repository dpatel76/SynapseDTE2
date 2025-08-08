# Deployment Scripts and Documentation

This directory contains all deployment-related scripts and documentation for SynapseDTE.

## Quick Start

For rapid deployment, see [QUICK_START.md](QUICK_START.md).

## Contents

### Documentation

- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Comprehensive deployment guide covering all components
- **[QUICK_START.md](QUICK_START.md)** - Quick start guide for rapid deployment  
- **[requirements.txt](requirements.txt)** - Python dependencies for the application

### Database Deployment Scripts

#### 1. With Source Database Access

- **[create_test_database.py](create_test_database.py)** - Creates a complete test database by copying from source
  ```bash
  python scripts/deployment/create_test_database.py
  ```

- **[export_schema.py](export_schema.py)** - Exports database schema and seed data to SQL files
  ```bash
  python scripts/deployment/export_schema.py
  ```

#### 2. Without Source Database Access

- **[create_database_from_schema.py](create_database_from_schema.py)** - Creates database from exported SQL files
  ```bash
  python scripts/deployment/create_database_from_schema.py
  ```

## Deployment Workflow

### Option 1: Direct Database Copy (requires source database)
1. Run `create_test_database.py` to create a test database directly from source

### Option 2: Export/Import (for deployment without source database)
1. On a machine with source database access, run `export_schema.py`
2. Copy the generated SQL files from `migrations/schema/` to the target machine
3. On the target machine, run `create_database_from_schema.py`

### Option 3: Full Application Deployment
1. Follow the instructions in `DEPLOYMENT_GUIDE.md` for complete application setup
2. Use `QUICK_START.md` for rapid deployment in development environments

## Environment Variables

All scripts support these environment variables:

```bash
# Database connection
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/dbname

# Alternative individual settings
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=synapse_dt

# Source database (for migration scripts)
SOURCE_DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/source_db
```

## Prerequisites

- Python 3.9+
- PostgreSQL 12+
- All Python packages in requirements.txt

## Security Notes

1. Never commit `.env` files with real credentials
2. Use strong passwords for database users
3. Restrict database access to application servers only
4. Enable SSL for database connections in production
5. Regular backups are essential

## Troubleshooting

See the troubleshooting sections in:
- [DEPLOYMENT_GUIDE.md#troubleshooting](DEPLOYMENT_GUIDE.md#troubleshooting)
- [QUICK_START.md#troubleshooting](QUICK_START.md#troubleshooting)