#!/bin/bash

# Setup Test Database Script
# Creates a test database for migration validation

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Test Database Setup Script ===${NC}"

# Database configuration
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-synapse_user}"
DB_PASSWORD="${DB_PASSWORD:-synapse_password}"
TEST_DB_NAME="${TEST_DB_NAME:-synapse_dt_test}"

# Check if psql is available
if ! command -v psql &> /dev/null; then
    echo -e "${RED}Error: psql command not found. Please install PostgreSQL client.${NC}"
    exit 1
fi

# Export password for non-interactive authentication
export PGPASSWORD=$DB_PASSWORD

echo -e "${YELLOW}Database Configuration:${NC}"
echo "Host: $DB_HOST:$DB_PORT"
echo "User: $DB_USER"
echo "Test Database: $TEST_DB_NAME"
echo ""

# Check if test database already exists
DB_EXISTS=$(psql -h $DB_HOST -p $DB_PORT -U $DB_USER -tAc "SELECT 1 FROM pg_database WHERE datname='$TEST_DB_NAME'" postgres 2>/dev/null || echo "0")

if [ "$DB_EXISTS" = "1" ]; then
    echo -e "${YELLOW}Test database '$TEST_DB_NAME' already exists.${NC}"
    read -p "Do you want to drop and recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Dropping existing test database...${NC}"
        psql -h $DB_HOST -p $DB_PORT -U $DB_USER -c "DROP DATABASE IF EXISTS $TEST_DB_NAME;" postgres
        echo -e "${GREEN}✓ Test database dropped${NC}"
    else
        echo "Keeping existing test database."
        exit 0
    fi
fi

# Create test database
echo -e "${YELLOW}Creating test database '$TEST_DB_NAME'...${NC}"
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -c "CREATE DATABASE $TEST_DB_NAME;" postgres

# Grant privileges
echo -e "${YELLOW}Granting privileges...${NC}"
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -c "GRANT ALL PRIVILEGES ON DATABASE $TEST_DB_NAME TO $DB_USER;" postgres

echo -e "${GREEN}✓ Test database created successfully!${NC}"

# Create .env.test file for the migration script
echo -e "${YELLOW}Creating .env.test configuration...${NC}"
cat > .env.test << EOF
# Test Database Configuration
SOURCE_DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/synapse_dt
TEST_DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$TEST_DB_NAME
EOF

echo -e "${GREEN}✓ Configuration saved to .env.test${NC}"

echo -e "\n${GREEN}=== Setup Complete ===${NC}"
echo -e "You can now run the migration reconciler:"
echo -e "${YELLOW}python scripts/database_migration_reconciler.py${NC}"