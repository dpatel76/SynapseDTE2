#!/bin/bash
set -e

echo "Testing Container Alembic Auto-Migration"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Database connection details
DB_NAME="synapse_dt"
DB_USER="synapse_user"

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

echo -e "${YELLOW}Step 2: Dropping all tables and types${NC}"
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
echo -e "${GREEN}✓ All tables and types dropped${NC}"

echo -e "${YELLOW}Step 3: Verifying empty database${NC}"
TABLES_AFTER_DROP=$(docker exec synapse-postgres-container psql -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';")
echo "Tables after drop: $TABLES_AFTER_DROP"

echo -e "${YELLOW}Step 4: Restarting backend container (this will trigger migrations)${NC}"
docker-compose -f docker-compose.container.yml restart backend

echo -e "${YELLOW}Step 5: Waiting for backend to start and run migrations${NC}"
echo "Waiting 20 seconds for migrations to complete..."
sleep 20

echo -e "${YELLOW}Step 6: Checking migration logs${NC}"
echo "=== Recent Backend Logs ==="
docker-compose -f docker-compose.container.yml logs --tail=100 backend | grep -E "(Starting|Waiting|Running|migration|alembic|Migration|Alembic|stamping|Stamping)" || true

echo -e "${YELLOW}Step 7: Verifying final state${NC}"
# Count tables
FINAL_TABLES=$(docker exec synapse-postgres-container psql -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';")
echo "Final table count: $FINAL_TABLES"

# Check alembic version
FINAL_VERSION=$(docker exec synapse-postgres-container psql -U $DB_USER -d $DB_NAME -t -c "SELECT version_num FROM alembic_version;" 2>/dev/null || echo "not set")
echo "Final Alembic version: $FINAL_VERSION"

# Check if backend is healthy
BACKEND_HEALTH=$(docker inspect synapse-backend-container --format='{{.State.Health.Status}}' 2>/dev/null || echo "unknown")
echo "Backend health status: $BACKEND_HEALTH"

echo -e "${YELLOW}Step 8: Testing application login${NC}"
# Test login endpoint
LOGIN_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "tester@example.com", "password": "password123"}' 2>/dev/null | tail -1)

if [[ "$LOGIN_RESPONSE" == "200" ]]; then
    echo -e "${GREEN}✓ Login successful!${NC}"
else
    echo -e "${RED}✗ Login failed with status: $LOGIN_RESPONSE${NC}"
fi

echo ""
echo -e "${BLUE}Test Summary:${NC}"
echo "- Started with $CURRENT_TABLES tables"
echo "- Dropped to $TABLES_AFTER_DROP tables"  
echo "- Container auto-migration resulted in $FINAL_TABLES tables"
echo "- Alembic version: $FINAL_VERSION"
echo "- Backend health: $BACKEND_HEALTH"
echo "- Login test: $LOGIN_RESPONSE"
echo ""

if [[ "$FINAL_TABLES" -gt "100" ]] && [[ "$LOGIN_RESPONSE" == "200" ]]; then
    echo -e "${GREEN}✅ SUCCESS: Container auto-migration worked!${NC}"
    echo "The backend container automatically:"
    echo "1. Detected the empty database"
    echo "2. Ran SQL initialization scripts"
    echo "3. Stamped Alembic version"
    echo "4. Started the application successfully"
else
    echo -e "${RED}❌ FAILED: Check logs above for issues${NC}"
    echo ""
    echo "Showing more backend logs:"
    docker-compose -f docker-compose.container.yml logs --tail=50 backend
fi

echo ""
echo -e "${BLUE}To restore from backup if needed:${NC}"
echo "docker exec -i synapse-postgres-container psql -U $DB_USER -d $DB_NAME < backups/synapse_dt_backup_*.sql"