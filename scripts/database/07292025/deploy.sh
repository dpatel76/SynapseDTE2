#!/bin/bash
# SynapseDTE Database Deployment Script
# Generated: 2025-07-29 22:24:28
# Total tables: 108 (including workflow/temporal tables)

set -e  # Exit on error

# Configuration
DB_NAME="${DB_NAME:-synapse_dt}"
DB_USER="${DB_USER:-postgres}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}SynapseDTE Database Deployment${NC}"
echo "=============================="
echo "Database: $DB_NAME"
echo "User: $DB_USER"
echo "Host: $DB_HOST:$DB_PORT"
echo ""

# Function to check if database exists
db_exists() {
    psql -U $DB_USER -h $DB_HOST -p $DB_PORT -lqt | cut -d \| -f 1 | grep -qw $DB_NAME
}

# Function to run psql command
run_psql() {
    psql -U $DB_USER -h $DB_HOST -p $DB_PORT "$@"
}

# Check deployment mode
if [ "$1" == "--seed-only" ]; then
    DEPLOYMENT_MODE="seed"
    echo -e "${YELLOW}Running in SEED ONLY mode (minimal data)${NC}"
else
    DEPLOYMENT_MODE="full"
    echo -e "${YELLOW}Running in FULL mode (complete data)${NC}"
fi

# Check if database exists
if db_exists; then
    echo -e "${YELLOW}WARNING: Database '$DB_NAME' already exists!${NC}"
    echo "Choose an option:"
    echo "1) Drop and recreate (DESTROYS ALL DATA)"
    echo "2) Skip schema, load data only"
    echo "3) Cancel"
    read -p "Enter choice [1-3]: " choice
    
    case $choice in
        1)
            echo -e "${RED}Dropping existing database...${NC}"
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
    echo -e "${GREEN}Loading database schema...${NC}"
    run_psql -d $DB_NAME -f 01_complete_schema.sql > schema_load.log 2>&1
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Schema loaded successfully${NC}"
    else
        echo -e "${RED}✗ Schema load failed! Check schema_load.log${NC}"
        exit 1
    fi
fi

# Load data based on mode
echo ""
if [ "$DEPLOYMENT_MODE" == "seed" ]; then
    echo -e "${GREEN}Loading seed data only...${NC}"
    run_psql -d $DB_NAME -f 03_seed_data_only.sql > seed_load.log 2>&1
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Seed data loaded successfully${NC}"
    else
        echo -e "${RED}✗ Seed data load failed! Check seed_load.log${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}Loading complete data...${NC}"
    run_psql -d $DB_NAME -f 02_complete_data.sql > data_load.log 2>&1
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Complete data loaded successfully${NC}"
    else
        echo -e "${RED}✗ Data load failed! Check data_load.log${NC}"
        exit 1
    fi
fi

# Verify deployment
echo ""
echo -e "${GREEN}Verifying deployment...${NC}"
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
    printf "  %-25s %s\n" "$table:" "$COUNT"
done

# Show test users
echo ""
echo -e "${GREEN}Available test users:${NC}"
echo "===================="
run_psql -d $DB_NAME -c "SELECT u.email, r.role_name, 'password123' as password FROM users u JOIN user_roles ur ON u.user_id = ur.user_id JOIN roles r ON ur.role_id = r.role_id ORDER BY u.email;" 2>/dev/null || echo "No users found"

echo ""
echo -e "${GREEN}Deployment complete!${NC}"
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
