#!/bin/bash
set -e

echo "Testing Alembic Migration from Scratch"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Database connection details
DB_HOST="localhost"
DB_PORT="5433"
DB_NAME="synapse_dt"
DB_USER="synapse_user"
DB_PASS="synapse_password"

echo -e "${BLUE}Current database backup is at:${NC}"
echo "backups/synapse_dt_backup_*.sql"
echo ""

echo -e "${RED}WARNING: This will DROP ALL TABLES in the database!${NC}"
echo -n "Are you sure you want to continue? (yes/no): "
read -r response

if [[ "$response" != "yes" ]]; then
    echo "Aborted."
    exit 1
fi

echo -e "${YELLOW}Step 1: Counting current tables${NC}"
CURRENT_TABLES=$(docker exec synapse-postgres-container psql -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';")
echo "Current tables in database: $CURRENT_TABLES"

echo -e "${YELLOW}Step 2: Dropping all tables${NC}"
# Generate DROP commands for all tables
docker exec synapse-postgres-container psql -U $DB_USER -d $DB_NAME -c "
DO \$\$ 
DECLARE
    r RECORD;
BEGIN
    -- Drop all tables
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
        EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
    END LOOP;
    
    -- Drop all custom types
    FOR r IN (SELECT typname FROM pg_type WHERE typtype = 'e' AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')) LOOP
        EXECUTE 'DROP TYPE IF EXISTS ' || quote_ident(r.typname) || ' CASCADE';
    END LOOP;
END \$\$;
"

echo -e "${GREEN}✓ All tables dropped${NC}"

echo -e "${YELLOW}Step 3: Verifying empty database${NC}"
TABLES_AFTER_DROP=$(docker exec synapse-postgres-container psql -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';")
echo "Tables after drop: $TABLES_AFTER_DROP"

echo -e "${YELLOW}Step 4: Stopping backend container${NC}"
docker-compose -f docker-compose.container.yml stop backend
echo -e "${GREEN}✓ Backend stopped${NC}"

echo -e "${YELLOW}Step 5: Running SQL initialization scripts${NC}"
# Run the SQL scripts to create schema
for script in /Users/dineshpatel/code/projects/SynapseDTE2/scripts/database/08032025/*.sql; do
    if [[ -f "$script" ]]; then
        script_name=$(basename "$script")
        echo -n "  Running $script_name... "
        if docker exec -i synapse-postgres-container psql -U $DB_USER -d $DB_NAME < "$script" > /dev/null 2>&1; then
            echo -e "${GREEN}✓${NC}"
        else
            echo -e "${RED}✗${NC}"
            echo -e "${RED}Failed to run $script_name${NC}"
            # Continue anyway to see what happens
        fi
    fi
done

echo -e "${YELLOW}Step 6: Checking alembic_version table${NC}"
ALEMBIC_EXISTS=$(docker exec synapse-postgres-container psql -U $DB_USER -d $DB_NAME -t -c "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'alembic_version');")
if [[ "$ALEMBIC_EXISTS" == " t" ]]; then
    echo "alembic_version table exists"
    ALEMBIC_VERSION=$(docker exec synapse-postgres-container psql -U $DB_USER -d $DB_NAME -t -c "SELECT version_num FROM alembic_version;" 2>/dev/null || echo "empty")
    echo "Current version: $ALEMBIC_VERSION"
else
    echo "alembic_version table does not exist"
fi

echo -e "${YELLOW}Step 7: Starting backend container (migrations will run automatically)${NC}"
docker-compose -f docker-compose.container.yml up -d backend

echo -e "${YELLOW}Step 8: Waiting for backend to start${NC}"
sleep 10

echo -e "${YELLOW}Step 9: Checking backend logs for migration${NC}"
echo "=== Backend Container Logs ==="
docker-compose -f docker-compose.container.yml logs backend | tail -n 50 | grep -E "(migration|alembic|Migration|Alembic|database|Database)" || true

echo -e "${YELLOW}Step 10: Verifying final state${NC}"
# Count tables
FINAL_TABLES=$(docker exec synapse-postgres-container psql -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';")
echo "Final table count: $FINAL_TABLES"

# Check alembic version
FINAL_VERSION=$(docker exec synapse-postgres-container psql -U $DB_USER -d $DB_NAME -t -c "SELECT version_num FROM alembic_version;" 2>/dev/null || echo "not set")
echo "Final Alembic version: $FINAL_VERSION"

# List some key tables
echo -e "${YELLOW}Key tables check:${NC}"
for table in users roles permissions test_cycles workflow_phases; do
    EXISTS=$(docker exec synapse-postgres-container psql -U $DB_USER -d $DB_NAME -t -c "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = '$table');")
    if [[ "$EXISTS" == " t" ]]; then
        echo -e "  ${GREEN}✓${NC} $table"
    else
        echo -e "  ${RED}✗${NC} $table"
    fi
done

echo -e "${YELLOW}Step 11: Testing application login${NC}"
# Wait a bit more for backend to fully start
sleep 5

# Test login endpoint
echo "Testing login endpoint..."
LOGIN_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "tester@example.com", "password": "password123"}' | tail -1)

if [[ "$LOGIN_RESPONSE" == "200" ]]; then
    echo -e "${GREEN}✓ Login successful!${NC}"
else
    echo -e "${RED}✗ Login failed with status: $LOGIN_RESPONSE${NC}"
    echo "Backend logs:"
    docker-compose -f docker-compose.container.yml logs backend | tail -20
fi

echo ""
echo -e "${BLUE}Test Summary:${NC}"
echo "- Started with $CURRENT_TABLES tables"
echo "- Dropped to $TABLES_AFTER_DROP tables"
echo "- Ended with $FINAL_TABLES tables"
echo "- Alembic version: $FINAL_VERSION"
echo ""

if [[ "$FINAL_TABLES" -eq "126" ]] && [[ "$LOGIN_RESPONSE" == "200" ]]; then
    echo -e "${GREEN}✅ TEST PASSED: Alembic migration successfully recreated database!${NC}"
else
    echo -e "${RED}❌ TEST FAILED: Check logs above for issues${NC}"
fi

echo ""
echo -e "${BLUE}To restore from backup if needed:${NC}"
echo "docker exec -i synapse-postgres-container psql -U $DB_USER -d $DB_NAME < backups/synapse_dt_backup_*.sql"