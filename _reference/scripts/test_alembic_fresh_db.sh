#!/bin/bash
set -e

echo "Testing Alembic migration on fresh database..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Database connection details
DB_HOST="localhost"
DB_PORT="5433"
DB_NAME="synapse_dt_test_alembic"
DB_USER="synapse_user"
DB_PASS="synapse_password"

echo -e "${YELLOW}Step 1: Creating fresh test database${NC}"
PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME;"
PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c "CREATE DATABASE $DB_NAME;"
echo -e "${GREEN}✓ Fresh database created: $DB_NAME${NC}"

echo -e "${YELLOW}Step 2: Running SQL scripts to create schema${NC}"
# Run the schema creation scripts
for script in /Users/dineshpatel/code/projects/SynapseDTE2/scripts/database/08032025/*.sql; do
    if [[ -f "$script" ]]; then
        echo "Running: $(basename $script)"
        PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f "$script" > /dev/null 2>&1 || {
            echo -e "${RED}✗ Failed to run $(basename $script)${NC}"
            exit 1
        }
    fi
done
echo -e "${GREEN}✓ All SQL scripts executed successfully${NC}"

echo -e "${YELLOW}Step 3: Checking database state before Alembic${NC}"
TABLES_BEFORE=$(PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';")
echo "Tables in database: $TABLES_BEFORE"

echo -e "${YELLOW}Step 4: Running Alembic migration${NC}"
# Set database URL for Alembic
export DATABASE_URL="postgresql://$DB_USER:$DB_PASS@$DB_HOST:$DB_PORT/$DB_NAME"

# Run alembic upgrade
cd /Users/dineshpatel/code/projects/SynapseDTE2
alembic upgrade head

echo -e "${YELLOW}Step 5: Verifying Alembic version table${NC}"
ALEMBIC_VERSION=$(PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT version_num FROM alembic_version;")
echo "Current Alembic version: $ALEMBIC_VERSION"

echo -e "${YELLOW}Step 6: Checking final database state${NC}"
TABLES_AFTER=$(PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';")
echo "Tables in database after migration: $TABLES_AFTER"

# List all tables
echo -e "${YELLOW}All tables in database:${NC}"
PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "\dt"

echo -e "${GREEN}✓ Alembic migration test completed successfully!${NC}"
echo -e "${GREEN}✓ Future database changes can be tracked using: alembic revision --autogenerate -m 'description'${NC}"

# Clean up test database
echo -e "${YELLOW}Cleaning up test database...${NC}"
PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME;"
echo -e "${GREEN}✓ Test database cleaned up${NC}"