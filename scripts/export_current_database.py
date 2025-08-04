#!/usr/bin/env python3
"""
Export current database schema and seed data for deployment on new machines
"""
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Configuration
DB_NAME = os.getenv("DB_NAME", "synapse_dt")
DB_USER = os.getenv("DB_USER", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

OUTPUT_DIR = Path("scripts/database/exports")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Create timestamp for backup
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

def run_command(cmd, description):
    """Run a shell command and handle errors"""
    print(f"\n{description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            return False
        print(f"✓ {description} completed")
        return True
    except Exception as e:
        print(f"Error running command: {e}")
        return False

def export_schema():
    """Export complete database schema"""
    schema_file = OUTPUT_DIR / f"schema_{timestamp}.sql"
    
    cmd = f"""pg_dump -U {DB_USER} -h {DB_HOST} -p {DB_PORT} -d {DB_NAME} \
        --schema-only \
        --no-owner \
        --no-privileges \
        --no-tablespaces \
        --no-unlogged-table-data \
        --if-exists \
        --clean \
        -f {schema_file}"""
    
    if run_command(cmd, "Exporting database schema"):
        print(f"Schema exported to: {schema_file}")
        return schema_file
    return None

def export_seed_data():
    """Export essential seed data only"""
    data_file = OUTPUT_DIR / f"seed_data_{timestamp}.sql"
    
    # Tables that contain essential seed data
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
        "phase_statuses"
    ]
    
    # Build pg_dump command with specific tables
    table_args = " ".join([f"-t {table}" for table in seed_tables])
    
    cmd = f"""pg_dump -U {DB_USER} -h {DB_HOST} -p {DB_PORT} -d {DB_NAME} \
        --data-only \
        --no-owner \
        --no-privileges \
        --disable-triggers \
        --inserts \
        {table_args} \
        -f {data_file}"""
    
    if run_command(cmd, "Exporting seed data"):
        print(f"Seed data exported to: {data_file}")
        return data_file
    return None

def create_deployment_script():
    """Create a deployment script for the new machine"""
    script_file = OUTPUT_DIR / f"deploy_{timestamp}.sh"
    
    script_content = f"""#!/bin/bash
# Database deployment script generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

# Configuration
DB_NAME="${{DB_NAME:-synapse_dt}}"
DB_USER="${{DB_USER:-postgres}}"
DB_HOST="${{DB_HOST:-localhost}}"
DB_PORT="${{DB_PORT:-5432}}"

echo "Database Deployment Script"
echo "========================="
echo "Database: $DB_NAME"
echo "User: $DB_USER"
echo "Host: $DB_HOST:$DB_PORT"
echo ""

# Check if database exists
if psql -U $DB_USER -h $DB_HOST -p $DB_PORT -lqt | cut -d \\| -f 1 | grep -qw $DB_NAME; then
    echo "WARNING: Database '$DB_NAME' already exists!"
    read -p "Drop and recreate? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Dropping existing database..."
        dropdb -U $DB_USER -h $DB_HOST -p $DB_PORT $DB_NAME
    else
        echo "Deployment cancelled."
        exit 1
    fi
fi

# Create database
echo "Creating database..."
createdb -U $DB_USER -h $DB_HOST -p $DB_PORT $DB_NAME

# Load schema
echo "Loading schema..."
psql -U $DB_USER -h $DB_HOST -p $DB_PORT -d $DB_NAME -f schema_{timestamp}.sql

# Load seed data
echo "Loading seed data..."
psql -U $DB_USER -h $DB_HOST -p $DB_PORT -d $DB_NAME -f seed_data_{timestamp}.sql

# Verify deployment
echo ""
echo "Verifying deployment..."
psql -U $DB_USER -h $DB_HOST -p $DB_PORT -d $DB_NAME -c "SELECT COUNT(*) as table_count FROM information_schema.tables WHERE table_schema = 'public';"
psql -U $DB_USER -h $DB_HOST -p $DB_PORT -d $DB_NAME -c "SELECT COUNT(*) as role_count FROM roles;"
psql -U $DB_USER -h $DB_HOST -p $DB_PORT -d $DB_NAME -c "SELECT COUNT(*) as permission_count FROM permissions;"
psql -U $DB_USER -h $DB_HOST -p $DB_PORT -d $DB_NAME -c "SELECT COUNT(*) as user_count FROM users;"

echo ""
echo "Deployment complete!"
echo ""
echo "Test users available:"
echo "===================="
psql -U $DB_USER -h $DB_HOST -p $DB_PORT -d $DB_NAME -c "SELECT u.email, r.role_name FROM users u JOIN user_roles ur ON u.user_id = ur.user_id JOIN roles r ON ur.role_id = r.role_id ORDER BY u.email;"
"""
    
    with open(script_file, 'w') as f:
        f.write(script_content)
    
    # Make script executable
    os.chmod(script_file, 0o755)
    
    print(f"Deployment script created: {script_file}")
    return script_file

def main():
    print("SynapseDTE Database Export Tool")
    print("==============================")
    print(f"Source Database: {DB_NAME}@{DB_HOST}:{DB_PORT}")
    print(f"Output Directory: {OUTPUT_DIR}")
    
    # Export schema
    schema_file = export_schema()
    if not schema_file:
        print("Failed to export schema!")
        sys.exit(1)
    
    # Export seed data
    data_file = export_seed_data()
    if not data_file:
        print("Failed to export seed data!")
        sys.exit(1)
    
    # Create deployment script
    deploy_script = create_deployment_script()
    
    print("\n" + "="*50)
    print("Export completed successfully!")
    print("="*50)
    print(f"\nFiles created in: {OUTPUT_DIR}")
    print(f"  - Schema: schema_{timestamp}.sql")
    print(f"  - Seed Data: seed_data_{timestamp}.sql")
    print(f"  - Deploy Script: deploy_{timestamp}.sh")
    print("\nTo deploy on new machine:")
    print(f"  1. Copy the entire '{OUTPUT_DIR}' directory to the new machine")
    print(f"  2. Run: ./deploy_{timestamp}.sh")
    print("\nAlternatively, manually run:")
    print(f"  psql -U postgres -d synapse_dt -f schema_{timestamp}.sql")
    print(f"  psql -U postgres -d synapse_dt -f seed_data_{timestamp}.sql")

if __name__ == "__main__":
    main()