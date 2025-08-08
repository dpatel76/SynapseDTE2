#!/bin/bash
set -e

echo "Database Schema Fix Script"
echo "========================="
echo ""
echo "This script will:"
echo "1. Backup the current database"
echo "2. Create a fresh database from SQLAlchemy models"
echo "3. Apply proper Alembic baseline"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Database details
DB_HOST="localhost"
DB_PORT="5433"
DB_NAME="synapse_dt"
DB_USER="synapse_user"
DB_PASS="synapse_password"

echo -e "${RED}WARNING: This will recreate the database to match the application models!${NC}"
echo -n "Continue? (yes/no): "
read -r response

if [[ "$response" != "yes" ]]; then
    echo "Aborted."
    exit 1
fi

echo -e "${YELLOW}Step 1: Creating backup of current database${NC}"
BACKUP_FILE="backups/synapse_dt_before_fix_$(date +%Y%m%d_%H%M%S).sql"
docker exec synapse-postgres-container pg_dump -U $DB_USER -d $DB_NAME > $BACKUP_FILE
echo -e "${GREEN}✓ Backup saved to: $BACKUP_FILE${NC}"

echo -e "${YELLOW}Step 2: Dropping and recreating database${NC}"
docker exec synapse-postgres-container psql -U $DB_USER -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME;"
docker exec synapse-postgres-container psql -U $DB_USER -d postgres -c "CREATE DATABASE $DB_NAME;"
echo -e "${GREEN}✓ Database recreated${NC}"

echo -e "${YELLOW}Step 3: Removing old Alembic migration${NC}"
rm -f alembic/versions/*sync_models_with_database.py
echo -e "${GREEN}✓ Old migration removed${NC}"

echo -e "${YELLOW}Step 4: Creating fresh Alembic migration from models${NC}"
export DATABASE_URL="postgresql://$DB_USER:$DB_PASS@$DB_HOST:$DB_PORT/$DB_NAME"

# Create all tables from models
alembic revision --autogenerate -m "create_all_tables_from_models"
echo -e "${GREEN}✓ Migration created${NC}"

echo -e "${YELLOW}Step 5: Applying migration to create all tables${NC}"
alembic upgrade head
echo -e "${GREEN}✓ All tables created from models${NC}"

echo -e "${YELLOW}Step 6: Adding seed data${NC}"
# Create test user with bcrypt password
docker exec synapse-postgres-container psql -U $DB_USER -d $DB_NAME << 'EOF'
-- Create LOB first
INSERT INTO lobs (lob_id, name, description, is_active, created_at, updated_at)
VALUES (gen_random_uuid(), 'Default LOB', 'Default Line of Business', true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT DO NOTHING;

-- Create test user with bcrypt password
INSERT INTO users (user_id, email, hashed_password, first_name, last_name, role, is_active, lob_id, created_at, updated_at)
VALUES (
    gen_random_uuid(),
    'tester@example.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewYpfQerS2RH/XbC',  -- password123
    'Test',
    'User',
    'Admin',
    true,
    (SELECT lob_id FROM lobs LIMIT 1),
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
) ON CONFLICT (email) DO NOTHING;

-- Create basic RBAC data
INSERT INTO rbac_roles (role_id, role_name, description, is_active, created_at, updated_at)
VALUES 
    (gen_random_uuid(), 'Admin', 'Administrator role', true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'User', 'Regular user role', true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT DO NOTHING;
EOF
echo -e "${GREEN}✓ Seed data added${NC}"

echo -e "${YELLOW}Step 7: Verifying database${NC}"
TABLE_COUNT=$(docker exec synapse-postgres-container psql -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';")
echo "Tables created: $TABLE_COUNT"

ALEMBIC_VERSION=$(docker exec synapse-postgres-container psql -U $DB_USER -d $DB_NAME -t -c "SELECT version_num FROM alembic_version;" 2>/dev/null | xargs)
echo "Alembic version: $ALEMBIC_VERSION"

echo -e "${YELLOW}Step 8: Restarting backend${NC}"
docker-compose -f docker-compose.container.yml restart backend
sleep 10

echo -e "${GREEN}✅ Database schema fixed!${NC}"
echo ""
echo "The database now matches the SQLAlchemy models."
echo "Test with: curl -X POST http://localhost:8001/api/v1/auth/login -H 'Content-Type: application/json' -d '{\"email\":\"tester@example.com\",\"password\":\"password123\"}'"