#!/usr/bin/env python3
"""
Export COMPLETE database including schema and ALL data for SynapseDTE
Includes temporal/workflow tables and all recent schema changes
Date: 2025-07-29
"""
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
import json

# Configuration
DB_NAME = os.getenv("DB_NAME", "synapse_dt")
DB_USER = os.getenv("DB_USER", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

# Output directory (same as script location)
SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR

def run_command(cmd, description, capture_output=True):
    """Run a shell command and handle errors"""
    print(f"\n{description}...")
    try:
        if capture_output:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Error: {result.stderr}")
                return False, None
            print(f"✓ {description} completed")
            return True, result.stdout
        else:
            result = subprocess.run(cmd, shell=True)
            if result.returncode != 0:
                return False, None
            print(f"✓ {description} completed")
            return True, None
    except Exception as e:
        print(f"Error running command: {e}")
        return False, None

def get_database_stats():
    """Get comprehensive database statistics"""
    stats = {}
    
    queries = {
        "total_tables": "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'",
        "total_views": "SELECT COUNT(*) FROM information_schema.views WHERE table_schema = 'public'",
        "total_sequences": "SELECT COUNT(*) FROM information_schema.sequences WHERE sequence_schema = 'public'",
        "total_enums": "SELECT COUNT(*) FROM pg_type WHERE typtype = 'e'",
        "total_indexes": "SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public'",
        "total_constraints": "SELECT COUNT(*) FROM information_schema.table_constraints WHERE constraint_schema = 'public'",
        "workflow_tables": "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND (table_name LIKE '%workflow%' OR table_name LIKE '%temporal%')"
    }
    
    for key, query in queries.items():
        cmd = f'psql -U {DB_USER} -h {DB_HOST} -p {DB_PORT} -d {DB_NAME} -t -c "{query}"'
        success, output = run_command(cmd, f"Getting {key}", capture_output=True)
        if success and output:
            stats[key] = int(output.strip())
        else:
            stats[key] = 0
    
    # Get row counts for important tables
    important_tables = [
        'users', 'roles', 'permissions', 'role_permissions',
        'workflow_activities', 'workflow_phases', 'workflow_executions',
        'test_cycles', 'reports', 'lobs', 'data_sources',
        'request_info', 'request_info_evidence', 'attribute_dictionaries'
    ]
    
    stats['table_counts'] = {}
    for table in important_tables:
        cmd = f'psql -U {DB_USER} -h {DB_HOST} -p {DB_PORT} -d {DB_NAME} -t -c "SELECT COUNT(*) FROM {table}"'
        success, output = run_command(cmd, f"Counting rows in {table}", capture_output=True)
        if success and output:
            stats['table_counts'][table] = int(output.strip())
    
    return stats

def export_complete_schema():
    """Export complete database schema including all objects"""
    schema_file = OUTPUT_DIR / "01_complete_schema.sql"
    
    # Use pg_dump with comprehensive options
    cmd = f"""pg_dump -U {DB_USER} -h {DB_HOST} -p {DB_PORT} -d {DB_NAME} \
        --schema-only \
        --no-owner \
        --no-privileges \
        --no-tablespaces \
        --no-unlogged-table-data \
        --if-exists \
        --clean \
        --create \
        --encoding=UTF8 \
        --verbose \
        -f {schema_file}"""
    
    success, _ = run_command(cmd, "Exporting complete database schema", capture_output=False)
    if success:
        print(f"✓ Schema exported to: {schema_file}")
        
        # Add header to schema file
        header = f"""-- SynapseDTE Complete Database Schema
-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-- Database: {DB_NAME}
-- Total Tables: 108 (including workflow/temporal tables)
-- 
-- This file includes:
-- - All table definitions
-- - All ENUM types
-- - All indexes
-- - All constraints
-- - All sequences
-- - All views
-- - All functions/procedures
--
-- Usage: psql -U postgres -f 01_complete_schema.sql

"""
        content = schema_file.read_text()
        schema_file.write_text(header + content)
        
        return schema_file
    return None

def export_complete_data():
    """Export ALL data from the database"""
    data_file = OUTPUT_DIR / "02_complete_data.sql"
    
    # Export all data
    cmd = f"""pg_dump -U {DB_USER} -h {DB_HOST} -p {DB_PORT} -d {DB_NAME} \
        --data-only \
        --no-owner \
        --no-privileges \
        --disable-triggers \
        --inserts \
        --column-inserts \
        --encoding=UTF8 \
        --verbose \
        -f {data_file}"""
    
    success, _ = run_command(cmd, "Exporting complete database data", capture_output=False)
    if success:
        print(f"✓ Data exported to: {data_file}")
        
        # Add header
        header = f"""-- SynapseDTE Complete Database Data
-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-- Database: {DB_NAME}
-- 
-- This file includes ALL data from ALL tables
-- Foreign key constraints are disabled during import
--
-- Usage: psql -U postgres -d synapse_dt -f 02_complete_data.sql

SET session_replication_role = 'replica';

"""
        content = data_file.read_text()
        data_file.write_text(header + content + "\n\nSET session_replication_role = 'origin';\n")
        
        return data_file
    return None

def export_seed_data_only():
    """Export only essential seed data"""
    seed_file = OUTPUT_DIR / "03_seed_data_only.sql"
    
    # Essential tables for minimal setup
    seed_tables = [
        "roles",
        "permissions", 
        "role_permissions",
        "lobs",
        "users",
        "user_roles",
        "workflow_activity_templates",
        "workflow_activity_dependencies",
        "attribute_dictionaries",
        "phase_statuses",
        "test_report_statuses",
        "observation_statuses",
        "risk_levels"
    ]
    
    table_args = " ".join([f"-t {table}" for table in seed_tables])
    
    cmd = f"""pg_dump -U {DB_USER} -h {DB_HOST} -p {DB_PORT} -d {DB_NAME} \
        --data-only \
        --no-owner \
        --no-privileges \
        --disable-triggers \
        --inserts \
        --column-inserts \
        {table_args} \
        -f {seed_file}"""
    
    success, _ = run_command(cmd, "Exporting essential seed data", capture_output=False)
    if success:
        print(f"✓ Seed data exported to: {seed_file}")
        return seed_file
    return None

def create_deployment_script():
    """Create comprehensive deployment script"""
    script_file = OUTPUT_DIR / "deploy.sh"
    
    script_content = f"""#!/bin/bash
# SynapseDTE Database Deployment Script
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Total tables: 108 (including workflow/temporal tables)

set -e  # Exit on error

# Configuration
DB_NAME="${{DB_NAME:-synapse_dt}}"
DB_USER="${{DB_USER:-postgres}}"
DB_HOST="${{DB_HOST:-localhost}}"
DB_PORT="${{DB_PORT:-5432}}"

# Colors for output
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
NC='\\033[0m' # No Color

echo -e "${{GREEN}}SynapseDTE Database Deployment${{NC}}"
echo "=============================="
echo "Database: $DB_NAME"
echo "User: $DB_USER"
echo "Host: $DB_HOST:$DB_PORT"
echo ""

# Function to check if database exists
db_exists() {{
    psql -U $DB_USER -h $DB_HOST -p $DB_PORT -lqt | cut -d \\| -f 1 | grep -qw $DB_NAME
}}

# Function to run psql command
run_psql() {{
    psql -U $DB_USER -h $DB_HOST -p $DB_PORT "$@"
}}

# Check deployment mode
if [ "$1" == "--seed-only" ]; then
    DEPLOYMENT_MODE="seed"
    echo -e "${{YELLOW}}Running in SEED ONLY mode (minimal data)${{NC}}"
else
    DEPLOYMENT_MODE="full"
    echo -e "${{YELLOW}}Running in FULL mode (complete data)${{NC}}"
fi

# Check if database exists
if db_exists; then
    echo -e "${{YELLOW}}WARNING: Database '$DB_NAME' already exists!${{NC}}"
    echo "Choose an option:"
    echo "1) Drop and recreate (DESTROYS ALL DATA)"
    echo "2) Skip schema, load data only"
    echo "3) Cancel"
    read -p "Enter choice [1-3]: " choice
    
    case $choice in
        1)
            echo -e "${{RED}}Dropping existing database...${{NC}}"
            dropdb -U $DB_USER -h $DB_HOST -p $DB_PORT $DB_NAME
            createdb -U $DB_USER -h $DB_HOST -p $DB_PORT $DB_NAME
            LOAD_SCHEMA=true
            ;;
        2)
            echo "Keeping existing schema, will load data only..."
            LOAD_SCHEMA=false
            ;;
        *)
            echo "Deployment cancelled."
            exit 1
            ;;
    esac
else
    echo "Creating new database..."
    createdb -U $DB_USER -h $DB_HOST -p $DB_PORT $DB_NAME
    LOAD_SCHEMA=true
fi

# Load schema if needed
if [ "$LOAD_SCHEMA" = true ]; then
    echo ""
    echo -e "${{GREEN}}Loading database schema...${{NC}}"
    run_psql -d $DB_NAME -f 01_complete_schema.sql > schema_load.log 2>&1
    if [ $? -eq 0 ]; then
        echo -e "${{GREEN}}✓ Schema loaded successfully${{NC}}"
    else
        echo -e "${{RED}}✗ Schema load failed! Check schema_load.log${{NC}}"
        exit 1
    fi
fi

# Load data based on mode
echo ""
if [ "$DEPLOYMENT_MODE" == "seed" ]; then
    echo -e "${{GREEN}}Loading seed data only...${{NC}}"
    run_psql -d $DB_NAME -f 03_seed_data_only.sql > seed_load.log 2>&1
    if [ $? -eq 0 ]; then
        echo -e "${{GREEN}}✓ Seed data loaded successfully${{NC}}"
    else
        echo -e "${{RED}}✗ Seed data load failed! Check seed_load.log${{NC}}"
        exit 1
    fi
else
    echo -e "${{GREEN}}Loading complete data...${{NC}}"
    run_psql -d $DB_NAME -f 02_complete_data.sql > data_load.log 2>&1
    if [ $? -eq 0 ]; then
        echo -e "${{GREEN}}✓ Complete data loaded successfully${{NC}}"
    else
        echo -e "${{RED}}✗ Data load failed! Check data_load.log${{NC}}"
        exit 1
    fi
fi

# Verify deployment
echo ""
echo -e "${{GREEN}}Verifying deployment...${{NC}}"
echo "========================"

# Check table count
TABLE_COUNT=$(run_psql -d $DB_NAME -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
echo "Tables: $TABLE_COUNT (expected: 108)"

# Check other objects
ENUM_COUNT=$(run_psql -d $DB_NAME -t -c "SELECT COUNT(*) FROM pg_type WHERE typtype = 'e'")
echo "Enum types: $ENUM_COUNT"

INDEX_COUNT=$(run_psql -d $DB_NAME -t -c "SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public'")
echo "Indexes: $INDEX_COUNT"

# Check key tables
echo ""
echo "Key table row counts:"
for table in users roles permissions workflow_activities test_cycles reports; do
    COUNT=$(run_psql -d $DB_NAME -t -c "SELECT COUNT(*) FROM $table" 2>/dev/null || echo "0")
    printf "  %-25s %s\\n" "$table:" "$COUNT"
done

# Show test users
echo ""
echo -e "${{GREEN}}Available test users:${{NC}}"
echo "===================="
run_psql -d $DB_NAME -c "SELECT u.email, r.role_name, 'password123' as password FROM users u JOIN user_roles ur ON u.user_id = ur.user_id JOIN roles r ON ur.role_id = r.role_id ORDER BY u.email;" 2>/dev/null || echo "No users found"

echo ""
echo -e "${{GREEN}}Deployment complete!${{NC}}"
echo ""
echo "Next steps:"
echo "1. Update .env file:"
echo "   DATABASE_URL=postgresql://$DB_USER:password@$DB_HOST:$DB_PORT/$DB_NAME"
echo "2. Start the application:"
echo "   cd ../../../  # Go to project root"
echo "   uvicorn app.main:app --reload"
echo "3. Access at http://localhost:8000"

# Cleanup log files on success
if [ -f schema_load.log ] && [ -f data_load.log ] || [ -f seed_load.log ]; then
    echo ""
    read -p "Remove log files? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -f schema_load.log data_load.log seed_load.log
        echo "Log files removed."
    fi
fi
"""
    
    with open(script_file, 'w') as f:
        f.write(script_content)
    
    os.chmod(script_file, 0o755)
    print(f"✓ Deployment script created: {script_file}")
    return script_file

def create_readme():
    """Create comprehensive README with instructions"""
    readme_file = OUTPUT_DIR / "README.md"
    
    # Get current stats
    stats = get_database_stats()
    
    readme_content = f"""# SynapseDTE Database Export - {datetime.now().strftime('%Y-%m-%d')}

## Overview

This directory contains a complete database export of SynapseDTE, including all schema changes up to July 29, 2025.

### Database Statistics
- **Total Tables**: {stats.get('total_tables', 0)} (including workflow/temporal tables)
- **Total Views**: {stats.get('total_views', 0)}
- **Total Sequences**: {stats.get('total_sequences', 0)}
- **Total ENUM Types**: {stats.get('total_enums', 0)}
- **Total Indexes**: {stats.get('total_indexes', 0)}
- **Total Constraints**: {stats.get('total_constraints', 0)}
- **Workflow/Temporal Tables**: {stats.get('workflow_tables', 0)}

### Key Table Row Counts
"""
    
    for table, count in stats.get('table_counts', {}).items():
        readme_content += f"- **{table}**: {count:,} rows\n"
    
    readme_content += f"""
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

- **Export Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Source Database**: {DB_NAME}
- **PostgreSQL Version**: Check with `psql --version`
- **Export Method**: pg_dump with comprehensive options
- **Includes**: Complete schema, all data, temporal tables
"""
    
    with open(readme_file, 'w') as f:
        f.write(readme_content)
    
    print(f"✓ README created: {readme_file}")
    return readme_file

def create_verification_script():
    """Create a script to verify the deployment"""
    verify_file = OUTPUT_DIR / "verify_deployment.py"
    
    verify_content = f'''#!/usr/bin/env python3
"""
Verify SynapseDTE database deployment
"""
import psycopg2
import sys
import os

# Database configuration
DB_NAME = os.getenv("DB_NAME", "synapse_dt")
DB_USER = os.getenv("DB_USER", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

def verify_database():
    """Verify database deployment"""
    try:
        # Connect to database
        conn_string = f"host={{DB_HOST}} port={{DB_PORT}} dbname={{DB_NAME}} user={{DB_USER}}"
        if DB_PASSWORD:
            conn_string += f" password={{DB_PASSWORD}}"
        
        conn = psycopg2.connect(conn_string)
        cur = conn.cursor()
        
        print("SynapseDTE Database Verification")
        print("================================")
        
        # Check tables
        cur.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        table_count = cur.fetchone()[0]
        print(f"✓ Tables: {{table_count}} (expected: 108)")
        
        # Check specific table groups
        checks = [
            ("Workflow tables", "table_name LIKE 'workflow%'"),
            ("Test tables", "table_name LIKE 'test%' OR table_name LIKE 'testing%'"),
            ("RFI tables", "table_name LIKE '%request_info%'"),
            ("User/Role tables", "table_name IN ('users', 'roles', 'permissions')")
        ]
        
        for check_name, condition in checks:
            cur.execute(f"""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND {{condition}}
            """)
            count = cur.fetchone()[0]
            print(f"✓ {{check_name}}: {{count}}")
        
        # Check data
        print("\\nData Verification:")
        data_checks = [
            ("users", "Users"),
            ("roles", "Roles"),
            ("permissions", "Permissions"),
            ("workflow_activity_templates", "Workflow templates"),
            ("lobs", "Lines of Business")
        ]
        
        for table, label in data_checks:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {{table}}")
                count = cur.fetchone()[0]
                print(f"  {{label}}: {{count}}")
            except:
                print(f"  {{label}}: ERROR")
        
        # Check test users
        print("\\nTest Users:")
        cur.execute("""
            SELECT u.email, r.role_name 
            FROM users u 
            JOIN user_roles ur ON u.user_id = ur.user_id 
            JOIN roles r ON ur.role_id = r.role_id 
            ORDER BY u.email
        """)
        for email, role in cur.fetchall():
            print(f"  {{email}} - {{role}}")
        
        conn.close()
        print("\\n✓ Database verification complete!")
        return True
        
    except Exception as e:
        print(f"\\n✗ Verification failed: {{e}}")
        return False

if __name__ == "__main__":
    sys.exit(0 if verify_database() else 1)
'''
    
    with open(verify_file, 'w') as f:
        f.write(verify_content)
    
    os.chmod(verify_file, 0o755)
    print(f"✓ Verification script created: {verify_file}")
    return verify_file

def main():
    """Main export process"""
    print("SynapseDTE Complete Database Export")
    print("===================================")
    print(f"Source: {DB_NAME}@{DB_HOST}:{DB_PORT}")
    print(f"Output: {OUTPUT_DIR}")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Get initial stats
    print("\nGathering database statistics...")
    stats = get_database_stats()
    
    # Save stats to JSON
    stats_file = OUTPUT_DIR / "database_stats.json"
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"✓ Stats saved to: {stats_file}")
    
    # Export schema
    schema_file = export_complete_schema()
    if not schema_file:
        print("Failed to export schema!")
        sys.exit(1)
    
    # Export complete data
    data_file = export_complete_data()
    if not data_file:
        print("Failed to export data!")
        sys.exit(1)
    
    # Export seed data
    seed_file = export_seed_data_only()
    if not seed_file:
        print("Failed to export seed data!")
        sys.exit(1)
    
    # Create deployment script
    deploy_script = create_deployment_script()
    
    # Create verification script
    verify_script = create_verification_script()
    
    # Create README
    readme = create_readme()
    
    print("\n" + "="*60)
    print("EXPORT COMPLETED SUCCESSFULLY!")
    print("="*60)
    print(f"\nFiles created in: {OUTPUT_DIR}")
    print("  - 01_complete_schema.sql (complete database structure)")
    print("  - 02_complete_data.sql (all data from all tables)")
    print("  - 03_seed_data_only.sql (minimal seed data)")
    print("  - deploy.sh (automated deployment script)")
    print("  - verify_deployment.py (verification script)")
    print("  - README.md (comprehensive instructions)")
    print("  - database_stats.json (current statistics)")
    
    print("\nTo deploy on new machine:")
    print(f"  1. Copy entire directory: {OUTPUT_DIR}")
    print("  2. Run: ./deploy.sh")
    print("     Or: ./deploy.sh --seed-only (for minimal setup)")
    
    print("\nDatabase includes:")
    print(f"  - {stats.get('total_tables', 0)} tables")
    print(f"  - {stats.get('workflow_tables', 0)} workflow/temporal tables")
    print(f"  - All schema changes through July 29, 2025")

if __name__ == "__main__":
    main()