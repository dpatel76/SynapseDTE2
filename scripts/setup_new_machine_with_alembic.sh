#!/bin/bash
set -e

echo "SynapseDTE2 - New Machine Setup Script"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5433}"
DB_NAME="${DB_NAME:-synapse_dt}"
DB_USER="${DB_USER:-synapse_user}"
DB_PASS="${DB_PASS:-synapse_password}"

echo -e "${BLUE}Database Configuration:${NC}"
echo "  Host: $DB_HOST"
echo "  Port: $DB_PORT"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo ""

# Function to check if PostgreSQL is running
check_postgres() {
    echo -e "${YELLOW}Checking PostgreSQL connection...${NC}"
    if PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c "SELECT 1" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PostgreSQL is accessible${NC}"
        return 0
    else
        echo -e "${RED}✗ Cannot connect to PostgreSQL${NC}"
        echo "Please ensure PostgreSQL is running and accessible at $DB_HOST:$DB_PORT"
        return 1
    fi
}

# Function to create database if it doesn't exist
create_database() {
    echo -e "${YELLOW}Checking if database exists...${NC}"
    if PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -lqt | cut -d \| -f 1 | grep -qw $DB_NAME; then
        echo -e "${GREEN}✓ Database '$DB_NAME' already exists${NC}"
        echo -n "Do you want to drop and recreate it? (y/N): "
        read -r response
        if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
            echo -e "${YELLOW}Dropping existing database...${NC}"
            PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c "DROP DATABASE $DB_NAME;"
            echo -e "${YELLOW}Creating fresh database...${NC}"
            PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c "CREATE DATABASE $DB_NAME;"
            echo -e "${GREEN}✓ Database recreated${NC}"
        else
            echo "Using existing database..."
        fi
    else
        echo -e "${YELLOW}Creating database...${NC}"
        PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c "CREATE DATABASE $DB_NAME;"
        echo -e "${GREEN}✓ Database created${NC}"
    fi
}

# Function to run SQL scripts
run_sql_scripts() {
    echo -e "${YELLOW}Running SQL initialization scripts...${NC}"
    
    SCRIPT_DIR="/Users/dineshpatel/code/projects/SynapseDTE2/scripts/database/08032025"
    
    if [[ ! -d "$SCRIPT_DIR" ]]; then
        echo -e "${RED}✗ SQL scripts directory not found: $SCRIPT_DIR${NC}"
        return 1
    fi
    
    # Run scripts in order
    for script in "$SCRIPT_DIR"/*.sql; do
        if [[ -f "$script" ]]; then
            script_name=$(basename "$script")
            echo -n "  Running $script_name... "
            if PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f "$script" > /dev/null 2>&1; then
                echo -e "${GREEN}✓${NC}"
            else
                echo -e "${RED}✗${NC}"
                echo -e "${RED}Failed to run $script_name${NC}"
                return 1
            fi
        fi
    done
    
    echo -e "${GREEN}✓ All SQL scripts executed successfully${NC}"
}

# Function to setup Alembic
setup_alembic() {
    echo -e "${YELLOW}Setting up Alembic migrations...${NC}"
    
    # Export database URL for Alembic
    export DATABASE_URL="postgresql://$DB_USER:$DB_PASS@$DB_HOST:$DB_PORT/$DB_NAME"
    
    # Change to project directory
    cd /Users/dineshpatel/code/projects/SynapseDTE2
    
    # Check if alembic is installed
    if ! command -v alembic &> /dev/null; then
        echo -e "${RED}✗ Alembic is not installed${NC}"
        echo "Please install Alembic: pip install alembic"
        return 1
    fi
    
    # Run migrations
    echo "  Running Alembic migrations..."
    if alembic upgrade head; then
        echo -e "${GREEN}✓ Alembic migrations completed${NC}"
    else
        echo -e "${RED}✗ Alembic migrations failed${NC}"
        return 1
    fi
    
    # Verify Alembic version
    VERSION=$(PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT version_num FROM alembic_version;" 2>/dev/null | xargs)
    if [[ -n "$VERSION" ]]; then
        echo -e "${GREEN}✓ Alembic version set to: $VERSION${NC}"
    else
        echo -e "${YELLOW}⚠ Could not verify Alembic version${NC}"
    fi
}

# Function to verify database setup
verify_setup() {
    echo -e "${YELLOW}Verifying database setup...${NC}"
    
    # Count tables
    TABLE_COUNT=$(PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';" | xargs)
    echo "  Total tables created: $TABLE_COUNT"
    
    # Check for key tables
    KEY_TABLES=("users" "roles" "permissions" "test_cycles" "reports" "workflow_phases")
    for table in "${KEY_TABLES[@]}"; do
        if PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT 1 FROM $table LIMIT 1;" > /dev/null 2>&1; then
            echo -e "  ${GREEN}✓${NC} Table '$table' exists"
        else
            echo -e "  ${RED}✗${NC} Table '$table' missing"
        fi
    done
    
    # Check test user
    TEST_USER=$(PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT email FROM users WHERE email = 'tester@example.com';" 2>/dev/null | xargs)
    if [[ "$TEST_USER" == "tester@example.com" ]]; then
        echo -e "  ${GREEN}✓${NC} Test user created (tester@example.com / password123)"
    else
        echo -e "  ${YELLOW}⚠${NC} Test user not found"
    fi
}

# Main setup flow
main() {
    echo ""
    echo -e "${BLUE}Starting database setup...${NC}"
    echo ""
    
    # Check PostgreSQL connection
    if ! check_postgres; then
        exit 1
    fi
    
    # Create database
    create_database
    
    # Run SQL scripts
    if ! run_sql_scripts; then
        echo -e "${RED}Setup failed during SQL script execution${NC}"
        exit 1
    fi
    
    # Setup Alembic
    if ! setup_alembic; then
        echo -e "${RED}Setup failed during Alembic migration${NC}"
        exit 1
    fi
    
    # Verify setup
    verify_setup
    
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}✓ Database setup completed successfully!${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Start the application containers:"
    echo "   docker-compose -f docker-compose.container.yml up -d"
    echo ""
    echo "2. Access the application:"
    echo "   Frontend: http://localhost:3001"
    echo "   Backend API: http://localhost:8001/docs"
    echo "   Temporal UI: http://localhost:8089"
    echo ""
    echo "3. Login with test credentials:"
    echo "   Email: tester@example.com"
    echo "   Password: password123"
    echo ""
    echo "4. For future database changes:"
    echo "   alembic revision --autogenerate -m 'description'"
    echo "   alembic upgrade head"
    echo ""
}

# Run main function
main