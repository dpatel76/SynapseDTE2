#!/bin/bash
# Load all seed data into the database

echo "Loading seed data into synapse_dt database..."

# Database connection parameters
DB_HOST="localhost"
DB_PORT="5433"
DB_NAME="synapse_dt"
DB_USER="synapse_user"
DB_PASSWORD="synapse_password"

# Directory containing seed files
SEED_DIR="/Users/dineshpatel/code/projects/SynapseDTE2/scripts/database/08032025/sql_seeds"

# Check if directory exists
if [ ! -d "$SEED_DIR" ]; then
    echo "Error: Seed directory $SEED_DIR does not exist"
    exit 1
fi

# Load seed files in a specific order to respect foreign key constraints
# Order matters due to dependencies between tables

# 1. Base tables (no foreign keys)
echo "Loading base tables..."
for file in lobs.sql rbac_roles.sql rbac_permissions.sql test_cycles.sql reports.sql regulatory_data_dictionaries.sql; do
    if [ -f "$SEED_DIR/$file" ]; then
        echo "Loading $file..."
        PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f "$SEED_DIR/$file" 2>&1 | grep -E "(ERROR|NOTICE|INSERT)" || true
    fi
done

# 2. User-related tables
echo "Loading user tables..."
for file in users.sql rbac_user_roles.sql rbac_role_permissions.sql rbac_user_permissions.sql rbac_permission_audit_logs.sql; do
    if [ -f "$SEED_DIR/$file" ]; then
        echo "Loading $file..."
        PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f "$SEED_DIR/$file" 2>&1 | grep -E "(ERROR|NOTICE|INSERT)" || true
    fi
done

# 3. Cycle and report related tables
echo "Loading cycle and report tables..."
for file in cycle_reports.sql workflow_phases.sql workflow_activity_templates.sql workflow_activity_dependencies.sql activity_definitions.sql activity_states.sql; do
    if [ -f "$SEED_DIR/$file" ]; then
        echo "Loading $file..."
        PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f "$SEED_DIR/$file" 2>&1 | grep -E "(ERROR|NOTICE|INSERT)" || true
    fi
done

# 4. Planning phase tables
echo "Loading planning phase tables..."
for file in cycle_report_planning_data_sources.sql cycle_report_planning_attributes.sql cycle_report_planning_pde_mappings.sql; do
    if [ -f "$SEED_DIR/$file" ]; then
        echo "Loading $file..."
        PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f "$SEED_DIR/$file" 2>&1 | grep -E "(ERROR|NOTICE|INSERT)" || true
    fi
done

# 5. Data profiling tables
echo "Loading data profiling tables..."
for file in cycle_report_data_profiling_rule_versions.sql cycle_report_data_profiling_results.sql; do
    if [ -f "$SEED_DIR/$file" ]; then
        echo "Loading $file..."
        PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f "$SEED_DIR/$file" 2>&1 | grep -E "(ERROR|NOTICE|INSERT)" || true
    fi
done

# 6. Remaining tables
echo "Loading remaining tables..."
for file in "$SEED_DIR"/*.sql; do
    # Skip if already loaded
    filename=$(basename "$file")
    if ! echo "$filename" | grep -qE "(lobs|rbac_|users|test_cycles|reports|regulatory_data_dictionaries|cycle_reports|workflow_|activity_|cycle_report_planning_|cycle_report_data_profiling_)"; then
        echo "Loading $filename..."
        PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f "$file" 2>&1 | grep -E "(ERROR|NOTICE|INSERT)" || true
    fi
done

# Load test user last
echo "Loading test user..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f "/Users/dineshpatel/code/projects/SynapseDTE2/scripts/database/08032025/99_test_user.sql"

echo "Seed data loading complete!"

# Verify some key tables
echo ""
echo "Verifying key tables:"
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT COUNT(*) as user_count FROM users;"
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT COUNT(*) as report_count FROM reports;"
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT COUNT(*) as cycle_count FROM test_cycles;"